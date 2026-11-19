# SPDX-License-Identifier: GPL-2.0-or-later
"""V078: source-locked real embedded (mesh-vertex) elephant ear upper fold.
Blender native Multires SIMPLE level2 evaluated geometry (V077), plus owned
original, bounded curve-guided mesh displacement (not native Crease brush).
No new visible tube. Professional method from Blender Studio Julien Kaspar:
source-observed folds rather than invented details; enough topology before detail.
Photographic/scientific ear top-fold: observational reference only, no copied mesh.
All artist parameters are originally designed for this stylized exercise.
This is TECH candidate only, never autonomous independent ART approval.
"""
import bpy,bmesh,hashlib,struct,math,json,pathlib,sys
from mathutils import Vector
OUT=pathlib.Path("v078_integrated_ear_fold");OUT.mkdir(exist_ok=True)
INPUT=pathlib.Path("v077_topology_preflight/V077_NATIVE_MULTRES_A_B_READINESS.blend")
INPUT_SHA="33d2d9a839df0b8b9e203244670f292d329324b04aee5fd34ab33999a4a8e7a8"
NEAR="06_EAR_NEAR";FAR="06_EAR_FAR";GUIDE="V076_NEAR_UPPER_EAR_ROLL"
PARAM={"native_source_mode":"MULTIRES_SIMPLE","levels":2,"ridge_amplitude":0.052,
 "trough_amplitude":0.034,"ridge_offset_signed":0.024,"trough_offset_signed":-0.094,
 "ridge_sigma":0.066,"trough_sigma":0.052,"min_vertices_moved":25,
 "max_vertices_moved":2600,"max_abs_volume_change_pct":3.0,
 "max_world_vertex_displacement":0.08,"root_mask_y_from":0.68,
 "root_mask_y_to":0.98,"root_max_world_displacement":0.008,
 "mirror_max_error":0.00001,"min_both_ridge_and_groove_vertices":8}
rec={"schema":"V078_REAL_INTEGRATED_ELEPHANT_EAR_FOLD_TECH_PROOF",
 "source":"V077 exact native Blender Multires A/B .blend","source_sha256_expected":INPUT_SHA,
 "professional":"Julien Kaspar Blender Studio Detailed Sculpting; Creating Facial Shapes: do not invent creases, design with reference",
 "anatomical_scope":"Elephant upper rolling fold observed in scientific imagery, no species lock and no copied artwork",
 "licensed_new_teacher_full_av_watched":False,"native_crease_brush_used":False,
 "native_multires_evaluated":True,"original_bounded_deformation_used":True,
 "parameters_frozen":PARAM,"art_approved":False,"independent_artist_review":False,
 "status":"INIT","tool_version":"Blender 5.2.2"}
CAMERAS={"FACE":(-9,0,3),"SIDE":(0,-9,3),"THREE_QUARTER":(-7,-8,5),"TOP":(0,-.3,11)}
TGT=Vector((-.25,0,1.89))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def fp(o):
 h=hashlib.sha256(o.type.encode())
 for row in o.matrix_world:
  for v in row:h.update(struct.pack("<d",float(v)))
 if o.type=="MESH":
  h.update(str((len(o.data.vertices),len(o.data.polygons))).encode())
  for v in o.data.vertices:h.update(struct.pack("<ddd",*map(float,v.co)))
 elif o.type=="CURVE":
  h.update(str(o.data.bevel_depth).encode())
  for spline in o.data.splines:
   for q in spline.bezier_points:
    h.update(struct.pack("<dddd",float(q.co.x),float(q.co.y),float(q.co.z),float(q.radius)))
 return h.hexdigest()
