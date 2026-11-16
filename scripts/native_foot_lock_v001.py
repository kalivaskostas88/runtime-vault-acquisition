#!/usr/bin/env python3
"""Native Blender 5.2.2 IK planting / bad-parent negative control.

A GitHub Actions *execution candidate*, not a local Blender PASS.
Use: blender -b --factory-startup --python native_foot_lock_v001.py -- build STEP /out/STEP
     blender -b /out/STEP/STEP.blend --python native_foot_lock_v001.py -- verify STEP /out/STEP
Purely original 3D teaching geometry. Never reads or modifies GS001 assets.
"""
import bpy
import json
import math
import sys
from pathlib import Path
from mathutils import Vector

FPS, LAST = 24, 96
KEYS = ((1, 0.00, 0.00), (24, 0.055, -0.018),
        (48, 0.210, -0.085), (72, 0.100, -0.040), (96, 0.00, 0.00))
POSITIONS = {'L': -0.23, 'R': 0.23}
FOOT_HEIGHT = 0.14
# This is a small synthetic puppet: no skin, COM or human anatomical proof.


def args():
    if '--' not in sys.argv:
        raise RuntimeError('Required args after --: build|verify STEP|SPLINE|BAD_PARENT /output/directory')
    a = sys.argv[sys.argv.index('--') + 1:]
    if len(a) != 3 or a[0] not in ('build','verify') or a[1] not in ('STEP','SPLINE','BAD_PARENT'):
        raise RuntimeError('Unexpected arguments: '+repr(a))
    return a[0], a[1], Path(a[2]).resolve()


def set_interpolation(obj, mode):
    ad = getattr(obj, 'animation_data', None)
    if not ad or not ad.action:
        return
    # Blender 5.2 may store FCurves inside action slots/layers.
    # Don't silently mislabel a STEP clip if curve discovery fails.
    action = ad.action
    found = 0
    curves = []
    try:
        curves.extend(list(action.fcurves))
    except (AttributeError, TypeError):
        pass
    if not curves:
        for layer in getattr(action, 'layers', []):
            for strip in layer.strips:
                for bag in getattr(strip, 'channelbags', []):
                    curves.extend(list(bag.fcurves))
    for curve in curves:
        for kp in curve.keyframe_points:
            kp.interpolation = 'CONSTANT' if mode == 'STEP' else 'BEZIER'
            if mode != 'STEP':
                kp.handle_left_type = 'AUTO_CLAMPED'
                kp.handle_right_type = 'AUTO_CLAMPED'
        found += 1
    if found == 0:
        raise RuntimeError('Cannot inspect FCurves; no interpolation proof')


def material(name, rgba):
    m=bpy.data.materials.new(name)
    m.diffuse_color=rgba
    return m


def shape_sphere(name, radius, rgba):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=12,ring_count=8,radius=radius)
    ob=bpy.context.object; ob.name=name
    ob.data.materials.append(material(name+'_MAT',rgba))
    return ob


def proxy_link(name,radius,rgba):
    bpy.ops.mesh.primitive_cylinder_add(vertices=12,radius=radius,depth=2.0)
    ob=bpy.context.object; ob.name=name
    ob.rotation_mode='QUATERNION'
    ob.data.materials.append(material(name+'_MAT',rgba))
    return ob


def place_segment(ob, a, b, frame):
    axis=b-a
    assert axis.length>1e-7
    ob.location=(a+b)*0.5
    ob.rotation_quaternion=Vector((0,0,1)).rotation_difference(axis)
    ob.scale=(1.0,1.0,axis.length*0.5)
    for path in ('location','rotation_quaternion','scale'):
        ob.keyframe_insert(data_path=path,frame=frame)


def animate_location(ob, values, baseline, curve_mode):
    for frame,dx,dz in values:
        ob.location=(baseline[0]+dx,baseline[1],baseline[2]+dz)
        ob.keyframe_insert(data_path='location',frame=frame)
    set_interpolation(ob,curve_mode)


