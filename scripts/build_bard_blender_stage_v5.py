import bpy, math, os, random
from mathutils import Vector

OUT="/tmp/bard_stage_v5"
os.makedirs(OUT, exist_ok=True)
rng=random.Random(2609215)

# reset
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

scene=bpy.context.scene
scene.render.engine='BLENDER_EEVEE'
scene.render.resolution_x=960
scene.render.resolution_y=540
scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
scene.render.film_transparent=False
scene.render.fps=25
scene.frame_start=1
scene.frame_end=200
scene.world.color=(0.003,0.0025,0.002)
try: scene.view_settings.look='AgX - Medium High Contrast'
except Exception: pass
scene.view_settings.exposure=-0.75

def rgba(h,a=1.0):
    h=h.lstrip('#')
    return tuple(int(h[i:i+2],16)/255 for i in (0,2,4))+(a,)

def pmat(name, base, rough=.72, metal=0.0):
    m=bpy.data.materials.new(name);m.use_nodes=True
    b=m.node_tree.nodes.get('Principled BSDF')
    b.inputs['Base Color'].default_value=base
    b.inputs['Roughness'].default_value=rough
    b.inputs['Metallic'].default_value=metal
    return m

def nmat(name,c0,c1,scale=5.0,rough=.78,bump=.14):
    m=bpy.data.materials.new(name);m.use_nodes=True
    nt=m.node_tree; bs=nt.nodes.get('Principled BSDF')
    tex=nt.nodes.new('ShaderNodeTexNoise')
    tex.inputs['Scale'].default_value=scale
    tex.inputs['Detail'].default_value=4.5
    tex.inputs['Roughness'].default_value=.66
    ramp=nt.nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].color=c0
    ramp.color_ramp.elements[1].color=c1
    nt.links.new(tex.outputs['Fac'],ramp.inputs['Fac'])
    nt.links.new(ramp.outputs['Color'],bs.inputs['Base Color'])
    bs.inputs['Roughness'].default_value=rough
    bumpn=nt.nodes.new('ShaderNodeBump')
    bumpn.inputs['Strength'].default_value=.32
    bumpn.inputs['Distance'].default_value=bump
    nt.links.new(tex.outputs['Fac'],bumpn.inputs['Height'])
    nt.links.new(bumpn.outputs['Normal'],bs.inputs['Normal'])
    return m

def emat(name,color,strength):
    m=bpy.data.materials.new(name);m.use_nodes=True
    bs=m.node_tree.nodes.get('Principled BSDF')
    bs.inputs['Base Color'].default_value=color
    bs.inputs['Emission Color'].default_value=color
    bs.inputs['Emission Strength'].default_value=strength
    bs.inputs['Roughness'].default_value=.28
    return m

WOOD=nmat('wood',rgba('#160d08'),rgba('#65381d'),7.0,.74,.08)
WOOD_D=nmat('wood_dark',rgba('#0d0806'),rgba('#3c2013'),8.5,.82,.08)
WOOD_L=nmat('wood_stage',rgba('#2a150c'),rgba('#834725'),8.0,.66,.06)
STONE=nmat('stone',rgba('#1e1c1b'),rgba('#574a3e'),4.0,.94,.18)
STONE_D=nmat('stone_dark',rgba('#0d0d0d'),rgba('#2c2723'),4.8,.95,.16)
CLOTH=pmat('cloth',rgba('#3a0e14'),.92)
OCHRE=pmat('ochre',rgba('#5b3a19'),.90)
METAL=pmat('iron',rgba('#201d1a'),.35,.76)
CERAMIC=nmat('ceramic',rgba('#2c1a13'),rgba('#603822'),8,.82,.03)
SKIN=pmat('skin',rgba('#4d2d20'),.75)
PATRON=pmat('patron',rgba('#0f0c0b'),.91)
PATRON2=pmat('patron2',rgba('#281610'),.88)
PROXY=pmat('proxy',rgba('#655d54'),.78)
LUTE=nmat('lute',rgba('#3e1f0d'),rgba('#9a5427'),8.5,.58,.04)
RUG=nmat('rug',rgba('#201010'),rgba('#6d231d'),10,.87,.04)
FLAME=emat('flame',rgba('#ff7418'),6.5)
CORE=emat('core',rgba('#ffd98d'),9.5)
WAX=pmat('wax',rgba('#c7a56d'),.80)

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

# room shell
box('floor',(0,0,-.12),(14,12,.24),WOOD_D,.02)
box('back',(0,5.0,3.0),(14,.34,6.0),STONE,.035)
box('left',(-7.0,.6,3.0),(.32,8.8,6.0),STONE_D,.035)
box('right',(7.0,.6,3.0),(.32,8.8,6.0),STONE_D,.035)

# irregular stone blocks
for row,z in enumerate([.40,1.00,1.60,2.20,2.80,3.40,4.00,4.60,5.20]):
    x=-6.45+(row%2)*.30
    while x<6.4:
        w=rng.uniform(.50,1.00)
        box('stone_block',(x+w/2,4.82,z),(w,.14,.42),STONE if rng.random()>.27 else STONE_D,.018)
        x+=w+rng.uniform(.07,.16)

