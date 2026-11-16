#!/usr/bin/env python3
"""V011: original native Blender 5.2.2 facial-closeup acting laboratory.
A/B intention timing + deliberately broken upper-lid shape-key binding.
Actual shape-key mesh evaluation, native Damped Track gaze, camera and fresh reopen.
No GS001 content. Mechanical proof only: NO claim that the acting is art approved.
Usage: blender -b --factory-startup --python native_facial_closeup_v011.py -- build THOUGHTFUL /path
       blender -b /path/THOUGHTFUL.blend --python native_facial_closeup_v011.py -- verify THOUGHTFUL /path
"""
import bpy, sys, json, math
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

FPS=24
LAST=72
VALID=('THOUGHTFUL','SYNCHRONIZED','BAD_LID_BIND')
EYEX={'L':-.295,'R':.295}
NX,ROWS=17,5


def args():
    if '--' not in sys.argv: raise RuntimeError('Missing -- mode variant out')
    p=sys.argv[sys.argv.index('--')+1:]
    if len(p)!=3 or p[0] not in ('build','verify') or p[1] not in VALID:
        raise RuntimeError('Invalid arguments '+repr(p))
    return p[0],p[1],Path(p[2]).resolve()


def material(n,c):
    m=bpy.data.materials.new(n)
    m.diffuse_color=(*c,1)
    return m


def sph(name,loc,scale,mat,parent=None,segs=32,rings=20):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segs,ring_count=rings,location=(0,0,0))
    ob=bpy.context.object;ob.name=name;ob.scale=scale
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    ob.location=loc
    if parent is not None: ob.parent=parent
    ob.data.materials.append(mat)
    return ob


def empty(name,loc=(0,0,0),parent=None):
    ob=bpy.data.objects.new(name,None)
    bpy.context.collection.objects.link(ob)
    ob.empty_display_size=.08
    if parent is not None:ob.parent=parent
    ob.location=loc
    return ob


def curves(obj):
    ad=getattr(obj,'animation_data',None)
    if not ad or not ad.action:raise RuntimeError('No action for '+obj.name)
    action=ad.action
    out=[]
    try:out=list(action.fcurves)
    except (TypeError,AttributeError):pass
    if not out:
        for lay in action.layers:
            for st in lay.strips:
                for bag in getattr(st,'channelbags',[]):out+=list(bag.fcurves)
    if not out:raise RuntimeError('No fcurves for '+obj.name)
    for c in out:
        for k in c.keyframe_points:
            k.interpolation='BEZIER'
            k.handle_left_type=k.handle_right_type='AUTO_CLAMPED'


def add_lid(side,upper,parent,mat):
    """Open aperture covers 0.235m; fully closed upper & lower free edges meet at z=0.103."""
    x0=EYEX[side]
    top,bottom=.310,-.103
    edge_open=.237 if upper else .000
    edge_close=.103
    vv=[];faces=[];closed=[]
    for j in range(ROWS):
        u=j/(ROWS-1)
        for i in range(NX):
            h=(i/(NX-1)-.5)*.42
            # Flat ribbons are intentionally synthetic but real native Blender meshes.
            v=(top*(1-u)+edge_open*u) if upper else (edge_open*(1-u)+bottom*u)
            vclose=(top*(1-u)+edge_close*u) if upper else (edge_close*(1-u)+bottom*u)
            vv.append((x0+h,-.707,v))
            closed.append((x0+h,-.707,vclose))
    for j in range(ROWS-1):
        for i in range(NX-1):
            a=j*NX+i;b=a+1;c=b+NX;d=a+NX
            faces.append((a,b,c,d))
    mesh=bpy.data.meshes.new(side+('_UPPER_LID_MESH' if upper else '_LOWER_LID_MESH'))
    mesh.from_pydata(vv,[],faces);mesh.update()
    ob=bpy.data.objects.new(side+('_UPPER_LID' if upper else '_LOWER_LID'),mesh)
    bpy.context.collection.objects.link(ob)
    ob.parent=parent;ob.data.materials.append(mat)
    ob.shape_key_add(name='Basis',from_mix=False)
    block=ob.shape_key_add(name='BLINK',from_mix=False)
    for i,p in enumerate(closed):block.data[i].co=p
    return ob


