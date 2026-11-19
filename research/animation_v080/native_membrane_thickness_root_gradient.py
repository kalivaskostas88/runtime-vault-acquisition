# SPDX-License-Identifier: GPL-2.0-or-later
"""V080 real African-savanna-elephant ear membrane thickness gradient study.
Exact original V079 .blend; create two new owned MESH objects, preserving the
broad primary silhouette and original V078 embedded fold. No fake native brush.
Professional/anatomical: SDZG African elephant outer ear lattice cartilage,
base muscles, thin distal flap; original stylized design, NOT measured anatomy.
Blender Studio Kaspar: large forms, preserve source, inspect from many angles.
Actual native Blender 5.2.2 vertex transformation with no mesh subdivision.
TECH mechanical test, independent artist ART_HOLD, NO fused head joint claim.
"""
import bpy,bmesh,json,pathlib,hashlib,struct,math,sys
from mathutils import Vector
from mathutils.bvhtree import BVHTree
OUT=pathlib.Path("v080_membrane_thickness");OUT.mkdir(exist_ok=True)
INPUT=pathlib.Path("v079_savanna_ear_silhouette/V079_ORIGINAL_SAVANNA_EAR_FLAP_NATIVE_CANDIDATE.blend")
SHA="b04204cd78581b7ebe95731d9ccc3f61ed454d35ebe3ed923d80b08b148a9aea"
NEAR="V079_NEAR_SAVANNA_FLAP_CANDIDATE";FAR="V079_FAR_MIRRORED_SAVANNA_FLAP_CANDIDATE";HEAD="04_HEAD"
# Frozen authored stylized controls, not scientific ear thickness standards
P={"root_hold_abs_y_below":0.80,"membrane_full_abs_y_above":1.42,
 "outer_x_depth_shrink_fraction":0.52,"upper_edge_depth_preserve_fraction":0.12,
 "max_individual_vertex_displacement":0.15,
 "max_abs_volume_change_percent":38.0,
 "min_outer_depth_reduction_fraction":0.27,
 "min_transition_zone_vertex_count":60,
 "min_outer_zone_vertex_count":80,
 "root_max_world_displacement":1e-5,
 "mirror_xyz_tolerance":1e-5,
 "expected_vertices":3314,"expected_faces":3312}
CAMS={"FACE":(-9,0,3),"SIDE":(0,-9,3),"THREE_QUARTER":(-7,-8,5),"TOP":(0,-.3,11)}
TGT=Vector((-.25,0,1.89))
r={"schema":"V080_REAL_SOURCE_LOCKED_MEMBRANE_THICKNESS_AND_ROOT_GRADIENT",
 "source_blend_sha256_expected":SHA,"native_blender_version":"5.2.2",
 "species":"African savanna Loxodonta africana, ORIGINAL stylized not certified anatomical 3D",
 "professional_reference":"Blender Studio Julien Kaspar written lesson Sculpting Multiple Objects; preserved source and orthographic big-form QA, new full teacher AV not watched",
 "anatomical_reference":"SDZG African Elephants physical characteristics: lattice cartilage and muscles at base; real photos show slender distal pinna",
 "source_urls":["https://ielc.libguides.com/sdzg/factsheets/african_elephant/characteristics","https://studio.blender.org/training/blender-fundamentals-45-lts/using-multiple-objects/"],
 "frozen_parameters":P,"method":"Actual Blender Mesh duplicate, controlled vertex-coordinate local X thickness compression with smooth distal-root gradient; not Sculpt Grab, not merging into head",
 "native_grab_brush_used":False,"head_mesh_fused":False,"full_new_teacher_av_watched":False,
 "independent_artist_approved":False,"art_approved":False,"status":"INIT"}
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def fp(ob):
 h=hashlib.sha256(ob.type.encode())
 for row in ob.matrix_world:
  for q in row:h.update(struct.pack("<d",float(q)))
 if ob.type=="MESH":
  h.update(str((len(ob.data.vertices),len(ob.data.polygons))).encode())
  for v in ob.data.vertices:h.update(struct.pack("<ddd",*map(float,v.co)))
 elif ob.type=="CURVE":
  h.update(str(ob.data.bevel_depth).encode())
  for spline in ob.data.splines:
   for q in spline.bezier_points:
    h.update(str((tuple(q.co),q.radius)).encode())
 return h.hexdigest()
