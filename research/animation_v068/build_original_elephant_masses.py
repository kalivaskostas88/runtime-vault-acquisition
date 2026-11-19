# SPDX-License-Identifier: GPL-2.0-or-later
"""V068 original first artistic blockout from real 3-view CC0 photography.
Teacher method: Julien Kaspar, Blender Fundamentals 4.5 LTS Basic Sculpting
and Sculpting Multiple Objects: silhouette first, primitive masses, low density,
apply scale, inspect multiangle, postpone all detail.
Reference: Greg Zaal, Poly Haven carved_wooden_elephant CC0.
No third-party mesh/geometry is imported. NOT ART_APPROVED, NOT a finished sculpt.
"""
import bpy,math,json,pathlib,hashlib,sys
from mathutils import Vector
OUT=pathlib.Path("v068_blockout");OUT.mkdir(parents=True,exist_ok=True)
REF=pathlib.Path("v068_reference")
bpy.ops.wm.read_factory_settings(use_empty=True)
assert bpy.app.version_string.startswith("5.2.2"),bpy.app.version_string
STUDY={
  "source_teacher":"https://studio.blender.org/training/blender-fundamentals-45-lts/basic-sculpting/",
  "source_blockout":"https://studio.blender.org/training/blender-fundamentals-45-lts/using-multiple-objects/",
  "reference_cc0":"https://polyhaven.com/a/carved_wooden_elephant",
  "policy":"original primitive-only figurine blockout, CC0 photos as references; never import prebuilt mesh",
  "target":"small recognizable elephant toy 3D, low-resolution mass-only"
}
def mat():
    m=bpy.data.materials.new("Study clay, no textures")
    m.diffuse_color=(0.62,0.65,0.65,1)
    return m
clay=mat()
pieces=[]
def finish(o,n,kind):
    o.name=n
    o.data.materials.append(clay)
    bpy.context.view_layer.objects.active=o
    o.select_set(True)
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    o.select_set(False)
    o["stage"]="BLOCKOUT_NOT_FINAL"
    o["role"]=kind
    pieces.append(o)
    return o
def ellipsoid(n,pos,sc,segments=20,rings=12):
    bpy.ops.object.select_all(action="DESELECT")
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments,ring_count=rings,location=pos)
    o=bpy.context.object;o.scale=sc
    return finish(o,n,"LOW_POLY_PRIMARY_VOLUME")
def foot(n,x,y,base_radius=0.43,z=0.86):
    bpy.ops.object.select_all(action="DESELECT")
    bpy.ops.mesh.primitive_cone_add(vertices=12,radius1=base_radius,radius2=base_radius*0.74,
        depth=1.72,location=(x,y,z))
    return finish(bpy.context.object,n,"LOW_POLY_WEIGHT_BEARING_LEG")
# Long axis X; elephant looks toward NEGATIVE X. Y is lateral width.
ellipsoid("01_BARREL_BODY",(0.30,0,2.27),(1.56,0.85,1.00))
ellipsoid("02_CHEST_SHOULDER",(-0.67,0,2.30),(0.74,0.83,0.96))
ellipsoid("03_BACK_RUMP",(1.24,0,2.35),(0.72,0.79,0.88))
ellipsoid("04_HEAD",(-1.42,0,2.70),(0.76,0.67,0.75))
ellipsoid("05_MUZZLE_ROOT",(-1.89,0,2.52),(0.44,0.48,0.46),16,10)
# Side-profile of broad ears is important; flat geometry oriented in X/Z plane.
for sign,label in ((-1,"NEAR"),(1,"FAR")):
    ellipsoid(f"06_EAR_{label}",(-1.07,sign*0.71,2.88),(0.50,0.14,0.67),18,12)
# Stagger four feet slightly along X so separate forms read in profile.
for x,side,name in [(-0.79,-0.53,"FRONT_NEAR"),(-0.60,0.53,"FRONT_FAR"),(1.34,-0.52,"REAR_NEAR"),(1.15,0.52,"REAR_FAR")]:
    foot("07_LEG_"+name,x,side,base_radius=0.42,z=0.86)
# Native CURVE is an original low-poly base for the trunk; not procedural copying of source mesh.
# Curve points form an inverted small 'C' with an upward curled tip, visibly attached to muzzle.
def trunk():
    c=bpy.data.curves.new("TRUNK_BROAD_MASS_CURVE","CURVE")
    c.dimensions="3D";c.resolution_u=12;c.bevel_depth=0.205;c.bevel_resolution=2
    c.use_fill_caps=True
    spline=c.splines.new("BEZIER")
    pts=[
      ((-2.04,0,2.55),1.33),((-2.33,0,2.29),1.18),
      ((-2.58,0,2.13),1.02),((-2.80,0,2.38),0.92),
      ((-2.89,0,2.79),0.80),((-2.82,0,3.20),0.64),
      ((-2.60,0,3.43),0.55)
    ]
    spline.bezier_points.add(len(pts)-1)
    for p,(xyz,radius) in zip(spline.bezier_points,pts):
        p.co=xyz;p.radius=radius;p.handle_left_type="AUTO";p.handle_right_type="AUTO"
    ob=bpy.data.objects.new("08_TRUNK_UPWARD_CURVE",c)
    bpy.context.collection.objects.link(ob)
    c.materials.append(clay);ob["stage"]="BLOCKOUT_NOT_FINAL";ob["role"]="ONE_BROAD_CURVED_BASE_MASS"
    pieces.append(ob)
