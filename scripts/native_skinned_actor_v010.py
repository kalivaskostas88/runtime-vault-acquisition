#!/usr/bin/env python3
"""Blender 5.2.2 original skinned-character proof; no GS001 assets.
Native armature+IK+vertex weights+shape-key facial reaction. Compare GOOD, SYNC,
BAD_WEIGHTS on same source meshes/poses. Mechanical validation only, not art PASS.
CLI: blender -b --factory-startup --python ... -- build VARIANT OUT
     blender -b OUT/VARIANT.blend --python ... -- verify VARIANT OUT
"""
import bpy, json, sys, math
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

FPS, LAST = 24, 72
VALID=('STAGGERED','SIMULTANEOUS','BAD_WEIGHTS')
SIDES={'L':-0.23,'R':0.23}
KEYS=((1,0.0,0.0),(16,0.045,-0.014),(34,0.175,-0.068),(51,0.12,-0.050),(72,0.0,0.0))
FOOT_Z=0.14
RING_N=25
SECTORS=14


def cli():
    if '--' not in sys.argv: raise RuntimeError('Require -- build|verify VARIANT OUT')
    a=sys.argv[sys.argv.index('--')+1:]
    if len(a)!=3 or a[0] not in ('build','verify') or a[1] not in VALID: raise RuntimeError('Bad args: '+str(a))
    return a[0],a[1],Path(a[2]).resolve()


def mat(name,color):
    m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);return m


def sub_color(ob,m):
    ob.data.materials.append(m);return ob


def apply_scale(ob):
    bpy.context.view_layer.objects.active=ob
    bpy.ops.object.select_all(action='DESELECT');ob.select_set(True)
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    ob.select_set(False)


def uv(name,location,scale,material,parent=None,segments=28,rings=16):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments,ring_count=rings,radius=1,location=(0,0,0))
    ob=bpy.context.object;ob.name=name
    ob.scale=scale;apply_scale(ob)
    if parent is not None:ob.parent=parent
    ob.location=location
    sub_color(ob,material)
    return ob


def key_curve(obj,interp='BEZIER'):
    ad=getattr(obj,'animation_data',None)
    if not ad or not ad.action: raise RuntimeError('Missing action on '+str(obj))
    act=ad.action;curves=[]
    try:curves=list(act.fcurves)
    except (TypeError,AttributeError):pass
    if not curves:
        for layer in act.layers:
            for strip in layer.strips:
                for bag in getattr(strip,'channelbags',[]):curves.extend(list(bag.fcurves))
    if not curves:raise RuntimeError('No action FCurves on '+str(obj))
    for cu in curves:
        for kp in cu.keyframe_points:
            kp.interpolation=interp
            if interp=='BEZIER':kp.handle_left_type=kp.handle_right_type='AUTO_CLAMPED'


def rig():
    bpy.ops.object.armature_add(enter_editmode=True,location=(0,0,0))
    rig=bpy.context.object;rig.name='ACTOR_RIG';arm=rig.data;arm.name='ACTOR_LEG_ARMATURE'
    for b in list(arm.edit_bones):arm.edit_bones.remove(b)
    for side,x in SIDES.items():
        hi=arm.edit_bones.new(side+'_THIGH');hi.head=(x,0,0);hi.tail=(x,-0.10,-0.50)
        lo=arm.edit_bones.new(side+'_SHIN');lo.head=hi.tail;lo.tail=(x,0,-1.04)
        lo.parent=hi;lo.use_connect=True
    bpy.ops.object.mode_set(mode='OBJECT')
    rig.location=(0,0,1.12)
    for frame,dx,dz in KEYS:
        rig.location=(dx,0,1.12+dz);rig.keyframe_insert(data_path='location',frame=frame)
    key_curve(rig)
    targets={}
    for side,x in SIDES.items():
        tar=bpy.data.objects.new(side+'_STATIONARY_IK_TARGET',None)
        bpy.context.collection.objects.link(tar);tar.location=(x,0,FOOT_Z)
        tar.empty_display_size=.10
        ik=rig.pose.bones[side+'_SHIN'].constraints.new(type='IK');ik.name='NATIVE_TWO_BONE_IK'
        ik.target=tar;ik.chain_count=2;ik.iterations=150;ik.use_stretch=False
        targets[side]=tar
    return rig,targets


