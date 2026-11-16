#!/usr/bin/env python3
"""Original native Blender 5.2.2 spherical eyelid-surface mechanics fixture.

DO NOT infer production facial anatomy from these deliberately simplified ribbons.
Guide empties evaluate Blender LIMIT_DISTANCE; ribbon meshes evaluate native
ShapeKey+Shrinkwrap. The two mechanisms are verified separately, NOT wired into
one professional face-control rig. Does not reference or modify GS001 assets.
"""
import bpy, sys, os, math, json, hashlib
from pathlib import Path
from mathutils import Vector

VERSIONS=("ATTACHED", "FLOATING", "UNLOCKED_GUIDE")
RADIUS=0.52
OFFSET=0.014
GUIDE_RADIUS=RADIUS+OFFSET
NX,NV=25,9
FPS,FRAMES=24,72
POSES=(1,20,32,40,55,72)
ROOT="EYE_SURFACE_MECHANISM_V013"

def ease(t):
    t=min(1.,max(0.,t));return t*t*(3-2*t)

def mat(name,color):
    m=bpy.data.materials.new(name)
    m.diffuse_color=(*color,1)
    return m

def ellipsoid(name,loc,scale,material,segments=64, rings=32):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments,ring_count=rings,radius=1, location=loc)
    o=bpy.context.object; o.name=name; o.scale=scale
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    o.data.materials.append(material)
    for poly in o.data.polygons: poly.use_smooth=True
    return o

def geometry(lid):
    verts=[]; faces=[]; upper=lid=='UPPER'
    for i in range(NX):
        x=(i/(NX-1)*2.-1.)*.37
        h=math.sqrt(max(0.,1.-(x/.43)**2))
        inner=(.205 if upper else -.175)*h
        outer=(.355 if upper else -.335)*h
        for j in range(NV):
            u=j/(NV-1)
            z=inner+(outer-inner)*u
            verts.append((x,-.565,z))
    for i in range(NX-1):
        for j in range(NV-1):
            a=i*NV+j
            faces.append((a,a+NV,a+NV+1,a+1) if upper else (a,a+1,a+NV+1,a+NV))
    return verts,faces

def make_lid(lid,skin,globe,variant):
    vertices,faces=geometry(lid)
    m=bpy.data.meshes.new(lid+'_RIBBON');m.from_pydata(vertices,[],faces);m.update()
    o=bpy.data.objects.new(lid+'_SKIN_RIBBON',m);bpy.context.collection.objects.link(o)
    o.data.materials.append(skin)
    for polygon in o.data.polygons:polygon.use_smooth=True
    o.shape_key_add(name='Basis',from_mix=False)
    blink=o.shape_key_add(name='BLINK',from_mix=False)
    follow=o.shape_key_add(name='EYE_FOLLOW',from_mix=False)
    for idx,v in enumerate(m.vertices):
        pos=v.co.copy(); row=idx%NV
        t=row/(NV-1)
        # Only the eyelid margin travels the full closing distance; skin near
        # orbital attachment stays put. Art-directed falloff, NOT anatomy.
        w=(1-t)**1.7
        blink.data[idx].co=(pos.x,pos.y,pos.z*(1-w))
        follow.data[idx].co=(pos.x,pos.y,pos.z+.043*(1-t)**2)
    # Blender shape key values, not mock deformation.
    for frame,val in ((1,0),(23,0),(32,1),(36,1),(43,0),(72,0)):
        blink.value=val;blink.keyframe_insert(data_path='value',frame=frame)
    for frame,val in ((1,0),(14,0),(23,1),(45,1),(62,0),(72,0)):
        follow.value=val;follow.keyframe_insert(data_path='value',frame=frame)
    sw=o.modifiers.new('SPHERICAL_SURFACE_FOLLOW','SHRINKWRAP')
    sw.target=globe;sw.wrap_method='NEAREST_SURFACEPOINT'
    sw.wrap_mode='ABOVE_SURFACE';sw.offset=OFFSET
    if variant=='FLOATING':
        sw.show_viewport=False;sw.show_render=False
    o['guide_mechanism']='independent demonstration; not driving this ribbon'
    return o

