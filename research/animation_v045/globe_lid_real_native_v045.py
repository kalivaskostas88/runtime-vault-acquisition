#!/usr/bin/env python3
"""V045: original Blender 5.2.2 *mechanical-only* globe/eyelid proximity fixture.
Teacher provenance: Julien Kaspar Blender Studio CC-BY V043 10:15–10:50 and 12:05–12:17.
This is an ORIGINAL parametric test, not a reconstruction of teacher's character.
NOT a full face, NOT artistic approval, NOT blinking/rigging, no production assets.
"""
import bpy,bmesh,sys,math,json,hashlib,traceback
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'native_v045';OUT.mkdir(exist_ok=True)
RADIUS=.70
GAP=.023
THICK=.027
CENTER_X=.94
CZ=.34
NX=101
NV=6
SIDES=(-1,1)
STATUS={"study":"V045_NATIVE_ORIGINAL_GLOBE_LID_CONFORMANCE_SCOPE","source":"Kaspar V043 full original educational lesson, sampled AV and official transcript","source_timecodes":["10:15-10:50","12:05-12:17"],"protection":"GS001_UNTOUCHED","art":"HOLD","reference_sheet":"NOT_APPROVED","native":"NOT_RUN","blink":"NOT_RUN","retopo":"NOT_RUN","integration":"NOT_RUN","cross_backend":"NOT_RUN","fixed_mechanical_limits":{"gap_target":GAP,"gap_tolerance":.002,"floating_max":.060,"penetration_min":-.002},"expected_images":4,"blender":"5.2.2"}
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def globe(side):
 c=Vector((side*CENTER_X,0,CZ))
 bpy.ops.mesh.primitive_uv_sphere_add(segments=64,ring_count=40,radius=RADIUS,location=c)
 o=bpy.context.object;o.name='V045.Globe.'+('L' if side==-1 else 'R')
 o["radius"]=RADIUS;o["side"]=side
 return o
def lid_mesh(side,upper):
 # Original globe-conforming inner eyelid margin; extents define a narrow outer tissue band.
 # Back margin sits GAP outside the true globe. No arbitrary eyeball intersections.
 nm=('UPPER' if upper else 'LOWER')+'.'+('L' if side==-1 else 'R')
 c=Vector((side*CENTER_X,0,CZ))
 verts=[]
 for layer in (0,1):     # back (closest to sphere), front (outer tissue)
  for j in range(NV):
   v=j/(NV-1)
   for i in range(NX):
    u=2*i/(NX-1)-1
    xx=.575*u*(1+.055*v)
    aperture=math.sqrt(max(0.,1-u*u))
    baseline=(.205 if upper else -.167)*aperture
    zz=baseline+(1 if upper else -1)*(.195*v)
    rn=RADIUS+GAP+(.09*v)+(THICK if layer==1 else 0.)
    if xx*xx+zz*zz >= rn*rn:
     raise AssertionError("invalid globe surface geometry")
    yy=-math.sqrt(rn*rn-xx*xx-zz*zz)
    verts.append((c.x+xx,c.y+yy,c.z+zz))
 def idx(layer,j,i):return layer*NV*NX+j*NX+i
 faces=[]
 for j in range(NV-1):
  for i in range(NX-1):
   a,b,c_,d=idx(1,j,i),idx(1,j,i+1),idx(1,j+1,i+1),idx(1,j+1,i)
   faces.append((a,b,c_,d))
   a,b,c_,d=idx(0,j,i),idx(0,j,i+1),idx(0,j+1,i+1),idx(0,j+1,i)
   faces.append((d,c_,b,a))
 for j in range(NV-1):
  for i in (0,NX-1):
   a,b=idx(0,j,i),idx(0,j+1,i)
   c_,d=idx(1,j+1,i),idx(1,j,i)
   faces.append((a,b,c_,d) if i==0 else (d,c_,b,a))
 for i in range(NX-1):
  for j in (0,NV-1):
   a,b=idx(0,j,i),idx(0,j,i+1)
   c_,d=idx(1,j,i+1),idx(1,j,i)
   faces.append((d,c_,b,a) if j==0 else (a,b,c_,d))
 mesh=bpy.data.meshes.new('V045.'+nm+'.closed.shell');mesh.from_pydata(verts,[],faces);mesh.update()
 o=bpy.data.objects.new('V045.Lid.'+nm,mesh);bpy.context.collection.objects.link(o)
 o['lid_side']=side;o['lid_upper']=bool(upper);o['margin_vertices']=NX;o['margin_gap']=GAP
 # A mesh with non-zero thickness and topologically closed manifold, but NOT integrated with head.
 return o
def topo(o):
 bm=bmesh.new();bm.from_mesh(o.data);edges=len(bm.edges)
 out={"vertices":len(bm.verts),"faces":len(bm.faces),"boundary":sum(e.is_boundary for e in bm.edges),"nonmanifold":sum(not e.is_manifold for e in bm.edges)}
 bm.free();return out
def audit(globes,lids):
 # This tests *actual native mesh margin vertices*, not the constructor's abstract formula.
 rows=[];all_gaps=[]
 for side,up,lid in lids:
  center=Vector(globes[side].location)
  # layer 0, radial band j=0, all 101 margin vertices
  distances=[((lid.matrix_world @ lid.data.vertices[i].co)-center).length-RADIUS for i in range(NX)]
  all_gaps+=distances
  rows.append({"side":side,"upper":up,"min":min(distances),"max":max(distances),"mean":sum(distances)/NX,"topology":topo(lid),"samples":len(distances)})
 return rows,all_gaps
