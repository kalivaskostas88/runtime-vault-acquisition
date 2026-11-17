"""Blender 5.2.2 original contour-first orbital module native experiment.
Read-only research scene, not a finished face. Two separate eye annulus modules
with relative shape keys; no claims of integrated head topology or artistic pass.
"""
import bpy, json, math, os, pathlib, sys, hashlib, bmesh
from mathutils import Vector
from collections import Counter
HERE=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from geometry_v029 import N,RINGS,CX,CZ,EYE_W,UP_H,LOW_H,eye_v,vertices,faces,aperture_area,center_gap
OUT=pathlib.Path(os.environ.get('ANIMATION_V029_OUT',str(HERE/'native_output')))
OUT.mkdir(parents=True,exist_ok=True)

def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for chunk in iter(lambda:f.read(1<<20),b''):h.update(chunk)
 return h.hexdigest()

def material(name,rgba,rough=.6):
 m=bpy.data.materials.new(name);m.diffuse_color=rgba;m.use_nodes=True
 bs=m.node_tree.nodes.get('Principled BSDF')
 if bs:
  bs.inputs['Base Color'].default_value=rgba
  bs.inputs['Roughness'].default_value=rough
 return m

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
skin=material('SkinClay',(0.72,0.51,0.39,1.0))
lidmat=material('LidSkin',(0.78,0.55,0.42,1.0))
sclera=material('Sclera',(0.93,0.92,0.87,1),.23)
iris=material('Iris',(0.17,0.42,0.43,1),.2)
pupil=material('Pupil',(0.055,0.065,0.07,1),.12)
softskin=material('LipAndNose',(0.52,0.31,0.27,1))

def ellipsoid(name,loc,scale,mat,segments=48,rings=24):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=segments,ring_count=rings,location=loc)
 ob=bpy.context.object;ob.name=name
 ob.scale=scale
 ob.data.materials.append(mat)
 for p in ob.data.polygons:p.use_smooth=True
 return ob

head=ellipsoid('REFERENCE_HEAD_NOT_WELDED',(0,0.10,0.02),(1.42,0.77,1.48),skin,48,32)
# Subtle nose/lips: reference context only, not integrated topology.
ellipsoid('NoseReference',(0,-0.68,0.13),(0.22,0.25,0.31),skin,32,16)
ellipsoid('MouthReference',(0,-0.665,-0.45),(0.30,0.085,0.055),softskin,32,12)
for side in (-1,1):
 ellipsoid(('Eyeball.L' if side==-1 else 'Eyeball.R'),(side*CX,-0.625,CZ),(0.272,0.272,0.272),sclera,48,32)
 ellipsoid(('Iris.L' if side==-1 else 'Iris.R'),(side*CX,-0.898,CZ),(0.110,0.015,0.110),iris,48,16)
 ellipsoid(('Pupil.L' if side==-1 else 'Pupil.R'),(side*CX,-0.918,CZ),(0.055,0.013,0.055),pupil,32,16)

modules={}
for side,suffix in [(-1,'L'),(1,'R')]:
 v=vertices(side,0)
 fs=faces()
 if side==1:fs=[tuple(reversed(f)) for f in fs]
 mesh=bpy.data.meshes.new('ContourFirst_'+suffix)
 mesh.from_pydata(v,[],fs);mesh.update()
 ob=bpy.data.objects.new('EyelidPatch.'+suffix,mesh)
 bpy.context.collection.objects.link(ob)
 mesh.materials.append(lidmat)
 for f in mesh.polygons:f.use_smooth=True
 ob.shape_key_add(name='Basis',from_mix=False)
 bk=ob.shape_key_add(name='Blink',from_mix=False)
 for i,pos in enumerate(vertices(side,1)):
  bk.data[i].co=pos
 bk.value=0.0
 modules[suffix]=ob

# A fixed camera and reproducible screenshot presets, not a beauty render.
bpy.ops.object.camera_add(location=(0,-5.0,0.85))
camera=bpy.context.object;camera.name='Camera.Front'
look=Vector((0,-0.35,0.12))-camera.location
camera.rotation_euler=look.to_track_quat('-Z','Y').to_euler()
camera.data.type='ORTHO';camera.data.ortho_scale=3.65
scene=bpy.context.scene;scene.camera=camera
scene.render.engine='BLENDER_WORKBENCH'
scene.display.shading.light='STUDIO'
scene.display.shading.color_type='MATERIAL'
scene.display.shading.show_cavity=True
scene.display.shading.cavity_type='BOTH'
scene.display.shading.curvature_ridge_factor=1.0
scene.display.shading.curvature_valley_factor=1.0
scene.display.shading.show_shadows=True
scene.render.resolution_x=720;scene.render.resolution_y=500;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.render.film_transparent=False
scene.world.color=(0.14,0.14,0.14)

