# SPDX-License-Identifier: GPL-2.0-or-later
"""V064 faithful native Smooth experiment on the EXACT V063 repaired .blend.
Authoritative teaching: Julien Kaspar, Blender Studio Sculpting Fundamentals CC-BY,
08:28–09:13 Smooth averaging can remove volume, not universal guarantee.
Native operator model: Blender Foundation sculpt_brush_render_tests.py (GPL-2.0+)
and brush_asset_test.py (GPL-2.0+).
V063 input retained unchanged. Real Smooth brush, no procedural geometry deformation.
"""
import bpy, bmesh, json, sys, pathlib, hashlib, struct, math
from mathutils import Vector
args=sys.argv[sys.argv.index("--")+1:]
ACTION=args[0]; OUT=pathlib.Path(args[1]).resolve();OUT.mkdir(parents=True,exist_ok=True)
SOURCE_EXPECTED_SHA="123e2a9a0ab77b9b0d5872686a3c98057eb6d939e2cdaa99382d367808877ec9"
def metric(ob):
    me=ob.data
    packed=b"".join(struct.pack("<ddd", *map(float,v.co)) for v in me.vertices)
    bm=bmesh.new();bm.from_mesh(me);vol=abs(bm.calc_volume(signed=True));bm.free()
    return dict(vertex_count=len(me.vertices),face_count=len(me.polygons),
        position_sha256=hashlib.sha256(packed).hexdigest(),volume=vol,
        x_max=max(float(v.co.x) for v in me.vertices),
        x_min=min(float(v.co.x) for v in me.vertices),
        z_max=max(float(v.co.z) for v in me.vertices))
def output(name,body):
    (OUT/name).write_text(json.dumps(body,ensure_ascii=False,indent=2,sort_keys=True)+"\n")
def viewport():
    d=bpy.context.copy()
    for area in d["screen"].areas:
        if area.type=="VIEW_3D":
            region=next((r for r in area.regions if r.type=="WINDOW"),None)
            if region:
                d["area"]=area;d["region"]=region
                area.spaces.active.region_3d.view_location=Vector((0.,0.,0.))
                area.spaces.active.region_3d.view_distance=4.
                return d
    raise RuntimeError("VIEW_3D missing: no fake sculpt")
def views(tag):
    scene=bpy.context.scene; scene.render.engine="BLENDER_WORKBENCH"
    scene.render.resolution_x=400;scene.render.resolution_y=400;scene.render.resolution_percentage=100
    scene.render.image_settings.file_format="PNG"
    scene.display.shading.light="STUDIO";scene.display.shading.color_type="SINGLE"
    scene.display.shading.single_color=(0.65,0.66,0.70)
    scene.render.film_transparent=False
    cam=next((x for x in bpy.data.objects if x.type=="CAMERA"),None)
    if cam is None: bpy.ops.object.camera_add();cam=bpy.context.object
    scene.camera=cam;cam.data.type="ORTHO";cam.data.ortho_scale=3.05
    for label,pos in [("FRONT",(0,-5,0.5)),("SIDE",(5,0,0.5)),("THREE_QUARTER",(4,-5,2.5))]:
        cam.location=Vector(pos);cam.rotation_euler=(Vector((0,0,0))-cam.location).to_track_quat("-Z","Y").to_euler()
        fn=OUT/f"{tag}_{label}.png";scene.render.filepath=str(fn)
        bpy.ops.render.render(write_still=True)
        assert fn.stat().st_size>1000,str(fn)
