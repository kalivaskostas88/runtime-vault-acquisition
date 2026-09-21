import bpy, math, json, pathlib, os
from mathutils import Vector

ROOT=pathlib.Path(".")
DOPE=json.loads((ROOT/"config/bard_studio_mechanical_v1_dope.json").read_text())
OUT=pathlib.Path("/tmp/bard_proxy_v1")
OUT.mkdir(parents=True,exist_ok=True)
FPS=int(DOPE["fps"]); DUR=float(DOPE["duration"]); END=int(round(FPS*DUR))

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene
scene.render.engine='BLENDER_WORKBENCH'
scene.render.resolution_x=384
scene.render.resolution_y=576
scene.render.resolution_percentage=100
scene.render.fps=FPS
scene.frame_start=1
scene.frame_end=END
scene.display.shading.light='STUDIO'
scene.display.shading.studio_light='paint.sl'
scene.display.shading.show_shadows=True
scene.display.shading.show_cavity=True
scene.display.shading.cavity_type='BOTH'
scene.display.shading.color_type='MATERIAL'
scene.world.color=(0.035,0.025,0.020)

def mat(name,c):
    m=bpy.data.materials.new(name);m.diffuse_color=(*c,1);return m
WOOD=mat('wood',(0.24,.10,.04)); STONE=mat('stone',(.22,.18,.15)); DARK=mat('dark',(.035,.028,.026))
BURG=mat('burgundy',(.28,.035,.045)); GOLD=mat('ochre',(.42,.24,.06)); SKIN=mat('skin',(.42,.25,.17))
BODY=mat('bard_body',(.22,.20,.18)); BODY2=mat('bard_dark',(.12,.11,.10)); LUTE=mat('lute',(.50,.23,.07))
MOUTH=mat('mouth',(.45,.025,.025)); EYE=mat('eye',(.01,.01,.01)); FIRE=mat('fire',(1.0,.34,.04))

def box(name,loc,dims,ma,bev=.02):
    bpy.ops.mesh.primitive_cube_add(location=loc);o=bpy.context.object;o.name=name;o.dimensions=dims
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    if bev:
        b=o.modifiers.new('bev','BEVEL');b.width=bev;b.segments=2
    o.data.materials.append(ma);return o

def cyl(name,loc,r,d,ma,verts=18):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts,radius=r,depth=d,location=loc)
    o=bpy.context.object;o.name=name;o.data.materials.append(ma);return o

def sph(name,loc,scale,ma):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=20,ring_count=12,location=loc)
    o=bpy.context.object;o.name=name;o.scale=scale;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    o.data.materials.append(ma);return o

def empty(name,loc):
    o=bpy.data.objects.new(name,None);bpy.context.collection.objects.link(o);o.location=loc;return o

def aim(o,target):
    o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()

def f(t):
    return max(1,min(END,int(round(t*FPS))+1))

# ---------------- stage blockout ----------------
box('floor',(0,0,-.1),(12,14,.2),DARK)
box('back',(0,5.15,3.05),(12,.35,6.1),STONE)
for x in (-4.8,-2.8,2.8,4.8): box('beam',(x,4.9,3.1),(.25,.28,5.9),WOOD)
for z in (1.05,3.15,5.2): box('beam',(0,4.9,z),(10.3,.28,.24),WOOD)
box('stage',(-.45,1.45,.22),(5.1,3.0,.44),WOOD,.04)
box('stage_front',(-.45,-.05,.45),(5.25,.18,.72),DARK,.03)
box('rug',(-.45,1.32,.52),(3.5,1.75,.04),BURG,.01)
box('bannerL',(-2.15,4.72,3.4),(1.0,.05,2.6),BURG)
box('bannerR',(1.55,4.72,3.4),(1.0,.05,2.6),BURG)
box('bannerC',(-.25,4.75,4.35),(1.15,.05,1.55),GOLD)

# hearth blockout + fire proxy
HX=3.1
for x in (HX-.6,HX+.6): box('hearth',(x,4.62,1.45),(.55,.62,2.8),STONE,.04)
box('hearth_top',(HX,4.60,2.9),(1.75,.65,.45),STONE,.04)
box('hearth_void',(HX,4.78,1.45),(1.0,.18,2.1),DARK,.01)
for dx,z,s in [(-.25,.70,.22),(0,.88,.30),(.25,.72,.22)]:
    sph('flame',(HX+dx,4.02,z),(s*.45,s*.20,s),FIRE)

