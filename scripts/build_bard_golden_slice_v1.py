import argparse, json, math, pathlib, hashlib, subprocess, shutil
import cv2
import numpy as np

EXPECTED_SHA='7e28541eac025b511b589644a969d2e383a50dadaf0ce56fa9b2246a298fbb18'
CROP=(115,35,930,1040) # x0,y0,x1,y1 source
FPS=25
DUR=8.0
CUTS=[('S1_MASTER',0.0,2.52),('S2_MEDIUM',2.52,3.60),('S3_CLOSE',3.60,6.20),('S4_RETURN',6.20,8.0)]
PLACEMENT_640={
 'S1_MASTER': dict(scale=.205,cx=321,top=64,occ=250,shadow_y=246,shadow_rx=65),
 'S2_MEDIUM': dict(scale=.285,cx=321,top=60,occ=283,shadow_y=278,shadow_rx=78),
 'S3_CLOSE': dict(scale=.455,cx=321,top=-12,occ=350,shadow_y=346,shadow_rx=105),
 'S4_RETURN': dict(scale=.285,cx=320,top=58,occ=283,shadow_y=278,shadow_rx=82),
}
MOUTH_STATES={
 'M0': dict(width=28.0, open=0.0, jaw=0.0, round=0.0),
 'M1': dict(width=30.0, open=4.5, jaw=1.2, round=0.0),
 'ME': dict(width=38.0, open=7.0, jaw=1.7, round=0.0),
 'MO': dict(width=22.0, open=18.0, jaw=3.0, round=1.0),
 'M3': dict(width=38.0, open=22.0, jaw=4.2, round=0.0),
}
# crop-space regions from source-bound control map
HEAD=(275,10,210,290)
TORSO=(230,280,285,305)
STRUM=(175,410,150,190)
CHORD=(435,360,125,150)
EYES=[(347,133),(384,133)]
MOUTH=(378,190)
BLINKS=[1.72,4.18,6.62]
HEAD_KEYS=[(0.34,0.82,-0.34,-0.35),(1.72,2.18,0.30,0.28),(5.15,5.65,-0.26,-0.25),(7.25,7.8,0.30,0.22)]
STRUMS=[0.4,1.0,1.96,3.24,5.36,5.8,6.56,7.68]
CHORDS=[1.56,2.88,4.08]
MOUTH_SEGS=[
(0,.08,'M0'),(.08,.38,'ME'),(.38,.5,'M1'),(.5,.6,'ME'),(.6,.82,'M1'),(.82,1.18,'ME'),
(1.18,1.88,'MO'),(1.88,1.98,'M0'),(1.98,2.62,'M1'),(2.62,2.72,'M1'),(2.72,3.48,'M1'),
(3.48,3.6,'M1'),(3.6,4.68,'M0'),(4.68,4.8,'M0'),(4.8,5.15,'MO'),(5.15,5.27,'M1'),
(5.27,5.5,'M1'),(5.5,6.1,'M1'),(6.1,6.22,'M1'),(6.22,6.58,'M3'),(6.58,7.08,'MO'),
(7.08,7.18,'M0'),(7.18,7.58,'M3'),(7.58,7.68,'M1'),(7.68,8.0,'ME')]

