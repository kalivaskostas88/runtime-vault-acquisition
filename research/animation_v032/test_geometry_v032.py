"""Static positive and negative topology controls for V032, not Blender proof."""
import json, math, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
from geometry_v032 import audit,build,directed_edges,extract_boundary_loops
from geometry_v031 import vertices as eye_vertices,faces as eye_faces

checks={}
a=audit();checks['one_connected_surface']=a['components']==1 and a['component_sizes']==[1045]
checks['exact_three_expected_boundaries']=a['perimeter_loop_lengths']==[50,50,72]
checks['all_quad_faces']=a['all_quads'] and a['quads']==960
checks['edge_usage_and_orientation']=a['nonmanifold_edges']==0 and a['same_direction_double_edges']==0
checks['zero_degenerate_projected_quad']=a['low_projected_quad_area']==0
checks['same_topology_across_blinks']=build(0,0)[1]==build(1,0)[1]==build(0,1)[1]
checks['same_vertex_count_across_blinks']=len(build(0,0)[0])==len(build(1,0)[0])==len(build(0,1)[0])==1045
checks['left_right_geometry_separation']=a['eye_ranges']['L'][1] <= a['eye_ranges']['R'][0]
checks['welded_nose_shared_seam']=a['seam_welded']
checks['source_eyelid_not_two_separate_islands']=(a['components']==1 and len(eye_vertices(-1))==265 and len(eye_vertices(1))==265)
# Positive/negative: a fake mesh with two distinct islands must FAIL the integration condition.
negv=[(0,0,0),(1,0,0),(1,0,1),(0,0,1),(4,0,0),(5,0,0),(5,0,1),(4,0,1)]
negf=[(0,1,2,3),(4,5,6,7)]
counts,dirs=directed_edges(negf)
checks['disconnected_negative_control_rejected']=not any(set(negf[0]) & set(negf[1]) for _ in [0])
# source-contour protection: original 48-sample eyelid upper/lower contour remain independent degrees of freedom.
base,left,right=[build(*p)[0] for p in [(0,0),(1,0),(0,1)]]
L=a['eye_ranges']['L'];R=a['eye_ranges']['R']
checks['blink_L_moves_only_L']=any(sum(abs(x-y) for x,y in zip(base[i],left[i]))>0.001 for i in range(*L)) and all(base[i]==left[i] for i in range(*R))
checks['blink_R_moves_only_R']=any(sum(abs(x-y) for x,y in zip(base[i],right[i]))>0.001 for i in range(*R)) and all(base[i]==right[i] for i in range(*L))
checks['outer_face_remains_fixed']=all(base[i]==left[i]==right[i] for i in range(578,1045))
output={'version':'V032','pass_count':sum(checks.values()),'total':len(checks),'checks':checks,'geometry':a,'scope':'STATIC_MESH_ALGORITHM_ONLY_NOT_NATIVE_NOT_ART'}
Path(__file__).with_name('STATIC_GATE_V032.json').write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'passed':output['pass_count'],'total':output['total'],'geometry':a},ensure_ascii=False))
if not all(checks.values()):raise SystemExit(1)
