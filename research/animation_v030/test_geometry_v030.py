#!/usr/bin/env python3
"""Independent bounded math preflight; Blender runtime validation separately required."""
import math,json,sys,pathlib,hashlib
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
import geometry_v030 as g
checks={}
checks['source_quads_count'] = len(g.faces())==192 and all(len(q)==4 for q in g.faces())
checks['source_verts_count'] = all(len(g.vertices(s))==240 for s in [-1,1])
checks['only_two_expected_annulus_boundaries']=len(g.boundary_edges(g.faces()))==2*g.N
checks['no_triple_connected_edges']=all(c==1 for c in g.boundary_edges(g.faces()).values())
checks['positive_area_and_strict_monotonic_blink']=all(g.aperture_area(a)>g.aperture_area(b)>0 for a,b in [(0,.25),(.25,.5),(.5,.75),(.75,1)])
checks['closed_area_under_four_percent_of_open']=0<g.aperture_area(1)/g.aperture_area(0)<.04
checks['continuous_open_to_closed_gap']=0<g.center_gap(1)<.02 and g.center_gap(0)>.35
checks['bilateral_reflection_exact']=all(all(math.isclose(g.eye_v(1,k,i,t)[0],-g.eye_v(-1,k,i,t)[0],abs_tol=1e-10) and all(math.isclose(g.eye_v(1,k,i,t)[j],g.eye_v(-1,k,i,t)[j],abs_tol=1e-10) for j in [1,2]) for i in range(g.N)) for t in [0,.5,1] for k in range(len(g.RINGS)))
checks['outer_ring_unmodified_on_blink']=all(g.eye_v(s,4,i,0)==g.eye_v(s,4,i,1) for s in [-1,1] for i in range(g.N))
checks['canthi_midline_locked']=all(math.isclose(g.eye_v(s,0,i,0)[2],g.eye_v(s,0,i,1)[2],abs_tol=1e-10) for s in [-1,1] for i in [0,g.N//2])
checks['negative_rectangle_topology_not_used']=all(abs(g.eye_v(1,0,i,0)[2]-g.CZ)>0 for i in [g.N//4,3*g.N//4]) and len(g.faces())>4
def _reject(f):
 try:f();return False
 except ValueError:return True
checks['invalid_parameters_rejected']=all((lambda fn: _reject(fn)) (lambda a=a,b=b,c=c,d=d: g.eye_v(a,b,c,d)) for a,b,c,d in [(0,0,0,0),(1,-1,0,0),(1,0,-1,0),(1,0,0,2)])
def_shas={name:hashlib.sha256((pathlib.Path(__file__).parent/name).read_bytes()).hexdigest() for name in ['geometry_v030.py','build_blender_v030.py']}
res={'version':'V030','domain':'STATIC_GEOMETRY_PREFLIGHT_ONLY','source_files_sha256':def_shas,'checks':checks,'pass':sum(checks.values()),'total':len(checks),'native_blender':'NOT_PROVEN_BY_THIS_TEST','art':'NOT_PROVEN','GS001':'UNTOUCHED'}
(pathlib.Path(__file__).parent/'STATIC_PREFLIGHT_V030.json').write_text(json.dumps(res,indent=2,ensure_ascii=False)+'\n')
print(json.dumps({'pass':res['pass'],'total':res['total'],'failed':[x for x,v in checks.items() if not v]},ensure_ascii=False))
if res['pass']!=res['total']:sys.exit(1)
