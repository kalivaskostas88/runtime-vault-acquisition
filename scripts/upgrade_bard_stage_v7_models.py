import bpy, pathlib, json, math, os
from mathutils import Vector

V6="/tmp/bard_stage_v6/BARD_STAGE_V6_MASTER.blend"
MODELS=pathlib.Path("/tmp/bard_stage_v7/models")
OUT=pathlib.Path("/tmp/bard_stage_v7")
OUT.mkdir(parents=True,exist_ok=True)

bpy.ops.wm.open_mainfile(filepath=V6)
scene=bpy.context.scene
scene.render.resolution_x=960
scene.render.resolution_y=540
scene.render.resolution_percentage=100
try: scene.view_settings.look='AgX - Medium High Contrast'
except Exception: pass
scene.view_settings.exposure=-0.98

manifest=json.loads((MODELS/"POLYHAVEN_MODEL_MANIFEST.json").read_text())

def delete_prefixes(prefixes):
    for o in list(bpy.data.objects):
        if any(o.name.startswith(p) for p in prefixes):
            bpy.data.objects.remove(o,do_unlink=True)

def append_asset(aid,loc=(0,0,0),scale=1.0,rot=(0,0,0),name=None):
    blend=manifest[aid]["blend"]["path"]
    with bpy.data.libraries.load(blend,link=False) as (src,dst):
        dst.objects=[n for n in src.objects if n]
    root=bpy.data.objects.new(name or f"PH_{aid}",None)
    bpy.context.collection.objects.link(root)
    root.location=loc
    root.scale=(scale,scale,scale)
    root.rotation_euler=rot
    appended=[]
    for o in dst.objects:
        if o is None: continue
        # Avoid importing cameras/lights from source assets.
        if o.type in {'CAMERA','LIGHT'}: 
            continue
        bpy.context.collection.objects.link(o)
        o.parent=root
        appended.append(o)
    return root,appended

# Remove blockout substitutes that read as primitives.
delete_prefixes([
    'stool_seat','stool_leg','side_table','side_leg',
    'barrel','lantern_ring','lantern_body','lantern_glow','lantern_chain'
])

stage_x=-1.25
# Real worn stool on stage.
append_asset('wooden_stool_01',loc=(stage_x-.08,1.18,.50),scale=1.18,rot=(0,0,math.radians(-6)),name='PH_stage_stool')

# Real table prop, deliberately scaled down as a side table.
append_asset('wooden_table_02',loc=(stage_x+1.20,1.42,.50),scale=.42,rot=(0,0,math.radians(8)),name='PH_side_table')

# Real barrels, varied scale/rotation for non-copy-paste set dressing.
for i,(loc,sc,ang) in enumerate([
    ((-5.15,3.52,.46),.88,math.radians(8)),
    ((-4.55,3.72,.46),.82,math.radians(-11)),
    ((5.75,3.58,.46),.84,math.radians(13)),
]):
    append_asset('wine_barrel_01',loc=loc,scale=sc,rot=(0,0,ang),name=f'PH_barrel_{i}')

# Real hanging lanterns.
for i,(loc,sc,ang) in enumerate([
    ((-.10,3.02,4.03),.84,math.radians(4)),
    ((2.55,3.50,3.78),.78,math.radians(-7)),
]):
    append_asset('wooden_lantern_01',loc=loc,scale=sc,rot=(0,0,ang),name=f'PH_lantern_{i}')

# Retain motivated lights but position them at actual lanterns.
for i,(x,y,z) in enumerate([(-.10,3.02,4.05),(2.55,3.50,3.80)]):
    d=bpy.data.lights.new(f'V7_lantern_light_{i}','POINT')
    d.color=(1.0,.34,.09); d.energy=72; d.shadow_soft_size=.20
    o=bpy.data.objects.new(f'V7_lantern_light_{i}',d);bpy.context.collection.objects.link(o);o.location=(x,y,z)

# Add a more detailed foreground wooden table from the same table asset.
append_asset('wooden_table_02',loc=(0,-4.35,.10),scale=.92,rot=(0,0,math.radians(2)),name='PH_foreground_table')

# Small camera refinement after real props: slightly lower, more intimate.
cam=scene.camera
cam.location=(.45,-10.65,2.92)
target=Vector((-.60,1.25,1.55))
cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
cam.data.lens=45

# Proxy visibility helpers.
proxy=[o for o in bpy.data.objects if o.name.startswith('proxy_')]
for o in proxy:o.hide_render=True
scene.render.filepath=str(OUT/'BARD_STAGE_V7_ENV_PLATE.png')
bpy.ops.render.render(write_still=True)

for o in proxy:o.hide_render=False
scene.render.filepath=str(OUT/'BARD_STAGE_V7_LAYOUT_PROXY.png')
bpy.ops.render.render(write_still=True)

bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'BARD_STAGE_V7_MASTER.blend'))
print('BARD_STAGE_V7_MODELS_OK')