def guide(name,x,z,center,variant):
    o=bpy.data.objects.new(name,None)
    bpy.context.collection.objects.link(o)
    o.empty_display_type='SPHERE';o.empty_display_size=.030
    o.hide_render=True
    c=o.constraints.new('LIMIT_DISTANCE')
    c.target=center;c.distance=GUIDE_RADIUS
    c.limit_mode='LIMITDIST_ONSURFACE';c.use_transform_limit=True
    if variant=='UNLOCKED_GUIDE':c.influence=0.0
    for f,p in ((1,0),(20,.030),(32,.065),(40,.085),(55,-.025),(72,0)):
        o.location=(x+p,-.565,z + p*.5)
        o.keyframe_insert(data_path='location',frame=f)
    return o

def build(variant,out):
    assert variant in VERSIONS
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene=bpy.context.scene
    scene.render.engine='BLENDER_WORKBENCH'
    scene.render.resolution_x=640;scene.render.resolution_y=420;scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG'
    scene.render.film_transparent=False
    scene.render.fps=FPS;scene.frame_start=1;scene.frame_end=FRAMES
    scene.render.engine='BLENDER_WORKBENCH'
    scene.display.shading.light='STUDIO';scene.display.shading.color_type='MATERIAL';scene.display.shading.show_shadows=True
    scene.display.shading.show_cavity=True
    if scene.world is None:
        scene.world=bpy.data.worlds.new('EYE_LAB_WORLD')
    scene.world.color=(.11,.12,.15)
    skin=mat('Skin_Warm',(.71,.44,.33))
    eye=mat('Eyeball_Ivory',(.93,.91,.82))
    iris=mat('Iris_Deep',(.12,.27,.27))
    pupil=mat('Pupil_Black',(.03,.035,.06))
    face=mat('Face_Clay',(.48,.30,.25))
    ellipsoid('FACE_CONTEXT',(0,.23,0),(.79,.43,.78),face)
    globe=ellipsoid('EYEBALL_SPHERE',(0,0,0),(RADIUS,)*3,eye,segments=96,rings=48)
    globe['radius_m']=RADIUS
    center=bpy.data.objects.new('EYE_CENTER',None);bpy.context.collection.objects.link(center)
    lidup=make_lid('UPPER',skin,globe,variant)
    lidlow=make_lid('LOWER',skin,globe,variant)
    for tag,x,z in [('L',-.24,.12),('C',0.,.13),('R',.24,.12)]:
        guide('UPPER_GUIDE_'+tag,x,z,center,variant)
    # Iris and pupil move over visible sphere; this is a synthetic animation,
    # not measured biological gaze or a true embedded ophthalmic mesh.
    ir=ellipsoid('IRIS',(0,-.523,-.015),(.133,.017,.133),iris,segments=48,rings=24)
    pu=ellipsoid('PUPIL',(0,-.543,-.015),(.065,.009,.065),pupil,segments=40,rings=20)
    for f,k in ((1,0),(12,0),(24,1),(45,1),(60,0),(72,0)):
        x=.10*k;z=.043*k-.015
        y=-math.sqrt(max(.01,RADIUS**2-x*x-z*z))
        ir.location=(x,y-.008,z);pu.location=(x,y-.028,z)
        ir.keyframe_insert(data_path='location',frame=f);pu.keyframe_insert(data_path='location',frame=f)
    # Camera: look straight into eye; no production character or borrowed art.
    cam_data=bpy.data.cameras.new('CAMERA_DATA');cam=bpy.data.objects.new('CAMERA',cam_data)
    bpy.context.collection.objects.link(cam)
    cam.location=(0,-4.4,.04)
    direction=Vector((0,0,0))-cam.location
    cam.rotation_euler=direction.to_track_quat('-Z','Y').to_euler()
    cam_data.type='ORTHO';cam_data.ortho_scale=1.65
    scene.camera=cam
    scene['proof_id']=ROOT;scene['variant']=variant
    scene.frame_set(1)
    out.mkdir(parents=True,exist_ok=True)
    report=evaluate(variant)
    (out/f'{variant}_BUILD.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    if not report['expected_gate_pass']:
        raise RuntimeError('native geometry failed: '+json.dumps(report)[:7000])
    bpy.ops.wm.save_as_mainfile(filepath=str((out/f'{variant}.blend').absolute()))
    print('V013_BUILD_PASS',variant,json.dumps({k:v for k,v in report.items() if k!='samples'}))

def evaluated_vertices(obj,deps):
    eo=obj.evaluated_get(deps)
    me=eo.to_mesh()
    try: return [eo.matrix_world @ v.co.copy() for v in me.vertices]
    finally:eo.to_mesh_clear()

def evaluate(variant):
    scene=bpy.context.scene
    assert scene['proof_id']==ROOT and scene['variant']==variant
    up=bpy.data.objects['UPPER_SKIN_RIBBON']
    lo=bpy.data.objects['LOWER_SKIN_RIBBON']
    guide_objs=[bpy.data.objects['UPPER_GUIDE_'+s] for s in ('L','C','R')]
    assert up.modifiers['SPHERICAL_SURFACE_FOLLOW'].type=='SHRINKWRAP'
    assert up.data.shape_keys.key_blocks.get('BLINK')
    assert all(e.constraints[0].type=='LIMIT_DISTANCE' for e in guide_objs)
    all_radial=[];all_guide=[];samples=[]
    for f in POSES:
        scene.frame_set(f);deps=bpy.context.evaluated_depsgraph_get()
        upper=evaluated_vertices(up,deps);lower=evaluated_vertices(lo,deps)
        # Radial surface distance to the ideal eyeball radius+small skin offset;
        # faceted target and normals mean this is approximate, not collision proof.
        er=max(abs(v.length-GUIDE_RADIUS) for v in upper+lower)
        ge=max(abs(e.evaluated_get(deps).matrix_world.translation.length-GUIDE_RADIUS) for e in guide_objs)
        all_radial.append(er);all_guide.append(ge)
        mid=NX//2
        margin_gap=(upper[mid*NV]-lower[mid*NV]).length
        samples.append({'frame':f,'radial_error_max_m':round(er,7),
                        'guide_radial_error_max_m':round(ge,7),
                        'lid_middle_aperture_m':round(margin_gap,7),
                        'blink':round(float(up.data.shape_keys.key_blocks['BLINK'].value),5)})
    mxr=max(all_radial);mxg=max(all_guide)
    close=[s['lid_middle_aperture_m'] for s in samples if s['frame']==32][0]
    opening=[s['lid_middle_aperture_m'] for s in samples if s['frame']==1][0]
    if variant=='ATTACHED':passing=mxr<.025 and mxg<.0002 and close<.020 and opening>.30
    elif variant=='FLOATING':passing=mxr>.075 and mxg<.0002 and close<.020 and opening>.30
    else:passing=mxr<.025 and mxg>.060 and close<.020 and opening>.30
    return {'proof':ROOT,'variant':variant,'runtime':bpy.app.version_string,
            'geometry_mechanism':'native Shrinkwrap surface modifier on shape-key ribbon',
            'guide_mechanism':'native Limit Distance constraint ON_SURFACE',
            'guide_drives_ribbon':False,
            'max_ribbon_radial_error_m':round(mxr,8),
            'max_guide_radial_error_m':round(mxg,8),
            'open_aperture_m':opening,'closed_aperture_m':close,
            'expected_gate_pass':bool(passing),'samples':samples,
            'scope_ceiling':'mechanical spherical adhesion only, not anatomically continuous face or professional acting',
            'artistic_status':'NOT_REVIEWED','GS001':'UNTOUCHED'}

def verify(variant,out):
    expected=json.loads((out/f'{variant}_BUILD.json').read_text())
    actual=evaluate(variant)
    if expected!=actual or not actual['expected_gate_pass']:
        raise RuntimeError('FRESH_REOPEN_MISMATCH '+json.dumps({'expected':expected,'actual':actual})[:8000])
    (out/f'{variant}_REOPEN.json').write_text(json.dumps(actual,indent=2),encoding='utf-8')
    for f in (1,20,32,40,55,72):
        bpy.context.scene.frame_set(f)
        bpy.context.scene.render.filepath=str((out/f'{variant}_frame_{f:04d}.png').absolute())
        bpy.ops.render.render(write_still=True)
    print('V013_REOPEN_PASS',variant,json.dumps({k:v for k,v in actual.items() if k!='samples'}))

if __name__=='__main__':
    i=sys.argv.index('--')+1 if '--' in sys.argv else len(sys.argv)
    args=sys.argv[i:]
    if len(args)!=3:raise ValueError('usage: -- build|verify ATTACHED|FLOATING|UNLOCKED_GUIDE /path')
    mode,variant,path=args
    if mode=='build':build(variant,Path(path))
    elif mode=='verify':verify(variant,Path(path))
    else:raise ValueError(mode)