def smile_mesh(parent,ink):
    nv=17; verts=[];faces=[]
    for r in range(2):
        for i in range(nv):
            x=(i/(nv-1)-.5)*.36
            z=-.365-.012*r-.035*(1-(x/.18)**2)
            verts.append((x,-.559,z))
    for i in range(nv-1):faces.append((i,i+1,i+nv+1,i+nv))
    mesh=bpy.data.meshes.new('MOUTH_SURFACE');mesh.from_pydata(verts,[],faces);mesh.update()
    ob=bpy.data.objects.new('MOUTH_SMILE_NATIVE',mesh);bpy.context.collection.objects.link(ob)
    ob.parent=parent;ob.data.materials.append(ink)
    ob.shape_key_add(name='Basis',from_mix=False)
    kb=ob.shape_key_add(name='SMILE',from_mix=False)
    for r in range(2):
        for i in range(nv):
            x=verts[i][0];ext=(abs(x)/.18)**1.65
            v=kb.data[r*nv+i].co
            v.z+=.078*ext-.015*(1-ext)
    return ob


def key_values(block,points):
    for f,v in points:
        block.value=v;block.keyframe_insert(data_path='value',frame=f)


def build_scene(variant):
    skin=material('SKIN_HONEY',(.77,.51,.36));hair=material('DARK_HAIR',(.18,.13,.13))
    white=material('EYE_IVORY',(.93,.91,.83));iris=material('IRIS_BLUE',(.19,.47,.55))
    pupil=material('PUPIL_INK',(.08,.11,.15));brow=material('BROW_DARK',(.24,.17,.14))
    cloth=material('CLOTH_TEAL',(.17,.37,.40));pink=material('FLOWER_PINK',(.88,.37,.51))
    green=material('STEM',(.25,.45,.25));yellow=material('CENTER',(.98,.68,.2))
    head=empty('HEAD_CTRL')
    sph('FACE_SURFACE',(0,0,0),(.68,.54,.78),skin,head)
    sph('HAIR_CAP',(0,.09,.52),(.70,.49,.28),hair,head)
    sph('LEFT_EAR',(-.66,0,-.07),(.11,.13,.18),skin,head)
    sph('RIGHT_EAR',(.66,0,-.07),(.11,.13,.18),skin,head)
    sph('NOSE',(0,-.556,-.115),(.105,.12,.16),skin,head)
    sph('NECK',(0,.03,-.74),(.18,.21,.34),skin)
    sph('SHOULDERS',(0,.09,-1.01),(.91,.36,.40),cloth)
    lips=smile_mesh(head,brow)
    aim_target=empty('NATIVE_GAZE_WORLD_TARGET',(0,-3.5,.07))
    for side,x in EYEX.items():
        sph(side+'_EYE',(x,-.530,.10),(.207,.127,.165),white,head)
        pivot=empty(side+'_EYE_AIM',(x,-.530,.10),head)
        constraint=pivot.constraints.new(type='DAMPED_TRACK')
        constraint.name='NATIVE_EYE_TARGET_TRACK'
        constraint.target=aim_target
        constraint.track_axis='TRACK_NEGATIVE_Y'
        sph(side+'_IRIS',(0,-.136,0),(.085,.024,.092),iris,pivot)
        sph(side+'_PUPIL',(0,-.162,0),(.042,.012,.059),pupil,pivot)
        brow_ob=sph(side+'_BROW',(x,-.618,.340),(.193,.032,.035),brow,head)
        # brow anticipation/release is subtle, may be reviewed independently.
        for f,v in ((1,.340),(20,.340),(40,.372),(LAST,.358)):
            brow_ob.location.z=v;brow_ob.keyframe_insert(data_path='location',frame=f)
        curves(brow_ob)
        up=add_lid(side,True,head,skin)
        low=add_lid(side,False,head,skin)
        if variant=='BAD_LID_BIND':
            # Deliberately disable the upper lid's deformation despite keyed 1.0 values.
            up.data.shape_keys.key_blocks['BLINK'].mute=True
    # A flower anchored in the camera-right foreground, no handoff or grasp claimed.
    bpy.ops.mesh.primitive_cylinder_add(vertices=12,radius=.017,depth=.28,location=(.99,-.36,-.48))
    bpy.context.object.name='SINGLE_FLOWER_STEM';bpy.context.object.data.materials.append(green)
    for i in range(5):
        ang=i*math.tau/5
        sph('FLOWER_PETAL_'+str(i),(.99+.09*math.cos(ang),-.36+.08*math.sin(ang),-.315),(.09,.035,.07),pink)
    sph('FLOWER_CENTER',(.99,-.425,-.315),(.05,.028,.05),yellow)
    # Locked shot from front, comfortable space for ears and forelock.
    sc=bpy.context.scene
    camdata=bpy.data.cameras.new('ACTING_CLOSEUP_CAMERA');camera=bpy.data.objects.new('ACTING_CLOSEUP_CAMERA',camdata)
    bpy.context.collection.objects.link(camera)
    camera.location=(0,-4.8,.05)
    camera.rotation_euler=(Vector((0,0,-.02))-camera.location).to_track_quat('-Z','Y').to_euler()
    camdata.type='ORTHO';camdata.ortho_scale=2.78;sc.camera=camera
    sc.render.engine='BLENDER_WORKBENCH'
    sc.display.shading.light='STUDIO'
    sc.display.shading.color_type='MATERIAL'
    sc.display.shading.show_cavity=True
    sc.display.shading.show_shadows=True
    sc.render.resolution_x=640;sc.render.resolution_y=480
    sc.render.resolution_percentage=100
    sc.render.image_settings.file_format='PNG'
    sc.render.film_transparent=False
    sc.camera.data.lens=50
    # Eying the flower is an authored story beat, not a claim of human biological law.
    if variant=='SYNCHRONIZED':
        eye=(18,35); h=(18,35); smile=(18,35)
        # blink at the same early phase
        upper=[(1,0),(18,0),(23,1),(26,1),(31,0),(LAST,0)]
        lower=[(1,0),(19,0),(24,1),(26,1),(30,0),(LAST,0)]
    else:
        eye=(12,21);h=(31,47);smile=(43,65)
        upper=[(1,0),(25,0),(30,1),(34,1),(39,0),(LAST,0)]
        lower=[(1,0),(26,0),(31,1),(34,1),(38,0),(LAST,0)]
    for f,x in ((1,0),(eye[0],0),(eye[1],.89),(LAST,.89)):
        aim_target.location.x=x;aim_target.keyframe_insert(data_path='location',frame=f)
    curves(aim_target)
    for f,z in ((1,0),(h[0],0),(h[1],-.075),(LAST,-.075)):
        head.rotation_euler[0]=z;head.keyframe_insert(data_path='rotation_euler',frame=f)
    curves(head)
    key_values(lips.data.shape_keys.key_blocks['SMILE'],[(1,0),(smile[0],0),(smile[1],1),(LAST,1)])
    curves(lips.data.shape_keys)
    for side in EYEX:
        for suffix,pts in [('UPPER_LID',upper),('LOWER_LID',lower)]:
            o=bpy.data.objects[side+'_'+suffix]
            key_values(o.data.shape_keys.key_blocks['BLINK'],pts)
            curves(o.data.shape_keys)


