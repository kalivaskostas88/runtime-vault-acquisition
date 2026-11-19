#!/usr/bin/env python3
"""V071 scoped native mechanical proof: three-body primitive joint voxel union.
Sources: teacher Julien Kaspar Blender Studio public written 4.5 LTS lessons,
historical licensed full video Fundamentals 2.80 visually inspected (not current
voxel lesson AV), and Blender 5.2 official mesh API.
NO protected GS001/V046 inputs, NO professional art approval claimed.
"""
import bpy,bmesh,os,sys,json,pathlib,hashlib,math
from mathutils import Vector
OUT=pathlib.Path("v071_body_fusion");OUT.mkdir(exist_ok=True)
BASE=pathlib.Path("v068_blockout/V068_ELEPHANT_MASS_BLOCKOUT.blend")
EXPECTED_SHA="5c31b092ea84a8bf50cbe25bdb5f7cef94a54127175c34d70c8cb2ed45beb31f"
VOXEL=0.06   # Predeclared single candidate. Do not tune blindly after observing outcome.
MAX_BBOX_SHIFT=0.14
VERT_CAP=180000
THREE=("01_BARREL_BODY","02_CHEST_SHOULDER","03_BACK_RUMP")
status={"schema":"V071_NATIVE_THREE_MASS_VOXEL_FUSION","blender_expected":"5.2.2",
        "source_native_sha256_expected":EXPECTED_SHA,"teacher_video_full_AV":"NO",
        "teacher_written_method":"PUBLIC_SOURCE_STUDIED",
        "old_teacher_fundamentals_video":"ALL_16_HALF_FPS_CONTACT_BOARDS_ACTUALLY_VISUALLY_REVIEWED; ORIGINAL_VTT_READ; FULL_AUDIO_NOT_LISTENED",
        "parameters_predeclared":{"voxel_size":VOXEL,"max_bbox_shift":MAX_BBOX_SHIFT,"vertex_cap":VERT_CAP},
        "status":"INIT","art":"HOLD","protected_assets":"NOT_TOUCHED"}
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def locs(o):
    return sorted((tuple(round(float(c),7) for c in o.matrix_world@v.co) for v in o.data.vertices))
def simple_fingerprint(o):
    if o.type=="MESH":
        me=o.data
        raw=[o.name,o.type,[round(x,8) for row in o.matrix_world for x in row],
             len(me.vertices),len(me.edges),len(me.polygons)]
        data=str(raw).encode()
        for v in me.vertices:
            data+=f"{v.co.x:.8f}:{v.co.y:.8f}:{v.co.z:.8f};".encode()
        return hashlib.sha256(data).hexdigest()
    if o.type=="CURVE":
        data=[o.name,o.type,[round(x,8) for row in o.matrix_world for x in row],o.data.bevel_depth,
              [(tuple(round(float(v),8) for v in p.co),float(p.radius)) for sp in o.data.splines for p in sp.bezier_points]]
        return hashlib.sha256(str(data).encode()).hexdigest()
    return None
def component_count(bm):
    unseen=set(bm.verts);ct=0
    while unseen:
        ct+=1; todo=[unseen.pop()]
        while todo:
            for edge in todo.pop().link_edges:
                v=edge.other_vert(edge.verts[0]) if False else None
                for v in edge.verts:
                    if v in unseen:unseen.remove(v);todo.append(v)
    return ct
def measure(me):
    bm=bmesh.new()
    try:
        bm.from_mesh(me);bm.verts.ensure_lookup_table();bm.edges.ensure_lookup_table()
        return {"components":component_count(bm),
             "verts":len(bm.verts),"faces":len(bm.faces),
             "boundary_edges":sum(1 for e in bm.edges if e.is_boundary),
             "nonmanifold_edges":sum(1 for e in bm.edges if not e.is_manifold),
             "volume":bm.calc_volume(signed=False)}
    finally:bm.free()
def bbox(o):
    pts=[o.matrix_world@Vector(x) for x in o.bound_box]
    return [[min(v[i] for v in pts),max(v[i] for v in pts)] for i in range(3)]
def render_views():
    sc=bpy.context.scene
    if not sc.camera:raise RuntimeError("No original camera in saved blend")
    original_resolution=(sc.render.resolution_x,sc.render.resolution_y,sc.render.resolution_percentage)
    orig_view=(tuple(sc.camera.location),tuple(sc.camera.rotation_euler))
    cam=sc.camera
    poses={"SIDE":(0,-9,3.0),"FACE":(-9,0,3.0),"THREE_QUARTER":(-7,-8,5.0),"TOP":(0,-0.3,11)}
    target=Vector((-.25,0,1.89))
    hashes={}
    for label,coord in poses.items():
        cam.location=Vector(coord)
        cam.rotation_euler=(target-cam.location).to_track_quat("-Z","Y").to_euler()
        p=(OUT/("AFTER_"+label+".png")).resolve()
        sc.render.filepath=str(p);bpy.ops.render.render(write_still=True)
        assert p.stat().st_size>2000
        hashes[p.name]=digest(p)
    cam.location=orig_view[0];cam.rotation_euler=orig_view[1]
    assert (sc.render.resolution_x,sc.render.resolution_y,sc.render.resolution_percentage)==original_resolution
    return hashes
