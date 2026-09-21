import bpy, math, os, random
from mathutils import Vector

OUT="/tmp/bard_stage_v3_master"
os.makedirs(OUT,exist_ok=True)
rng=random.Random(260921)

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene
scene.render.engine='BLENDER_EEVEE'
scene.render.resolution_x=768
scene.render.resolution_y=1152
scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
scene.render.film_transparent=False
scene.render.fps=25
scene.frame_start=1
scene.frame_end=200
scene.world.color=(0.005,0.004,0.003)
try:
    scene.view_settings.look='AgX - Medium High Contrast'
except Exception:
    pass
scene.view_settings.exposure=-1.05

def rgba(h,a=1):
    h=h.lstrip('#');return tuple(int(h[i:i+2],16)/255 for i in (0,2,4))+(a,)

def simple_mat(name,color,rough=.7,metal=0):
    m=bpy.data.materials.new(name);m.use_nodes=True
    b=m.node_tree.nodes.get('Principled BSDF')
    b.inputs['Base Color'].default_value=color;b.inputs['Roughness'].default_value=rough;b.inputs['Metallic'].default_value=metal
    return m

def proc_mat(name,c1,c2,scale=4.0,rough=.75,bump=.15):
    m=bpy.data.materials.new(name);m.use_nodes=True
    nt=m.node_tree; bs=nt.nodes.get('Principled BSDF')
    tex=nt.nodes.new('ShaderNodeTexNoise');tex.inputs['Scale'].default_value=scale;tex.inputs['Detail'].default_value=3.0;tex.inputs['Roughness'].default_value=.65
    ramp=nt.nodes.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].color=c1;ramp.color_ramp.elements[1].color=c2
    nt.links.new(tex.outputs['Fac'],ramp.inputs['Fac']);nt.links.new(ramp.outputs['Color'],bs.inputs['Base Color'])
    bs.inputs['Roughness'].default_value=rough
    if bump>0:
        bp=nt.nodes.new('ShaderNodeBump');bp.inputs['Strength'].default_value=.30;bp.inputs['Distance'].default_value=bump
        nt.links.new(tex.outputs['Fac'],bp.inputs['Height']);nt.links.new(bp.outputs['Normal'],bs.inputs['Normal'])
    return m

def emissive(name,color,strength):
    m=bpy.data.materials.new(name);m.use_nodes=True
    bs=m.node_tree.nodes.get('Principled BSDF')
    bs.inputs['Base Color'].default_value=color
    bs.inputs['Emission Color'].default_value=color
    bs.inputs['Emission Strength'].default_value=strength
    bs.inputs['Roughness'].default_value=.35
    return m

STONE=proc_mat('stone',rgba('#2c2926'),rgba('#54483d'),3.2,.92,.20)
STONE_D=proc_mat('stone_dark',rgba('#171615'),rgba('#322d28'),4.0,.95,.16)
WOOD=proc_mat('wood',rgba('#1b0f09'),rgba('#5a2e17'),5.2,.78,.10)
WOOD_L=proc_mat('wood_stage',rgba('#2b150c'),rgba('#7a4324'),6.0,.68,.08)
CLOTH=simple_mat('cloth',rgba('#3a0d13'),.9)
OCHRE=simple_mat('ochre',rgba('#563719'),.9)
METAL=simple_mat('metal',rgba('#2a2521'),.42,.65)
CERAMIC=simple_mat('ceramic',rgba('#3b251a'),.82)
PEOPLE=simple_mat('people',rgba('#100d0d'),.9)
PEOPLE2=simple_mat('people2',rgba('#25150f'),.88)
SKIN=simple_mat('skin',rgba('#4f2f21'),.78)
PROXY=simple_mat('bard_proxy',rgba('#5a5149'),.8)
LUTE=simple_mat('lute_proxy',rgba('#6f3d1d'),.62)
FLAME=emissive('flame',rgba('#ff7a18'),5.0)
CORE=emissive('flame_core',rgba('#ffd27a'),8.0)

def box(name,loc,dims,mat,bev=.025):
    bpy.ops.mesh.primitive_cube_add(location=loc);o=bpy.context.object;o.name=name;o.dimensions=dims
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    if bev:
        b=o.modifiers.new('bevel','BEVEL');b.width=bev;b.segments=2
    o.data.materials.append(mat);return o

def cyl(name,loc,r,d,mat,verts=24):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts,radius=r,depth=d,location=loc);o=bpy.context.object;o.name=name;o.data.materials.append(mat);return o

def sphere(name,loc,scale,mat):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=12,location=loc);o=bpy.context.object;o.name=name;o.scale=scale
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(mat);return o

