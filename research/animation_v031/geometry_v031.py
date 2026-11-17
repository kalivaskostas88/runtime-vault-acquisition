"""Original V031 depth-conforming orbital module with connected upper eyelid margin. No head topology integration.
Contours-first quads, 48 angular samples, 5 curved concentric rings. Static math
independent of Blender. The geometry is an original demonstration, not a
reproduction or redistributed mesh from MK Graphics/Blender Studio.
"""
import math
N=48
# Relative ring factors from lid rim to upper cheek/brow support.
RINGS=(1.0,1.10,1.26,1.49,1.78)
CX=0.63
CZ=0.40
EYE_W=0.365
UP_H=0.220
LOW_H=0.175

def side_index(side):
    if side not in (-1,1): raise ValueError('side must be -1 or +1')
    return side

def eye_v(side, ring, index, closure):
    side_index(side)
    if not 0 <= index < N or not 0 <= ring < len(RINGS) or not 0 <= closure <=1:
        raise ValueError('out of range')
    a=2*math.pi*index/N
    k=RINGS[ring]
    xx=math.cos(a)
    zz=math.sin(a)
    # Inwards rim and near support deform, outer face rings fade out.
    influence={0:1.0,1:0.93,2:0.53,3:0.17,4:0.0}[ring]
    contraction=closure*influence
    h=(UP_H if zz>=0 else LOW_H)
    # A small nonzero closed slit protects against topological degeneration,
    # but is not a guarantee of photographic eyelid closure.
    target_h=0.0057 if zz>=0 else 0.0052
    hh=(1-contraction)*h+contraction*target_h
    x=side*(CX+k*EYE_W*xx)
    z=CZ+k*hh*zz
    # Front negative Y; eyelid crease is raised forward at rim relative to cheek.
    # Eye globe radius 0.265 frontmost Y=-0.865 in the center.
    y= -0.955 + 0.28*(k-1)/(.78) + 0.052*(k*xx)**2 + 0.026*(k*zz)**2
    # Slight axial movement simulates lid roll; limited to inner rings.
    y-=0.014*closure*influence*abs(zz)
    # Anatomically motivated, bounded frontal eye-surface clearance envelope.
    # The sphere is purely our original synthetic test object, not a copied asset.
    # This fixes the causal depth penetration seen in V029 rather than exaggerating
    # the blink amount. The resulting art quality is still unproven.
    globe_radius=0.272
    projected=(x-side*CX)**2+(z-CZ)**2
    if projected<globe_radius**2:
        globe_front_y=-0.625-math.sqrt(globe_radius**2-projected)
        y=min(y,globe_front_y-0.065)
    return (x,y,z)

def upper_margin_vertex(side,index,closure):
    """Single skin-attached upper lash/waterline quad rim, not a floating occluder.
    A closed upper lid is deliberately a little anterior to and overlapping the
    lower rim; there is no invisible globe toggle or untested expression slider.
    """
    if not 0 <= index <= N//2:raise ValueError('invalid upper margin index')
    x,y,z=eye_v(side,0,index,closure)
    taper=0.35+0.65*abs(math.sin(2*math.pi*index/N))
    z-=(0.0015+0.038*closure)*taper
    y-=(0.004+0.040*closure)*taper
    return (x,y,z)

def vertices(side,closure=0.0):
    main=[eye_v(side,k,i,closure) for k in range(len(RINGS)) for i in range(N)]
    margin=[upper_margin_vertex(side,i,closure) for i in range(N//2+1)]
    return main+margin

def faces():
    # Original winding is mirrored later in Blender (and can invert normals).
    fs=[(k*N+i,k*N+(i+1)%N,(k+1)*N+(i+1)%N,(k+1)*N+i)
             for k in range(len(RINGS)-1) for i in range(N)]
    # Face winding on the shared eye rim is opposite to the first annulus band.
    first=len(RINGS)*N
    fs.extend((i+1,i,first+i,first+i+1) for i in range(N//2))
    return fs

def aperture_area(closure):
    # projected sampled polygon area of the inside border
    pts=[eye_v(1,0,i,closure) for i in range(N)]
    return abs(sum(pts[i][0]*pts[(i+1)%N][2]-pts[(i+1)%N][0]*pts[i][2] for i in range(N)))/2

def boundary_edges(faces_data):
    from collections import Counter
    count=Counter()
    for f in faces_data:
        for a,b in zip(f,f[1:]+f[:1]):count[tuple(sorted((a,b)))]+=1
    return {e:n for e,n in count.items() if n!=2}

def center_gap(closure):
    upper=eye_v(1,0,N//4,closure)[2];lower=eye_v(1,0,3*N//4,closure)[2]
    return upper-lower

if __name__=='__main__':
    fs=faces()
    a0=aperture_area(0);a05=aperture_area(.5);a1=aperture_area(1)
    assert N==48 and len(fs)==(len(RINGS)-1)*N+N//2
    assert a0>a05>a1>0
    assert a1/a0<.04,(a0,a1)
    assert len(boundary_edges(fs))==2*N+2
    assert all(len(f)==4 for f in fs)
    for k in range(len(RINGS)):
        assert all(math.isclose(eye_v(1,k,i,0)[0],-eye_v(-1,k,i,0)[0],abs_tol=1e-10) for i in range(N))
    print({'rings':len(RINGS),'verts_per_eye':len(vertices(1)),'quads_per_eye':len(fs),'boundary_edges':len(boundary_edges(fs)),
          'open_area':round(a0,7),'half_area':round(a05,7),'closed_area':round(a1,7),'closed_to_open_ratio':round(a1/a0,5),'center_gap_open':center_gap(0),'center_gap_closed':center_gap(1)})
