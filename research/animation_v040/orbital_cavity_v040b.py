#!/usr/bin/env python3
"""V040 isolated real Blender 5.2.2 orbital concavity via EXACT boolean Difference.
Research fixture ONLY: no eyes, eyelids, anatomically finished face, GS001 or art approval.
One dominant treatment: on the unchanged V039 original station-profile head, subtract
TWO mirrored interior ellipsoidal cutters to test true negative volume vs V039 protrusions.
No sculpt brush assets (headless Boolean != V037 problematic headless brush activation).
"""
import bpy,sys,math,json,hashlib,pathlib,traceback,bmesh
from mathutils import Vector
HERE=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
sys.path.insert(0,str(HERE.parent/"animation_v039"))
from original_head_geometry_v039 import build,audit
OUT=HERE/'native_v040';OUT.mkdir(parents=True,exist_ok=True)
CONFIG={"blender_major_minor":[5,2],"operation":"DIFFERENCE","solver":"EXACT",
  "centers_x":[-.44,.44],"center_y":-.92,"center_z":.44,
  "radius_x":.33,"radius_y":.34,"radius_z":.29,
  "ray_tolerance_remote":2e-5,"min_center_depth":.035,"max_center_depth":.35}
R={"version":"V040B","scope":"RESEARCH_ONLY_BOOLEAN_NEGATIVE_ORBITAL_VOLUME_NOT_HUMAN_ANATOMY",
 "input":"V039 original unsculpted closed station-profile head, generated from exact source code",
 "pro_sources":["Blender 5.2 Boolean Exact manual","Blender Studio Julien Kaspar Primitive-to-Planar head and brow-lid overlap public descriptions"],
 "GS001":"UNTOUCHED","art":"HOLD","character_design_sheet":"NOT_DRAWN",
 "eyelids":"NOT_RUN","retopology":"NOT_RUN","blink":"NOT_RUN","integration":"NOT_RUN",
 "native":"NOT_RUN","config":CONFIG}

def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()

def check_boolean_inputs(op, solver, manifold):
 if op!='DIFFERENCE':raise ValueError('FORBID_ANYTHING_EXCEPT_DIFFERENCE')
 if solver!='EXACT':raise ValueError('EXACT_BOOLEAN_REQUIRED')
 if not manifold:raise ValueError('CLOSED_MANIFOLD_REQUIRED')
 return True

def negative_preflight():
 out=[]
 for args in [('UNION','EXACT',True),('DIFFERENCE','FLOAT',True),('DIFFERENCE','EXACT',False)]:
  try:check_boolean_inputs(*args)
  except ValueError:out.append('REJECTED_'+args[0]+'_'+args[1]+'_'+str(args[2]))
  else:raise AssertionError('Unsafe config accepted: '+str(args))
 return out

def topology(obj):
 bm=bmesh.new();bm.from_mesh(obj.data);bm.verts.ensure_lookup_table();bm.edges.ensure_lookup_table();bm.verts.index_update()
 count_faces=len(bm.faces);count_verts=len(bm.verts)
 boundary=sum(1 for e in bm.edges if e.is_boundary)
 bad=sum(1 for e in bm.edges if not e.is_manifold)
 faces_3=sum(1 for f in bm.faces if len(f.verts)==3)
 # Components: this ensures no shells were accidentally separated from body.
 adjacency=[[] for _ in bm.verts]
 for e in bm.edges:
  a,b=e.verts[0].index,e.verts[1].index
  adjacency[a].append(b);adjacency[b].append(a)
 seen=set();comps=0
 for i in range(count_verts):
  if i in seen:continue
  comps+=1;seen.add(i);stack=[i]
  while stack:
   for j in adjacency[stack.pop()]:
    if j not in seen:seen.add(j);stack.append(j)
 volume=abs(bm.calc_volume(signed=True))
 bm.free()
 return {"vertices":count_verts,"faces":count_faces,"triangle_faces":faces_3,
         "boundary_edges":boundary,"nonmanifold_edges":bad,"connected_components":comps,"volume":volume}

def first_front_hit(obj,x,z):
 hit,location,normal,index=obj.ray_cast(Vector((x,-3.0,z)),Vector((0,1,0)),distance=8)
 if not hit:raise RuntimeError('No front ray hit for x='+str(x)+' z='+str(z))
 return float(location.y)

def camera(scene,name,loc,at=(0,0,0)):
 d=bpy.data.cameras.new(name);d.type='ORTHO';d.ortho_scale=3.9
 o=bpy.data.objects.new('Camera.'+name,d);scene.collection.objects.link(o)
 o.location=loc;o.rotation_euler=(Vector(at)-o.location).to_track_quat('-Z','Y').to_euler();return o

def snap(scene,cam,name):
 p=OUT/name;scene.camera=cam;scene.render.filepath=str(p)
 bpy.ops.render.render(write_still=True)
 if not p.exists() or p.stat().st_size<15000:raise RuntimeError('Invalid preview '+name)
 return {'file':p.name,'sha256':sha(p),'bytes':p.stat().st_size}

