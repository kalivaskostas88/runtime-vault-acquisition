# SPDX-License-Identifier: GPL-2.0-or-later
"""V076 source-locked professional CURVE-guided elephant ear upper-rim study.

Grounding:
* Julien Kaspar / Blender Studio: primary masses & silhouette before small detail.
* Blender Secrets / Jan van den Hemel, Easy Ear Sculpting Tip (2026): CURVE
  modeling as controllable ear structure (original lesson is HUMAN ear; its
  anatomy IS NOT copied); public written explanation in 80.lv Feb 26 2026.
* Elephant actual upper rolled rim documented in observational photos/research.
Only OUR original elephant contour/fold design parameters, NOT teacher numbers.
Truth: 2 independent original Blender CURVE objects over existing real V075 ear
surfaces, NO sculpt brush, NO mesh subdivision, NO new rig, NO finished art claim.
Original V075 remains untouched; one discrete visual fold candidate.
"""
import bpy, sys, json, math, struct, hashlib, pathlib
from mathutils import Vector
from mathutils.bvhtree import BVHTree
OUT=pathlib.Path("v076_curve_ear_rim");OUT.mkdir(exist_ok=True)
SOURCE=pathlib.Path("v075_ear_grab/V075_REAL_GRAB_EAR_CONTOUR_CANDIDATE.blend")
SOURCE_SHA="741b6b912216b48fa7fe6edacaa96a3b630b08a31277412b3d1bee66d952de4c"
NEAR="06_EAR_NEAR"
FAR="06_EAR_FAR"
TOP_FRACTIONS=(.11,.22,.33,.44,.55,.66,.77,.88)
Z_BELOW_LOCAL_TOP=0.145
WORLD_OFFSET=0.023
BEVEL=0.027
TAPER=(.26,.65,.95,1.00,1.00,.95,.65,.26)
VIEW_POS={"SIDE":(0,-9,3),"FACE":(-9,0,3),
          "THREE_QUARTER":(-7,-8,5),"TOP":(0,-0.3,11)}
TARGET=Vector((-.25,0,1.89))
rec={"schema":"V076_SOURCE_LOCKED_ORIGINAL_NATIVE_CURVE_EAR_RIM",
 "teacher_source":"Jan van den Hemel/Blender Secrets: curve-controlled human ear tutorial, https://www.youtube.com/watch?v=-ij6rXb15yA, public descriptive text 80.lv",
 "scope_transfer":"ONLY CURVE control mechanics, NO HUMAN EAR anatomy copied",
 "animal_shape_source":"elephant upper rolled rim/fold observational photo, original generic-stylized artistic extrapolation",
 "full_original_teacher_video_watched":False,"authored_art":"UNAPPROVED_CANDIDATE",
 "start_source_sha":SOURCE_SHA,"blender_version":"5.2.2",
 "frozen_parameters":{"top_path_fractions":TOP_FRACTIONS,
    "z_below_mesh_top":Z_BELOW_LOCAL_TOP,"world_normal_offset":WORLD_OFFSET,
    "curve_bevel_depth":BEVEL,"bezier_control_count":len(TOP_FRACTIONS),
    "radius_taper":TAPER,"allowed_nearest_surface_max":0.055,
    "allowed_contact_ends_max":0.055},
 "status":"INIT","art_approved":False,"source_original_preserved":False}
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def fingerprint(o):
 b=hashlib.sha256()
 b.update(o.name.encode());b.update(str([round(float(x),8) for row in o.matrix_world for x in row]).encode())
 if o.type=="MESH":
  b.update(str((len(o.data.vertices),len(o.data.polygons))).encode())
  for v in o.data.vertices:b.update(struct.pack("<ddd",*map(float,v.co)))
 elif o.type=="CURVE":
  b.update(str((o.data.bevel_depth,[(tuple(p.co),float(p.radius)) for s in o.data.splines for p in s.bezier_points])).encode())
 return b.hexdigest()
