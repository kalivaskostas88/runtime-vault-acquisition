#!/usr/bin/env python3
"""V037 primary technical capability lab for actual Blender sculpt brush strokes.
Not a facial artwork; no blind sculpting/reto, no copying teacher geometry, GS001 untouched.
Uses Blender 5.2 official asset brush and OperatorStrokeElement API.
"""
import bpy, os, json, pathlib, math, hashlib, traceback
from mathutils import Euler
ROOT=pathlib.Path(__file__).resolve().parent
OUT=ROOT/'native_probe_output'; OUT.mkdir(parents=True,exist_ok=True)
receipt={'version':'V037','scope':'MINIMAL_NATIVE_REAL_SCULPT_STROKE_FEASIBILITY_ONLY','blender':bpy.app.version_string,
         'source_method':['https://docs.blender.org/api/5.2/bpy.ops.sculpt.html',
                          'https://developer.blender.org/docs/release_notes/4.3/sculpt/',
                          'https://studio.blender.org/training/stylized-character-workflow/5d3a1fe14980f083715e410f/'],
         'brush_asset_activated':False,'operator_called':False,'geometry_modified':False,'art_pass':False,
         'original_face_changed':False,'GS001':'UNTOUCHED'}
try:
    bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=128,ring_count=64,location=(0,0,0))
    obj=bpy.context.object;obj.name='OriginalV037.BRUSH_CAPABILITY_TEST_ONLY'
    for p in obj.data.polygons:p.use_smooth=True
    before=[tuple(v.co) for v in obj.data.vertices]
    receipt['vertices']=len(before)
    area=next((a for a in bpy.context.screen.areas if a.type=='VIEW_3D'),None)
    if not area:raise RuntimeError('NO_VIEW3D_AREA_ON_HEADLESS')
    region=next((r for r in area.regions if r.type=='WINDOW'),None)
    if not region:raise RuntimeError('NO_VIEW3D_REGION')
    rv3=area.spaces.active.region_3d
    rv3.view_perspective='ORTHO'; rv3.view_distance=4.5
    rv3.view_rotation=Euler((math.pi/2,0,0),'XYZ').to_quaternion()
    context=dict(window=bpy.context.window,screen=bpy.context.screen,area=area,region=region)
    with bpy.context.temp_override(**context):
        bpy.ops.object.mode_set(mode='SCULPT')
        last_errors=[]
        for name in ['Draw','Clay Strips','Draw Sharp','Blob']:
            try:
                res=bpy.ops.brush.asset_activate(asset_library_type='ESSENTIALS', asset_library_identifier='',
                  relative_asset_identifier='brushes/essentials_brushes-mesh_sculpt.blend/Brush/'+name)
                brush=bpy.context.tool_settings.sculpt.brush
                if brush:
                    receipt['brush_asset_activated']=True;receipt['brush_name']=brush.name
                    receipt['asset_result']=sorted(res)
                    break
            except Exception as e:
                last_errors.append(f'{name}:{type(e).__name__}:{str(e)[:150]}')
        receipt['asset_errors']=last_errors
        brush=bpy.context.tool_settings.sculpt.brush
        if not brush:raise RuntimeError('NO_ACTIVE_BRUSH')
        receipt['brush_info']={'name':brush.name,'size':getattr(brush,'size',None),'strength':getattr(brush,'strength',None),'sculpt_tool':getattr(brush,'sculpt_tool',None)}
        if hasattr(brush,'size'):brush.size=96
        if hasattr(brush,'strength'):brush.strength=0.75
        cx,cy=region.width/2,region.height/2
        stroke=[]
        for i,t in enumerate(range(-8,9)):
            stroke.append({'name':'SculptV037','location':(t*.012,-math.sqrt(max(.001,1-(t*.012)**2)),0),
              'mouse':(cx+t*1.4,cy),'mouse_event':(cx+t*1.4,cy),
              'pressure':.95,'size':96,'time':i*.04,'is_start':i==0,'x_tilt':0.,'y_tilt':0.})
        receipt['stroke_points']=len(stroke)
        receipt['operator_result']=sorted(bpy.ops.sculpt.brush_stroke(stroke=stroke,mode='NORMAL'))
        receipt['operator_called']=True
        bpy.ops.object.mode_set(mode='OBJECT')
    after=[tuple(v.co) for v in obj.data.vertices]
    differences=[math.dist(a,b) for a,b in zip(before,after)]
    receipt['deformation']={'changed_vertices_gt_1e_7':sum(d>1e-7 for d in differences),
      'max_vertex_displacement':max(differences),'rms_displacement':math.sqrt(sum(d*d for d in differences)/len(differences))}
    receipt['geometry_modified']=receipt['deformation']['changed_vertices_gt_1e_7']>=5
    path=OUT/'v037_original_native_sculpt_probe.blend';bpy.ops.wm.save_as_mainfile(filepath=str(path))
    receipt['blend_file']={'name':path.name,'size':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
    receipt['status']='PASS_NATIVE_BRUSH_CHANGE' if receipt['geometry_modified'] else 'HOLD_BRUSH_DID_NOT_CHANGE_MESH'
except Exception as e:
    receipt['status']='FAILED_NATIVE_BRUSH_PROBE';receipt['error_type']=type(e).__name__
    receipt['error_message']=str(e)[:350]
    traceback.print_exc()
finally:
    (OUT/'BRUSH_PROBE_RECEIPT.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print('V037_PROBE='+json.dumps(receipt,ensure_ascii=False))
    if receipt['status']!='PASS_NATIVE_BRUSH_CHANGE':raise RuntimeError(receipt['status'])
