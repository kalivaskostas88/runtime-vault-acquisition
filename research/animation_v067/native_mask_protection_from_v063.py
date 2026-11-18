# SPDX-License-Identifier: GPL-2.0-or-later
"""V067: Actual native Sculpt Mask protection versus unmasked Draw control.
Teacher: Julien Kaspar Sculpting Fundamentals 12:43-14:48 (CC-BY).
Official Blender Foundation sculpt brush asset + stroke operator method (GPL-2.0+).
Two disposable copies of one verified V063 saved .blend. No procedural substitute.
"""
import bpy, bmesh, json, hashlib, pathlib, sys, struct, math
from mathutils import Vector
args=sys.argv[sys.argv.index("--")+1:]
CASE=args[0]; OUT=pathlib.Path(args[1]).resolve(); OUT.mkdir(parents=True,exist_ok=True)
BASE="123e2a9a0ab77b9b0d5872686a3c98057eb6d939e2cdaa99382d367808877ec9"
SOURCE_FILE_SHA="f4f62d23cd0fc5167513825fffd36ab9b82e98d198d50d49feb44e86040d2ecc"
OBJ_NAME="V063_TEACHER_FIRST_ORIGINAL_SPHERE"
def save(name,data):
    (OUT/name).write_text(json.dumps(data,ensure_ascii=False,indent=2,sort_keys=True)+"\n")
def mesh_state(obj):
    me=obj.data
    bytes_=b"".join(struct.pack("<ddd",*[float(v) for v in x.co]) for x in me.vertices)
    bm=bmesh.new();bm.from_mesh(me);vol=abs(bm.calc_volume(signed=True));bm.free()
    return {"sha":hashlib.sha256(bytes_).hexdigest(),"vertices":len(me.vertices),
            "faces":len(me.polygons),"volume":vol}
def coordinates(obj):
    return [[float(c) for c in v.co] for v in obj.data.vertices]
def masks(obj):
    attr=obj.data.attributes.get(".sculpt_mask")
    if attr is None:return None
    return [float(x.value) for x in attr.data]
def region():
    ctx=bpy.context.copy()
    for area in ctx["screen"].areas:
        if area.type=="VIEW_3D":
            r=next((r for r in area.regions if r.type=="WINDOW"),None)
            if r:
                ctx.update({"area":area,"region":r})
                area.spaces.active.region_3d.view_location=Vector((0,0,0))
                area.spaces.active.region_3d.view_distance=4.0
                return ctx
    raise RuntimeError("VIEW_3D missing; cannot claim native Mask")
def brush_stroke(obj,asset,strength,size):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True);bpy.context.view_layer.objects.active=obj
    bpy.ops.object.mode_set(mode="SCULPT")
    ctx=region()
    with bpy.context.temp_override(**ctx):
        result=bpy.ops.brush.asset_activate(asset_library_type="ESSENTIALS",
            relative_asset_identifier="brushes/essentials_brushes-mesh_sculpt.blend/Brush/"+asset)
    if "FINISHED" not in result:raise RuntimeError("Actual brush asset activation failed: "+asset)
    brush=bpy.context.tool_settings.sculpt.brush
    if brush is None or brush.name!=asset:raise RuntimeError("Wrong active brush: "+str(brush))
    brush.strength=strength;brush.size=size
    bpy.ops.ed.undo_push()
    bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.mode_set(mode="SCULPT")
    ctx=region();w=ctx["area"].width;h=ctx["area"].height
    events=[]
    for i in range(75):
        t=i/74.;x=w*(0.38+0.24*t);y=h/2.
        events.append(dict(name="stroke",mouse=(x,y),mouse_event=(int(x),int(y)),
            location=(0.,0.,0.),is_start=i==0,pressure=1.,time=1.+i/60.,
            size=1.,x_tilt=0.,y_tilt=0.))
    with bpy.context.temp_override(**ctx):
        if not bpy.ops.sculpt.brush_stroke.poll():raise RuntimeError("Genuine sculpt operator cannot run")
        done=bpy.ops.sculpt.brush_stroke(stroke=events,override_location=True)
    bpy.ops.object.mode_set(mode="OBJECT")
    if "FINISHED" not in done:raise RuntimeError("Native brush stroke failed")
    return {"brush":brush.name,"brush_type":brush.sculpt_brush_type,
            "strength":float(brush.strength),"size":int(brush.size),
            "events":75,"viewport":[w,h],"result":sorted(done)}
