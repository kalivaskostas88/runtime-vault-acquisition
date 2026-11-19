# SPDX-License-Identifier: GPL-2.0-or-later
"""V077 real native topology feasibility preflight on V076 Blender original.
Two isolated original ear mesh DUPLICATES + Blender 5.2.2 native Multires
SIMPLE vs CATMULL_CLARK (two levels), actual evaluated mesh metrics.
No new sculpt/crease is claimed; no alterations to original V076 resources.
Source licenses: Blender Foundation Multires manual, Blender Studio Julien Kaspar
Detailed Sculpting source excerpt. New teacher video not watched.
"""
import bpy,bmesh,math,json,hashlib,struct,sys,pathlib
from mathutils import Vector
from mathutils.bvhtree import BVHTree
OUT=pathlib.Path("v077_topology_preflight");OUT.mkdir(exist_ok=True)
INPUT=pathlib.Path("v076_curve_ear_rim/V076_ACTUAL_NATIVE_CURVE_GUIDED_EAR_RIM_CANDIDATE.blend")
INPUT_SHA="2c537d34ec5eb68ec1b7ba1b99677f68f5730fae2b3e24efd474f548b4d4e99d"
EAR="06_EAR_NEAR"
MODES=("SIMPLE","CATMULL_CLARK")
LEVELS=2
CAP=40000
r={"schema":"V077_REAL_NATIVE_MULTRES_TOPOLOGY_AB_STUDY",
 "exact_original_sha256_expected":INPUT_SHA,"version_required":"Blender 5.2.2",
 "teacher":"Blender Studio Julien Kaspar Detailed Sculpting: prepare good multires base mesh, high levels can freeze; public excerpt only",
 "official_api":"Blender Foundation Multiresolution modifier manual",
 "full_new_teacher_video_watched":False,"audio_listened":False,
 "experiment":"Two isolated native Multires modifiers on source-locked copies of V076 actual ear; same 2 levels, A/B SIMPLE and CATMULL_CLARK",
 "limits":{"levels":LEVELS,"vertex_cap":CAP},
 "art_approved":False,"real_fold_created":False,"status":"INIT"}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def local_hash(o):
 h=hashlib.sha256()
 h.update(o.type.encode())
 for row in o.matrix_world:
  for x in row:h.update(struct.pack("<d",float(x)))
 if o.type=="MESH":
  h.update(str((len(o.data.vertices),len(o.data.edges),len(o.data.polygons))).encode())
  for v in o.data.vertices:h.update(struct.pack("<ddd",*map(float,v.co)))
 elif o.type=="CURVE":
  h.update(str((o.data.bevel_depth,[[tuple(map(float,p.co)),float(p.radius)] for s in o.data.splines for p in s.bezier_points])).encode())
 return h.hexdigest()
def measure_mesh(mesh,mat):
 bm=bmesh.new()
 try:
  bm.from_mesh(mesh); bm.verts.ensure_lookup_table()
  vol=abs(bm.calc_volume(signed=True))*abs(mat.determinant())
  boundary=sum(1 for edge in bm.edges if edge.is_boundary)
  nonmanifold=sum(1 for edge in bm.edges if not edge.is_manifold)
  pts=[mat@v.co for v in bm.verts]
  bbox=[[min(float(p[i]) for p in pts),max(float(p[i]) for p in pts)] for i in range(3)]
  return {"verts":len(bm.verts),"edges":len(bm.edges),"faces":len(bm.faces),
    "boundary_edges":boundary,"nonmanifold_edges":nonmanifold,
    "signed_volume_abs":vol,"world_bbox":bbox}
 finally:bm.free()
def source_bvh(o):
 mesh=o.data;mesh.calc_loop_triangles()
 vs=[tuple(o.matrix_world@v.co) for v in mesh.vertices]
 tris=[tuple(t.vertices) for t in mesh.loop_triangles]
 return BVHTree.FromPolygons(vs,tris,all_triangles=True)
