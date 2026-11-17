#!/usr/bin/env python3
"""V039 ORIGINAL DESIGN BLOCKOUT + one real Blender native Draw broad brow pass.
No teacher mesh, no user image generation, no claim to professional face or ART pass.
Never operates on GS001 or any real canonical production character.
"""
import bpy, os, sys, json, math, hashlib, pathlib, traceback
from mathutils import Vector
from bpy_extras import view3d_utils
HERE=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from original_head_geometry_v039 import build,audit,shell_front_y
OUT=HERE/'native_v039';OUT.mkdir(parents=True,exist_ok=True)
REPORT={'version':'V039','date':'2026-11-17','blender':bpy.app.version_string,
 'kind':'ORIGINAL_BLOCKOUT_WITH_REAL_NATIVE_SCOPED_BROAD_BROW_STROKE',
 'source':'Original local pure Python cranial station design; not a traced studio model',
 'preexisting_native_reference':'V037C GUI/Xvfb masked Draw/Smooth verified',
 'GS001':'UNTOUCHED','art_status':'HOLD','face_anatomy':'NOT_COMPLETE',
 'new_face_retopo':'NOT_RUN','blink':'NOT_RUN','integration':'NOT_RUN',
 'design_sheet':'3D_BLOCKOUT_WITH_FOUR_VIEWS_ONLY_NOT_ART_REFERENCE_APPROVED',
 'native_status':'NOT_RUN'}

