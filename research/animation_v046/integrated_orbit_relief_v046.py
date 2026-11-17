#!/usr/bin/env python3
"""V046 original continuous facial *broad tissue* orbital-relief native experiment.
Exact original V039 parametric closed head mesh; V043 Julien Kaspar source-led
decision: broad head/proportions and organic tissue relationship first.
One treatment: local C2 supported orbital supra/infra relief on same head
mesh vs identical no-relief control; both use same 2 Boolean cutouts and eyeballs.
NO art-approved design, NO eyelid margin implementation, retopo, acting or GS001.
"""
import bpy,bmesh,sys,math,json,hashlib,traceback
from mathutils import Vector
from pathlib import Path
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE.parent/"animation_v039"))
from original_head_geometry_v039 import build,audit as original_audit
OUT=HERE/"native_v046";OUT.mkdir(exist_ok=True)
PARAM={"upper_z":.71,"lower_z":.145,"upper_a":.103,"lower_a":.080,
       "x_centers":[-.44,.44],"cut_y":-.92,"cut_z":.43,
       "cut_radii":[.305,.40,.22],"globe_center_y":-.66,"globe_r":.245,
       "one_relief_variable":"add paired upper and lower broad flesh volumes to original head"}
R={"version":"V046","source":"Kaspar original full CC-BY V043 10:15–12:17; Blender Studio professional tissue/brow advice; original independent V039 head",
 "method":"SAME_ORIGINAL_CONNECTED_HEAD_MESH_ORBITAL_RELIEF_NOT_FINISHED_EYELIDS",
 "GS001":"UNTOUCHED","art":"HOLD","design_four_view":"NOT_APPROVED","native":"NOT_RUN",
 "rig":"NOT_RUN","blink":"NOT_RUN","retopo":"NOT_RUN","cross_backend":"NOT_RUN",
 "input_original":"V039 original parametric head source, not V040B historical saved artifact",
 "variable":PARAM["one_relief_variable"],"params":PARAM}
def sha(p):
 h=hashlib.sha256()
 with open(p,"rb") as f:
  for c in iter(lambda:f.read(1024*1024),b""):h.update(c)
 return h.hexdigest()
def bump(x,z,cx,cz,wx,wz,amplitude):
 t=1-((x-cx)/wx)**2-((z-cz)/wz)**2
 return amplitude*max(0.,t)**2
def local_delta(x,y,z):
 # Only front-facing surface, compact support; creates volumetric tissue, not eyelid strips.
 if y>=-.16:return 0.
 return sum(bump(x,z,cx,.71,.39,.24,-.103) +
            bump(x,z,cx,.145,.38,.25,-.080) for cx in PARAM["x_centers"])
def mesh_from_original(name,relief):
 v,f=build();effects=[]
 if relief:
  changed=[]
  for i,(x,y,z) in enumerate(v):
   d=local_delta(x,y,z)
   effects.append(d)
   v[i]=(x,y+d,z)
   if abs(d)>1e-8:changed.append(i)
 else:effects=[0.]*len(v)
 mesh=bpy.data.meshes.new(name+".mesh");mesh.from_pydata(v,[],f);mesh.update()
 ob=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(ob)
 for p in ob.data.polygons:p.use_smooth=True
 return ob,effects
def topology(o):
 bm=bmesh.new();bm.from_mesh(o.data)
 bm.verts.ensure_lookup_table();bm.verts.index_update()
 graph=[[] for _ in bm.verts]
 for e in bm.edges:
  a,b=e.verts[0].index,e.verts[1].index
  graph[a].append(b);graph[b].append(a)
 seen=set();parts=0
 for i in range(len(bm.verts)):
  if i in seen:continue
  parts+=1;seen.add(i);q=[i]
  while q:
   for nxt in graph[q.pop()]:
    if nxt not in seen:seen.add(nxt);q.append(nxt)
 d={"vertices":len(bm.verts),"faces":len(bm.faces),
    "boundary":sum(e.is_boundary for e in bm.edges),
    "nonmanifold":sum(not e.is_manifold for e in bm.edges),
    "components":parts,"signed_volume":bm.calc_volume(signed=True)}
 bm.free();return d
def check_relief(effects,source):
 pos=[];upper=0;lower=0;remote=0
 for idx,(p,d) in enumerate(zip(source,effects)):
  x,y,z=p
  if abs(d)>1e-6:
   pos.append(idx)
   if z>.41:upper+=1
   if z<.41:lower+=1
   if abs(x)>.92 or z>1.05 or z<-.26 or y>-.16:remote+=1
 return {"modified":len(pos),"upper":upper,"lower":lower,"remote":remote,"min_displacement":min(effects),"max_displacement":max(effects)}
