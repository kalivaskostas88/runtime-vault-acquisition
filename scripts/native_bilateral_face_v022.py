#!/usr/bin/env python3
"""V022 Blender 5.2.2 original two-eye / nose / cheek integration microproof.
No production assets, no biometric/anatomical fidelity claims. 4 controlled variants.
CLI: blender -b --factory-startup --python SCRIPT -- build|verify VARIANT OUTPUT
"""
import bpy,sys,math,json
from pathlib import Path
from collections import defaultdict
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

FIXTURE='V022_BILATERAL_EYE_NOSE_CHEEK_TECHNICAL_INTEGRATION'
VARIANTS=('LEFT_ONLY','RIGHT_ONLY','CROSSTALK','SCALP_LEAK')
SIDES=('LEFT','RIGHT')
NP=96; NL=44; FPS=24; END=72
EYE_I={'RIGHT':(4,10),'LEFT':(86,92)}   # angular surface indices in continuous single mesh
EYE_J=(23,27)                         # hole removes faces j=23,24,25,26
SCENES={'FRONT':(0.,-4.8,.17),'LEFT':(-2.0,-4.6,.44),'RIGHT':(2.,-4.6,.44)}
TIME=((1,0.),(18,0.),(28,.70),(32,1.),(38,1.),(49,0.),(72,0.))

def mat(name,rgb):
    m=bpy.data.materials.new(name);m.diffuse_color=(*rgb,1);return m

def sphere(name,r,xyz,color):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32,ring_count=16,radius=r,location=xyz)
    o=bpy.context.object;o.name=name;o.data.materials.append(color)
    for f in o.data.polygons:f.use_smooth=True
    return o

def relief(theta,z):
    # Synthetic landmark proxies, NOT metric anatomical measurements.
    # Only front facing area. Nose bridge/tip, malar pads and brow ridges.
    if math.cos(theta)<0:return (0.,0.,0.)
    nose=.16*math.exp(-(theta/.17)**2-((z+.02)/.41)**2)+.19*math.exp(-(theta/.20)**2-((z+.18)/.13)**2)
    cheek=.095*math.exp(-((abs(theta)-.50)/.23)**2-((z+.25)/.20)**2)
    brow=.070*math.exp(-((abs(theta)-.38)/.25)**2-((z-.52)/.14)**2)
    return nose,cheek,brow

def surface_point(i,j):
    theta=2*math.pi*i/NP
    lat=-math.pi/2+math.pi*j/(NL-1)
    z=1.20*math.sin(lat)
    spread=math.cos(lat)
    x=.98*spread*math.sin(theta)
    nose,cheek,brow=relief(theta,z)
    y=-.77*spread*math.cos(theta)-(nose+cheek+brow)
    return (x,y,z)

def source_geometry():
    # All j=1..NL-2 rows share original indexes. 2 pole vertices and 2 disjoint openings.
    vertices=[];meta=[];faces=[]
    for j in range(1,NL-1):
        for i in range(NP):
            vertices.append(surface_point(i,j));meta.append((i,j))
    lower=len(vertices);vertices.append((0.,0.,-1.20));meta.append((-1,0))
    upper=len(vertices);vertices.append((0.,0.,1.20));meta.append((-1,NL-1))
    def ix(i,j):return (j-1)*NP+(i%NP)
    def omitted(i,j):
        return EYE_J[0] <= j < EYE_J[1] and any(lo<=i<hi for lo,hi in EYE_I.values())
    for j in range(1,NL-2):
        for i in range(NP):
            if omitted(i,j):continue
            k=(i+1)%NP
            faces.append((ix(i,j),ix(k,j),ix(k,j+1),ix(i,j+1)))
    for i in range(NP):
        k=(i+1)%NP
        faces.append((lower,ix(k,1),ix(i,1)))
        faces.append((upper,ix(i,NL-2),ix(k,NL-2)))
    # Preknown antipattern: removing eye-hole faces may leave isolated interior grid vertices.
    # Compact only referenced vertices BEFORE any shape key to guarantee one connected skin.
    used=sorted({k for face in faces for k in face})
    remap={old:new for new,old in enumerate(used)}
    global INDEX_MAP
    INDEX_MAP={(i,j):remap[old] for old,(i,j) in enumerate(meta) if old in remap and i>=0}
    return [vertices[k] for k in used],[tuple(remap[k] for k in f) for f in faces],[meta[k] for k in used]

