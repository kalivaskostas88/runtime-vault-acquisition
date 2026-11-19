# SPDX-License-Identifier: GPL-2.0-or-later
"""V082 professional-first ear construction Golden Slice.
Sources V081 actual Blender Studio video frames: editable LOW POLY OPEN surface
followed by subdivision and solidify; official Blender 4.5 Solidify docs.
Specific cat ear Blender Secrets YouTube video YFzmfoxHuyM is ACCESS_HOLD, not
claimed watched. Transfer only confirmed method, not unobserved teacher actions.
Create ORIGINAL low-poly African savanna elephant ear open mid-surfaces in a
NEW protected V079 Blender project. Real native Blender Subsurf+Solidify,
graded root vs distal thickness by vertex group. TECH proof, ART_HOLD.
"""
import bpy,bmesh,hashlib,json,pathlib,struct,math,sys
from mathutils import Vector
OUT=pathlib.Path("v082_open_pinna_surface");OUT.mkdir(exist_ok=True)
SOURCE=pathlib.Path("v079_savanna_ear_silhouette/V079_ORIGINAL_SAVANNA_EAR_FLAP_NATIVE_CANDIDATE.blend")
SOURCE_SHA="b04204cd78581b7ebe95731d9ccc3f61ed454d35ebe3ed923d80b08b148a9aea"
OLD=("V079_NEAR_SAVANNA_FLAP_CANDIDATE","V079_FAR_MIRRORED_SAVANNA_FLAP_CANDIDATE")
NEW=("V082_NEAR_OPEN_QUAD_PINNA","V082_FAR_OPEN_QUAD_PINNA")
Z=(2.18,2.32,2.49,2.69,2.89,3.10,3.28,3.43,3.55,3.63)
INNER_Y=(-.72,-.68,-.63,-.59,-.56,-.54,-.55,-.58,-.65,-.74)
OUTER_Y=(-.90,-1.21,-1.53,-1.73,-1.93,-2.02,-2.03,-1.94,-1.74,-1.40)
COLS=7
P={"rows":len(Z),"columns":COLS,"low_poly_surface_quads":(len(Z)-1)*(COLS-1),
"max_base_vertices":80,"subsurf_levels":2,"solidify_thickness":.080,
"solidify_min_thickness_weight_ratio":.26,"subsurface_resolution":"NATIVE_CATMUll_CLARK",
"root_thickness_weight":1.0,"tip_thickness_weight":0.0,
"max_final_verts":25000,"symmetry_tol":1e-5}
CAMS={"FACE":(-9,0,3),"SIDE":(0,-9,3),"THREE_QUARTER":(-7,-8,5),"TOP":(0,-.3,11)}
TGT=Vector((-.25,0,1.89))
r={"schema":"V082_REAL_NATIVE_OPEN_QUAD_SUBSURF_SOLIDIFY_ELEPHANT_PINNA",
"source_original_sha256":SOURCE_SHA,"blender":"5.2.2","teacher":"Julien Kaspar, Blender Studio 4.5 Sculpting Multiple Objects: V081 actual sparse sampled video frames",
"additional_source":"Blender Studio official Solidify documentation",
"specialized_cat_ear_video":"YFzmfoxHuyM access hold from public YouTube GitHub yt-dlp no player response; NOT VISUALLY_STUDIED",
"full_new_teacher_video_watched":False,"audio_listened":False,
"professional_method_transfer":"editable open mid-surface then native non-destructive Subdivision Surface + Solidify",
"new_anatomical_claim":"ORIGINAL STYLIZED African savanna elephant; not professional anatomy",
"artist_approved":False,"independent_art_approved":False,"joint_fused_to_head":False,
"frozen_parameters":P,"status":"INIT"}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def fpr(o):
 h=hashlib.sha256(o.type.encode())
 for line in o.matrix_world:
  for a in line:h.update(struct.pack("<d",float(a)))
 if o.type=="MESH":
  h.update(str((len(o.data.vertices),len(o.data.polygons))).encode())
  for v in o.data.vertices:h.update(struct.pack("<ddd",*map(float,v.co)))
 elif o.type=="CURVE":
  h.update(str(o.data.bevel_depth).encode())
  for spline in o.data.splines:
   for v in spline.bezier_points:h.update(str((tuple(v.co),v.radius)).encode())
 return h.hexdigest()
