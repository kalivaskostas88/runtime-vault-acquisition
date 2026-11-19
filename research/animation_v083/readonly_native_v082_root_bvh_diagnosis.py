# SPDX-License-Identifier: GPL-2.0-or-later
"""V083 non-destructive geometry diagnosis of V082 ear attachment BEFORE joining.
Professional-first rule: shape separately, diagnose contacts, defer fusion until
anatomical shape and teacher sources justify it. This file edits NO mesh.
Uses Blender 5.2.2 native evaluated Subsurf+Solidify head/ear BVH.
"""
import bpy,bmesh,pathlib,hashlib,struct,json,sys,math,statistics
from mathutils import Vector
from mathutils.bvhtree import BVHTree
OUT=pathlib.Path("v083_root_readonly");OUT.mkdir(exist_ok=True)
SOURCE=pathlib.Path("v082_open_pinna_surface/V082_ORIGINAL_OPEN_SURFACE_EAR_PROOF.blend")
EXPECTED_SHA="73597cc408e68f767df1423e127553ef34004a5ddb672b4ee894ca7ec7073f74"
HEAD="04_HEAD"
EARS=["V082_NEAR_OPEN_QUAD_PINNA","V082_FAR_OPEN_QUAD_PINNA"]
r={"schema":"V083_ACTUAL_READONLY_ELEPHANT_EAR_ROOT_POSITION_AND_CONTACT",
 "source":"exact V082 original saved .blend first independent successful native GitHub run 44552915211",
 "source_sha256_expected":EXPECTED_SHA,"blender_required":"5.2.2",
 "method":"Professional source study first, native Blender world BVH and actual evaluated mesh; no object changes",
 "fusion_done":False,"sculpt_brush_used":False,"artist_approved":False,
 "root_contact_is_art_proof":False,"status":"INIT","ear_geometry":{}}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def object_fp(o):
 h=hashlib.sha256(o.type.encode())
 for row in o.matrix_world:
  for v in row:h.update(struct.pack("<d",float(v)))
 if o.type=="MESH":
  h.update(str((len(o.data.vertices),len(o.data.polygons))).encode())
  for v in o.data.vertices:h.update(struct.pack("<ddd",*map(float,v.co)))
 elif o.type=="CURVE":
  h.update(str(o.data.bevel_depth).encode())
  for spline in o.data.splines:
   for pt in spline.bezier_points:h.update(str((tuple(pt.co),pt.radius)).encode())
 return h.hexdigest()
def bvhtree(o,mesh=None):
 me=mesh if mesh is not None else o.data
 me.calc_loop_triangles()
 verts=[tuple(o.matrix_world@v.co) for v in me.vertices]
 faces=[tuple(int(i) for i in f.vertices) for f in me.loop_triangles]
 return BVHTree.FromPolygons(verts,faces,all_triangles=True)
def topology(me):
 bm=bmesh.new()
 try:
  bm.from_mesh(me)
  return {"verts":len(bm.verts),"faces":len(bm.faces),
   "nonmanifold_edges":sum(1 for e in bm.edges if not e.is_manifold),
   "open_boundary_edges":sum(1 for e in bm.edges if e.is_boundary)}
 finally:bm.free()
def box(o,me=None):
 me=me if me is not None else o.data
 vs=[o.matrix_world@v.co for v in me.vertices]
 return [[min(q[i] for q in vs),max(q[i] for q in vs)] for i in range(3)]
def describe(vals):
 vals=sorted(vals)
 return {"n":len(vals),"min":vals[0],"median":statistics.median(vals),
         "p90":vals[int(.9*(len(vals)-1))],"max":vals[-1],"mean":statistics.mean(vals)}
