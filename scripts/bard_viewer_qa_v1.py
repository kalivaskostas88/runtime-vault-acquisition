import cv2, json, pathlib, numpy as np, subprocess, sys

if len(sys.argv) < 3:
    raise SystemExit("usage: viewer_qa.py INPUT.mp4 OUTPUT.json")

inp=pathlib.Path(sys.argv[1]); out=pathlib.Path(sys.argv[2])
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
# Relative ROIs so the same QA survives later layout changes.
rois={
  "face": (int(W*.36),int(H*.10),int(W*.61),int(H*.42)),
  "mouth":(int(W*.43),int(H*.19),int(W*.55),int(H*.30)),
  "right_hand":(int(W*.25),int(H*.36),int(W*.47),int(H*.62)),
  "left_hand":(int(W*.52),int(H*.31),int(W*.70),int(H*.55))
}
def motion_series(rect):
    x0,y0,x1,y1=rect; vals=[0.0]
    for i in range(1,len(frames)):
        a=cv2.cvtColor(frames[i-1][y0:y1,x0:x1],cv2.COLOR_BGR2GRAY)
        b=cv2.cvtColor(frames[i][y0:y1,x0:x1],cv2.COLOR_BGR2GRAY)
        vals.append(float(cv2.absdiff(a,b).mean()))
    return np.array(vals,np.float32)

metrics={}
for name,rect in rois.items():
    v=motion_series(rect)
    jerk=np.abs(np.diff(v,prepend=v[0]))
    metrics[name]={
      "motion_mean":round(float(v.mean()),4),
      "motion_p95":round(float(np.percentile(v,95)),4),
      "motion_max":round(float(v.max()),4),
      "jerk_p95":round(float(np.percentile(jerk,95)),4),
      "jerk_max":round(float(jerk.max()),4),
      "peak_time_seconds":round(float(v.argmax()/fps),3)
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
