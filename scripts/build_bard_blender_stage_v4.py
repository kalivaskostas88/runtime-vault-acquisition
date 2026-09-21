import bpy, math, os, random
from mathutils import Vector

OUT="/tmp/bard_stage_v4"
os.makedirs(OUT,exist_ok=True)
rng=random.Random(260921)

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

scene=bpy.context.scene
scene.render.engine='BLENDER_EEVEE'
scene.render.resolution_x=640
scene.render.resolution_y=960
scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
scene.render.film_transparent=False
scene.world.color=(0.004,0.003,0.002)
try:
    scene.view_settings.look='AgX - Medium High Contrast'
except Exception:
    pass
scene.view_settings.exposure=-0.65

def rgba(h,a=1.0):
    h=h.lstrip('#')
    return tuple(int(h[i:i+2],16)/255 for i in (0,2,4))+(a,)

def principled(name,base,rough=.7,metal=0.0):
    m=bpy.data.materials.new(name);m.use_nodes=True
    b=m.node_tree.nodes.get('Principled BSDF')
    b.inputs['Base Color'].default_value=base
    b.inputs['Roughness'].default_value=rough
    b.inputs['Metallic'].default_value=metal
    return m

def procedural(name,c0,c1,scale,rough=.78,bump=.18):
    m=bpy.data.materials.new(name);m.use_nodes=True
    nt=m.node_tree;bs=nt.nodes.get('Principled BSDF')
    tex=nt.nodes.new('ShaderNodeTexNoise')
    tex.inputs['Scale'].default_value=scale
    tex.inputs['Detail'].default_value=4.0
    tex.inputs['Roughness'].default_value=.68
    ramp=nt.nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].color=c0
    ramp.color_ramp.elements[1].color=c1
    nt.links.new(tex.outputs['Fac'],ramp.inputs['Fac'])
    nt.links.new(ramp.outputs['Color'],bs.inputs['Base Color'])
    bs.inputs['Roughness'].default_value=rough
    bp=nt.nodes.new('ShaderNodeBump')
    bp.inputs['Strength'].default_value=.38
    bp.inputs['Distance'].default_value=bump
    nt.links.new(tex.outputs['Fac'],bp.inputs['Height'])
    nt.links.new(bp.outputs['Normal'],bs.inputs['Normal'])
    return m

def emissive(name,color,strength):
    m=bpy.data.materials.new(name);m.use_nodes=True
    bs=m.node_tree.nodes.get('Principled BSDF')
    bs.inputs['Base Color'].default_value=color
    bs.inputs['Emission Color'].default_value=color
    bs.inputs['Emission Strength'].default_value=strength
    bs.inputs['Roughness'].default_value=.3
    return m

WOOD=procedural('wood',rgba('#1a0e08'),rgba('#66391e'),5.5,.75,.10)
WOOD_D=procedural('wood_dark',rgba('#0e0906'),rgba('#3d2114'),6.5,.82,.10)
WOOD_L=procedural('stage_wood',rgba('#2b150b'),rgba('#7e4728'),7.0,.65,.08)
STONE=procedural('stone',rgba('#24211f'),rgba('#594c41'),3.1,.94,.20)
STONE_D=procedural('stone_dark',rgba('#11100f'),rgba('#2a2420'),3.8,.95,.17)
CLOTH=principled('cloth',rgba('#370c12'),.92)
CLOTH_G=principled('cloth_gold',rgba('#5c3b18'),.90)
METAL=principled('iron',rgba('#25211e'),.38,.72)
CERAMIC=procedural('ceramic',rgba('#2e1b14'),rgba('#5c3420'),7.5,.82,.04)
SKIN=principled('skin',rgba('#4b2d20'),.75)
PATRON=principled('patron',rgba('#100c0b'),.90)
PATRON2=principled('patron2',rgba('#24140f'),.88)
PROXY=principled('proxy',rgba('#61594f'),.78)
LUTE=procedural('lute',rgba('#43200e'),rgba('#8c4d24'),8,.58,.05)
FLAME=emissive('flame',rgba('#ff7516'),6.0)
CORE=emissive('core',rgba('#ffd57f'),9.0)

def box(name,loc,dims,mat,bevel=.02):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    o=bpy.context.object;o.name=name;o.dimensions=dims
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    if bevel:
        b=o.modifiers.new('bevel','BEVEL');b.width=bevel;b.segments=2
    o.data.materials.append(mat);return o

def cyl(name,loc,r,d,mat,verts=24):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts,radius=r,depth=d,location=loc)
    o=bpy.context.object;o.name=name;o.data.materials.append(mat);return o

def sphere(name,loc,scale,mat,seg=24):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg,ring_count=12,location=loc)
    o=bpy.context.object;o.name=name;o.scale=scale
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    o.data.materials.append(mat);return o

def aim(o,target):
    o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()

