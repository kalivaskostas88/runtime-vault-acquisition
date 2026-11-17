"""Fresh official Blender 5.2.2 reload of V032 .blend: verifies mesh identity, face loops and three shape keys."""
import bpy,json,pathlib,os
from collections import Counter
out=pathlib.Path(os.environ['ANIMATION_V032_OUT'])
ob=bpy.data.objects.get('FaceSkin.CONTINUOUS')
assert ob is not None
assert ob.type=='MESH'
assert len(ob.data.vertices)==1045 and len(ob.data.polygons)==960
assert all(len(p.vertices)==4 for p in ob.data.polygons)
assert sorted([x.name for x in ob.data.shape_keys.key_blocks])==['Basis','Blink.L','Blink.R']
assert bpy.data.objects.get('Eyeball.L') and bpy.data.objects.get('Eyeball.R')
assert bpy.data.objects.get('RearSkull.ReferenceNotIntegrated')
edge_counts=Counter()
for f in ob.data.polygons:
 v=list(f.vertices)
 for a,b in zip(v,v[1:]+v[:1]):edge_counts[tuple(sorted((a,b)))]+=1
assert len([e for e,n in edge_counts.items() if n==1])==172
assert not any(n>2 for n in edge_counts.values())
assert not bpy.data.objects.get('GS001')
data={'status':'PASS','version':'V032','blender':bpy.app.version_string,'object':'FaceSkin.CONTINUOUS','vertices':len(ob.data.vertices),'quads':len(ob.data.polygons),'shape_keys':[x.name for x in ob.data.shape_keys.key_blocks], 'boundary_edges':172,'art':'HOLD','GS001':'UNTOUCHED'}
(out/'FRESH_READBACK.json').write_text(json.dumps(data,indent=2)+'\n')
print('V032_FRESH_READBACK='+json.dumps(data))
