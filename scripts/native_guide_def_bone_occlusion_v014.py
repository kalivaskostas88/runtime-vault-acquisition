#!/usr/bin/env python3
"""V014 native Blender 5.2.2: linked eye-guide -> deform bone -> weighted ribbon -> Shrinkwrap,
with evaluated camera-ray iris occlusion and causal negative controls. Original research fixture.
Scope is mechanism, NOT natural anatomy, continuous face topology, performance approval, or GS001.
Usage: blender -b --factory-startup --python SCRIPT -- build COUPLED /output/COUPLED
       blender -b /output/COUPLED/COUPLED.blend --python SCRIPT -- verify COUPLED /output/COUPLED
"""
import bpy, sys, math, json
from pathlib import Path
from mathutils import Vector

VARIANTS=('COUPLED','DISCONNECTED','FRONT_IRIS')
R=0.52
OFFSET=0.014
RG=R+OFFSET
NX,NV,NB=29,9,7
FPS,FRAMES=24,72
SAMPLE_FRAMES=(1,16,28,32,38,52,72)
ID='EYE_GUIDE_TO_DEFORM_AND_OCCLUSION_V014'

def mat(name, rgb):
    m=bpy.data.materials.new(name);m.diffuse_color=tuple(rgb)+(1.0,);return m

def ball(name, location, scale, material, segments=72, rings=36):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments,ring_count=rings,radius=1,location=location)
    o=bpy.context.object;o.name=name;o.scale=scale
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    o.data.materials.append(material)
    for p in o.data.polygons:p.use_smooth=True
    return o

def lid_margin(x,side,closure):
    h=math.sqrt(max(0.0,1.0-(x/.46)**2))
    return (1 if side=='UPPER' else -1)*.205*h*(1-closure)

def guide_raw(x,z):
    # Deliberately off-sphere; the native ON_SURFACE constraint supplies the actual radius.
    y=-math.sqrt(max(.01,RG*RG-x*x-z*z))
    return Vector((x,y,z))*1.065

def constrained_guide_rest(x,z):
    r=guide_raw(x,z);return r.normalized()*RG

def get_key_values():
    return ((1,0.0),(18,0.0),(28,.72),(32,1.0),(38,1.0),(49,0.0),(72,0.0))

def make_guides(center):
    guides={}
    for side in ('UPPER','LOWER'):
        for n in range(NB):
            x=(n/(NB-1)*2-1)*.36
            name=f'{side}_GUIDE_{n}'
            obj=bpy.data.objects.new(name,None);bpy.context.collection.objects.link(obj)
            obj.empty_display_type='SPHERE';obj.empty_display_size=.025;obj.hide_render=True
            c=obj.constraints.new('LIMIT_DISTANCE');c.name='SPHERE_ON_SURFACE'
            c.target=center;c.distance=RG;c.limit_mode='LIMITDIST_ONSURFACE';c.use_transform_limit=True
            for fr,q in get_key_values():
                pos=guide_raw(x,lid_margin(x,side,q))
                obj.location=pos;obj.keyframe_insert(data_path='location',frame=fr)
            guides[name]=obj
    return guides

def make_armature(guides,variant):
    arm=bpy.data.armatures.new('V014_DEFORM_BONES')
    rig=bpy.data.objects.new('V014_SKIN_RIG',arm);bpy.context.collection.objects.link(rig)
    bpy.context.view_layer.objects.active=rig;rig.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    socket=arm.edit_bones.new('SOCKET');socket.head=(0,.12,0);socket.tail=(0,.20,0)
    for name in guides:
        side,n=name.split('_GUIDE_')
        idx=int(n);x=(idx/(NB-1)*2-1)*.36
        rest=constrained_guide_rest(x,lid_margin(x,side,0))
        b=arm.edit_bones.new(f'{side}_DEF_{idx}')
        b.head=rest;b.tail=rest+Vector((0,.065,0))
        b.use_connect=False
    bpy.ops.object.mode_set(mode='OBJECT');rig.select_set(False)
    for name,g in guides.items():
        side,n=name.split('_GUIDE_');p=rig.pose.bones[f'{side}_DEF_{n}']
        c=p.constraints.new('COPY_LOCATION');c.name='FOLLOW_SPHERE_GUIDE';c.target=g
        c.target_space='WORLD';c.owner_space='WORLD';c.influence=0 if variant=='DISCONNECTED' else 1
    return rig