# timber framing / ceiling
for x in (-6.15,-3.25,0.0,3.25,6.15): box('beam_v',(x,4.70,3.0),(.24,.28,5.9),WOOD,.03)
for z in (.90,3.0,5.10): box('beam_h',(0,4.68,z),(12.6,.28,.22),WOOD,.03)
for x in (-5.5,-2.75,0,2.75,5.5): box('ceiling_beam',(x,.25,5.70),(.22,9.0,.24),WOOD,.03)

# stage: left-center, modest and intimate
stage_x=-1.25
box('stage_base',(stage_x,1.35,.22),(5.6,2.8,.44),WOOD_L,.05)
for i in range(10):
    box('plank',(stage_x-2.58+i*.57,1.34,.48),(.50,2.50,.07),WOOD_L if i%2 else WOOD,.01)
box('stage_front',(stage_x,-.07,.45),(5.75,.18,.72),WOOD_D,.03)
box('step_low',(stage_x-2.0,-.54,.14),(1.0,.66,.28),WOOD_L,.025)
box('step_high',(stage_x-2.0,-.28,.30),(1.0,.48,.18),WOOD_L,.025)
# rug on stage
box('stage_rug',(stage_x-.15,1.05,.535),(3.2,1.55,.035),RUG,.01)

# banners
box('banner_l',(stage_x-1.8,4.56,3.35),(.90,.045,2.45),CLOTH,.012)
box('banner_r',(stage_x+1.45,4.56,3.35),(.90,.045,2.45),CLOTH,.012)
box('banner_c',(stage_x-.15,4.59,4.28),(1.0,.045,1.46),OCHRE,.012)

# stool / side table
cyl('stool_seat',(stage_x-.10,1.20,1.02),.43,.15,WOOD,28)
for dx,dy in ((-.28,-.23),(.28,-.23),(-.28,.23),(.28,.23)):
    cyl('stool_leg',(stage_x-.10+dx,1.20+dy,.50),.048,.92,WOOD,16)
cyl('side_table',(stage_x+1.25,1.40,1.00),.39,.09,WOOD,28)
cyl('side_leg',(stage_x+1.25,1.40,.54),.075,.88,WOOD_D,18)
cyl('mug',(stage_x+1.14,1.35,1.22),.082,.23,CERAMIC,18)

# fireplace at right side, clearly in frame
hx=4.35
for x in (hx-.62,hx+.62): box('hearth_pillar',(x,4.46,1.40),(.54,.60,2.76),STONE,.04)
box('hearth_top',(hx,4.45,2.82),(1.80,.64,.44),STONE,.04)
box('hearth_floor',(hx,4.02,.28),(2.10,1.24,.28),STONE_D,.035)
box('hearth_void',(hx,4.62,1.38),(1.06,.18,2.02),STONE_D,.01)

# stone arch wedges over hearth
arch_center=(hx,4.45,2.35)
for i in range(11):
    a=math.radians(18+i*14.4)
    r=1.15
    x=hx+math.cos(a)*r
    z=2.35+math.sin(a)*r
    w=box('arch_stone',(x,4.37,z),(.42,.42,.34),STONE,.025)
    w.rotation_euler[1]=a-math.pi/2

# fire logs and flames
for i in range(5):
    log=cyl('log',(hx-.38+i*.19,3.91,.53),.09,.82,WOOD_D,16)
    log.rotation_euler=(0,math.radians(78),math.radians((i-2)*9))
for i,(dx,z,s) in enumerate([(-.34,.69,.22),(-.12,.88,.33),(.10,.73,.25),(.30,.82,.20),(.42,.66,.16)]):
    sphere('flame',(hx+dx,3.88,z),(s*.48,s*.22,s*1.15),CORE if i==1 else FLAME)
fire=point('firelight',(hx,3.58,1.34),(1.0,.23,.05),860,1.05)
# add reflected warm light near stage right
point('fire_bounce',(2.6,2.9,2.3),(1.0,.24,.06),185,.75)

# candle sconces
for i,(x,z) in enumerate([(-5.2,2.45),(-3.3,2.72),(.45,2.75),(2.2,2.45)]):
    box('sconce',(x,4.51,z),(.16,.26,.09),METAL,.012)
    cyl('candle',(x,4.34,z+.20),.052,.30,WAX,16)
    sphere('candle_flame',(x,4.32,z+.40),(.030,.022,.080),CORE)
    point('candle_light',(x,4.12,z+.42),(1.0,.43,.12),62,.17)

# hanging lanterns
for j,(x,y,z) in enumerate([(-.1,3.0,4.45),(2.65,3.55,4.15)]):
    cyl('lantern_ring',(x,y,z),.17,.06,METAL,20)
    cyl('lantern_body',(x,y,z-.18),.13,.32,METAL,20)
    sphere('lantern_glow',(x,y,z-.18),(.075,.075,.12),CORE)
    point('lantern_light',(x,y,z-.15),(1.0,.42,.12),85,.22)
    box('lantern_chain',(x,y,z+.55),(.035,.035,.9),METAL,.005)

