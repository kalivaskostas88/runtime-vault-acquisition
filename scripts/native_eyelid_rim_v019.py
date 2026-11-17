#!/usr/bin/env python3
"""V019: native Blender stylized full-head eyelid rim wall/thickness & local corrective crease.
Native Blender 5.2.2, pre-researched Solidify rim and object-scale negative controls.
Scope: synthetic procedural head, not human anatomy, final acting or GS001.
CLI: blender -b --factory-startup --python SCRIPT -- build|verify WELDED_HEAD|NO_RIM|UNAPPLIED_SCALE OUTDIR
"""
import bpy, sys, json, math
from collections import defaultdict
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
from mathutils.bvhtree import BVHTree

ID='NATIVE_EYELID_RIM_SOLIDITY_V019'
VARIANTS=('RIM_VALID','NO_RIM','UNAPPLIED_SCALE')
N=48; FRONT=10; BACK=5; FRAME_COUNT=72; FPS=24
FRAMES=(1,18,28,32,38,49,72)
CLOSE=.1695
EYE_MARGIN_X=.30;EYE_MARGIN_Z=.17
SPLIT_BAND=4
THICKNESS=.024
HEAD_SOURCE_VERTICES=(FRONT+BACK)*N+1
HEAD_SOURCE_FACES=(FRONT-1+BACK)*N+N
PREDECLARED_NEGATIVES=('NO_RIM','UNAPPLIED_SCALE')
STAGES={'FRONT':(0,-4.8,.14),'LEFT':(-2.25,-4.6,.32),'RIGHT':(2.25,-4.6,.32)}

def material(name, rgb):
    m=bpy.data.materials.new(name);m.diffuse_color=(*rgb,1.);return m

def sphere(name,radius,location,mat):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=64,ring_count=32,radius=radius,location=location)
    ob=bpy.context.object;ob.name=name;ob.data.materials.append(mat)
    for p in ob.data.polygons:p.use_smooth=True
    return ob

def pose_curve():return ((1,0.),(18,0.),(28,.70),(32,1.),(38,1.),(49,0.),(72,0.))

def rig():
    arm=bpy.data.armatures.new('V019_ARMATURE_DATA')
    ob=bpy.data.objects.new('V019_HEAD_RIG',arm);bpy.context.collection.objects.link(ob)
    bpy.context.view_layer.objects.active=ob;ob.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    for name,tail in [('UPPER_DEF',(0,.08,0)),('LOWER_DEF',(0,-.08,0)),('SKULL',(0,.06,0))]:
        b=arm.edit_bones.new(name);b.head=(0,0,0);b.tail=tail;b.use_connect=False;b.use_deform=True
    bpy.ops.object.mode_set(mode='OBJECT');ob.select_set(False)
    for side in ('UPPER','LOWER'):
        target=bpy.data.objects.new(side+'_GUIDE',None);bpy.context.collection.objects.link(target)
        target.hide_render=True;target.empty_display_size=.035
        for f,q in pose_curve():
            target.location=(0,0,(-1 if side=='UPPER' else 1)*CLOSE*q)
            target.keyframe_insert(data_path='location',frame=f)
        p=ob.pose.bones[side+'_DEF'];co=p.constraints.new('COPY_LOCATION')
        co.name='COPY_GUIDE_WORLD';co.target=target;co.owner_space='WORLD';co.target_space='WORLD'
    return ob

def face_surface_ring(k,i):
    t=k/(FRONT-1);a=math.tau*i/N
    x=(.30+.56*t)*math.cos(a)
    z=(.17+.81*t)*math.sin(a)
    y=-.69*math.sqrt(max(0.,1-t*t))-.06*(1-t)**3
    return (x,y,z)

def head_geometry(variant):
    verts=[];faces=[];features=[]
    # FACE: eye margin is ring 0. Ring FRONT-1 is the precise equator used by the back head.
    for k in range(FRONT):
        for i in range(N):
            verts.append(face_surface_ring(k,i))
            features.append(('FACE',k/(FRONT-1),math.tau*i/N))
    # BACK: vertices start at the shared front equator. No duplicate seam vertices.
    for k in range(1,BACK+1):
        angle=(k/(BACK+1))*(math.pi/2)
        xscale=.86*math.cos(angle);zscale=.98*math.cos(angle);y=.73*math.sin(angle)
        for i in range(N):
            a=math.tau*i/N
            verts.append((xscale*math.cos(a),y,zscale*math.sin(a)))
            features.append(('BACK',1.,a))
    pole=len(verts);verts.append((0.,.73,0.));features.append(('POLE',1.,0.))
    # Quads are oriented consistently on front and back surface; split negative removes ONE bridge band.
    for k in range(FRONT-1+BACK):
        # No missing bridge polygons in any V019 treatment; retain canonical V016B head mesh.
        for i in range(N):
            j=(i+1)%N;a=k*N+i;b=k*N+j;c=(k+1)*N+j;d=(k+1)*N+i
            faces.append((a,d,c,b))
    last=(FRONT+BACK-1)*N
    for i in range(N):faces.append((last+i,pole,last+(i+1)%N))
    return verts,faces,features

