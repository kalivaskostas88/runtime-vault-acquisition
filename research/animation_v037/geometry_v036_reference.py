"""V036 ORIGINAL stylized facial-volume sculpt study, sourced from real V035 teaching.
Not a traced teacher mesh, not face retopology, not rig/deformation or certified anatomy.
Broad head/jaw proportions before eye-orbit, nose, lip and chin volume transitions.
"""
import math
from collections import Counter
RX,RY,RZ=1.34, .90, 1.58
CY,CZ=.16,-.04
MERIDIANS,LAT_BANDS=160,96
EYE_X,EYE_Z,EYE_RAD=.55,.405,.203

def g(x,z,mx,mz,sx,sz):
    return math.exp(-.5*((x-mx)/sx)**2-.5*((z-mz)/sz)**2)

def head_x_radius(z):
    # Original stylized wedge-like jaw, more lateral volume at cheek/brow.
    low=max(0,min(1,(.05-z)/1.40))
    return RX*(1-.185*low)+.06*g(0,z,0,.30,100,.33)

def front_volume(x,z):
    ax=abs(x)
    # Major sculpt volumes, not paint/shading tricks.
    brow=-.115*g(ax,z,.55,.72,.33,.145)
    glabella=-.094*g(x,z,0,.55,.24,.26)
    inner_orbit=+.18*g(ax,z,EYE_X,EYE_Z,.305,.204)
    # Embedded orbital tissue is a continuous shell ridge around an elliptical recess.
    rad=math.sqrt(((ax-EYE_X)/.305)**2+((z-EYE_Z)/.172)**2)
    rim=-.145*(1+.35*max(0,(ax-EYE_X)/.305))*math.exp(-.5*((rad-1)/.225)**2)*g(ax,z,EYE_X,EYE_Z,.48,.36)
    upper_lid=-.031*g(ax,z,EYE_X,.555,.305,.063)
    lower_lid=-.045*g(ax,z,EYE_X,.247,.314,.068)
    tear_trough=+.023*g(ax,z,.64,.157,.27,.047)
    cheek=-.120*g(ax,z,.79,-.045,.37,.32)
    under_cheek=+.016*g(ax,z,1.02,-.41,.25,.20)
    # Deliberate central bridge and tip, with bilateral alae and recessed lower nostril cues.
    root=-.068*g(x,z,0,.45,.165,.24)
    dorsum=-.198*g(x,z,0,.13,.122,.32)
    tip=-.312*g(x,z,0,-.205,.195,.132)
    alae=-.151*g(ax,z,.183,-.282,.095,.105)
    nostril_recess=+.141*g(ax,z,.180,-.370,.072,.042)
    columella=-.048*g(x,z,0,-.350,.065,.072)
    # A curved cupid's bow and separation between upper/lower labial volumes.
    philtrum=-.048*g(x,z,0,-.454,.112,.12)
    cupids=-.031*g(ax,z,.13,-.575,.088,.055)
    upper_lip=-.125*g(x,z,0,-.603,.326,.059)
    lower_lip=-.106*g(x,z,0,-.739,.331,.073)
    mouth_seam=+.080*g(x,z,0,-.675,.328,.030)
    commissures=+.046*g(ax,z,.342,-.656,.058,.052)
    chin=-.102*g(x,z,0,-1.022,.41,.19)
    chin_sulcus=+.027*g(x,z,0,-.874,.36,.044)
    return sum((brow,glabella,inner_orbit,rim,upper_lid,lower_lid,tear_trough,cheek,under_cheek,
                root,dorsum,tip,alae,nostril_recess,columella,philtrum,cupids,upper_lip,lower_lip,
                mouth_seam,commissures,chin,chin_sulcus))

def front_y(x,z):
    rx=head_x_radius(z)
    q=1-(x/rx)**2-((z-CZ)/RZ)**2
    if q<=.024: raise ValueError('outside frontal source shape domain')
    sideface=math.sqrt(q)
    return CY-RY*sideface+(sideface**4)*front_volume(x,z)

