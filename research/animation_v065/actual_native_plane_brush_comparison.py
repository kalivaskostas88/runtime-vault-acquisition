# SPDX-License-Identifier: GPL-2.0-or-later
"""V065 teacher-first real native PLANE brush A/B on the exact saved V063 repaired .blend.
Sources:
* Julien Kaspar, Sculpting Fundamentals CC-BY 08:25-10:13; original source study V061.
* Blender 5.2 manual Essentials sculpt brush assets "Flatten/Contrast", "Scrape/Fill".
* Blender Foundation brush_asset_test.py and sculpt_brush_render_tests.py GPL-2.0-or-later.
Not a character sculpt or artistic approval; source asset never overwritten.
"""
import bpy, bmesh, hashlib, json, math, pathlib, struct, sys
from mathutils import Vector
import numpy as np
a=sys.argv[sys.argv.index("--")+1:]
MODE=a[0]
OUT=pathlib.Path(a[1]).resolve()
OUT.mkdir(parents=True,exist_ok=True)
BASE_SHA="123e2a9a0ab77b9b0d5872686a3c98057eb6d939e2cdaa99382d367808877ec9"
SOURCE_BLEND_SHA="f4f62d23cd0fc5167513825fffd36ab9b82e98d198d50d49feb44e86040d2ecc"
BRUSHES={"flatten":"Flatten/Contrast","scrape":"Scrape/Fill"}
def metric(ob):
    mesh=ob.data
    raw=b"".join(struct.pack("<ddd",*[float(c) for c in vert.co]) for vert in mesh.vertices)
    bm=bmesh.new();bm.from_mesh(mesh);vol=abs(bm.calc_volume(signed=True));bm.free()
    return {"vertex_count":len(mesh.vertices),"face_count":len(mesh.polygons),
            "position_sha256":hashlib.sha256(raw).hexdigest(),"volume":vol,
            "x_max":max(float(v.co.x) for v in mesh.vertices),
            "y_max":max(float(v.co.y) for v in mesh.vertices)}
def geometry(ob):
    return np.array([[float(c) for c in vert.co] for vert in ob.data.vertices],dtype=np.float64)
def local_roi(coords):
    # Same fixed pre-treatment vertex indices in both treatments; visible X-facing bulge.
    ids=np.where((coords[:,0]>0.78)&(np.abs(coords[:,1])<0.7)&(np.abs(coords[:,2])<0.7))[0]
    assert len(ids)>=20,("Insufficient fixed ROI",len(ids))
    return ids
def planarity(coords,ids):
    p=coords[ids]
    centered=p-p.mean(axis=0)
    _,sv,_=np.linalg.svd(centered,full_matrices=False)
    return {"plane_rmse":float(sv[-1]/math.sqrt(len(ids))),
            "centroid":p.mean(axis=0).tolist(),
            "singular_values":sv.tolist()}
def persist(fname,d):
    (OUT/fname).write_text(json.dumps(d,ensure_ascii=False,indent=2,sort_keys=True)+"\n")
def view_override():
    ctx=bpy.context.copy()
    for area in ctx["screen"].areas:
        if area.type=="VIEW_3D":
            region=next((r for r in area.regions if r.type=="WINDOW"),None)
            if region:
                ctx["area"]=area;ctx["region"]=region
                area.spaces.active.region_3d.view_location=Vector((0.,0.,0.))
                area.spaces.active.region_3d.view_distance=4.
                return ctx
    raise RuntimeError("No VIEW_3D window; native brush unavailable")
def render_views(stage):
    scene=bpy.context.scene;scene.render.engine="BLENDER_WORKBENCH"
    scene.render.resolution_x=400;scene.render.resolution_y=400;scene.render.resolution_percentage=100
    scene.render.image_settings.file_format="PNG"
    scene.display.shading.light="STUDIO";scene.display.shading.color_type="SINGLE"
    scene.display.shading.single_color=(0.65,0.66,0.70)
    scene.render.film_transparent=False
    cam=next((x for x in bpy.data.objects if x.type=="CAMERA"),None)
    if cam is None:
        bpy.ops.object.camera_add()
        cam=bpy.context.object
    scene.camera=cam;cam.data.type="ORTHO";cam.data.ortho_scale=3.05
    for name,pos in [("FRONT",(0,-5,0.5)),("SIDE",(5,0,0.5)),("THREE_QUARTER",(4,-5,2.5))]:
        cam.location=Vector(pos)
        cam.rotation_euler=(Vector((0,0,0))-cam.location).to_track_quat("-Z","Y").to_euler()
        target=OUT/f"{stage}_{name}.png";scene.render.filepath=str(target)
        bpy.ops.render.render(write_still=True)
        if target.stat().st_size<1000:raise RuntimeError("Empty genuine render "+str(target))
