"""V034 static preflight; positive and negative controls and precise scope."""
import math,json,pathlib
from sculpt_geometry_v034 import generate,front_y,front_volume,landmarks,audit
v,f=generate();a=audit();k=a['landmarks'];checks={}
checks['closed_original_target']=a['open_boundary_edges']==0 and a['edge_2use_fraction']==1
checks['no_nonmanifold_edges']=a['overconnected_edges']==0
checks['expected_sculpt_resolution']=a['vertices']==(72-1)*128+2 and a['faces']==(72-2)*128+256
checks['sculpt_is_not_retpo']=a['pole_triangles']==256 and a['quads']==(72-2)*128
checks['symmetry_l_r']=all(abs(k[l][1]-k[r][1])<1e-9 for l,r in [('left_ala','right_ala'),('left_inner_canthus','right_inner_canthus'),('left_cheek_malar','right_cheek_malar')])
checks['nasal_tip_in_front_of_bridge']=k['nasal_tip'][1]<k['nasal_dorsum'][1]-.09
checks['nasal_tip_in_front_of_malar']=k['nasal_tip'][1]<k['right_cheek_malar'][1]-.08
checks['nostril_inset_bounded']=front_y(.2,-.31)>front_y(.2,-.22)-.15
checks['all_finite']=all(math.isfinite(x) for xyz in v for x in xyz)
checks['smooth_c2_nasal_field']=a['nasal_second_derivative_proxy_max']<65
checks['anatomical_landmarks_present']=len(k)>=15
checks['negative_outside_domain_rejected']=False
try:front_y(3,3)
except ValueError:checks['negative_outside_domain_rejected']=True
checks['wrong_profile_rejected']=front_volume(0,-.145)<front_volume(1.5,-1.5)-.2
r={'version':'V034','static_tests':checks,'passed':sum(checks.values()),'total':len(checks),'sculpt_metrics':{z:x for z,x in a.items() if z!='landmarks'},'landmarks':k,'claim':'STATIC ORIGINAL TARGET SCULPT ONLY; no native Blender or artistic quality certified'}
pathlib.Path(__file__).with_name('STATIC_GATE_V034.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'passed':r['passed'],'total':r['total'],'metrics':r['sculpt_metrics']}))
if not all(checks.values()):raise SystemExit(1)