def point(name,loc,color,energy,radius=.3):
    d=bpy.data.lights.new(name,'POINT');d.color=color;d.energy=energy;d.shadow_soft_size=radius
    o=bpy.data.objects.new(name,d);bpy.context.collection.objects.link(o);o.location=loc;return o

def area(name,loc,target,color,energy,size):
    d=bpy.data.lights.new(name,'AREA');d.color=color;d.energy=energy;d.shape='DISK';d.size=size
    o=bpy.data.objects.new(name,d);bpy.context.collection.objects.link(o);o.location=loc;aim(o,target);return o

# --- room shell ---
box('floor',(0,0,-.12),(11.5,13,.24),WOOD_D,.02)
box('back',(0,5.05,3.0),(11.5,.34,6.0),STONE,.035)
box('left',(-5.75,.6,3.0),(.30,9.0,6.0),STONE_D,.035)
box('right',(5.75,.6,3.0),(.30,9.0,6.0),STONE_D,.035)

# stone breakup
for row,z in enumerate([.42,1.02,1.62,2.22,2.82,3.42,4.02,4.62,5.22]):
    x=-5.15+(row%2)*.32
    while x<5.2:
        w=rng.uniform(.52,.95)
        box('stone_block',(x+w/2,4.87,z),(w,.15,.43),STONE if rng.random()>.28 else STONE_D,.02)
        x+=w+rng.uniform(.07,.15)

# timber frame
for x in (-5.0,-3.05,3.05,5.0): box('beam_v',(x,4.75,3.0),(.22,.24,5.9),WOOD,.028)
for z in (.92,3.02,5.08): box('beam_h',(0,4.74,z),(10.3,.24,.22),WOOD,.028)
for x in (-4.4,-2.2,0,2.2,4.4): box('ceiling_beam',(x,.45,5.68),(.20,8.9,.22),WOOD,.028)

# --- modest raised stage ---
box('stage_base',(-.3,1.35,.22),(5.0,2.85,.44),WOOD_L,.05)
for i in range(9):
    box('plank',(-2.62+i*.58,1.34,.48),(.52,2.56,.07),WOOD_L if i%2 else WOOD,.01)
box('stage_front',(-.3,-.08,.45),(5.15,.18,.72),WOOD_D,.03)
box('step_low',(-2.2,-.56,.14),(1.05,.68,.28),WOOD_L,.025)
box('step_high',(-2.2,-.28,.30),(1.05,.50,.18),WOOD_L,.025)

# textiles
box('banner_l',(-2.0,4.62,3.4),(.92,.05,2.55),CLOTH,.012)
box('banner_r',(1.55,4.62,3.4),(.92,.05,2.55),CLOTH,.012)
box('banner_c',(-.2,4.64,4.35),(1.05,.05,1.55),CLOTH_G,.012)

# stool and side table
cyl('stool_seat',(-.52,1.28,1.02),.42,.15,WOOD,28)
for dx,dy in ((-.28,-.23),(.28,-.23),(-.28,.23),(.28,.23)):
    cyl('stool_leg',(-.52+dx,1.28+dy,.50),.047,.92,WOOD,16)
cyl('table_top',(1.16,1.46,1.00),.40,.09,WOOD,28)
cyl('table_leg',(1.16,1.46,.54),.075,.88,WOOD_D,18)
cyl('mug',(1.05,1.41,1.22),.085,.23,CERAMIC,20)

# hearth right, visible but not dominant
hx=3.15
for x in (hx-.60,hx+.60): box('hearth_pillar',(x,4.52,1.42),(.52,.58,2.80),STONE,.04)
box('hearth_top',(hx,4.51,2.86),(1.70,.62,.44),STONE,.04)
box('hearth_floor',(hx,4.10,.28),(1.95,1.22,.28),STONE_D,.035)
box('hearth_void',(hx,4.68,1.42),(.98,.18,2.08),STONE_D,.01)
for i in range(4):
    log=cyl('log',(hx-.32+i*.21,4.0,.55),.095,.78,WOOD_D,16)
    log.rotation_euler=(0,math.radians(78),math.radians((i-1.5)*10))
for i,(dx,z,s) in enumerate([(-.30,.70,.22),(-.08,.88,.33),(.18,.69,.24),(.34,.78,.18)]):
    sphere('flame',(hx+dx,3.95,z),(s*.48,s*.22,s*1.1),CORE if i==1 else FLAME)
point('firelight',(hx,3.65,1.35),(1.0,.24,.05),720,1.05)

# wall candle sconces
for i,(x,z) in enumerate([(-4.15,2.55),(-2.75,2.75),(.85,2.82)]):
    box('sconce',(x,4.55,z),(.16,.26,.09),METAL,.012)
    wax=principled(f'wax_{i}',rgba('#c3a069'),.8)
    cyl('candle',(x,4.38,z+.20),.052,.30,wax,16)
    sphere('flame',(x,4.36,z+.40),(.032,.023,.082),CORE)
    point('candle_light',(x,4.13,z+.42),(1.0,.46,.13),72,.17)

