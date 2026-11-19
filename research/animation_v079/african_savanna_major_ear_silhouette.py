# SPDX-License-Identifier: GPL-2.0-or-later
"""V079: real original broad ear-flap sculptural silhouette on SOURCE-LOCKED V078 Blender model.
Primary purpose: transfer African SAVANNA elephant broad upper flap, tapering lower
contour and thinner outer ear into one ORIGINAL stylized source candidate.
Sources: SANParks African Bush Elephant (pointed triangular ears); IEF African-vs-Asian;
ElephantVoices front ear photographic reference (visual analysis only, NOT copied);
Blender Studio Kaspar Sculpting Multiple Objects: reference-first orthographic
big silhouette and Grab; old full V043/V070 study already archived.
This is native Blender Mesh editing using controlled world vertex coordinates,
NOT a native Sculpt Grab stroke or rigging, NOT artist-approved anatomy.
"""
import bpy,bmesh,json,hashlib,math,struct,pathlib,sys
from mathutils import Vector
OUT=pathlib.Path("v079_savanna_ear_silhouette");OUT.mkdir(exist_ok=True)
SOURCE=pathlib.Path("v078_integrated_ear_fold/V078_NATIVE_EMBEDDED_EAR_FOLD_CANDIDATE.blend")
SHA="5f4e7357c8147e60894a011deebf87ba05c2ff8200f3b64382235d0fb6325a71"
NEAR="V078_NEAR_REAL_SURFACE_FOLD";FAR="V078_FAR_MIRRORED_REAL_SURFACE_FOLD"
P={"outer_fan_shoulder_max_outward_y":0.245,"base_outer_outward_y":0.075,
   "shoulder_height_fraction":0.68,"shoulder_height_sigma":0.29,
   "upper_top_flatten_z":0.06,"lower_tip_drop_z":0.15,
   "outer_thickness_reduction_factor":0.25,
   "root_mask_start_abs_y":0.80,"root_mask_full_abs_y":1.32,
   "max_abs_volume_change_pct":27.0,"max_displacement":0.39,
   "root_protected_y_gt":-0.80,"root_max_disp":0.00001,
   "min_outer_y_extent_gain":0.12,"min_upper_vs_lower_flare_mean_ratio":1.45,
   "max_mirror_xyz_error":0.00001,"expected_vertices":3314,"expected_faces":3312}
CAMS={"FACE":(-9,0,3),"SIDE":(0,-9,3),"THREE_QUARTER":(-7,-8,5),"TOP":(0,-.3,11)}
CENTER=Vector((-.25,0,1.89))
r={"schema":"V079_AFRICAN_SAVANNA_ELEPHANT_PRIMARY_EAR_FLAP_SILHOUETTE",
 "date":"2026-11-19","source_sha_expected":SHA,"blender_version":"5.2.2",
 "source_model":"V078 native high-resolution ridge-trough mesh; 3314 vertices",
 "species_target":"African savanna elephant (Loxodonta africana), STYLIZED, not certified zoological anatomical model",
 "physical_reference":{"SANParks":"https://www.sanparks.org/conservation/parks/marakele-national-park/primary-consumers-herbivores/african-elephant",
   "IEF":"https://elephantconservation.org/faq-items/how-can-you-tell-the-difference-between-an-african-and-an-asian-elephant/",
   "ElephantVoices_visual_target":"https://www.elephantvoices.org/elephant-acoustic-communication"},
 "teacher":"Blender Studio Julien Kaspar 'Sculpting Multiple Objects' orthographic silhouette & reference-first; full new video NOT watched",
 "method":"Original authored Blender mesh world-vertex broad-form warp of a COPY of original V078; not Brush Grab; no new wrinkles",
 "native_grab_brush_used":False,"full_new_teacher_av_watched":False,
 "parameters_frozen":P,"art_approved":False,"independent_artist_review":False,
 "status":"INIT"}
