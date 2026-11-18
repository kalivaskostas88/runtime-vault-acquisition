# SPDX-License-Identifier: GPL-2.0-or-later
"""V063 real native Blender sculpt-brush proof; original isolated teaching sphere only.
Teacher: Julien Kaspar, Sculpting Fundamentals, CC-BY:
https://studio.blender.org/training/stylized-character-workflow/5d5e6141b01c790d39b7ed4e/
Technical operator method based on Blender Foundation's own GPL-2.0-or-later
tests/python/sculpt_brush_render_tests.py and sculpt_paint/brush_asset_test.py.
No protected studio assets. A native brush operation must modify real mesh data or FAIL.
"""
import bpy, sys, json, math, hashlib, struct, pathlib, bmesh
from mathutils import Vector

OUT = pathlib.Path(sys.argv[sys.argv.index("--")+2]).resolve()
ACTION = sys.argv[sys.argv.index("--")+1]
OUT.mkdir(parents=True,exist_ok=True)

def save_json(path,d):
    pathlib.Path(path).write_text(json.dumps(d,indent=2,ensure_ascii=False,sort_keys=True)+"\n")
def mesh_state(obj):
    me=obj.data
    packed=b"".join(struct.pack("<ddd",*[float(c) for c in v.co]) for v in me.vertices)
    bm=bmesh.new();bm.from_mesh(me)
    vol=abs(bm.calc_volume(signed=True))
    bm.free()
    return dict(vertices=len(me.vertices),faces=len(me.polygons),position_sha256=hashlib.sha256(packed).hexdigest(),volume=vol,
                x_min=min(v.co.x for v in me.vertices),x_max=max(v.co.x for v in me.vertices),
                z_max=max(v.co.z for v in me.vertices))
def set_view_override():
    d=bpy.context.copy()
    for area in d['screen'].areas:
        if area.type=='VIEW_3D':
            region=next((r for r in area.regions if r.type=='WINDOW'),None)
            if region:
                d['area']=area; d['region']=region
                area.spaces.active.region_3d.view_location=Vector((0.,0.,0.))
                area.spaces.active.region_3d.view_distance=4.0
                return d
    raise RuntimeError("REAL_VIEW_3D_CONTEXT_MISSING; do not fake sculpt proof")
def camera_views(ob,tag):
    scene=bpy.context.scene
    scene.render.engine='BLENDER_WORKBENCH'
    scene.render.resolution_x=400;scene.render.resolution_y=400;scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG'
    scene.display.shading.light='STUDIO'
    scene.display.shading.color_type='SINGLE'
    scene.display.shading.single_color=(0.65,0.66,0.70)
    scene.render.film_transparent=False
    cam=next((a for a in bpy.data.objects if a.type=='CAMERA'),None)
    if cam is None:
        bpy.ops.object.camera_add()
        cam=bpy.context.object
    scene.camera=cam
    cam.data.type='ORTHO';cam.data.ortho_scale=3.05
    for label,vec in [('FRONT',(0,-5,0.5)),('SIDE',(5,0,0.5)),('THREE_QUARTER',(4,-5,2.5))]:
        cam.location=Vector(vec)
        cam.rotation_euler=(Vector((0,0,0))-cam.location).to_track_quat('-Z','Y').to_euler()
        path=OUT/f"{tag}_{label}.png"
        scene.render.filepath=str(path)
        bpy.ops.render.render(write_still=True)
        if not path.exists() or path.stat().st_size<1000:raise RuntimeError("Missing native render "+str(path))
