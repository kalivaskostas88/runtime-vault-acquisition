import cv2, json, math, sys, pathlib, numpy as np
p=pathlib.Path(sys.argv[1]); out=pathlib.Path(sys.argv[2])
cap=cv2.VideoCapture(str(p)); fps=cap.get(cv2.CAP_PROP_FPS); frames=[]
while True:
 ok,f=cap.read()
 if not ok: break
 frames.append(f)
cap.release(); H,W=frames[0].shape[:2]; scale=W/640.0
cuts=[2.52,3.60,6.20]
strums=[0.4,1.0,1.96,3.24,5.36,5.8,6.56,7.68]
blinks=[1.72,4.18,6.62]
# shot-aware performer screen placement / source mapping
place={
'S1_MASTER':(.205,321,64),'S2_MEDIUM':(.285,321,60),'S3_CLOSE':(.455,321,-12),'S4_RETURN':(.285,320,58)}
def sid(t):
 if t<2.52:return 'S1_MASTER'
 if t<3.6:return 'S2_MEDIUM'
 if t<6.2:return 'S3_CLOSE'
 return 'S4_RETURN'
def src_to_screen(t,x,y):
 s,cx,top=place[sid(t)]; sf=s*scale; sw=815*sf; x0=cx*scale-sw/2
 return x0+x*sf, top*scale+y*sf
def roi(t,center,size):
 cx,cy=src_to_screen(t,*center); w=size[0]*place[sid(t)][0]*scale; h=size[1]*place[sid(t)][0]*scale
 x0=max(0,int(cx-w/2)); x1=min(W,int(cx+w/2)); y0=max(0,int(cy-h/2)); y1=min(H,int(cy+h/2)); return x0,y0,x1,y1
def diff_mean(i,center,size):
 if i<=0:return 0.0
 t=i/fps
 # exclude shot boundary neighborhoods
 if any(abs(t-c)<.12 for c in cuts):return None
 x0,y0,x1,y1=roi(t,center,size)
 a=cv2.cvtColor(frames[i-1][y0:y1,x0:x1],cv2.COLOR_BGR2GRAY); b=cv2.cvtColor(frames[i][y0:y1,x0:x1],cv2.COLOR_BGR2GRAY)
 if a.size==0:return None
 return float(cv2.absdiff(a,b).mean())
series={'mouth':[],'right_hand':[],'left_hand':[],'eyes':[],'face_shell':[]}
for i in range(1,len(frames)):
 t=i/fps
 for name,center,size in [
  ('mouth',(378,190),(110,80)),('right_hand',(250,505),(150,190)),('left_hand',(497,435),(125,150)),('eyes',(365,133),(100,45)),('face_shell',(365,145),(190,210))]:
  v=diff_mean(i,center,size)
  if v is not None:series[name].append((t,v))
def vals(name,pred): return np.array([v for t,v in series[name] if pred(t)],dtype=np.float32)
def mean(a): return float(a.mean()) if len(a) else 0.0
def p95(a): return float(np.percentile(a,95)) if len(a) else 0.0
sing=lambda t:(t<3.60 or t>=4.68)
pause=lambda t:(3.72<=t<=4.56)
event=lambda centers,w: lambda t:any(abs(t-c)<=w for c in centers)
off=lambda centers,w: lambda t:not any(abs(t-c)<=w for c in centers) and not any(abs(t-c)<.12 for c in cuts)
ms=vals('mouth',sing); mp=vals('mouth',pause)
rhe=vals('right_hand',event(strums,.14)); rho=vals('right_hand',off(strums,.22))
lhe=vals('left_hand',event([1.56,2.88,4.08],.18)); lho=vals('left_hand',off([1.56,2.88,4.08],.28))
be=vals('eyes',event(blinks,.12)); bo=vals('eyes',off(blinks,.20))
# face shell during non-mouth pause to flag unexplained motion; excludes blink windows
fs=vals('face_shell',lambda t: pause(t) and not any(abs(t-b)<.18 for b in blinks))
rep={
 'qa_id':'BARD_EVENT_QA_V1','input':str(p),'frame_count':len(frames),'fps':fps,'resolution':[W,H],
 'mouth':{'sing_mean':mean(ms),'pause_mean':mean(mp),'sing_to_pause_ratio':mean(ms)/max(mean(mp),1e-6),'sing_p95':p95(ms),'pause_p95':p95(mp)},
 'right_hand':{'event_mean':mean(rhe),'off_event_mean':mean(rho),'off_to_event_ratio':mean(rho)/max(mean(rhe),1e-6),'event_p95':p95(rhe),'off_p95':p95(rho)},
 'left_hand':{'event_mean':mean(lhe),'off_event_mean':mean(lho),'off_to_event_ratio':mean(lho)/max(mean(lhe),1e-6)},
 'eyes':{'blink_window_mean':mean(be),'off_blink_mean':mean(bo),'blink_to_off_ratio':mean(be)/max(mean(bo),1e-6)},
 'face_shell_pause_nonblink':{'mean':mean(fs),'p95':p95(fs)},
 'gates':{
  'mouth_activity_separates_pause': bool(mean(ms)>mean(mp)*3.0),
  'right_hand_event_bound': bool(mean(rho)<mean(rhe)*0.25),
  'blink_event_detectable': bool(mean(be)>mean(bo)*1.4),
  'manual_viewer_qa_required': True
 }
}
out.write_text(json.dumps(rep,indent=2)); print(json.dumps(rep,indent=2))