def hashfile(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def fp(o):
 h=hashlib.sha256()
 h.update(o.type.encode())
 for row in o.matrix_world:
  for v in row:h.update(struct.pack("<d",float(v)))
 if o.type=="MESH":
  h.update(str((len(o.data.vertices),len(o.data.polygons))).encode())
  for v in o.data.vertices:h.update(struct.pack("<ddd",*map(float,v.co)))
 elif o.type=="CURVE":
  h.update(str((o.data.bevel_depth,tuple((tuple(p.co),float(p.radius)) for s in o.data.splines for p in s.bezier_points))).encode())
 return h.hexdigest()
def metrics(ob):
 me=ob.data;bm=bmesh.new()
 try:
  bm.from_mesh(me)
  signed=abs(bm.calc_volume(signed=True))*abs(ob.matrix_world.determinant())
  boundary=sum(1 for e in bm.edges if e.is_boundary)
  nonmanifold=sum(1 for e in bm.edges if not e.is_manifold)
  pts=[ob.matrix_world@v.co for v in bm.verts]
  bb=[[min(float(v[i]) for v in pts),max(float(v[i]) for v in pts)] for i in range(3)]
  return {"vertices":len(bm.verts),"faces":len(bm.faces),"boundary":boundary,
    "nonmanifold":nonmanifold,"volume":signed,"world_bbox":bb}
 finally:bm.free()
def ss(a,b,x):
 t=max(0,min(1,(x-a)/(b-a)))
 return t*t*(3-2*t)
def render(tag):
 sc=bpy.context.scene;cam=sc.camera
 assert cam
 sc.render.engine="BLENDER_WORKBENCH"
 sc.render.resolution_x=720;sc.render.resolution_y=720;sc.render.resolution_percentage=100
 sc.render.image_settings.file_format="PNG"
 result={}
 for name,position in CAMS.items():
  cam.data.type="PERSP";cam.location=Vector(position)
  cam.rotation_euler=(CENTER-cam.location).to_track_quat("-Z","Y").to_euler()
  p=(OUT/(tag+"_"+name+".png")).resolve()
  sc.render.filepath=str(p);bpy.ops.render.render(write_still=True)
  assert p.stat().st_size>1000
  result[p.name]=hashfile(p)
 # same camera for the exact ear macro comparison
 cam.data.type="ORTHO";cam.data.ortho_scale=2.7
 center=Vector((-1.14,-1.07,2.93))
 cam.location=Vector((-7.,-5.,4.3))
 cam.rotation_euler=(center-cam.location).to_track_quat("-Z","Y").to_euler()
 p=(OUT/(tag+"_EAR_DETAIL.png")).resolve();sc.render.filepath=str(p)
 bpy.ops.render.render(write_still=True);result[p.name]=hashfile(p)
 return result
try:
 assert bpy.app.version_string.startswith("5.2.2")
 assert SOURCE.is_file() and hashfile(SOURCE)==SHA,"Original V078 SHA mismatch"
 bpy.ops.wm.open_mainfile(filepath=str(SOURCE.resolve()))
 obs=bpy.data.objects
 originals={o.name:fp(o) for o in obs if o.type in ("MESH","CURVE")}
 names=sorted(o.name for o in obs)
 packed={i.name:tuple(i.size) for i in bpy.data.images if i.packed_file}
 assert len(packed)>=3
 original_ear=obs[NEAR];far_original=obs[FAR]
 assert original_ear.get("stage")=="V078_REAL_EAR_FOLD_MESH_CANDIDATE_ART_HOLD"
 assert len(original_ear.data.vertices)==P["expected_vertices"]
 baseline=metrics(original_ear)
 assert baseline["boundary"]==0 and baseline["nonmanifold"]==0
 r["source_near_ear_mesh_metrics"]=baseline
 r["original_source_objects"]=len(names)
 r["before_renders"]=render("BEFORE")
 col=bpy.data.collections.new("V079_ORIGINAL_SAVANNA_EAR_STYLIZED_SILHOUETTE_CANDIDATES")
 bpy.context.scene.collection.children.link(col)
 near=original_ear.copy();near.data=original_ear.data.copy()
 near.name="V079_NEAR_SAVANNA_FLAP_CANDIDATE";col.objects.link(near)
 near.matrix_world=original_ear.matrix_world.copy()
 oldworld=[near.matrix_world@v.co for v in near.data.vertices]
 # Unmodified V078 shape has this actual bbox, from receipt, not invented.
 bound=baseline["world_bbox"]
 cx=(bound[0][0]+bound[0][1])*.5
 zlo,zhi=bound[2]
 assert 2.0<zlo<2.5 and 3.3<zhi<3.8,("unexpected source silhouette",bound)
 inv=near.matrix_world.inverted()
 disp=[];y_flare_upper=[];y_flare_lower=[];root=[];taper_disp=[]
 upper=moved=0
 for vertex,p in zip(near.data.vertices,oldworld):
  u=(-p.y)
  influence=ss(P["root_mask_start_abs_y"],P["root_mask_full_abs_y"],u)
  h=(p.z-zlo)/(zhi-zlo)
  shoulder=math.exp(-.5*((h-P["shoulder_height_fraction"])/P["shoulder_height_sigma"])**2)
  out=(P["base_outer_outward_y"]+P["outer_fan_shoulder_max_outward_y"]*shoulder)*influence
  top_shave=P["upper_top_flatten_z"]*ss(.79,.98,h)*influence
  tip_down=P["lower_tip_drop_z"]*(1-ss(.22,.58,h))*influence
  thin=P["outer_thickness_reduction_factor"]*influence
  desired=Vector((cx+(p.x-cx)*(1-thin),p.y-out,p.z-top_shave-tip_down))
  d=desired-p
  if d.length>1e-6:moved+=1
  disp.append(float(d.length))
  if p.y>P["root_protected_y_gt"]:root.append(float(d.length))
  if .55<h<.82 and u>1.1:y_flare_upper.append(out)
  if .04<h<.31 and u>1.1:y_flare_lower.append(out)
  if u>1.34:taper_disp.append(abs(float((p.x-cx)*thin)))
  vertex.co=inv@desired
 near.data.update()
 post=metrics(near)
 vol_pct=(post["volume"]/baseline["volume"]-1)*100
 topmean=sum(y_flare_upper)/len(y_flare_upper) if y_flare_upper else 0.
 botmean=sum(y_flare_lower)/len(y_flare_lower) if y_flare_lower else 0.
 r["original_near_mesh_deformation"]={"moved_vertices":moved,"max_displacement":max(disp),
  "root_max":max(root,default=0.),"max_outer_y_gain":baseline["world_bbox"][1][0]-post["world_bbox"][1][0],
  "mean_upper_fan_y_displacement":topmean,"upper_sample_count":len(y_flare_upper),
  "mean_lower_fan_y_displacement":botmean,"lower_sample_count":len(y_flare_lower),
  "upper_to_lower_flare_ratio":(topmean/botmean if botmean>0 else None),
  "outer_thickness_reduction_sample_mean":sum(taper_disp)/len(taper_disp) if taper_disp else 0.,
  "volume_change_percent":vol_pct,"result_mesh_metrics":post}
 assert len(y_flare_upper)>20 and len(y_flare_lower)>20,"Cannot certify relative upper/lower flap expansion"
 assert topmean>P["min_upper_vs_lower_flare_mean_ratio"]*botmean,"Flap not anatomically upper broad/lower taper"
 assert baseline["world_bbox"][1][0]-post["world_bbox"][1][0]>P["min_outer_y_extent_gain"],"Too weak visual width"
 assert max(root,default=0.)<P["root_max_disp"],"Unsafe attachment root movement"
 assert max(disp)<P["max_displacement"],"Too broad violent warp"
 assert abs(vol_pct)<P["max_abs_volume_change_pct"],"Unsafe gross volume"
 assert post["vertices"]==baseline["vertices"]==P["expected_vertices"]
 assert post["faces"]==baseline["faces"]==P["expected_faces"]
 assert post["boundary"]==0 and post["nonmanifold"]==0
 # Mirror in WORLD space to ensure no accidental local-center mismatch.
 far=far_original.copy()
 far.data=near.data.copy();far.name="V079_FAR_MIRRORED_SAVANNA_FLAP_CANDIDATE"
 col.objects.link(far);far.matrix_world=far_original.matrix_world.copy()
 inv_far=far.matrix_world.inverted()
 for vnear,vfar in zip(near.data.vertices,far.data.vertices):
  w=near.matrix_world@vnear.co
  vfar.co=inv_far@Vector((w.x,-w.y,w.z))
 bm=bmesh.new()
 try:
  bm.from_mesh(far.data);bmesh.ops.reverse_faces(bm,faces=list(bm.faces));bm.to_mesh(far.data)
 finally:bm.free()
 far.data.update();bpy.context.view_layer.update()
 mirror=max((Vector((a.x,-a.y,a.z))-b).length for a,b in
  zip([near.matrix_world@v.co for v in near.data.vertices],[far.matrix_world@v.co for v in far.data.vertices]))
 r["mirror_full_xyz_max_difference"]=mirror
 assert mirror<P["max_mirror_xyz_error"]
 assert metrics(far)["boundary"]==0 and metrics(far)["nonmanifold"]==0
 # Existing V078 real integrated folds are in the deformed highres vertices,
 # not thrown away. Visual swap only inside disposable candidate .blend.
 original_ear.hide_render=True;far_original.hide_render=True
 near.hide_render=False;far.hide_render=False
 for o in (near,far):
  o["stage"]="V079_AFRICAN_SAVANNA_STYLIZED_SILHOUETTE_TECH_CANDIDATE_ART_HOLD"
  o["source_sha256"]=SHA
  o["deformation_method"]="ORIGINAL_BOUNDED_NATIVE_BLENDER_MESH_VERTEX_SILHOUETTE_WARP_NOT_SCULPT_BRUSH"
  o["art_approved"]=False
 r["after_renders"]=render("AFTER")
 assert sorted(o.name for o in obs if not o.name.startswith("V079_"))==names
 assert all(fp(obs[n])==old for n,old in originals.items()),"Original V078 geometry or transforms mutated"
 assert packed=={i.name:tuple(i.size) for i in bpy.data.images if i.packed_file}
 r["source_geometry_untouched"]=True;r["packed_photos_unchanged"]=True
 # Exact scene source visibility only changed for the two replaced ear objects.
 r["original_visibility_changed_only_for"]=[NEAR,FAR]
 dst=(OUT/"V079_ORIGINAL_SAVANNA_EAR_FLAP_NATIVE_CANDIDATE.blend").resolve()
 bpy.ops.wm.save_as_mainfile(filepath=str(dst))
 r["saved_native_blend_sha256"]=hashfile(dst)
 r["status"]="NATIVE_REAL_MAJOR_SILHOUETTE_TECH_PASS; SELF_ART_QA_PENDING; ART_HOLD"
except Exception as e:r["status"]="FAIL_OR_EVIDENCE_HOLD";r["error"]=repr(e)
finally:
 (OUT/"V079_ACTUAL_BROAD_EAR_SILHOUETTE_RECEIPT.json").write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n")
 print("V079_BROAD_SAVANNA_EAR",json.dumps({k:r.get(k) for k in ("status","error","original_near_mesh_deformation","mirror_full_xyz_max_difference","saved_native_blend_sha256")},ensure_ascii=False)[:13000],flush=True)
if r["status"].startswith("FAIL"):sys.exit(79)