def generate():
    verts=[];faces=[]
    for row in range(1,LAT_BANDS):
        lat=-math.pi/2+math.pi*row/LAT_BANDS
        cl=math.cos(lat);z=CZ+RZ*math.sin(lat);rx=head_x_radius(z)
        for j in range(MERIDIANS):
            lon=2*math.pi*j/MERIDIANS
            x=rx*cl*math.sin(lon)
            weight=max(0,math.cos(lon))**4
            y=CY-RY*cl*math.cos(lon)+weight*front_volume(x,z)
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
    labels={'glabella':(0,.55),'brow.L':(-.55,.71),'brow.R':(.55,.71),
        'canthus.inner.L':(-.245,.405),'canthus.inner.R':(.245,.405),
        'canthus.outer.L':(-.855,.405),'canthus.outer.R':(.855,.405),
        'nose.root':(0,.44),'nose.dorsum':(0,.10),'nose.tip':(0,-.206),
        'ala.L':(-.19,-.29),'ala.R':(.19,-.29),
        'nostril.L':(-.182,-.372),'nostril.R':(.182,-.372),
        'cheek.L':(-.79,-.06),'cheek.R':(.79,-.06),
        'mouth.left':(-.34,-.675),'mouth.right':(.34,-.675),
        'upper.lip':(0,-.595),'lower.lip':(0,-.742),
        'chin':(0,-1.02)}
    return {k:(x,front_y(x,z),z) for k,(x,z) in labels.items()}

def eye_targets():
    # Eyeballs lie *within a modeled orbital recess*, without face-mask retopology.
    # Their placement is a candidate; not a professional eyeball-depth threshold.
    result={}
    for side,label in [(-1,'L'),(1,'R')]:
        x=side*EYE_X
        # At the outer eye corner the skin should be in front of the globe edge.
        rim_y=front_y(x+side*.288,EYE_Z)
        cy=front_y(x,EYE_Z)+EYE_RAD-.090
        result[label]={'x':x,'y':cy,'z':EYE_Z,'radius':EYE_RAD,
                       'rim_y':rim_y,'front_eye_y':cy-EYE_RAD,
                       'eye_front_to_outer_rim':rim_y-(cy-EYE_RAD)}
    return result

def audit():
    v,f=generate();edge_use=Counter()
    for face in f:
        for a,b in zip(face,face[1:]+face[:1]): edge_use[tuple(sorted((a,b)))]+=1
    d=landmarks();eyes=eye_targets()
    n0=front_y(0,-.20);mid=front_y(0,.20)
    jaw_hi=head_x_radius(.35);jaw_lo=head_x_radius(-1.02)
    # Contrast analytical orbit center (recess) and rim (anterior protrusion).
    orbit_contrast=front_y(EYE_X,EYE_Z)-front_y(EYE_X+.288,EYE_Z)
    return {'vertices':len(v),'faces':len(f),'quads':sum(len(p)==4 for p in f),
       'pole_triangles':sum(len(p)==3 for p in f),
       'boundary_edges':sum(c==1 for c in edge_use.values()),
       'nonmanifold_edges':sum(c>2 for c in edge_use.values()),
       'edge_two_use_all':all(c==2 for c in edge_use.values()),
       'jaw_tapers':jaw_lo<jaw_hi,
       'eye_orbit_center_recess_to_outer_rim':orbit_contrast,
       'nose_tip_anterior_to_bridge':n0-mid,
       'upper_lip_anterior_to_mouth_seam':front_y(0,-.602)-front_y(0,-.675),
       'lower_lip_anterior_to_mouth_seam':front_y(0,-.743)-front_y(0,-.675),
       'landmarks':d,'eyes':eyes,
       'scope':'ORIGINAL_STYLIZED_3D_SCULPT_VOLUME_FIXTURE_NOT_ANATOMY_CERTIFIED_NOT_RETOPO_NOT_BLINK'}

if __name__=='__main__':
 import json
 print(json.dumps(audit(),indent=2,ensure_ascii=False))
