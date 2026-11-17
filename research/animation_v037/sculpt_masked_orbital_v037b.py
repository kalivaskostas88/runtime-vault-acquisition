#!/usr/bin/env python3
"""V037 actual Blender GUI Sculpt brush on original copy of V036 negative witness.
Target ONE anatomical issue only: overly harsh eyelid socket lip / donut-shaped orbit.
This is a control study, not an approved face or animation, and never edits GS001.
"""
import bpy, json, math, os, sys, pathlib, hashlib, traceback, statistics
from mathutils import Vector
from bpy_extras import view3d_utils
HERE=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from geometry_v036_reference import generate,front_y,eye_targets
OUT=HERE/'face_sculpt_output_v2';OUT.mkdir(parents=True,exist_ok=True)
R={'version':'V037B','run_type':'ACTUAL_NATIVE_BLENDER_SCULPT_SMOOTH_GUIDED_ON_V036_COPY',
    'blender':bpy.app.version_string,'mode':'GUI_VIRTUAL_DISPLAY','GS001':'UNTOUCHED',
    'source_teacher_windows':'V035 Aram Art W02/W05 real visual & ASR; Kaspar brow-overlap note public text',
    'reference_baseline':'V036 original analytic head recreated unchanged before actual strokes',
    'art_pass':False,'face_retopo':False,'blink_pass':False}