def met(ob):
 bm=bmesh.new()
 try:
  bm.from_mesh(ob.data)
  points=[ob.matrix_world@v.co for v in bm.verts]
  return {"vertices":len(bm.verts),"faces":len(bm.faces),
   "boundary_edges":sum(e.is_boundary for e in bm.edges),
   "nonmanifold_edges":sum(not e.is_manifold for e in bm.edges),
   "volume":abs(bm.calc_volume(signed=True))*abs(ob.matrix_world.determinant()),
   "world_bbox":[[min(float(q[i]) for q in points),max(float(q[i]) for q in points)] for i in range(3)]}
 finally:bm.free()
def ss(a,b,x):
 t=max(0,min(1.,(x-a)/(b-a)));return t*t*(3-2*t)
def xdepth_band(ob,lo,hi):
 p=[ob.matrix_world@v.co for v in ob.data.vertices]
 p=[v for v in p if lo<=abs(v.y)<hi]
 assert p
 return {"count":len(p),"x_min":min(v.x for v in p),"x_max":max(v.x for v in p),
 "x_span":max(v.x for v in p)-min(v.x for v in p)}
def bvh(ob):
 m=ob.data;m.calc_loop_triangles()
 verts=[tuple(ob.matrix_world@v.co) for v in m.vertices]
 tris=[tuple(int(x) for x in t.vertices) for t in m.loop_triangles]
 return BVHTree.FromPolygons(verts,tris,all_triangles=True)
def render(stage):
 scene=bpy.context.scene;cam=scene.camera;assert cam
 scene.render.engine="BLENDER_WORKBENCH";scene.render.resolution_x=720;scene.render.resolution_y=720
 scene.render.resolution_percentage=100;scene.render.image_settings.file_format="PNG"
 hashes={}
 for name,pos in CAMS.items():
  cam.data.type="PERSP";cam.location=Vector(pos)
  cam.rotation_euler=(TGT-cam.location).to_track_quat("-Z","Y").to_euler()
  f=(OUT/(stage+"_"+name+".png")).resolve()
  scene.render.filepath=str(f);bpy.ops.render.render(write_still=True)
  assert f.stat().st_size>1200;hashes[f.name]=sha(f)
 cam.data.type="ORTHO";cam.data.ortho_scale=2.7
 center=Vector((-1.14,-1.07,2.93));cam.location=Vector((-7.,-5.,4.3))
 cam.rotation_euler=(center-cam.location).to_track_quat("-Z","Y").to_euler()
 f=(OUT/(stage+"_EAR_DETAIL.png")).resolve()
 scene.render.filepath=str(f);bpy.ops.render.render(write_still=True)
 hashes[f.name]=sha(f)
 return hashes
