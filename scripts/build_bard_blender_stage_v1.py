import bpy
import math
import random
from mathutils import Vector

SEED = 260921
rng = random.Random(SEED)
OUT = "/tmp/bard_stage_v1"

# ---------- scene reset ----------
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
for datablocks in (bpy.data.meshes, bpy.data.curves, bpy.data.materials, bpy.data.cameras, bpy.data.lights):
    pass

scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 768
scene.render.resolution_y = 1152
scene.render.resolution_percentage = 100
scene.render.fps = 25
scene.frame_start = 1
scene.frame_end = 200
scene.render.image_settings.file_format = 'PNG'
scene.render.film_transparent = False
try:
    scene.view_settings.look = 'AgX - Medium High Contrast'
except Exception:
    pass
scene.world.color = (0.012, 0.008, 0.006)

# ---------- helpers ----------
def rgba(hexstr, a=1.0):
    s = hexstr.lstrip('#')
    return tuple(int(s[i:i+2],16)/255 for i in (0,2,4)) + (a,)

def mat_principled(name, base, rough=0.55, metallic=0.0):
    m=bpy.data.materials.new(name)
    m.use_nodes=True
    bsdf=m.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value=base
    bsdf.inputs['Roughness'].default_value=rough
    bsdf.inputs['Metallic'].default_value=metallic
    return m

def mat_emission(name, color, strength):
    m=bpy.data.materials.new(name)
    m.use_nodes=True
    nt=m.node_tree
    nt.nodes.clear()
    out=nt.nodes.new('ShaderNodeOutputMaterial')
    em=nt.nodes.new('ShaderNodeEmission')
    em.inputs['Color'].default_value=color
    em.inputs['Strength'].default_value=strength
    nt.links.new(em.outputs['Emission'], out.inputs['Surface'])
    return m

def add_box(name, loc, dims, mat, bevel=0.03):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    o=bpy.context.object
    o.name=name
    o.dimensions=dims
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel>0:
        mod=o.modifiers.new('soft_edges','BEVEL')
        mod.width=bevel
        mod.segments=2
    o.data.materials.append(mat)
    return o

def add_cyl(name, loc, radius, depth, mat, vertices=32):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=loc)
    o=bpy.context.object
    o.name=name
    o.data.materials.append(mat)
    return o

def add_sphere(name, loc, scale, mat):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, location=loc)
    o=bpy.context.object
    o.name=name
    o.scale=scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    o.data.materials.append(mat)
    return o

def aim(obj, target):
    direction=Vector(target)-obj.location
    obj.rotation_euler=direction.to_track_quat('-Z','Y').to_euler()

def add_point(name, loc, color, energy, radius=0.3):
    data=bpy.data.lights.new(name,'POINT')
    data.color=color
    data.energy=energy
    data.shadow_soft_size=radius
    o=bpy.data.objects.new(name,data)
    bpy.context.collection.objects.link(o)
    o.location=loc
    return o

def add_area(name, loc, target, color, energy, size):
    data=bpy.data.lights.new(name,'AREA')
    data.color=color
    data.energy=energy
    data.shape='DISK'
    data.size=size
    o=bpy.data.objects.new(name,data)
    bpy.context.collection.objects.link(o)
    o.location=loc
    aim(o,target)
    return o

def key(obj, prop_path, values):
    for frame,val in values:
        setattr(obj, prop_path, val)
        obj.keyframe_insert(data_path=prop_path, frame=frame)

# ---------- materials ----------
WOOD=mat_principled('wood', rgba('#3b2114'), .72)
WOOD2=mat_principled('wood_dark', rgba('#23150f'), .78)
WOOD3=mat_principled('wood_stage', rgba('#5a3420'), .64)
STONE=mat_principled('stone', rgba('#40372f'), .92)
STONE2=mat_principled('stone_var', rgba('#55483b'), .89)
CLOTH=mat_principled('cloth_burgundy', rgba('#4c1518'), .83)
CLOTH2=mat_principled('cloth_ochre', rgba('#6a4b1f'), .86)
METAL=mat_principled('metal', rgba('#302924'), .36, .65)
MUG=mat_principled('ceramic', rgba('#4d3122'), .8)
PEOPLE=mat_principled('audience_dark', rgba('#171313'), .85)
PEOPLE2=mat_principled('audience_brown', rgba('#2b1c17'), .82)
SKIN=mat_principled('audience_skin', rgba('#6b4936'), .72)
FLAME=mat_emission('flame', rgba('#ff8b22'), 5.2)
FLAME2=mat_emission('flame_core', rgba('#ffd98c'), 8.0)

# ---------- room ----------
add_box('floor',(0,0,-0.12),(12,14,.24),WOOD2,.02)
add_box('back_wall',(0,5.15,3.2),(12,.38,6.4),STONE,.05)
add_box('left_wall',(-6.0,0.5,3.2),(.34,9.5,6.4),STONE,.05)
add_box('right_wall',(6.0,0.5,3.2),(.34,9.5,6.4),STONE,.05)