def render_views(label):
    scene=bpy.context.scene
    scene.render.engine="BLENDER_WORKBENCH"
    scene.render.resolution_x=400;scene.render.resolution_y=400;scene.render.resolution_percentage=100
    scene.render.image_settings.file_format="PNG"
    scene.display.shading.light="STUDIO";scene.display.shading.color_type="SINGLE"
    scene.display.shading.single_color=(0.65,0.66,0.70)
    cam=next((o for o in bpy.data.objects if o.type=="CAMERA"),None)
    if cam is None:
        bpy.ops.object.camera_add();cam=bpy.context.object
    scene.camera=cam;cam.data.type="ORTHO";cam.data.ortho_scale=3.05
    for v,p in [("FRONT",(0,-5,0.5)),("SIDE",(5,0,0.5)),("THREE_QUARTER",(4,-5,2.5))]:
        cam.location=Vector(p)
        cam.rotation_euler=(Vector((0,0,0))-cam.location).to_track_quat("-Z","Y").to_euler()
        fn=OUT/f"{label}_{v}.png";scene.render.filepath=str(fn)
        bpy.ops.render.render(write_still=True)
        if fn.stat().st_size<1000:raise RuntimeError("Empty render: "+str(fn))
def run_case():
    assert bpy.app.version_string.startswith("5.2.2"),bpy.app.version_string
    obj=bpy.data.objects.get(OBJ_NAME)
    assert obj and obj.type=="MESH","Not the actual saved V063 object"
    before=mesh_state(obj)
    assert before["sha"]==BASE and before["vertices"]==4514,("Wrong baseline",before)
    original_coords=coordinates(obj)
    old_masks=masks(obj)
    if old_masks and max(old_masks)>1e-7:raise RuntimeError("Source unexpectedly had a mask")
    render_views("BEFORE")
    m=None;mask_stroke=None;mask_only=before.copy()
    if CASE=="masked":
        mask_stroke=brush_stroke(obj,"Mask",1.0,140)
        mask_only=mesh_state(obj)
        m=masks(obj)
        if m is None:
            save("ERROR_RECEIPT.json",{"reason":"Native Mask stroke produced no .sculpt_mask attribute","mask_stroke":mask_stroke})
            raise RuntimeError("Native Mask attribute absent after painting; API investigation required")
        if mask_only["sha"]!=before["sha"]:
            raise RuntimeError("Mask-only stroke changed vertex positions; stop")
        if len(m)!=before["vertices"]:raise RuntimeError("Unexpected mask length")
    draw_stroke=brush_stroke(obj,"Draw",0.16,110)
    after=mesh_state(obj)
    endcoords=coordinates(obj)
    displacements=[math.dist(a,b) for a,b in zip(original_coords,endcoords)]
    if CASE=="masked":
        m_final=masks(obj)
        if m_final is None or max(abs(x-y) for x,y in zip(m,m_final))>1e-6:
            raise RuntimeError("Mask values mutated unexpectedly during Draw")
    render_views("AFTER")
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/"RESULT.blend"))
    res={"schema":"V067_TRUE_NATIVE_MASK_PROTECTION_STUDY","case":CASE,
         "version":bpy.app.version_string,"source_mesh_sha":BASE,
         "source_blend_sha":SOURCE_FILE_SHA,"teacher":"Julien Kaspar Sculpting Fundamentals 12:43-14:48 (CC-BY, original sampled frames and caption study)",
         "before":before,"mask_only_geometry":mask_only,"after":after,
         "mask_stroke":mask_stroke,"draw_stroke":draw_stroke,
         "mask_values":m if CASE=="masked" else [0.]*before["vertices"],
         "mask_gt_05":sum(x>=0.5 for x in m) if m is not None else 0,
         "mask_gt_09":sum(x>=0.9 for x in m) if m is not None else 0,
         "max_mask":max(m) if m is not None else 0.,
         "draw_displacements":displacements,
         "changed_vertices":sum(x>1e-7 for x in displacements),
         "geometry_changed":before["sha"]!=after["sha"],
         "art_approval":False,"protected_assets_touched":False,
         "no_claim_of_full_av_listening":True}
    save("BUILD_RECEIPT.json",res)
    print("V067_REAL_NATIVE_MASK_CASE",json.dumps({k:v for k,v in res.items() if k not in ("mask_values","draw_displacements")}),flush=True)
    if not res["geometry_changed"] and CASE=="control":raise RuntimeError("Control Draw did not change mesh")
    if CASE=="masked" and res["mask_gt_05"]<20:raise RuntimeError("Native Mask did not cover enough real vertices")
def reopen():
    r=json.loads((OUT/"BUILD_RECEIPT.json").read_text())
    obj=bpy.data.objects.get(OBJ_NAME)
    assert obj and obj.type=="MESH"
    state=mesh_state(obj)
    assert state["sha"]==r["after"]["sha"] and state["volume"]==r["after"]["volume"]
    if r["case"]=="masked":
        saved=masks(obj)
        assert saved is not None and len(saved)==len(r["mask_values"])
        assert max(abs(x-y) for x,y in zip(saved,r["mask_values"]))<1e-6
    save("REOPEN_RECEIPT.json",{"fresh_blender_reopen_pass":True,"case":r["case"],
        "final_mesh_sha":state["sha"],"mask_attribute_preserved":r["case"]=="masked",
        "art_approval":False})
    print("V067_REOPEN_PASS",r["case"],state["sha"])
if CASE in ("control","masked"):run_case()
elif CASE=="verify":reopen()
else:raise RuntimeError("Unknown case "+CASE)