try:
 assert bpy.app.version_string.startswith("5.2.2")
 assert SOURCE.is_file() and sha(SOURCE)==EXPECTED_SHA
 bpy.ops.wm.open_mainfile(filepath=str(SOURCE.resolve()))
 original={o.name:object_fp(o) for o in bpy.data.objects if o.type in ("MESH","CURVE")}
 prior_names=sorted(o.name for o in bpy.data.objects)
 packed={i.name:tuple(i.size) for i in bpy.data.images if i.packed_file}
 assert len(packed)>=3
 head=bpy.data.objects[HEAD]
 assert head.type=="MESH"
 head_bvh=bvhtree(head)
 head_topo=topology(head.data)
 r["head"]={"mesh_topology":head_topo,"world_bbox":box(head)}
 dg=bpy.context.evaluated_depsgraph_get()
 for name in EARS:
  obj=bpy.data.objects[name]
  assert obj.type=="MESH" and obj.get("stage")=="V082_OPEN_QUAD_SUBSURF_SOLIDIFY_ART_HOLD"
  assert len(obj.modifiers)==2 and obj.modifiers[0].type=="SUBSURF" and obj.modifiers[1].type=="SOLIDIFY"
  assert len(obj.data.vertices)==70
  root=[];root_dist=[];root_nearest=[]
  for i in range(10):
   # Verified V082 own low-poly topology: row-major 10x7. Column0 root.
   v=obj.data.vertices[i*7]
   pt=obj.matrix_world@v.co
   nearest=head_bvh.find_nearest(pt)
   assert nearest
   gap=float((pt-nearest[0]).length)
   root.append([float(x) for x in pt])
   root_dist.append(gap)
   root_nearest.append([float(x) for x in nearest[0]])
  evaluated=obj.evaluated_get(dg)
  mesh=evaluated.to_mesh(preserve_all_data_layers=False,depsgraph=dg)
  try:
   assert len(mesh.vertices)==1850,("V082 evaluated ear mesh altered",len(mesh.vertices))
   topology_eval=topology(mesh)
   assert topology_eval["open_boundary_edges"]==0 and topology_eval["nonmanifold_edges"]==0
   evaluated_bvh=bvhtree(evaluated,mesh)
   triangle_crossing=len(head_bvh.overlap(evaluated_bvh))
   rootx=[p[0] for p in root]
   rooty=[p[1] for p in root]
   rootz=[p[2] for p in root]
   r["ear_geometry"][name]={
     "raw_surface":topology(obj.data),"evaluated_solid":topology_eval,
     "modifiers":[{"name":m.name,"type":m.type} for m in obj.modifiers],
     "raw_root_world_positions":root,
     "root_head_nearest_surface_world_positions":root_nearest,
     "raw_root_to_head_unsigned_surface_distance":describe(root_dist),
     "root_world_y_range":[min(rooty),max(rooty)],
     "root_world_z_range":[min(rootz),max(rootz)],
     "root_world_x_range":[min(rootx),max(rootx)],
     "evaluated_ear_head_triangle_overlap_pairs":triangle_crossing,
     "head_to_ear_nearest_proximity_not_fusion":True,
     "all_10_root_points_measured_in_world":True
   }
  finally:evaluated.to_mesh_clear()
 assert sorted(o.name for o in bpy.data.objects)==prior_names
 assert all(object_fp(bpy.data.objects[name])==h for name,h in original.items())
 assert packed=={i.name:tuple(i.size) for i in bpy.data.images if i.packed_file}
 r["all_original_geometry_and_transforms_sha_unchanged"]=True
 r["all_original_packed_photo_refs_unchanged"]=True
 r["decision"]="Before any Voxel Remesh, compare root gaps, triangulated contact, ear silhouette & teacher-specified risk of collapsing thin membrane."
 r["status"]="REAL_NATIVE_READONLY_ROOT_BVH_DIAGNOSTIC_PASS; NO_FUSION; ART_HOLD"
except Exception as e:
 r["status"]="FAIL_OR_SOURCE_HOLD";r["error"]=repr(e)
finally:
 (OUT/"V083_ACTUAL_EAR_ROOT_WORLD_BVH_RECEIPT.json").write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n")
 print("V083_ACTUAL_ROOT_BVH",json.dumps({k:r.get(k) for k in ("status","error","head","ear_geometry")},ensure_ascii=False)[:16000],flush=True)
if r["status"].startswith("FAIL"):sys.exit(83)
