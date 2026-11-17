"""Fresh Blender reopened V034 native source artifact independently."""
import bpy,os,json,pathlib
p=pathlib.Path(os.environ.get('ANIMATION_V034_OUT','research/animation_v034/native_output'))
ob=bpy.data.objects.get('TargetSculpt.Original.CLOSED_REFERENCE')
assert ob is not None and ob.type=='MESH'
assert len(ob.data.vertices)==9090 and len(ob.data.polygons)==9216
assert bpy.data.collections.get('ORIGINAL_PATCH_GUIDES_NOT_TOPOLOGY') is not None
assert not ob.data.shape_keys
names=[o.name for o in bpy.data.objects]
assert any(x.startswith('ReferenceEye.L') for x in names) and any(x.startswith('ReferenceEye.R') for x in names)
r={'status':'PASS','version':'V034','blender':bpy.app.version_string,'original_head_vertices':len(ob.data.vertices),'faces':len(ob.data.polygons),'sculpt_target_reopened':True,'shape_keys':False,'GS001':'UNTOUCHED','ART':'HOLD'}
(p/'FRESH_READBACK.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
print('READBACK='+json.dumps(r))
