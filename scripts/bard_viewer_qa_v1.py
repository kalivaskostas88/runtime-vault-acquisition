import cv2, json, pathlib, numpy as np, subprocess, sys

if len(sys.argv) < 3:
    raise SystemExit("usage: viewer_qa.py INPUT.mp4 OUTPUT.json [COVERAGE.json]")

inp=pathlib.Path(sys.argv[1]); out=pathlib.Path(sys.argv[2])
coverage=pathlib.Path(sys.argv[3]) if len(sys.argv)>3 else None
cap=cv2.VideoCapture(str(inp))
fps=cap.get(cv2.CAP_PROP_FPS)
frames=[]
while True:
    ok,f=cap.read()
    if not ok: break
    frames.append(f)
cap.release()
if not frames: raise RuntimeError("no frames")

H,W=frames[0].shape[:2]
rois={
  "face": (int(W*.36),int(H*.10),int(W*.61),int(H*.42)),
  "mouth":(int(W*.43),int(H*.19),int(W*.55),int(H*.30)),
  "right_hand":(int(W*.25),int(H*.36),int(W*.47),int(H*.62)),
  "left_hand":(int(W*.52),int(H*.31),int(W*.70),int(H*.55))
}

# Editorial cuts are intentional discontinuities and must not be scored as animation jerk.
excluded=set()
cut_times=[]
if coverage and coverage.exists():
    cfg=json.loads(coverage.read_text())
    cut_times=[float(s["start"]) for s in cfg.get("shots",[])[1:]]
    for t in cut_times:
        idx=int(round(t*fps))
        for j in range(max(0,idx-2),min(len(frames),idx+3)):
            excluded.add(j)

def motion_series(rect):
    x0,y0,x1,y1=rect; vals=np.zeros(len(frames),np.float32)
    for i in range(1,len(frames)):
        a=cv2.cvtColor(frames[i-1][y0:y1,x0:x1],cv2.COLOR_BGR2GRAY)
        b=cv2.cvtColor(frames[i][y0:y1,x0:x1],cv2.COLOR_BGR2GRAY)
        vals[i]=float(cv2.absdiff(a,b).mean())
    return vals

metrics={}
for name,rect in rois.items():
    v=motion_series(rect)
    jerk=np.abs(np.diff(v,prepend=v[0]))
    keep=np.array([i not in excluded for i in range(len(v))],dtype=bool)
    vk=v[keep]; jk=jerk[keep]
    metrics[name]={
      "motion_mean_excluding_cuts":round(float(vk.mean()),4),
      "motion_p95_excluding_cuts":round(float(np.percentile(vk,95)),4),
      "motion_max_excluding_cuts":round(float(vk.max()),4),
      "jerk_p95_excluding_cuts":round(float(np.percentile(jk,95)),4),
      "jerk_max_excluding_cuts":round(float(jk.max()),4),
      "peak_time_seconds_excluding_cuts":round(float(np.flatnonzero(keep)[vk.argmax()]/fps),3)
    }

probe=json.loads(subprocess.check_output([
  "ffprobe","-v","error","-show_entries","format=duration",
  "-show_entries","stream=codec_type,codec_name,width,height,r_frame_rate",
  "-of","json",str(inp)
],text=True))
report={
 "qa_id":"BARD_VIEWER_QA_V1",
 "input":str(inp),
 "frame_count":len(frames),
 "fps":fps,
 "duration_seconds":len(frames)/fps,
 "coverage_cut_times_seconds":cut_times,
 "excluded_frames_around_editorial_cuts":sorted(excluded),
 "region_metrics":metrics,
 "ffprobe":probe,
 "gates":{
   "random_global_face_wobble":"MANUAL_REVIEW_REQUIRED",
   "mouth_transition_pop":"MANUAL_REVIEW_REQUIRED",
   "blink_naturalness":"MANUAL_REVIEW_REQUIRED",
   "strum_contact":"MANUAL_REVIEW_REQUIRED",
   "viewer_uncanny_response":"MANUAL_REVIEW_REQUIRED"
 }
}
out.write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
