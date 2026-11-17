#!/usr/bin/env python3
"""Dense action windows from exactly the V043 verified full original CC-BY MP4.
No inference that contact-sheet export equals human visual interpretation."""
from pathlib import Path
from PIL import Image,ImageDraw
import requests,subprocess,json,hashlib,math,os
ROOT=Path("research/animation_v043"); REC=json.loads((ROOT/"CAPTURE.json").read_text())
assert REC["status"]=="ORIGINAL_FULL_MP4_CAPTURED_ALL_SPAN_INDEXED"
assert REC["source_acquired"] and REC["license_claim"].endswith("CC-BY")
EXP=REC["video_sha256"]
URL=REC["official_download_href"]
assert URL.startswith("https://studio.blender.org/download-source/") and URL.endswith(".mp4")
OUT=ROOT/"dense_contacts";OUT.mkdir(exist_ok=True)
TMP=Path(os.getenv("RUNNER_TEMP","/tmp"))/"v043_dense";TMP.mkdir(exist_ok=True)
video=TMP/"verified_original.mp4"
with requests.get(URL,stream=True,timeout=(25,100)) as r:
 r.raise_for_status()
 with video.open("wb") as f:
  for chunk in r.iter_content(1024*1024):
   if chunk:f.write(chunk)
def sha(p):
 h=hashlib.sha256()
 with open(p,"rb") as f:
  for b in iter(lambda:f.read(1024*1024),b""):h.update(b)
 return h.hexdigest()
assert sha(video)==EXP,"SOURCE_MEDIA_SHA_CHANGED_STOP"
from imageio_ffmpeg import get_ffmpeg_exe
FF=get_ffmpeg_exe()
# Sourced from full 1fps V043 actual contact review and actual timed public subtitles.
WINDOWS=[
 {"id":"W01","start":48.0,"end":67.0,"fps":4,"topic":"broad head before early secondary eye socket"},
 {"id":"W02","start":167.0,"end":185.0,"fps":4,"topic":"temporary eyes carved into head not detached spheres"},
 {"id":"W03","start":464.0,"end":491.0,"fps":4,"topic":"eyelid broad geometry and three-quarter viewing"},
 {"id":"W04","start":615.0,"end":651.0,"fps":8,"topic":"teacher replaces sculpted eyes with sphere and masks cavity"},
 {"id":"W05","start":680.0,"end":732.0,"fps":4,"topic":"iris mask shrink and eyelid conform to globe"},
 {"id":"W06","start":827.0,"end":893.0,"fps":4,"topic":"sculpted brow removal and detached eyebrow mask experiment"},
 {"id":"W07","start":920.0,"end":936.0,"fps":4,"topic":"brow-to-nose edge balance"},
]
report={"schema":"V043_DENSE_TIME_CODED_ORIGINAL_SOURCE","source_url":REC["source_url"],"source_sha256":EXP,"source_bytes":video.stat().st_size,"windows":[],"status":"PARTIAL","visual_review":"NOT_YET_REVIEWED","audio_listening":"NOT_PERCEPTUALLY_AUDITED","art":"HOLD","gs001":"UNTOUCHED"}
try:
 for w in WINDOWS:
  d=TMP/w["id"];d.mkdir(exist_ok=True)
  cmd=[FF,"-hide_banner","-loglevel","error","-y","-ss",str(w["start"]),"-i",str(video),"-t",str(w["end"]-w["start"]),"-vf",f"fps={w['fps']},scale=440:-2","-q:v","6",str(d/"F_%05d.jpg")]
  subprocess.run(cmd,check=True,timeout=160)
  fs=sorted(d.glob("F_*.jpg")); assert len(fs)>=int((w["end"]-w["start"])*w["fps"])-4
  wd=OUT/w["id"];wd.mkdir(exist_ok=True)
  nc,nr=8,8;cellw,cellh=220,138
  files=[]
  for k in range(math.ceil(len(fs)/(nc*nr))):
   sheet=Image.new("RGB",(nc*cellw,nr*cellh),(22,22,22));draw=ImageDraw.Draw(sheet)
   for j,p in enumerate(fs[k*nc*nr:(k+1)*nc*nr]):
    idx=k*nc*nr+j;im=Image.open(p).convert("RGB");im.thumbnail((cellw-3,cellh-25))
    x=(j%nc)*cellw;y=(j//nc)*cellh
    sheet.paste(im,(x+(cellw-im.width)//2,y))
    seconds=w["start"]+idx/w["fps"]
    draw.text((x+4,y+cellh-22),f"{int(seconds)//60:02d}:{seconds%60:05.2f}",fill="white")
   p=wd/f"DENSE_{k:02d}.jpg";sheet.save(p,quality=83,optimize=True);files.append(p)
  report["windows"].append({**w,"frames_actual":len(fs),"contact_sheets":len(files),"contact_sha256":{p.name:sha(p) for p in files}})
  print("DENSE_WINDOW",w["id"],len(fs),len(files),flush=True)
 report["status"]="DENSE_7_ORIGINAL_AV_WINDOWS_INDEXED_PASS"
finally:
 (ROOT/"DENSE_RECEIPT.json").write_text(json.dumps(report,ensure_ascii=False,indent=2))
 print("DENSE_RECEIPT",json.dumps(report,ensure_ascii=False)[:6500],flush=True)
if report["status"]!="DENSE_7_ORIGINAL_AV_WINDOWS_INDEXED_PASS":raise SystemExit(44)