def measure(mesh,mat):
 b=bmesh.new()
 try:
  b.from_mesh(mesh)
  m={"verts":len(b.verts),"faces":len(b.faces),
  "open_boundary_edges":sum(e.is_boundary for e in b.edges),
  "nonmanifold_edges":sum(not e.is_manifold for e in b.edges)}
  if m["open_boundary_edges"]==0 and m["nonmanifold_edges"]==0:m["volume_abs"]=abs(b.calc_volume(signed=True))*abs(mat.determinant())
  return m
 finally:b.free()
def build(near):
 mesh=bpy.data.meshes.new("V082_ORIGINAL_OPEN_MIDSURFACE_"+("NEAR" if near else "FAR"))
 vs=[];fs=[]
 for i,z in enumerate(Z):
  for col in range(COLS):
   u=col/(COLS-1)
   y=(1-u)*INNER_Y[i]+u*OUTER_Y[i]
   # Original mild saddle of a membrane, not a sphere, no crease details
   x=-1.095-0.075*math.sin(math.pi*u)*(0.65+0.35*math.sin((z-Z[0])/(Z[-1]-Z[0])*math.pi))
   if 0.15<u<.86:x+=.020*math.sin(math.pi*u)*math.cos(math.pi*(z-2.8)/1.45)
   if not near:y=-y
   vs.append((x,y,z))
 for i in range(len(Z)-1):
  for col in range(COLS-1):
   a=i*COLS+col
   quad=(a,a+1,a+1+COLS,a+COLS)
   if not near:quad=tuple(reversed(quad))
   fs.append(quad)
 mesh.from_pydata(vs,[],fs);mesh.update()
 obj=bpy.data.objects.new(NEW[0 if near else 1],mesh)
 bpy.context.scene.collection.objects.link(obj)
 return obj
def render(tag):
 sc=bpy.context.scene
 sc.render.engine="BLENDER_WORKBENCH"
 sc.render.resolution_x=720;sc.render.resolution_y=720
 sc.render.resolution_percentage=100;sc.render.image_settings.file_format="PNG"
 cam=sc.camera;assert cam
 hashes={}
 for k,p in CAMS.items():
  cam.data.type="PERSP";cam.location=Vector(p)
  cam.rotation_euler=(TGT-cam.location).to_track_quat("-Z","Y").to_euler()
  path=(OUT/(tag+"_"+k+".png")).resolve()
  sc.render.filepath=str(path);bpy.ops.render.render(write_still=True)
  hashes[path.name]=sha(path)
 cam.data.type="ORTHO";cam.data.ortho_scale=2.7
 center=Vector((-1.14,-1.07,2.93));cam.location=Vector((-7,-5,4.3))
 cam.rotation_euler=(center-cam.location).to_track_quat("-Z","Y").to_euler()
 path=(OUT/(tag+"_EAR_DETAIL.png")).resolve();sc.render.filepath=str(path);bpy.ops.render.render(write_still=True)
 hashes[path.name]=sha(path)
 return hashes