def world_bvh(o):
 m=o.data;m.calc_loop_triangles()
 coords=[tuple(o.matrix_world@v.co) for v in m.vertices]
 faces=[tuple(int(i) for i in t.vertices) for t in m.loop_triangles]
 return BVHTree.FromPolygons(coords,faces,all_triangles=True)
def bbox(o):
 vs=[o.matrix_world@Vector(x) for x in o.bound_box]
 return [[min(v[i] for v in vs),max(v[i] for v in vs)] for i in range(3)]
def render(tag):
 sc=bpy.context.scene;sc.render.engine="BLENDER_WORKBENCH"
 sc.render.resolution_x=650;sc.render.resolution_y=650;sc.render.resolution_percentage=100
 sc.render.image_settings.file_format="PNG"
 assert sc.camera
 hashes={}
 for lab,location in VIEW_POS.items():
  sc.camera.location=Vector(location)
  sc.camera.rotation_euler=(TARGET-sc.camera.location).to_track_quat("-Z","Y").to_euler()
  p=(OUT/(tag+"_"+lab+".png")).resolve()
  sc.render.filepath=str(p);bpy.ops.render.render(write_still=True)
  assert p.stat().st_size>1000
  hashes[p.name]=sha(p)
 return hashes
def sample_upper_front_surface(o):
 # Reuse the ORIGINAL ear mesh; do not invent an unrelated new polygon shape.
 # Compute each guide point at a Y slice, just below the upper actual mesh
 # silhouette, and ray cast from the external front -X side into the mesh.
 bboxw=bbox(o); miny,maxy=bboxw[1]
 points=[];records=[]
 verts=[o.matrix_world@v.co for v in o.data.vertices]
 tree=world_bvh(o)
 mat_inv=o.matrix_world.inverted()
 world_dir=Vector((1.,0.,0.))
 local_dir=(mat_inv.to_3x3()@world_dir).normalized()
 for fraction in TOP_FRACTIONS:
  y=maxy-(maxy-miny)*fraction
  pool=[v for v in verts if abs(v.y-y)<.125]
  assert len(pool)>=3,("Not enough real top guide samples",fraction,len(pool))
  topz=max(v.z for v in pool)
  target_z=topz-Z_BELOW_LOCAL_TOP
  world_origin=Vector((-6.,y,target_z))
  local_origin=mat_inv@world_origin
  hit,normal,face,distance=o.ray_cast(local_origin,local_dir,distance=15.)
  assert face>=0,("Guide ray missed original ear surface",fraction,target_z)
  hit_world=o.matrix_world@hit
  n=(o.matrix_world.to_3x3().inverted().transposed()@normal).normalized()
  assert n.x<-.25,("Guide not projected on the true front-facing ear surface",fraction,n[:])
  guided=hit_world+n*WORLD_OFFSET
  nearest=tree.find_nearest(guided)
  assert nearest is not None
  actual_distance=(guided-nearest[0]).length
  assert actual_distance<.055,("Guide is detached from original ear surface",fraction,actual_distance)
  points.append(guided)
  records.append({"fraction":fraction,"target_y":y,"sampled_upper_z":topz,
   "raycast_face_id":int(face),"point":[float(q) for q in guided],
   "actual_nearest_mesh_distance":float(actual_distance),
   "front_normal_x":float(n.x)})
 return points,records
def add_native_curve(name,pts):
 data=bpy.data.curves.new(name+"_NATIVE_DATA","CURVE")
 data.dimensions="3D";data.resolution_u=24
 data.bevel_depth=BEVEL;data.bevel_resolution=3
 spline=data.splines.new("BEZIER")
 spline.bezier_points.add(len(pts)-1)
 for i,(bp,p) in enumerate(zip(spline.bezier_points,pts)):
  bp.co=p
  bp.handle_left_type="AUTO";bp.handle_right_type="AUTO"
  bp.radius=TAPER[i]
 ob=bpy.data.objects.new(name,data)
 bpy.context.scene.collection.objects.link(ob)
 ob["stage"]="V076_NARROW_NATIVE_CURVE_FOLD_ART_HOLD"
 ob["teacher_scope"]="Original curve control method adapted to generic elephant, not human ear geometry"
 ob["source_v075_sha256"]=SOURCE_SHA
 return ob
