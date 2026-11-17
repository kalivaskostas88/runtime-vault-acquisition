"""V032 native Blender 5.2.2 proof of one contiguous two-eye facial SKIN mesh.
Does not claim finished head, studio rig, true eyelid musculature, or ART PASS.
Original integration follows professional contour-first edge-flow learning from V028;
reuses V031 bounded blink mechanism but independently proves the new integration.
"""
import bpy,math,json,os,pathlib,hashlib,sys
from mathutils import Vector
HERE=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from geometry_v031 import N,CX,CZ
from geometry_v032 import build,audit,directed_edges,extract_boundary_loops

OUT=pathlib.Path(os.environ.get('ANIMATION_V032_OUT',str(HERE/'native_output')))
OUT.mkdir(parents=True,exist_ok=True)

def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for c in iter(lambda:f.read(1<<20),b''):h.update(c)
 return h.hexdigest()

def material(name,rgba,rough=0.63):
 m=bpy.data.materials.new(name);m.diffuse_color=rgba;m.use_nodes=True
 n=m.node_tree.nodes.get('Principled BSDF')
 if n:
  n.inputs['Base Color'].default_value=rgba
  n.inputs['Roughness'].default_value=rough
 return m

def ellipsoid(name,loc,scale,mat,segments=48,rings=32):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=segments,ring_count=rings,location=loc)
 o=bpy.context.object;o.name=name;o.scale=scale;o.data.materials.append(mat)
 for p in o.data.polygons:p.use_smooth=True
 return o

bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
skin=material('OriginalSkin',(0.71,0.49,0.39,1.0))
sclera=material('Sclera',(0.92,0.93,0.92,1.0),0.22)
iris=material('Iris',(0.17,0.40,0.49,1.0),0.16)
pupil=material('Pupil',(0.05,0.06,0.07,1),0.12)
rear_skin=material('RearContextOnly',(0.58,0.40,0.34,1.0))

basis_verts,fs,info=build(0,0)
left_verts,left_faces,left_meta=build(1,0)
right_verts,right_faces,right_meta=build(0,1)
if fs!=left_faces or fs!=right_faces:raise RuntimeError('Blink changes topology')
q=audit()
if q['components']!=1 or q['perimeter_loop_lengths']!=[50,50,72] or q['nonmanifold_edges']!=0 or q['same_direction_double_edges']!=0 or not q['all_quads']:
 raise RuntimeError('Topological integration preflight fail')
mesh=bpy.data.meshes.new('UnifiedFacialMesh_Source')
mesh.from_pydata(basis_verts,[],fs);mesh.update()
face=bpy.data.objects.new('FaceSkin.CONTINUOUS',mesh)
bpy.context.collection.objects.link(face)
face.data.materials.append(skin)
for p in face.data.polygons:p.use_smooth=True
face.shape_key_add(name='Basis',from_mix=False)
for label,coords in [('Blink.L',left_verts),('Blink.R',right_verts)]:
 b=face.shape_key_add(name=label,from_mix=False)
 for i,xyz in enumerate(coords):b.data[i].co=xyz
 b.value=0.0

# Eyeball context is intentionally a separate internal organ from the face skin.
# Synthetic original reference skull is a *separate background display* behind
# the continuous front face; this is NOT a single watertight whole-head mesh.
ellipsoid('RearSkull.ReferenceNotIntegrated',(0,0.38,-0.05),(1.77,.80,1.74),rear_skin,64,32)
for side in (-1,1):
 suffix='L' if side<0 else 'R'
 ellipsoid('Eyeball.'+suffix,(side*CX,-0.625,CZ),(0.272,0.272,0.272),sclera)
 ellipsoid('Iris.'+suffix,(side*CX,-0.898,CZ),(0.11,0.015,0.11),iris,40,16)
 ellipsoid('Pupil.'+suffix,(side*CX,-0.918,CZ),(0.055,.014,.055),pupil,32,16)

bpy.ops.object.camera_add(location=(0,-6.25,0.66))
cam=bpy.context.object;cam.name='Camera.Front'
def aim_camera(cam,point):
 cam.rotation_euler=(Vector(point)-cam.location).to_track_quat('-Z','Y').to_euler()
aim_camera(cam,(0,-0.38,0.0))
cam.data.type='ORTHO';cam.data.ortho_scale=4.55
bpy.ops.object.camera_add(location=(2.3,-5.75,0.85))
cam34=bpy.context.object;cam34.name='Camera.ThreeQuarter'
aim_camera(cam34,(0,-0.3,0.02));cam34.data.type='ORTHO';cam34.data.ortho_scale=4.65
scene=bpy.context.scene;scene.camera=cam
scene.render.engine='BLENDER_WORKBENCH'
scene.display.shading.light='STUDIO'
scene.display.shading.color_type='MATERIAL'
scene.display.shading.show_cavity=True
scene.display.shading.cavity_type='BOTH'
scene.display.shading.curvature_ridge_factor=1.0
scene.display.shading.curvature_valley_factor=1.0
scene.display.shading.show_shadows=True
scene.render.resolution_x=840;scene.render.resolution_y=620
scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
scene.world.color=(0.12,0.12,0.12)

# NOTE exact seam vertices must be shared, not merely geometrically overlapped.
# Both eyeballs are part of the reference context, never toggled/invisibly hidden.
shapeL=face.data.shape_keys.key_blocks['Blink.L']
shapeR=face.data.shape_keys.key_blocks['Blink.R']

def set_blink(l,r):
 shapeL.value=l;shapeR.value=r;bpy.context.view_layer.update()