def make_head(variant,r,skin):
    verts,faces,feat=head_geometry('WELDED_HEAD')
    mesh=bpy.data.meshes.new('V019_FULL_HEAD_SINGLE_MESH')
    mesh.from_pydata(verts,[],faces);mesh.update()
    ob=bpy.data.objects.new('V019_FULL_HEAD_SKIN',mesh);bpy.context.collection.objects.link(ob)
    mesh.materials.append(skin)
    for p in mesh.polygons:p.use_smooth=True
    ob.shape_key_add(name='Basis')
    fold=ob.shape_key_add(name='SOCKET_FOLD_CORRECTIVE')
    # Authored small material-space fold correction, shared vertex identity, no topology changes.
    for idx,(domain,t,theta) in enumerate(feat):
        if domain=='FACE':fold.data[idx].co.y-=.015*(1-t)**2
    for f,q in pose_curve():
        fold.value=q;fold.keyframe_insert(data_path='value',frame=f)
    # Tiny, deliberately stylized local crease; does not establish anatomy.
    crease=ob.shape_key_add(name='UPPER_LID_LOCAL_CREASE')
    for idx,(domain,t,theta) in enumerate(feat):
        if domain=='FACE':
            angular=max(0.,math.sin(theta))**3
            radial=math.exp(-((t-.32)/.13)**2)
            crease.data[idx].co.y-=.035*angular*radial
    for f,q in pose_curve():
        crease.value=q;crease.keyframe_insert(data_path='value',frame=f)
    up=ob.vertex_groups.new(name='UPPER_DEF');down=ob.vertex_groups.new(name='LOWER_DEF')
    skull=ob.vertex_groups.new(name='SKULL')
    for idx,(domain,t,theta) in enumerate(feat):
        radial=((1-t)**1.5 if domain=='FACE' else 0.) if variant!='LEAKY_WEIGHTS' else (1. if domain!='POLE' else 0.)
        wu=max(0.,math.sin(theta))*radial;wl=max(0.,-math.sin(theta))*radial
        ws=max(0.,1-wu-wl)
        if wu>1e-6:up.add([idx],wu,'REPLACE')
        if wl>1e-6:down.add([idx],wl,'REPLACE')
        if ws>1e-6:skull.add([idx],ws,'REPLACE')
    mod=ob.modifiers.new('ACTUAL_FULL_HEAD_ARMATURE','ARMATURE')
    mod.object=r;mod.use_vertex_groups=True;mod.use_bone_envelopes=False
    # Deliberate modifier ORDER: armature deforms original head first, Solidify makes
    # shell and connects the single eyelid margin after deformation.
    shell=ob.modifiers.new('V019_RIM_WALL_SOLIDIFY','SOLIDIFY')
    shell.thickness=THICKNESS; shell.offset=-1.0
    shell.use_rim=(variant!='NO_RIM')
    shell.use_even_offset=True; shell.use_quality_normals=True
    if variant=='UNAPPLIED_SCALE':
        # Official manual: thickness uses local coordinates; non-uniform scale changes world thickness.
        ob.scale=(1.65,1.0,.55)
    return ob

def camera_at(name, scene):
    ob=bpy.data.objects['V019_CAMERA']
    ob.location=STAGES[name]
    ob.rotation_euler=(Vector((0.,0.,0.))-ob.location).to_track_quat('-Z','Y').to_euler()
    bpy.context.view_layer.update();return ob