def run():
    assert bpy.app.version_string.startswith("5.2.2"),"Unexpected Blender version"
    obj=bpy.data.objects.get("V063_TEACHER_FIRST_ORIGINAL_SPHERE")
    assert obj is not None and obj.type=="MESH","Actual original V063 object missing"
    before=metric(obj)
    assert before["position_sha256"]==BASE_SHA,"Source geometry did not match V063 run2"
    coords_before=geometry(obj);ids=local_roi(coords_before)
    plane_before=planarity(coords_before,ids)
    render_views("BEFORE")
    bpy.ops.object.select_all(action="DESELECT");obj.select_set(True);bpy.context.view_layer.objects.active=obj
    bpy.ops.object.mode_set(mode="SCULPT")
    view=view_override();asset=BRUSHES[MODE]
    with bpy.context.temp_override(**view):
        result=bpy.ops.brush.asset_activate(asset_library_type="ESSENTIALS",
            relative_asset_identifier="brushes/essentials_brushes-mesh_sculpt.blend/Brush/"+asset)
    assert "FINISHED" in result,"Official 5.2 asset not activated: "+asset
    brush=bpy.context.tool_settings.sculpt.brush
    assert brush and brush.name==asset,("Wrong active asset",str(brush))
    assert brush.sculpt_brush_type=="PLANE",("Legacy brush type not verified",brush.sculpt_brush_type)
    brush.strength=0.65;brush.size=110
    bpy.ops.ed.undo_push()
    bpy.ops.object.mode_set(mode="OBJECT");bpy.ops.object.mode_set(mode="SCULPT")
    view=view_override();w,h=view["area"].width,view["area"].height
    events=[]
    for i in range(75):
        t=i/74
        x=w*(0.38+0.24*t);y=h*0.5
        events.append(dict(name="stroke",mouse=(x,y),mouse_event=(int(x),int(y)),
            location=(0.,0.,0.),is_start=i==0,pressure=1.,time=1.+i/60.,
            size=1.,x_tilt=0.,y_tilt=0.))
    with bpy.context.temp_override(**view):
        assert bpy.ops.sculpt.brush_stroke.poll(),"Real Blender native stroke cannot run"
        stroke_result=bpy.ops.sculpt.brush_stroke(stroke=events,override_location=True)
    bpy.ops.object.mode_set(mode="OBJECT")
    after=metric(obj);coords_after=geometry(obj)
    diff=np.linalg.norm(coords_after-coords_before,axis=1)
    moved=int(np.count_nonzero(diff>1e-7))
    plane_after=planarity(coords_after,ids)
    receipt={"schema":"V065_REAL_NATIVE_PLANE_BRUSH_AB_ON_V063",
        "source":"exact V063 repaired native model, run 44305384790",
        "source_file_sha256":SOURCE_BLEND_SHA,"input_mesh_sha256":BASE_SHA,
        "teacher":"Julien Kaspar Sculpting Fundamentals 08:25-10:13",
        "teacher_studied_level":"2019 original MP4 sampled visually plus original 378 timecoded captions; not full audio listened",
        "manual_52":"https://docs.blender.org/manual/en/5.2/sculpt_paint/sculpting/brushes/brushes.html",
        "blender_version":bpy.app.version_string,"case":MODE,"actual_brush_name":brush.name,
        "actual_brush_type":brush.sculpt_brush_type,"native_operator":"bpy.ops.sculpt.brush_stroke",
        "strength":float(brush.strength),"size":int(brush.size),"events":len(events),
        "viewport":[w,h],"stroke_finished":"FINISHED" in stroke_result,
        "before":before,"after":after,"roi_n":len(ids),
        "roi_selection":"pre-treatment X > 0.78, abs(Y) < 0.7, abs(Z) < 0.7",
        "roi_flatness_before":plane_before,"roi_flatness_after":plane_after,
        "roi_flatness_rmse_delta":plane_after["plane_rmse"]-plane_before["plane_rmse"],
        "roi_flatness_improved":plane_after["plane_rmse"]<plane_before["plane_rmse"],
        "volume_delta_percent":100*(after["volume"]/before["volume"]-1),
        "moved_vertices":moved,"mean_vertex_displacement":float(np.mean(diff)),
        "max_vertex_displacement":float(np.max(diff)),
        "native_geometry_changed":before["position_sha256"]!=after["position_sha256"],
        "same_topology":before["vertex_count"]==after["vertex_count"] and before["face_count"]==after["face_count"],
        "technical_pass":"FINISHED" in stroke_result and moved>0 and before["position_sha256"]!=after["position_sha256"] and before["vertex_count"]==after["vertex_count"],
        "plane_quality_claim_only_if_measurement":True,
        "art_approved":False,"is_original_licensed_third_party_media":False,"protected_assets_touched":False}
    persist("BUILD_RECEIPT.json",receipt)
    render_views("AFTER")
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/"RESULT.blend"))
    print("V065_NATIVE_PLANE_CASE",json.dumps(receipt,ensure_ascii=False),flush=True)
    if not receipt["technical_pass"]:
        raise RuntimeError("Genuine PLANE brush did not change mesh; see original receipt")
def verify():
    r=json.loads((OUT/"BUILD_RECEIPT.json").read_text())
    obj=bpy.data.objects.get("V063_TEACHER_FIRST_ORIGINAL_SPHERE")
    assert obj and obj.type=="MESH"
    m=metric(obj)
    assert m["position_sha256"]==r["after"]["position_sha256"],"Fresh reopen mesh SHA mismatch"
    assert m["volume"]==r["after"]["volume"],"Fresh reopen volume mismatch"
    assert r["technical_pass"] and r["actual_brush_type"]=="PLANE"
    persist("REOPEN_RECEIPT.json",{"fresh_reopen_pass":True,"case":r["case"],
        "verified_mesh_sha256":m["position_sha256"],"verified_volume":m["volume"],
        "art_approved":False})
    print("V065_NATIVE_PLANE_REOPEN_PASS",r["case"],m["position_sha256"],flush=True)
if MODE=="flatten" or MODE=="scrape":
    run()
elif MODE=="verify":
    verify()
else:
    raise RuntimeError("Unexpected case "+MODE)
