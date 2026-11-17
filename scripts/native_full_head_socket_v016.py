#!/usr/bin/env python3
"""V016: a single original, full stylized 3D head SKIN mesh with one eye-hole.
Native Blender 5.2.2, exact positive/negative topology and armature weight stress tests.
Scope: synthetic procedural head, not human anatomy, final acting or GS001.
CLI: blender -b --factory-startup --python SCRIPT -- build|verify WELDED_HEAD|SPLIT_SEAM|LEAKY_WEIGHTS OUTDIR
"""
import bpy, sys, json, math
from collections import defaultdict
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
from mathutils.bvhtree import BVHTree

ID='NATIVE_FULL_HEAD_WELDED_EYE_SOCKET_V016'
VARIANTS=('WELDED_HEAD','SPLIT_SEAM','LEAKY_WEIGHTS')
N=48; FRONT=10; BACK=5; FRAME_COUNT=72; FPS=24
FRAMES=(1,18,28,32,38,49,72)
CLOSE=.1695
EYE_MARGIN_X=.30;EYE_MARGIN_Z=.17
SPLIT_BAND=4
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
    arm=bpy.data.armatures.new('V016_ARMATURE_DATA')
    ob=bpy.data.objects.new('V016_HEAD_RIG',arm);bpy.context.collection.objects.link(ob)
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
        if variant=='SPLIT_SEAM' and k==SPLIT_BAND:continue
        for i in range(N):
            j=(i+1)%N;a=k*N+i;b=k*N+j;c=(k+1)*N+j;d=(k+1)*N+i
            faces.append((a,d,c,b))
    last=(FRONT+BACK-1)*N
    for i in range(N):faces.append((last+i,pole,last+(i+1)%N))
    return verts,faces,features

def make_head(variant,r,skin):
    verts,faces,feat=head_geometry(variant)
    mesh=bpy.data.meshes.new('V016_FULL_HEAD_SINGLE_MESH')
    mesh.from_pydata(verts,[],faces);mesh.update()
    ob=bpy.data.objects.new('V016_FULL_HEAD_SKIN',mesh);bpy.context.collection.objects.link(ob)
    mesh.materials.append(skin)
    for p in mesh.polygons:p.use_smooth=True
    ob.shape_key_add(name='Basis')
    fold=ob.shape_key_add(name='SOCKET_FOLD_CORRECTIVE')
    # Authored small material-space fold correction, shared vertex identity, no topology changes.
    for idx,(domain,t,theta) in enumerate(feat):
        if domain=='FACE':fold.data[idx].co.y-=.015*(1-t)**2
    for f,q in pose_curve():
        fold.value=q;fold.keyframe_insert(data_path='value',frame=f)
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
    return ob

def camera_at(name, scene):
    ob=bpy.data.objects['V016_CAMERA']
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