def topo_count(ob):
    nv=len(ob.data.vertices);graph=[set() for _ in range(nv)];uses=defaultdict(int)
    for p in ob.data.polygons:
        vs=list(p.vertices)
        for j,a in enumerate(vs):
            b=vs[(j+1)%len(vs)];graph[a].add(b);graph[b].add(a)
            uses[tuple(sorted((a,b)))]+=1
    components=0;seen=set()
    for k in range(nv):
        if k in seen:continue
        components+=1;stack=[k];seen.add(k)
        while stack:
            cur=stack.pop()
            for nx in graph[cur]-seen:seen.add(nx);stack.append(nx)
    boundary=[e for e,c in uses.items() if c==1]
    bad=sum(1 for c in uses.values() if c>2)
    bg=defaultdict(set)
    for a,b in boundary:bg[a].add(b);bg[b].add(a)
    boundary_loops=0;seen=set()
    for i in bg:
        if i in seen:continue
        boundary_loops+=1;stack=[i];seen.add(i)
        while stack:
            cur=stack.pop()
            for nx in bg[cur]-seen:seen.add(nx);stack.append(nx)
    return {'vertices':nv,'faces':len(ob.data.polygons),'edges':len(uses),
            'components':components,'boundary_loops':boundary_loops,'boundary_edges':len(boundary),
            'non_manifold_fan_edges':bad,'euler_characteristic':nv-len(uses)+len(ob.data.polygons)}

def evaluated_vertices(ob,deps):
    ev=ob.evaluated_get(deps);mesh=ev.to_mesh()
    try:return [ev.matrix_world@v.co.copy() for v in mesh.vertices]
    finally:ev.to_mesh_clear()

def area_of_triangle(a,b,c):return ((b-a).cross(c-a)).length*.5

def face_quality(points, ob):
    areas=[]
    for p in ob.data.polygons:
        vs=list(p.vertices)
        if len(vs)==4:
            areas.extend((area_of_triangle(points[vs[0]],points[vs[1]],points[vs[2]]),
                         area_of_triangle(points[vs[0]],points[vs[2]],points[vs[3]])))
        else:areas.append(area_of_triangle(*(points[k] for k in vs)))
    return {'minimum_triangle_area_m2':round(min(areas),10),
            'near_zero_triangle_count':sum(a<1e-8 for a in areas)}

def camera_bounds(scene,cam,points):
    # all head vertices including back pole projected into final ortho camera
    xy=[world_to_camera_view(scene,cam,p) for p in points]
    return {'min_x':round(min(p.x for p in xy),5),'max_x':round(max(p.x for p in xy),5),
            'min_y':round(min(p.y for p in xy),5),'max_y':round(max(p.y for p in xy),5)}

def make_mesh_bvh(ob,deps):
    e=ob.evaluated_get(deps);me=e.to_mesh()
    try:
        verts=[e.matrix_world@v.co for v in me.vertices]
        tri=[]
        for p in me.polygons:
            vs=list(p.vertices)
            if len(vs)==4:tri.extend(((vs[0],vs[1],vs[2]),(vs[0],vs[2],vs[3])))
            else:tri.append(tuple(vs))
        return BVHTree.FromPolygons(verts,tri,all_triangles=True)
    finally:e.to_mesh_clear()

def eye_visibility(scene,cam,face_bvh, pupil_bvh):
    # Camera-parallel rays from real orthographic camera through fixed raster-plane offsets.
    rot=cam.rotation_euler.to_quaternion();direc=(rot@Vector((0,0,-1))).normalized()
    right=rot@Vector((1,0,0));up=rot@Vector((0,1,0));eye=Vector((0.,-.744,0.))
    base=cam.location+right*((eye-cam.location).dot(right))+up*((eye-cam.location).dot(up))
    n=0;visible=0
    for a in range(-8,9):
        for b in range(-8,9):
            origin=base+right*a*.009+up*b*.009
            phit,_,_,pd=pupil_bvh.ray_cast(origin,direc,8.0)
            if phit is None:continue
            n+=1
            fhit,_,_,fd=face_bvh.ray_cast(origin,direc,8.0)
            if fhit is None or pd<fd-.00015:visible+=1
    return {'sampled_pupil_rays':n,'visible_rays':visible,
            'visible_fraction':round(visible/n,5) if n else 1.0}