try:
 assert bpy.app.version_string.startswith("5.2.2")
 assert INPUT.is_file() and sha(INPUT)==SHA,"V079 actual source SHA mismatch"
 bpy.ops.wm.open_mainfile(filepath=str(INPUT.resolve()))
 objects=bpy.data.objects
 before_names=sorted(ob.name for ob in objects)
 baseline={ob.name:fp(ob) for ob in objects if ob.type in ("MESH","CURVE")}
 packed={im.name:tuple(im.size) for im in bpy.data.images if im.packed_file}
 assert len(packed)>=3
 near_old=objects[NEAR];far_old=objects[FAR];head=objects[HEAD]
 assert near_old.get("stage")=="V079_AFRICAN_SAVANNA_STYLIZED_SILHOUETTE_TECH_CANDIDATE_ART_HOLD"
 assert head.type=="MESH"
 pre=met(near_old)
 assert pre["vertices"]==3314 and pre["faces"]==3312
 assert pre["boundary_edges"]==pre["nonmanifold_edges"]==0
 all_before=[near_old.matrix_world@v.co for v in near_old.data.vertices]
 old_bands={"outer":xdepth_band(near_old,1.45,2.1),"transition":xdepth_band(near_old,.95,1.25)}
 r["before_near_ear"]=pre;r["before_x_depth_bands"]=old_bands
 # The source V079 already visually hides its old V078 primary ear.
 r["before_renders"]=render("BEFORE")
 col=bpy.data.collections.new("V080_THIN_GRADIENT_MEMBRANE_CANDIDATE")
 bpy.context.scene.collection.children.link(col)
 near=near_old.copy();near.data=near_old.data.copy()
 near.name="V080_NEAR_GRADIENT_THIN_EAR";col.objects.link(near)
 near.matrix_world=near_old.matrix_world.copy()
 # World X is front/back thickness; preserve WORLD Y/Z large silhouette.
 xmid=(pre["world_bbox"][0][0]+pre["world_bbox"][0][1])/2
 inv=near.matrix_world.inverted()
 displacement=[];root_disp=[];transition=[];outer=[]
 for vert,p in zip(near.data.vertices,all_before):
  u=abs(p.y)
  influence=ss(P["root_hold_abs_y_below"],P["membrane_full_abs_y_above"],u)
  h=(p.z-pre["world_bbox"][2][0])/(pre["world_bbox"][2][1]-pre["world_bbox"][2][0])
  edge_protect=P["upper_edge_depth_preserve_fraction"]*ss(.78,.98,h)
  squeeze=P["outer_x_depth_shrink_fraction"]*influence*(1-edge_protect)
  desired=Vector((xmid+(p.x-xmid)*(1-squeeze),p.y,p.z))
  d=(desired-p).length;displacement.append(d)
  if u<P["root_hold_abs_y_below"]:root_disp.append(d)
  if .95<u<1.25:transition.append(d)
  if 1.45<u<2.1:outer.append(d)
  vert.co=inv@desired
 near.data.update()
 aft=met(near)
 new_bands={"outer":xdepth_band(near,1.45,2.1),"transition":xdepth_band(near,.95,1.25)}
 depth_reduction=1-new_bands["outer"]["x_span"]/old_bands["outer"]["x_span"]
 vol_pct=100*(aft["volume"]/pre["volume"]-1)
 r["near_deformation"]={"moved_vertices":sum(x>1e-7 for x in displacement),
  "max_world_vertex_displacement":max(displacement),
  "root_max_world_displacement":max(root_disp,default=0.),
  "transition_avg_displacement":sum(transition)/len(transition) if transition else None,
  "outer_avg_displacement":sum(outer)/len(outer) if outer else None,
  "transition_count":len(transition),"outer_count":len(outer),
  "outer_x_depth_reduction_fraction":depth_reduction,
  "volume_change_percent":vol_pct,
  "y_bbox_change":max(abs(aft["world_bbox"][1][i]-pre["world_bbox"][1][i]) for i in range(2)),
  "z_bbox_change":max(abs(aft["world_bbox"][2][i]-pre["world_bbox"][2][i]) for i in range(2)),
  "after_world_mesh":aft,"after_x_depth_bands":new_bands}
 assert len(transition)>P["min_transition_zone_vertex_count"] and len(outer)>P["min_outer_zone_vertex_count"]
 assert depth_reduction>P["min_outer_depth_reduction_fraction"],("Not sufficiently thin",depth_reduction)
 assert 0.005<max(displacement)<P["max_individual_vertex_displacement"],("Unsafe excessive thickness change",max(displacement))
 assert max(root_disp,default=0.)<P["root_max_world_displacement"],"Head root safety breach"
 assert abs(vol_pct)<P["max_abs_volume_change_percent"],"Volume collapse/expansion out of gate"
 assert r["near_deformation"]["y_bbox_change"]<1e-5 and r["near_deformation"]["z_bbox_change"]<1e-5,"Primary silhouette Y/Z changed"
 assert aft["boundary_edges"]==aft["nonmanifold_edges"]==0 and aft["vertices"]==3314 and aft["faces"]==3312
 # Exact world-space bilateral ear reflection as prior V079 already proved.
 far=far_old.copy();far.data=near.data.copy();far.name="V080_FAR_GRADIENT_THIN_EAR"
 col.objects.link(far);far.matrix_world=far_old.matrix_world.copy()
 inverse_far=far.matrix_world.inverted()
 for va,vb in zip(near.data.vertices,far.data.vertices):
  w=near.matrix_world@va.co
  vb.co=inverse_far@Vector((w.x,-w.y,w.z))
 bm=bmesh.new()
 try:
  bm.from_mesh(far.data);bmesh.ops.reverse_faces(bm,faces=list(bm.faces));bm.to_mesh(far.data)
 finally:bm.free()
 far.data.update();bpy.context.view_layer.update()
 mirrored=max((Vector((q.x,-q.y,q.z))-w).length for q,w in zip(
  [near.matrix_world@v.co for v in near.data.vertices],
  [far.matrix_world@v.co for v in far.data.vertices]))
 r["full_xyz_mirror_error"]=mirrored
 assert mirrored<P["mirror_xyz_tolerance"]
 assert met(far)["nonmanifold_edges"]==0 and met(far)["boundary_edges"]==0
 # Anatomical contact diagnostics: triangle intersections are not fusion/proof of real organic seam
 headtree=bvh(head)
 old_crossings=len(headtree.overlap(bvh(near_old)))
 new_crossings=len(headtree.overlap(bvh(near)))
 r["head_ear_contact_diagnostic"]={"old_triangle_surface_crossings":old_crossings,"new_triangle_surface_crossings":new_crossings,
   "head_mesh_modified":False,"joint_is_fused":False,
   "interpretation":"BVH triangle intersections alone cannot certify natural articulated cartilage/muscular attachment"}
 assert new_crossings>0 and old_crossings>0,"Head-ear root lost geometric surface contact"
 near_old.hide_render=True;far_old.hide_render=True
 for ob in (near,far):
  ob.hide_render=False
  ob["stage"]="V080_THINNER_GRADIENT_EAR_TECH_CANDIDATE_ART_HOLD"
  ob["source_sha256"]=SHA
  ob["anatomy"]="STYLIZED_NOT_ART_APPROVED"
  ob["method"]="ORIGINAL_MESH_THICKNESS_WARP_NOT_SCULPT_BRUSH"
 r["after_renders"]=render("AFTER")
 assert sorted(o.name for o in objects if not o.name.startswith("V080_"))==before_names
 assert all(fp(objects[n])==v for n,v in baseline.items()),"Original V079 geometry/transforms mutated"
 assert packed=={im.name:tuple(im.size) for im in bpy.data.images if im.packed_file}
 r["all_previous_mesh_curve_data_unchanged"]=True
 r["all_three_original_cc0_refs_unchanged"]=True
 dst=(OUT/"V080_NATIVE_GRADIENT_THIN_EAR_CANDIDATE.blend").resolve()
 bpy.ops.wm.save_as_mainfile(filepath=str(dst))
 r["saved_blend_sha256"]=sha(dst)
 r["status"]="NATIVE_GRADED_THIN_EAR_TECH_PASS; NO_ORGANIC_JOINT_ART_PROOF; ART_HOLD"
except Exception as e:
 r["status"]="FAIL_OR_SOURCE_HOLD";r["error"]=repr(e)
finally:
 (OUT/"V080_REAL_THICKNESS_AND_ROOT_RECEIPT.json").write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n")
 print("V080_THIN_MEMBRANE",json.dumps({k:r.get(k) for k in ("status","error","near_deformation","full_xyz_mirror_error","head_ear_contact_diagnostic","saved_blend_sha256")},ensure_ascii=False)[:14000],flush=True)
if r["status"].startswith("FAIL"):sys.exit(80)