# Bounded geometric technical audit: no full-face integration is inferred.
checks={}
for suffix,ob in modules.items():
 counts=Counter()
 for poly in ob.data.polygons:
  vids=list(poly.vertices)
  for a,b in zip(vids,vids[1:]+vids[:1]): counts[tuple(sorted((a,b)))]+=1
 boundary=[e for e,n in counts.items() if n==1]
 nonmanifold=[e for e,n in counts.items() if n>2]
 checks[suffix]={
  'vertex_count':len(ob.data.vertices),'quad_count':len(ob.data.polygons),
  'boundary_edges_expected_open_module':len(boundary),
  'overconnected_edges':len(nonmanifold),
  'non_quad_faces':sum(1 for f in ob.data.polygons if len(f.vertices)!=4),
  'outer_ring_exactly_fixed':all((Vector(ob.data.shape_keys.key_blocks['Blink'].data[i].co)-Vector(ob.data.shape_keys.key_blocks['Basis'].data[i].co)).length<1e-8 for i in range((len(RINGS)-1)*N,len(RINGS)*N)),
  'inner_ring_moves':any((Vector(ob.data.shape_keys.key_blocks['Blink'].data[i].co)-Vector(ob.data.shape_keys.key_blocks['Basis'].data[i].co)).length>0.1 for i in range(N))
 }

ratio=aperture_area(1)/aperture_area(0)
# Explicit negative control: rectangle cannot pass the smooth contour criterion.
rect=[(-.35,-.2),(.35,-.2),(.35,.2),(-.35,.2)]
def corner_angle(p0,p1,p2):
 ax=p0[0]-p1[0];ay=p0[1]-p1[1]
 bx=p2[0]-p1[0];by=p2[1]-p1[1]
 return math.degrees(math.acos(max(-1,min(1,(ax*bx+ay*by)/(math.hypot(ax,ay)*math.hypot(bx,by))))))
rectangles_angles=[corner_angle(rect[(i-1)%4],rect[i],rect[(i+1)%4]) for i in range(4)]
neg_control_rejected=(sum(70<a<110 for a in rectangles_angles)==4)

# Native shape-key isolation: only named module changes, mesh source/other module untouched.
initial={k:tuple(tuple(float(z) for z in v.co) for v in o.data.vertices) for k,o in modules.items()}
iso=[]
for active,other in [('L','R'),('R','L')]:
 modules[active].data.shape_keys.key_blocks['Blink'].value=0.72
 modules[other].data.shape_keys.key_blocks['Blink'].value=0.0
 bpy.context.view_layer.update()
 active_basis=modules[active].data.shape_keys.key_blocks['Basis']
 active_blink=modules[active].data.shape_keys.key_blocks['Blink']
 neutral_other=modules[other].data.shape_keys.key_blocks['Basis']
 # Verify evaluated mesh displacement, not just slider values.
 eval_act=modules[active].evaluated_get(bpy.context.evaluated_depsgraph_get())
 eval_other=modules[other].evaluated_get(bpy.context.evaluated_depsgraph_get())
 active_shift=max((v.co-active_basis.data[i].co).length for i,v in enumerate(eval_act.data.vertices))
 offshift=max((v.co-neutral_other.data[i].co).length for i,v in enumerate(eval_other.data.vertices))
 iso.append({'target':active,'target_max_move':active_shift,'other_max_move':offshift,'PASS':active_shift>0.07 and offshift<1e-7})
 modules[active].data.shape_keys.key_blocks['Blink'].value=0.0