def ring_point(side,t,angle):
    # Anatomical rest centerline follows the exact bent edit-bone chain.
    x=SIDES[side]
    if t<=0.5:
        a=t*2;cx=x;cy=-0.10*a;cz=-0.50*a
    else:
        a=(t-0.5)*2;cx=x;cy=-0.10+0.10*a;cz=-0.50-0.54*a
    radius=(0.125*(1-t)+0.078*t)*(1+0.025*math.cos(2*angle))
    return (cx+radius*math.cos(angle),cy+radius*math.sin(angle),cz)


def build_skin(side,rig,variant,material):
    verts=[];faces=[]
    for ri in range(RING_N):
        t=ri/(RING_N-1)
        for k in range(SECTORS):
            angle=2*math.pi*k/SECTORS
            verts.append(ring_point(side,t,angle))
    for r in range(RING_N-1):
        for k in range(SECTORS):
            a=r*SECTORS+k;b=r*SECTORS+(k+1)%SECTORS
            c=(r+1)*SECTORS+(k+1)%SECTORS;d=(r+1)*SECTORS+k
            faces.append((a,b,c,d))
    faces+=[tuple(reversed(tuple(range(SECTORS)))),tuple((RING_N-1)*SECTORS+k for k in range(SECTORS))]
    mesh=bpy.data.meshes.new(side+'_SKIN_TOPOLOGY')
    mesh.from_pydata(verts,[],faces);mesh.update()
    ob=bpy.data.objects.new(side+'_SKIN',mesh);bpy.context.collection.objects.link(ob)
    ob.parent=rig;ob.location=(0,0,0)
    thigh=ob.vertex_groups.new(name=side+'_THIGH')
    shin=ob.vertex_groups.new(name=side+'_SHIN')
    for r in range(RING_N):
        t=r/(RING_N-1)
        if variant=='BAD_WEIGHTS':
            w_lo=0.0
        else:
            s=max(0,min(1,(t-0.44)/0.12));w_lo=s*s*(3-2*s)
        indices=list(range(r*SECTORS,(r+1)*SECTORS))
        if w_lo < 1-1e-9:thigh.add(indices,max(0,1-w_lo),'REPLACE')
        if w_lo > 1e-9:shin.add(indices,w_lo,'REPLACE')
    deform=ob.modifiers.new('NATIVE_ARMATURE_SKINNING','ARMATURE')
    deform.object=rig;deform.use_vertex_groups=True;deform.use_bone_envelopes=False
    deform.use_deform_preserve_volume=False
    sub_color(ob,material)
    return ob


def mouth_mesh(head,mouthmat):
    n=9;vv=[];fs=[]
    for row in range(2):
        for i in range(n):
            x=-0.125+0.25*i/(n-1)
            z=-0.115-0.006*(1-(x/.125)**2)-0.012*row
            vv.append((x,-.240,z))
    for i in range(n-1):fs.append((i,i+1,n+i+1,n+i))
    me=bpy.data.meshes.new('MOUTH_MESH');me.from_pydata(vv,[],fs);me.update()
    ob=bpy.data.objects.new('MOUTH_SHAPEKEY',me);bpy.context.collection.objects.link(ob)
    ob.parent=head;ob.location=(0,0,0);sub_color(ob,mouthmat)
    ob.shape_key_add(name='Basis',from_mix=False)
    smiling=ob.shape_key_add(name='SMILE',from_mix=False)
    for i in range(n):
        x=vv[i][0]
        ends=(abs(x)/.125)**1.7
        for row in range(2):
            idx=row*n+i
            co=smiling.data[idx].co
            co.z+=0.050*ends-0.018*(1-ends)
    return ob