# timber beams on back wall
for x in (-5.15,-3.0,3.0,5.15):
    add_box(f'beam_v_{x}',(x,4.88,3.25),(.26,.28,6.1),WOOD,.03)
for z in (1.05,3.2,5.35):
    add_box(f'beam_h_{z}',(0,4.86,z),(10.6,.28,.26),WOOD,.03)
# ceiling beams
for x in (-4.8,-2.4,0,2.4,4.8):
    add_box(f'ceiling_{x}',(x,0.6,5.9),(.22,10.0,.24),WOOD,.03)

# ---------- stage ----------
add_box('stage_base',(0,1.65,.18),(5.8,3.45,.36),WOOD3,.05)
# individual planks for read
for i in range(10):
    x=-2.6+i*.58
    add_box(f'stage_plank_{i}',(x,1.63,.39),(.52,3.18,.06),WOOD if i%2 else WOOD3,.015)
# modest front fascia
add_box('stage_fascia',(0,-.02,.42),(5.95,.16,.54),WOOD2,.03)

# back curtains / banners
add_box('banner_left',(-2.2,4.71,3.4),(1.18,.05,2.9),CLOTH,.015)
add_box('banner_right',(2.2,4.71,3.4),(1.18,.05,2.9),CLOTH,.015)
add_box('banner_center',(0,4.73,4.45),(1.4,.05,1.9),CLOTH2,.015)

# stool/chair center-left: reserved for bard
add_cyl('stool_seat',(-.35,1.55,1.05),.48,.16,WOOD,32)
for dx,dy in ((-.32,-.28),(.32,-.28),(-.32,.28),(.32,.28)):
    leg=add_cyl('stool_leg',(-.35+dx,1.55+dy,.52),.055,.95,WOOD,20)

# stage side table
add_cyl('small_table_top',(1.85,1.75,1.02),.48,.09,WOOD,32)
add_cyl('small_table_leg',(1.85,1.75,.55),.09,.9,WOOD2,24)
add_cyl('tankard',(1.73,1.70,1.22),.105,.26,MUG,24)
add_cyl('tankard_handle',(1.86,1.70,1.22),.055,.12,METAL,20)

# ---------- hearth on right ----------
# hearth opening at x 4.05
hx,hy=4.15,4.67
for x in (3.4,4.9):
    add_box('hearth_pillar',(x,4.60,1.45),(.62,.65,2.9),STONE2,.05)
add_box('hearth_top',(4.15,4.58,3.0),(2.2,.68,.5),STONE2,.05)
add_box('hearth_floor',(4.15,4.12,.28),(2.4,1.35,.28),STONE,.04)
# inner dark cavity
add_box('hearth_inner',(4.15,4.78,1.45),(1.16,.18,2.35),WOOD2,.02)

# logs
for i in range(4):
    log=add_cyl(f'log_{i}',(3.78+i*.25,4.08,.55),.11,1.05,WOOD2,20)
    log.rotation_euler=(0,math.radians(78),math.radians(8*(i-1)))

# animated flames + light
flame_objs=[]
for idx,(x,z,s) in enumerate(((3.82,.75,.28),(4.12,.90,.38),(4.42,.74,.30),(4.02,.60,.22))):
    o=add_sphere(f'flame_{idx}',(x,4.02,z),(s*.55,s*.25,s*1.2),FLAME if idx%2 else FLAME2)
    flame_objs.append(o)
    base=o.scale.copy()
    for fr,fac,dx in ((1,1.0,0),(25,1.18,.04),(50,.82,-.03),(75,1.12,.02),(100,.9,-.02),(125,1.2,.03),(150,.84,-.04),(175,1.14,.02),(200,1.0,0)):
        o.scale=(base.x*fac,base.y,base.z*(.82+fac*.18))
        o.location.x=x+dx
        o.keyframe_insert(data_path='scale',frame=fr)
        o.keyframe_insert(data_path='location',frame=fr)

firelight=add_point('firelight',(4.1,3.65,1.55),(1.0,.32,.08),980,1.25)
for fr,en in ((1,900),(25,1120),(50,760),(75,1040),(100,820),(125,1170),(150,730),(175,1060),(200,900)):
    firelight.data.energy=en
    firelight.data.keyframe_insert(data_path='energy',frame=fr)

# ---------- candles ----------
def add_candle(name,x,y,z):
    add_cyl(name+'_wax',(x,y,z),.07,.46,mat_principled(name+'_waxmat',rgba('#c9a66b'),.74),20)
    f=add_sphere(name+'_flame',(x,y,z+.30),(.035,.025,.09),FLAME2)
    light=add_point(name+'_light',(x,y-.05,z+.34),(1.0,.52,.18),115,.22)
    for fr,fac in ((1,1.0),(30,.78),(60,1.14),(90,.86),(120,1.18),(150,.82),(180,1.10),(200,1.0)):
        f.scale=(.035*(.92+fac*.08),.025,.09*fac)
        f.keyframe_insert(data_path='scale',frame=fr)
        light.data.energy=105*fac
        light.data.keyframe_insert(data_path='energy',frame=fr)