# 2D first-hit optical witness: may reveal if retina is still seen with closed modules.
# Scan front projection of each iris/globe window; only actual globe/iris/pupil first hits count.
def visible_globe_fraction(side,closure):
 for s in ('L','R'):modules[s].data.shape_keys.key_blocks['Blink'].value=closure
 bpy.context.view_layer.update()
 deps=bpy.context.evaluated_depsgraph_get()
 count=0;globe_hits=0;patch_hits=0
 for xi in range(23):
  x=side*CX+(xi-11)*0.029
  for zi in range(17):
   z=CZ+(zi-8)*0.028
   count+=1
   ok,point,norm,index,obj,mat=scene.ray_cast(deps,Vector((x,-3.0,z)),Vector((0,1,0)),distance=5.0)
   if ok and obj:
    if obj.name.startswith(('Eyeball.','Iris.','Pupil.')):globe_hits+=1
    if obj.name.startswith('EyelidPatch.'):patch_hits+=1
 return {'rays':count,'globe_visible_hits':globe_hits,'globe_first_hit_fraction':globe_hits/count,'lid_first_hit_fraction':patch_hits/count}

occlusion={}
for state,v in [('OPEN',0.0),('HALF',0.5),('CLOSED',1.0)]:
 occlusion[state]={'L':visible_globe_fraction(-1,v),'R':visible_globe_fraction(1,v)}

# Six precommitted images with distinct shape key values.
presets=[('OPEN',0.0,0.0),('RIGHT_HALF',0.0,0.5),('RIGHT_CLOSED',0.0,1.0),('LEFT_CLOSED',1.0,0.0),('BOTH_HALF',0.5,0.5),('BOTH_CLOSED',1.0,1.0)]
images={}
for name,left,right in presets:
 modules['L'].data.shape_keys.key_blocks['Blink'].value=left
 modules['R'].data.shape_keys.key_blocks['Blink'].value=right
 bpy.context.view_layer.update()
 path=OUT/('preview_'+name+'.png')
 scene.render.filepath=str(path)
 bpy.ops.render.render(write_still=True)
 images[name]={'file':path.name,'sha256':sha(path),'bytes':path.stat().st_size,'L':left,'R':right}

modules['L'].data.shape_keys.key_blocks['Blink'].value=0.0
modules['R'].data.shape_keys.key_blocks['Blink'].value=0.0
bpy.context.view_layer.update()
scene.render.filepath=''
scene.frame_set(1)
blend=OUT/'native_orbital_module_v029.blend'
bpy.ops.wm.save_as_mainfile(filepath=str(blend))

# Only narrow, measurable candidate gates; no unearned character or art pass.
mesh_pass=all(
 q['vertex_count']==N*len(RINGS) and q['quad_count']==N*(len(RINGS)-1)
 and q['boundary_edges_expected_open_module']==2*N and q['overconnected_edges']==0
 and q['non_quad_faces']==0 and q['outer_ring_exactly_fixed'] and q['inner_ring_moves']
 for q in checks.values())
tech={'mesh_local_static_pass':mesh_pass,'closure_geometry_ratio_pass':0<ratio<.04,
      'bilateral_isolation_pass':all(q['PASS'] for q in iso),
      'negative_rectangle_control_rejected':neg_control_rejected}
# Occlusion needs actual measured closed fraction; do not assume will pass.
occlusion_pass=all(occlusion['CLOSED'][s]['globe_first_hit_fraction']<.04 and
                   occlusion['OPEN'][s]['globe_first_hit_fraction']>.08 for s in ['L','R'])
receipt={'version':'V029','runtime':bpy.app.version_string,'source_technique':'contour-first eyelid annular quads from professional video; original geometry','intent':'ISOLATED_ORBITAL_MODULE_NO_FACE_WELD',
 'scope_no_false_claim':['not a complete head retopology','not integrated face topology','not expressive acting','no independent artist grade'],
 'mesh_per_eye':checks,'shape_key_isolation':iso,
 'open_to_closed_aperture_ratio':ratio,'aperture_gap_open':center_gap(0),'aperture_gap_closed':center_gap(1),
 'raycast_front_occlusion':occlusion,'technical_check_flags':tech,
 'technical_local_gate':'PASS' if all(tech.values()) else 'FAIL',
 'occlusion_gate':'PASS' if occlusion_pass else 'HOLD',
 'art_gate':'HOLD','full_face_integration':'NOT_TESTED','GS001':'UNTOUCHED',
 'blend_file':blend.name,'blend_sha256':sha(blend),'previews':images}
(OUT/'RECEIPT.json').write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
print('V029_NATIVE_RESULT='+json.dumps({'technical':receipt['technical_local_gate'],'occlusion':receipt['occlusion_gate'],'art':receipt['art_gate'],'ratio':ratio,'occlusion_values':occlusion,'preview_count':len(images)}))
if not all(tech.values()):raise RuntimeError('V029 narrow technical gate did not pass')