def char_art(actor,variant,targets):
    skinmat=mat('WARM_SKIN',(0.82,0.55,0.41))
    capmat=mat('INK',(0.16,0.15,0.22))
    clothmat=mat('MOSS_TUNIC',(0.26,0.53,0.50))
    bluemat=mat('LEG_CLOTH',(0.25,0.40,0.69))
    shoemat=mat('BOOTS',(0.43,0.32,0.27))
    eyesmat=mat('EYES_WHITE',(0.93,0.90,0.82))
    pupilmat=mat('PUPIL',(0.16,0.27,0.38))
    blushmat=mat('CHEEKS',(0.78,0.35,0.41))
    flowerpink=mat('FLOWER_PINK',(0.91,0.39,0.51))
    flowerstem=mat('FLOWER_STEM',(0.24,0.52,0.23))
    floor=mat('GROUND',(0.34,0.32,0.32))
    for side in SIDES:
        build_skin(side,actor,variant,bluemat)
        # Ankle-following shoes: foot target visually persists, not claiming physics contact.
        shoe=uv(side+'_SHOE',(SIDES[side],-0.075,.105),(.165,.225,.075),shoemat)
        # shoe doesn't move because contact is locked to world; no hand contact in this experiment.
        shoe['proof']='WORLD_PLANTED_SHOE'
    uv('BODY',(0,0,.445),(.295,.215,.465),clothmat,parent=actor)
    uv('BELT',(0,-.035,.105),(.28,.20,.095),shoemat,parent=actor)
    # Shirt collar as accessory (independent from deforming leg mesh)
    uv('NECK',(0,0,.803),(.11,.12,.16),skinmat,parent=actor)
    # Root/head independently authored from moving pelvis.
    head=uv('HEAD',(0,0,1.034),(.258,.240,.287),skinmat,parent=actor)
    uv('HAIR',(0,.039,.188),(.285,.220,.13),capmat,parent=head)
    # Face points toward camera y<0, with independent gaze offsets.
    pupils=[]
    for side,s in [('L',-1),('R',1)]:
        uv(side+'_EYE_WHITE',(s*.100,-.218,.042),(.059,.030,.071),eyesmat,parent=head)
        pu=uv(side+'_PUPIL',(s*.100,-.248,.040),(.028,.014,.036),pupilmat,parent=head)
        pupils.append(pu)
        uv(side+'_CHEEK',(s*.135,-.197,-.091),(.045,.009,.024),blushmat,parent=head)
    mouth=mouth_mesh(head,capmat)
    # Two arms deliberately unrigged; facial/leg qualification only.
    uv('L_ARM',(-.35,0,.40),(.100,.12,.310),clothmat,parent=actor)
    uv('R_ARM',(.35,0,.40),(.100,.12,.310),clothmat,parent=actor)
    uv('L_HAND',(-.35,-.017,.128),(.078,.090,.108),skinmat,parent=actor)
    uv('R_HAND',(.35,-.017,.128),(.078,.090,.108),skinmat,parent=actor)
    # One original flower as visual stimulus to look at; never moves or transfers.
    bpy.ops.mesh.primitive_cylinder_add(vertices=12,radius=.016,depth=.46,location=(.91,-.43,.64))
    stem=bpy.context.object;stem.name='STATIONARY_FLOWER_STEM';sub_color(stem,flowerstem)
    for k in range(5):
        angle=k*2*math.pi/5
        uv('PETAL_'+str(k),(.91+0.082*math.cos(angle),-.43+0.082*math.sin(angle),.89),(.094,.083,.045),flowerpink)
    uv('FLOWER_CENTER',(.91,-.43,.90),(.055,.055,.053),mat('FLOWER_CENTER_MAT',(0.96,.76,.26)))
    floor_obj=uv('GROUND_TEST_PLANE',(0,0,-.35),(3,3,.34),floor)
    # Orthographic camera, readable head and contacts in frame.
    camd=bpy.data.cameras.new('SHOT_CAMERA');cam=bpy.data.objects.new('SHOT_CAMERA',camd)
    bpy.context.collection.objects.link(cam)
    cam.location=(2.0,-5.8,2.40)
    look=Vector((0.21,0,1.18));cam.rotation_euler=(look-cam.location).to_track_quat('-Z','Y').to_euler()
    camd.type='ORTHO';camd.ortho_scale=4.20;bpy.context.scene.camera=cam
    sc=bpy.context.scene;sc.render.engine='BLENDER_WORKBENCH'
    sc.display.shading.light='STUDIO';sc.display.shading.color_type='MATERIAL'
    sc.display.shading.show_shadows=True;sc.display.shading.show_cavity=True
    sc.render.resolution_x=640;sc.render.resolution_y=480;sc.render.resolution_percentage=100
    sc.render.image_settings.file_format='PNG'
    sc.render.film_transparent=False
    # Reactions: same start and end, only timing differs.
    if variant=='SIMULTANEOUS':
        eye_frames=(20,40);head_frames=(20,40);smile_frames=(20,40)
    else:
        eye_frames=(16,26);head_frames=(31,48);smile_frames=(45,65)
    def keys_of(ob,path,fr0,fr1,a,b):
        setattr(ob,path,a);ob.keyframe_insert(data_path=path,frame=fr0)
        setattr(ob,path,b);ob.keyframe_insert(data_path=path,frame=fr1)
        key_curve(ob)
    for pu in pupils:
        orig=tuple(pu.location)
        for f,x in ((1,orig[0]),(eye_frames[0],orig[0]),(eye_frames[1],orig[0]+.033),(LAST,orig[0]+.033)):
            pu.location.x=x;pu.keyframe_insert(data_path='location',frame=f)
        key_curve(pu)
    for f,a in ((1,0),(head_frames[0],0),(head_frames[1],-.095),(LAST,-.095)):
        head.rotation_euler[1]=a;head.keyframe_insert(data_path='rotation_euler',frame=f)
    key_curve(head)
    smile=mouth.data.shape_keys.key_blocks['SMILE']
    for f,val in ((1,0),(smile_frames[0],0),(smile_frames[1],1),(LAST,1)):
        smile.value=val;smile.keyframe_insert(data_path='value',frame=f)
    key_curve(mouth.data.shape_keys)
    return mouth