def eval_lid_z(obj,upper,dp):
    ob=obj.evaluated_get(dp)
    me=ob.to_mesh()
    try:
        idx=(ROWS-1)*NX+NX//2 if upper else NX//2
        return float((ob.matrix_world @ me.vertices[idx].co).z)
    finally:
        ob.to_mesh_clear()


def sample_at(frame,variant):
    sc=bpy.context.scene
    sc.frame_set(frame)
    dg=bpy.context.evaluated_depsgraph_get()
    target=bpy.data.objects['NATIVE_GAZE_WORLD_TARGET'].evaluated_get(dg)
    result={'frame':frame,'eye_target_x':round(target.matrix_world.translation.x,6),'apertures':{},'eye_alignment':{},'shape_values':{}}
    for side in EYEX:
        u=bpy.data.objects[side+'_UPPER_LID'];l=bpy.data.objects[side+'_LOWER_LID']
        zup=eval_lid_z(u,True,dg);zlow=eval_lid_z(l,False,dg)
        gap=zup-zlow
        result['apertures'][side]=round(gap,7)
        result['shape_values'][side+'_UP']=round(float(u.data.shape_keys.key_blocks['BLINK'].value),6)
        result['shape_values'][side+'_LOW']=round(float(l.data.shape_keys.key_blocks['BLINK'].value),6)
        pivot=bpy.data.objects[side+'_EYE_AIM'].evaluated_get(dg)
        axis=pivot.matrix_world.to_quaternion() @ Vector((0,-1,0))
        direction=(target.matrix_world.translation-pivot.matrix_world.translation).normalized()
        result['eye_alignment'][side]=round(axis.dot(direction),7)
    result['smile']=round(float(bpy.data.objects['MOUTH_SMILE_NATIVE'].data.shape_keys.key_blocks['SMILE'].value),6)
    result['head_pitch']=round(float(bpy.data.objects['HEAD_CTRL'].rotation_euler[0]),6)
    return result


