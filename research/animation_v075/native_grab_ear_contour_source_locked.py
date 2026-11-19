# SPDX-License-Identifier: GPL-2.0-or-later
"""V075 — first actual Blender 5.2.2 sculpt Grab on V074 elephant ear contour.
Teacher-first: Blender Foundation Grab official brush manual (2026), Julien Kaspar
Blender Studio: primary silhouettes before detailing, original zoo photographs for
anatomical reference. All art direction numeric choices are OUR frozen tests.
No procedural mesh vertex deformation is used for the NEAR ear: native Grab brush
asset + sculpt.brush_stroke changes the actual source-locked mesh.
The FAR ear receives a separately owned copy of the sculpted native mesh for
strict symmetry, as already proven by V074.
No other parts, rig, or protected assets modified. ART_HOLD always.
"""
import bpy,bmesh,json,hashlib,struct,math,sys,pathlib
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from bpy_extras.view3d_utils import location_3d_to_region_2d
OUT=pathlib.Path("v075_ear_grab");OUT.mkdir(exist_ok=True)
SOURCE=pathlib.Path("v074_ear_art_blockout/V074_ORIGINAL_EAR_FAN_BLOCKOUT_CANDIDATE.blend")
SOURCE_SHA="b29e7f6aed50c0165656c1bbb820972e2c738dfb3ef784d2b6dbfbd1a62aca22"
NEAR,FAR="06_EAR_NEAR","06_EAR_FAR"
# PRE-FROZEN original design — not supposed to be universal teacher settings.
STRENGTH=0.14  # measured native displacement 12.6009pct @0.64 and 4.72535pct @0.24; forecast ~2.76pct at 0.14, same 3pct stop gate
SIZE=65  # reduced brush radius protects compact thin flap; art world start/end unchanged
EVENTS=61
VIEW=Vector((-1.15,-1.00,3.0))
VIEW_DISTANCE=2.8  # measured 3.8 yielded 13.2008px; zoom only, do NOT relax >15px gate
ORIGIN=Vector((-1.24,-1.43,3.25))  # world-space upper/outboard fan contour
END=Vector((-1.24,-1.62,3.37))     # mild outboard+upward Grab, no ear-root dragging
PIXEL_STROKE_CALIBRATION=1.50  # 13.2008px stale view projection ×1.50 = 19.8012px, unchanged >15px gate
CAMERAS={"SIDE":(0,-9,3.0),"FACE":(-9,0,3.0),"THREE_QUARTER":(-7,-8,5.0),"TOP":(0,-0.3,11)}
RENDER_TARGET=Vector((-.25,0,1.89))
MAX_DISP=0.42
ROOT_SAFE_MAX=0.08
VOL_ABS_PERCENT_MAX=3.0
MIRROR_TOL=1e-5
status={"schema":"V075_ACTUAL_NATIVE_GRAB_STYLIZED_EAR_FAN_CONTOUR",
"professional_written_teacher":"Blender Foundation 5.2 Grab official manual, Julien Kaspar Blender Studio primary silhouettes",
"original_anatomy_reference":"San Diego Zoo / elephant species variation, generic stylized artistic result not species approved",
"new_specific_teacher_full_AV_watched":False,"actual_native_grab_claim":True,
"source_sha256_expected":SOURCE_SHA,"blender_version":"5.2.2",
"prior_rejected_native_grab":"run 44492336888 105/200 verts 12.6009pct @strength 0.64 size105; run 44492640356 105/200 verts 4.72535pct @strength 0.24 size65",
"frozen_preflight":{"asset":"Grab","strength":STRENGTH,"size_px":SIZE,"events":EVENTS,"view_distance_calibrated_from_measured_13_2008px":VIEW_DISTANCE,
"stroke_world_origin":list(ORIGIN),"stroke_world_end":list(END),
"headless_pixel_stroke_calibration":PIXEL_STROKE_CALIBRATION,
"max_vertex_displacement":MAX_DISP,"root_max_displacement":ROOT_SAFE_MAX,
"max_abs_volume_change_pct":VOL_ABS_PERCENT_MAX,"max_world_mirror_diff":MIRROR_TOL,
"min_moved_vertices":8,"min_outward_vertex_change":0.025,"min_upper_z_change":0.012},
"source_preserved":True,"art_approved":False,"independent_art_approval":False,
"status":"INIT"}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def mesh_hash(ob):
 return hashlib.sha256(b"".join(struct.pack("<ddd",*map(float,v.co)) for v in ob.data.vertices)).hexdigest()
