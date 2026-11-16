#!/usr/bin/env python3
"""V015: genuine Blender 5.2.2 topology and weighted facial socket microproof.

Original pedagogical annular socket with ONE mesh, native armature skinning,
corrective shape key, two negative controls. Not human face/art approval.
Build and fresh-reopen via CLI with: build|verify CONNECTED|TORN_RING|RIGID_WEIGHTS path
"""
import bpy, sys, json, math
from pathlib import Path
from collections import defaultdict, deque
from mathutils import Vector
from mathutils.bvhtree import BVHTree

VERSIONS=('CONNECTED','TORN_RING','RIGID_WEIGHTS')
N=48; RINGS=7
FPS=24; FRAMES=72
SAMPLE=(1,18,28,32,38,49,72)
TEST_ID='NATIVE_CONTIGUOUS_ORBITAL_SOCKET_V015'
MAX_CLOSE=.1695

def material(name, color):
    m=bpy.data.materials.new(name);m.diffuse_color=(*color,1.0);return m

def make_sphere(name,radius,location,m):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=64,ring_count=32,radius=radius,location=location)
    obj=bpy.context.object;obj.name=name;obj.data.materials.append(m)
    for p in obj.data.polygons:p.use_smooth=True
    return obj

def make_rig():
    arm=bpy.data.armatures.new('V015_ACTUAL_BONES')
    rig=bpy.data.objects.new('V015_FACE_ARMATURE',arm)
    bpy.context.collection.objects.link(rig)
    bpy.context.view_layer.objects.active=rig
    rig.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    for name,tail in [('UPPER_DEF',(0,.08,0)),('LOWER_DEF',(0,-.08,0)),('SOCKET',(0,.05,.0))]:
        b=arm.edit_bones.new(name);b.head=(0,0,0);b.tail=tail
        b.use_deform=True;b.use_connect=False
    bpy.ops.object.mode_set(mode='OBJECT')
    rig.select_set(False)
    for side in ['UPPER','LOWER']:
        target=bpy.data.objects.new(side+'_BLINK_TARGET',None)
        bpy.context.collection.objects.link(target)
        target.empty_display_size=.04;target.hide_render=True
        for f,amount in [(1,0),(18,0),(28,.70),(32,1),(38,1),(49,0),(72,0)]:
            target.location=(0,0,(-1 if side=='UPPER' else 1)*MAX_CLOSE*amount)
            target.keyframe_insert(data_path='location',frame=f)
        cons=rig.pose.bones[side+'_DEF'].constraints.new('COPY_LOCATION')
        cons.name='FOLLOW_BLINK_GUIDE';cons.target=target
        cons.target_space='WORLD';cons.owner_space='WORLD'
    return rig

def make_socket(variant,rig,skin):
    verts=[];faces=[];params=[]
    for r in range(RINGS):
        t=r/(RINGS-1)
        rx=.31+(.64-.31)*t
        rz=.17+(.48-.17)*t
        for i in range(N):
            theta=math.tau*i/N
            x=rx*math.cos(theta);z=rz*math.sin(theta)
            y=-.55+.045*t*t
            verts.append((x,y,z));params.append((t,theta))
    for r in range(RINGS-1):
        if variant=='TORN_RING' and r==3:continue
        for i in range(N):
            a=r*N+i;b=r*N+(i+1)%N;c=(r+1)*N+(i+1)%N;d=(r+1)*N+i
            faces.append((a,b,c,d))
    me=bpy.data.meshes.new('V015_SINGLE_ORBITAL_PATCH_MESH')
    me.from_pydata(verts,[],faces);me.update()
    obj=bpy.data.objects.new('V015_SINGLE_ORBITAL_PATCH',me)
    bpy.context.collection.objects.link(obj);me.materials.append(skin)
    for p in me.polygons:p.use_smooth=True
    # A single stable topology allows a small, native corrective shape key.
    obj.shape_key_add(name='Basis')
    roll=obj.shape_key_add(name='LID_ROLL')
    for k,(t,theta) in enumerate(params):
        roll.data[k].co.y-=.010*(1-t)**2
    for f,q in [(1,0),(18,0),(28,.7),(32,1),(38,1),(49,0),(72,0)]:
        roll.value=q;roll.keyframe_insert(data_path='value',frame=f)
    up=obj.vertex_groups.new(name='UPPER_DEF');lo=obj.vertex_groups.new(name='LOWER_DEF')
    base=obj.vertex_groups.new(name='SOCKET')
    for k,(t,theta) in enumerate(params):
        radial=(1-t)**1.5 if variant!='RIGID_WEIGHTS' else 1.0
        top=max(0,math.sin(theta))*radial
        bottom=max(0,-math.sin(theta))*radial
        fixed=1-top-bottom
        if top>1e-6:up.add([k],top,'REPLACE')
        if bottom>1e-6:lo.add([k],bottom,'REPLACE')
        if fixed>1e-6:base.add([k],fixed,'REPLACE')
    modifier=obj.modifiers.new('TRUE_WEIGHTED_SKIN','ARMATURE')
    modifier.object=rig;modifier.use_vertex_groups=True;modifier.use_bone_envelopes=False
    return obj