def evaluate(variant):
    scene=bpy.context.scene
    assert scene['fixture_id']==ID and scene['fixture_variant']==variant
    face=bpy.data.objects['V016_FULL_HEAD_SKIN'];cam=bpy.data.objects['V016_CAMERA']
    assert face.modifiers[0].type=='ARMATURE' and 'SOCKET_FOLD_CORRECTIVE' in face.data.shape_keys.key_blocks
    tp=topo_count(face)
    baseline=[face.matrix_world@v.co for v in face.data.vertices]
    max_outer=0.;max_inner=0.;max_behind=0.;min_area=1e8
    records=[]
    for frame in FRAMES:
        scene.frame_set(frame);deps=bpy.context.evaluated_depsgraph_get()
        points=evaluated_vertices(face,deps)
        inn=max((points[i]-baseline[i]).length for i in range(N))
        out=max((points[(FRONT-1)*N+i]-baseline[(FRONT-1)*N+i]).length for i in range(N))
        rear=max((points[FRONT*N+i]-baseline[FRONT*N+i]).length for i in range(N))
        opening=(points[N//4]-points[3*N//4]).length
        min_area=min(min_area,face_quality(points,face)['minimum_triangle_area_m2'])
        max_outer=max(max_outer,out);max_inner=max(max_inner,inn);max_behind=max(max_behind,rear)
        rec={'frame':frame,'aperture_m':round(opening,7),
             'inner_motion_m':round(inn,7),'equator_motion_m':round(out,7),'back_head_motion_m':round(rear,7),
             'area_quality':face_quality(points,face)}
        if frame in (1,32):
            face_bvh=make_mesh_bvh(face,deps);pupil_bvh=make_mesh_bvh(bpy.data.objects['PUPIL'],deps)
            perspectives={}
            for name in STAGES:
                camera_at(name,scene)
                perspectives[name]={'bounds':camera_bounds(scene,cam,points),
                                    'pupil_visibility':eye_visibility(scene,cam,face_bvh,pupil_bvh)}
            camera_at('FRONT',scene)
            rec['multi_angle']=perspectives
        records.append(rec)
    open_=records[0]['aperture_m'];close=next(x for x in records if x['frame']==32)['aperture_m']
    g1=(tp['components']==1 and tp['boundary_loops']==1 and tp['non_manifold_fan_edges']==0
        and tp['boundary_edges']==N and tp['euler_characteristic']==1 and tp['faces']==720 and tp['vertices']==721)
    if variant=='WELDED_HEAD':
        open_angles=records[0]['multi_angle'];closed_angles=next(x for x in records if x['frame']==32)['multi_angle']
        # V016A native camera-ray witness: 100% visible pupil at full blink in all 3 cameras.
        # V016B depth-only repair must reverse that outcome without hiding open eye.
        occlusion_ok=all(closed_angles[name]['pupil_visibility']['sampled_pupil_rays']>=15 and
                         closed_angles[name]['pupil_visibility']['visible_fraction']<.12 and
                         open_angles[name]['pupil_visibility']['visible_fraction']>.35 for name in STAGES)
        ok=g1 and max_outer<.002 and max_behind<.002 and max_inner>.14 and close<.02 and open_>.30 and occlusion_ok
    elif variant=='SPLIT_SEAM':ok=(tp['components']==2 and tp['boundary_loops']==3 and tp['boundary_edges']==3*N
                                    and tp['faces']==672 and tp['vertices']==721 and max_inner>.14)
    else:ok=g1 and max_outer>.10 and max_behind>.10 and max_inner>.14
    return {'fixture':ID,'variant':variant,'blender':bpy.app.version_string,'frames':FRAME_COUNT,'fps':FPS,
            'one_blender_skin_object':True,'armature_weighted':True,'native_shape_key':True,
            'topology':tp,'open_aperture_m':round(open_,7),'closed_aperture_m':round(close,7),
            'max_inner_motion_m':round(max_inner,7),'max_equator_motion_m':round(max_outer,7),
            'max_back_head_motion_m':round(max_behind,7),'min_evaluated_triangle_area_m2':round(min_area,10),
            'native_mechanical_gate':bool(ok),'samples':records,
            'scope':'original oval head with one eye aperture; not a full anatomical human face or hand animation',
            'art_review':'HOLD','occlusion_depth_repair':'V016B_EYE_ASSEMBLY_MOVED_0p040M_Y_ONLY','GS001':'UNTOUCHED'}

def build(variant,out):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene=bpy.context.scene
    scene.world=bpy.data.worlds.new('V016_WORLD');scene.world.color=(.13,.15,.18)
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
    cd=bpy.data.cameras.new('V016_CAM_DATA');cam=bpy.data.objects.new('V016_CAMERA',cd)
    bpy.context.collection.objects.link(cam);cd.type='ORTHO';cd.ortho_scale=2.7;scene.camera=cam
    camera_at('FRONT',scene)
    scene['fixture_id']=ID;scene['fixture_variant']=variant
    out.mkdir(parents=True,exist_ok=True)
    result=evaluate(variant)
    (out/f'{variant}_BUILD.json').write_text(json.dumps(result,indent=2))
    if not result['native_mechanical_gate']:raise RuntimeError('V016_NATIVE_GATE_FAIL '+json.dumps({k:v for k,v in result.items() if k!='samples'})[:4000])
    bpy.ops.wm.save_as_mainfile(filepath=str((out/f'{variant}.blend').absolute()))
    print('V016_NATIVE_BUILD_PASS',variant,json.dumps({k:v for k,v in result.items() if k!='samples'}))

def verify(variant,out):
    prior=json.loads((out/f'{variant}_BUILD.json').read_text())
    now=evaluate(variant)
    if prior!=now or not now['native_mechanical_gate']:
        raise RuntimeError('V016_NATIVE_REOPEN_MISMATCH '+json.dumps({'old':prior,'new':now})[:5500])
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
    print('V016_NATIVE_REOPEN_PASS',variant)

if __name__=='__main__':
    argv=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
    if len(argv)!=3:raise ValueError('usage -- build|verify VARIANT OUTPUT_DIR')
    mode,variant,path=argv
    if variant not in VARIANTS:raise ValueError(variant)
    if mode=='build':build(variant,Path(path))
    elif mode=='verify':verify(variant,Path(path))
    else:raise ValueError(mode)