def rig_and_targets(variant):
    bpy.ops.object.armature_add(enter_editmode=True, location=(0,0,0))
    rig=bpy.context.object
    rig.name='PROOF_RIG'
    arm=rig.data
    arm.name='PROOF_LEG_ARMATURE'
    # Remove default edit bone.
    for b in list(arm.edit_bones):
        arm.edit_bones.remove(b)
    for side,x in POSITIONS.items():
        thigh=arm.edit_bones.new(side+'_THIGH')
        thigh.head=(x,0,0)
        thigh.tail=(x,-0.10,-0.50)
        shin=arm.edit_bones.new(side+'_SHIN')
        # Intentional small rest-knee bend (Y<0) to avoid collinear IK singularity.
        # V008 first native run: perfectly straight rest chain missed target by 0.06m.
        shin.head=(x,-0.10,-0.50)
        shin.tail=(x,0,-1.04)
        shin.parent=thigh
        shin.use_connect=True
    bpy.ops.object.mode_set(mode='OBJECT')
    rig.location=(0,0,1.12)
    animate_location(rig,KEYS,(0,0,1.12), 'STEP' if variant=='STEP' else 'SPLINE')

    mover=None
    if variant=='BAD_PARENT':
        mover=bpy.data.objects.new('WRONG_ROOT_PARENT',None)
        bpy.context.collection.objects.link(mover)
        animate_location(mover,KEYS,(0,0,0),'SPLINE')

    targets={}
    for side,x in POSITIONS.items():
        target=bpy.data.objects.new(side+'_WORLD_FOOT_TARGET',None)
        bpy.context.collection.objects.link(target)
        target.location=(x,0,FOOT_HEIGHT)
        target.empty_display_size=0.10
        if mover is not None:
            # World at first frame stays identical, but now the target inherits root motion.
            target.parent=mover
        targets[side]=target
        c=rig.pose.bones[side+'_SHIN'].constraints.new(type='IK')
        c.name=side+'_NATIVE_IK_CHAIN_2'
        c.target=target
        c.chain_count=2
        c.use_tail=True
        c.use_stretch=False
        c.iterations=100
    return rig,targets


def get_positions(rig, targets, frame):
    sc=bpy.context.scene
    sc.frame_set(frame)
    deps=bpy.context.evaluated_depsgraph_get()
    rig_eval=rig.evaluated_get(deps)
    outputs={}
    for side,target in targets.items():
        pb=rig_eval.pose.bones[side+'_SHIN']
        # evaluated final pose (including IK) is in armature object space
        toe=rig_eval.matrix_world @ pb.tail
        tgt=target.evaluated_get(deps).matrix_world.translation
        outputs[side]={
            'tip':[round(v,7) for v in toe],
            'target':[round(v,7) for v in tgt],
            'tip_error_m':round((toe-tgt).length,8),
        }
    return outputs


def add_look():
    scene=bpy.context.scene
    scene.render.engine='BLENDER_WORKBENCH'
    scene.display.shading.light='STUDIO'
    scene.display.shading.color_type='MATERIAL'
    scene.render.resolution_x=480
    scene.render.resolution_y=320
    scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG'
    bpy.ops.mesh.primitive_cube_add(size=1.0,location=(0,0,-0.06))
    floor=bpy.context.object;floor.name='GROUND'
    floor.scale=(3,3,0.10)
    floor.data.materials.append(material('FLOOR_MAT',(0.28,0.32,0.35,1)))
    camera_data=bpy.data.cameras.new('CAMERA_DATA')
    camera=bpy.data.objects.new('CAMERA',camera_data)
    scene.collection.objects.link(camera)
    camera.location=(2.65,-4.3,2.10)
    look=Vector((0,0,0.70))
    camera.rotation_euler=(look-camera.location).to_track_quat('-Z','Y').to_euler()
    camera_data.type='ORTHO'
    camera_data.ortho_scale=3.30
    scene.camera=camera


def make_visuals(rig, targets):
    objs={}
    for side in POSITIONS:
        objs[side+'_THIGH']=proxy_link(side+'_THIGH_PROXY',0.075,(0.33,0.54,0.75,1))
        objs[side+'_SHIN']=proxy_link(side+'_SHIN_PROXY',0.062,(0.69,0.80,0.89,1))
        objs[side+'_FOOT']=shape_sphere(side+'_FOOT_PROXY',0.095,(0.2,0.8,0.36,1))
    body=proxy_link('TORSO_PROXY',0.15,(0.7,0.45,0.35,1))
    head=shape_sphere('HEAD_PROXY',0.18,(0.9,0.67,0.50,1))
    for frame in range(1,LAST+1):
        bpy.context.scene.frame_set(frame)
        deps=bpy.context.evaluated_depsgraph_get()
        erig=rig.evaluated_get(deps)
        for side in POSITIONS:
            for part,bone in [('THIGH',side+'_THIGH'),('SHIN',side+'_SHIN')]:
                pb=erig.pose.bones[bone]
                a=erig.matrix_world @ pb.head
                b=erig.matrix_world @ pb.tail
                place_segment(objs[side+'_'+part],a,b,frame)
            foot=objs[side+'_FOOT']
            foot.location=targets[side].evaluated_get(deps).matrix_world.translation
            foot.keyframe_insert(data_path='location',frame=frame)
        pelvis=erig.matrix_world @ Vector((0,0,0))
        place_segment(body,pelvis, pelvis+Vector((0,0,0.43)), frame)
        head.location=pelvis+Vector((0,0,0.67))
        head.keyframe_insert(data_path='location',frame=frame)
    return objs