def evaluated_face_bvh(obj,deps):
    e=obj.evaluated_get(deps);me=e.to_mesh()
    try:
        verts=[e.matrix_world@v.co for v in me.vertices]
        tris=[]
        for p in me.polygons:
            v=list(p.vertices)
            if len(v)==4:tris.extend([(v[0],v[1],v[2]),(v[0],v[2],v[3])])
            elif len(v)==3:tris.append(tuple(v))
        return BVHTree.FromPolygons(verts,tris,all_triangles=True)
    finally:e.to_mesh_clear()

def ray_hits_face(bvh,x,z):
    return bvh.ray_cast(Vector((x,-2.5,z)),Vector((0,1,0)),2.5)[0] is not None

def connected_components(obj):
    n=len(obj.data.vertices);graph=[set() for _ in range(n)]
    counts=defaultdict(int)
    for f in obj.data.polygons:
        verts=list(f.vertices)
        for i,a in enumerate(verts):
            b=verts[(i+1)%len(verts)]
            graph[a].add(b);graph[b].add(a)
            counts[tuple(sorted((a,b)))]+=1
    seen=set();components=0
    for start in range(n):
        if start in seen:continue
        components+=1;seen.add(start);q=[start]
        while q:
            v=q.pop()
            for w in graph[v]-seen:seen.add(w);q.append(w)
    boundary=[edge for edge,count in counts.items() if count==1]
    boundary_graph=defaultdict(set)
    for u,v in boundary:boundary_graph[u].add(v);boundary_graph[v].add(u)
    loops=0;seen=set()
    for start in boundary_graph:
        if start in seen:continue
        loops+=1;seen.add(start);q=[start]
        while q:
            v=q.pop()
            for w in boundary_graph[v]-seen:seen.add(w);q.append(w)
    assert all(cnt in (1,2) for cnt in counts.values()),'non-manifold edge'
    return {'components':components,'boundary_loops':loops,'boundary_edges':len(boundary),'faces':len(obj.data.polygons),'vertices':n}

def skin_world(obj,deps):
    e=obj.evaluated_get(deps);me=e.to_mesh()
    try:return [e.matrix_world@v.co.copy() for v in me.vertices]
    finally:e.to_mesh_clear()