def other_fingerprint(o):
 if o.type=="MESH":
  return hashlib.sha256((mesh_hash(o)+str(tuple(round(float(a),8) for row in o.matrix_world for a in row))).encode()).hexdigest()
 if o.type=="CURVE":
  return hashlib.sha256(repr([(tuple(p.co),p.radius) for s in o.data.splines for p in s.bezier_points]).encode()).hexdigest()
 return None
def measure(ob):
 me=ob.data; bm=bmesh.new();bm.from_mesh(me)
 try:volume=abs(bm.calc_volume(signed=True))
 finally:bm.free()
 return {"vertices":len(me.vertices),"faces":len(me.polygons),"volume":volume,"mesh_position_sha256":mesh_hash(ob)}
def renders(tag):
 sc=bpy.context.scene
 sc.render.engine="BLENDER_WORKBENCH";sc.render.resolution_x=650;sc.render.resolution_y=650
 sc.render.resolution_percentage=100;sc.render.image_settings.file_format="PNG"
 assert sc.camera
 result={}
 for label,c in CAMERAS.items():
  sc.camera.location=Vector(c)
  sc.camera.rotation_euler=(RENDER_TARGET-sc.camera.location).to_track_quat("-Z","Y").to_euler()
  p=(OUT/(tag+"_"+label+".png")).resolve()
  sc.render.filepath=str(p);bpy.ops.render.render(write_still=True)
  assert p.stat().st_size>1200
  result[p.name]=sha(p)
 return result
def viewport():
 ctx=bpy.context.copy()
 for area in ctx["screen"].areas:
  if area.type=="VIEW_3D":
   region=next((x for x in area.regions if x.type=="WINDOW"),None)
   if region:
    ctx.update(area=area,region=region)
    p=area.spaces.active.region_3d
    p.view_location=VIEW;p.view_distance=VIEW_DISTANCE
    p.view_rotation=(VIEW-Vector((-10,-1,3.15))).to_track_quat("-Z","Y")
    p.view_perspective="ORTHO"
    return ctx
 raise RuntimeError("No real native VIEW_3D; no fake brush")
def bvh(o):
 me=o.data;me.calc_loop_triangles()
 vv=[tuple(o.matrix_world@v.co) for v in me.vertices]
 tt=[tuple(int(x) for x in t.vertices) for t in me.loop_triangles]
 return BVHTree.FromPolygons(vv,tt,all_triangles=True)