initial=face.data.shape_keys.key_blocks['Basis']
iso=[]
for which,notwhich in [('L','R'),('R','L')]:
 set_blink(.72 if which=='L' else 0,.72 if which=='R' else 0)
 eval_ob=face.evaluated_get(bpy.context.evaluated_depsgraph_get())
 s0,s1=info['eye_ranges'][which];o0,o1=info['eye_ranges'][notwhich]
 target=max((eval_ob.data.vertices[i].co-initial.data[i].co).length for i in range(s0,s1))
 other=max((eval_ob.data.vertices[i].co-initial.data[i].co).length for i in range(o0,o1))
 fixed=max((eval_ob.data.vertices[i].co-initial.data[i].co).length for i in list(info['rect_indices'])+info['outer_loop_indices'])
 iso.append({'target':which,'moving_eye_max_delta':target,'other_eye_max_delta':other,'outer_face_fixed_max_delta':fixed,'PASS':target>0.07 and other<1e-8 and fixed<1e-8})
set_blink(0,0)

# Native raycast samples reused unchanged from V031. These are only FRONT view;
# additional three-quarter camera previews are ART references, not raycast PASS.
def visible_globe_fraction(side,closure):
 set_blink(closure,closure)
 deps=bpy.context.evaluated_depsgraph_get()
 num=391;hits=0;lid=0
 for xi in range(23):
  x=side*CX+(xi-11)*.029
  for zi in range(17):
   z=CZ+(zi-8)*.028
   ok,p,n,index,o,mat=scene.ray_cast(deps,Vector((x,-3,z)),Vector((0,1,0)),distance=5.0)
   if ok and o:
    if o.name.startswith(('Eyeball.','Iris.','Pupil.')):hits+=1
    if o.name=='FaceSkin.CONTINUOUS':lid+=1
 return {'rays':num,'globe_first_hits':hits,'globe_first_hit_fraction':hits/num,'skin_first_hit_fraction':lid/num}

occlusion={}
for st,val in [('OPEN',0),('HALF',.5),('CLOSED',1)]:
 occlusion[st]={s:visible_globe_fraction(side,val) for s,side in [('L',-1),('R',1)]}

image_presets=[('FRONT_OPEN',0,0,cam),('FRONT_RIGHT_HALF',0,.5,cam),('FRONT_RIGHT_CLOSED',0,1,cam),('FRONT_LEFT_CLOSED',1,0,cam),('FRONT_BOTH_HALF',.5,.5,cam),('FRONT_BOTH_CLOSED',1,1,cam),('OBLIQUE_OPEN',0,0,cam34),('OBLIQUE_BOTH_CLOSED',1,1,cam34)]
images={}
for name,l,r,camera in image_presets:
 set_blink(l,r);scene.camera=camera
 p=OUT/('preview_'+name+'.png');scene.render.filepath=str(p)
 bpy.ops.render.render(write_still=True)
 images[name]={'sha256':sha(p),'bytes':p.stat().st_size,'L':l,'R':r,'camera':camera.name}
set_blink(0,0);scene.camera=cam;scene.render.filepath='';scene.frame_set(1)
blend=OUT/'native_integrated_facial_mask_v032.blend'
bpy.ops.wm.save_as_mainfile(filepath=str(blend))

# Deliberately tight acceptance gates; do not infer a studio/ART PASS.
geometry_ok=(q['vertices']==1045 and q['quads']==960 and q['components']==1 and q['perimeter_loop_lengths']==[50,50,72] and q['nonmanifold_edges']==0 and q['same_direction_double_edges']==0 and q['all_quads'] and q['low_projected_quad_area']==0)
mechanics_ok=all(x['PASS'] for x in iso)
front_occlusion_ok=all(occlusion['CLOSED'][s]['globe_first_hit_fraction']<.04 and occlusion['OPEN'][s]['globe_first_hit_fraction']>.08 for s in ('L','R'))
receipt={'version':'V032','runtime':bpy.app.version_string,'scope':'ONE_CONNECTED_FACIAL_SKIN_WITH_TWO_EYE_HOLES; NOT_FULL_SKULL','source_teaching':'MK Graphics V028 13:49-15:29 connected loops + Julien Kaspar facial retopo diagrams + official Blender bridge edges guidance',
 'geometry':q,'integration_gate':'PASS' if geometry_ok else 'FAIL',
 'bilateral_isolation':iso,'isolation_gate':'PASS' if mechanics_ok else 'FAIL',
 'front_raycast_occlusion':occlusion,'front_occlusion_gate':'PASS' if front_occlusion_ok else 'HOLD',
 'art':'HOLD','whole_head_watertight':'NOT_ATTEMPTED','side_view_occlusion':'VISUAL_REVIEW_ONLY_NOT_PROVED','GS001':'UNTOUCHED','limitations':['reference rear skull remains separate','two eye openings and outer skin perimeter intentional','not skin weighting, facial rig, real deformation','not artist-certified'],
 'blend':{'path':blend.name,'sha256':sha(blend),'size':blend.stat().st_size},'previews':images}
(OUT/'RECEIPT.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print('V032_NATIVE_RESULT='+json.dumps({'integration':receipt['integration_gate'],'isolation':receipt['isolation_gate'],'front_occlusion':receipt['front_occlusion_gate'],'art':receipt['art'],'open':occlusion['OPEN'],'closed':occlusion['CLOSED'],'previews':len(images)}))
if not(geometry_ok and mechanics_ok and front_occlusion_ok):raise RuntimeError('V032 integration mechanics gate did not pass')