def measure(me,world):
 bm=bmesh.new()
 try:
  bm.from_mesh(me);bm.verts.ensure_lookup_table()
  volume=abs(bm.calc_volume(signed=True))*abs(world.determinant())
  boundary=sum(e.is_boundary for e in bm.edges)
  nonmanifold=sum(not e.is_manifold for e in bm.edges)
  pts=[world@v.co for v in bm.verts]
  bounds=[[min(float(p[i]) for p in pts),max(float(p[i]) for p in pts)] for i in range(3)]
  return {"verts":len(bm.verts),"faces":len(bm.faces),"boundary_edges":boundary,
   "nonmanifold_edges":nonmanifold,"volume":volume,"bbox_world":bounds}
 finally:bm.free()
def smoothstep(a,b,v):
 t=min(1.,max(0.,(v-a)/(b-a)))
 return t*t*(3-2*t)
def nearest_path(p,guide):
 # Signed perpendicular YZ distance to REAL V076 Bezier control path; no
 # invented world location. End segment yields normalized path parameter.
 best=None
 lengths=[(guide[i+1]-guide[i]).length for i in range(len(guide)-1)]
 total=sum(lengths)
 traveled=0.
 for i,dist in enumerate(lengths):
  a,b=guide[i],guide[i+1]
  va=Vector((p.y-a.y,p.z-a.z))
  seg=Vector((b.y-a.y,b.z-a.z))
  t=min(1.,max(0.,va.dot(seg)/seg.length_squared))
  clos=va-seg*t
  d=clos.length
  signed=(seg.x*clos.y-seg.y*clos.x)/seg.length
  u=(traveled+t*dist)/total
  if best is None or d<best[0]:best=(d,signed,u)
  traveled+=dist
 return best
def draw(tag):
 scene=bpy.context.scene; scene.render.engine="BLENDER_WORKBENCH"
 scene.render.resolution_x=720;scene.render.resolution_y=720
 scene.render.resolution_percentage=100;scene.render.image_settings.file_format="PNG"
 cam=scene.camera;assert cam
 original=(cam.data.type,cam.data.ortho_scale)
 result={}
 for n,pos in CAMERAS.items():
  cam.data.type="PERSP";cam.location=Vector(pos)
  cam.rotation_euler=(TGT-cam.location).to_track_quat("-Z","Y").to_euler()
  p=(OUT/(tag+"_"+n+".png")).resolve();scene.render.filepath=str(p)
  bpy.ops.render.render(write_still=True)
  assert p.stat().st_size>1200
  result[p.name]=sha(p)
 # Dedicated native ear detail frame. Same optics for before/after.
 cam.data.type="ORTHO";cam.data.ortho_scale=2.2
 close_target=Vector((-1.08,-1.05,2.86))
 cam.location=Vector((-6.,-5.0,4.2))
 cam.rotation_euler=(close_target-cam.location).to_track_quat("-Z","Y").to_euler()
 p=(OUT/(tag+"_EAR_DETAIL.png")).resolve();scene.render.filepath=str(p)
 bpy.ops.render.render(write_still=True)
 result[p.name]=sha(p)
 cam.data.type=original[0];cam.data.ortho_scale=original[1]
 return result
