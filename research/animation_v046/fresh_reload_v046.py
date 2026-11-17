#!/usr/bin/env python3
"""V046 independent saved Blender run; actual unchanged baseline/treatment readback."""
import bpy,bmesh,json,hashlib,sys,traceback
from pathlib import Path
from mathutils import Vector
OUT=Path(__file__).resolve().parent/"native_v046"
R=json.loads((OUT/"RECEIPT.json").read_text())
Q={"version":"V046_NEW_BLENDER_PROCESS_SAVED_MODEL_AUDIT","status":"NOT_RUN","GS001":"UNTOUCHED","art":"HOLD"}
def sha(p):
 h=hashlib.sha256()
 with open(p,"rb") as f:
  for b in iter(lambda:f.read(1<<20),b""):h.update(b)
 return h.hexdigest()
def ray(o,x,z):
 ok,pos,n,idx=o.ray_cast(Vector((x,-3,z)),Vector((0,1,0)),distance=8)
 if not ok:raise AssertionError("MISS")
 return float(pos.y)
def topology(o):
 bm=bmesh.new();bm.from_mesh(o.data)
 bm.verts.ensure_lookup_table();bm.verts.index_update()
 adj=[[] for _ in bm.verts]
 for ed in bm.edges:
  a,b=ed.verts[0].index,ed.verts[1].index;adj[a].append(b);adj[b].append(a)
 visited=set();parts=0
 for i in range(len(bm.verts)):
  if i in visited:continue
  parts+=1;stack=[i];visited.add(i)
  while stack:
   for j in adj[stack.pop()]:
    if j not in visited:visited.add(j);stack.append(j)
 s={"vertices":len(bm.verts),"faces":len(bm.faces),"boundary":sum(e.is_boundary for e in bm.edges),"nonmanifold":sum(not e.is_manifold for e in bm.edges),"components":parts}
 bm.free();return s
try:
 assert R["native"]=="NATIVE_CONNECTED_ORBITAL_RELIEF_SCOPED_PASS"
 assert tuple(bpy.app.version[:2])==(5,2)
 file=Path(bpy.data.filepath);assert file.name=="V046_CONTINUOUS_TISSUE_EXPERIMENT.blend"
 assert sha(file)==R["blend"]["sha256"]
 base=bpy.data.objects["V046.Baseline.NoTissueRelief"]
 treated=bpy.data.objects["V046.Treatment.CONTINUOUS.ORBITAL.SKIN"]
 current=topology(treated)
 prior=R["treatment_topology"]
 assert all(current[k]==prior[k] for k in current)
 assert current["components"]==1 and current["nonmanifold"]==0 and current["boundary"]==0
 rows=[]
 for old in R["actual_raycast_comparison"]:
  a,b=ray(base,old["x"],old["z"]),ray(treated,old["x"],old["z"])
  assert abs(a-old["baseline_y"])<1e-6 and abs(b-old["treated_y"])<1e-6
  rows.append(old["label"])
 entries=R["baseline_renders"]+R["treatment_renders"]
 assert len(entries)==8
 for x in entries: assert sha(OUT/x["name"])==x["sha256"]
 assert all("GS001" not in x.name for x in bpy.data.objects)
 Q.update({"status":"V046_INDEPENDENT_FRESH_READBACK_PASS","blend_sha256":sha(file),"ray_labels":rows,
 "topology":current,"render_sha_verified":len(entries)})
except BaseException as e:
 Q["status"]="V046_FRESH_READBACK_HOLD";Q["error"]=repr(e)[:700];traceback.print_exc()
finally:
 (OUT/"FRESH_READBACK.json").write_text(json.dumps(Q,indent=2,ensure_ascii=False)+"\n")
 print("V046_FRESH_READBACK",json.dumps(Q,ensure_ascii=False),flush=True)
if Q["status"]!="V046_INDEPENDENT_FRESH_READBACK_PASS":sys.exit(46)