def topology(vertices,faces):
    nv=len(vertices); counts=defaultdict(int);neighbors=[set() for _ in range(nv)]
    for f in faces:
        for a,b in zip(f,f[1:]+f[:1]):
            k=tuple(sorted((a,b)));counts[k]+=1;neighbors[a].add(b);neighbors[b].add(a)
    boundary=[e for e,c in counts.items() if c==1];bad=sum(c>2 for c in counts.values())
    seen=set();comp=0
    for i in range(nv):
        if i in seen:continue
        comp+=1;stack=[i];seen.add(i)
        while stack:
            for n in neighbors[stack.pop()]-seen:seen.add(n);stack.append(n)
    bn=defaultdict(set)
    for a,b in boundary:bn[a].add(b);bn[b].add(a)
    seen=set();loops=0
    for i in bn:
        if i in seen:continue
        loops+=1;st=[i];seen.add(i)
        while st:
            for n in bn[st.pop()]-seen:seen.add(n);st.append(n)
    return dict(vertices=nv,faces=len(faces),components=comp,boundary_edges=len(boundary),boundary_loops=loops,
                nonmanifold_fan_edges=bad,euler=nv-len(counts)+len(faces))

def index(i,j):return INDEX_MAP[(i%NP,j)]

def make_armature():
    data=bpy.data.armatures.new('V022_HEAD_RIG_DATA')
    rig=bpy.data.objects.new('V022_HEAD_RIG',data);bpy.context.collection.objects.link(rig)
    bpy.context.view_layer.objects.active=rig;rig.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    bone=data.edit_bones.new('HEAD');bone.head=(0,0,0);bone.tail=(0,0,.2)
    bpy.ops.object.mode_set(mode='OBJECT');rig.select_set(False)
    return rig

def set_key(o,name,amt,scalp=False):
    key=o.shape_key_add(name=name,from_mix=False)
    # Each key is authored from Basis, never from a currently active shape.
    basis=o.data.shape_keys.key_blocks['Basis']
    target='LEFT' if name.startswith('LEFT') else 'RIGHT'
    mid=(EYE_I[target][0]+EYE_I[target][1])/2
    upper,bottom=EYE_J[1],EYE_J[0]
    for n,(i,j) in enumerate(META):
        if i<0:continue
        dist_i=abs(i-mid)
        # Both eyes completely separate; no implicit Mirror operator/index assumptions.
        horizontal=math.exp(-((dist_i/4.0)**4))
        if dist_i>9:continue
        if abs(j-upper)<=4:
            fall=math.exp(-((j-upper)/1.42)**2)
            key.data[n].co.z-=amt*horizontal*fall
        if abs(j-bottom)<=4:
            fall=math.exp(-((j-bottom)/1.42)**2)
            key.data[n].co.z+=amt*.97*horizontal*fall
    # Save a zero-leak shape by default; error is deliberately isolated in its own key.
    return key

def build_head(variant,rig):
    verts,faces,meta=source_geometry();global META;META=meta
    mesh=bpy.data.meshes.new('V022_TWO_EYE_FACE_MESH');mesh.from_pydata(verts,[],faces);mesh.update()
    o=bpy.data.objects.new('V022_HEAD_SKIN',mesh);bpy.context.collection.objects.link(o)
    o.data.materials.append(mat('SKIN',(.72,.51,.40)))
    for f in mesh.polygons:f.use_smooth=True
    vg=o.vertex_groups.new(name='HEAD');vg.add(list(range(len(verts))),1.,'REPLACE')
    o.shape_key_add(name='Basis',from_mix=False)
    keys={'LEFT':set_key(o,'LEFT_LID_BLINK',.165),'RIGHT':set_key(o,'RIGHT_LID_BLINK',.165)}
    # Intentionally separate, explicit negative leak key.
    leak=o.shape_key_add(name='WRONG_SCALP_LEAK',from_mix=False)
    for n,(i,j) in enumerate(meta):
        if (i>=0 and math.cos(2*math.pi*i/NP)<-.45) or i<0:
            leak.data[n].co.z+=.065
    for f,q in TIME:
        keys['LEFT'].value=q if variant!='RIGHT_ONLY' else 0.
        keys['RIGHT'].value=q if variant in ('RIGHT_ONLY','CROSSTALK') else 0.
        leak.value=q if variant=='SCALP_LEAK' else 0.
        for k in (keys['LEFT'],keys['RIGHT'],leak):k.keyframe_insert(data_path='value',frame=f)
    arm=o.modifiers.new('V022_NATIVE_ARMATURE','ARMATURE');arm.object=rig;arm.use_vertex_groups=True;arm.use_bone_envelopes=False
    solid=o.modifiers.new('V022_LID_RIM_SOLIDIFY','SOLIDIFY');solid.thickness=.018;solid.offset=-1;solid.use_rim=True;solid.use_even_offset=True
    return o