try:
 assert bpy.app.version_string.startswith("5.2.2")
 assert SOURCE.is_file() and sha(SOURCE)==SOURCE_SHA,"V074 original lost or wrong SHA"
 bpy.ops.wm.open_mainfile(filepath=str(SOURCE.resolve()))
 bpy.context.view_layer.update()
 objects=bpy.data.objects;ears=[objects[NEAR],objects[FAR]]
 assert all(x.type=="MESH" and x.get("stage")=="V074_EAR_FAN_SHAPE_BLOCKOUT_ART_HOLD" for x in ears)
 assert all(all(abs(float(a)-1)<1e-6 for a in x.scale) for x in ears)
 stage_parts={x.name for x in objects if x.get("stage")}
 status["source_stage_part_count"]=len(stage_parts)
 status["source_stage_part_names"]=sorted(stage_parts)
 assert len(stage_parts)==11,("V071 joined 3 body objects into one: expected exactly 11 original parts",len(stage_parts))
 assert mesh_hash(ears[0])==mesh_hash(ears[1]),"V074 ears not local mesh-equal"
 original_objs=sorted(o.name for o in objects)
 untouched={o.name:other_fingerprint(o) for o in objects if o.type in {"MESH","CURVE"} and o.name not in [NEAR,FAR]}
 packed={im.name:tuple(im.size) for im in bpy.data.images if im.packed_file}
 assert len(packed)>=3
 before={n:measure(objects[n]) for n in [NEAR,FAR]}
 coords=[v.co.copy() for v in ears[0].data.vertices]
 world_before=[ears[0].matrix_world@v.co for v in ears[0].data.vertices]
 status["before"]=before;status["before_renders"]=renders("BEFORE")
 bpy.ops.object.select_all(action="DESELECT")
 ear=ears[0];ear.select_set(True);bpy.context.view_layer.objects.active=ear
 # Preserve separate objects; hide other items only from viewport during stroke.
 hidden={o.name:o.hide_get() for o in objects if o!=ear and o.type in {"MESH","CURVE"}}
 for n in hidden:objects[n].hide_set(True)
 bpy.ops.object.mode_set(mode="SCULPT")
 c=viewport()
 with bpy.context.temp_override(**c):
  act=bpy.ops.brush.asset_activate(asset_library_type="ESSENTIALS",
      relative_asset_identifier="brushes/essentials_brushes-mesh_sculpt.blend/Brush/Grab")
 assert "FINISHED" in act,act
 brush=bpy.context.tool_settings.sculpt.brush
 assert brush and brush.name=="Grab","Wrong native asset"
 brush.size=SIZE;brush.strength=STRENGTH
 bpy.ops.ed.undo_push()
 bpy.ops.object.mode_set(mode="OBJECT");bpy.ops.object.mode_set(mode="SCULPT")
 c=viewport();reg=c["region"];rv=c["area"].spaces.active.region_3d
 a=location_3d_to_region_2d(reg,rv,ORIGIN)
 b=location_3d_to_region_2d(reg,rv,END)
 status["viewport_projection"]={"region_wh":[reg.width,reg.height],
   "from_xy":None if a is None else list(a),"to_xy":None if b is None else list(b),
   "pixel_stroke_length":None if a is None or b is None else math.dist(tuple(a),tuple(b)),
   "region_view_distance":float(rv.view_distance),
   "zoom_outcome":"SOURCE_DIAGNOSTIC_PRE_STROKE_ONLY"}
 if a is None or b is None:raise RuntimeError("Contour target off front sculpt screen")
 assert 0.08*reg.width<a.x<.92*reg.width and .08*reg.height<a.y<.92*reg.height,("Anchor outside usable viewport",status["viewport_projection"])
 # The background RegionView3D projection matrix demonstrably stays stale after
 # view_distance updates (run 44491671456: both distances projected 13.200784px).
 # Keep Blender's *actual* point a and direction toward b for native raycast;
 # calibrate only the 2D mouse path length without changing the guarded model.
 native_target=a+(b-a)*PIXEL_STROKE_CALIBRATION
 status["viewport_projection"]["calibrated_to_xy"]=list(native_target)
 status["viewport_projection"]["calibrated_length_px"]=math.dist(tuple(a),tuple(native_target))
 assert math.dist(tuple(a),tuple(native_target))>15,("Calibrated contour motion still too short",status["viewport_projection"])
 assert 0.08*reg.width<native_target.x<.92*reg.width and .08*reg.height<native_target.y<.92*reg.height
 stroke=[]
 for i in range(EVENTS):
  t=i/(EVENTS-1)
  xy=a.lerp(native_target,t)
  local_target=ear.matrix_world.inverted() @ ORIGIN.lerp(END,t)
  stroke.append(dict(name="stroke",mouse=(float(xy.x),float(xy.y)),
      mouse_event=(int(xy.x),int(xy.y)),
      location=tuple(float(v) for v in local_target),is_start=i==0,pressure=1.0,time=1.+i/60.0,
      size=1.,x_tilt=0.,y_tilt=0.))
 with bpy.context.temp_override(**c):
  assert bpy.ops.sculpt.brush_stroke.poll(),"Native Grab brush operator cannot poll"
  result=bpy.ops.sculpt.brush_stroke(stroke=stroke,override_location=False)
 assert "FINISHED" in result,result
 bpy.ops.object.mode_set(mode="OBJECT")
 for n,v in hidden.items():objects[n].hide_set(v)
 bpy.context.view_layer.update()
 actual=[ears[0].matrix_world@v.co for v in ears[0].data.vertices]
 displacement=[(b-a).length for a,b in zip(world_before,actual)]
 change=[b-a for a,b in zip(world_before,actual)]
 moved=[i for i,d in enumerate(displacement) if d>1e-7]
 # Preserve head-side base region; measure in WORLD coordinates.
 root=[i for i,p in enumerate(world_before) if p.y > -0.80]
 rootmax=max([displacement[i] for i in root],default=0)
 peak=max(displacement)
 max_y_out=max([-change[i].y for i in moved],default=0)
 max_z_up=max([change[i].z for i in moved],default=0)
 volume_delta_pct=(measure(ear)["volume"]/before[NEAR]["volume"]-1)*100
 status["stroke_actual"]={"asset":brush.name,"operator":"bpy.ops.sculpt.brush_stroke",
     "native_location_source":"EXPLICIT_LOCAL_MESH_COORDINATES",
     "override_location":False,"stroke_local_from":list(stroke[0]["location"]),
     "stroke_local_to":list(stroke[-1]["location"]),
     "events":len(stroke),"screen_from_xy":[float(x) for x in a],
     "screen_to_xy":[float(x) for x in b],"moved_near_ear_vertices":len(moved),
     "peak_displacement":peak,"root_near_head_max_displacement":rootmax,
     "max_outward_y_movement":max_y_out,"max_upper_z_movement":max_z_up,
     "near_ear_volume_change_pct":volume_delta_pct}
 assert len(moved)>=8,"Native Grab ran but did not move the intended shape"
 assert len(moved)<len(actual)*.85,"Not a localized shape move"
 assert peak < MAX_DISP,"Grab distortion too large"
 assert rootmax<ROOT_SAFE_MAX,"Ear root displaced too far"
 assert max_y_out>0.025 and max_z_up>0.012,"Contour did not flare outward+upwards"
 assert abs(volume_delta_pct)<VOL_ABS_PERCENT_MAX,"Unexpected volume distortion"
 # Local native sculpt on NEAR; mirror to FAR by copying owned mesh data only.
 # V074 already proves local coordinate symmetry and world mirror placement.
 ears[1].data=ears[0].data.copy()
 bpy.context.view_layer.update()
 assert ears[0].data!=ears[1].data and mesh_hash(ears[0])==mesh_hash(ears[1])
 near_y=sorted((ears[0].matrix_world@v.co).y for v in ears[0].data.vertices)
 far_y=sorted((ears[1].matrix_world@v.co).y for v in ears[1].data.vertices)
 mirror_error=max(abs(p+q) for p,q in zip(near_y,reversed(far_y)))
 status["world_mirror_max_error"]=mirror_error
 assert mirror_error<MIRROR_TOL,"Sculpt ruined paired ear symmetry"
 head_bvh=bvh(objects["04_HEAD"])
 crosses={o.name:len(head_bvh.overlap(bvh(o))) for o in ears}
 status["ear_to_head_intersections_after"]=crosses
 assert all(n>0 for n in crosses.values()),"Native Grab cut away root head contact"
 assert sorted(o.name for o in objects)==original_objs
 assert all(other_fingerprint(objects[n])==h for n,h in untouched.items()),"Unrelated mesh or curve changed"
 assert packed=={im.name:tuple(im.size) for im in bpy.data.images if im.packed_file}
 assert all(before[n]["vertices"]==len(objects[n].data.vertices) for n in [NEAR,FAR])
 assert all(before[n]["faces"]==len(objects[n].data.polygons) for n in [NEAR,FAR])
 status["all_others_unchanged"]=True;status["three_packed_refs_unchanged"]=True
 status["after"]={n:measure(objects[n]) for n in [NEAR,FAR]}
 status["after_renders"]=renders("AFTER")
 for o in ears:
  o["stage"]="V075_REAL_GRAB_EAR_CONTOUR_CANDIDATE_ART_HOLD"
  o["native_brush"]="Grab"
 dest=(OUT/"V075_REAL_GRAB_EAR_CONTOUR_CANDIDATE.blend").resolve()
 bpy.ops.wm.save_as_mainfile(filepath=str(dest))
 status["result_blend_sha256"]=sha(dest)
 status["status"]="NATIVE_ACTUAL_GRAB_BRUSH_SCOPED_TECH_PASS; FOUR_VIEW_SELF_ART_PENDING; ART_HOLD"
except Exception as e:
 status["status"]="FAILED_OR_SOURCE_HOLD";status["error"]=repr(e)
finally:
 (OUT/"V075_GENUINE_GRAB_EAR_RECEIPT.json").write_text(json.dumps(status,ensure_ascii=False,indent=2)+"\n")
 print("V075_NATIVE_GRAB_EAR",json.dumps({k:status.get(k) for k in ("status","error","stroke_actual","world_mirror_max_error","ear_to_head_intersections_after")},ensure_ascii=False),flush=True)
if status["status"].startswith("FAILED"):sys.exit(75)