def result_for_frames(variant, rig, targets):
    samples=[]
    first=None
    max_tip_error=0.0
    max_foot_target_drift=0.0
    for f in range(1,LAST+1):
        points=get_positions(rig,targets,f)
        if first is None:
            first={side:Vector(points[side]['target']) for side in POSITIONS}
        for side in POSITIONS:
            max_tip_error=max(max_tip_error,points[side]['tip_error_m'])
            max_foot_target_drift=max(max_foot_target_drift,(Vector(points[side]['target'])-first[side]).length)
        if f in (1,10,24,48,72,96):
            samples.append({'frame':f,'legs':points})
    # Validate *both* solver tip-to-target error and foot planting.
    # Do not equate target-locked with actual foot mesh ground contact.
    err_limit=0.03
    expected_drift=(0.0 if variant!='BAD_PARENT' else 0.15)
    should_pass=(max_tip_error<err_limit and
       ((max_foot_target_drift<1e-5) if variant!='BAD_PARENT' else (max_foot_target_drift>expected_drift)))
    return {'variant':variant,'fps':FPS,'frames':LAST,'blender_version':bpy.app.version_string,
            'max_ik_tip_error_m':round(max_tip_error,8),
            'max_foot_target_drift_m':round(max_foot_target_drift,8),
            'negative_control':variant=='BAD_PARENT',
            'expected_behavior_pass':bool(should_pass),
            'samples':samples,'artistic_review':'NOT_REVIEWED',
            'scope':'original 3D bone-chain, not skinned mesh, COM, or GS001'}


def build(variant,outdir):
    if tuple(bpy.app.version[:3])!=(5,2,2):
        raise RuntimeError('Must use verified Blender 5.2.2; got '+bpy.app.version_string)
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    outdir.mkdir(parents=True,exist_ok=True)
    sc=bpy.context.scene
    sc.frame_start=1; sc.frame_end=LAST
    sc.render.fps=FPS
    rig,targets=rig_and_targets(variant)
    add_look()
    make_visuals(rig, targets)
    res=result_for_frames(variant,rig,targets)
    if not res['expected_behavior_pass']:
        raise RuntimeError('Native solver/foot-target assertions failed: '+json.dumps(res)[:6000])
    bpy.context.scene.frame_set(1)
    bpy.ops.wm.save_as_mainfile(filepath=str(outdir/(variant+'.blend')))
    (outdir/(variant+'_BUILD_RECEIPT.json')).write_text(json.dumps(res,indent=2))
    print('BUILD PASS (fresh-open still required): '+variant)


def verify(variant,outdir):
    if tuple(bpy.app.version[:3])!=(5,2,2):
        raise RuntimeError('Incorrect Blender version on fresh reopen')
    rig=bpy.data.objects.get('PROOF_RIG')
    if not rig or rig.type!='ARMATURE': raise RuntimeError('Original armature not in reopened file')
    targets={side:bpy.data.objects.get(side+'_WORLD_FOOT_TARGET') for side in POSITIONS}
    if any(v is None for v in targets.values()):raise RuntimeError('Foot targets missing')
    res=result_for_frames(variant,rig,targets)
    if not res['expected_behavior_pass']:
        raise RuntimeError('Fresh reopened rig did not meet expected behavior')
    old=json.loads((outdir/(variant+'_BUILD_RECEIPT.json')).read_text())
    if res!=old: raise RuntimeError('Fresh scene evaluated data differs from build receipt')
    sc=bpy.context.scene
    # Preview samples only: original Blender render of original rig-driven proxy.
    for n in (1,24,48,72,96):
        sc.frame_set(n)
        sc.render.filepath=str(outdir/(variant+'_frame_%04d.png'%n))
        bpy.ops.render.render(write_still=True)
    (outdir/(variant+'_REOPEN_PASS.json')).write_text(json.dumps(res,indent=2))
    print('FRESH_REOPEN_PASS: '+variant)


if __name__=='__main__':
    mode,variant,output=args()
    if mode=='build':build(variant,output)
    else:verify(variant,output)