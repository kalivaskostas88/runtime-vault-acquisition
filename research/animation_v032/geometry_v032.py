"""Original dual-eye unified facial-mask quad topology.
Based on verified V031 curve/occlusion mechanism, expanded to one connected
facial skin patch with two intentional eye apertures and one face perimeter.
Teacher basis: MK Graphics V028 timed loop connection + Julien Kaspar loops/poles;
this code is independently authored, not a copied creator mesh.
"""
import math
from collections import Counter, defaultdict, deque
from pathlib import Path
from typing import Dict, List, Tuple
from geometry_v031 import N, RINGS, CX, CZ, vertices as eye_vertices, faces as eye_faces

CELL_CX=0.75
CELL_HW=0.75
CELL_HH=0.80
OUTER_STEPS=6


def face_y(x,z):
    # Synthetic original stylized face, not anatomy-certified.
    nose=-0.16*math.exp(-(x/0.21)**2-((z+0.31)/0.58)**2)
    brow=-0.030*math.exp(-((abs(x)-0.65)/0.43)**2-((z-0.92)/0.20)**2)
    return -0.62+0.12*(x/1.5)**2+0.055*((z-CZ)/1.5)**2 + nose + brow


def vertex_outer_fix(side,i,vert):
    """A SMALL and bounded original-integration-only outer-ring separation at the nasal bridge.
    The proven inner and supporting rings 0-3 and upper margin are unchanged.
    The V031 inner eye motion remains identical; new integration requires a fresh witness.
    """
    x,y,z=vert
    theta=2*math.pi*i/N
    # Original 4th outer support ring crosses center by ~0.020 m; move it
    # back to own side of the new x=0 shared nasal seam.
    taper=math.exp(-((math.cos(theta)+1)/0.18)**2)
    return (x+side*0.074*taper,y,z)


def rect_pt(side,i):
    theta=2*math.pi*i/N
    ct,st=math.cos(theta),math.sin(theta)
    div=max(abs(ct)/CELL_HW,abs(st)/CELL_HH)
    x=side*(CELL_CX+ct/div)
    z=CZ+st/div
    return (x,face_y(x,z),z)


def outer_target(x,z):
    theta=math.atan2((z-CZ)/CELL_HH,x/(2*CELL_CX))
    xx=2.10*math.cos(theta)
    zz=-0.055+2.13*math.sin(theta)
    return (xx,face_y(xx,zz)+0.24,zz)


def directed_edges(fs):
    c=Counter(); d=defaultdict(list)
    for f in fs:
        for a,b in zip(f,f[1:]+f[:1]):
            key=(min(a,b),max(a,b));c[key]+=1;d[key].append((a,b))
    return c,d


def extract_boundary_loops(fs):
    counts,direc=directed_edges(fs)
    adj=defaultdict(list)
    for k,n in counts.items():
        if n==1:
            a,b=k;adj[a].append(b);adj[b].append(a)
    if any(len(neighbors)!=2 for neighbors in adj.values()):
        raise ValueError('Noncycle or branching boundary')
    remaining=set(adj)
    loops=[]
    while remaining:
        first=min(remaining);loop=[first]; prev=None;cur=first
        for _ in range(len(adj)+2):
            choices=[n for n in adj[cur] if n!=prev]
            if len(choices)!=1 and prev is not None:raise ValueError('Unexpected boundary junction')
            nxt=choices[0]
            if nxt==first:break
            if nxt in loop:raise ValueError('Self-returning boundary')
            loop.append(nxt)
            prev,cur=cur,nxt
        else:raise ValueError('Open boundary')
        remaining.difference_update(loop)
        # Orient the loop to match face winding along its edges.
        key=(min(loop[0],loop[1]),max(loop[0],loop[1]))
        if direc[key][0]!=(loop[0],loop[1]):loop=[loop[0]]+list(reversed(loop[1:]))
        loops.append(loop)
    return loops