try:
    assert bpy.app.version_string.startswith("5.2.2"),bpy.app.version_string
    assert BASE.is_file(),"V068 original reusable .blend source missing"
    source_sha=digest(BASE);status["actual_source_sha256"]=source_sha
    assert source_sha==EXPECTED_SHA, "Input V068 SHA mismatch; no editing allowed"
    bpy.ops.wm.open_mainfile(filepath=str(BASE.resolve()))
    objects=bpy.data.objects
    core=[objects[n] for n in THREE]
    assert all(x.type=="MESH" for x in core)
    assert all(max(abs(s-1) for s in x.scale)<1e-6 for x in core)
    assert all(len(x.modifiers)==0 for x in core),"Core has unaccounted modifiers"
    before_mesh_objects={o.name:simple_fingerprint(o) for o in objects if o.get("stage")=="BLOCKOUT_NOT_FINAL" and o.name not in THREE}
    orig_refs={im.name:(len(im.packed_files),tuple(im.size)) for im in bpy.data.images if im.packed_file or len(im.packed_files)>0}
    assert len(orig_refs)>=3, "Lost packed CC0 source reference"
    original_parts={n:measure(objects[n].data) for n in THREE}
    assert all(p["boundary_edges"]==0 and p["components"]==1 for p in original_parts.values()),original_parts
    old_bb=[[min(bbox(o)[i][0] for o in core),max(bbox(o)[i][1] for o in core)] for i in range(3)]
    bpy.ops.object.mode_set(mode="OBJECT") if bpy.context.object and bpy.context.object.mode!="OBJECT" else None
    bpy.ops.object.select_all(action="DESELECT")
    for o in core:o.select_set(True)
    bpy.context.view_layer.objects.active=core[0]
    bpy.ops.object.join()
    union=bpy.context.view_layer.objects.active
    assert union and union.name==THREE[0]
    no_fusion=measure(union.data)
    assert no_fusion["components"]==3, f"Join-only negative control failed: {no_fusion}"
    status["join_only_negative_control"]=no_fusion
    union.data.remesh_voxel_size=VOXEL
    assert bpy.ops.object.voxel_remesh.poll()
    action=bpy.ops.object.voxel_remesh()
    assert "FINISHED" in action,action
    result=measure(union.data)
    after_bb=bbox(union)
    bb_drifts=[max(abs(a-b) for a,b in zip(old_bb[i],after_bb[i])) for i in range(3)]
    status["native_remesh"]={"result":result,"world_bbox_before":old_bb,"world_bbox_after":after_bb,"bbox_drift":bb_drifts}
    assert result["components"]==1,"Remeshed body remains disjoint"
    assert result["boundary_edges"]==0 and result["nonmanifold_edges"]==0, "Output not closed 2-manifold"
    assert 500 < result["verts"] < VERT_CAP, "Unexpected catastrophic topology density"
    assert max(bb_drifts)<MAX_BBOX_SHIFT, "Significant outer silhouette bbox drift"
    assert result["volume"]>0.1
    changed={name:(simple_fingerprint(objects[name])!=h) for name,h in before_mesh_objects.items()}
    status["other_objects_mutated"]=changed
    assert not any(changed.values()),"An unrelated native asset changed"
    check_refs={im.name:(len(im.packed_files),tuple(im.size)) for im in bpy.data.images if im.packed_file or len(im.packed_files)>0}
    assert check_refs==orig_refs,"Packed photographic reference metadata changed"
    union["stage"]="RESEARCH_BODY_CORE_FUSION_NOT_ART_APPROVED"
    union["source_parts"]=list(THREE)
    union["voxel_size"]=VOXEL
    union["art_reviewer"]="NOT_PERFORMED"
    status["view_render_sha256"]=render_views()
    f=(OUT/"V071_THREE_BODY_FUSION_CANDIDATE.blend").resolve()
    bpy.ops.wm.save_as_mainfile(filepath=str(f))
    status["saved_file_sha256"]=digest(f)
    status["expected_object_count_delta"]=2
    status["status"]="NATIVE_BOUNDED_MECHANICAL_PASS; ART_HOLD; REPEAT_PENDING"
except BaseException as e:
    status["status"]="FAILED_OR_TOOL_HOLD"
    status["error"]=repr(e)
finally:
    (OUT/"V071_NATIVE_BODY_FUSION_RECEIPT.json").write_text(json.dumps(status,ensure_ascii=False,indent=2)+"\n")
    print("V071_NATIVE_RESULT",json.dumps({k:status.get(k) for k in ("status","error","native_remesh","other_objects_mutated","saved_file_sha256")},ensure_ascii=False)[:6000],flush=True)
if status["status"].startswith("FAILED"):sys.exit(71)