def make_lid(side,skin,globe,rig):
    vertices=[];faces=[]
    upper=side=='UPPER'
    for i in range(NX):
        x=(i/(NX-1)*2-1)*.38
        h=math.sqrt(max(0.0,1-(x/.46)**2))
        inner=(.205 if upper else -.205)*h
        outer=(.385 if upper else -.385)*h
        for j in range(NV):
            t=j/(NV-1)
            z=inner+(outer-inner)*t
            vertices.append((x,-.555,z))
    for i in range(NX-1):
        for j in range(NV-1):
            a=i*NV+j
            faces.append((a,a+NV,a+NV+1,a+1) if upper else (a,a+1,a+NV+1,a+NV))
    mesh=bpy.data.meshes.new(side+'_CONNECTED_SKIN_MESH');mesh.from_pydata(vertices,[],faces);mesh.update()
    obj=bpy.data.objects.new(side+'_SKIN',mesh);bpy.context.collection.objects.link(obj)
    obj.data.materials.append(skin)
    for poly in mesh.polygons:poly.use_smooth=True
    groups=[obj.vertex_groups.new(name=f'{side}_DEF_{n}') for n in range(NB)]
    socket=obj.vertex_groups.new(name='SOCKET')
    for i in range(NX):
        u=i/(NX-1)*(NB-1);a=min(NB-2,int(u));alpha=u-a
        for j in range(NV):
            vid=i*NV+j;t=j/(NV-1)
            driven=(1-t)**1.4
            if driven>1e-8:
                groups[a].add([vid],driven*(1-alpha),'REPLACE')
                if alpha>0:groups[a+1].add([vid],driven*alpha,'REPLACE')
            if driven<1:socket.add([vid],1-driven,'REPLACE')
    a=obj.modifiers.new('GUIDE_DEF_BONE_SKINNING','ARMATURE');a.object=rig;a.use_vertex_groups=True;a.use_bone_envelopes=False
    sw=obj.modifiers.new('EYEBALL_SURFACE_SAFETY','SHRINKWRAP');sw.target=globe
    sw.wrap_method='NEAREST_SURFACEPOINT';sw.wrap_mode='ABOVE_SURFACE';sw.offset=OFFSET
    return obj

def pupil_disk(name,rad,depth,matl):
    verts=[];faces=[];center=(0,-R-depth,0)
    verts.append(center)
    n=64
    for k in range(n):
        a=k*math.tau/n;x=math.cos(a)*rad;z=math.sin(a)*rad
        y=-math.sqrt(R*R-x*x-z*z)-depth
        verts.append((x,y,z))
    for k in range(n):faces.append((0,k+1,((k+1)%n)+1))
    mesh=bpy.data.meshes.new(name+'_MESH');mesh.from_pydata(verts,[],faces);mesh.update()
    o=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(o)
    mesh.materials.append(matl)
    return o