def aim(o,target):
    o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()

def point(name,loc,color,energy,radius=.25):
    d=bpy.data.lights.new(name,'POINT');d.color=color;d.energy=energy;d.shadow_soft_size=radius
    o=bpy.data.objects.new(name,d);bpy.context.collection.objects.link(o);o.location=loc;return o

def area(name,loc,target,color,energy,size):
    d=bpy.data.lights.new(name,'AREA');d.color=color;d.energy=energy;d.shape='DISK';d.size=size
    o=bpy.data.objects.new(name,d);bpy.context.collection.objects.link(o);o.location=loc;aim(o,target);return o

# room
box('floor',(0,0,-.12),(12,14,.24),WOOD,.02)
box('back',(0,5.35,3.1),(12,.38,6.2),STONE,.04)
box('left',(-6.05,.8,3.1),(.35,9.4,6.2),STONE_D,.04)
box('right',(6.05,.8,3.1),(.35,9.4,6.2),STONE_D,.04)
# back stone breakup blocks
for row,z in enumerate([.55,1.2,1.85,2.5,3.15,3.8,4.45,5.1]):
    x=-5.45+(row%2)*.36
    while x<5.5:
        ww=rng.uniform(.55,1.0)
        box('stone_block',(x+ww/2,5.12,z),(ww,.16,.48),STONE if rng.random()>.35 else STONE_D,.025)
        x+=ww+rng.uniform(.08,.18)
# beams
for x in (-5.05,-3.0,3.0,5.05): box('beam',(x,4.92,3.15),(.24,.30,6.0),WOOD,.03)
for z in (1.05,3.15,5.25): box('beam',(0,4.90,z),(10.4,.30,.24),WOOD,.03)
for x in (-4.5,-2.2,.2,2.6,4.8): box('ceiling',(x,.7,5.82),(.22,9.2,.24),WOOD,.03)

# stage
box('stage_base',(-.45,1.45,.22),(5.1,3.0,.44),WOOD_L,.05)
for i in range(9):
    box('stage_plank',(-2.65+i*.58,1.43,.48),(.52,2.72,.07),WOOD_L if i%2 else WOOD,.012)
box('stage_front',(-.45,-.05,.45),(5.25,.18,.72),WOOD,.03)
# 2 steps left-front
box('step1',(-2.35,-.55,.15),(1.15,.70,.30),WOOD_L,.03)
box('step2',(-2.35,-.24,.31),(1.15,.52,.18),WOOD_L,.03)

# backdrop textiles
box('bannerL',(-2.18,4.75,3.45),(1.0,.05,2.65),CLOTH,.012)
box('bannerR',(1.55,4.75,3.45),(1.0,.05,2.65),CLOTH,.012)
box('bannerC',(-.3,4.78,4.38),(1.15,.05,1.60),OCHRE,.012)

# stool and small table
cyl('stool_seat',(-.65,1.35,1.06),.44,.16,WOOD,28)
for dx,dy in ((-.29,-.25),(.29,-.25),(-.29,.25),(.29,.25)): cyl('stool_leg',(-.65+dx,1.35+dy,.53),.05,.96,WOOD,16)
cyl('side_table',(1.15,1.55,1.02),.43,.10,WOOD,28);cyl('side_table_leg',(1.15,1.55,.56),.08,.92,WOOD,18)
cyl('mug',(1.05,1.50,1.24),.09,.24,CERAMIC,20)

# hearth moved into composition at right
HX=3.15
for x in (HX-.62,HX+.62): box('hearth_pillar',(x,4.66,1.45),(.55,.62,2.85),STONE,.04)
box('hearth_top',(HX,4.64,2.93),(1.75,.65,.46),STONE,.04)
box('hearth_floor',(HX,4.18,.28),(2.0,1.28,.28),STONE_D,.04)
box('hearth_void',(HX,4.80,1.45),(1.02,.18,2.15),STONE_D,.01)
for i in range(4):
    lg=cyl('log',(HX-.35+i*.22,4.08,.55),.10,.82,WOOD,16);lg.rotation_euler=(0,math.radians(78),math.radians((i-1.5)*12))
for i,(dx,z,s) in enumerate([(-.32,.72,.24),(-.08,.90,.34),(.18,.70,.26),(.34,.82,.20)]):
    f=sphere('flame',(HX+dx,4.02,z),(s*.48,s*.22,s*1.1),CORE if i%2==1 else FLAME)
fire=point('firelight',(HX,3.72,1.40),(1.0,.26,.06),760,1.1)

