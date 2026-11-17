#!/usr/bin/env python3
"""Independent 5.2.2 Blender background reopen of already-saved V039B GUI Sculpt.
Does NOT call brush.asset_activate or any sculpt stroke. Never touches GS001.
Checks exact original baseline reconstruction against persisted sculpt mesh and 8 preview hashes.
"""
import bpy,math,json,pathlib,hashlib,sys,traceback
HERE=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from original_head_geometry_v039 import build
OUT=HERE/'native_v039b'
REPORT={'version':'V039B_INDEPENDENT_RELOAD','status':'NOT_RUN','blender':bpy.app.version_string,
        'art_status':'HOLD','GS001':'UNTOUCHED','brush_asset_activation':'NOT_CALLED_IN_BACKGROUND'}

def sha(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for block in iter(lambda:f.read(1048576),b''):h.update(block)
 return h.hexdigest()
try:
 receipt=json.loads((OUT/'RECEIPT.json').read_text())
 blend=OUT/receipt['blend']['file']
 assert blend.is_file()
 assert sha(blend)==receipt['blend']['sha256'],'SHA mismatch before reopen'
 bpy.ops.wm.open_mainfile(filepath=str(blend))
 assert bpy.app.version[:2]==(5,2)
 assert not any('GS001' in x.name for x in bpy.data.objects)
 ob=bpy.data.objects.get('V039.ORIGINAL.BLOCKOUT');assert ob is not None
 mesh=ob.data
 old,_=build()
 assert len(mesh.vertices)==len(old)==11650
 a=mesh.attributes.get('.sculpt_mask');assert a and a.domain=='POINT'
 mask=[item.value for item in a.data]
 moved=[math.dist(tuple(v.co),old[i]) for i,v in enumerate(mesh.vertices)]
 metrics={'all_moved':sum(x>1e-7 for x in moved),
  'editable_moved':sum(x>1e-7 for x,m in zip(moved,mask) if m<1.0),
  'fully_masked_moved':sum(x>1e-7 for x,m in zip(moved,mask) if m==1.0),
  'near_full_transitional_moved':sum(x>1e-7 for x,m in zip(moved,mask) if .999<m<1.0),
  'near_full_transitional_vertices':sum(.999<m<1.0 for m in mask),
  'anatomically_far_moved':sum(x>1e-7 for x,v in zip(moved,old) if v[2]<-.10 or v[2]>1.1),
  'max_editable':max([x for x,m in zip(moved,mask) if m<1],default=0.),
  'max_fully_masked':max([x for x,m in zip(moved,mask) if m==1],default=0.),
  'max_far':max([x for x,v in zip(moved,old) if v[2]<-.10 or v[2]>1.1],default=0.),
  'max_global':max(moved)}
 for key,val in receipt['measured'].items():
  if isinstance(val,int):assert metrics[key]==val,(key,metrics[key],val)
  else:assert abs(metrics[key]-val)<1e-5,(key,metrics[key],val)
 hashes=[]
 for item in receipt['before']+receipt['after']:
  f=OUT/item['filename'];assert f.is_file() and f.stat().st_size==item['bytes']
  assert sha(f)==item['sha256'],('Preview changed',f)
  hashes.append(item['filename'])
 expected_cameras={'Camera.FRONT','Camera.THREE_QUARTER','Camera.TRUE_PROFILE','Camera.LOW'}
 assert expected_cameras.issubset({o.name for o in bpy.data.objects})
 assert receipt['native_status']=='PASS_NARROW_BROW_SCULPT'
 assert receipt['GS001']=='UNTOUCHED' and receipt['art_status']=='HOLD'
 REPORT.update({'status':'FRESH_RELOAD_PASS','measured_after_reopen':metrics,'preview_hashes_verified':hashes,
 'blend_sha256':sha(blend),'camera_count':4,'source_blender_receipt_sha256':sha(OUT/'RECEIPT.json'),
 'native_technical_scope':'ONE_REAL_BROW_STROKE_NOT_FULL_FACE_OR_ART_APPROVAL'})
except BaseException as e:
 REPORT['status']='FRESH_RELOAD_FAIL'
 REPORT['error_type']=type(e).__name__;REPORT['error_details']=str(e)[:500]
 traceback.print_exc()
finally:
 (OUT/'FRESH_READBACK.json').write_text(json.dumps(REPORT,ensure_ascii=False,indent=2)+'\n')
 print('V039B_FRESH_REOPEN='+json.dumps({'status':REPORT['status'],'measurements':REPORT.get('measured_after_reopen'),'error':REPORT.get('error_details')}),flush=True)
 if REPORT['status']!='FRESH_RELOAD_PASS':sys.exit(7)