def close_geometry(geom):
 return geom["boundary"]==0 and geom["nonmanifold"]==0 and geom["components"]==1
def check_cutter_configuration(op,solver):
 if op!="DIFFERENCE" or solver!="EXACT":raise ValueError("SAFE_EXACT_DIFFERENCE_REQUIRED")
def bool_cut(head,side):
 x=side*.44
 bpy.ops.mesh.primitive_uv_sphere_add(segments=64,ring_count=32,location=(x,PARAM["cut_y"],PARAM["cut_z"]))
 cutter=bpy.context.object
 cutter.scale=tuple(PARAM["cut_radii"])
 bpy.context.view_layer.objects.active=cutter
 bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 bpy.ops.object.select_all(action='DESELECT');head.select_set(True);bpy.context.view_layer.objects.active=head
 modifier=head.modifiers.new("V046.SOCKET."+str(side),"BOOLEAN")
 modifier.operation="DIFFERENCE";modifier.solver="EXACT";modifier.object=cutter
 check_cutter_configuration(modifier.operation,modifier.solver)
 bpy.ops.object.modifier_apply(modifier=modifier.name)
 bpy.data.objects.remove(cutter,do_unlink=True)
 head.select_set(False)
def ray(o,x,z):
 hit,loc,n,ix=o.ray_cast(Vector((x,-3,z)),Vector((0,1,0)),distance=8)
 if not hit:raise RuntimeError("NO_FRONT_HEAD_HIT:"+str((x,z)))
 return float(loc.y)
def create_globes():
 globes={}
 for s in (-1,1):
  bpy.ops.mesh.primitive_uv_sphere_add(segments=64,ring_count=40,radius=PARAM["globe_r"],location=(s*.44,PARAM["globe_center_y"],PARAM["cut_z"]))
  o=bpy.context.object;o.name="V046.Eye."+("L" if s<0 else "R")
  o["radius"]=PARAM["globe_r"]
  for p in o.data.polygons:p.use_smooth=True
  globes[s]=o
 return globes
def mat(name,c):
 m=bpy.data.materials.new(name);m.diffuse_color=c;return m
def camera(scene,name,loc,targ=(0,0,.03)):
 cam=bpy.data.cameras.new(name);cam.type="ORTHO";cam.ortho_scale=3.6
 ob=bpy.data.objects.new("Camera."+name,cam);scene.collection.objects.link(ob)
 ob.location=loc;ob.rotation_euler=(Vector(targ)-ob.location).to_track_quat('-Z','Y').to_euler()
 return ob
def snap(scene,cam,name):
 p=OUT/name;scene.camera=cam;scene.render.filepath=str(p)
 bpy.ops.render.render(write_still=True)
 assert p.exists() and p.stat().st_size>13000,name
 return {"name":p.name,"sha256":sha(p),"bytes":p.stat().st_size}