def evaluated_mesh_topology(ob,deps):
    ev=ob.evaluated_get(deps); me=ev.to_mesh()
    try:
        nv=len(me.vertices); edges=defaultdict(int); graph=[set() for _ in range(nv)]
        for poly in me.polygons:
            v=list(poly.vertices)
            for i,a in enumerate(v):
                b=v[(i+1)%len(v)]
                edges[tuple(sorted((a,b)))]+=1;graph[a].add(b);graph[b].add(a)
        seen=set();comp=0
        for k in range(nv):
            if k in seen:continue
            comp+=1; stack=[k];seen.add(k)
            while stack:
                a=stack.pop()
                for t in graph[a]-seen: seen.add(t);stack.append(t)
        boundary=[e for e,count in edges.items() if count==1]
        return {'vertices':nv,'faces':len(me.polygons),'components':comp,
                'boundary_edges':len(boundary),'nonmanifold_fan_edges':sum(v>2 for v in edges.values()),
                'euler_characteristic':nv-len(edges)+len(me.polygons)}
    finally: ev.to_mesh_clear()

def wall_thickness_samples(ob,deps):
    ev=ob.evaluated_get(deps);me=ev.to_mesh()
    try:
        nv=HEAD_SOURCE_VERTICES
        assert len(me.vertices)==2*nv, ('unexpected Solidify vertex ordering or count',len(me.vertices),nv)
        pairs=[]
        # Defensive: sample full rings excluding pole; same-index duplicated shell convention is
        # a hypothesis checked by native result, not an asserted Blender API contract.
        for i in range(0,nv-1,7):
            a=ev.matrix_world@me.vertices[i].co
            b=ev.matrix_world@me.vertices[i+nv].co
            pairs.append((a-b).length)
        pairs.sort()
        return {'sample_n':len(pairs),'minimum_m':round(pairs[0],7),
                'median_m':round(pairs[len(pairs)//2],7),'maximum_m':round(pairs[-1],7),
                'max_min_ratio':round(pairs[-1]/max(1e-12,pairs[0]),5)}
    finally: ev.to_mesh_clear()

def authored_crease_witness(ob):
    b=ob.data.shape_keys.key_blocks['Basis']; c=ob.data.shape_keys.key_blocks['UPPER_LID_LOCAL_CREASE']
    upper_index=3*N+N//4
    rear_index=FRONT*N+N//4
    return {'upper_local_delta_m':round((c.data[upper_index].co-b.data[upper_index].co).length,7),
            'rear_local_delta_m':round((c.data[rear_index].co-b.data[rear_index].co).length,7),
            'shape_key_basis_same_topology':len(c.data)==len(b.data)}

def evaluate(variant):
    scene=bpy.context.scene
    assert scene['fixture_id']==ID and scene['fixture_variant']==variant
    face=bpy.data.objects['V019_FULL_HEAD_SKIN']
    assert len(face.modifiers)==2 and face.modifiers[0].type=='ARMATURE' and face.modifiers[1].type=='SOLIDIFY'
    assert 'UPPER_LID_LOCAL_CREASE' in face.data.shape_keys.key_blocks
    assert variant=='UNAPPLIED_SCALE' or all(abs(float(v)-1.)<1e-9 for v in face.scale)
    source=topo_count(face)
    assert source['components']==1 and source['boundary_loops']==1 and source['boundary_edges']==N
    crest=authored_crease_witness(face)
    scene.frame_set(32)
    deps=bpy.context.evaluated_depsgraph_get()
    shell=face.modifiers[1]
    tp=evaluated_mesh_topology(face,deps)
    thickness=wall_thickness_samples(face,deps)
    records=[]
    for frame in FRAMES:
        scene.frame_set(frame);deps=bpy.context.evaluated_depsgraph_get()
        pose=face.data.shape_keys.key_blocks['UPPER_LID_LOCAL_CREASE'].value
        records.append({'frame':frame,'crease_value':round(pose,5)})
    # Source model has exactly 721 vertices, 720 faces and one intentional ocular boundary;
    # Solidify adds two copies, and rim-fill adds exactly 48 bridge faces.
    structural=(source['vertices']==721 and source['faces']==720 and source['components']==1
                and source['boundary_loops']==1 and tp['vertices']==1442
                and tp['nonmanifold_fan_edges']==0 and crest['upper_local_delta_m']>.018
                and crest['rear_local_delta_m']==0 and crest['shape_key_basis_same_topology'])
    if variant=='RIM_VALID':
        gate=(structural and tp['components']==1 and tp['boundary_edges']==0
              and tp['faces']==1488 and all(abs(v-1.)<1e-9 for v in face.scale)
              and .010<thickness['minimum_m'] and thickness['maximum_m']<.050)
    elif variant=='NO_RIM':
        gate=(structural and tp['components']==2 and tp['boundary_edges']==2*N
              and tp['faces']==1440 and shell.use_rim is False)
    else:
        gate=(structural and tp['components']==1 and tp['boundary_edges']==0 and tp['faces']==1488
              and all(abs(v-exp)<1e-5 for v,exp in zip(face.scale,(1.65,1.,.55)))
              and thickness['max_min_ratio']>1.3)
    return {'fixture':ID,'variant':variant,'blender':bpy.app.version_string,'native_gate':bool(gate),
            'source_head':source,'evaluated_shell':tp,'measured_world_wall_thickness':thickness,
            'crease_authored':crest,'modifier_order':[m.type for m in face.modifiers],
            'rim_fill':bool(shell.use_rim),'object_scale':[round(v,5) for v in face.scale],
            'frames':FRAME_COUNT,'fps':FPS,'samples':records,'art_grade':'HOLD',
            'scope':'original single-eye stylized oval; Solidify rim and one procedural upper crease; no anatomical proof',
            'source_claims':'Blender 5.2 Solidify manual warns rim/normal/nonuniform-scale/approximate thickness',
            'GS001':'UNTOUCHED'}

def build(variant,out):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene=bpy.context.scene
    scene.world=bpy.data.worlds.new('V019_WORLD');scene.world.color=(.13,.15,.18)
    scene.render.engine='BLENDER_WORKBENCH';scene.display.shading.color_type='MATERIAL'
    scene.display.shading.light='STUDIO';scene.display.shading.show_cavity=True;scene.display.shading.show_shadows=True
    scene.render.resolution_x=640;scene.render.resolution_y=480;scene.render.resolution_percentage=100
    scene.render.fps=FPS;scene.frame_start=1;scene.frame_end=FRAME_COUNT
    scene.render.image_settings.file_format='PNG'
    face_color=material('FLESH',(.82,.55,.42));eye_color=material('SCLERA',(.94,.93,.85))
    iris_color=material('IRIS',(.13,.42,.43));pupil_color=material('PUPIL',(.018,.022,.036))
    sphere('EYEBALL',.37,(0,-.36,0),eye_color)
    i=sphere('IRIS',.080,(0,-.730,0),iris_color);i.scale=(1,.16,1)
    p=sphere('PUPIL',.036,(0,-.744,0),pupil_color);p.scale=(1,.14,1)
    r=rig();make_head(variant,r,face_color)
    cd=bpy.data.cameras.new('V019_CAM_DATA');cam=bpy.data.objects.new('V019_CAMERA',cd)
    bpy.context.collection.objects.link(cam);cd.type='ORTHO';cd.ortho_scale=2.7;scene.camera=cam
    camera_at('FRONT',scene)
    scene['fixture_id']=ID;scene['fixture_variant']=variant
    out.mkdir(parents=True,exist_ok=True)
    result=evaluate(variant)
    (out/f'{variant}_BUILD.json').write_text(json.dumps(result,indent=2))
    if not result['native_gate']:raise RuntimeError('V019_NATIVE_GATE_FAIL '+json.dumps({k:v for k,v in result.items() if k!='samples'})[:4000])
    bpy.ops.wm.save_as_mainfile(filepath=str((out/f'{variant}.blend').absolute()))
    print('V019_NATIVE_BUILD_PASS',variant,json.dumps({k:v for k,v in result.items() if k!='samples'}))

def verify(variant,out):
    prior=json.loads((out/f'{variant}_BUILD.json').read_text())
    now=evaluate(variant)
    if prior!=now or not now['native_gate']:
        raise RuntimeError('V019_NATIVE_REOPEN_MISMATCH '+json.dumps({'old':prior,'new':now})[:5500])
    (out/f'{variant}_REOPEN.json').write_text(json.dumps(now,indent=2))
    scene=bpy.context.scene
    for angle in STAGES:
        camera_at(angle,scene)
        frames=(1,18,28,32,38,49,72) if angle=='FRONT' else (1,32)
        for f in frames:
            scene.frame_set(f)
            scene.render.filepath=str((out/f'{variant}_{angle}_frame_{f:04d}.png').absolute())
            bpy.ops.render.render(write_still=True)
    camera_at('FRONT',scene)
    print('V019_NATIVE_REOPEN_PASS',variant)

if __name__=='__main__':
    argv=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
    if len(argv)!=3:raise ValueError('usage -- build|verify VARIANT OUTPUT_DIR')
    mode,variant,path=argv
    if variant not in VARIANTS:raise ValueError(variant)
    if mode=='build':build(variant,Path(path))
    elif mode=='verify':verify(variant,Path(path))
    else:raise ValueError(mode)