def assertion(rows,gaps):
 return len(rows)==4 and len(gaps)==4*NX and all(abs(x-GAP)<=.002 for x in gaps) and all(
  q["topology"]["boundary"]==0 and q["topology"]["nonmanifold"]==0 for q in rows)
def negative_controls(globes,lids):
 # Probe invalid mesh placements *on copied actual mesh objects*, preserve original geometry.
 negatives={}
 originals={id(lid):lid.location.copy() for _,_,lid in lids}
 def probe(label, selection,dy):
  for _,_,obj in selection:obj.location.y+=dy
  rows,gaps=audit(globes,lids)
  negatives[label]={"rejected":not assertion(rows,gaps),"min_gap":min(gaps),"max_gap":max(gaps)}
  for _,_,obj in selection:obj.location.y-=dy
 probe("FLOATING_LID_FORWARD",lids,-.16)
 probe("PENETRATING_LID_BACK",lids,.18)
 probe("ASYMMETRIC_ONE_EYE",[(s,u,o) for s,u,o in lids if s==1],-.12)
 assert all(v["rejected"] for v in negatives.values()),negatives
 return negatives
def mat(name,rgba):
 m=bpy.data.materials.new(name);m.diffuse_color=rgba;return m
def camera(scene,name,location,target):
 d=bpy.data.cameras.new(name);d.type="ORTHO";d.ortho_scale=3.9
 o=bpy.data.objects.new("Camera."+name,d);scene.collection.objects.link(o)
 o.location=location;o.rotation_euler=(Vector(target)-o.location).to_track_quat("-Z","Y").to_euler()
 return o
try:
 assert tuple(bpy.app.version[:2])==(5,2),bpy.app.version_string
 bpy.ops.object.select_all(action="SELECT");bpy.ops.object.delete(use_global=False)
 assert not any("GS001" in o.name for o in bpy.data.objects)
 sc=bpy.context.scene;sc.render.engine="BLENDER_WORKBENCH";sc.render.resolution_x=660;sc.render.resolution_y=530;sc.render.resolution_percentage=100
 sc.render.image_settings.file_format="PNG";sc.display.shading.light="STUDIO";sc.display.shading.color_type="MATERIAL";sc.display.shading.show_cavity=True
 globe_mat=mat("V045.Globe.White.NotFinal",(0.83,0.87,0.9,1))
 upper_mat=mat("V045.Lid.Upper.Coral.NotFinal",(0.8,.44,.41,1))
 lower_mat=mat("V045.Lid.Lower.Coral.NotFinal",(0.64,.34,.34,1))
 globes={s:globe(s) for s in SIDES}
 lids=[(s,u,lid_mesh(s,u)) for s in SIDES for u in (True,False)]
 for x in globes.values():x.data.materials.append(globe_mat)
 for _,u,x in lids:x.data.materials.append(upper_mat if u else lower_mat)
 for o in list(globes.values())+[q[2] for q in lids]:
  for p in o.data.polygons:p.use_smooth=True
 rows,gaps=audit(globes,lids);STATUS["geometry"]={"all_globe_count":len(globes),"lid_count":len(lids),"margin_samples":len(gaps),"gap_min":min(gaps),"gap_max":max(gaps),"gap_mean":sum(gaps)/len(gaps),"lid_data":rows,"all_globe_radius":RADIUS,"thickness":THICK}
 STATUS["negative_controls"]=negative_controls(globes,lids)
 assert assertion(rows,gaps),"V045 margin conformance native mesh gate failed"
 cameras=[camera(sc,"FRONT",(0,-5,.4),(0,0,.34)),camera(sc,"THREE_QUARTER",(3.0,-4.3,1.4),(0,0,.34)),
  camera(sc,"TRUE_SIDE",(5,-0.08,.4),(.94,0,.34)),camera(sc,"LOW",(0,-4,-1.3),(0,0,.34))]
 imgs=[]
 for c in cameras:
  sc.camera=c;p=OUT/("V045_"+c.data.name+".png");sc.render.filepath=str(p);bpy.ops.render.render(write_still=True)
  if p.stat().st_size<10000:raise AssertionError("image missing or short "+str(p))
  imgs.append({"name":p.name,"sha256":sha(p),"bytes":p.stat().st_size})
 STATUS["images"]=imgs
 blend=OUT/"V045_GLOBE_LID_ORIGINAL_TEST_FIXTURE.blend";bpy.ops.wm.save_as_mainfile(filepath=str(blend))
 STATUS["blend"]={"name":blend.name,"sha256":sha(blend),"bytes":blend.stat().st_size}
 STATUS["native"]="NATIVE_GLOBE_LID_MARGIN_PROXIMITY_PASS"
except BaseException as exc:
 STATUS["native"]="HOLD_OR_FAILURE";STATUS["error"]=type(exc).__name__+": "+str(exc)[:400]
 traceback.print_exc()
finally:
 (OUT/"RECEIPT.json").write_text(json.dumps(STATUS,indent=2,ensure_ascii=False)+"\n")
 print("V045_NATIVE_RECEIPT",json.dumps({"native":STATUS["native"],"geometry":STATUS.get("geometry",{}),"negative":STATUS.get("negative_controls",{}),"error":STATUS.get("error")},ensure_ascii=False)[:9000],flush=True)
if STATUS["native"]!="NATIVE_GLOBE_LID_MARGIN_PROXIMITY_PASS":sys.exit(45)