def build(left=0.0,right=0.0):
    allv=[];allf=[]; ranges={}; rect_indices=set()
    dedup={}
    def register(v):
        # Only shared boundary rect vertices are deduplicated. Other geometry
        # never auto-merged: an accidental overlap must be detected separately.
        q=tuple(round(c,8) for c in v)
        if q in dedup:return dedup[q]
        idx=len(allv); allv.append(v);dedup[q]=idx
        return idx
    for side,blink,label in [(-1,left,'L'),(1,right,'R')]:
        base=len(allv)
        vs=eye_vertices(side,blink)
        for i in range(N):
            idx=(len(RINGS)-1)*N+i
            vs[idx]=vertex_outer_fix(side,i,vs[idx])
        allv.extend(vs)
        ranges[label]=(base,len(allv))
        fs=eye_faces()
        # Ensure normals are uniform for the mirror side.
        allf.extend(tuple(base+j for j in (f if side==-1 else tuple(reversed(f)))) for f in fs)
        rectids=[register(rect_pt(side,i)) for i in range(N)]
        rect_indices.update(rectids)
        for i in range(N):
            j=(i+1)%N
            face=(base+(len(RINGS)-1)*N+i,base+(len(RINGS)-1)*N+j,rectids[j],rectids[i])
            allf.append(face if side==-1 else tuple(reversed(face)))

    # The two rectangular eye cells already share their x=0 nose-bridge edge.
    # Their union has exactly one outer perimeter loop of 72 edges.
    counts,direc=directed_edges(allf)
    candidates=[]
    for e,n in counts.items():
        if n==1 and set(e).issubset(rect_indices):candidates.append(direc[e][0])
    if len(candidates)!=72:raise ValueError(f'expected 72-cell exterior edges, got {len(candidates)}')
    direct={a:b for a,b in candidates}
    first=min(direct);loop=[first];cur=first
    for _ in range(72):
        nxt=direct[cur]
        if nxt==first:break
        if nxt in loop:raise ValueError('cell boundary repeats')
        loop.append(nxt);cur=nxt
    if len(loop)!=72 or direct[loop[-1]]!=first:raise ValueError('cell perimeter not loop')

    prev=loop
    base_points=[allv[i] for i in loop]
    exterior_targets=[outer_target(p[0],p[2]) for p in base_points]
    for k in range(1,OUTER_STEPS+1):
        t=k/OUTER_STEPS
        nextids=[]
        for p,target in zip(base_points,exterior_targets):
            # Ease toward more rounded facial silhouette, preserving count.
            x=(1-t)*p[0]+t*target[0]
            z=(1-t)*p[2]+t*target[2]
            y=(1-t)*p[1]+t*target[1]
            nextids.append(len(allv));allv.append((x,y,z))
        for i in range(len(loop)):
            j=(i+1)%len(loop)
            # Old boundary direction prev[i] -> prev[j], new face opposite.
            allf.append((prev[j],prev[i],nextids[i],nextids[j]))
        prev=nextids

    return allv,allf,{'eye_ranges':ranges,'rect_indices':sorted(rect_indices),
                      'outer_loop_indices':prev,'cell_perimeter_count':len(loop),
                      'first_module_end':ranges['L'][1],
                      'facial_skin_connected':True}


def audit(left=0,right=0):
    vs,fs,info=build(left,right)
    counts,directed=directed_edges(fs)
    boundary={e for e,n in counts.items() if n==1}
    nonmanifold=[e for e,n in counts.items() if n>2]
    bad_direction=[e for e,pairs in directed.items() if len(pairs)==2 and pairs[0]==pairs[1]]
    adj=[set() for _ in vs]
    for a,b in counts:
        adj[a].add(b);adj[b].add(a)
    seen=set();components=[]
    for i in range(len(vs)):
        if i in seen:continue
        q=deque([i]);seen.add(i);cnt=0
        while q:
            a=q.popleft();cnt+=1
            for b in adj[a]:
                if b not in seen:seen.add(b);q.append(b)
        components.append(cnt)
    loops=extract_boundary_loops(fs)
    all_quads=all(len(f)==4 and len(set(f))==4 for f in fs)
    nonzero=sum(1 for f in fs if quad_projected_area([vs[i] for i in f])<=1e-7)
    return {'vertices':len(vs),'quads':len(fs),'components':len(components),
            'component_sizes':components,'perimeter_loop_lengths':sorted(len(l) for l in loops),
            'boundary_edges':len(boundary),'nonmanifold_edges':len(nonmanifold),
            'same_direction_double_edges':len(bad_direction),'all_quads':all_quads,
            'low_projected_quad_area':nonzero,'seam_welded':info['cell_perimeter_count']==72,
            'eye_ranges':info['eye_ranges']}


def quad_projected_area(vs):
    # Polygon x-z projected area; this is not 3D curvature quality.
    return abs(sum(vs[i][0]*vs[(i+1)%len(vs)][2]-vs[(i+1)%len(vs)][0]*vs[i][2] for i in range(len(vs))))/2

if __name__=='__main__':
    import json
    r=audit()
    print(json.dumps(r,ensure_ascii=False,indent=2))
    assert r['components']==1
    assert r['nonmanifold_edges']==0 and r['same_direction_double_edges']==0
    assert r['perimeter_loop_lengths']==[50,50,72]
    assert r['all_quads'] and r['seam_welded']