try:
 assert bpy.app.version_string.startswith("5.2.2")
 assert SOURCE.is_file() and sha(SOURCE)==SOURCE_SHA,"Input V075 original .blend SHA mismatch"
 bpy.ops.wm.open_mainfile(filepath=str(SOURCE.resolve()))
 bpy.context.view_layer.update()
 objects=bpy.data.objects
 near=objects[NEAR];far=objects[FAR]
 assert near.get("stage")=="V075_REAL_GRAB_EAR_CONTOUR_CANDIDATE_ART_HOLD"
 assert far.get("stage")=="V075_REAL_GRAB_EAR_CONTOUR_CANDIDATE_ART_HOLD"
 assert len(near.data.vertices)==len(far.data.vertices)==200
 originally=sorted(o.name for o in objects)
 baseline={o.name:fingerprint(o) for o in objects if o.type in {"MESH","CURVE"}}
 refs={im.name:tuple(im.size) for im in bpy.data.images if im.packed_file}
 assert len(refs)>=3
 rec["source_original_object_count"]=len(originally)
 rec["source_ear_mesh_original_sha"]={x.name:fingerprint(x) for x in (near,far)}
 rec["before_renders"]=render("BEFORE")
 nearpts,proof=sample_upper_front_surface(near)
 farpts=[Vector((p.x,-p.y,p.z)) for p in nearpts]
 # Confirm the mirrored line also fits the actual original FAR mesh surface.
 farbvh=world_bvh(far)
 far_fit=[float((p-farbvh.find_nearest(p)[0]).length) for p in farpts]
 assert all(d<.055 for d in far_fit),"Mirrored fold line disconnected from opposite ear"
 names=["V076_NEAR_UPPER_EAR_ROLL","V076_FAR_UPPER_EAR_ROLL"]
 made=[add_native_curve(names[0],nearpts),add_native_curve(names[1],farpts)]
 bpy.context.view_layer.update()
 assert sorted(o.name for o in objects)==sorted(originally+names),"Wrong original object count"
 assert all(fingerprint(objects[n])==h for n,h in baseline.items()),"Original art geometry mutated"
 assert refs=={i.name:tuple(i.size) for i in bpy.data.images if i.packed_file}
 mirror_delta=max((Vector((a.x,-a.y,a.z))-b).length for a,b in zip(nearpts,farpts))
 assert mirror_delta<1e-7
 rec["fold_original_sampled_guide"]=proof
 rec["mirrored_opposite_original_mesh_surface_distances"]=far_fit
 rec["curve_objects"]={x.name:{"type":x.type,"bevel_depth":x.data.bevel_depth,
  "control_points":len(x.data.splines[0].bezier_points)} for x in made}
 rec["max_full_xyz_world_curve_control_mirror_error"]=mirror_delta
 rec["ear_body_head_unchanged"]=True;rec["three_original_cc0_refs_unchanged"]=True
 rec["after_renders"]=render("AFTER")
 p=(OUT/"V076_ACTUAL_NATIVE_CURVE_GUIDED_EAR_RIM_CANDIDATE.blend").resolve()
 bpy.ops.wm.save_as_mainfile(filepath=str(p))
 rec["saved_blend_sha256"]=sha(p)
 rec["status"]="NATIVE_TWO_CURVE_EAR_RIM_TECH_PASS; FOUR_VIEW_SELF_ART_PENDING; ART_HOLD"
except BaseException as e:
 rec["status"]="FAILED_OR_SOURCE_HOLD";rec["error"]=repr(e)
finally:
 (OUT/"V076_REAL_CURVE_RIM_SOURCE_AND_TECH_RECEIPT.json").write_text(json.dumps(rec,ensure_ascii=False,indent=2)+"\n")
 print("V076_REAL_EAR_CURVE",json.dumps({k:rec.get(k) for k in ("status","error","curve_objects","max_full_xyz_world_curve_control_mirror_error","saved_blend_sha256")},ensure_ascii=False),flush=True)
if rec["status"].startswith("FAILED"):sys.exit(76)
