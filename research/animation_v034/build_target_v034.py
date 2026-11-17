"""V034 native original stylized *target sculpt* and patch-guide demonstration.
Does NOT reconstruct retopology, inherit V032 blink proof, or assert professional ART PASS.
Teacher: Julien Kaspar Snow facial retopology source V033 timecoded anatomy patches.
"""
import bpy,sys,os,pathlib,json,hashlib,math
from mathutils import Vector
HERE=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from sculpt_geometry_v034 import generate,audit,landmarks,front_y
OUT=pathlib.Path(os.environ.get('ANIMATION_V034_OUT',str(HERE/'native_output')))
OUT.mkdir(parents=True,exist_ok=True)
def hashfile(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for x in iter(lambda:f.read(1024*1024),b''):h.update(x)
 return h.hexdigest()

def mat(name,color):
 m=bpy.data.materials.new(name);m.diffuse_color=color;m.use_nodes=True
 shader=m.node_tree.nodes.get('Principled BSDF')
 if shader:shader.inputs['Base Color'].default_value=color
 return m

def sphere(name,loc,scale,material,segs=40,rings=24):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=segs,ring_count=rings,location=loc)
 ob=bpy.context.object;ob.name=name;ob.scale=scale;ob.data.materials.append(material)
 for p in ob.data.polygons:p.use_smooth=True
 return ob

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
sculpt_mat=mat('UnfinishedTargetSculpt.Original',(0.65,0.45,0.34,1))
teal=mat('PlanningContours.AnatomicalGuesses',(0.08,0.79,0.77,1))
orange=mat('NosePatch.PlanNotProof',(0.96,0.50,0.15,1))
red=mat('SuggestedPoles.NotVerified',(0.93,0.28,0.27,1))
sclera=mat('SyntheticEyeballReference',(0.91,.92,.93,1))
iris=mat('SyntheticIrisReference',(.16,.40,.48,1))
pupil=mat('SyntheticPupilReference',(.04,.06,.065,1))
verts,faces=generate();metrics=audit();land=landmarks()
mesh=bpy.data.meshes.new('TARGET_STYLIZED_SCULPT_NO_RIG_NO_RETOPO')
mesh.from_pydata(verts,[],faces);mesh.update()
head=bpy.data.objects.new('TargetSculpt.Original.CLOSED_REFERENCE',mesh)
bpy.context.collection.objects.link(head);head.data.materials.append(sculpt_mat)
for p in head.data.polygons:p.use_smooth=True
# Eyeballs are independent visible proportions/rig-context references, no hide trick.
for side in [-1,1]:
 label='L' if side<0 else 'R';x=side*.635
 sphere('ReferenceEye.'+label,(x,-.688,.40),(.235,.235,.235),sclera)
 sphere('ReferenceIris.'+label,(x,-.928,.40),(.103,.018,.103),iris,32,20)
 sphere('ReferencePupil.'+label,(x,-.946,.40),(.051,.013,.051),pupil,32,16)

collection=bpy.data.collections.new('ORIGINAL_PATCH_GUIDES_NOT_TOPOLOGY')
bpy.context.scene.collection.children.link(collection)

def draw(name,pts,material,radius=.009):
 curve=bpy.data.curves.new(name,'CURVE');curve.dimensions='3D';curve.resolution_u=3
 curve.bevel_depth=radius;curve.bevel_resolution=2
 spline=curve.splines.new('POLY');spline.points.add(len(pts)-1)
 for i,(x,z) in enumerate(pts):
  p=spline.points[i]
  p.co=(x,front_y(x,z)-.018,z,1)
 ob=bpy.data.objects.new(name,curve);collection.objects.link(ob);ob.data.materials.append(material)
 return ob

def ellipse(cx,cz,rx,rz,n=64):
 return [(cx+rx*math.cos(2*math.pi*i/n),cz+rz*math.sin(2*math.pi*i/n)) for i in range(n+1)]

