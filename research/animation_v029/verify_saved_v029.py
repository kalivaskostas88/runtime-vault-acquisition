"""Freshly reopened Blender V029 evidence: no visual/art claims."""
import bpy,json,os,pathlib,math
OUT=pathlib.Path(os.environ['ANIMATION_V029_OUT'])
checks={}
for label in ('L','R'):
 ob=bpy.data.objects.get('EyelidPatch.'+label)
 assert ob is not None,'missing eye object '+label
 assert len(ob.data.vertices)==240 and len(ob.data.polygons)==192
 key=ob.data.shape_keys
 assert key and 'Basis' in key.key_blocks and 'Blink' in key.key_blocks
 dis=max((key.key_blocks['Basis'].data[i].co-key.key_blocks['Blink'].data[i].co).length for i in range(240))
 assert dis>0.15,dis
 checks[label]={'verts':len(ob.data.vertices),'quads':len(ob.data.polygons),'max_delta':dis}
assert bpy.data.objects.get('REFERENCE_HEAD_NOT_WELDED') is not None
source=json.loads((OUT/'RECEIPT.json').read_text())
assert source['technical_local_gate']=='PASS',source['technical_check_flags']
assert source['art_gate']=='HOLD'
assert source['full_face_integration']=='NOT_TESTED'
assert len(source['previews'])==6
for name,item in source['previews'].items():
 assert (OUT/item['file']).is_file() and (OUT/item['file']).stat().st_size>5000
(OUT/'FRESH_READBACK.json').write_text(json.dumps({'status':'PASS','blender_version':bpy.app.version_string,'objects':checks,'art':'HOLD','GS001':'UNTOUCHED'},indent=2)+'\n')
print('V029_FRESH_READBACK_PASS '+json.dumps(checks))