def build(variant,out):
    assert variant in VARIANTS
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene=bpy.context.scene
    scene.render.engine='BLENDER_WORKBENCH';scene.render.resolution_x=640;scene.render.resolution_y=420
    scene.render.resolution_percentage=100;scene.render.fps=FPS
    scene.frame_start=1;scene.frame_end=FRAMES;scene.render.image_settings.file_format='PNG'
    scene.display.shading.color_type='MATERIAL';scene.display.shading.light='STUDIO'
    scene.display.shading.show_cavity=True;scene.display.shading.show_shadows=True
    scene.world=bpy.data.worlds.new('V014_WORLD');scene.world.color=(.10,.12,.14)
    skin=mat('SKIN',(.72,.49,.40));face=mat('FACE',(.43,.28,.26));eye=mat('EYE',(.93,.91,.85))
    iris=mat('IRIS',(.11,.45,.48));pupil=mat('PUPIL',(.023,.027,.040))
    ball('FACE_CONTEXT',(0,.26,0),(.80,.49,.78),face)
    globe=ball('EYEBALL_SPHERE',(0,0,0),(R,R,R),eye,segments=96,rings=48)
    center=bpy.data.objects.new('EYE_CENTER',None);bpy.context.collection.objects.link(center)
    guides=make_guides(center)
    rig=make_armature(guides,variant)
    make_lid('UPPER',skin,globe,rig);make_lid('LOWER',skin,globe,rig)
    additional=.028 if variant=='FRONT_IRIS' else 0
    pupil_disk('IRIS',.125,.004+additional,iris)
    pupil_disk('PUPIL',.061,.008+additional,pupil)
    camdat=bpy.data.cameras.new('CAM');cam=bpy.data.objects.new('CAMERA',camdat)
    bpy.context.collection.objects.link(cam);cam.location=(0,-4.5,0)
    cam.rotation_euler=(Vector((0,0,0))-cam.location).to_track_quat('-Z','Y').to_euler()
    camdat.type='ORTHO';camdat.ortho_scale=1.7;scene.camera=cam
    scene['proof_id']=ID;scene['variant']=variant
    out.mkdir(parents=True,exist_ok=True)
    report=evaluate(variant)
    (out/f'{variant}_BUILD.json').write_text(json.dumps(report,indent=2))
    if not report['expected_gate_pass']:raise RuntimeError('NATIVE_V014_MECHANISM_FAILED '+json.dumps(report)[:5000])
    bpy.ops.wm.save_as_mainfile(filepath=str((out/f'{variant}.blend').absolute()))
    print('V014_BUILD_PASS',variant,json.dumps({k:v for k,v in report.items() if k!='samples'}))

def mesh_world(obj,deps):
    ev=obj.evaluated_get(deps);me=ev.to_mesh()
    try:return [ev.matrix_world @ v.co.copy() for v in me.vertices]
    finally:ev.to_mesh_clear()

def mesh_hit_y(obj,deps,x,z):
    ev=obj.evaluated_get(deps)
    matinv=ev.matrix_world.inverted()
    ro=matinv @ Vector((x,-2,z))
    raydir=(matinv.to_3x3() @ Vector((0,1,0))).normalized()
    hit,loc,norm,idx=ev.ray_cast(ro,raydir,distance=4)
    return float((ev.matrix_world @ loc).y) if hit else None

def ray_witness(deps):
    upper=bpy.data.objects['UPPER_SKIN'];lower=bpy.data.objects['LOWER_SKIN'];pup=bpy.data.objects['PUPIL']
    n=0;visible=0;examples=[]
    for i in range(19):
        x=(i-9)*.007
        for j in range(19):
            z=(j-9)*.007
            yp=mesh_hit_y(pup,deps,x,z)
            if yp is None:continue
            n+=1
            ys=[v for v in [mesh_hit_y(upper,deps,x,z),mesh_hit_y(lower,deps,x,z)] if v is not None]
            if not ys or min(ys)>yp-.0001:
                visible+=1
                if len(examples)<7:examples.append([round(x,4),round(z,4),round(yp,5),round(min(ys),5) if ys else None])
    return {'pupil_rays':n,'visible_rays':visible,'visible_fraction':round(visible/n,5) if n else 1.,'visibility_examples':examples}