try:
 assert tuple(bpy.app.version[:2])==(5,2),bpy.app.version_string
 bpy.ops.object.select_all(action="SELECT");bpy.ops.object.delete(use_global=False)
 assert original_audit()["all_edges_two"] and original_audit()["boundary"]==0
 source=build()[0];base,del0=mesh_from_original("V046.Baseline.NoTissueRelief",False)
 treated,del1=mesh_from_original("V046.Treatment.CONTINUOUS.ORBITAL.SKIN",True)
 R["relief_before_cut"]=check_relief(del1,source)
 R["base_before_cut_topology"]=topology(base);R["treated_before_cut_topology"]=topology(treated)
 assert R["relief_before_cut"]["modified"]>70 and R["relief_before_cut"]["upper"]>10 and R["relief_before_cut"]["lower"]>10
 assert R["relief_before_cut"]["remote"]==0
 assert R["relief_before_cut"]["min_displacement"]<-.09
 assert close_geometry(R["treated_before_cut_topology"])
 # Native negative controls before modifying treatment: intentional wrong conditions rejected.
 corrupt=list(del1);remote_idx=next(i for i,p in enumerate(source) if abs(p[0])>.96 and p[2]<.4)
 corrupt[remote_idx]=-.1
 synthetic={"NEG_NO_POSITIVE_RELIEF":check_relief(del0,source)["modified"]==0,
            "NEG_REMOTE_UNAUTHORIZED_DELTA":check_relief(corrupt,source)["remote"]>0}
 try:check_cutter_configuration("UNION","EXACT")
 except ValueError:synthetic["NEG_WRONG_BOOLEAN_OPERATION"]=True
 else:synthetic["NEG_WRONG_BOOLEAN_OPERATION"]=False
 try:check_cutter_configuration("DIFFERENCE","FLOAT")
 except ValueError:synthetic["NEG_WRONG_BOOLEAN_SOLVER"]=True
 else:synthetic["NEG_WRONG_BOOLEAN_SOLVER"]=False
 assert all(synthetic.values())
 R["preflight_negative_controls"]=synthetic
 # both same identical apertures, only changed treatment is organically continuous facial relief
 for side in (-1,1):
  bool_cut(base,side);bool_cut(treated,side)
 R["baseline_topology"]=topology(base);R["treatment_topology"]=topology(treated)
 assert close_geometry(R["baseline_topology"]) and close_geometry(R["treatment_topology"])
 # Compare real Boolean head shapes at fixed exposed broad-skin landmarks and unchanged controls.
 probe=[("upper_L",-.44,.79),("upper_R",.44,.79),
        ("lower_L",-.44,.085),("lower_R",.44,.085),
        ("socket_center_L",-.44,.43),("socket_center_R",.44,.43),
        ("remote_forehead",0,1.12),("remote_jaw",0,-.83),("remote_temple",.88,.1)]
 diff=[]
 for label,x,z in probe:
  ya,yb=ray(base,x,z),ray(treated,x,z)
  diff.append({"label":label,"x":x,"z":z,"baseline_y":ya,"treated_y":yb,"forward_relief_delta":yb-ya})
 R["actual_raycast_comparison"]=diff
 byname={q["label"]:q["forward_relief_delta"] for q in diff}
 assert all(byname["upper_"+s]<-.018 and byname["lower_"+s]<-.012 for s in ("L","R")),byname
 assert all(abs(byname[k])<.00003 for k in ("remote_forehead","remote_jaw","remote_temple")),byname
 # New geometry specifically must be on same one head mesh, no separate "lid ribbons".
 assert len([ob for ob in bpy.data.objects if "Lid" in ob.name])==0
 # Create same two eyeballs for before and after baseline visual comparisons.
 globes=create_globes()
 sym_ok=abs(globes[-1].location.y-globes[1].location.y)<1e-7
 assert sym_ok
 globes[1].location.y-=.11
 bpy.context.view_layer.update()
 false_sym_detected=abs(globes[-1].matrix_world.translation.y-globes[1].matrix_world.translation.y)>.09
 globes[1].location.y+=.11;bpy.context.view_layer.update()
 assert false_sym_detected
 R["native_geometry_negative_control"]={"asymmetrically_displaced_globe_rejected":false_sym_detected}
 scene=bpy.context.scene;scene.render.engine="BLENDER_WORKBENCH"
 scene.render.resolution_x=660;scene.render.resolution_y=660;scene.render.resolution_percentage=100
 scene.render.image_settings.file_format="PNG"
 scene.display.shading.light="STUDIO";scene.display.shading.color_type="MATERIAL"
 scene.display.shading.show_shadows=True;scene.display.shading.show_cavity=True;scene.display.shading.cavity_type="BOTH"
 skin=mat("V046.Skin.Tan.Provisional",(0.66,.49,.39,1));eye=mat("V046.Globe.Grey",(0.87,.88,.91,1))
 base.data.materials.append(skin);treated.data.materials.append(skin)
 for obj in globes.values():obj.data.materials.append(eye)
 cams=[camera(scene,"FRONT",(0,-5.8,.3)),camera(scene,"THREE_QUARTER",(3.5,-4.6,.35)),
       camera(scene,"TRUE_PROFILE",(6,-.03,.3)),camera(scene,"LOW",(0,-5,-1.7))]
 base.hide_render=False;treated.hide_render=True
 R["baseline_renders"]=[snap(scene,c,"BASE_"+c.data.name+".png") for c in cams]
 base.hide_render=True;treated.hide_render=False
 R["treatment_renders"]=[snap(scene,c,"TREAT_"+c.data.name+".png") for c in cams]
 file=OUT/"V046_CONTINUOUS_TISSUE_EXPERIMENT.blend"
 bpy.ops.wm.save_as_mainfile(filepath=str(file))
 R["blend"]={"name":file.name,"sha256":sha(file),"bytes":file.stat().st_size}
 R["native"]="NATIVE_CONNECTED_ORBITAL_RELIEF_SCOPED_PASS"
except BaseException as e:
 R["native"]="HOLD_NATIVE_OR_QA";R["error"]=type(e).__name__+": "+str(e)[:600]
 traceback.print_exc()
finally:
 (OUT/"RECEIPT.json").write_text(json.dumps(R,indent=2,ensure_ascii=False)+"\n")
 print("V046_NATIVE_RECEIPT",json.dumps({k:R.get(k) for k in ("native","error","relief_before_cut","treatment_topology","actual_raycast_comparison","preflight_negative_controls")},ensure_ascii=False)[:6000],flush=True)
if R["native"]!="NATIVE_CONNECTED_ORBITAL_RELIEF_SCOPED_PASS":sys.exit(46)