def proximity(mesh,mat,source):
 ds=[]
 for v in mesh.vertices:
  q=source.find_nearest(mat@v.co)
  assert q is not None
  ds.append(float((mat@v.co-q[0]).length))
 ds.sort()
 return {"min":ds[0],"median":ds[len(ds)//2],
         "p95":ds[int(len(ds)*.95)],"max":ds[-1],"count":len(ds)}
try:
 assert bpy.app.version_string.startswith("5.2.2")
 assert INPUT.is_file()
 assert sha(INPUT)==INPUT_SHA,"V076 original source SHA mismatched"
 bpy.ops.wm.open_mainfile(filepath=str(INPUT.resolve()))
 originals={o.name:local_hash(o) for o in bpy.data.objects if o.type in {"MESH","CURVE"}}
 original_names=sorted(o.name for o in bpy.data.objects)
 refs={img.name:tuple(img.size) for img in bpy.data.images if img.packed_file}
 assert len(refs)>=3
 ear=bpy.data.objects[EAR]
 assert len(ear.data.vertices)==200 and ear.type=="MESH"
 assert bpy.data.objects["V076_NEAR_UPPER_EAR_ROLL"].type=="CURVE"
 assert bpy.data.objects["V076_FAR_UPPER_EAR_ROLL"].type=="CURVE"
 base=measure_mesh(ear.data,ear.matrix_world)
 assert base["boundary_edges"]==0 and base["nonmanifold_edges"]==0
 r["base_ear"]=base;r["source_objects"]=len(original_names)
 src_bvh=source_bvh(ear)
 collection=bpy.data.collections.new("V077_DIAGNOSTIC_MULTRES_COMPARE")
 bpy.context.scene.collection.children.link(collection)
 r["modes"]={}
 for mode in MODES:
  dup=ear.copy()
  dup.data=ear.data.copy()
  dup.name="V077_MULTRES_"+mode+"_DIAGNOSTIC_ONLY"
  collection.objects.link(dup)
  bpy.ops.object.select_all(action="DESELECT")
  dup.select_set(True);bpy.context.view_layer.objects.active=dup
  modifier=dup.modifiers.new("V077_NATIVE_"+mode,"MULTIRES")
  actual_ops=[]
  for step in range(LEVELS):
   assert bpy.ops.object.multires_subdivide.poll(),"Multires operator unavailable"
   op=bpy.ops.object.multires_subdivide(modifier=modifier.name,mode=mode)
   assert "FINISHED" in op,op
   actual_ops.append("FINISHED")
  assert modifier.total_levels==LEVELS,(mode,modifier.total_levels)
  modifier.levels=LEVELS
  modifier.sculpt_levels=LEVELS
  modifier.render_levels=LEVELS
  bpy.context.view_layer.update()
  depsgraph=bpy.context.evaluated_depsgraph_get()
  evalob=dup.evaluated_get(depsgraph)
  evalmesh=evalob.to_mesh(preserve_all_data_layers=False,depsgraph=depsgraph)
  try:
   metric=measure_mesh(evalmesh,evalob.matrix_world)
   near=proximity(evalmesh,evalob.matrix_world,src_bvh)
  finally:evalob.to_mesh_clear()
  assert metric["verts"]>base["verts"]
  assert metric["verts"]<CAP
  assert metric["boundary_edges"]==0 and metric["nonmanifold_edges"]==0
  vol_pct=(metric["signed_volume_abs"]/base["signed_volume_abs"]-1)*100
  bb_drifts=[max(abs(metric["world_bbox"][i][q]-base["world_bbox"][i][q]) for q in (0,1)) for i in range(3)]
  r["modes"][mode]={"operator":"bpy.ops.object.multires_subdivide",
   "native_operators":actual_ops,"total_levels":modifier.total_levels,
   "base_ear_original_unchanged":True,"evaluated":metric,
   "evaluated_surface_distance_to_base":near,
   "native_volume_change_percent":vol_pct,
   "world_bbox_drift":bb_drifts,"status":"MEASURED_NOT_ART_APPROVED"}
  dup.hide_render=True;dup.hide_set(True)
 assert all(local_hash(bpy.data.objects[n])==h for n,h in originals.items()),"V076 original resource was mutated"
 assert refs=={img.name:tuple(img.size) for img in bpy.data.images if img.packed_file}
 assert sorted(n for n in bpy.data.objects if not n.startswith("V077_"))==original_names
 r["all_original_meshes_curves_unchanged"]=True
 r["three_packed_cc0_references_unchanged"]=True
 # This proof is feasibility, not an approved ear-sculpting change.
 p=(OUT/"V077_NATIVE_MULTRES_A_B_READINESS.blend").resolve()
 bpy.ops.wm.save_as_mainfile(filepath=str(p))
 r["output_file_sha256"]=sha(p)
 r["status"]="NATIVE_MULTRES_TOPOLOGY_AB_TECH_PASS; NO_FOLD_CREATED; ART_HOLD"
except BaseException as e:
 r["status"]="FAIL_OR_METHOD_HOLD";r["error"]=repr(e)
finally:
 (OUT/"V077_REAL_NATIVE_MULTRES_READINESS_RECEIPT.json").write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n")
 print("V077_MULTRES_A_B",json.dumps({k:r.get(k) for k in ("status","error","base_ear","modes","output_file_sha256")},ensure_ascii=False)[:16000],flush=True)
if r["status"].startswith("FAIL"):sys.exit(77)