# shelves / barrel cluster left
for z in (1.65,2.30,2.95): box('shelf',(-5.2,4.43,z),(2.15,.24,.10),WOOD,.018)
for k in range(12):
    x=-6.0+(k%4)*.52; z=1.78+(k//4)*.65
    cyl('bottle',(x,4.24,z),.06,.27,CERAMIC,14)
for x,y in [(-5.35,3.50),(-4.75,3.72),(5.95,3.65)]:
    b=cyl('barrel',(x,y,.80),.50,1.35,WOOD,24);b.rotation_euler=(math.radians(90),0,0)

# audience tables
def table(x,y,w=1.9):
    box('table',(x,y,.76),(w,.95,.11),WOOD,.03)
    for dx in (-w*.38,w*.38):
        for dy in (-.30,.30): box('table_leg',(x+dx,y+dy,.38),(.10,.10,.74),WOOD_D,.01)
for p in [(-4.75,-1.0),(3.7,-1.05),(-3.8,-2.95),(3.45,-2.9)]: table(*p)

# patrons; leave center visual channel clear
patrons=[(-5.05,-.95),(-4.35,-1.2),(3.25,-.9),(4.25,-1.18),(-4.0,-2.9),(-3.4,-3.15),(3.1,-2.8),(3.9,-3.2)]
for i,(x,y) in enumerate(patrons):
    sphere('head',(x,y,1.74),(.19,.19,.22),SKIN)
    cyl('torso',(x,y,1.14),.26,.78,PATRON if i%2==0 else PATRON2,18)

# foreground silhouettes for depth
sphere('fg_head_l',(-5.6,-4.65,1.70),(.55,.43,.57),PATRON)
sphere('fg_head_r',(5.45,-4.65,1.62),(.52,.42,.54),PATRON2)
box('fg_table',(0,-4.75,.55),(5.0,.75,.12),WOOD_D,.04)

# bard proxy, used only for layout
proxy=[]
px=stage_x-.05
proxy.append(sphere('proxy_head',(px,1.16,2.20),(.21,.21,.25),PROXY))
proxy.append(cyl('proxy_torso',(px,1.17,1.64),.29,.84,PROXY,20))
l=sphere('proxy_lute',(px+.28,1.00,1.52),(.62,.12,.39),LUTE);proxy.append(l)
neck=box('proxy_neck',(px+.89,1.00,1.64),(1.02,.10,.11),LUTE,.02);neck.rotation_euler[1]=math.radians(-8);proxy.append(neck)

# lighting
area('key',(-3.0,-2.4,4.6),(stage_x,1.2,1.55),(1.0,.47,.21),610,3.7)
area('fill',(4.2,-1.5,4.1),(stage_x,1.2,1.45),(.22,.29,.46),85,4.0)
area('backwarm',(stage_x,3.8,4.3),(stage_x,1.2,1.65),(1.0,.29,.07),290,2.8)
point('rim',(stage_x-2.3,3.0,2.9),(1.0,.18,.04),145,.42)

# haze
volmat=bpy.data.materials.new('haze');volmat.use_nodes=True
nt=volmat.node_tree
bs=nt.nodes.get('Principled BSDF');nt.nodes.remove(bs)
vol=nt.nodes.new('ShaderNodeVolumePrincipled')
vol.inputs['Density'].default_value=.008
vol.inputs['Anisotropy'].default_value=.25
out=nt.nodes.get('Material Output');nt.links.new(vol.outputs['Volume'],out.inputs['Volume'])
box('haze_box',(0,.25,2.9),(12.8,8.2,5.2),volmat,0)

# camera landscape
camd=bpy.data.cameras.new('Camera');cam=bpy.data.objects.new('Camera',camd)
bpy.context.collection.objects.link(cam);scene.camera=cam
cam.location=(.55,-10.8,3.05)
aim(cam,(-.55,1.3,1.52))
cam.data.lens=43
cam.data.sensor_width=36
cam.data.dof.use_dof=True
focus=bpy.data.objects.new('Focus',None);bpy.context.collection.objects.link(focus);focus.location=(stage_x,1.2,1.55)
cam.data.dof.focus_object=focus;cam.data.dof.aperture_fstop=3.4

# render proxy layout and clean plate
scene.render.filepath=OUT+'/BARD_STAGE_V5_LAYOUT_PROXY.png'
bpy.ops.render.render(write_still=True)
for o in proxy:o.hide_render=True
scene.render.filepath=OUT+'/BARD_STAGE_V5_ENV_PLATE.png'
bpy.ops.render.render(write_still=True)

bpy.ops.wm.save_as_mainfile(filepath=OUT+'/BARD_STAGE_V5_MASTER.blend')
print('BARD_STAGE_V5_OK')