try:
 assert bpy.app.version_string.startswith("5.2.2")
 assert SOURCE.is_file() and sha(SOURCE)==SOURCE_SHA
 bpy.ops.wm.open_mainfile(filepath=str(SOURCE.resolve()))
 objects=bpy.data.objects
 base={o.name:fpr(o) for o in objects if o.type in ("MESH","CURVE")}
 original_names=sorted(o.name for o in objects)
 photos={i.name:tuple(i.size) for i in bpy.data.images if i.packed_file}
 assert len(photos)>=3
 assert all(objects[n].get("stage")=="V079_AFRICAN_SAVANNA_STYLIZED_SILHOUETTE_TECH_CANDIDATE_ART_HOLD" for n in OLD)
 r["before_renders"]=render("BEFORE")
 new=[build(True),build(False)]
 r["object_proof"]={}
 for obj,near in zip(new,(True,False)):
  raw=measure(obj.data,obj.matrix_world)
  assert raw["verts"]==70 and raw["faces"]==54
  assert raw["open_boundary_edges"]>0
  group=obj.vertex_groups.new(name="V082_VARIABLE_THICKNESS_WEIGHTS")
  for i in range(len(Z)):
   for col in range(COLS):
    u=col/(COLS-1)
    w=1-(u*u*(3-2*u))
    group.add([i*COLS+col],w,"REPLACE")
  sub=obj.modifiers.new("V082_NATIVE_SUBDIVISION_SURFACE","SUBSURF")
  sub.subdivision_type="CATMULL_CLARK";sub.levels=2;sub.render_levels=2
  solid=obj.modifiers.new("V082_NATIVE_SOLIDIFY_VARIABLE_THICKNESS","SOLIDIFY")
  solid.solidify_mode="EXTRUDE"
  solid.thickness=P["solidify_thickness"]
  solid.offset=0
  solid.use_rim=True
  solid.vertex_group=group.name
  solid.thickness_vertex_group=P["solidify_min_thickness_weight_ratio"]
  bpy.context.view_layer.update()
  ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
  mesh=ev.to_mesh()
  try:m=measure(mesh,ev.matrix_world)
  finally:ev.to_mesh_clear()
  assert m["verts"]>70 and m["verts"]<P["max_final_verts"]
  assert m["open_boundary_edges"]==0 and m["nonmanifold_edges"]==0
  assert m["volume_abs"]>0.0001
  obj["stage"]="V082_OPEN_QUAD_SUBSURF_SOLIDIFY_ART_HOLD"
  obj["real_proof"]="Actual Blender Subsurf + Solidify; 70-vertex open quad base, evaluated manifold closed final"
  obj["source_sha256"]=SOURCE_SHA
  r["object_proof"][obj.name]={"base":raw,"evaluated":m,
    "modifier_stack":[{"type":m.type,"name":m.name} for m in obj.modifiers],
    "raw_mid_surface_open":True,"evaluated_solid_closed":True,
    "initial_near_far_thickness_ratio":P["solidify_min_thickness_weight_ratio"]}
 # original V079 near/far are hidden ONLY in new derivative scene; preserve geometry
 for n in OLD:objects[n].hide_render=True
 r["after_renders"]=render("AFTER")
 assert sorted(o.name for o in objects if not o.name.startswith("V082_"))==original_names
 assert all(fpr(objects[n])==h for n,h in base.items()),"Source geometry/transform corruption"
 assert photos=={i.name:tuple(i.size) for i in bpy.data.images if i.packed_file}
 r["protected_previous_geometry_unchanged"]=True
 r["three_packed_photo_refs_unchanged"]=True
 r["original_visibility_changed_only_for"]=list(OLD)
 dst=(OUT/"V082_ORIGINAL_OPEN_SURFACE_EAR_PROOF.blend").resolve()
 bpy.ops.wm.save_as_mainfile(filepath=str(dst))
 r["saved_blend_sha256"]=sha(dst)
 r["status"]="REAL_OPEN_QUAD_NATIVE_SUBSURF_SOLIDIFY_TECH_PASS; NO_ART_APPROVAL; ROOT_NOT_FUSED"
except Exception as e:
 r["status"]="FAIL_OR_METHOD_HOLD";r["error"]=repr(e)
finally:
 (OUT/"V082_REAL_OPEN_SURFACE_TECH_RECEIPT.json").write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n")
 print("V082_REAL_OPEN_SURFACE",json.dumps({k:r.get(k) for k in ("status","error","object_proof","saved_blend_sha256")},ensure_ascii=False)[:6500],flush=True)
if r["status"].startswith("FAIL"):sys.exit(82)
