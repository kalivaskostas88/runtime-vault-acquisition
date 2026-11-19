# SPDX-License-Identifier: GPL-2.0-or-later
"""V072 native Blender sculpt Smooth on actual V071 voxel-fused elephant torso.
Teacher-first: Blender Studio Kaspar Basic Sculpting public written Smooth warning;
V064 real essential Smooth asset + Blender Foundation native stroke protocol.
One localized stroke with unchanged original, frozen controls, ART_HOLD.
"""
import bpy,bmesh,json,hashlib,math,sys,pathlib,struct
from mathutils import Vector
from bpy_extras.view3d_utils import location_3d_to_region_2d
OUT=pathlib.Path("v072_targeted_smooth");OUT.mkdir(exist_ok=True)
INPUT=pathlib.Path("v071_body_fusion/V071_THREE_BODY_FUSION_CANDIDATE.blend")
SOURCE_SHA="098b83455277022cab496f67e2ecf2959703c90e55f56a89bc8eae6534c4554d"
CORE="01_BARREL_BODY"
VIEW_TARGET=Vector((.12,0.,2.30))
STROKE_ANCHOR=Vector((-.55,-.75,2.48))
BRUSH_STRENGTH=0.30
BRUSH_SIZE=66
STROKE_EVENTS=51
VOLUME_LOSS_MAX_PCT=1.25
MAX_POINT_DISPLACEMENT=0.10
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def snap(o):
    m=o.data
    bm=bmesh.new();bm.from_mesh(m);vol=abs(bm.calc_volume(signed=True));bm.free()
    b=b"".join(struct.pack("<ddd",*map(float,v.co)) for v in m.vertices)
    return {"vertices":len(m.vertices),"faces":len(m.polygons),"volume":vol,
      "position_sha256":hashlib.sha256(b).hexdigest()}
def fingerprint(o):
    if o.type=="MESH":return snap(o)["position_sha256"]
    if o.type=="CURVE":return hashlib.sha256(str([(p.co[:],p.radius) for s in o.data.splines for p in s.bezier_points]).encode()).hexdigest()
    return None
def viewport():
    ctx=bpy.context.copy()
    for a in ctx["screen"].areas:
        if a.type=="VIEW_3D":
            r=next((x for x in a.regions if x.type=="WINDOW"),None)
            if r:
                ctx.update(area=a,region=r)
                sp=a.spaces.active;sp.region_3d.view_location=VIEW_TARGET
                sp.region_3d.view_distance=5.6
                # point viewport from true side, same original native orientation family
                sp.region_3d.view_rotation=(VIEW_TARGET-Vector((0.,-10.,3.0))).to_track_quat("-Z","Y")
                sp.region_3d.view_perspective="ORTHO"
                return ctx
    raise RuntimeError("No native VIEW_3D screen; never fake a sculpt stroke")
def pics(tag):
    sc=bpy.context.scene
    sc.render.engine="BLENDER_WORKBENCH"
    sc.render.resolution_x=650;sc.render.resolution_y=650;sc.render.resolution_percentage=100
    sc.render.image_settings.file_format="PNG"
    cam=sc.camera;assert cam is not None
    target=Vector((-.25,0,1.89))
    poses={"SIDE":(0,-9,3.0),"FACE":(-9,0,3.0),"THREE_QUARTER":(-7,-8,5.0),"TOP":(0,-.3,11)}
    hashes={}
    for view,coords in poses.items():
        cam.location=Vector(coords)
        cam.rotation_euler=(target-cam.location).to_track_quat("-Z","Y").to_euler()
        p=(OUT/(tag+"_"+view+".png")).resolve();sc.render.filepath=str(p)
        bpy.ops.render.render(write_still=True)
        assert p.stat().st_size>1000
        hashes[p.name]=sha(p)
    return hashes
status={"schema":"V072_TEACHER_LED_TORSO_SMOOTH_NATIVE_SMALL","source_sha_expected":SOURCE_SHA,
  "native_blender_version":"5.2.2","source_video_full_av":"NOT_CLAIMED",
  "professional_method":"Kaspar Blender Fundamentals 4.5 LTS Basic Sculpting/Smoothing public text; V064 proven native brush workflow",
  "controls_predeclared":{"strength":BRUSH_STRENGTH,"size":BRUSH_SIZE,"events":STROKE_EVENTS,
      "anchor":list(STROKE_ANCHOR),"max_absolute_vol_loss_percent":VOLUME_LOSS_MAX_PCT,
      "max_vertex_displacement":MAX_POINT_DISPLACEMENT},
  "status":"INIT","art_approved":False,"protected_assets_touched":False}