def hashfile(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
 return h.hexdigest()

def check_brush(n):
 if not n or not n.startswith('Draw'):raise ValueError('DRAW_REQUIRED_'+str(n))
 return True

def guard_mask(mesh):
 a=mesh.attributes.get('.sculpt_mask')
 if not a or a.domain!='POINT' or a.data_type!='FLOAT':raise ValueError('MISSING_POINT_SCULPT_MASK')
 vals=[x.value for x in a.data]
 if not any(v<.01 for v in vals) or not any(v>.99 for v in vals):raise ValueError('MASK_NOT_LOCALIZED')
 return True

def unit_negative_controls():
 ok=[]
 try:check_brush('Smooth');raise AssertionError('Wrong brush not blocked')
 except ValueError:ok.append('wrong_brush_blocked')
 # Missing/invalid mask test is performed with a bare throwaway mesh, never the actual head.
 tmp=bpy.data.meshes.new('V039.TEST.NOMASK')
 try:
  try:guard_mask(tmp);raise AssertionError('Missing mask not blocked')
  except ValueError:ok.append('missing_mask_blocked')
 finally:bpy.data.meshes.remove(tmp)
 return ok

def make_cam(scene,name,location,target=(0,0,0),scale=3.85):
 camdat=bpy.data.cameras.new(name)
 camdat.type='ORTHO';camdat.ortho_scale=scale
 cam=bpy.data.objects.new('Camera.'+name,camdat)
 scene.collection.objects.link(cam)
 cam.location=location;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler()
 return cam

def render(scene,cam,p):
 scene.camera=cam;scene.render.filepath=str(p)
 bpy.ops.render.render(write_still=True)
 assert p.is_file() and p.stat().st_size>15000,(p,p.stat().st_size if p.exists() else 0)
 return {'filename':p.name,'bytes':p.stat().st_size,'sha256':hashfile(p)}

try:
 print('V039 begin original research fixture',flush=True)
 assert bpy.app.version[:2]==(5,2),('Unexpected Blender',bpy.app.version)
 bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
 assert not any('GS001' in x.name for x in bpy.data.objects)
 verts,faces=build();ga=audit()
 assert ga['all_edges_two'] and ga['boundary']==0 and ga['overconnected']==0
 mesh=bpy.data.meshes.new('V039.ORIGINAL.CRANIUM.MESH');mesh.from_pydata(verts,[],faces);mesh.update()
 head=bpy.data.objects.new('V039.ORIGINAL.BLOCKOUT',mesh);bpy.context.collection.objects.link(head)
 mat=bpy.data.materials.new('V039.CLAY.BLOCKOUT.ART_HOLD');mat.diffuse_color=(.67,.51,.40,1)
 mesh.materials.append(mat)
 for p in mesh.polygons:p.use_smooth=True
 # The sclupt mask forbids edits outside the intended brow volume across BOTH sides.
 attr=mesh.attributes.new(name='.sculpt_mask',type='FLOAT',domain='POINT')
 before=[];mask=[]; editable=0
 for i,v in enumerate(mesh.vertices):
  x,y,z=v.co
  rad=math.sqrt(((abs(x)-.46)/.48)**2+((z-.57)/.36)**2)
  t=max(0.,min(1.,(rad-.72)/.36))
  m=t*t*(3-2*t)
  attr.data[i].value=m;mask.append(m)
  if m<.999:editable+=1
  before.append(tuple(v.co))
 guard_mask(mesh)
 assert 250<editable<len(mesh.vertices)//3,('Inappropriate mask size',editable,len(mesh.vertices))
 REPORT['topology_preflight']=ga
 REPORT['mask']={'name':'.sculpt_mask','domain':'POINT','editable':editable,'protected':len(verts)-editable,
 'source':'ellipse around both brow ridge regions; no mouth/nose/scalp modifications permitted'}
 REPORT['negative_preflight']=unit_negative_controls()
 scene=bpy.context.scene
 scene.render.engine='BLENDER_WORKBENCH'
 scene.display.shading.light='STUDIO';scene.display.shading.color_type='MATERIAL';scene.display.shading.show_shadows=True
 scene.display.shading.show_cavity=True;scene.display.shading.cavity_type='BOTH'
 scene.render.resolution_x=630;scene.render.resolution_y=620;scene.render.resolution_percentage=100
 scene.render.image_settings.file_format='PNG'
 if scene.world is None:scene.world=bpy.data.worlds.new('V039.World')
 scene.world.color=(.10,.10,.10)
 cams=[make_cam(scene,'FRONT',(0,-6.0,.15)),
       make_cam(scene,'THREE_QUARTER',(3.6,-5.2,.32)),
       make_cam(scene,'TRUE_PROFILE',(6,-.06,.15)),
       make_cam(scene,'LOW',(0,-5.4,-1.4))]
 REPORT['before']=[render(scene,c,OUT/('BEFORE_'+c.name[7:]+'.png')) for c in cams]
 bpy.ops.object.select_all(action='DESELECT');head.select_set(True);bpy.context.view_layer.objects.active=head
 area=next((a for a in bpy.context.screen.areas if a.type=='VIEW_3D'),None)
 if not area:raise RuntimeError('GUI VIEW_3D required; background brush activation prohibited for this recipe')
 reg=next((x for x in area.regions if x.type=='WINDOW'),None)
 if not reg:raise RuntimeError('VIEW_3D WINDOW region missing')
 r3d=area.spaces.active.region_3d;r3d.view_perspective='ORTHO'
 r3d.view_location=Vector((0,0,0));r3d.view_distance=4.35
 r3d.view_rotation=cams[0].rotation_euler.to_quaternion()
 strokes=[]
 with bpy.context.temp_override(window=bpy.context.window,screen=bpy.context.screen,area=area,region=reg):
  bpy.ops.object.mode_set(mode='SCULPT')
  asset_result=bpy.ops.brush.asset_activate(asset_library_type='ESSENTIALS',asset_library_identifier='',
   relative_asset_identifier='brushes/essentials_brushes-mesh_sculpt.blend/Brush/Draw')
  active=bpy.context.tool_settings.sculpt.brush
  check_brush(active.name if active else None)
  REPORT['brush']={'name':active.name,'asset_op_status':sorted(asset_result)}
  active.size=65;active.strength=.17
  REPORT['brush']['size']=active.size;REPORT['brush']['strength']=active.strength
  for side in [-1,1]:
   sample=[]
   for j in range(27):
    t=j/26.
    x=side*(.21+.52*t)
    z=.54+.055*math.sin(math.pi*t)
    y=shell_front_y(x,z)-.003
    xy=view3d_utils.location_3d_to_region_2d(reg,r3d,Vector((x,y,z)))
    if xy is None:raise RuntimeError('Projected brow point is outside GUI frame')
    sample.append({'name':'V039.OriginalBrowPlane','location':(x,y,z),
     'mouse':(float(xy.x),float(xy.y)),'mouse_event':(float(xy.x),float(xy.y)),
     'pressure':.20,'size':65,'time':j*.045,'is_start':j==0,'x_tilt':0.,'y_tilt':0.})
   out=bpy.ops.sculpt.brush_stroke(stroke=sample,mode='NORMAL')
   if 'FINISHED' not in out:raise RuntimeError('Native stroke did not finish: '+str(out))
   strokes.append({'side':side,'samples':len(sample),'status':sorted(out)})
  bpy.ops.object.mode_set(mode='OBJECT')
 REPORT['strokes']=strokes
 after=[tuple(v.co) for v in mesh.vertices]
 offsets=[math.dist(a,b) for a,b in zip(before,after)]
 remote=[d for d,m in zip(offsets,mask) if m>.999]
 local=[d for d,m in zip(offsets,mask) if m<.999]
 REPORT['measured']={'all_moved':sum(d>1e-7 for d in offsets),'local_moved':sum(d>1e-7 for d in local),
 'protected_moved':sum(d>1e-7 for d in remote), 'max_local':max(local,default=0.),
 'max_remote':max(remote,default=0.), 'max_global':max(offsets,default=0.)}
 REPORT['after']=[render(scene,c,OUT/('AFTER_'+c.name[7:]+'.png')) for c in cams]
 blend=OUT/'V039_ORIGINAL_BROW_BLOCKOUT.blend';bpy.ops.wm.save_as_mainfile(filepath=str(blend))
 REPORT['blend']={'file':blend.name,'sha256':hashfile(blend),'bytes':blend.stat().st_size}
 v=REPORT['measured']
 REPORT['native_status']='PASS_NARROW_BROW_SCULPT' if 20<=v['local_moved']<=editable and v['protected_moved']==0 and 0<v['max_local']<.22 else 'HOLD_NATIVE_SCOPE'
 print('V039 result',REPORT['native_status'],v,flush=True)
except BaseException as e:
 REPORT['native_status']='FAIL_RUNTIME_OR_PREFLIGHT'
 REPORT['error_type']=type(e).__name__;REPORT['error_detail']=str(e)
 traceback.print_exc()
finally:
 (OUT/'RECEIPT.json').write_text(json.dumps(REPORT,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
 if not bpy.app.background:
  try:bpy.ops.wm.quit_blender()
  except BaseException:pass