def make_eyes():
    mat_white=mat('WHITE',(.90,.88,.79)); mat_iris=mat('TEAL',(.14,.43,.46)); mat_black=mat('BLACK',(.025,.025,.037))
    # Front-facing, symmetric eyeballs. Basic spherical placeholders, not production eye anatomy.
    for side in SIDES:
        mid=sum(EYE_I[side])/2; theta=2*math.pi*mid/NP
        x=.98*math.sin(theta)*.978
        z=(surface_point(int(mid),23)[2]+surface_point(int(mid),27)[2])/2
        skin=surface_point(int(mid),25)
        sphere(side+'_EYEBALL',.205,(x,skin[1]+.115,z),mat_white)
        a=sphere(side+'_IRIS',.079,(x,skin[1]-.092,z),mat_iris);a.scale=(1,.16,1)
        p=sphere(side+'_PUPIL',.038,(x,skin[1]-.105,z),mat_black);p.scale=(1,.14,1)

def camera(angle):
    o=bpy.data.objects['V022_CAM'];o.location=SCENES[angle]
    o.rotation_euler=(Vector((0.,0.,0.))-o.location).to_track_quat('-Z','Y').to_euler()
    bpy.context.view_layer.update();return o

def eval_points(ob):
    deps=bpy.context.evaluated_depsgraph_get();e=ob.evaluated_get(deps);me=e.to_mesh()
    try:return [e.matrix_world@v.co.copy() for v in me.vertices]
    finally:e.to_mesh_clear()

def eval_topo(ob):
    deps=bpy.context.evaluated_depsgraph_get();e=ob.evaluated_get(deps);me=e.to_mesh()
    try:return topology(me.vertices,[tuple(p.vertices) for p in me.polygons])
    finally:e.to_mesh_clear()

def witness(variant):
    # Reconstruct deterministic source index mapping on every fresh Blender process.
    global META
    canonical_vertices,canonical_faces,META=source_geometry()
    scene=bpy.context.scene; o=bpy.data.objects['V022_HEAD_SKIN']
    assert len(o.data.vertices)==len(canonical_vertices) and len(o.data.polygons)==len(canonical_faces)
    assert scene['fixture']==FIXTURE and scene['variant']==variant
    source=topology(o.data.vertices,[tuple(f.vertices) for f in o.data.polygons]);assert len(o.modifiers)==2
    scene.frame_set(1); neutral=eval_points(o)
    scene.frame_set(32); active=eval_points(o);meshstat=eval_topo(o)
    def gap(side,points):
        center=round(sum(EYE_I[side])/2)
        return round(abs(points[index(center,EYE_J[1])].z-points[index(center,EYE_J[0])].z),6)
    aperture={s:{'open_m':gap(s,neutral),'closed_m':gap(s,active),'closure_delta_m':round(gap(s,neutral)-gap(s,active),6)} for s in SIDES}
    rear=[n for n,(i,j) in enumerate(META) if i<0 or math.cos(2*math.pi*i/NP)<-.55]
    scalp=max((active[i]-neutral[i]).length for i in rear)
    keys=o.data.shape_keys.key_blocks
    offside={}
    basis=keys['Basis']
    for s in SIDES:
        other='RIGHT' if s=='LEFT' else 'LEFT'
        key=keys[s+'_LID_BLINK']
        mark=index(round(sum(EYE_I[other])/2),EYE_J[1])
        offside[s]=round((key.data[mark].co-basis.data[mark].co).length,9)
    # Relief evidence from source vertex positions vs analytic bare spheroid.
    def point_bump(i,j):
        p=o.data.vertices[index(i,j)].co;theta=2*math.pi*i/NP;lat=-math.pi/2+math.pi*j/(NL-1)
        return round(-p.y-.77*math.cos(lat)*math.cos(theta),6)
    nose=point_bump(0,20)
    cheek=point_bump(8,18)
    brow=point_bump(7,27)
    stats={'fixture':FIXTURE,'variant':variant,'blender':bpy.app.version_string,'source_topology':source,
           'evaluated_topology':meshstat,'gap_per_eye':aperture,'max_remote_scalp_displacement_m':round(scalp,7),
           'shape_key_offside_delta_m':offside,'qualitative_landmarks_bump_m':{'nose':nose,'cheek':cheek,'brow':brow},
           'modifier_order':[m.type for m in o.modifiers], 'frames':END,'fps':FPS,
           'art':'ART_HOLD; synthetic symmetric head, polygonal eye rings, no anatomy or acting validation',
           'protected':'GS001_UNTOUCHED'}
    expected={'LEFT_ONLY':('LEFT',False,False),'RIGHT_ONLY':('RIGHT',False,False),'CROSSTALK':('LEFT',True,False),'SCALP_LEAK':('LEFT',False,True)}
    active_eye,cross,leak=expected[variant]
    passive_eye='RIGHT' if active_eye=='LEFT' else 'LEFT'
    base=(source['components']==1 and source['boundary_loops']==2 and source['nonmanifold_fan_edges']==0 and
          meshstat['components']==1 and meshstat['boundary_edges']==0 and meshstat['nonmanifold_fan_edges']==0 and
          all(offside[s]<1e-7 for s in SIDES) and
          all(len(k.data)==source['vertices'] for k in keys) and
          nose>.11 and cheek>.035 and brow>.035)
    motion=(aperture[active_eye]['closure_delta_m']>.20 and (aperture[passive_eye]['closure_delta_m']>.20 if cross else aperture[passive_eye]['closure_delta_m']<.002))
    scalp_ok=(scalp>.05 if leak else scalp<.001)
    stats['native_gate']=bool(base and motion and scalp_ok)
    stats['predeclared_negative_controls']=['CROSSTALK','SCALP_LEAK']
    return stats

