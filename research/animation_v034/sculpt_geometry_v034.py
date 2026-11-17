"""V034 independently authored stylized facial volume reference, not anatomy-certified.
Analytic closed ellipsoid with smooth front-oriented facial volume fields. NO RETOPO.
A source sculpture/landmark planning fixture before changed orbital topology.
"""
import math
from collections import Counter

RX, RY, RZ=1.63, .98, 1.72
CY,CZ=.20,-.08
MERIDIANS=128
LAT_BANDS=72


def gauss(x,z,mx,mz,sx,sz):
    return math.exp(-.5*((x-mx)/sx)**2-.5*((z-mz)/sz)**2)


def front_volume(x,z):
    """Negative extends anterior; positive produces sockets/nostril recesses."""
    ax=abs(x)
    bridge=-.145*gauss(x,z,0,.26,.205,.48)
    nasal_tip=-.255*gauss(x,z,0,-.14,.24,.195)
    alae=-.115*gauss(ax,z,.235,-.20,.137,.18)
    # Bilateral recessed nostril vestibule *suggestion* — NOT punched nostril hole.
    nostril_recess=+.085*gauss(ax,z,.20,-.31,.092,.062)
    eye_socket=+.095*gauss(ax,z,.635,.44,.40,.245)
    brow=-.082*gauss(ax,z,.65,.79,.39,.16)
    cheek=-.116*gauss(ax,z,.97,-.19,.42,.37)
    philtrum=-.042*gauss(x,z,0,-.44,.19,.12)
    upper_lip=-.062*gauss(x,z,0,-.62,.42,.075)
    lower_lip=-.067*gauss(x,z,0,-.75,.40,.09)
    chin=-.085*gauss(x,z,0,-1.02,.40,.22)
    return bridge+nasal_tip+alae+nostril_recess+eye_socket+brow+cheek+philtrum+upper_lip+lower_lip+chin


def front_y(x,z):
    """Target surface Y on visible front at any inside-ellipsoid XZ coordinate."""
    q=1-(x/RX)**2-((z-CZ)/RZ)**2
    if q<=.02:raise ValueError('point outside safe facial frontal domain')
    sideface=math.sqrt(q)
    return CY-RY*sideface+(sideface**4)*front_volume(x,z)


def generate():
    """Two poles, LAT_BANDS-1 circumferential rows, a closed 3D preview sculpt."""
    verts=[];faces=[]
    for row in range(1,LAT_BANDS):
        lat=-math.pi/2+math.pi*row/LAT_BANDS
        cl=math.cos(lat)
        z=CZ+RZ*math.sin(lat)
        for j in range(MERIDIANS):
            longitude=2*math.pi*j/MERIDIANS
            # front (negative Y) is longitude=0
            x=RX*cl*math.sin(longitude)
            y=CY-RY*cl*math.cos(longitude)
            weight=max(0,math.cos(longitude))**4
            y+=weight*front_volume(x,z)
            verts.append((x,y,z))
    bottom=len(verts);verts.append((0,CY,CZ-RZ))
    top=len(verts);verts.append((0,CY,CZ+RZ))
    for row in range(LAT_BANDS-2):
        for j in range(MERIDIANS):
            j2=(j+1)%MERIDIANS
            a=row*MERIDIANS+j;b=row*MERIDIANS+j2
            c=(row+1)*MERIDIANS+j2;d=(row+1)*MERIDIANS+j
            faces.append((a,b,c,d))
    for j in range(MERIDIANS):
        j2=(j+1)%MERIDIANS
        faces.append((bottom,j2,j))
        last=(LAT_BANDS-2)*MERIDIANS
        faces.append((top,last+j,last+j2))
    return verts,faces


def landmarks():
    d={
        'glabella':(0,.63), 'nasal_root':(0,.45),'nasal_dorsum':(0,.15),
        'nasal_tip':(0,-.145),'left_ala':(-.23,-.19),'right_ala':(.23,-.19),
        'left_nostril_recess':(-.20,-.31),'right_nostril_recess':(.20,-.31),
        'left_inner_canthus':(-.305,.40),'right_inner_canthus':(.305,.40),
        'left_outer_canthus':(-.99,.40),'right_outer_canthus':(.99,.40),
        'left_cheek_malar':(-.98,-.17),'right_cheek_malar':(.98,-.17),
        'philtrum':(0,-.43),'upper_lip':(0,-.61),'chin':(0,-1.04)
    }
    return {k:(x,front_y(x,z),z) for k,(x,z) in d.items()}


def audit():
    v,f=generate()
    edges=Counter()
    for face in f:
        for a,b in zip(face,face[1:]+face[:1]):edges[tuple(sorted((a,b)))]+=1
    d=landmarks()
    # Smoothness proxy: maximum change in per-sample slope over the nasal root.
    # This is a local C2 analytic surface; quantified as finite second difference.
    h=.012
    samples=[]
    for x in (-.23,-.17,-.11,-.05,0,.05,.11,.17,.23):
        for z in (.02,.16,.30,.44,.58):
            secondx=abs(front_y(x+h,z)-2*front_y(x,z)+front_y(x-h,z))/(h*h)
            secondz=abs(front_y(x,z+h)-2*front_y(x,z)+front_y(x,z-h))/(h*h)
            samples.extend([secondx,secondz])
    bridge=d['nasal_dorsum'][1];tip=d['nasal_tip'][1]
    cheek=d['right_cheek_malar'][1];eye=d['right_inner_canthus'][1]
    return {'vertices':len(v),'faces':len(f),'quads':sum(len(x)==4 for x in f),
        'pole_triangles':sum(len(x)==3 for x in f), 'edge_2use_fraction':sum(x==2 for x in edges.values())/len(edges),
        'open_boundary_edges':sum(x==1 for x in edges.values()),'overconnected_edges':sum(x>2 for x in edges.values()),
        'center_tip_y':tip,'center_dorsum_y':bridge,'malar_cheek_y':cheek,'inner_canthus_y':eye,
        'centerline_depth_delta_tip_minus_dorsum':tip-bridge,
        'nasal_second_derivative_proxy_max':max(samples),'landmarks':d,
        'scope':'ORIGINAL_TARGET_SCULPT_SHAPE_ONLY_NOT_RETOPO_NOT_ANATOMY_CERTIFIED'}

if __name__=='__main__':
    import json
    print(json.dumps(audit(),ensure_ascii=False,indent=2))