def sha256(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for c in iter(lambda:f.read(1024*1024),b''): h.update(c)
    return h.hexdigest()

def build_matte(img):
    H,W=img.shape[:2]
    m=np.full((H,W),cv2.GC_BGD,np.uint8)
    poly=np.array([[435,48],[365,75],[325,125],[300,220],[255,315],[225,450],[180,620],[160,830],[120,1040],[85,1160],
      [125,1180],[185,1140],[240,1040],[280,960],[330,980],[360,1200],[285,1360],[315,1450],[430,1510],
      [520,1520],[610,1490],[715,1510],[760,1435],[720,1310],[690,1160],[745,1010],[840,1170],[925,1270],
      [950,1230],[915,1050],[880,850],[845,660],[810,500],[780,350],[720,250],[660,140],[590,80],[530,45]],np.int32)
    cv2.fillPoly(m,[poly],cv2.GC_PR_FGD)
    for x0,y0,x1,y1 in [(430,100,590,270),(350,330,690,740),(300,470,660,700),(330,750,690,1100),(340,1120,680,1420)]:
        m[y0:y1,x0:x1]=cv2.GC_FGD
    b=18; m[:b,:]=0; m[-b:,:]=0; m[:,:b]=0; m[:,-b:]=0
    bgd=np.zeros((1,65),np.float64); fgd=np.zeros((1,65),np.float64)
    cv2.grabCut(img,m,None,bgd,fgd,8,cv2.GC_INIT_WITH_MASK)
    mask=np.where((m==cv2.GC_FGD)|(m==cv2.GC_PR_FGD),255,0).astype(np.uint8)
    n,labels,stats,_=cv2.connectedComponentsWithStats(mask,8)
    if n>1:
        idx=1+np.argmax(stats[1:,cv2.CC_STAT_AREA]); mask=np.where(labels==idx,255,0).astype(np.uint8)
    mask=cv2.morphologyEx(mask,cv2.MORPH_CLOSE,np.ones((3,3),np.uint8),iterations=1)
    mask=cv2.GaussianBlur(mask,(0,0),1.2)
    rgba=cv2.cvtColor(img,cv2.COLOR_BGR2BGRA); rgba[:,:,3]=mask
    x0,y0,x1,y1=CROP
    return rgba[y0:y1,x0:x1].copy()

def rectmask(shape, rect, feather=0.18):
    h,w=shape[:2]; x,y,rw,rh=rect
    x=max(0,int(round(x))); y=max(0,int(round(y))); rw=max(2,min(w-x,int(round(rw)))); rh=max(2,min(h-y,int(round(rh))))
    m=np.zeros((h,w),np.float32); m[y:y+rh,x:x+rw]=1.0
    k=max(3,int(round(min(rw,rh)*feather))); k += 1-k%2
    m=cv2.GaussianBlur(m,(k,k),0); mx=m.max()
    if mx>0:m/=mx
    return m[...,None]

def affine_local(img, rect, angle=0, dx=0, dy=0, sx=1.0, sy=1.0, feather=.20):
    # ROI-only transform: avoids warping the full 815x1005 sprite for tiny local motion.
    h,w=img.shape[:2]; x,y,rw,rh=[float(v) for v in rect]
    pad=max(8,int(round(max(rw,rh)*0.28)))
    x0=max(0,int(math.floor(x-pad))); y0=max(0,int(math.floor(y-pad)))
    x1=min(w,int(math.ceil(x+rw+pad))); y1=min(h,int(math.ceil(y+rh+pad)))
    if x1<=x0 or y1<=y0: return img
    patch=img[y0:y1,x0:x1].copy(); ph,pw=patch.shape[:2]
    cx=(x+rw/2)-x0; cy=(y+rh/2)-y0
    M=cv2.getRotationMatrix2D((cx,cy),angle,1.0)
    M[0,0]*=sx; M[0,1]*=sx; M[1,0]*=sy; M[1,1]*=sy
    M[0,2]+=(1-sx)*cx + dx; M[1,2]+=(1-sy)*cy + dy
    alt=cv2.warpAffine(patch,M,(pw,ph),flags=cv2.INTER_CUBIC,borderMode=cv2.BORDER_REFLECT_101)
    mask=np.zeros((ph,pw),np.float32)
    rx0=max(0,int(round(x-x0))); ry0=max(0,int(round(y-y0)))
    rx1=min(pw,int(round(x+rw-x0))); ry1=min(ph,int(round(y+rh-y0)))
    mask[ry0:ry1,rx0:rx1]=1.0
    k=max(3,int(round(min(rw,rh)*feather))); k += 1-k%2
    mask=cv2.GaussianBlur(mask,(k,k),0); mx=mask.max()
    if mx>0: mask/=mx
    m=mask[...,None]
    out=np.clip(patch.astype(np.float32)*(1-m)+alt.astype(np.float32)*m,0,255).astype(np.uint8)
    img[y0:y1,x0:x1]=out
    return img

def pulse(t,center,half):
    d=abs(t-center)
    if d>=half:return 0.0
    # raised cosine for smooth attack/release
    return 0.5*(1+math.cos(math.pi*d/half))

def shot_for(t):
    for sid,a,b in CUTS:
        if a <= t < b or (sid=='S4_RETURN' and t<=b): return sid
    return 'S4_RETURN'

def state_at(t):
    for a,b,s in MOUTH_SEGS:
        if a<=t<b or (b>=8 and t<=b): return s
    return 'M0'

def controls_for_frames(n):
    # state targets -> temporally smoothed numeric controls, avoiding mouth pops
    vals=[]
    prev=np.array([28.,0.,0.,0.],np.float32)
    for i in range(n):
        t=i/FPS; s=MOUTH_STATES[state_at(t)]
        target=np.array([s['width'],s['open'],s['jaw'],s['round']],np.float32)
        alpha=.58 if i else 1.0
        prev=(1-alpha)*prev+alpha*target
        vals.append(prev.copy())
    return vals

def mouth_anim(sprite, ctrl):
    width,opn,jaw,rnd=map(float,ctrl)
    # Deliberately restrained: config geometry is semantic, visual magnitude is ~35%.
    opn*=0.42; jaw*=0.44
    cx,cy=MOUTH
    # jaw shift localized below mouth, not whole face
    if jaw>0.05:
        sprite=affine_local(sprite,(cx-48,cy-2,96,62),dy=jaw,feather=.34)
    if opn>0.15:
        # Separate upper/lower lip by tiny opposing local transforms.
        sprite=affine_local(sprite,(cx-38,cy-16,76,23),dy=-opn*.13,sy=1.0,feather=.42)
        sprite=affine_local(sprite,(cx-42,cy-1,84,28),dy=opn*.32,sy=1.0+opn*.012,feather=.42)
        # Subtle mouth cavity, sampled dark brown not absolute black.
        overlay=sprite.copy()
        axes=(max(4,int(width*.31*(.72 if rnd>.5 else 1.0))),max(1,int(opn*.44)))
        cv2.ellipse(overlay,(int(cx),int(cy+opn*.13)),axes,0,0,360,(18,13,12,205),-1,lineType=cv2.LINE_AA)
        m=np.zeros(sprite.shape[:2],np.uint8)
        cv2.ellipse(m,(int(cx),int(cy+opn*.13)),axes,0,0,360,255,-1,lineType=cv2.LINE_AA)
        m=cv2.GaussianBlur(m,(0,0),.85).astype(np.float32)[...,None]/255.0
        # preserve alpha and blend RGB only
        rgb=np.clip(sprite[:,:,:3].astype(np.float32)*(1-m*.62)+overlay[:,:,:3].astype(np.float32)*(m*.62),0,255).astype(np.uint8)
        sprite[:,:,:3]=rgb
    return sprite

def blink_anim(sprite,t):
    b=max(pulse(t,c,.115) for c in BLINKS)
    if b<.01:return sprite
    for cx,cy in EYES:
        # individual eye-only closure; no whole-eye-band compression
        rect=(cx-17,cy-8,34,18)
        sy=max(.48,1-.50*b)
        sprite=affine_local(sprite,rect,sy=sy,dy=2.0*b,feather=.38)
        # tiny upper-lid darkening at full closure
        if b>.55:
            ov=sprite.copy(); y=int(cy+1)
            cv2.line(ov,(int(cx-9),y),(int(cx+9),y),(33,25,23,255),1,cv2.LINE_AA)
            m=np.zeros(sprite.shape[:2],np.uint8); cv2.line(m,(int(cx-9),y),(int(cx+9),y),255,2,cv2.LINE_AA)
            m=cv2.GaussianBlur(m,(0,0),.6).astype(np.float32)[...,None]/255.0
            sprite[:,:,:3]=np.clip(sprite[:,:,:3].astype(np.float32)*(1-m*.45)+ov[:,:,:3].astype(np.float32)*(m*.45),0,255).astype(np.uint8)
    return sprite

def body_anim(sprite,t):
    # torso support/breath: very low amplitude, phrase-support not idle bobble
    q=math.sin(2*math.pi*t/3.4)
    sprite=affine_local(sprite,TORSO,sx=1.0+0.0025*q,sy=1.0+0.0018*q,feather=.35)
    # explicit strums only
    for i,c in enumerate(STRUMS):
        p=pulse(t,c,.115)
        if p>0:
            sign=1 if i%2==0 else -1
            sprite=affine_local(sprite,STRUM,angle=sign*1.2*p,dx=sign*1.3*p,dy=2.0*p,feather=.34)
    # restrained fret/chord shifts
    for i,c in enumerate(CHORDS):
        p=pulse(t,c,.16)
        if p>0:
            sign=-1 if i%2==0 else 1
            sprite=affine_local(sprite,CHORD,dx=sign*1.2*p,dy=-.5*p,feather=.36)
    # deliberate head phrase accents, sub-degree only
    for a,b,ang,vy in HEAD_KEYS:
        if a<=t<=b:
            u=(t-a)/(b-a); e=math.sin(math.pi*u)
            sprite=affine_local(sprite,HEAD,angle=ang*e,dy=vy*e,feather=.40)
    return sprite

def warm_grade(sprite):
    rgb=sprite[:,:,:3].astype(np.float32)
    # BGR: slightly reduce blue, nudge red; compress highlights, lift black minimally
    rgb[:,:,0]*=.91; rgb[:,:,1]*=.98; rgb[:,:,2]*=1.045
    rgb=np.clip((rgb-8)*.98+8,0,255)
    out=sprite.copy(); out[:,:,:3]=rgb.astype(np.uint8)
    return out

def paste_rgba(bg,fg,x,y,occ_y=None):
    H,W=bg.shape[:2]; h,w=fg.shape[:2]
    x0=max(0,x); y0=max(0,y); x1=min(W,x+w); y1=min(H,y+h)
    if x1<=x0 or y1<=y0:return bg
    fx0=x0-x; fy0=y0-y; fx1=fx0+(x1-x0); fy1=fy0+(y1-y0)
    f=fg[fy0:fy1,fx0:fx1].copy()
    a=f[:,:,3].astype(np.float32)/255.0
    if occ_y is not None:
        yy=np.arange(y0,y1)
        # hard occlusion with 3px feather just above front edge
        fade=np.clip((occ_y-yy)/3.0,0,1).astype(np.float32)
        a*=fade[:,None]
    a=a[...,None]
    b=bg[y0:y1,x0:x1].astype(np.float32)
    bg[y0:y1,x0:x1]=np.clip(b*(1-a)+f[:,:,:3].astype(np.float32)*a,0,255).astype(np.uint8)
    return bg

def add_shadow(bg,cx,cy,rx,scale):
    ov=bg.copy(); ry=max(4,int(10*scale));
    cv2.ellipse(ov,(int(cx),int(cy)),(int(rx),ry),0,0,360,(10,8,7),-1,cv2.LINE_AA)
    mask=np.zeros(bg.shape[:2],np.uint8); cv2.ellipse(mask,(int(cx),int(cy)),(int(rx),ry),0,0,360,110,-1,cv2.LINE_AA)
    mask=cv2.GaussianBlur(mask,(0,0),6*scale).astype(np.float32)[...,None]/255.0
    return np.clip(bg.astype(np.float32)*(1-mask*.42)+ov.astype(np.float32)*(mask*.42),0,255).astype(np.uint8)

def add_foreground_patrons(bg,scale):
    H,W=bg.shape[:2]
    layer=np.zeros((H,W,4),np.uint8)
    # One coherent seated patron from behind at extreme foreground-left.
    # It masks the legacy primitive audience heads/table without creating background chaos.
    head=(int(50*scale),int(170*scale)); hr=int(29*scale)
    cv2.circle(layer,head,hr,(15,16,17,238),-1,cv2.LINE_AA)
    # shoulders/back
    cv2.ellipse(layer,(int(52*scale),int(242*scale)),(int(78*scale),int(78*scale)),0,180,360,(13,14,15,240),-1,cv2.LINE_AA)
    pts=np.array([[int(-24*scale),int(208*scale)],[int(132*scale),int(210*scale)],[int(145*scale),H],[0,H]],np.int32)
    cv2.fillPoly(layer,[pts],(12,13,14,238),lineType=cv2.LINE_AA)
    # very soft edge and slight warm rim on room-facing side
    cv2.ellipse(layer,(int(74*scale),int(215*scale)),(int(24*scale),int(48*scale)),0,250,72,(28,22,18,90),2,cv2.LINE_AA)
    layer=cv2.GaussianBlur(layer,(0,0),5.5*scale)
    a=layer[:,:,3:4].astype(np.float32)/255.0
    return np.clip(bg.astype(np.float32)*(1-a)+layer[:,:,:3].astype(np.float32)*a,0,255).astype(np.uint8)

def build_glow_mask(bg, scale):
    # Motivated warm-light mask from existing candle/fire highlights only.
    b,g,r=cv2.split(bg)
    hot=((r>185)&(g>95)&(b<155)&((r.astype(np.int16)-b.astype(np.int16))>55)).astype(np.uint8)*255
    hot=cv2.morphologyEx(hot,cv2.MORPH_OPEN,np.ones((3,3),np.uint8),iterations=1)
    m=cv2.GaussianBlur(hot,(0,0),max(6.0,18.0*scale)).astype(np.float32)/255.0
    if m.max()>0: m/=m.max()
    return m[...,None]

def environment_life(bg, glow, t, phase):
    # Deterministic low-amplitude flame/candle breathing; no geometry motion.
    amp=0.012*math.sin(2*math.pi*1.73*t+phase)+0.006*math.sin(2*math.pi*3.07*t+phase*1.7)
    gain=1.0+amp*glow
    return np.clip(bg.astype(np.float32)*gain,0,255).astype(np.uint8)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--plates',required=True)
    ap.add_argument('--source',required=True)
    ap.add_argument('--audio',required=True)
    ap.add_argument('--outdir',required=True)
    ap.add_argument('--tag',default='V1R3')
    args=ap.parse_args()
    plates=pathlib.Path(args.plates); source=pathlib.Path(args.source); out=pathlib.Path(args.outdir); out.mkdir(parents=True,exist_ok=True)
    if sha256(source)!=EXPECTED_SHA: raise RuntimeError('canonical source SHA mismatch')
    img=cv2.imread(str(source),cv2.IMREAD_COLOR); sprite0=warm_grade(build_matte(img))
    bg0=cv2.imread(str(plates/'S1_MASTER_ENV.png')); H,W=bg0.shape[:2]
    scale=W/640.0
    if abs(H/(W)-360/640)>0.005: raise RuntimeError(f'Unexpected aspect {W}x{H}')
    bgs={sid:cv2.imread(str(plates/f'{sid}_ENV.png')) for sid,_,_ in CUTS}
    glows={sid:build_glow_mask(b,scale) for sid,b in bgs.items()}
    shot_phase={'S1_MASTER':0.3,'S2_MEDIUM':1.1,'S3_CLOSE':2.0,'S4_RETURN':2.8}
    for sid,b in bgs.items():
        if b is None or b.shape[:2]!=(H,W): raise RuntimeError(f'bad plate {sid}')
    raw=out/f'BARD_GOLDEN_SLICE_{args.tag}_SILENT.mp4'
    final=out/f'BARD_GOLDEN_SLICE_{args.tag}_AV.mp4'
    fourcc=cv2.VideoWriter_fourcc(*'mp4v'); vw=cv2.VideoWriter(str(raw),fourcc,FPS,(W,H))
    if not vw.isOpened(): raise RuntimeError('VideoWriter failed')
    controls=controls_for_frames(int(FPS*DUR))
    metrics={'mouth_diff':[],'right_hand_diff':[],'left_hand_diff':[]}
    prev=None
    for i in range(int(FPS*DUR)):
        t=i/FPS; sid=shot_for(t); bg=environment_life(bgs[sid].copy(),glows[sid],t,shot_phase[sid]); p=PLACEMENT_640[sid]
        sf=p['scale']*scale
        sprite=sprite0.copy()
        sprite=body_anim(sprite,t); sprite=blink_anim(sprite,t); sprite=mouth_anim(sprite,controls[i])
        neww=max(1,int(round(sprite.shape[1]*sf))); newh=max(1,int(round(sprite.shape[0]*sf)))
        spr=cv2.resize(sprite,(neww,newh),interpolation=cv2.INTER_LANCZOS4)
        cx=int(round(p['cx']*scale)); top=int(round(p['top']*scale)); x=cx-neww//2
        occ=int(round(p['occ']*scale)); sy=int(round(p['shadow_y']*scale)); rx=int(round(p['shadow_rx']*scale))
        bg=add_shadow(bg,cx,sy,rx,scale)
        bg=paste_rgba(bg,spr,x,top,occ)
        if sid=='S1_MASTER': bg=add_foreground_patrons(bg,scale)
        vw.write(bg)
        if prev is not None and prev.shape==bg.shape:
            d=cv2.absdiff(prev,bg)
            # screen-space ROIs scaled from 640 layout; informational only
            def mean_roi(rect):
                x0,y0,x1,y1=[int(v*scale) for v in rect]; return float(d[y0:y1,x0:x1].mean())
            metrics['mouth_diff'].append(mean_roi((285,92,360,160)) if sid=='S3_CLOSE' else 0.0)
            metrics['right_hand_diff'].append(mean_roi((245,210,350,325)))
            metrics['left_hand_diff'].append(mean_roi((335,180,430,285)))
        prev=bg
    vw.release()
    subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-i',str(raw),'-i',str(args.audio),'-map','0:v:0','-map','1:a:0','-c:v','libx264','-preset','medium','-crf','18','-pix_fmt','yuv420p','-r','25','-c:a','aac','-b:a','192k','-shortest',str(final)],check=True)
    # ffprobe
    probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration,size','-show_entries','stream=codec_type,codec_name,width,height,r_frame_rate,sample_rate,channels','-of','json',str(final)],text=True))
    # contact sheet at 1fps
    contact=out/f'BARD_GOLDEN_SLICE_{args.tag}_CONTACT.jpg'
    subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-i',str(final),'-vf',f'fps=1,scale={W//2}:-1,tile=2x4','-frames:v','1',str(contact)],check=True)
    rep={
      'proof_id':f'BARD_GOLDEN_SLICE_{args.tag}',
      'status':'INTEGRATED_RENDER_COMPLETE_PENDING_VIEWER_QA',
      'source_sha256':EXPECTED_SHA,
      'resolution':[W,H],'fps':FPS,'duration_target':DUR,
      'coverage_cut_times':[2.52,3.60,6.20],
      'audio_path':str(args.audio),'output':str(final),'output_sha256':sha256(final),
      'ffprobe':probe,
      'mechanical_evidence':{
        'mouth_motion_nonzero_frames':int(sum(v>0.05 for v in metrics['mouth_diff'])),
        'right_hand_motion_nonzero_frames':int(sum(v>0.05 for v in metrics['right_hand_diff'])),
        'left_hand_motion_nonzero_frames':int(sum(v>0.05 for v in metrics['left_hand_diff']))
      },
      'manual_gates':['random_global_face_wobble','mouth_transition_pop','blink_naturalness','strum_contact','seated_read','matte_edge','lighting_match','viewer_uncanny_response']
    }
    (out/f'BARD_GOLDEN_SLICE_{args.tag}_VALIDATION.json').write_text(json.dumps(rep,indent=2))
    print(json.dumps(rep,indent=2))

if __name__=='__main__': main()