try:
 assert tuple(bpy.app.version[:2])==(5,2),bpy.app.version_string
 assert len(bpy.data.objects)==0 or not any('GS001' in o.name for o in bpy.data.objects)
 bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
 ga=audit();assert ga['all_edges_two'] and ga['boundary']==0
 check_boolean_inputs(CONFIG['operation'],CONFIG['solver'],True)
 R['negative_preflight']=negative_preflight()
 verts,faces=build();mesh=bpy.data.meshes.new('V040.OriginalSource.V039.Mesh')
 mesh.from_pydata(verts,[],faces);mesh.update()
 head=bpy.data.objects.new('V040.BLOCKOUT.ORBITAL.CAVITY',mesh);bpy.context.collection.objects.link(head)
 bpy.context.view_layer.objects.active=head;head.select_set(True)
 mat=bpy.data.materials.new('V040.Clay.NoArtApproval');mat.diffuse_color=(.62,.54,.49,1)
 head.data.materials.append(mat)
 for face in head.data.polygons:face.use_smooth=True
 scene=bpy.context.scene
 scene.render.engine='BLENDER_WORKBENCH'
 scene.display.shading.light='STUDIO';scene.display.shading.color_type='MATERIAL'
 scene.display.shading.show_shadows=True;scene.display.shading.show_cavity=True
 scene.display.shading.cavity_type='BOTH';scene.render.image_settings.file_format='PNG'
 scene.render.resolution_x=620;scene.render.resolution_y=620;scene.render.resolution_percentage=100
 if not scene.world:scene.world=bpy.data.worlds.new('V040.World')
 scene.world.color=(.08,.08,.08)
 cams=[camera(scene,'FRONT',(0,-6,.15)),camera(scene,'THREE_QUARTER',(3.6,-5.2,.32)),
       camera(scene,'TRUE_PROFILE',(6,-.06,.15)),camera(scene,'LOW',(0,-5.4,-1.4))]
 points=[(-.44,.44),(.44,.44),(0,0),(.9,.0),(0,1.04),(.55,-.64)]
 base_hits={(str(x),str(z)):first_front_hit(head,x,z) for x,z in points}
 R['base_topology']=topology(head)
 R['before']=[snap(scene,c,'BEFORE_'+c.name[7:]+'.png') for c in cams]
 cutters=[]
 for side in [-1,1]:
  bpy.ops.mesh.primitive_uv_sphere_add(segments=64,ring_count=40,location=(side*.44,CONFIG['center_y'],CONFIG['center_z']))
  cutter=bpy.context.object;cutter.name='V040.Cutter.'+('L' if side<0 else 'R')
  cutter.scale=(CONFIG['radius_x'],CONFIG['radius_y'],CONFIG['radius_z'])
  # Apply transform to avoid ambiguous cutter dimensions.
  bpy.context.view_layer.objects.active=cutter
  bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
  cutters.append(cutter)
  cutter.hide_render=True
  bpy.ops.object.select_all(action='DESELECT')
  head.select_set(True);bpy.context.view_layer.objects.active=head
  m=head.modifiers.new('V040.ELLIPSOID_ORBIT_CAVITY_'+str(side),'BOOLEAN')
  m.operation='DIFFERENCE';m.solver='EXACT';m.object=cutter
  bpy.ops.object.modifier_apply(modifier=m.name)
  cutter.hide_render=True
  bpy.data.objects.remove(cutter,do_unlink=True)
  cutters.pop()
 R['after_topology']=topology(head)
 new_hits={(str(x),str(z)):first_front_hit(head,x,z) for x,z in points}
 R['ray_proof']=[{'x':x,'z':z,'before_y':base_hits[(str(x),str(z))],
   'after_y':new_hits[(str(x),str(z))],
   'inward_depth':new_hits[(str(x),str(z))]-base_hits[(str(x),str(z))]} for x,z in points]
 R['after']=[snap(scene,c,'AFTER_'+c.name[7:]+'.png') for c in cams]
 outblend=OUT/'V040_ORBIT_CAVITY_BLOCKOUT.blend'
 bpy.ops.wm.save_as_mainfile(filepath=str(outblend))
 R['blend']={'file':outblend.name,'sha256':sha(outblend),'bytes':outblend.stat().st_size}
 centers=[v['inward_depth'] for v in R['ray_proof'][:2]]
 remote=[abs(v['inward_depth']) for v in R['ray_proof'][2:]]
 valid=(R['after_topology']['boundary_edges']==0 and R['after_topology']['nonmanifold_edges']==0
   and R['after_topology']['connected_components']==1
   and all(CONFIG['min_center_depth']<d<CONFIG['max_center_depth'] for d in centers)
   and all(d<=CONFIG['ray_tolerance_remote'] for d in remote))
 R['native']='NATIVE_BOOLEAN_CAVITY_SCOPE_PASS' if valid else 'HOLD_BOOLEAN_CAVITY_SCOPE'
 print('V040_NATIVE_RESULT',R['native'],'centers',centers,'far',remote,flush=True)
except BaseException as e:
 R['native']='FAIL_RUNTIME_OR_TECHNICAL_GATE';R['failure_type']=type(e).__name__
 R['failure_message']=str(e)[:800];traceback.print_exc()
finally:
 (OUT/'RECEIPT.json').write_text(json.dumps(R,ensure_ascii=False,indent=2)+'\n',encoding='utf8')