def build():
    if not bpy.app.version_string.startswith('5.2.2'):raise RuntimeError("WRONG_BLENDER_VERSION "+bpy.app.version_string)
    bpy.ops.object.select_all(action='DESELECT')
    for ob in list(bpy.data.objects):
        if ob.type=='MESH':bpy.data.objects.remove(ob,do_unlink=True)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=96,ring_count=48,radius=1,location=(0,0,0))
    ob=bpy.context.object;ob.name='V063_TEACHER_FIRST_ORIGINAL_SPHERE'
    base=mesh_state(ob)
    camera_views(ob,'BASE')
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'BASE.blend'))
    bpy.ops.object.select_all(action='DESELECT')
    ob.select_set(True)
    bpy.context.view_layer.objects.active=ob
    bpy.ops.object.mode_set(mode='SCULPT')
    view=set_view_override()
    with bpy.context.temp_override(**view):
        activated=bpy.ops.brush.asset_activate(asset_library_type='ESSENTIALS',
            relative_asset_identifier='brushes/essentials_brushes-mesh_sculpt.blend/Brush/Draw')
        if 'FINISHED' not in activated:raise RuntimeError("DRAW_ASSET_ACTIVATION_NOT_FINISHED")
    brush=bpy.context.tool_settings.sculpt.brush
    if brush is None or brush.name!='Draw':raise RuntimeError("ACTIVE_DRAW_BRUSH_NOT_CONFIRMED")
    brush.strength=0.16
    brush.size=110
    bpy.ops.ed.undo_push()
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.mode_set(mode='SCULPT')
    view=set_view_override()
    area=view['area'];w,h=area.width,area.height
    # Screen-space pass across CENTER of the actual sphere, as in Blender's own brush test.
    # These are real native sculpt events, not BMesh displacement proxies.
    stroke=[]
    for i in range(75):
        t=i/74
        x=w*(0.38+0.24*t);y=h*0.50
        stroke.append(dict(name='stroke',mouse=(x,y),mouse_event=(int(x),int(y)),
            location=(0.,0.,0.),is_start=i==0,pressure=1.,time=1.+i/60.,
            size=1.,x_tilt=0.,y_tilt=0.))
    with bpy.context.temp_override(**view):
        if not bpy.ops.sculpt.brush_stroke.poll():raise RuntimeError("REAL_NATIVE_BRUSH_STROKE_POLL_FAILED")
        result=bpy.ops.sculpt.brush_stroke(stroke=stroke,override_location=True)
    bpy.ops.object.mode_set(mode='OBJECT')
    after=mesh_state(ob)
    changed=base['position_sha256']!=after['position_sha256']
    receipt=dict(schema='V063_REAL_NATIVE_SCULPT_PROOF',bpy_version=bpy.app.version_string,
        teacher_source='https://studio.blender.org/training/stylized-character-workflow/5d5e6141b01c790d39b7ed4e/',
        operator="bpy.ops.sculpt.brush_stroke",brush_asset=brush.name,
        brush_strength=brush.strength,brush_size=brush.size,
        github_source_method='Blender Foundation sculpt_brush_render_tests.py GPL-2.0+',
        stroke_points=len(stroke),result=sorted(result),area_size=[w,h],
        baseline=base,sculpted=after,
        same_vertex_count=base['vertices']==after['vertices'],
        real_mesh_changed=changed,
        native_proof_pass=changed and ('FINISHED' in result),
        artist_approved=False,teacher_full_av_listened=False,
        protected_assets_accessed=False,
        interpretation='Only single Draw asset native operator and resulting mesh change; NOT finished art; no Smooth/Mask/Dyntopo claims')
    save_json(OUT/'BUILD_RECEIPT.json',receipt)
    if not receipt['native_proof_pass']:raise RuntimeError("NO_MESH_CHANGE_VIA_REAL_SCULPT_OPERATOR")
    camera_views(ob,'SCULPT')
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'SCULPT.blend'))
    print('V063_REAL_NATIVE_PROOF',json.dumps(receipt),flush=True)
def verify():
    if not (OUT/'BUILD_RECEIPT.json').is_file():raise RuntimeError("BUILD_RECEIPT_MISSING")
    rec=json.loads((OUT/'BUILD_RECEIPT.json').read_text())
    ob=bpy.data.objects.get('V063_TEACHER_FIRST_ORIGINAL_SPHERE')
    if not ob or ob.type!='MESH':raise RuntimeError("OBJECT_NOT_REOPENED")
    observed=mesh_state(ob)
    assert observed['position_sha256']==rec['sculpted']['position_sha256'],"REOPENED_MESH_DIFFERS"
    assert observed['vertices']==rec['baseline']['vertices'],"VERTEX_COUNT_DIFFERS"
    assert rec['native_proof_pass'] is True
    save_json(OUT/'REOPEN_RECEIPT.json',dict(fresh_reopen_pass=True,mesh_sha=observed['position_sha256'],
        blender_version=bpy.app.version_string,artist_approved=False,source='SCULPT.blend'))
    print("V063_FRESH_REOPEN_PASS",observed['position_sha256'],flush=True)
if ACTION=="build":build()
elif ACTION=="verify":verify()
else:raise ValueError(ACTION)