def build(variant,out):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene=bpy.context.scene;scene.world=bpy.data.worlds.new('V022_WORLD');scene.world.color=(.11,.14,.17)
    scene.render.engine='BLENDER_WORKBENCH';scene.display.shading.color_type='MATERIAL';scene.display.shading.light='STUDIO'
    scene.display.shading.show_cavity=True;scene.display.shading.show_shadows=True
    scene.render.resolution_x=640;scene.render.resolution_y=480;scene.render.resolution_percentage=100
    scene.render.fps=FPS;scene.frame_start=1;scene.frame_end=END
    rig=make_armature();head=build_head(variant,rig);make_eyes()
    cd=bpy.data.cameras.new('V022_CAMERA_DATA');cam=bpy.data.objects.new('V022_CAM',cd)
    bpy.context.collection.objects.link(cam);cd.type='ORTHO';cd.ortho_scale=2.95;scene.camera=cam
    camera('FRONT');scene['fixture']=FIXTURE;scene['variant']=variant
    out.mkdir(parents=True,exist_ok=True)
    r=witness(variant);(out/(variant+'_BUILD.json')).write_text(json.dumps(r,indent=2))
    if not r['native_gate']:raise RuntimeError('V022_NATIVE_GATE_FAILURE '+json.dumps(r)[:6000])
    bpy.ops.wm.save_as_mainfile(filepath=str((out/(variant+'.blend')).absolute()))
    print('V022_NATIVE_BUILD_PASS',variant,json.dumps({'gaps':r['gap_per_eye'],'topology':r['source_topology'],'landmarks':r['qualitative_landmarks_bump_m']}))

def verify(variant,out):
    prev=json.loads((out/(variant+'_BUILD.json')).read_text());new=witness(variant)
    if prev!=new or not new['native_gate']:raise RuntimeError('V022_REOPEN_MISMATCH '+json.dumps({'old':prev,'new':new})[:5500])
    (out/(variant+'_REOPEN.json')).write_text(json.dumps(new,indent=2))
    scene=bpy.context.scene
    for angle in SCENES:
        camera(angle)
        frames=(1,24,32,49,72) if angle=='FRONT' else (32,)
        for f in frames:
            scene.frame_set(f);scene.render.filepath=str((out/f'{variant}_{angle}_{f:04d}.png').absolute())
            bpy.ops.render.render(write_still=True)
    camera('FRONT')
    print('V022_NATIVE_REOPEN_PASS',variant)

if __name__=='__main__':
    args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
    if len(args)!=3:raise RuntimeError('Usage: -- build|verify VARIANT OUTPUT')
    mode,variant,dest=args
    if variant not in VARIANTS:raise ValueError(variant)
    if mode=='build':build(variant,Path(dest))
    elif mode=='verify':verify(variant,Path(dest))
    else:raise ValueError(mode)