# wall candle sconces
for i,(x,z) in enumerate([(-4.15,2.7),(-2.7,2.9),(1.0,3.0)]):
    box('sconce',(x,4.68,z),(.18,.30,.10),METAL,.015)
    cyl('candle',(x,4.48,z+.22),.055,.32,simple_mat(f'wax{i}',rgba('#c9a56c'),.8),18)
    sphere('wick',(x,4.46,z+.43),(.035,.025,.09),CORE)
    point('candle_light',(x,4.22,z+.45),(1.0,.48,.15),80,.18)

# shelves + barrels
for z in (1.7,2.35,3.0): box('shelf',(-4.35,4.58,z),(2.0,.28,.11),WOOD,.02)
for k in range(9):
    x=-5.0+(k%3)*.55;z=1.84+(k//3)*.65;cyl('bottle',(x,4.37,z),.07,.29,CERAMIC,14)
for x,y in [(-4.65,3.72),(-4.05,3.84),(4.55,3.75)]:
    b=cyl('barrel',(x,y,.82),.52,1.38,WOOD,24);b.rotation_euler=(math.radians(90),0,0)

# audience tables
def table(x,y,w=2.0):
    box('table',(x,y,.78),(w,1.0,.12),WOOD,.035)
    for dx in (-w*.38,w*.38):
        for dy in (-.32,.32): box('leg',(x+dx,y+dy,.39),(.11,.11,.78),WOOD,.015)
for p in [(-3.35,-1.18),(3.15,-1.0),(-2.7,-3.3),(2.85,-3.2)]: table(*p)

# low-detail patrons
for i,(x,y) in enumerate([(-3.7,-1.1),(-2.95,-.9),(2.7,-.85),(3.55,-1.2),(-2.9,-3.15),(-2.2,-3.45),(2.45,-3.15),(3.25,-3.35)]):
    sphere('head',(x,y,1.8),(.20,.20,.23),SKIN);cyl('torso',(x,y,1.18),.27,.80,PEOPLE if i%2==0 else PEOPLE2,18)

# stage rug and foreground depth framing
box('stage_rug',(-.45,1.33,.535),(3.45,1.75,.035),CLOTH,.01)
box('foreground_table',(0,-5.25,.78),(4.4,1.15,.15),WOOD,.04)
for dx in (-1.55,1.55):
    box('foreground_table_leg',(dx,-5.25,.38),(.15,.15,.76),WOOD,.02)
# low foreground cups / jugs, intended to fall out of focus
cyl('fg_jug',(-1.25,-4.95,1.04),.18,.48,CERAMIC,22)
cyl('fg_cup',(.75,-4.92,.98),.11,.28,CERAMIC,20)
# two foreground listener silhouettes create depth without blocking the performer
for i,(x,y) in enumerate([(-3.25,-4.15),(3.15,-4.25)]):
    sphere(f'fg_head_{i}',(x,y,1.82),(.24,.24,.27),SKIN)
    cyl(f'fg_torso_{i}',(x,y,1.15),.34,.95,PEOPLE if i==0 else PEOPLE2,20)

# lighting: darker room / stage-led
area('key',(-2.6,-2.2,4.8),(-.5,1.3,1.55),(1.0,.50,.24),620,4.0)
area('softfill',(3.8,-1.0,4.2),(-.5,1.3,1.4),(.28,.34,.50),95,4.2)
area('backwarm',(-.2,3.9,4.7),(-.5,1.2,1.7),(1.0,.32,.09),310,3.0)
point('rim',(-2.8,3.4,3.0),(1.0,.21,.05),170,.45)

# master camera: intimate 3/4 view, stage-led, hearth visible
camd=bpy.data.cameras.new('Camera');cam=bpy.data.objects.new('Camera',camd);bpy.context.collection.objects.link(cam);scene.camera=cam
cam.data.sensor_width=36
cam.data.dof.use_dof=True
focus=bpy.data.objects.new('Focus',None);bpy.context.collection.objects.link(focus);focus.location=(-.55,1.30,1.55)
cam.data.dof.focus_object=focus;cam.data.dof.aperture_fstop=3.2
cam.location=(.75,-9.65,3.05);cam.data.lens=43;aim(cam,(-.45,1.35,1.58))
scene.frame_set(80)
scene.render.filepath=f"{OUT}/BARD_STAGE_ENVIRONMENT_V3_MASTER.png"
bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=f"{OUT}/BARD_STAGE_ENVIRONMENT_V3_MASTER.blend")
print('BARD_STAGE_ENVIRONMENT_V3_MASTER_OK')