def evaluate(variant):
    scene=bpy.context.scene
    assert scene['v015_id']==TEST_ID and scene['v015_variant']==variant
    obj=bpy.data.objects['V015_SINGLE_ORBITAL_PATCH']
    assert obj.modifiers[0].type=='ARMATURE'
    assert 'LID_ROLL' in obj.data.shape_keys.key_blocks
    topo=connected_components(obj)
    records=[];max_outer=0;max_inner=0
    for frame in SAMPLE:
        scene.frame_set(frame);deps=bpy.context.evaluated_depsgraph_get()
        points=skin_world(obj,deps)
        basis=[obj.matrix_world@v.co for v in obj.data.vertices]
        od=max((points[(RINGS-1)*N+i]-basis[(RINGS-1)*N+i]).length for i in range(N))
        inn=max((points[i]-basis[i]).length for i in range(N))
        max_outer=max(max_outer,od);max_inner=max(max_inner,inn)
        ap=(points[N//4]-points[3*N//4]).length
        # Native evaluated ray witness on same connected skin / split negative.
        if frame in (1,32,72):
            bvh=evaluated_face_bvh(obj,deps)
            samples=[]
            for xi in range(-10,11):
                for zi in range(-10,11):
                    x=xi*.006;z=zi*.006
                    if x*x+z*z>.065*.065:continue
                    samples.append(ray_hits_face(bvh,x,z))
            pupil_visible=1.0-sum(samples)/len(samples)
        else:pupil_visible=None
        records.append({'frame':frame,'inner_motion_m':round(inn,7),'outer_motion_m':round(od,7),
                        'aperture_m':round(ap,7), 'pupil_visible_fraction':round(pupil_visible,6) if pupil_visible is not None else None})
    closed=next(x for x in records if x['frame']==32)
    open_=records[0]
    if variant=='CONNECTED':
        ok=topo['components']==1 and topo['boundary_loops']==2 and topo['faces']==288 and max_outer<.002 and max_inner>.14 and closed['aperture_m']<.02 and open_['aperture_m']>.30
    elif variant=='TORN_RING':
        ok=topo['components']==2 and topo['boundary_loops']==4 and topo['faces']==240 and max_outer<.002 and max_inner>.14
    else:
        ok=topo['components']==1 and topo['boundary_loops']==2 and topo['faces']==288 and max_outer>.10 and max_inner>.14
    return {'proof_id':TEST_ID,'variant':variant,'blender':bpy.app.version_string,'frames':FRAMES,'fps':FPS,
            'native_armature_weighted':True,'native_shape_key_roll':True,'topology':topo,
            'max_outer_ring_displacement_m':round(max_outer,7),'max_inner_ring_displacement_m':round(max_inner,7),
            'open_aperture_m':open_['aperture_m'],'closed_aperture_m':closed['aperture_m'],
            'closed_iris_visible_fraction':closed['pupil_visible_fraction'],
            'expected_gate_pass':bool(ok),'samples':records,
            'art_approval':'NOT_REVIEWED','scope':'single stylized annulus with hole, not real integrated head or natural eye anatomy',
            'GS001':'UNTOUCHED'}

def build(variant,out):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene=bpy.context.scene
    scene.world=bpy.data.worlds.new('V015_WORLD');scene.world.color=(.12,.14,.16)
    scene.render.engine='BLENDER_WORKBENCH';scene.display.shading.color_type='MATERIAL'
    scene.display.shading.light='STUDIO';scene.display.shading.show_cavity=True
    scene.display.shading.show_shadows=True
    scene.render.resolution_x=640;scene.render.resolution_y=420;scene.render.resolution_percentage=100
    scene.render.fps=FPS;scene.frame_start=1;scene.frame_end=FRAMES
    scene.render.image_settings.file_format='PNG'
    skin=material('SINGLE_SKIN',(.85,.56,.42));eye=material('SCLERA',(.94,.92,.85))
    iris=material('IRIS',(.09,.49,.52));pupmat=material('PUPIL',(.03,.035,.05))
    make_sphere('EYEBALL',.485,(0,.020,0),eye)
    # Iris/pupil are behind the continuous skin and in front of the globe.
    # Original non-photorealistic classroom materials, not a realistic face.
    disk=make_sphere('IRIS_DISK',.085,(0,-.485,0),iris)
    disk.scale=(1,.15,1)
    disk2=make_sphere('PUPIL_DISK',.036,(0,-.498,0),pupmat)
    disk2.scale=(1,.13,1)
    rig=make_rig()
    make_socket(variant,rig,skin)
    camdat=bpy.data.cameras.new('CAM');cam=bpy.data.objects.new('CAMERA',camdat)
    bpy.context.collection.objects.link(cam)
    cam.location=(0,-4.5,.04)
    cam.rotation_euler=(Vector((0,0,0))-cam.location).to_track_quat('-Z','Y').to_euler()
    camdat.type='ORTHO';camdat.ortho_scale=1.76;scene.camera=cam
    scene['v015_id']=TEST_ID;scene['v015_variant']=variant
    out.mkdir(parents=True,exist_ok=True)
    report=evaluate(variant)
    (out/f'{variant}_BUILD.json').write_text(json.dumps(report,indent=2))
    if not report['expected_gate_pass']:raise RuntimeError('V015_BUILD_GATE_FAIL '+json.dumps(report)[:6500])
    bpy.ops.wm.save_as_mainfile(filepath=str((out/f'{variant}.blend').absolute()))
    print('V015_BUILD_PASS',variant,json.dumps({k:v for k,v in report.items() if k!='samples'}))

def verify(variant,out):
    prev=json.loads((out/f'{variant}_BUILD.json').read_text())
    current=evaluate(variant)
    if prev!=current or not current['expected_gate_pass']:
        raise RuntimeError('V015_REOPEN_GATE_FAIL '+json.dumps({'old':prev,'new':current})[:4500])
    (out/f'{variant}_REOPEN.json').write_text(json.dumps(current,indent=2))
    for f in (1,18,28,32,38,49,72):
        bpy.context.scene.frame_set(f)
        bpy.context.scene.render.filepath=str((out/f'{variant}_frame_{f:04d}.png').absolute())
        bpy.ops.render.render(write_still=True)
    print('V015_REOPEN_PASS',variant)

if __name__=='__main__':
    at=sys.argv.index('--')+1 if '--' in sys.argv else len(sys.argv)
    args=sys.argv[at:]
    if len(args)!=3:raise ValueError('usage -- build|verify CONNECTED|TORN_RING|RIGID_WEIGHTS /output')
    mode,variant,path=args
    if variant not in VERSIONS:raise ValueError(variant)
    if mode=='build':build(variant,Path(path))
    elif mode=='verify':verify(variant,Path(path))
    else:raise ValueError(mode)