#!/usr/bin/env python3
"""V061: publicly free CC-BY Blender Studio lesson; source download and unbiased all-span frames.
Never claim AV fully studied merely because this script creates previews."""
from __future__ import annotations
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import hashlib, json, re, subprocess, requests, os, math, shutil, datetime
SRC="https://www.youtube.com/watch?v=TAGWu08oWAM"
OUT=Path("research/animation_v061"); PRIVATE=Path(os.environ.get("RUNNER_TEMP","/tmp"))/"v061_licensed_video"
OUT.mkdir(parents=True,exist_ok=True); PRIVATE.mkdir(parents=True,exist_ok=True)
class Tags(HTMLParser):
 def __init__(self): super().__init__();self.links=[];self.sources=[]
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if tag=="a": self.links.append(a)
  elif tag=="source":self.sources.append(a)
def run(*args): return subprocess.run(args,check=True,capture_output=True,text=True).stdout
def sha(p):
 h=hashlib.sha256()
 with open(p,"rb") as f:
  for b in iter(lambda:f.read(1024*1024),b""):h.update(b)
 return h.hexdigest()
def write(d): (OUT/"CAPTURE.json").write_text(json.dumps(d,indent=2,ensure_ascii=False)+"\n")
rec={"schema":"V061_KASPAR_ORIGINAL_CC_BY_CAPTURE","source_url":SRC,"author":"Julien Kaspar / Blender Studio","license_claim":"Blender Studio page expressly marks lesson Free / License CC-BY","status":"INIT","source_acquired":False,"visual_study":"NOT_YET_VISUALLY_REVIEWED","audio_listening":"NOT_PERCEPTUALLY_AUDITED","art":"HOLD","new_native_blender":"NOT_RUN","gs001":"UNTOUCHED","date":"2026-11-18"}
try:
 # Alternative official Blender Foundation public YouTube release; original Studio direct URL was 503.
 # The Studio page explicitly licenses this lesson CC-BY. No premium/DRM source used.
 rec["publisher"]="Blender Foundation (verified official public YouTube release)"
 rec["license_reference"]="https://studio.blender.org/training/stylized-character-workflow/5d5e6141b01c790d39b7ed4e/"
 rec["distribution"]="YOUTUBE_OFFICIAL_NOT_STUDIO_BYTE_IDENTICAL"
 rec["youtube_id"]="TAGWu08oWAM"
 full=PRIVATE/"sculpting_fundamentals_original.mp4"
 cmd=["yt-dlp","--no-playlist","--no-progress","--merge-output-format","mp4","--format","bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]/best","--output",str(PRIVATE/"sculpting_fundamentals_original.%(ext)s"),SRC]
 run(*cmd)
 choices=list(PRIVATE.glob("sculpting_fundamentals_original.*"))
 usable=[p for p in choices if p.suffix.lower() in (".mp4",".mkv",".webm")]
 assert usable, "yt-dlp did not produce real media"
 if usable[0]!=full: shutil.move(str(usable[0]),str(full))
 rec["official_download_href"]=SRC
 rec["download_status"]="YT_DLP_PUBLIC_SOURCE_SUCCESS"
 rec["final_download_host"]="youtube.com"
 tags=Tags()
 assert full.stat().st_size > 1000000, "Download was not full video"
 meta=json.loads(run("ffprobe","-v","error","-show_format","-show_streams","-of","json",str(full)))
 streams=meta["streams"];vs=next(x for x in streams if x["codec_type"]=="video")
 dur=float(meta["format"]["duration"])
 assert 1450 < dur < 1570, "Unexpected duration; do not certify"
 rec.update({"status":"SOURCE_DOWNLOADED_MEDIA_VERIFIED","source_acquired":True,"video_sha256":sha(full),"video_bytes":full.stat().st_size,"duration_sec":dur,"video_width":vs.get("width"),"video_height":vs.get("height"),"streams":[{"codec":x.get("codec_name"),"type":x.get("codec_type")} for x in streams]})
 # Search for user-facing English subtitle file explicitly linked in the public page.
 sublinks=[urljoin(SRC,x.get("href","")) for x in tags.links if any(k in x.get("href","").lower() for k in (".srt",".vtt","subtitle"))]
 rec["subtitle_link_count"]=len(sublinks);rec["subtitle_public_hrefs"]=[x for x in sublinks if urlparse(x).netloc=="studio.blender.org"][:3]
 for i,sub in enumerate(rec["subtitle_public_hrefs"]):
  try:
   r=s.get(sub,timeout=30)
   if r.ok and len(r.content)<2_000_000 and ("WEBVTT" in r.text[:30] or "-->" in r.text[:300]):
    (OUT/"ORIGINAL_LICENSED_EN_SUBTITLES.txt").write_text(r.text)
    rec["subtitle_source_sha256"]=hashlib.sha256(r.content).hexdigest()
    break
  except Exception:pass
 # Full-span unbiased temporal index; sampling every second ≠ real-time full video observation.
 frames=PRIVATE/"all_seconds";frames.mkdir(exist_ok=True)
 run("ffmpeg","-hide_banner","-loglevel","error","-y","-i",str(full),"-vf","fps=1,scale=400:-2","-q:v","6",str(frames/"F_%05d.jpg"))
 fs=sorted(frames.glob("F_*.jpg"))
 assert len(fs)>=math.floor(dur)-2,"Incomplete full-span frame extraction"
 rec["one_fps_frame_count"]=len(fs)
 # Persist 14 contact sheets to a compact set of true image data from original.
 contact=OUT/"contacts";contact.mkdir(exist_ok=True)
 ncols,nrows=8,10; bw,bh=200,140
 for chunk in range(math.ceil(len(fs)/(ncols*nrows))):
  sheet=Image.new("RGB",(ncols*bw,nrows*bh),(25,25,25));dr=ImageDraw.Draw(sheet)
  for j,p in enumerate(fs[chunk*ncols*nrows:(chunk+1)*ncols*nrows]):
   im=Image.open(p).convert("RGB");im.thumbnail((bw-6,bh-26))
   x=(j%ncols)*bw;y=(j//ncols)*bh
   sheet.paste(im,(x+(bw-im.width)//2,y))
   seconds=chunk*80+j
   dr.text((x+4,y+bh-23),f"{seconds//60:02d}:{seconds%60:02d}",fill="white")
  name=contact/f"CONTACT_{chunk:02d}.jpg"
  sheet.save(name,quality=81,optimize=True)
 rec["contact_count"]=len(list(contact.glob("*.jpg")))
 rec["contact_sha256"]={x.name:sha(x) for x in sorted(contact.glob("*.jpg"))}
 # Full continuous audio remains private for licensed research; extraction not claim of hearing.
 if any(x["codec_type"]=="audio" for x in streams):
  audio=PRIVATE/"source_audio_16khz_mono.wav"
  run("ffmpeg","-hide_banner","-loglevel","error","-y","-i",str(full),"-vn","-ar","16000","-ac","1","-c:a","pcm_s16le",str(audio))
  rec["audio_extracted"]=True;rec["audio_sha256"]=sha(audio)
 else:rec["audio_extracted"]=False
 rec["status"]="ORIGINAL_FULL_MP4_CAPTURED_ALL_SPAN_INDEXED"
except Exception as exc:
 rec["status"]="CAPTURE_OR_RIGHTS_HOLD";rec["error"]=repr(exc)
finally:
 write(rec)
 print("V061_RECEIPT",json.dumps(rec,ensure_ascii=False)[:6000],flush=True)
if rec["status"]!="ORIGINAL_FULL_MP4_CAPTURED_ALL_SPAN_INDEXED":raise SystemExit(43)