def evaluate(variant):
    if tuple(bpy.app.version)!=(5,2,2):raise RuntimeError('Exact Blender 5.2.2 required')
    samples={str(f):sample_at(f,variant) for f in (1,18,24,25,32,34,48,65,72)}
    baseline=samples['1']
    if not all(.18<baseline['apertures'][s]<.28 for s in EYEX):
        raise RuntimeError('Open aperture baseline invalid '+repr(baseline))
    for f,s in samples.items():
        if any(v<.997 for v in s['eye_alignment'].values()):
            raise RuntimeError('Native Damped Track constraint not aligned at '+f+' '+repr(s['eye_alignment']))
        if any(v < -.015 for v in s['apertures'].values()):
            raise RuntimeError('Upper/lower lids have excessive penetration at '+f)
        if any(v > .29 for v in s['apertures'].values()):
            raise RuntimeError('Lid rupture '+f)
    peak_frame=25 if variant=='SYNCHRONIZED' else 32
    atblink=samples[str(peak_frame)]
    assert all(atblink['shape_values'][side+'_UP']>.99 and atblink['shape_values'][side+'_LOW']>.99 for side in EYEX), 'Blink anim values should peak at authored peak frame'
    max_blink_gap=max(atblink['apertures'].values())
    if variant=='BAD_LID_BIND':
        if not .09<max_blink_gap<.17:raise RuntimeError('Negative fixture did not expose muted upper lid '+str(max_blink_gap))
        for side in EYEX:
            if not bpy.data.objects[side+'_UPPER_LID'].data.shape_keys.key_blocks['BLINK'].mute:
                raise RuntimeError('Unexpected upper eyelid not muted')
    else:
        if max_blink_gap>.012:raise RuntimeError('Proper closed aperture mismatch '+str(max_blink_gap))
        for side in EYEX:
            if bpy.data.objects[side+'_UPPER_LID'].data.shape_keys.key_blocks['BLINK'].mute:
                raise RuntimeError('Upper eyelid incorrectly muted')
    # Separate causal beat across positive A/B:
    if variant!='SYNCHRONIZED':
        if not samples['24']['eye_target_x']>.8 or samples['24']['smile']!=0.0:
            raise RuntimeError('Thoughtful gaze lead / intention hold missing')
    else:
        if not samples['24']['smile']>0.05:
            raise RuntimeError('Synchronized smile response missing')
    if abs(samples['72']['smile']-1)>1e-6 or samples['1']['smile']!=0.0:
        raise RuntimeError('Smile endpoint mismatched')
    # Native camera projection gate from four extreme head / shoulders positions.
    sc=bpy.context.scene;cam=sc.camera
    margin=1
    for f in (1,24,32,48,72):
        sc.frame_set(f);dg=bpy.context.evaluated_depsgraph_get()
        obj=bpy.data.objects['HEAD_CTRL'].evaluated_get(dg)
        for q in (Vector((-.78,0,0)),Vector((.78,0,0)),Vector((0,0,.87)),Vector((0,0,-.84))):
            pos=obj.matrix_world @ q
            p=world_to_camera_view(sc,cam,pos)
            margin=min(margin,p.x,1-p.x,p.y,1-p.y)
            if p.z<=0 or not (.045<p.x<.955 and .045<p.y<.955):
                raise RuntimeError('CAMERA_CROP frame='+str(f)+' proj='+str(tuple(p)))
    return {'status':'NATIVE_FACIAL_TECHNICAL_PASS','variant':variant,'blender':bpy.app.version_string,
            'frames':LAST,'fps':FPS,'lid_mesh_vertices_per_piece':NX*ROWS,
            'native_shape_key_rig':True,'gaze_constraint':'DAMPED_TRACK',
            'blink_peak_frame':peak_frame,'max_evaluated_blink_gap_m':round(max_blink_gap,7),
            'original_aperture_m':baseline['apertures']['L'],
            'minimum_normalized_camera_margin':round(margin,7),'samples':samples,
            'negative_control_expected':variant=='BAD_LID_BIND',
            'artistic_approval':'NOT_REVIEWED','anatomical_face_rig':'STYLIZED_PROXY_NOT_APPROVED','GS001':'NOT_TOUCHED'}


def build(variant,out):
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    sc=bpy.context.scene;sc.frame_start=1;sc.frame_end=LAST;sc.render.fps=FPS
    build_scene(variant)
    receipt=evaluate(variant)
    sc.frame_set(1)
    out.mkdir(parents=True,exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(out/(variant+'.blend')))
    (out/(variant+'_BUILD.json')).write_text(json.dumps(receipt,indent=2))
    print('FACIAL_BUILD_PASS',variant,json.dumps({k:v for k,v in receipt.items() if k!='samples'}))


def verify(variant,out):
    old=json.loads((out/(variant+'_BUILD.json')).read_text())
    new=evaluate(variant)
    if old!=new:raise RuntimeError('Fresh-reopen semantic mismatch')
    sc=bpy.context.scene
    for f in (1,18,24,32,48,72):
        sc.frame_set(f)
        sc.render.filepath=str(out/f'{variant}_frame_{f:04d}.png')
        bpy.ops.render.render(write_still=True)
    (out/(variant+'_REOPEN.json')).write_text(json.dumps(new,indent=2))
    print('FACIAL_REOPEN_PASS',variant)

if __name__=='__main__':
    m,v,o=args()
    if m=='build':build(v,o)
    else:verify(v,o)