#!/usr/bin/env python3
"""V040 independent native saved .blend read-only verification; no brush activation or asset mutation."""
import bpy,bmesh,json,hashlib,math,pathlib,sys,traceback
from mathutils import Vector
HERE=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'animation_v039'))
from original_head_geometry_v039 import build,audit
OUT=HERE/'native_v040';OUT.mkdir(exist_ok=True)
P=OUT/'RECEIPT.json'; B=OUT/'V040_ORBIT_CAVITY_BLOCKOUT.blend'
res={'version':'V040_FRESH','blender':bpy.app.version_string,'status':'NOT_RUN','art':'HOLD','GS001':'UNTOUCHED'}
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for x in iter(lambda:f.read(2**20),b''):h.update(x)
 return h.hexdigest()
def front(obj,x,z):
 hit,loc,_,_=obj.ray_cast(Vector((x,-3,z)),Vector((0,1,0)),distance=8)
 if not hit:raise ValueError(f'Missing front hit {x},{z}')
 return float(loc.y)
def topo(ob):
 bm=bmesh.new();bm.from_mesh(ob.data);bm.verts.ensure_lookup_table();bm.edges.ensure_lookup_table();bm.verts.index_update()
 border=sum(e.is_boundary for e in bm.edges);nonmanifold=sum(not e.is_manifold for e in bm.edges)
 nxt=[[] for _ in bm.verts]
 for e in bm.edges:
  a,b=e.verts[0].index,e.verts[1].index;nxt[a].append(b);nxt[b].append(a)
 seen=set();components=0
 for v in range(len(nxt)):
  if v in seen:continue
  components+=1;st=[v];seen.add(v)
  while st:
   for j in nxt[st.pop()]:
    if j not in seen:seen.add(j);st.append(j)
 result={'verts':len(bm.verts),'faces':len(bm.faces),'boundary':border,'nonmanifold':nonmanifold,'components':components}
 bm.free();return result
try:
 assert bpy.app.version[:2]==(5,2)
 r=json.loads(P.read_text())
 assert r['native']=='NATIVE_BOOLEAN_CAVITY_SCOPE_PASS'
 assert r['GS001']=='UNTOUCHED' and r['art']=='HOLD'
 assert sha(B)==r['blend']['sha256'],'SAVED_BLEND_HASH_MISMATCH'
 res['blend_sha256']=sha(B)
 seen=[]
 for f in r['before']+r['after']:
  path=OUT/f['file'];assert path.stat().st_size==f['bytes'] and sha(path)==f['sha256'],f['file']
  seen.append(f['file'])
 res['verified_png_sha256']=seen
 bpy.ops.wm.open_mainfile(filepath=str(B))
 assert not any('GS001' in o.name for o in bpy.data.objects)
 head=bpy.data.objects.get('V040.BLOCKOUT.ORBITAL.CAVITY')
 assert head is not None
 t=topo(head);res['saved_topology']=t
 assert t['components']==1 and t['boundary']==0 and t['nonmanifold']==0
 assert t['verts']==r['after_topology']['vertices'] and t['faces']==r['after_topology']['faces']
 v,f=build();m=bpy.data.meshes.new('V040_TEMP_INDEPENDENT_BASELINE');m.from_pydata(v,[],f);m.update()
 base=bpy.data.objects.new('V040_TEMP_BASELINE',m)
 bpy.context.collection.objects.link(base)
 rec=[]
 for s in r['ray_proof']:
  x,z=s['x'],s['z']
  now=front(head,x,z);start=front(base,x,z);depth=now-start
  assert abs(depth-s['inward_depth'])<1e-5,('RAY_DIFF',x,z,depth,s['inward_depth'])
  rec.append({'x':x,'z':z,'depth':depth,'baseline':start,'cavity':now})
 assert all(.035<x['depth']<.35 for x in rec[:2]);assert all(abs(x['depth'])<2e-5 for x in rec[2:])
 res['verified_rays']=rec
 res['status']='FRESH_READBACK_PASS'
except BaseException as e:
 res['status']='FRESH_READBACK_FAIL';res['error']=type(e).__name__+':'+str(e)[:350]
 traceback.print_exc()
finally:
 (OUT/'FRESH_READBACK.json').write_text(json.dumps(res,indent=2,ensure_ascii=False)+'\n')
 print('V040_FRESH',res['status'],flush=True)