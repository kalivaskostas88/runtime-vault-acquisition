#!/usr/bin/env python3
"""V070 original teacher clip provenance and visually indexable contact sheets.
Downloads only the public MP4 explicitly embedded in the public CC-BY Blender Studio
Basic Sculpting/The Voxel Remesher section. No auth, login, bypass, or production art.
Contact sheets are for visual review; extraction alone is NOT 'video watched'.
"""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse
from PIL import Image,ImageDraw
import requests,subprocess,json,hashlib,math,re,base64,datetime,os
OUT=Path("research/animation_v070");OUT.mkdir(parents=True,exist_ok=True)
PRIVATE=Path(os.environ.get("RUNNER_TEMP","/tmp"))/"v070_teacher_media";PRIVATE.mkdir(parents=True,exist_ok=True)
SRC="https://studio.blender.org/training/blender-fundamentals-45-lts/basic-sculpting/"
TARGET_PATH="/files/4e/73/4e7348f5f064ed1eb9470da770cf566c-1-1080p.mp4"
URL="https://studio.blender.org"+TARGET_PATH
def sha(b):return hashlib.sha256(b).hexdigest()
def call(*args):
 r=subprocess.run(args,check=True,capture_output=True,text=True)
 return r.stdout
rec={"schema":"V070_ORIGINAL_EMBEDDED_VOXEL_TEACHER_CLIP","source_page":SRC,"embedded_source_path":TARGET_PATH,
     "teacher":"Julien Kaspar, Blender Studio","usage":"research, CC-BY attribution; no source video republication",
     "source_video_full_review":False,"teacher_audio_actually_listened":False,
     "new_blender_native_run":"NOT_RUN","art":"HOLD","status":"INIT",
     "date_utc":datetime.datetime.now(datetime.timezone.utc).isoformat()}
try:
 s=requests.Session();s.headers["User-Agent"]="Mozilla/5.0 (V070 educational source study)"
 p=s.get(SRC,timeout=45);p.raise_for_status()
 if "CC-BY" not in p.text:raise RuntimeError("Original page did not visibly claim CC-BY")
 if TARGET_PATH not in p.text:raise RuntimeError("Target not explicitly embedded in publicly returned HTML")
 rec["html_sha256"]=sha(p.content);rec["license_page_indicator"]="CC-BY published on source page"
 f=PRIVATE/"voxel_remesher_original_clip.mp4"
 with s.get(URL,timeout=(30,120),stream=True) as rr:
  rec["source_http_status"]=rr.status_code;rec["final_host"]=urlparse(rr.url).netloc
  rr.raise_for_status()
  if rec["final_host"] not in ("studio.blender.org","cloud.blender.org"):raise RuntimeError("Unexpected destination host")
  size=0
  with f.open("wb") as w:
   for c in rr.iter_content(chunk_size=1024*1024):
    if c:
     size+=len(c)
     if size>80_000_000:raise RuntimeError("Media is too large for scoped sample capture")
     w.write(c)
 if f.stat().st_size<20_000:raise RuntimeError("MP4 missing/too small")
 meta=json.loads(call("ffprobe","-v","error","-show_format","-show_streams","-of","json",str(f)))
 duration=float(meta["format"]["duration"])
 if not (0.3<duration<240):raise RuntimeError("Duration outside small instructional clip scope")
 streams=meta["streams"]
 rec.update({"status":"REAL_PUBLIC_SOURCE_DOWNLOADED","video_sha256":sha(f.read_bytes()),"video_size_bytes":f.stat().st_size,
  "duration_sec":duration,"video_codecs":[{"type":x["codec_type"],"codec":x.get("codec_name")} for x in streams],
  "original_teacher_media_located":True,"source_video_full_review":False,"teacher_audio_actually_listened":False})
 frames=PRIVATE/"frames";frames.mkdir(exist_ok=True)
 call("ffmpeg","-y","-v","error","-i",str(f),"-vf","fps=2,scale=240:-2","-q:v","5",str(frames/"F_%04d.jpg"))
 fs=sorted(frames.glob("F_*.jpg"))
 if len(fs)<1:raise RuntimeError("No actual media frames")
 rec["contact_sample_fps"]=2;rec["contact_sample_count"]=len(fs)
 sheets=OUT/"teacher_contact_b64";sheets.mkdir(exist_ok=True)
 count_per=20;bw,bh=240,155
 for n in range(math.ceil(len(fs)/count_per)):
  canvas=Image.new("RGB",(4*bw,5*bh),(24,24,24));draw=ImageDraw.Draw(canvas)
  for k,fp in enumerate(fs[n*count_per:(n+1)*count_per]):
   im=Image.open(fp).convert("RGB");im.thumbnail((bw-4,bh-30))
   x=(k%4)*bw;y=(k//4)*bh
   canvas.paste(im,(x+(bw-im.width)//2,y))
   time_s=(n*count_per+k)/2.0
   draw.text((x+6,y+bh-25),f"{time_s:05.1f}s",fill="white")
  from io import BytesIO
  buf=BytesIO();canvas.save(buf,"JPEG",quality=75,optimize=True)
  (sheets/f"VOXEL_CONTACT_{n:02d}.jpg.b64").write_text(base64.b64encode(buf.getvalue()).decode()+"\n")
 rec["contact_sheet_count"]=len(list(sheets.glob("*.b64")))
 rec["contact_sheet_sha256"]={x.name:sha(base64.b64decode(x.read_text())) for x in sorted(sheets.glob("*.b64"))}
 rec["status"]="ORIGINAL_TEACHER_VOXEL_CLIP_CAPTURED_CONTACTS_INDEXED_NOT_YET_REVIEWED"
except Exception as e:
 rec["status"]="SOURCE_ACCESS_HOLD";rec["error"]=str(e)[:300]
finally:
 (OUT/"VOXEL_CLIP_CAPTURE_RECEIPT.json").write_text(json.dumps(rec,ensure_ascii=False,indent=2)+"\n")
 print("V070_TEACHER_VOXEL_MEDIA",json.dumps({k:rec.get(k) for k in ("status","duration_sec","source_http_status","video_size_bytes","contact_sheet_count","error")},ensure_ascii=False),flush=True)
if rec["status"]!="ORIGINAL_TEACHER_VOXEL_CLIP_CAPTURED_CONTACTS_INDEXED_NOT_YET_REVIEWED":raise SystemExit(70)
