#!/usr/bin/env python3
"""V045 independent separate-process readback of exact saved .blend and true render hashes."""
import bpy,hashlib,json,math,sys,traceback
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parent;OUT=ROOT/"native_v045"
rc=json.loads((OUT/"RECEIPT.json").read_text())
read={"version":"V045_SEPARATE_BLENDER_PROCESS_RELOAD","native_receipt":rc.get("native"),"GS001":"UNTOUCHED","art":"HOLD","status":"NOT_RUN"}
def sha(p):
 h=hashlib.sha256()
 with open(p,"rb") as f:
  for c in iter(lambda:f.read(2**20),b""):h.update(c)
 return h.hexdigest()
try:
 assert rc["native"]=="NATIVE_GLOBE_LID_MARGIN_PROXIMITY_PASS"
 assert tuple(bpy.app.version[:2])==(5,2)
 assert bpy.data.filepath and bpy.data.filepath.endswith("V045_GLOBE_LID_ORIGINAL_TEST_FIXTURE.blend")
 bl=Path(bpy.data.filepath);assert sha(bl)==rc["blend"]["sha256"],"BLEND_HASH_MISMATCH"
 assert len(rc["images"])==4
 files=[]
 for entry in rc["images"]:
  p=OUT/entry["name"]
  assert p.exists() and sha(p)==entry["sha256"],"ORIGINAL_RENDER_HASH_MISMATCH"
  files.append(entry["name"])
 globes={s:bpy.data.objects["V045.Globe."+("L" if s==-1 else "R")] for s in (-1,1)}
 rows=[];all_gaps=[]
 for s in (-1,1):
  for u in (True,False):
   lid=bpy.data.objects["V045.Lid."+("UPPER" if u else "LOWER")+"."+("L" if s==-1 else "R")]
   c=Vector(globes[s].location);rr=float(globes[s]["radius"])
   gaps=[((lid.matrix_world @ lid.data.vertices[i].co)-c).length-rr for i in range(int(lid["margin_vertices"]))]
   rows.append({"side":s,"upper":u,"min":min(gaps),"max":max(gaps),"samples":len(gaps)})
   all_gaps.extend(gaps)
 assert len(rows)==4 and len(all_gaps)==404
 assert all(abs(g-.023)<.002 for g in all_gaps),"REOPENED_MARGIN_GAP_FAILED"
 assert all(abs(d)<1e-7 for a,b in zip(rows,rc["geometry"]["lid_data"]) for d in (a["min"]-b["min"],a["max"]-b["max"]))
 read.update({"status":"FRESH_SAVED_NATIVE_RELOAD_PASS","model_sha256":sha(bl),"verified_original_images":files,"sample_count":len(all_gaps),"min_gap":min(all_gaps),"max_gap":max(all_gaps)})
except BaseException as ex:
 read["status"]="FRESH_READBACK_HOLD";read["error"]=type(ex).__name__+": "+str(ex)[:550];traceback.print_exc()
finally:
 (OUT/"FRESH_READBACK.json").write_text(json.dumps(read,ensure_ascii=False,indent=2)+"\n")
 print("V045_READBACK",json.dumps(read,ensure_ascii=False),flush=True)
if read["status"]!="FRESH_SAVED_NATIVE_RELOAD_PASS":sys.exit(46)