try:
 assert bpy.app.version_string.startswith("5.2.2")
 assert INPUT.is_file() and sha(INPUT)==INPUT_SHA,"V077 source exact SHA mismatch"
 bpy.ops.wm.open_mainfile(filepath=str(INPUT.resolve()))
 objects=bpy.data.objects
 originals={o.name:fp(o) for o in objects if o.type in {"MESH","CURVE"}}
 namebefore=sorted(o.name for o in objects)
 refs={im.name:tuple(im.size) for im in bpy.data.images if im.packed_file}
 assert len(refs)>=3
 near0=objects[NEAR];far0=objects[FAR];src=objects["V077_MULTRES_SIMPLE_DIAGNOSTIC_ONLY"]
 assert src.modifiers[0].type=="MULTIRES" and src.modifiers[0].total_levels==2
 assert len(near0.data.vertices)==len(far0.data.vertices)==200
 guideob=objects[GUIDE];guide=[guideob.matrix_world@p.co for p in guideob.data.splines[0].bezier_points]
 assert len(guide)==8
 rec["original_model_objects_before"]=len(namebefore)
 # Disable *render visibility* of V076 decorative tubes, never delete the guides.
 original_render_visibility={o.name:o.hide_render for o in objects}
 for n in ("V076_NEAR_UPPER_EAR_ROLL","V076_FAR_UPPER_EAR_ROLL"):
  objects[n].hide_render=True
 rec["before_renders"]=draw("BEFORE")
 # Real native Blender Multires evaluated mesh, materialized to owned MESH.
 bpy.context.view_layer.update()
 dep=bpy.context.evaluated_depsgraph_get()
 ev=src.evaluated_get(dep)
 hi=bpy.data.meshes.new_from_object(ev,preserve_all_data_layers=False,depsgraph=dep)
 assert len(hi.vertices)==3314 and len(hi.polygons)==3312
 group=bpy.data.collections.new("V078_ORIGINAL_EAR_SURFACE_FOLD_CANDIDATE")
 bpy.context.scene.collection.children.link(group)
 near=bpy.data.objects.new("V078_NEAR_REAL_SURFACE_FOLD",hi)
 group.objects.link(near);near.matrix_world=near0.matrix_world.copy()
 pre=measure(hi,near.matrix_world)
 assert pre["boundary_edges"]==0 and pre["nonmanifold_edges"]==0
 hi.calc_normals_split() if hasattr(hi,"calc_normals_split") else None
 start=[v.co.copy() for v in hi.vertices]
 world_orig=[near.matrix_world@p for p in start]
 ridge_count=trough_count=0
 ds=[];moved=0;rootmax=0.;maxabs=0.;max_ridge=0.;min_trough=0.
 inv=near.matrix_world.inverted().to_3x3()
 for i,v in enumerate(hi.vertices):
  p=world_orig[i]
  d,signed,u=nearest_path(p,guide)
  front=smoothstep(.20,.78,-(near.matrix_world.to_3x3()@v.normal).normalized().x)
  root=smoothstep(PARAM["root_mask_y_from"],PARAM["root_mask_y_to"],-p.y)
  endfade=smoothstep(.0,.16,u)*smoothstep(.0,.16,1-u)
  ridge=PARAM["ridge_amplitude"]*math.exp(-.5*((signed-PARAM["ridge_offset_signed"])/PARAM["ridge_sigma"])**2)
  valley=PARAM["trough_amplitude"]*math.exp(-.5*((signed-PARAM["trough_offset_signed"])/PARAM["trough_sigma"])**2)
  strength=(ridge-valley)*front*root*endfade
  # This is a real displacement of vertices on the surface, not a tube, a
  # virtual modifier, or a native sculpt Crease brush claim.
  normal=(near.matrix_world.to_3x3()@v.normal).normalized()
  offset_world=normal*strength
  if offset_world.length>1e-7:
   moved+=1; ds.append(strength)
   maxabs=max(maxabs,offset_world.length)
   if p.y>-.8:rootmax=max(rootmax,offset_world.length)
   if strength>.005:ridge_count+=1
   if strength<-.004:trough_count+=1
   max_ridge=max(max_ridge,strength)
   min_trough=min(min_trough,strength)
  v.co+=inv@offset_world
 hi.update()
 after=measure(hi,near.matrix_world)
 diff_pct=(after["volume"]/pre["volume"]-1)*100
 rec["mesh_deformation"]={"original_highres":pre,"after_highres":after,
  "moved_vertices":moved,"ridge_vertices":ridge_count,"trough_vertices":trough_count,
  "max_world_vertex_displacement":maxabs,"max_root_zone_displacement":rootmax,
  "max_ridge_signed_strength":max_ridge,"min_trough_signed_strength":min_trough,
  "volume_change_percent":diff_pct}
 assert PARAM["min_vertices_moved"]<moved<PARAM["max_vertices_moved"],("wrong focal footprint",moved)
 assert ridge_count>=8 and trough_count>=8,("Fold must have both positive ridge and negative groove",ridge_count,trough_count)
 assert 0.012<maxabs<PARAM["max_world_vertex_displacement"],("Effect too small/strong",maxabs)
 assert rootmax<PARAM["root_max_world_displacement"],("Ear root unsafe",rootmax)
 assert abs(diff_pct)<PARAM["max_abs_volume_change_pct"],("Volume gate",diff_pct)
 assert after["boundary_edges"]==0 and after["nonmanifold_edges"]==0
 assert after["verts"]==pre["verts"] and after["faces"]==pre["faces"]
 # Mirrored new REAL mesh BMesh; shared visual source curves only GUIDE.
 far_mesh=hi.copy()
 bm=bmesh.new()
 try:
  bm.from_mesh(far_mesh)
  for v in bm.verts:v.co.y=-v.co.y
  bmesh.ops.reverse_faces(bm,faces=list(bm.faces))
  bm.to_mesh(far_mesh)
 finally:bm.free()
 far_mesh.update()
 far=bpy.data.objects.new("V078_FAR_MIRRORED_REAL_SURFACE_FOLD",far_mesh)
 group.objects.link(far);far.matrix_world=far0.matrix_world.copy()
 bpy.context.view_layer.update()
 mirror=max((Vector(( (near.matrix_world@a.co).x,-(near.matrix_world@a.co).y,(near.matrix_world@a.co).z))-(far.matrix_world@b.co)).length
   for a,b in zip(near.data.vertices,far.data.vertices))
 rec["paired_world_xyz_max_mirror_error"]=mirror
 assert mirror<PARAM["mirror_max_error"],("World mirror failed",mirror)
 assert measure(far.data,far.matrix_world)["boundary_edges"]==0
 # Candidate uses ONLY new true surfaces as ears in render. The source ear
 # meshes and curve guides remain stored unaltered for full provenance.
 near0.hide_render=True;far0.hide_render=True
 src.hide_render=True
 near.hide_render=False;far.hide_render=False
 for o in (near,far):
  o["stage"]="V078_REAL_EAR_FOLD_MESH_CANDIDATE_ART_HOLD"
  o["derived_from_original_blend_sha256"]=INPUT_SHA
  o["deformation_method"]="V076_CURVE_GUIDED_OWNED_VERTEX_NORMAL_DEFORMATION_NOT_BRUSH"
 rec["after_renders"]=draw("AFTER")
 assert all(fp(objects[n])==h for n,h in originals.items()),"Original mesh/curve data or transforms changed"
 assert refs=={im.name:tuple(im.size) for im in bpy.data.images if im.packed_file}
 assert sorted(o.name for o in bpy.data.objects if not o.name.startswith("V078_"))==namebefore
 rec["original_mesh_and_curve_data_preserved"]=True
 rec["original_visibility_changes"]={n:{"before":a,"after":objects[n].hide_render}
   for n,a in original_render_visibility.items() if a!=objects[n].hide_render}
 rec["packed_cc0_refs_preserved"]=True
 outfile=(OUT/"V078_NATIVE_EMBEDDED_EAR_FOLD_CANDIDATE.blend").resolve()
 bpy.ops.wm.save_as_mainfile(filepath=str(outfile))
 rec["native_saved_blend_sha256"]=sha(outfile)
 rec["status"]="NATIVE_SOURCE_GUIDED_REAL_MESH_FOLD_TECH_PASS; SELF_VISUAL_REVIEW_PENDING; ART_HOLD"
except Exception as e:
 rec["status"]="FAIL_OR_SOURCE_HOLD";rec["error"]=repr(e)
finally:
 (OUT/"V078_REAL_SURFACE_FOLD_RECEIPT.json").write_text(json.dumps(rec,ensure_ascii=False,indent=2)+"\n")
 print("V078_REAL_INTEGRATED_FOLD",json.dumps({k:rec.get(k) for k in ("status","error","mesh_deformation","paired_world_xyz_max_mirror_error","native_saved_blend_sha256")},ensure_ascii=False)[:13000],flush=True)
if rec["status"].startswith("FAIL"):sys.exit(78)
