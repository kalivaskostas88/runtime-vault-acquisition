# SPDX-License-Identifier: GPL-2.0-or-later
"""V074: professional anatomy-guided ORIGINAL low-poly elephant ear fan blockout.
Source-lock V072 .blend exactly; V073 head+ear BVH diagnosis; Blender Studio
Julien Kaspar 'Sculpting Multiple Objects' big-mass before detail method,
Smithsonian/San Diego Zoo ear flap vs species distinctions.
These numbers are OUR frozen stylized candidate, not Kaspar's or zoo metrics.
Actual Blender Edit Mode transform operators (not pretending brush sculpt).
Only two original ear proxy meshes changed, no remesh, no head/legs edits.
TECH proof differs from ART, which must stay HOLD pending independent review.
"""
import bpy,bmesh,json,hashlib,struct,sys,pathlib,math
from mathutils import Vector
from mathutils.bvhtree import BVHTree
OUT=pathlib.Path("v074_ear_art_blockout");OUT.mkdir(exist_ok=True)
SOURCE=pathlib.Path("v072_targeted_smooth/V072_SMALL_SMOOTH_CANDIDATE.blend")
SOURCE_SHA="e551ec647ff1714b341567f6512ecf92344f229f672ae04ef37bab590cb5591d"
EAR_NAMES=["06_EAR_NEAR","06_EAR_FAR"]
TARGET_SCALE=(0.48,1.23,1.06)
OUTWARD_SHIFT=0.13
DEFAULT_CAMERA_POS={"SIDE":(0,-9,3.0),"FACE":(-9,0,3.0),"THREE_QUARTER":(-7,-8,5.0),"TOP":(0,-0.3,11)}
CENTER=Vector((-.25,0,1.89))
r={"schema":"V074_PROFESSIONAL_SOURCE_BASED_ORIGINAL_NATIVE_ART_DIRECTED_EAR_PROPORTION",
 "source_blend_sha256_expected":SOURCE_SHA,"blender_version_required":"5.2.2",
 "source_anatomy":"elephant ear lamina is broad and relatively flat; elephant species differ; designed original stylized candidate, species not classified",
 "teacher_method":"Julien Kaspar Blender Studio: low-poly separate primary masses, refine silhouette before detailed work",
 "actual_media_full_av":"NO","source_professional_written":"YES","original_cc0_reference":"Poly Haven / Greg Zaal preserved",
 "predeclared_candidate":{"ear_local_mesh_scale_x_y_z":TARGET_SCALE,"ear_outward_location_delta_y_abs":OUTWARD_SHIFT,
 "tech_min_ear_width_ratio_front":1.1,"tech_max_outer_bbox_width_ratio_front":1.55,
 "max_symmetric_mesh_hash_difference":"ZERO","head_ear_interface_required":True},
 "state":"INIT","art_approved":False,"independent_art_reviewer":False,
 "no_rigging_claim":True,"no_sculpt_brush_claim":True}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def fingerprint(o):
 if o.type=="MESH":
  b=bytearray()
  b.extend(str([[round(float(v),9) for v in row] for row in o.matrix_world]).encode())
  for v in o.data.vertices:b.extend(struct.pack("<ddd",*map(float,v.co)))
  return hashlib.sha256(b).hexdigest()
 if o.type=="CURVE":
  a=[o.name,tuple(o.matrix_world),[(tuple(p.co),p.radius) for s in o.data.splines for p in s.bezier_points]]
  return hashlib.sha256(repr(a).encode()).hexdigest()
 return None
def coords_hash(o):
 a=b"".join(struct.pack("<ddd",*map(float,v.co)) for v in o.data.vertices)
 return hashlib.sha256(a).hexdigest()
def box(o):
 vs=[o.matrix_world@Vector(p) for p in o.bound_box]
 return [[min(v[i] for v in vs),max(v[i] for v in vs)] for i in range(3)]