def evaluate(variant):
    scene=bpy.context.scene
    assert scene['proof_id']==ID and scene['variant']==variant
    rig=bpy.data.objects['V014_SKIN_RIG']
    up=bpy.data.objects['UPPER_SKIN'];lo=bpy.data.objects['LOWER_SKIN']
    assert len(rig.pose.bones)==NB*2+1
    assert up.modifiers[0].type=='ARMATURE' and up.modifiers[1].type=='SHRINKWRAP'
    samples=[];max_guide_bone_error=0.;max_skin_radial_error=0.
    for f in SAMPLE_FRAMES:
        scene.frame_set(f);deps=bpy.context.evaluated_depsgraph_get()
        ug=mesh_world(up,deps);lg=mesh_world(lo,deps)
        radius_err=max(abs(v.length-RG) for v in ug+lg)
        max_skin_radial_error=max(max_skin_radial_error,radius_err)
        errors=[]
        for side in ('UPPER','LOWER'):
            for j in range(NB):
                target=bpy.data.objects[f'{side}_GUIDE_{j}'].evaluated_get(deps).matrix_world.translation
                bone=rig.evaluated_get(deps).pose.bones[f'{side}_DEF_{j}']
                head=rig.evaluated_get(deps).matrix_world @ bone.head
                errors.append((head-target).length)
        ge=max(errors);max_guide_bone_error=max(max_guide_bone_error,ge)
        mid=NX//2
        aperture=(ug[mid*NV]-lg[mid*NV]).length
        record={'frame':f,'aperture_m':round(aperture,7),'guide_bone_error_m':round(ge,7),'skin_radial_error_m':round(radius_err,7)}
        if f in (1,32,72):record['camera_ray_pupil']=ray_witness(deps)
        samples.append(record)
    start=samples[0]['aperture_m'];close=next(x for x in samples if x['frame']==32)
    open_vis=samples[0]['camera_ray_pupil']['visible_fraction']
    closed_vis=close['camera_ray_pupil']['visible_fraction']
    if variant=='COUPLED':
        passed=max_guide_bone_error<.005 and close['aperture_m']<.035 and start>.28 and max_skin_radial_error<.025 and closed_vis<.12 and open_vis>.35
    elif variant=='DISCONNECTED':
        passed=max_guide_bone_error>.08 and close['aperture_m']>.20 and max_skin_radial_error<.025 and closed_vis>.30
    else:
        passed=max_guide_bone_error<.005 and close['aperture_m']<.035 and max_skin_radial_error<.025 and closed_vis>.35
    return {'proof_id':ID,'variant':variant,'blender':bpy.app.version_string,'fps':FPS,'frames':FRAMES,
            'guide_to_def_bone':variant!='DISCONNECTED','deformation_uses_native_armature':True,
            'evaluated_skin_shrinkwrap':True,'max_guide_to_deform_bone_error_m':round(max_guide_bone_error,7),
            'max_evaluated_skin_radial_error_m':round(max_skin_radial_error,7),
            'open_aperture_m':start,'closed_aperture_m':close['aperture_m'],
            'closed_camera_ray_pupil_visible_fraction':closed_vis,
            'open_camera_ray_pupil_visible_fraction':open_vis,
            'expected_gate_pass':bool(passed),'samples':samples,
            'scope':'original spherical socket, weighted strips not contiguous human face; not aesthetic approval',
            'art_status':'NOT_APPROVED','GS001':'UNTOUCHED'}

def verify(variant,out):
    expected=json.loads((out/f'{variant}_BUILD.json').read_text())
    actual=evaluate(variant)
    if expected!=actual or not actual['expected_gate_pass']:
        raise RuntimeError('V014_REOPEN_MISMATCH '+json.dumps({'before':expected,'after':actual})[:6000])
    (out/f'{variant}_REOPEN.json').write_text(json.dumps(actual,indent=2))
    for f in (1,28,32,38,49,72):
        bpy.context.scene.frame_set(f)
        bpy.context.scene.render.filepath=str((out/f'{variant}_frame_{f:04d}.png').absolute())
        bpy.ops.render.render(write_still=True)
    print('V014_REOPEN_PASS',variant,json.dumps({k:v for k,v in actual.items() if k!='samples'}))

if __name__=='__main__':
    at=sys.argv.index('--')+1 if '--' in sys.argv else len(sys.argv)
    args=sys.argv[at:]
    if len(args)!=3:raise ValueError('usage -- build|verify COUPLED|DISCONNECTED|FRONT_IRIS /output')
    mode,variant,out=args
    if variant not in VARIANTS:raise ValueError(variant)
    if mode=='build':build(variant,Path(out))
    elif mode=='verify':verify(variant,Path(out))
    else:raise ValueError(mode)