trunk()
# Tail is a separate low density small mass: only silhouette, no details.
def tail():
    c=bpy.data.curves.new("TAIL_BROAD_BASE","CURVE");c.dimensions="3D"
    c.resolution_u=8;c.bevel_depth=0.08;c.bevel_resolution=2;c.use_fill_caps=True
    s=c.splines.new("BEZIER");s.bezier_points.add(2)
    pts=[(1.80,0,2.60),(2.12,0,1.94),(2.12,0,1.36)]
    for p,xyz in zip(s.bezier_points,pts):
        p.co=xyz;p.handle_left_type="AUTO";p.handle_right_type="AUTO"
    ob=bpy.data.objects.new("09_TAIL_PLACEHOLDER",c)
    bpy.context.collection.objects.link(ob);c.materials.append(clay)
    ob["stage"]="BLOCKOUT_NOT_FINAL";pieces.append(ob)
tail()
# Load all original CC0 photographic reference images and PACK them into .blend.
ref_metadata={}
for name in ("orth_front","orth_side","orth_top"):
    src=REF/(name+".png")
    assert src.is_file(),f"Missing true third-party CC0 visual reference: {src}"
    data=src.read_bytes()
    sha=hashlib.sha256(data).hexdigest()
    img=bpy.data.images.load(str(src),check_existing=False);img.pack()
    e=bpy.data.objects.new("REFERENCE_CC0_"+name,None)
    bpy.context.collection.objects.link(e)
    e.empty_display_type="IMAGE";e.data=img
    e.empty_display_size=5.9
    e.hide_render=True
    e.show_in_front=False
    if name=="orth_front":
        e.rotation_euler=(math.pi/2,0,0);e.location=(0,3.0,1.85)
    elif name=="orth_side":
        e.rotation_euler=(math.pi/2,0,math.pi/2);e.location=(3.3,0,1.85)
    else:
        e.location=(0,0,-0.7)
    e.hide_set(True) # available in viewport through Outliner; hidden for clay-view clarity
    ref_metadata[name]={"sha256":sha,"image_px":img.size[:],"packed":True}
# Four cameras from real 3D scene with one shared mesh collection.
s=bpy.context.scene
s.render.engine="BLENDER_WORKBENCH"
s.render.resolution_x=650;s.render.resolution_y=650;s.render.resolution_percentage=100
s.render.image_settings.file_format="PNG"
s.display.shading.light="STUDIO"
s.display.shading.color_type="SINGLE"
s.display.shading.single_color=(0.65,0.68,0.70)
s.render.film_transparent=False
bpy.ops.object.camera_add()
camera=bpy.context.object;camera.name="REVIEW_CAMERA"
s.camera=camera;camera.data.type="ORTHO";camera.data.ortho_scale=6.8
views={
    "SIDE":(0,-9,3.0),
    "FACE":(-9,0,3.0),
    "THREE_QUARTER":(-7,-8,5.0),
    "TOP":(0,-0.3,11)
}
target=Vector((-.25,0,1.89))
for name,pos in views.items():
    camera.location=Vector(pos)
    camera.rotation_euler=(target-camera.location).to_track_quat("-Z","Y").to_euler()
    s.render.filepath=str((OUT/(name+".png")).resolve())
    bpy.ops.render.render(write_still=True)
    assert (OUT/(name+".png")).stat().st_size>2000
# Don't make up visual-art approval. Verify component count and physical ground contact.
native=[o for o in bpy.data.objects if o.get("stage")=="BLOCKOUT_NOT_FINAL"]
legs=[o for o in native if o.name.startswith("07_LEG_")]
assert len(legs)==4
assert all(o.type=="MESH" for o in legs)
assert all(abs((o.location.z-o.dimensions.z/2))<.001 for o in legs),"Legs no longer touch ground"
assert len([o for o in native if o.name.startswith("06_EAR_")])==2
assert len(native)>=12
assert all(max(abs(a-1) for a in o.scale)<1e-6 for o in native if o.type=="MESH"),"Scale not applied"
bpy.ops.wm.save_as_mainfile(filepath=str((OUT/"V068_ELEPHANT_MASS_BLOCKOUT.blend").resolve()))
report={"schema":"V068_ORIGINAL_ELEPHANT_FIGURINE_BLOCKOUT",
    "blender_version":bpy.app.version_string,"teacher_first":STUDY,
    "reference_image_evidence":ref_metadata,
    "source_3d_mesh_imported":False,
    "art_stage":"FIRST_BLOCKOUT_ONLY","full_art_approval":False,
    "native_component_count":len(native),"four_legs_grounded":True,
    "symmetric_ear_pieces":True,"all_mesh_scales_applied":True,
    "rendered_views":list(views),
    "original_3d_asset_components":[{"name":o.name,"type":o.type,"role":o.get("role","BLOCKOUT"),
      "dimensions":[round(v,4) for v in o.dimensions]} for o in native],
    "qa_state":"GEOMETRY_FILE_RENDER_PASS; ART_SILHOUETTE_REVIEW_REQUIRED; ART_HOLD",
    "render_sha256":{(name+".png"):hashlib.sha256((OUT/(name+".png")).read_bytes()).hexdigest() for name in views}}
(OUT/"V068_BLOCKOUT_BUILD_RECEIPT.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
print("V068_REAL_BLOCKOUT",json.dumps(report,ensure_ascii=False),flush=True)
