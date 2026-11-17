"""V036 independent stylized target sculpt fixture, Blender 5.2.2.
Professional source: V035 original Aram Art selected teaching windows + Blender Studio Kaspar.
Original authored geometry; anatomical inspiration but no teacher mesh tracing.
NO retopo, NO blink, NO art pass, GS001 UNTOUCHED.
"""
import bpy,sys,os,pathlib,json,hashlib,math
from mathutils import Vector
from mathutils.bvhtree import BVHTree
HERE=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from geometry_v036 import generate,audit,landmarks,front_y,eye_targets,EYE_X,EYE_Z,EYE_RAD
OUT=pathlib.Path(os.environ.get('ANIMATION_V036_OUT',str(HERE/'native_output')))
OUT.mkdir(parents=True,exist_ok=True)
def sha(f):
 h=hashlib.sha256()
 with open(f,'rb') as inp:
  for b in iter(lambda:inp.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def material(name,color):
 m=bpy.data.materials.new(name);m.diffuse_color=color;m.use_nodes=True
 bsdf=m.node_tree.nodes.get('Principled BSDF')
 if bsdf:bsdf.inputs['Base Color'].default_value=color
 return m

def ball(name,loc,scale,ma,seg=40,ring=24):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=seg,ring_count=ring,location=loc)
 ob=bpy.context.object;ob.name=name;ob.scale=scale;ob.data.materials.append(ma)
 for p in ob.data.polygons:p.use_smooth=True
 return ob
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
sculpt_mat=material('ArtistStudyClay.NotArtPass',(0.57,0.40,0.32,1))
eyeball_mat=material('ReferenceEyeSclera.NotFinal',(0.90,0.91,0.89,1))
iris_mat=material('ReferenceIris.Original',(.25,.47,.46,1))
pupil_mat=material('ReferencePupil',(.055,.06,.065,1))
detail_mat=material('OriginalStudyBrownLines',(.16,.11,.10,1))
verts,faces=generate();m=audit();lm=landmarks();eyes=eye_targets()
mesh=bpy.data.meshes.new('V036_CLOSED_FACIAL_SCULPT_NOT_RETOPO');mesh.from_pydata(verts,[],faces);mesh.update()
head=bpy.data.objects.new('OriginalSculptV036.ONE_CLOSED_SHELL',mesh)
bpy.context.collection.objects.link(head);mesh.materials.append(sculpt_mat)
for poly in mesh.polygons:poly.use_smooth=True
# Separate eye reference objects are intentionally NOT rigged or part of face retopo.
feature=bpy.data.collections.new('OPTIONAL_STUDY_FEATURES_NOT_RETOPO')
bpy.context.scene.collection.children.link(feature)
def feature_obj(obj):
 for c in tuple(obj.users_collection):c.objects.unlink(obj)
 feature.objects.link(obj)
 return obj
for label,e in eyes.items():
 x,y,z=e['x'],e['y'],e['z'];r=e['radius']
 # Eye references are visible but intended to be embraced by modeled orbit tissue.
 feature_obj(ball('ReferenceEye.'+label,(x,y,z),(r,r,r),eyeball_mat,48,32))
 feature_obj(ball('Iris.'+label,(x,y-r-.006,z),(.087,.009,.088),iris_mat,32,20))
 feature_obj(ball('Pupil.'+label,(x,y-r-.018,z),(.041,.012,.041),pupil_mat,32,20))

def curve_on_surface(name,xz,ma,radius=.012):
 curve=bpy.data.curves.new(name,'CURVE');curve.dimensions='3D';curve.resolution_u=2
 curve.bevel_depth=radius;curve.bevel_resolution=3
 sp=curve.splines.new('POLY');sp.points.add(len(xz)-1)
 for i,(x,z) in enumerate(xz):
  sp.points[i].co=(x,front_y(x,z)-.014,z,1)
 ob=bpy.data.objects.new(name,curve);feature.objects.link(ob);ob.data.materials.append(ma)
 return ob
# Explicitly decoration only. Brow tissue and lips themselves are *sculpted in the head*.
for s,label in [(-1,'L'),(1,'R')]:
 brow=[]
 for i in range(33):
  t=i/32
  x=s*(.305+.51*t)
  z=.745+.055*math.sin(math.pi*t)-.012*t
  brow.append((x,z))
 curve_on_surface('ReferenceBrowHair.'+label,brow,detail_mat,.013)
 # Small pigment mark follows the recessed nostril candidate, not a modeled through hole.
 x=s*.18;z=-.37
 feature_obj(ball('NostrilPigmentCue.NOT_HOLE.'+label,(x,front_y(x,z)-.011,z),(.044,.008,.018),detail_mat,24,14))
line=[]
for i in range(47):
 t=-1+2*i/46;x=t*.351
 z=-.671+.006*t*t
 line.append((x,z))
