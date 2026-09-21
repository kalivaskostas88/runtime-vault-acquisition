import bpy, pathlib, json, os
from mathutils import Vector

V5="/tmp/bard_stage_v5/BARD_STAGE_V5_MASTER.blend"
ASSET=pathlib.Path("/tmp/bard_stage_v6/assets")
OUT=pathlib.Path("/tmp/bard_stage_v6")
OUT.mkdir(parents=True,exist_ok=True)

bpy.ops.wm.open_mainfile(filepath=V5)
scene=bpy.context.scene
scene.render.resolution_x=960
scene.render.resolution_y=540
scene.render.resolution_percentage=100
scene.render.engine='BLENDER_EEVEE'
try: scene.view_settings.look='AgX - Medium High Contrast'
except Exception: pass
scene.view_settings.exposure=-0.95

manifest=json.loads((ASSET/"POLYHAVEN_MANIFEST.json").read_text())

def path_for(aid,kind):
    x=manifest[aid].get(kind)
    return x["path"] if x else None

def image(path,noncolor=False):
    im=bpy.data.images.load(path,check_existing=True)
    if noncolor:
        try: im.colorspace_settings.name='Non-Color'
        except Exception: pass
    return im

def pbrify(mat,aid,scale=2.5,rough_default=.75,normal_strength=.45):
    diff=path_for(aid,'diffuse'); rough=path_for(aid,'rough'); nor=path_for(aid,'normal')
    nt=mat.node_tree; nt.nodes.clear()
    out=nt.nodes.new('ShaderNodeOutputMaterial')
    bs=nt.nodes.new('ShaderNodeBsdfPrincipled')
    bs.inputs['Roughness'].default_value=rough_default
    texc=nt.nodes.new('ShaderNodeTexCoord')
    mapping=nt.nodes.new('ShaderNodeMapping')
    mapping.inputs['Scale'].default_value=(scale,scale,scale)
    nt.links.new(texc.outputs['Generated'],mapping.inputs['Vector'])
    td=nt.nodes.new('ShaderNodeTexImage');td.image=image(diff);td.projection='BOX';td.projection_blend=.22
    nt.links.new(mapping.outputs['Vector'],td.inputs['Vector'])
    nt.links.new(td.outputs['Color'],bs.inputs['Base Color'])
    if rough:
        tr=nt.nodes.new('ShaderNodeTexImage');tr.image=image(rough,True);tr.projection='BOX';tr.projection_blend=.22
        nt.links.new(mapping.outputs['Vector'],tr.inputs['Vector'])
        nt.links.new(tr.outputs['Color'],bs.inputs['Roughness'])
    if nor:
        tn=nt.nodes.new('ShaderNodeTexImage');tn.image=image(nor,True);tn.projection='BOX';tn.projection_blend=.22
        nm=nt.nodes.new('ShaderNodeNormalMap');nm.inputs['Strength'].default_value=normal_strength
        nt.links.new(mapping.outputs['Vector'],tn.inputs['Vector'])
        nt.links.new(tn.outputs['Color'],nm.inputs['Color'])
        nt.links.new(nm.outputs['Normal'],bs.inputs['Normal'])
    nt.links.new(bs.outputs['BSDF'],out.inputs['Surface'])

# Apply human-made CC0 textures to major surfaces.
for n in ('stone','stone_dark'):
    if n in bpy.data.materials:
        pbrify(bpy.data.materials[n],'medieval_wall_02',scale=2.0,rough_default=.9,normal_strength=.55)
for n in ('wood','wood_dark','stage_wood'):
    if n in bpy.data.materials:
        pbrify(bpy.data.materials[n],'medieval_wood',scale=3.2 if n!='stage_wood' else 2.1,rough_default=.72,normal_strength=.42)

# Tame banner saturation; richer textile read without "game blockout" orange.
for n,col in [('cloth',(0.095,0.012,0.018,1)),('ochre',(0.18,0.08,0.025,1))]:
    m=bpy.data.materials.get(n)
    if m and m.use_nodes:
        bs=m.node_tree.nodes.get('Principled BSDF')
        if bs: bs.inputs['Base Color'].default_value=col

# Lighting refinement: less orange wash, stronger motivated pools.
for o in bpy.data.objects:
    if o.type!='LIGHT': continue
    if 'fire' in o.name.lower():
        o.data.energy*=0.78
        o.data.color=(1.0,.18,.035)
    elif 'candle' in o.name.lower() or 'lantern' in o.name.lower():
        o.data.energy*=0.78
        o.data.color=(1.0,.36,.10)
    elif o.data.type=='AREA':
        o.data.energy*=0.88

# Add a subtle cool ambient separator from camera-left.
def area(name,loc,target,color,energy,size):
    d=bpy.data.lights.new(name,'AREA');d.color=color;d.energy=energy;d.shape='DISK';d.size=size
    o=bpy.data.objects.new(name,d);bpy.context.collection.objects.link(o);o.location=loc
    o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
    return o
area('V6_cool_separator',(-5.3,-1.5,4.1),(-1.2,1.2,1.6),(.16,.22,.34),62,4.8)

# Hide proxy for clean plate first.
proxy=[o for o in bpy.data.objects if o.name.startswith('proxy_')]
for o in proxy:o.hide_render=True
scene.render.filepath=str(OUT/'BARD_STAGE_V6_ENV_PLATE.png')
bpy.ops.render.render(write_still=True)

# Proxy layout for integration scale check.
for o in proxy:o.hide_render=False
scene.render.filepath=str(OUT/'BARD_STAGE_V6_LAYOUT_PROXY.png')
bpy.ops.render.render(write_still=True)

# Save master.
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'BARD_STAGE_V6_MASTER.blend'))
print('BARD_STAGE_V6_PBR_OK')