for side in [-1,1]:
 x=side*.635;suf='L' if side<0 else 'R'
 draw('EyeRimPlan.'+suf,ellipse(x,.40,.345,.225),teal)
 draw('EyeSupportPlan.'+suf,ellipse(x,.40,.465,.335),teal,.006)
 draw('AlaVolumePlan.'+suf,ellipse(side*.232,-.22,.16,.128),orange,.008)
 draw('NasoCheekFlowPlan.'+suf,[(side*.31,.49),(side*.305,.30),(side*.33,.12),(side*.41,-.06),(side*.54,-.27),(side*.66,-.49),(side*.84,-.70)],orange,.01)
 draw('CheekRedirectPlan.'+suf,[(side*1.02,.35),(side*1.17,.08),(side*1.24,-.17),(side*1.32,-.43)],teal,.008)
 # Candidate pole marks are proposals on the outer cheek, NOT approved pole placement.
 px,pz=side*1.15,-.15
 pole=sphere('SuggestedPole.NOT_APPROVED.'+suf,(px,front_y(px,pz)-.029,pz),(.025,.025,.025),red,12,8)
 for owner in tuple(pole.users_collection):owner.objects.unlink(pole)
 collection.objects.link(pole)
draw('NasalDorsumPlan',[(0,.66),(0,.46),(0,.29),(0,.11),(0,-.04),(0,-.17)],orange,.013)

bpy.ops.object.camera_add(location=(0,-6.2,.20));front=bpy.context.object;front.name='Camera.Front'
bpy.ops.object.camera_add(location=(3,-5.4,.6));three=bpy.context.object;three.name='Camera.Oblique'
bpy.ops.object.camera_add(location=(5.7,-2.6,.3));side=bpy.context.object;side.name='Camera.Profile'
for cam,scale in [(front,4.25),(three,4.25),(side,4.25)]:
 cam.rotation_euler=(Vector((0,-.07,0))-cam.location).to_track_quat('-Z','Y').to_euler()
 cam.data.type='ORTHO';cam.data.ortho_scale=scale
scene=bpy.context.scene
scene.render.engine='BLENDER_WORKBENCH'
scene.display.shading.light='STUDIO';scene.display.shading.color_type='MATERIAL'
scene.display.shading.show_cavity=True
scene.display.shading.cavity_type='BOTH'
scene.display.shading.curvature_ridge_factor=.75
scene.display.shading.curvature_valley_factor=.75
scene.display.shading.show_shadows=True
scene.render.resolution_x=840;scene.render.resolution_y=700
scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG'
scene.world.color=(.11,.11,.11)
images={}
for cam in [front,three,side]:
 for show in [False,True]:
  for ob in collection.objects:ob.hide_render=not show
  scene.camera=cam
  name='PREVIEW_'+cam.name.split('.')[-1].upper()+('_GUIDES' if show else '_SCULPT')+'.png'
  path=OUT/name;scene.render.filepath=str(path)
  bpy.ops.render.render(write_still=True)
  images[name]={'sha256':hashfile(path),'bytes':path.stat().st_size,'guides':show,'camera':cam.name}
for ob in collection.objects:ob.hide_render=False
scene.camera=front;scene.render.filepath=''
blend=OUT/'original_target_sculpt_v034.blend';bpy.ops.wm.save_as_mainfile(filepath=str(blend))
receipt={'version':'V034','runtime':bpy.app.version_string,
 'scope':'ORIGINAL ANATOMICALLY INSPIRED STYLIZED TARGET SCULPT + QUAD PATCH PLAN; NOT RETOPO; NOT RIG; NOT PROFESSIONAL ANATOMY CERTIFIED',
 'sculpt_metrics':{k:v for k,v in metrics.items() if k!='landmarks'},'landmarks':land,'guide_count':len(collection.objects),
 'target_closed_mesh':metrics['open_boundary_edges']==0 and metrics['overconnected_edges']==0,
 'native_target_sculpt_gate':'PASS' if metrics['open_boundary_edges']==0 and metrics['overconnected_edges']==0 else 'FAIL',
 'proposed_patch_plan_status':'UNTESTED_BEFORE_PROJECTION','existing_v032_blink_proof':'NOT_INHERITED','V032_unchanged':True,
 'art_gate':'HOLD','GS001':'UNTOUCHED','limitations':['analytic approximated sculpt rather than a professionally artist-sculpted original','nostril forms are surface cues not real nostril apertures','guides do not certify pole routing or geometry','eyes remain separate reference objects','no new animation blink or deform proof'],
 'blend':{'name':blend.name,'sha256':hashfile(blend),'bytes':blend.stat().st_size},'previews':images}
(OUT/'RECEIPT.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print('NATIVE_TARGET_V034='+json.dumps({'sculpt':receipt['native_target_sculpt_gate'],'faces':metrics['faces'],'verts':metrics['vertices'],'guides':len(collection.objects),'previews':len(images),'art':receipt['art_gate']}))
if receipt['native_target_sculpt_gate']!='PASS':raise RuntimeError('V034 target sculpt invalid')