# stool and side table
cyl('stool',(-.55,1.35,1.02),.42,.15,WOOD,24)
for dx,dy in ((-.28,-.24),(.28,-.24),(-.28,.24),(.28,.24)): cyl('stool_leg',(-.55+dx,1.35+dy,.52),.05,.95,WOOD,14)
cyl('side_table',(1.20,1.52,1.00),.40,.09,WOOD,24);cyl('side_leg',(1.20,1.52,.54),.08,.90,WOOD,14)
cyl('mug',(1.10,1.47,1.20),.09,.24,GOLD,16)

# audience tables and silhouettes
def table(x,y,w=2.0):
    box('table',(x,y,.76),(w,1.0,.12),WOOD,.03)
    for dx in (-w*.38,w*.38):
        for dy in (-.32,.32): box('leg',(x+dx,y+dy,.38),(.11,.11,.76),WOOD,.01)
for p in [(-3.2,-1.2),(3.0,-1.05),(-2.6,-3.25),(2.7,-3.2)]: table(*p)
for i,(x,y) in enumerate([(-3.6,-1.1),(-2.9,-.9),(2.65,-.9),(3.45,-1.2),(-2.75,-3.1),(2.55,-3.1)]):
    sph('p_head',(x,y,1.78),(.20,.20,.23),SKIN);cyl('p_torso',(x,y,1.15),.28,.82,DARK,16)

# foreground depth
box('fg_table',(0,-5.0,.76),(4.1,1.1,.14),WOOD,.035)
for x in (-3.0,3.05):
    sph('fg_head',(x,-4.15,1.75),(.24,.24,.27),SKIN);cyl('fg_torso',(x,-4.15,1.12),.34,.95,DARK,18)

# ---------------- articulated bard proxy ----------------
ROOTP=empty('BARD_ROOT',(-.55,1.30,0))
TORSO=empty('TORSO_PIVOT',(0,0,1.62));TORSO.parent=ROOTP
torso_mesh=cyl('torso_mesh',(0,0,0),.33,.92,BODY,24);torso_mesh.parent=TORSO
torso_mesh.location=(0,0,0)

# cloak / shoulders
cloak=sph('cloak',(0,.03,.12),(.52,.20,.50),BODY2);cloak.parent=TORSO

HEAD=empty('HEAD_PIVOT',(0,-.01,2.18));HEAD.parent=ROOTP
head=sph('head_mesh',(0,0,0),(.23,.22,.27),SKIN);head.parent=HEAD

# face features (front is -Y)
left_eye=box('eyeL',(-.075,-.218,.045),(.055,.018,.025),EYE,.005);left_eye.parent=HEAD
right_eye=box('eyeR',(.075,-.218,.045),(.055,.018,.025),EYE,.005);right_eye.parent=HEAD
mouth=box('mouth',(0,-.225,-.075),(.16,.018,.035),MOUTH,.005);mouth.parent=HEAD
mouth_base=mouth.scale.copy()

# lute body/neck parented to torso
lute_body=sph('lute_body',(0,-.28,1.48),(.62,.11,.40),LUTE);lute_body.parent=ROOTP
lute_body.rotation_euler=(math.radians(90),0,math.radians(-10))
lute_neck=box('lute_neck',(.55,-.28,1.62),(1.35,.09,.11),LUTE,.018);lute_neck.parent=ROOTP
lute_neck.rotation_euler[1]=math.radians(-8)

# right arm: strumming
RSH=empty('RIGHT_SHOULDER',(-.36,-.02,1.78));RSH.parent=ROOTP
upperR=box('upperR',(-.26,0,-.14),(.16,.15,.58),BODY,.05);upperR.parent=RSH;upperR.rotation_euler[1]=math.radians(-22)
REL=empty('RIGHT_ELBOW',(-.18,-.12,-.40));REL.parent=RSH
foreR=box('foreR',(.23,-.04,-.12),(.54,.14,.14),SKIN,.045);foreR.parent=REL;foreR.rotation_euler[1]=math.radians(-13)
handR=sph('handR',(.52,-.05,-.11),(.10,.07,.09),SKIN);handR.parent=REL

# left arm on neck
LSH=empty('LEFT_SHOULDER',(.38,-.01,1.78));LSH.parent=ROOTP
upperL=box('upperL',(.18,0,-.14),(.16,.15,.56),BODY,.05);upperL.parent=LSH;upperL.rotation_euler[1]=math.radians(30)
handL=sph('handL',(.30,-.27,-.08),(.10,.07,.10),SKIN);handL.parent=LSH

# seated legs
for x in (-.18,.18):
    th=cyl('thigh',(x,.10,.95),.13,.70,BODY2,18);th.parent=ROOTP;th.rotation_euler=(math.radians(70),0,0)
    sh=cyl('shin',(x,-.18,.56),.115,.72,BODY2,18);sh.parent=ROOTP;sh.rotation_euler=(math.radians(-10),0,0)