def build():
    assert bpy.app.version_string.startswith("5.2.2"),bpy.app.version_string
    obj=bpy.data.objects.get("V063_TEACHER_FIRST_ORIGINAL_SPHERE")
    if obj is None or obj.type!="MESH":raise RuntimeError("Actual V063 object missing")
    baseline=metric(obj)
    if baseline["position_sha256"]!=SOURCE_EXPECTED_SHA:
        raise RuntimeError("Wrong original repaired V063 source mesh "+baseline["position_sha256"])
    if baseline["vertex_count"]!=4514:raise RuntimeError("Input topology mismatch")
    coords_before=[v.co.copy() for v in obj.data.vertices]
    views("BEFORE")
    bpy.ops.object.select_all(action="DESELECT");obj.select_set(True);bpy.context.view_layer.objects.active=obj
    bpy.ops.object.mode_set(mode="SCULPT")
    v=viewport()
    with bpy.context.temp_override(**v):
        result=bpy.ops.brush.asset_activate(asset_library_type="ESSENTIALS",
             relative_asset_identifier="brushes/essentials_brushes-mesh_sculpt.blend/Brush/Smooth")
    assert "FINISHED" in result,"Smooth asset activation rejected"
    brush=bpy.context.tool_settings.sculpt.brush
    assert brush and brush.name=="Smooth","Not real Smooth asset"
    brush.strength=0.65;brush.size=110
    bpy.ops.ed.undo_push()
    bpy.ops.object.mode_set(mode="OBJECT");bpy.ops.object.mode_set(mode="SCULPT")
    v=viewport();w,h=v["area"].width,v["area"].height
    stroke=[]
    for i in range(75):
        t=i/74
        x=w*(0.38+0.24*t);y=h*0.50
        stroke.append(dict(name="stroke",mouse=(x,y),mouse_event=(int(x),int(y)),
            location=(0.,0.,0.),is_start=i==0,pressure=1.0,time=1.+i/60.,
            size=1.,x_tilt=0.,y_tilt=0.))
    with bpy.context.temp_override(**v):
        if not bpy.ops.sculpt.brush_stroke.poll(): raise RuntimeError("Smooth brush_stroke poll failed")
        outcome=bpy.ops.sculpt.brush_stroke(stroke=stroke,override_location=True)
    bpy.ops.object.mode_set(mode="OBJECT")
    after=metric(obj)
    disp=[float((vert.co-co).length) for co,vert in zip(coords_before,obj.data.vertices)]
    moved=sum(n>1e-7 for n in disp)
    volchange=after["volume"]-baseline["volume"]
    result=dict(schema="V064_REAL_NATIVE_KASPAR_SMOOTH",
        version=bpy.app.version_string,authoritative_teacher="Julien Kaspar Blender Studio Sculpting Fundamentals 08:28–09:13",
        source_blend="V063 repaired real SCULPT.blend, GitHub Actions 44305384790",
        source_mesh_sha_expected=SOURCE_EXPECTED_SHA,
        baseline=baseline,after=after,
        native_operator="bpy.ops.sculpt.brush_stroke",native_asset=brush.name,
        native_strength=float(brush.strength),native_size=int(brush.size),
        events=len(stroke),view_size=[w,h],stroke_finished=("FINISHED" in outcome),
        volume_delta=volchange,volume_delta_percent=volchange/baseline["volume"]*100.,
        moved_vertices=moved,max_vertex_displacement=max(disp),
        mean_vertex_displacement=sum(disp)/len(disp),
        native_mesh_change=after["position_sha256"]!=baseline["position_sha256"],
        same_topology=(after["vertex_count"]==baseline["vertex_count"] and after["face_count"]==baseline["face_count"]),
        volume_reduced=after["volume"]<baseline["volume"],
        technical_pass=("FINISHED" in outcome and moved>0 and after["volume"]<baseline["volume"]
            and after["vertex_count"]==baseline["vertex_count"]),
        bitwise_repeat_proved=False,artist_approved=False,protected_assets_touched=False,
        valid_claim="One real Smooth stroke on V063 saved Draw repair; no artist approval nor general smoothing efficacy")
    output("SMOOTH_ACTUAL_BUILD_RECEIPT.json",result)
    print("V064_NATIVE_SMOOTH_RECEIPT",json.dumps(result),flush=True)
    views("AFTER")
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/"SMOOTH.blend"))
    if not result["technical_pass"]:
        print("V064_TECHNICAL_GATE_HOLD; consult native evidence",flush=True)
        raise SystemExit(64)
def verify():
    record=json.loads((OUT/"SMOOTH_ACTUAL_BUILD_RECEIPT.json").read_text())
    obj=bpy.data.objects.get("V063_TEACHER_FIRST_ORIGINAL_SPHERE")
    if obj is None:raise RuntimeError("Missing smooth native object on reopen")
    actual=metric(obj)
    assert actual["position_sha256"]==record["after"]["position_sha256"],"Fresh reopened positions differ"
    assert actual["volume"]==record["after"]["volume"],"Fresh reopened volume differs"
    assert record["technical_pass"] and record["native_asset"]=="Smooth"
    output("SMOOTH_REOPEN_RECEIPT.json",dict(fresh_reopen_pass=True,source_input_sha=SOURCE_EXPECTED_SHA,
        after_sha=actual["position_sha256"],volume=actual["volume"],artist_approved=False))
    print("V064_SMOOTH_NATIVE_REOPEN_PASS",actual["position_sha256"],flush=True)
if ACTION=="build":build()
elif ACTION=="verify":verify()
else:raise ValueError(ACTION)