def triangles(o):
 o.data.calc_loop_triangles()
 vs=[tuple(o.matrix_world@v.co) for v in o.data.vertices]
 ts=[tuple(int(i) for i in t.vertices) for t in o.data.loop_triangles]
 return BVHTree.FromPolygons(vs,ts,all_triangles=True)
def images(label):
 sc=bpy.context.scene
 sc.render.engine="BLENDER_WORKBENCH"
 sc.render.resolution_x=650;sc.render.resolution_y=650;sc.render.resolution_percentage=100
 sc.render.image_settings.file_format="PNG"
 cam=sc.camera;assert cam is not None
 result={}
 for name,pos in DEFAULT_CAMERA_POS.items():
  cam.location=Vector(pos)
  cam.rotation_euler=(CENTER-cam.location).to_track_quat("-Z","Y").to_euler()
  p=(OUT/(label+"_"+name+".png")).resolve()
  sc.render.filepath=str(p);bpy.ops.render.render(write_still=True)
  assert p.stat().st_size>2000
  result[p.name]=sha(p)
 return result
try:
 assert bpy.app.version_string.startswith("5.2.2")
 assert sha(SOURCE)==SOURCE_SHA,"Wrong verified native V072 source SHA"
 bpy.ops.wm.open_mainfile(filepath=str(SOURCE.resolve()))
 objects=bpy.data.objects
 assert objects["01_BARREL_BODY"].get("stage")=="V072_SMALL_NATIVE_SMOOTH_CANDIDATE_ART_HOLD"
 ears=[objects[n] for n in EAR_NAMES];head=objects["04_HEAD"]
 assert all(o.type=="MESH" and o.get("stage")=="BLOCKOUT_NOT_FINAL" for o in ears)
 assert all(len(o.modifiers)==0 and all(abs(x-1)<1e-6 for x in o.scale) for o in ears)
 original={o.name:fingerprint(o) for o in objects if (o.type in ("MESH","CURVE") and o.name not in EAR_NAMES)}
 source_ear_meshes=[coords_hash(o) for o in ears]
 assert len(set(source_ear_meshes))==1,"Source left/right ears are not mirror-compatible original primitives"
 packed={i.name:tuple(i.size) for i in bpy.data.images if i.packed_file}
 assert len(packed)>=3,"Unpacked CC0 source refs"
 original_objects=sorted(o.name for o in objects)
 orig_bb={o.name:box(o) for o in ears}
 orig_loc={o.name:list(o.location) for o in ears}
 r["source_ear_mesh_sha256"]=dict(zip(EAR_NAMES,source_ear_meshes))
 r["before_world_bbox"]=orig_bb
 r["before_renders"]=images("BEFORE")
 # Only high-level sculpt art-directing of already teacher-blocked ellipsoids.
 # This is Blender's native Edit Mode mesh resize—not a native Grab/Smooth brush.
 for o in ears:
  bpy.ops.object.mode_set(mode="OBJECT") if bpy.context.object and bpy.context.object.mode!="OBJECT" else None
  bpy.ops.object.select_all(action="DESELECT")
  o.select_set(True);bpy.context.view_layer.objects.active=o
  bpy.ops.object.mode_set(mode="EDIT")
  bpy.ops.mesh.select_all(action="SELECT")
  op=bpy.ops.transform.resize(value=TARGET_SCALE,orient_type="LOCAL")
  assert "FINISHED" in op,op
  bpy.ops.object.mode_set(mode="OBJECT")
  sign=-1 if "NEAR" in o.name else 1
  o.location.y+=sign*OUTWARD_SHIFT
  assert all(abs(s-1)<1e-6 for s in o.scale)
  o["stage"]="V074_EAR_FAN_SHAPE_BLOCKOUT_ART_HOLD"
  o["source"]="V072_TRUE_SAVED_SOURCE"
  o["species"]="UNSPECIFIED_STYLIZED_ELEPHANT"
 # Source-proven symmetry repair: Blender Edit Mode may produce different last-bit
 # floating coordinates for equivalent independently transformed left/right assets.
 # Preserve the same frozen design scale, don't relax the symmetry gate:
 # clone the already transformed NEAR mesh datablock for the opposite FAR ear.
 # Both original ears had identical LOCAL source mesh SHA and their WORLD
 # locations are opposite in Y, hence the same local geometry preserves symmetry.
 local_before_symmetry={o.name:coords_hash(o) for o in ears}
 r["symmetry_repair_provenance"]={"initial_transformed_local_sha256":local_before_symmetry,
    "first_run_failed":"44474315835",
    "cause":"BOTH native Edit-Mode resizes returned FINISHED, but local-vertex byte hashes differed",
    "repair":"FAR ear receives deep copy of transformed NEAR native ear mesh datablock; frozen scale/position same"}
 if len(set(local_before_symmetry.values()))!=1:
  ears[1].data=ears[0].data.copy()
 assert ears[0].data!=ears[1].data,"Require separate mesh datablocks even after symmetry lock"
 final_bb={o.name:box(o) for o in ears}
 ear_mesh_sha={o.name:coords_hash(o) for o in ears}
 r["after_ear_mesh_sha256"]=ear_mesh_sha
 assert len(set(ear_mesh_sha.values()))==1,"Symmetric native mesh local coordinates mismatch"
 width_before=2*(abs(orig_loc["06_EAR_NEAR"][1])+.49)
 width_after=final_bb["06_EAR_FAR"][1][1]-final_bb["06_EAR_NEAR"][1][0]
 width_ratio=width_after/width_before
 r["frontal_ear_outer_width_ratio_world_proxy"]=width_ratio
 assert 1.1<width_ratio<1.55,"Candidate ear lateral extent outside predeclared width gate"
 # A conservative explicit anatomical articulation: preserve surface intersections
 # with the head in each ear to permit later sculpt/fusion; NO fusion now.
 headtree=triangles(head)
 crossings={o.name:len(headtree.overlap(triangles(o))) for o in ears}
 r["head_ear_triangle_crossings_after"]=crossings
 assert all(v>0 for v in crossings.values()),"Ear root lost existing head contact"
 r["head_ear_articulation"] = "TWO_SEPARATE_EAR_MESHES_STILL_CROSS_HEAD_SURFACE"
 assert sorted(o.name for o in objects)==original_objects
 r["no_unrelated_component_mutation"]=all(fingerprint(objects[name])==h for name,h in original.items())
 assert r["no_unrelated_component_mutation"],"Changed other Blender artistic component"
 r["cc0_packed_reference_metadata_unchanged"]=(packed=={i.name:tuple(i.size) for i in bpy.data.images if i.packed_file})
 assert r["cc0_packed_reference_metadata_unchanged"]
 r["after_world_bbox"]=final_bb
 r["after_renders"]=images("AFTER")
 save=(OUT/"V074_ORIGINAL_EAR_FAN_BLOCKOUT_CANDIDATE.blend").resolve()
 bpy.ops.wm.save_as_mainfile(filepath=str(save))
 r["saved_blend_sha256"]=sha(save)
 r["state"]="NATIVE_REAL_EDIT_MODE_FORM_BLOCKOUT_TECH_PASS; ART_HOLD; REPEAT_PENDING"
except BaseException as e:
 r["state"]="FAILED_OR_BLOCKED"
 r["error"]=repr(e)
finally:
 (OUT/"V074_EAR_FORM_AND_SOURCE_RECEIPT.json").write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n")
 print("V074_NATIVE_ART_FORM",json.dumps({x:r.get(x) for x in ("state","error","frontal_ear_outer_width_ratio_world_proxy","head_ear_triangle_crossings_after","no_unrelated_component_mutation")},ensure_ascii=False),flush=True)
if r["state"].startswith("FAILED"):sys.exit(74)