# ---------------- animation ----------------
# mouth drawing substitutions as stepped scale states
states={
    'M0':(.88,.28),'M1':(.95,.65),'M2':(1.00,1.05),'M3':(1.02,1.70),'ME':(1.18,.72),'MO':(.62,1.45)
}
for seg in DOPE['mouth_segments']:
    fr=f(seg['start']); sx,sz=states[seg['state']]
    mouth.scale=(mouth_base.x*sx,mouth_base.y,mouth_base.z*sz)
    mouth.keyframe_insert(data_path='scale',frame=fr)
    # keep state until end
    mouth.keyframe_insert(data_path='scale',frame=max(fr,f(seg['end'])-1))
# Blender 5.2 uses layered Actions; avoid direct fcurve access here.
# The dope sheet already holds each pose until the frame immediately before
# the next pose, so transitions remain effectively one-frame substitutions.

# blinks: scale eyes vertically around centers
for eye in (left_eye,right_eye):
    base=eye.scale.copy()
    for t in DOPE['blink_centers']:
        for dt,zs in [(-.08,1.0),(-.025,.12),(0,.04),(.04,.28),(.10,1.0)]:
            eye.scale=(base.x,base.y,base.z*zs);eye.keyframe_insert(data_path='scale',frame=f(t+dt))

# head intentional accents only
HEAD.rotation_mode='XYZ'
HEAD.rotation_euler=(0,0,0);HEAD.keyframe_insert(data_path='rotation_euler',frame=1)
for a,b,yaw,nod in DOPE['head_keys']:
    mid=(a+b)/2
    HEAD.rotation_euler=(math.radians(nod*2.1),0,math.radians(yaw*2.1));HEAD.keyframe_insert(data_path='rotation_euler',frame=f(mid))
    HEAD.rotation_euler=(0,0,0);HEAD.keyframe_insert(data_path='rotation_euler',frame=f(b+.06))

# deterministic breathing on torso
TORSO.scale=(1,1,1);TORSO.keyframe_insert(data_path='scale',frame=1)
for fr in range(1,END+1,8):
    t=(fr-1)/FPS
    q=math.sin(2*math.pi*t/3.2)
    TORSO.scale=(1+.010*q,1,1+.006*q);TORSO.keyframe_insert(data_path='scale',frame=fr)

# strum events: elbow rotation around Y, alternating down/up
REL.rotation_mode='XYZ'
base_y=math.radians(-4)
REL.rotation_euler=(0,base_y,0);REL.keyframe_insert(data_path='rotation_euler',frame=1)
for i,t in enumerate(DOPE['strum_centers']):
    amp=math.radians(13 if i%2==0 else -11)
    REL.rotation_euler=(0,base_y,0);REL.keyframe_insert(data_path='rotation_euler',frame=f(t-.10))
    REL.rotation_euler=(0,base_y+amp,0);REL.keyframe_insert(data_path='rotation_euler',frame=f(t))
    REL.rotation_euler=(0,base_y-math.radians(4)*(-1 if i%2 else 1),0);REL.keyframe_insert(data_path='rotation_euler',frame=f(t+.10))
    REL.rotation_euler=(0,base_y,0);REL.keyframe_insert(data_path='rotation_euler',frame=f(t+.19))

# left-hand chord hints
baseLoc=handL.location.copy();handL.keyframe_insert(data_path='location',frame=1)
for i,t in enumerate(DOPE['chord_centers']):
    handL.location=(baseLoc.x+(i%2*2-1)*.07,baseLoc.y,baseLoc.z+.025*(i%2));handL.keyframe_insert(data_path='location',frame=f(t))
    handL.location=baseLoc;handL.keyframe_insert(data_path='location',frame=f(t+.28))

# camera
camd=bpy.data.cameras.new('Camera');cam=bpy.data.objects.new('Camera',camd);bpy.context.collection.objects.link(cam);scene.camera=cam
cam.location=(.65,-9.25,3.0);cam.data.lens=44;cam.data.sensor_width=36
aim(cam,(-.45,1.35,1.55))

# video output
scene.render.filepath=str(OUT/"BARD_STAGE_MECHANICAL_PROXY_V1.mp4")
scene.render.image_settings.file_format='FFMPEG'
scene.render.ffmpeg.format='MPEG4'
scene.render.ffmpeg.codec='H264'
scene.render.ffmpeg.constant_rate_factor='MEDIUM'
scene.render.ffmpeg.ffmpeg_preset='GOOD'
bpy.ops.render.render(animation=True)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/"BARD_STAGE_MECHANICAL_PROXY_V1.blend"))
print('BARD_STAGE_MECHANICAL_PROXY_V1_OK')
