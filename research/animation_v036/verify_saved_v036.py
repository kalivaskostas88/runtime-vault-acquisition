"""Independent second Blender process reads the persisted V036 blend and validates original state."""
import bpy,json,os,pathlib
out=pathlib.Path(os.environ.get('ANIMATION_V036_OUT','research/animation_v036/native_output'))
obj=bpy.data.objects.get('OriginalSculptV036.ONE_CLOSED_SHELL')
valid=bool(obj and obj.type=='MESH' and len(obj.data.vertices)>15000 and len(obj.data.polygons)>15000 and not obj.data.shape_keys)
meta={'version':'V036','status':'PASS' if valid else 'FAIL','blender':bpy.app.version_string,
 'source_sculpt_reopened':valid,'vertices':len(obj.data.vertices) if obj else 0,
 'faces':len(obj.data.polygons) if obj else 0,
 'feature_objects':len(bpy.data.collections.get('OPTIONAL_STUDY_FEATURES_NOT_RETOPO').objects) if bpy.data.collections.get('OPTIONAL_STUDY_FEATURES_NOT_RETOPO') else 0,
 'no_shape_keys':bool(obj and not obj.data.shape_keys),
 'GS001':'UNTOUCHED','ART':'HOLD','FACE_RETOPO':'NOT_RUN','BLINK':'NOT_RUN'}
(out/'FRESH_READBACK.json').write_text(json.dumps(meta,indent=2)+'\n')
print('V036_READBACK='+json.dumps(meta))
if not valid:raise RuntimeError('V036 reopened blend did not match source')