# shelves / barrels / props
for z in (1.62,2.28,2.94): box('shelf',(-4.38,4.47,z),(1.9,.25,.10),WOOD,.018)
for k in range(9):
    x=-4.98+(k%3)*.52; z=1.75+(k//3)*.66
    cyl('bottle',(x,4.27,z),.065,.28,CERAMIC,14)
for x,y in [(-4.62,3.65),(-4.03,3.78),(4.42,3.72)]:
    b=cyl('barrel',(x,y,.80),.50,1.35,WOOD,24);b.rotation_euler=(math.radians(90),0,0)

# foreground and audience tables
def table(x,y,w=1.9):
    box('table',(x,y,.76),(w,.95,.11),WOOD,.03)
    for dx in (-w*.38,w*.38):
        for dy in (-.30,.30): box('table_leg',(x+dx,y+dy,.38),(.10,.10,.74),WOOD_D,.01)
for p in [(-3.2,-1.15),(3.0,-1.05),(-2.6,-3.0),(2.75,-3.0)]: table(*p)

# patrons, purposely low-detail and low-light
for i,(x,y) in enumerate([(-3.55,-1.1),(-2.85,-.95),(2.55,-.90),(3.35,-1.20),(-2.78,-2.96),(-2.08,-3.22),(2.36,-2.95),(3.12,-3.18)]):
    sphere('head',(x,y,1.76),(.19,.19,.22),SKIN)
    cyl('torso',(x,y,1.15),.26,.78,PATRON if i%2==0 else PATRON2,18)

# subtle foreground occluders for depth
sphere('fg_head_l',(-4.25,-5.0,1.65),(.48,.40,.52),PATRON)
sphere('fg_head_r',(4.15,-4.85,1.56),(.44,.38,.48),PATRON2)

# proxy collection
proxy_objs=[]
proxy_objs.append(sphere('proxy_head',(-.50,1.20,2.18),(.21,.21,.25),PROXY))
proxy_objs.append(cyl('proxy_torso',(-.50,1.20,1.62),.29,.82,PROXY,20))
lute=sphere('proxy_lute',(-.22,1.02,1.50),(.60,.12,.38),LUTE);proxy_objs.append(lute)
neck=box('proxy_neck',(.40,1.02,1.62),(1.00,.10,.11),LUTE,.02);neck.rotation_euler[1]=math.radians(-8);proxy_objs.append(neck)

# lights
area('key',(-2.5,-2.3,4.5),(-.35,1.2,1.55),(1.0,.48,.22),560,3.6)
area('fill',(3.7,-1.2,4.0),(-.35,1.2,1.45),(.23,.30,.47),85,4.0)
area('backwarm',(-.15,3.7,4.3),(-.35,1.2,1.65),(1.0,.30,.08),280,2.8)
point('rim',(-2.65,3.1,2.9),(1.0,.18,.04),145,.42)

# volume haze
volmat=bpy.data.materials.new('haze');volmat.use_nodes=True
nt=volmat.node_tree
bs=nt.nodes.get('Principled BSDF')
nt.nodes.remove(bs)
vol=nt.nodes.new('ShaderNodeVolumePrincipled')
vol.inputs['Density'].default_value=.012
vol.inputs['Anisotropy'].default_value=.25
out=nt.nodes.get('Material Output')
nt.links.new(vol.outputs['Volume'],out.inputs['Volume'])
haze=box('haze_box',(0,.3,2.9),(10.5,8.3,5.4),volmat,0)

# camera
camd=bpy.data.cameras.new('Camera')
cam=bpy.data.objects.new('Camera',camd)
bpy.context.collection.objects.link(cam)
scene.camera=cam
cam.location=(1.35,-9.5,3.20)
aim(cam,(-.35,1.25,1.55))
cam.data.lens=48
cam.data.sensor_width=36
cam.data.dof.use_dof=True
focus=bpy.data.objects.new('Focus',None);bpy.context.collection.objects.link(focus);focus.location=(-.35,1.25,1.55)
cam.data.dof.focus_object=focus
cam.data.dof.aperture_fstop=3.2

# render layout with proxy
scene.render.filepath=OUT+'/BARD_STAGE_V4_LAYOUT_PROXY.png'
bpy.ops.render.render(write_still=True)

# render clean plate without proxy
for o in proxy_objs:o.hide_render=True
scene.render.filepath=OUT+'/BARD_STAGE_V4_ENV_PLATE.png'
bpy.ops.render.render(write_still=True)

bpy.ops.wm.save_as_mainfile(filepath=OUT+'/BARD_STAGE_V4_MASTER.blend')
print('BARD_STAGE_V4_OK')
