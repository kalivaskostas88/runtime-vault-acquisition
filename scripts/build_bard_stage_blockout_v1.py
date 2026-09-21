import bpy, math, os
from mathutils import Vector

OUT="/tmp/bard_stage_blockout_v1"
os.makedirs(OUT,exist_ok=True)

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene
scene.render.engine='BLENDER_WORKBENCH'
scene.render.resolution_x=512
scene.render.resolution_y=768
scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
scene.display.shading.light='STUDIO'
scene.display.shading.studio_light='paint.sl'
scene.display.shading.show_shadows=True
scene.display.shading.show_cavity=True
scene.display.shading.cavity_type='BOTH'
scene.display.shading.color_type='MATERIAL'
scene.world.color=(0.04,0.03,0.025)

def mat(name,color):
    m=bpy.data.materials.new(name)
    m.diffuse_color=(*color,1)
    return m
WOOD=mat('wood',(0.20,0.09,0.035))
STONE=mat('stone',(0.23,0.20,0.17))
CLOTH=mat('cloth',(0.32,0.035,0.04))
GOLD=mat('ochre',(0.45,0.27,0.06))
DARK=mat('dark',(0.045,0.035,0.03))
SKIN=mat('skin',(0.36,0.20,0.12))

def box(name,loc,dims,ma,bev=.03):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    o=bpy.context.object;o.name=name;o.dimensions=dims
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    if bev:
        b=o.modifiers.new('bev','BEVEL');b.width=bev;b.segments=2
    o.data.materials.append(ma);return o

def cyl(name,loc,r,d,ma,verts=20):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts,radius=r,depth=d,location=loc)
    o=bpy.context.object;o.name=name;o.data.materials.append(ma);return o

def sphere(name,loc,scale,ma):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=20,ring_count=12,location=loc)
    o=bpy.context.object;o.name=name;o.scale=scale
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    o.data.materials.append(ma);return o

def aim(o,target):
    o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()

# room shell
box('floor',(0,0,-.12),(12,14,.24),DARK)
box('back',(0,5.15,3.2),(12,.35,6.4),STONE)
box('left',(-6,0.5,3.2),(.3,9.5,6.4),STONE)
box('right',(6,0.5,3.2),(.3,9.5,6.4),STONE)
for x in (-5.15,-3,3,5.15): box('beam',(x,4.86,3.2),(.25,.28,6.1),WOOD)
for z in (1.05,3.2,5.35): box('beam',(0,4.86,z),(10.6,.28,.25),WOOD)

# stage, deliberately modest not concert-like
box('stage',(0,1.65,.18),(5.8,3.45,.36),WOOD,.05)
for i in range(10):
    box('plank',(-2.6+i*.58,1.63,.39),(.52,3.18,.06),WOOD,.01)
box('fascia',(0,-.02,.42),(5.95,.16,.54),DARK)

# bard reserved zone helper, not rendered as person
# stool center-left
cyl('stool',(-.35,1.55,1.05),.48,.16,WOOD,24)
for dx,dy in ((-.32,-.28),(.32,-.28),(-.32,.28),(.32,.28)):
    cyl('leg',(-.35+dx,1.55+dy,.52),.055,.95,WOOD,16)
# backdrop
box('bannerL',(-2.2,4.7,3.45),(1.18,.05,2.9),CLOTH,.01)
box('bannerR',(2.2,4.7,3.45),(1.18,.05,2.9),CLOTH,.01)
box('bannerC',(0,4.72,4.48),(1.4,.05,1.9),GOLD,.01)

# hearth right
for x in (3.4,4.9): box('hearth_pillar',(x,4.60,1.45),(.62,.65,2.9),STONE,.05)
box('hearth_top',(4.15,4.58,3.0),(2.2,.68,.5),STONE,.05)
box('hearth_floor',(4.15,4.12,.28),(2.4,1.35,.28),STONE,.04)
box('hearth_inner',(4.15,4.78,1.45),(1.16,.18,2.35),DARK,.02)

# small table on stage
cyl('small_table',(1.85,1.75,1.02),.48,.09,WOOD,24)
cyl('small_table_leg',(1.85,1.75,.55),.09,.9,WOOD,16)

# barrels/shelves
for x,y in [(-4.6,3.75),(-4.0,3.86),(4.9,3.65)]:
    b=cyl('barrel',(x,y,.82),.55,1.5,WOOD,24);b.rotation_euler=(math.radians(90),0,0)
for z in (2.0,2.7,3.4): box('shelf',(-4.25,4.60,z),(2.4,.28,.12),WOOD,.02)

# audience tables
def table(x,y):
    box('table',(x,y,.77),(2.25,1.15,.12),WOOD,.04)
    for dx in (-.86,.86):
        for dy in (-.36,.36): box('tleg',(x+dx,y+dy,.38),(.12,.12,.76),DARK,.01)
for x,y in [(-3.25,-1.15),(3.0,-1.0),(-2.55,-3.15),(2.7,-3.25)]: table(x,y)

# low-detail seated patrons, keep central aisle and stage clear
for i,(x,y) in enumerate([(-3.55,-1.1),(-2.85,-.85),(2.65,-.8),(3.35,-1.2),(-2.8,-3.0),(-2.2,-3.35),(2.35,-3.2),(3.1,-3.3)]):
    sphere('head',(x,y,1.83),(.22,.22,.25),SKIN)
    cyl('torso',(x,y,1.15),.28,.85,DARK,18)

# camera
camd=bpy.data.cameras.new('Camera');cam=bpy.data.objects.new('Camera',camd);bpy.context.collection.objects.link(cam);scene.camera=cam
cam.location=(0,-10.8,3.55);aim(cam,(0,1.35,1.55));cam.data.lens=48;cam.data.sensor_width=36

scene.render.filepath=OUT+'/BARD_STAGE_BLOCKOUT_V1.png'
bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=OUT+'/BARD_STAGE_BLOCKOUT_V1.blend')
print('BARD_STAGE_BLOCKOUT_V1_OK')