try:
    assert bpy.app.version_string.startswith("5.2.2")
    assert INPUT.is_file()
    assert sha(INPUT)==SOURCE_SHA,"Original candidate source mismatch"
    bpy.ops.wm.open_mainfile(filepath=str(INPUT.resolve()))
    o=bpy.data.objects[CORE]
    assert o.type=="MESH" and o.get("stage")=="RESEARCH_BODY_CORE_FUSION_NOT_ART_APPROVED"
    before=snap(o)
    assert before["vertices"]==7882,"unexpected source geometry"
    protected={x.name:fingerprint(x) for x in bpy.data.objects if x.name!=CORE and x.get("stage")=="BLOCKOUT_NOT_FINAL"}
    images={i.name:tuple(i.size) for i in bpy.data.images if i.packed_file}
    assert len(images)>=3
    initial=[v.co.copy() for v in o.data.vertices]
    status["before"]=before
    status["before_renders"]=pics("BEFORE")
    bpy.ops.object.select_all(action="DESELECT")
    o.select_set(True);bpy.context.view_layer.objects.active=o
    # Hide unrelated proxies from viewport only during brush: later restore, no data change.
    hidden={x.name:x.hide_get() for x in bpy.data.objects if x!=o and x.type in {"MESH","CURVE"}}
    for name in hidden:bpy.data.objects[name].hide_set(True)
    bpy.ops.object.mode_set(mode="SCULPT")
    v=viewport()
    with bpy.context.temp_override(**v):
        state=bpy.ops.brush.asset_activate(asset_library_type="ESSENTIALS",
            relative_asset_identifier="brushes/essentials_brushes-mesh_sculpt.blend/Brush/Smooth")
    assert "FINISHED" in state
    brush=bpy.context.tool_settings.sculpt.brush
    assert brush and brush.name=="Smooth"
    brush.strength=BRUSH_STRENGTH;brush.size=BRUSH_SIZE
    bpy.ops.ed.undo_push()
    bpy.ops.object.mode_set(mode="OBJECT");bpy.ops.object.mode_set(mode="SCULPT")
    v=viewport();reg=v["region"];rv=v["area"].spaces.active.region_3d
    xy=location_3d_to_region_2d(reg,rv,STROKE_ANCHOR)
    if xy is None:raise RuntimeError("Anchor projected behind view")
    w,h=reg.width,reg.height
    assert 0.15*w<xy.x<0.85*w and .15*h<xy.y<.85*h,("Bad projected anchor",list(xy),w,h)
    # A short single physical stroke across the barrel/chest interface:
    # fixed screen path; 51 event samples; no parameter hunting.
    events=[]
    for i in range(STROKE_EVENTS):
        t=i/(STROKE_EVENTS-1)
        sx=xy.x+(t-.5)*75
        sy=xy.y+math.sin(t*math.pi)*10
        events.append(dict(name="stroke",mouse=(sx,sy),mouse_event=(int(sx),int(sy)),
           location=(0.,0.,0.),is_start=i==0,pressure=1.,time=1.+i/60.,
           size=1.,x_tilt=0.,y_tilt=0.))
    with bpy.context.temp_override(**v):
        assert bpy.ops.sculpt.brush_stroke.poll()
        result=bpy.ops.sculpt.brush_stroke(stroke=events,override_location=True)
    assert "FINISHED" in result
    bpy.ops.object.mode_set(mode="OBJECT")
    for name,value in hidden.items():bpy.data.objects[name].hide_set(value)
    after=snap(o)
    disp=[(v.co-c).length for c,v in zip(initial,o.data.vertices)]
    moved=sum(d>1e-7 for d in disp)
    volume_loss=(before["volume"]-after["volume"])/before["volume"]*100
    assert after["vertices"]==before["vertices"] and after["faces"]==before["faces"]
    status.update({"after":after,"moved_vertices":moved,
       "max_displacement":max(disp),"volume_loss_percent":volume_loss,
       "projected_anchor_xy":[float(x) for x in xy],
       "native_operator":"bpy.ops.sculpt.brush_stroke","native_brush":"Smooth"})
    assert moved>20,"The brush did not actually sculpt"
    assert max(disp)<MAX_POINT_DISPLACEMENT,"Large deformation outside predeclared gate"
    assert -0.10<volume_loss<VOLUME_LOSS_MAX_PCT,"Volume change unsafe or unexpectedly growing"
    assert before["position_sha256"]!=after["position_sha256"]
    assert all(fingerprint(bpy.data.objects[name])==h for name,h in protected.items()),"Other artistic components changed"
    assert {i.name:tuple(i.size) for i in bpy.data.images if i.packed_file}==images
    status["after_renders"]=pics("AFTER")
    o["stage"]="V072_SMALL_NATIVE_SMOOTH_CANDIDATE_ART_HOLD"
    o["source_blend_sha256"]=SOURCE_SHA
    o["native_brush"]="Smooth"
    dest=(OUT/"V072_SMALL_SMOOTH_CANDIDATE.blend").resolve()
    bpy.ops.wm.save_as_mainfile(filepath=str(dest))
    status["saved_blend_sha256"]=sha(dest)
    status["status"]="NATIVE_TARGETED_SMOOTH_MECHANICAL_PASS; SELF_ART_QA_PENDING; ART_HOLD"
except Exception as e:
    status["status"]="FAILED_OR_SOURCE_HOLD";status["error"]=repr(e)
finally:
    (OUT/"V072_SCOPED_SMOOTH_RECEIPT.json").write_text(json.dumps(status,ensure_ascii=False,indent=2)+"\n")
    print("V072_REAL_NATIVE_SMOOTH",json.dumps({k:status.get(k) for k in ("status","error","moved_vertices","volume_loss_percent","max_displacement","native_operator")},ensure_ascii=False))
if status["status"].startswith("FAILED"):sys.exit(72)
