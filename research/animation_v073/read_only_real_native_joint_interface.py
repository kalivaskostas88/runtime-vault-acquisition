#!/usr/bin/env python3
"""V073 read-only professional art interface diagnostic on exact real V072 Blender .blend.
Source-first: Kaspar official Blender Studio 'Fine Control', 'Detailed Sculpting',
'Smoothing & Stylising Body' written lessons: don't join head/ears/legs blindly.
Mechanics of intersection ≠ artist anatomy. No mesh mutations and no art PASS.
"""
import bpy,math,json,hashlib,sys,pathlib,statistics,struct
from mathutils import Vector
from mathutils.bvhtree import BVHTree
INPUT=pathlib.Path("v072_targeted_smooth/V072_SMALL_SMOOTH_CANDIDATE.blend")
EXPECT_SHA="e551ec647ff1714b341567f6512ecf92344f229f672ae04ef37bab590cb5591d"
OUT=pathlib.Path("v073_joint_diagnostic");OUT.mkdir(exist_ok=True)
PARTS=["04_HEAD","05_MUZZLE_ROOT","06_EAR_NEAR","06_EAR_FAR",
  "07_LEG_FRONT_NEAR","07_LEG_FRONT_FAR","07_LEG_REAR_NEAR","07_LEG_REAR_FAR"]
TARGET="01_BARREL_BODY"
r={"schema":"V073_REAL_BLENDER_RESEARCH_ONLY_ADJACENT_PART_INTERFACES",
   "input_file_sha256_expected":EXPECT_SHA,"source_required":"V072 exact original first Smooth candidate",
   "version_required":"Blender 5.2.2","native_modify":False,
   "art_approved":False,"source_full_av_studied":False,
   "method":"world-space native triangle BVH overlaps + nearest-surface vertex distances, read-only",
   "limitations":"BVH triangle intersections do not certify anatomical transitions; sampled nearest distances aren't exact global Hausdorff; touching/contained meshes may have no triangle intersections",
   "status":"INIT"}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def mesh_hash(o):
 h=hashlib.sha256()
 for v in o.data.vertices:h.update(struct.pack("<ddd",*map(float,v.co)))
 return h.hexdigest()
def triangles(o):
 me=o.data
 me.calc_loop_triangles()
 verts=[tuple(o.matrix_world@v.co) for v in me.vertices]
 tris=[tuple(int(j) for j in face.vertices) for face in me.loop_triangles]
 assert verts and tris,(o.name,len(verts),len(tris))
 return verts,tris,BVHTree.FromPolygons(verts,tris,all_triangles=True)
def bbox_world(o):
 pts=[o.matrix_world@Vector(v) for v in o.bound_box]
 return [[min(v[i] for v in pts),max(v[i] for v in pts)] for i in range(3)]
def bbox_intersection(a,b):
 return [max(0,min(a[i][1],b[i][1])-max(a[i][0],b[i][0])) for i in range(3)]
def sample_nearest(verts,tree):
 ds=[]
 for p in verts:
  hit=tree.find_nearest(Vector(p))
  if hit is None:continue
  ds.append(float((Vector(p)-hit[0]).length))
 assert len(ds)==len(verts)
 return {"min":min(ds),"median":statistics.median(ds),"p90":sorted(ds)[int(.9*(len(ds)-1))],
         "max":max(ds),"fraction_under_voxel_006":sum(v<.06 for v in ds)/len(ds),
         "fraction_under_012":sum(v<.12 for v in ds)/len(ds),
         "sample_count":len(ds)}
try:
 assert bpy.app.version_string.startswith("5.2.2")
 assert INPUT.is_file()
 actual=sha(INPUT);r["actual_source_sha256"]=actual
 assert actual==EXPECT_SHA,("immutable V072 source mismatch",actual)
 bpy.ops.wm.open_mainfile(filepath=str(INPUT.resolve()))
 target=bpy.data.objects[TARGET]
 assert target.type=="MESH" and target.get("stage")=="V072_SMALL_NATIVE_SMOOTH_CANDIDATE_ART_HOLD"
 originals={o.name:mesh_hash(o) for o in bpy.data.objects if o.type=="MESH"}
 original_count=len(bpy.data.objects)
 cc0={im.name:tuple(im.size) for im in bpy.data.images if im.packed_file}
 assert len(cc0)>=3
 tgtvs,tgttris,tgtbvh=triangles(target)
 tgtbox=bbox_world(target)
 r["torso"]={"name":TARGET,"vertices":len(tgtvs),"triangles":len(tgttris),
     "bbox":tgtbox,"position_sha256":originals[TARGET]}
 r["interfaces"]={}
 for name in PARTS:
  ob=bpy.data.objects[name]
  assert ob.type=="MESH",name
  vs,tris,bvh=triangles(ob)
  hits=tgtbvh.overlap(bvh)
  intersection=bbox_intersection(tgtbox,bbox_world(ob))
  proximity=sample_nearest(vs,tgtbvh)
  r["interfaces"][name]={"vertex_count":len(vs),"tri_count":len(tris),
    "triangle_overlap_pairs":len(hits),"world_bbox_intersection_widths":intersection,
    "has_bbox_overlap_on_all_axes":all(d>0 for d in intersection),
    "sample_vertex_to_torso_surface_distance":proximity,
    "native_unchanged_mesh_sha256":originals[name],
    "art_status":"SEPARATE_PROXY; INTERFACE_SHAPE_NOT_ART_APPROVED"}
 r["no_other_mesh_mutation"]=all(mesh_hash(bpy.data.objects[n])==h for n,h in originals.items())
 r["object_count_unchanged"]=original_count==len(bpy.data.objects)
 r["original_packed_refs_unchanged"]=cc0=={im.name:tuple(im.size) for im in bpy.data.images if im.packed_file}
 assert r["no_other_mesh_mutation"] and r["object_count_unchanged"] and r["original_packed_refs_unchanged"]
 r["status"]="NATIVE_READONLY_INTERFACE_DIAGNOSTIC_PASS; ART_HOLD; NOT_A_FUSION"
except Exception as e:
 r["status"]="FAILED_OR_ACCESS_HOLD";r["error"]=repr(e)
finally:
 (OUT/"V073_REAL_ORIGINAL_INTERFACE_RECEIPT.json").write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n")
 print("V073_REAL_INTERFACE",json.dumps({k:r.get(k) for k in ("status","error","torso","no_other_mesh_mutation")},ensure_ascii=False)[:3000],flush=True)
 print("V073_PARTS",json.dumps({n:{"overlap":x["triangle_overlap_pairs"],"near06":x["sample_vertex_to_torso_surface_distance"]["fraction_under_voxel_006"]} for n,x in r.get("interfaces",{}).items()},ensure_ascii=False),flush=True)
if r["status"].startswith("FAILED"):sys.exit(73)
