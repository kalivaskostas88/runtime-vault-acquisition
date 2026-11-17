"""V036 original head's honest static contract; art judgment is separate."""
import json,math,sys
from geometry_v036 import audit,front_y,landmarks,generate,EYE_X,EYE_Z,EYE_RAD
r=audit();e=r['eyes'];l=r['landmarks'];v,f=generate()
checks={
 'single_sculpt_closed_no_boundary':r['boundary_edges']==0,
 'no_nonmanifold_hyperconnected':r['nonmanifold_edges']==0,
 'every_sculpt_edge_two_use':r['edge_two_use_all'],
 'sufficient_new_shape_sampling':r['vertices']>13000,
 'mostly_quads_sculpt_reference':r['quads']>14000,
 'no_claim_quad_retopology':r['pole_triangles']>0,
 'jaw_tapered_stylized_silhouette':r['jaw_tapers'],
 'bilateral_eyes_same_depth':abs(e['L']['y']-e['R']['y'])<1e-10,
 'eye_radius_matches_design':abs(e['R']['radius']-.203)<1e-9,
 'eye_front_anterior_to_orbit_center': all(0<front_y(x['x'],x['z'])-x['front_eye_y']<.16 for x in e.values()),
 'eye_protrusion_reduced_from_v034_static_reference':all(front_y(x['x'],x['z'])-x['front_eye_y']<.301165 for x in e.values()),
 'nose_tip_forward_of_dorsum':r['nose_tip_anterior_to_bridge']<-.10,
 'upper_lip_forward_of_mouth_seam':r['upper_lip_anterior_to_mouth_seam']<-.02,
 'lower_lip_forward_of_mouth_seam':r['lower_lip_anterior_to_mouth_seam']<-.007,
 'nose_ala_bilateral':abs(l['ala.L'][1]-l['ala.R'][1])<1e-10,
 'cheeks_bilateral':abs(l['cheek.L'][1]-l['cheek.R'][1])<1e-10,
 'landmarks_defined':len(l)>=20,
 'domain_guard_rejects_polar_bad':False,
}
try:front_y(3,0)
except ValueError:checks['domain_guard_rejects_polar_bad']=True
status='PASS' if all(checks.values()) else 'FAIL'
print(json.dumps({'version':'V036','status':status,'checks':checks,'passed':sum(checks.values()),'total':len(checks),'sculpt_scope_only':True,'art':'HOLD'},indent=2))
if status!='PASS':sys.exit(1)