curve_on_surface('MouthSeamPigmentCue.NOT_MOUTH_CAVITY',line,detail_mat,.009)
# Orthographic true-profile and low-angle study views, in addition to front/3-quarter.
bpy.ops.object.camera_add(location=(0,-5.9,.1));front=bpy.context.object;front.name='Camera.Front'
bpy.ops.object.camera_add(location=(3.10,-5.25,.50));oblique=bpy.context.object;oblique.name='Camera.Oblique'
bpy.ops.object.camera_add(location=(6.25,-.12,.25));profile=bpy.context.object;profile.name='Camera.TrueProfile'
bpy.ops.object.camera_add(location=(2,-5.1,-1.6));low=bpy.context.object;low.name='Camera.LowAngle'
for cam in [front,oblique,profile,low]:
 cam.rotation_euler=(Vector((0,-.10,-.06))-cam.location).to_track_quat('-Z','Y').to_euler()
 cam.data.type='ORTHO';cam.data.ortho_scale=3.83
scene=bpy.context.scene
scene.render.engine='BLENDER_WORKBENCH'
scene.display.shading.light='STUDIO';scene.display.shading.color_type='MATERIAL'
scene.display.shading.show_cavity=True;scene.display.shading.cavity_type='BOTH'
scene.display.shading.curvature_ridge_factor=.78
scene.display.shading.curvature_valley_factor=.78
scene.display.shading.show_shadows=True
scene.render.resolution_x=820;scene.render.resolution_y=720
scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG'
scene.world.color=(.09,.09,.09)
imgs={}
for cam in [front,oblique,profile,low]:
 for features_on in [False,True]:
  for ob in feature.objects:ob.hide_render=not features_on
  scene.camera=cam
  name='PREVIEW_'+cam.name.split('.')[-1].upper()+('_FACE' if features_on else '_SCULPT')+'.png'
  path=OUT/name;scene.render.filepath=str(path)
  bpy.ops.render.render(write_still=True)
  imgs[name]={'sha256':sha(path),'bytes':path.stat().st_size,'camera':cam.name,'features':features_on}
for ob in feature.objects:ob.hide_render=False
scene.camera=front;scene.render.filepath=''
# Native static mesh and camera view check; not occlusion under blinking.
from collections import Counter
edge=Counter()
for p in mesh.polygons:
 for k in range(p.loop_total):
  a=mesh.loops[p.loop_start+k].vertex_index
  b=mesh.loops[p.loop_start+(k+1)%p.loop_total].vertex_index
  edge[tuple(sorted((a,b)))]+=1
native={'vertices':len(mesh.vertices),'faces':len(mesh.polygons),
        'boundary':sum(n==1 for n in edge.values()),'nonmanifold_gt2':sum(n>2 for n in edge.values()),
        'all_edges_2use':all(n==2 for n in edge.values())}
blend=OUT/'original_stylized_sculpt_v036.blend'
bpy.ops.wm.save_as_mainfile(filepath=str(blend))
receipt={'version':'V036','runtime':bpy.app.version_string,'source_training':'V035 selected Aram Art windows W01-W06 W08 + Kaspar public written notes',
 'scope':'ORIGINAL TARGET SCULPT WITH ORBITAL LID AND NASAL/LABIAL VOLUME; NOT FINAL ART, NOT FACE RETOPO OR BLINK',
 'native_sculpt_gate':'PASS' if native['all_edges_2use'] else 'FAIL','native_geometry':native,
 'static_design':{k:v for k,v in m.items() if k not in ('landmarks','eyes')},
 'landmarks':lm,'reference_eyes':eyes,'feature_objects':len(feature.objects),
 'previews':imgs,'original_blend':{'name':blend.name,'bytes':blend.stat().st_size,'sha256':sha(blend)},
 'v034_negative_control':'Original V034 sculpt unchanged; baseline anterior projection 0.301165, different sculpt shapes and no blink, metrics not interchangeable',
 'V032_unmodified':True,'GS001':'UNTOUCHED','art_gate':'HOLD','retopo_gate':'NOT_RUN','blink_gate':'NOT_RUN',
 'limitations':['parametric sculpt derived from taught anatomical priorities, not direct hand-sculpted artist solution',
  'nostril pigmented recess is NOT a true open nostril',
  'mouth seam pigment is NOT an interior mouth',
  'eyes are independent reference spheres, NOT integrated deformable eyelids',
  'still views do not prove natural expressions or blink','no professional art review']}
(OUT/'RECEIPT.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print('V036_NATIVE='+json.dumps({'gate':receipt['native_sculpt_gate'],'vertices':native['vertices'],'faces':native['faces'],'images':len(imgs),'art':receipt['art_gate']}))
if receipt['native_sculpt_gate']!='PASS':raise RuntimeError('static native target sculpt FAIL')
