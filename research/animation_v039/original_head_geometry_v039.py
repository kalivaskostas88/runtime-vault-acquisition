"""Original planar-to-soft cranial blockout geometry: no copied artist meshes.
Pure Python so geometry/topology and failure controls can run without Blender.
V039 is a simple art research fixture, not a production-quality face.
"""
from math import sin, cos, pi, sqrt
from collections import Counter
N_RING=92
N_AROUND=128
Z_CENTER=0.0
Z_RADIUS=1.48
# z, width multiplier, depth multiplier, depth-offset: intentional cranium/cheek/jaw/stern taper.
PROFILE=[
 (-1.46,.71,.80,.04), (-1.12,.76,.79,.02),(-.95,.80,.85,0),
 (-.64,.88,.95,-.02),(-.25,.96,1.02,-.04),(.18,1.02,.96,-.04),
 (.58,1.00,.92,-.01),(.94,1.04,.99,.01),(1.27,1.02,.93,.03),(1.46,.96,.91,.05)
]

def lerp(a,b,t):return a+(b-a)*t

def station(z):
    for i in range(len(PROFILE)-1):
        a,b=PROFILE[i],PROFILE[i+1]
        if z<=b[0]:
            t=max(0.,min(1.,(z-a[0])/(b[0]-a[0])))
            s=t*t*(3-2*t)
            return tuple(lerp(a[k],b[k],s) for k in range(1,4))
    return PROFILE[-1][1:]

def shell_front_y(x,z):
    w,d,cy=station(z)
    q=max(0.,1-(z/Z_RADIUS)**2)
    rho=w*1.02*sqrt(q)
    if abs(x)>rho:raise ValueError('Point outside head silhouette')
    return cy-.91*d*sqrt(q)*sqrt(max(0,1-(x/rho)**2))

def build():
    verts=[];faces=[]
    for i in range(1,N_RING):
        phi=-pi/2+pi*i/N_RING
        cl=cos(phi); z=Z_RADIUS*sin(phi)
        w,d,cy=station(z)
        for j in range(N_AROUND):
            theta=2*pi*j/N_AROUND
            x=1.02*w*cl*sin(theta)
            y=cy-.91*d*cl*cos(theta)
            verts.append((x,y,z))
    lower=len(verts);verts.append((0,station(-Z_RADIUS)[2],-Z_RADIUS))
    upper=len(verts);verts.append((0,station(Z_RADIUS)[2],Z_RADIUS))
    for i in range(N_RING-2):
        for j in range(N_AROUND):
            k=(j+1)%N_AROUND; b=i*N_AROUND
            faces.append((b+j,b+k,b+N_AROUND+k,b+N_AROUND+j))
    topstart=(N_RING-2)*N_AROUND
    for j in range(N_AROUND):
        k=(j+1)%N_AROUND
        faces.append((lower,k,j))
        faces.append((upper,topstart+j,topstart+k))
    return verts,faces

def audit():
    verts,faces=build();e=Counter()
    for face in faces:
        for a,b in zip(face,face[1:]+face[:1]):e[tuple(sorted((a,b)))]+=1
    return dict(vertices=len(verts),faces=len(faces),all_edges_two=all(v==2 for v in e.values()),
      boundary=sum(v==1 for v in e.values()),overconnected=sum(v>2 for v in e.values()),
      lateral_width_at_cheek=station(-.25)[0],jaw_width=station(-1.12)[0],
      cranium_width=station(.94)[0],is_original=True,
      scope='PLANAR_HEAD_BLOCKOUT_ONLY_NOT_FACE_ANATOMY_OR_ART_APPROVAL')
if __name__=='__main__':
 import json;print(json.dumps(audit(),indent=2))