for j,p in enumerate([(-2.45,2.55,1.25),(2.3,2.75,1.18),(-3.3,-1.4,1.02),(3.35,-1.0,1.04)]):
    add_candle(f'candle_{j}',*p)

# ---------- tavern props ----------
# barrels
for i,(x,y) in enumerate([(-4.6,3.75),(-4.0,3.86),(4.9,3.65)]):
    b=add_cyl(f'barrel_{i}',(x,y,.82),.55,1.5,WOOD,32)
    b.rotation_euler=(math.radians(90),0,0)
    for oz in (-.48,.48):
        r=add_cyl(f'barrel_ring_{i}_{oz}',(x,y,.82+oz),.565,.035,METAL,32)

# side shelves
for y,z in ((4.60,2.0),(4.60,2.7),(4.60,3.4)):
    add_box(f'shelf_{z}',(-4.25,y,z),(2.4,.28,.12),WOOD,.02)
for k in range(12):
    x=-5.0+(k%4)*.48
    z=2.13+(k//4)*.7
    add_cyl(f'bottle_{k}',(x,4.36,z),.08,.34,MUG,16)

# ---------- audience tables ----------
def add_table(name,x,y):
    add_box(name+'_top',(x,y,.77),(2.25,1.15,.12),WOOD,.04)
    for dx in (-.86,.86):
        for dy in (-.36,.36):
            add_box(name+'_leg',(x+dx,y+dy,.38),(.12,.12,.76),WOOD2,.02)

for idx,(x,y) in enumerate([(-3.25,-1.15),(3.0,-1.0),(-2.55,-3.15),(2.7,-3.25)]):
    add_table(f'table_{idx}',x,y)

def add_patron(name,x,y,z=0.0,turn=0.0,mat=PEOPLE):
    torso=add_cyl(name+'_torso',(x,y,1.15+z),.28,.85,mat,24)
    torso.rotation_euler=(0,0,turn)
    add_sphere(name+'_head',(x,y,1.83+z),(.22,.22,.25),SKIN)
    # shoulder mass
    add_sphere(name+'_shoulder',(x,y,1.42+z),(.42,.24,.20),mat)

# deliberately low-detail / subdued audience
patrons=[(-3.55,-1.1,.2),(-2.85,-.85,-.3),(2.65,-.8,.35),(3.35,-1.2,-.4),(-2.8,-3.0,.1),(-2.2,-3.35,-.2),(2.35,-3.2,.25),(3.1,-3.3,-.25)]
for i,(x,y,t) in enumerate(patrons):
    add_patron(f'patron_{i}',x,y,0,t,PEOPLE if i%2==0 else PEOPLE2)

# ---------- lighting ----------
add_area('key',(-2.0,-2.0,5.0),(0,1.5,1.5),(1.0,.58,.30),920,5.0)
add_area('fill',(3.5,-1.5,4.6),(0,1.7,1.4),(.32,.38,.52),260,4.5)
add_area('stage_warm',(0,3.2,5.0),(0,1.4,1.2),(1.0,.42,.16),480,3.5)
add_point('stage_rim',(-2.7,3.5,3.2),(1.0,.27,.09),310,.65)

# ---------- camera ----------
cam_data=bpy.data.cameras.new('Camera')
cam=bpy.data.objects.new('Camera',cam_data)
bpy.context.collection.objects.link(cam)
scene.camera=cam
cam.location=(0,-10.8,3.55)
aim(cam,(0,1.35,1.55))
cam.data.lens=48
cam.data.sensor_width=36
cam.data.dof.use_dof=True
focus=bpy.data.objects.new('Focus',None)
bpy.context.collection.objects.link(focus)
focus.location=(0,1.45,1.45)
cam.data.dof.focus_object=focus
cam.data.dof.aperture_fstop=3.6

# foreground framing beams / chair backs for depth
add_box('foreground_left',(-5.1,-4.7,1.25),(1.35,.55,2.5),WOOD2,.12)
add_box('foreground_right',(5.0,-4.55,1.05),(1.45,.55,2.1),WOOD2,.12)

# ---------- render representative frames ----------
import os
os.makedirs(OUT, exist_ok=True)
frames=[1,66,133,200]
for fr in frames:
    scene.frame_set(fr)
    scene.render.filepath=f"{OUT}/stage_{fr:03d}.png"
    bpy.ops.render.render(write_still=True)

bpy.ops.wm.save_as_mainfile(filepath=f"{OUT}/BARD_STAGE_ENVIRONMENT_V1.blend")
print("BARD_STAGE_ENVIRONMENT_V1_OK")
