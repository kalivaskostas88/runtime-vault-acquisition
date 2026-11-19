#!/usr/bin/env python3
"""V070 actual Blender Studio CC-BY original Sculpting Fundamentals AV capture.
Only the explicitly public 2019 lesson and explicit public Download .mp4.
Timecoded frame contacts != having watched/listened to full movie.
"""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin,urlparse
from PIL import Image,ImageDraw
from io import BytesIO
import os,requests,subprocess,json,hashlib,math,base64
SRC="https://studio.blender.org/training/stylized-character-workflow/5d5e6141b01c790d39b7ed4e/"
OUT=Path("research/animation_v070");OUT.mkdir(parents=True,exist_ok=True)
PRIVATE=Path(os.environ.get("RUNNER_TEMP","/tmp"))/"v070_public_teacher_fundamentals";PRIVATE.mkdir(exist_ok=True)
def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for c in iter(lambda:f.read(2**20),b""):h.update(c)
 return h.hexdigest()
def run(*cmd):return subprocess.run(cmd,check=True,capture_output=True,text=True).stdout
class Links(HTMLParser):
 def __init__(self):super().__init__();self.links=[]
 def handle_starttag(self,t,attrs):
  d=dict(attrs)
  if t=="a" and d.get("href"):self.links.append(d["href"])
rec={"schema":"V070_OFFICIAL_FREE_CC_BY_KASPAR_SCULPTING_FUNDAMENTALS",
"source":SRC,"teacher":"Julien Kaspar / Blender Studio (2019, Blender 2.80)",
"license":"CC-BY if officially declared in original page",
"status":"INIT","downloaded":False,"actually_watched":False,"audio_actually_listened":False,
"blender_522_compatibility_proved":False,"native_remesh":"NOT_RUN","art":"HOLD"}
try:
 sess=requests.Session();sess.headers["User-Agent"]="Mozilla/5.0 (educational CC-BY original-source access)"
 page=sess.get(SRC,timeout=45);page.raise_for_status()
 if "CC-BY" not in page.text:raise RuntimeError("CC-BY not present, stop")
 parsed=Links();parsed.feed(page.text)
 candidates=[urljoin(SRC,x) for x in parsed.links if "/download-source/files/" in x and ".mp4" in x]
 candidates=[x for x in candidates if urlparse(x).netloc=="studio.blender.org"]
 if not candidates:raise RuntimeError("No explicitly public original Download MP4")
 selected=next((x for x in candidates if "1080p" in x),candidates[0])
 rec["official_link"]=selected;rec["source_html_sha256"]=hashlib.sha256(page.content).hexdigest()
 movie=PRIVATE/"Sculpting_Fundamentals_original.mp4"
 with sess.get(selected,timeout=(30,120),stream=True) as response:
  rec["http_status"]=response.status_code;rec["download_final_host"]=urlparse(response.url).netloc
  response.raise_for_status()
  if rec["download_final_host"] not in ("studio.blender.org","cloud.blender.org"):raise RuntimeError("Unapproved source")
  size=0
  with movie.open("wb") as f:
   for b in response.iter_content(chunk_size=2**20):
    if b:
     size+=len(b)
     if size>160_000_000:raise RuntimeError("Source exceeds research transfer cap")
     f.write(b)
 if movie.stat().st_size<1_000_000:raise RuntimeError("Incomplete movie")
 meta=json.loads(run("ffprobe","-v","error","-show_format","-show_streams","-of","json",str(movie)))
 duration=float(meta["format"]["duration"])
 if not 30<duration<3600:raise RuntimeError("Duration outside expected lesson range")
 rec.update({"status":"ACTUAL_ORIGINAL_FULL_VIDEO_ACQUIRED","downloaded":True,
  "original_mp4_sha256":sha(movie),"bytes":movie.stat().st_size,"duration_sec":duration,
  "streams":[{"codec_type":s["codec_type"],"codec":s.get("codec_name")} for s in meta["streams"]]})
 sub=[urljoin(SRC,x) for x in parsed.links if any(v in x.lower() for v in (".vtt",".srt","download-subtitle","subtitle"))]
 rec["official_subtitle_links"]=[x for x in sub if urlparse(x).netloc=="studio.blender.org"][:4]
 for link in rec["official_subtitle_links"]:
  try:
   v=sess.get(link,timeout=30)
   if v.ok and len(v.content)<2_000_000 and ("WEBVTT" in v.text[:30] or "-->" in v.text[:300]):
    (OUT/"FUNDAMENTALS_OFFICIAL_CAPTIONS.txt").write_text(v.text)
    rec["captions_sha256"]=hashlib.sha256(v.content).hexdigest();break
  except Exception:pass
 fdir=PRIVATE/"half_fps";fdir.mkdir(exist_ok=True)
 run("ffmpeg","-y","-v","error","-i",str(movie),"-vf","fps=0.5,scale=250:-2","-q:v","6",str(fdir/"f_%04d.jpg"))
 frames=sorted(fdir.glob("*.jpg"))
 if len(frames)<math.floor(duration/2)-2:raise RuntimeError("Full-span sparse frame index incomplete")
 rec["half_fps_frame_count"]=len(frames)
 outbase=OUT/"fundamentals_contact_b64";outbase.mkdir(exist_ok=True)
 nper=48;cols=8;rows=6;bw=180;bh=132
 for pageidx in range(math.ceil(len(frames)/nper)):
  im=Image.new("RGB",(cols*bw,rows*bh),(23,23,23));d=ImageDraw.Draw(im)
  for k,f in enumerate(frames[pageidx*nper:(pageidx+1)*nper]):
   thumb=Image.open(f).convert("RGB");thumb.thumbnail((bw-5,bh-27))
   x=(k%cols)*bw;y=(k//cols)*bh
   im.paste(thumb,(x+(bw-thumb.width)//2,y))
   t=(pageidx*nper+k)*2
   d.text((x+5,y+bh-22),f"{t//60:02d}:{t%60:02d}",fill="white")
  buf=BytesIO();im.save(buf,"JPEG",quality=67,optimize=True)
  (outbase/f"FUND_CONTACT_{pageidx:02d}.jpg.b64").write_text(base64.b64encode(buf.getvalue()).decode()+"\n")
 rec["full_span_contacts_count"]=len(list(outbase.glob("*.b64")))
 rec["source_video_full_review"]="NOT_YET_VISUALLY_REVIEWED";rec["audio_review"]="NOT_LISTENED"
 rec["status"]="ORIGINAL_PUBLIC_FULL_MOVIE_CAPTURED_HALF_FPS_INDEXED_STUDY_PENDING"
except Exception as e:
 rec["error"]=str(e)[:350];rec["status"]="ORIGINAL_SOURCE_ACCESS_HOLD"
finally:
 (OUT/"FUNDAMENTALS_VIDEO_RECEIPT.json").write_text(json.dumps(rec,ensure_ascii=False,indent=2)+"\n")
 print("V070_FUNDAMENTALS",json.dumps({k:rec.get(k) for k in ("status","duration_sec","http_status","bytes","half_fps_frame_count","full_span_contacts_count","error")},ensure_ascii=False),flush=True)
if rec["status"]!="ORIGINAL_PUBLIC_FULL_MOVIE_CAPTURED_HALF_FPS_INDEXED_STUDY_PENDING":raise SystemExit(70)
