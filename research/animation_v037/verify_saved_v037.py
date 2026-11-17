#!/usr/bin/env python3
"""Independent Blender 5.2.2 fresh reopen and source-baseline/SCULPT_MASK audit.
Runs in a distinct official Blender process; no sculpt brush activation is performed.
"""
import bpy,os,sys,json,pathlib,math,hashlib
HERE=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from geometry_v036_reference import generate
OUT=HERE/'face_sculpt_output_v3'
r=json.loads((OUT/'RECEIPT.json').read_text(encoding='utf8'))
assert r['technical_gate']=='PASS_SCOPED_LOCAL_REAL_SCULPT' and r['art_gate']=='HOLD_INDEPENDENT_VISUAL_CRITIQUE'
object_name='V037.OriginalV036Copy.SculptTarget'
obj=bpy.data.objects.get(object_name)
assert obj and obj.type=='MESH', 'original research sculpture missing'
original_v,_=generate()
assert len(obj.data.vertices)==len(original_v)==15202
attr=obj.data.attributes.get('.sculpt_mask')
assert attr and attr.domain=='POINT'
maskeditable=sum(a.value<.999 for a in attr.data)
assert maskeditable==r['native_sculpt_mask']['editable_vertices']==248
changed=[];remote=[]
for ref, v in zip(original_v,obj.data.vertices):
    d=math.dist(ref,tuple(v.co))
    if d>1e-7:
        changed.append(d)
        if ref[2]>1.05 or ref[2]<-.16:remote.append(d)
assert len(changed)==r['measured_change']['total_moved_gt_1e7']==124
assert len(remote)==r['measured_change']['remote_moved_gt_1e7']==0
assert abs(max(changed)-r['measured_change']['global_max'])<1e-6
p=OUT/r['blend']['path']
h=hashlib.sha256(p.read_bytes()).hexdigest()
assert h==r['blend']['sha256']
files={}
for label in ('before_previews','after_previews'):
    for c,data in r[label].items():
        path=OUT/data['file']; assert path.is_file()
        digest=hashlib.sha256(path.read_bytes()).hexdigest()
        assert digest==data['sha256']
        files[data['file']]=digest
report={'version':'V037C','native_blender_reopen':'PASS','blender':bpy.app.version_string,
        'source_blend_sha256':h,'original_mesh_vertices':len(obj.data.vertices),
        'sculpt_mask_unmasked_vertices':maskeditable,'vertices_moved_after_reopen':len(changed),
        'changed_remote_vertices':len(remote),'max_after_reopen':max(changed),
        'preview_hashes_verified':len(files),'art':'HOLD','GS001':'UNTOUCHED',
        'scope':'NATIVE_BRUSH_MASKED_LOCALITY_ONLY_NOT_ARTISTIC_FACE_OR_BLINK'}
(OUT/'FRESH_READBACK.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print('V037_FRESH_REOPEN='+json.dumps(report,ensure_ascii=False))