def point_eval(eval_obj,ri):
    vs=eval_obj.data.vertices
    base=ri*SECTORS
    p=Vector((0,0,0))
    for j in range(SECTORS):p+=eval_obj.matrix_world @ vs[base+j].co
    return p/SECTORS


def evaluate(variant):
    sc=bpy.context.scene
    actor=bpy.data.objects['ACTOR_RIG']
    skins={side:bpy.data.objects[side+'_SKIN'] for side in SIDES}
    targets={side:bpy.data.objects[side+'_STATIONARY_IK_TARGET'] for side in SIDES}
    mouth=bpy.data.objects['MOUTH_SHAPEKEY']
    eye=bpy.data.objects['L_PUPIL']
    if not all(len(ob.data.vertices)==RING_N*SECTORS for ob in skins.values()):raise RuntimeError('Unexpected skin topology')
    # independent rest and weight validity check
    for side,ob in skins.items():
        for v in ob.data.vertices:
            weights=sum(g.weight for g in v.groups if ob.vertex_groups[g.group].name in (side+'_THIGH',side+'_SHIN'))
            if abs(weights-1)>1e-5:raise RuntimeError('Non-unit vertex sum')
        mods=[x for x in ob.modifiers if x.type=='ARMATURE' and x.object==actor]
        if len(mods)!=1 or mods[0].use_deform_preserve_volume: raise RuntimeError('Native LBS modifier contract failure')
    samples=[];mx_good=0;mx_drift=0;mx_change=0;baseline=None
    max_tip=0
    for f in range(1,LAST+1):
        sc.frame_set(f);dep=bpy.context.evaluated_depsgraph_get()
        erig=actor.evaluated_get(dep)
        for side in SIDES:
            pob=erig.pose.bones[side+'_SHIN'];toe=erig.matrix_world @ pob.tail
            target=targets[side].evaluated_get(dep).matrix_world.translation
            max_tip=max(max_tip,(toe-target).length)
            if baseline is None:pass
            eob=skins[side].evaluated_get(dep)
            ankle=point_eval(eob,RING_N-1)
            mx_good=max(mx_good,(toe-ankle).length)
            orig=skins[side].matrix_world @ skins[side].data.vertices[(RING_N//2+3)*SECTORS].co
            moved=eob.matrix_world @ eob.data.vertices[(RING_N//2+3)*SECTORS].co
            mx_change=max(mx_change,(moved-orig).length)
            if f in (1,16,24,34,48,65,72) and side=='L':
                samples.append({'frame':f,'toe':[round(v,5) for v in toe],
                                'skin_ankle':[round(v,5) for v in ankle],
                                'ankle_gap_m':round((toe-ankle).length,7)})
    # now check face shape key and gaze intermediate values and endpoints
    if bpy.data.objects['MOUTH_SHAPEKEY'].data.shape_keys is None:raise RuntimeError('No native expression shape key')
    values={}
    for f in (1,24,36,52,72):
        sc.frame_set(f);dep=bpy.context.evaluated_depsgraph_get()
        values[str(f)]={'smile':round(float(mouth.data.shape_keys.key_blocks['SMILE'].value),5),
                        'eye_local_x':round(float(eye.location.x),5)}
    if abs(values['1']['smile'])>1e-6 or abs(values['72']['smile']-1)>1e-6:raise RuntimeError('Expression endpoints invalid')
    if max_tip>.005:raise RuntimeError('IK solver tip error too large '+str(max_tip))
    if mx_change<.045:raise RuntimeError('No evaluated native mesh deformation '+str(mx_change))
    # For negative control, large toe/skin detachment is expected and MUST be observed.
    valid=mx_good>.060 if variant=='BAD_WEIGHTS' else mx_good<.012
    if not valid:raise RuntimeError('Ankle-skin native deformation gate failed: '+json.dumps({'variant':variant,'gap':mx_good,'deform':mx_change}) )
    # Positive cases must be genuinely segmented skin vs bad all-thigh weights.
    sum_shin=sum(sum(g.weight for g in v.groups if skins['L'].vertex_groups[g.group].name=='L_SHIN') for v in skins['L'].data.vertices)
    if variant=='BAD_WEIGHTS' and sum_shin!=0:raise RuntimeError('Bad weights negative control not isolated')
    if variant!='BAD_WEIGHTS' and sum_shin<50:raise RuntimeError('Shin skin weights unexpectedly missing')
    # Independent shot-camera framing: ALL head/hair top + both planted soles
    # must remain safely within render. The first real V010 run had mechanical
    # PASS but CUT OFF THE FACE; that is a genuine shot-qualification failure.
    cam=sc.camera
    frame_margin=1.0
    for f in (1,24,48,LAST):
        sc.frame_set(f);dep=bpy.context.evaluated_depsgraph_get()
        head=bpy.data.objects['HEAD'].evaluated_get(dep)
        points=[head.matrix_world @ Vector((0,0,.345))]
        for side in SIDES:
            shoe=bpy.data.objects[side+'_SHOE'].evaluated_get(dep)
            points.append(shoe.matrix_world @ Vector((0,0,-.078)))
        for pos in points:
            pr=world_to_camera_view(sc,cam,pos)
            if pr.z<=0:raise RuntimeError('Camera target behind camera')
            frame_margin=min(frame_margin,pr.x,1-pr.x,pr.y,1-pr.y)
            if not (0.048<pr.x<.952 and 0.048<pr.y<.952):
                raise RuntimeError('CAMERA_FRAMING_FAIL: character cropped at frame '
                                   +str(f)+' projection='+str(tuple(round(v,5) for v in pr)))
    out={'status':'MECHANICAL_PASS','variant':variant,'blender':bpy.app.version_string,
         'frames':LAST,'fps':FPS,'vertices_per_leg':RING_N*SECTORS,
         'max_ik_tip_error_m':round(max_tip,8),
         'minimum_camera_subject_margin_normalized':round(frame_margin,6),
         'max_skin_ankle_gap_m':round(mx_good,8),
         'max_native_deformation_m':round(mx_change,8),
         'shin_weight_total_left':round(sum_shin,5),
         'expected_negative_control':variant=='BAD_WEIGHTS',
         'facial_sample_values':values,'anatomical_approval':'NOT_REVIEWED',
         'com_and_balance':'NOT_MEASURED','artistic_approval':'NOT_REVIEWED',
         'GS001':'NOT_TOUCHED','samples':samples}
    return out


def build(variant,out):
    if tuple(bpy.app.version)!=(5,2,2):raise RuntimeError('Exact Blender 5.2.2 required')
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    out.mkdir(parents=True,exist_ok=True)
    sc=bpy.context.scene;sc.frame_start=1;sc.frame_end=LAST;sc.render.fps=FPS
    actor,targets=rig()
    char_art(actor,variant,targets)
    receipt=evaluate(variant)
    sc.frame_set(1)
    bpy.ops.wm.save_as_mainfile(filepath=str(out/(variant+'.blend')))
    (out/(variant+'_BUILD.json')).write_text(json.dumps(receipt,indent=2))
    print('NATIVE_SKIN_BUILD_PASS',variant,json.dumps({k:v for k,v in receipt.items() if k not in ('samples','facial_sample_values')}))


def verify(variant,out):
    if tuple(bpy.app.version)!=(5,2,2):raise RuntimeError('Version mismatch')
    old=json.loads((out/(variant+'_BUILD.json')).read_text())
    fresh=evaluate(variant)
    if fresh!=old:raise RuntimeError('Fresh reopen semantic data not equal')
    sc=bpy.context.scene
    for f in (1,24,48,72):
        sc.frame_set(f)
        sc.render.filepath=str(out/f'{variant}_frame_{f:04d}.png')
        bpy.ops.render.render(write_still=True)
    (out/(variant+'_REOPEN.json')).write_text(json.dumps(fresh,indent=2))
    print('NATIVE_SKIN_REOPEN_PASS',variant)


if __name__=='__main__':
    mode,variant,out=cli()
    if mode=='build':build(variant,out)
    else:verify(variant,out)