def sha(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
      for block in iter(lambda:f.read(1<<20),b''):h.update(block)
    return h.hexdigest()

def make_mat(name,col):
    mat=bpy.data.materials.new(name);mat.diffuse_color=col
    return mat

def render(scene,cam,path,visible):
    for ob in features:ob.hide_render=not visible
    scene.camera=cam;scene.render.filepath=str(path)
    bpy.ops.render.render(write_still=True)
    return {'file':path.name,'bytes':path.stat().st_size,'sha256':sha(path)}
try:
    print('V037_FACE_STAGE:init',flush=True)
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    verts,faces=generate()
    mesh=bpy.data.meshes.new('ORIGINAL_V036_RESEARCH_SHELL_BEFORE_SCULPT')
    mesh.from_pydata(verts,[],faces);mesh.update()
    head=bpy.data.objects.new('V037.OriginalV036Copy.SculptTarget',mesh)
    bpy.context.collection.objects.link(head)
    clay=make_mat('V037.Clay.NOT_ART_PASS',(.58,.41,.32,1));eye_mat=make_mat('V037.ReferenceGlobe',(.86,.87,.86,1))
    mesh.materials.append(clay)
    for p in mesh.polygons:p.use_smooth=True
    # Blender native sculpt mask (.sculpt_mask): only a narrow orbital annulus is editable.
    # Contrast previous failure (V037A) where 3201 remote vertices moved without masking.
    attr=mesh.attributes.get('.sculpt_mask')
    if not attr:attr=mesh.attributes.new(name='.sculpt_mask',type='FLOAT',domain='POINT')
    available=0
    for i,v in enumerate(mesh.vertices):
      x,z=v.co.x,v.co.z
      radial=math.sqrt(((abs(x)-.55)/.305)**2+((z-.405)/.172)**2)
      delta=abs(radial-1.)
      t=max(0.,min(1.,(delta-.11)/.105))
      mask=t*t*(3-2*t)
      attr.data[i].value=mask
      if mask<.999:available+=1
    mesh.update()
    R['native_sculpt_mask']={'attribute':attr.name,'vertex_domain':attr.domain,'editable_vertices':available,'protected_vertices':len(mesh.vertices)-available,'rule':'unmask one thin orbital ring on both sides'}
    features=[]
    for side,d in eye_targets().items():
      bpy.ops.mesh.primitive_uv_sphere_add(segments=32,ring_count=20,location=(d['x'],d['y'],d['z']))
      o=bpy.context.object;o.name='EyeReference.'+side
      o.scale=(d['radius'],)*3
      o.data.materials.append(eye_mat)
      for p in o.data.polygons:p.use_smooth=True
      features.append(o)
    front_cam=bpy.data.cameras.new('Front'); ob_cam=bpy.data.cameras.new('Oblique');prof_cam=bpy.data.cameras.new('Profile')
    def cam(name,data,loc,target=(0,-.08,-.10)):
        ob=bpy.data.objects.new(name,data);bpy.context.collection.objects.link(ob)
        ob.location=loc;ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler()
        data.type='ORTHO';data.ortho_scale=3.7
        return ob
    cameras=[cam('Camera.Front',front_cam,(0,-6.0,.15)),
       cam('Camera.Oblique',ob_cam,(3.1,-5.3,.4)),
       cam('Camera.Profile',prof_cam,(6.2,-.12,.24))]
    scene=bpy.context.scene;scene.render.engine='BLENDER_WORKBENCH'
    scene.display.shading.light='STUDIO';scene.display.shading.color_type='MATERIAL';scene.display.shading.show_shadows=True
    scene.display.shading.show_cavity=True;scene.display.shading.cavity_type='BOTH';scene.display.shading.curvature_ridge_factor=.74
    scene.render.resolution_x=640;scene.render.resolution_y=580;scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG';scene.world.color=(.09,.09,.09)
    R['before_previews']={}
    for camob in cameras:
      f=OUT/('BEFORE_'+camob.name.split('.')[-1].upper()+'.png')
      R['before_previews'][camob.name]=render(scene,camob,f,True)
    before=[tuple(v.co) for v in mesh.vertices]
    # GUI with proper VIEW_3D context is required. Background asset_activate can segfault (Blender #152862).
    bpy.ops.object.select_all(action='DESELECT');head.select_set(True);bpy.context.view_layer.objects.active=head
    area=next((a for a in bpy.context.screen.areas if a.type=='VIEW_3D'),None)
    if not area:raise RuntimeError('No Blender UI VIEW_3D context')
    reg=next((x for x in area.regions if x.type=='WINDOW'),None)
    if not reg:raise RuntimeError('No Blender VIEW_3D WINDOW region')
    region3d=area.spaces.active.region_3d
    region3d.view_perspective='ORTHO';region3d.view_location=(0,-.06,0)
    region3d.view_distance=4.2;region3d.view_rotation=cameras[0].rotation_euler.to_quaternion()
    with bpy.context.temp_override(window=bpy.context.window,screen=bpy.context.screen,area=area,region=reg):
      bpy.ops.object.mode_set(mode='SCULPT')
      print('V037_FACE_STAGE:sculpt entered',flush=True)
      result=bpy.ops.brush.asset_activate(asset_library_type='ESSENTIALS',asset_library_identifier='',
             relative_asset_identifier='brushes/essentials_brushes-mesh_sculpt.blend/Brush/Draw')
      b=bpy.context.tool_settings.sculpt.brush
      if not b or 'FINISHED' not in result:raise RuntimeError('Known Draw brush asset activation failed: '+str(result))
      R['brush']={'name':b.name,'activation':sorted(result)}
      b.size=19;b.strength=.20
      R['brush']['size']=b.size;R['brush']['strength']=b.strength
      allstrokes=[]
      for side in (-1,1):
        for upper in (True,False):
          n=25
          # Align with the actual elliptical original V036 socket band around eye reference.
          arc=[]
          for j in range(n):
            t=math.pi*j/(n-1)
            theta=t if upper else -t
            x=side*(.55+.304*math.cos(theta));z=.405+.171*math.sin(theta)
            y=front_y(x,z)-.003
            xy=view3d_utils.location_3d_to_region_2d(reg,region3d,Vector((x,y,z)))
            if xy is None:raise RuntimeError('No valid front viewport projection')
            arc.append({'name':'V037_SmoothSocket','location':(x,y,z),
              'mouse':(float(xy.x),float(xy.y)),
              'mouse_event':(float(xy.x),float(xy.y)),
              'pressure':.21,'size':19,'time':j*.035,'is_start':j==0,'x_tilt':0.,'y_tilt':0.})
          status=bpy.ops.sculpt.brush_stroke(stroke=arc,mode='NORMAL',brush_toggle='SMOOTH')
          allstrokes.append({'side':side,'upper':upper,'points':len(arc),'native_toggle':'SMOOTH','op_status':sorted(status)})
      R['strokes']=allstrokes
      print('V037_FACE_STAGE:sculpt strokes completed',flush=True)
      bpy.ops.object.mode_set(mode='OBJECT')
    after=[tuple(v.co) for v in mesh.vertices]
    displacements=[math.dist(a,b) for a,b in zip(before,after)]
    eyezone=lambda p: abs(abs(p[0])-.55)<.48 and abs(p[2]-.405)<.34
    remote=lambda p:p[2]>1.05 or p[2]<-.16
    eye_change=[v for p,v in zip(before,displacements) if eyezone(p)]
    remote_change=[v for p,v in zip(before,displacements) if remote(p)]
    R['measured_change']={'total_moved_gt_1e7':sum(v>1e-7 for v in displacements),
      'eye_zone_moved_gt_1e7':sum(v>1e-7 for v in eye_change),
      'eye_zone_max':max(eye_change,default=0.),'remote_moved_gt_1e7':sum(v>1e-7 for v in remote_change),
      'remote_max':max(remote_change,default=0.),
      'global_max':max(displacements),'global_rms':math.sqrt(sum(d*d for d in displacements)/len(displacements))}
    R['after_previews']={}
    for camob in cameras:
      f=OUT/('AFTER_'+camob.name.split('.')[-1].upper()+'.png')
      R['after_previews'][camob.name]=render(scene,camob,f,True)
    path=OUT/'original_v036_sculpted_orbit_v037.blend';bpy.ops.wm.save_as_mainfile(filepath=str(path))
    R['blend']={'path':path.name,'sha256':sha(path),'bytes':path.stat().st_size}
    # Technical, pre-registered locality gates. Cosmetic approval is impossible here.
    t=R['measured_change']
    R['technical_gate']='PASS_SCOPED_LOCAL_REAL_SCULPT' if 10<=t['eye_zone_moved_gt_1e7']<=3500 and t['remote_moved_gt_1e7']==0 and .0000005<t['eye_zone_max']<.16 else 'HOLD_NO_CONTROLLED_LOCALITY'
    R['art_gate']='HOLD_INDEPENDENT_VISUAL_CRITIQUE';R['blender_native_sculpt']=True
except BaseException as e:
    R['technical_gate']='FAILED_NATIVE_RUN';R['error_type']=type(e).__name__;R['error_detail']=str(e)[:400]
    traceback.print_exc()
finally:
    (OUT/'RECEIPT.json').write_text(json.dumps(R,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print('V037_FACE='+json.dumps({'technical':R['technical_gate'],'change':R.get('measured_change'),
                'brush':R.get('brush'),'error':R.get('error_detail')},ensure_ascii=False),flush=True)
    if not bpy.app.background:
      try:bpy.ops.wm.quit_blender()
      except Exception as e:print('V037_FACE_QUIT_ERROR '+str(e),flush=True)
