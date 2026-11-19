#!/usr/bin/env python3
"""V081 genuine visual practice-study of public official Blender Studio clips.

Only public video elements embedded in openly accessible *free* official lesson.
No paywall bypass, tokens, cookies, or third-party proxy. Obtain fresh same-session
presigned video GET URL from page. Keep MP4s solely in ephemeral GitHub runner /tmp.
NEVER commit or upload source video. Make *temporary* low-resolution contact sheets
and private 7-day research artifact for immediate visual examination. CC-BY not
declared on this 4.5 lesson page, so DO NOT redistribute media. No claim of
audio listening or full continuous viewing based on contact sheets.
"""
import requests,bs4,urllib.parse,pathlib,json,hashlib,subprocess,math,os
from PIL import Image,ImageDraw
from io import BytesIO
OUT=pathlib.Path("research/animation_v081");OUT.mkdir(exist_ok=True)
SCRATCH=pathlib.Path(os.environ.get("RUNNER_TEMP","/tmp"))/"v081_actual_teacher_video_ephemeral"
SCRATCH.mkdir(parents=True,exist_ok=True)
URL="https://studio.blender.org/training/blender-fundamentals-45-lts/using-multiple-objects/"
# Only source segments corresponding to making a thin controlled base mesh.
INDICES=(2,3,4,11)
SIZE_CAP_PER=75_000_000
SIZE_CAP_AGGREGATE=160_000_000
rec={"schema":"V081_REAL_VIDEO_FRAMES_PROFESSIONAL_MODELING_BASE_MESH_STUDY",
 "source":URL,"source_teacher":"Julien Kaspar / official Blender Studio",
 "page_access":"public openly accessible official free training",
 "media_license_on_page":"NOT_EXPLICITLY_DECLARED; TEMPORARY_PRIVATE_STUDY_ONLY",
 "selected_video_order":list(INDICES),
 "teacher_AV_fully_watched":False,"audio_listened":False,"video_scenes_visually_examined":False,
 "no_original_video_upload":True,"status":"INIT","segments":[]}
def run(*args):return subprocess.run(args,check=True,text=True,capture_output=True).stdout
s=requests.Session();s.headers["User-Agent"]="Mozilla/5.0 (education, official public page)"
total=0
try:
 p=s.get(URL,timeout=50);p.raise_for_status()
 page=bs4.BeautifulSoup(p.text,"html.parser")
 clips=page.select("video")
 assert len(clips)>=12,len(clips)
 for idx in INDICES:
  v=clips[idx];q=v.find("source");assert q and q.get("src")
  media=urllib.parse.urljoin(URL,q["src"])
  assert urllib.parse.urlsplit(media).hostname=="studio.blender.org"
  path=urllib.parse.urlsplit(media).path
  header=v.find_previous(["h2","h3","h4","h5"])
  title=header.get_text(" ",strip=True) if header else "Unlabeled"
  entry={"index":idx,"heading":title,"official_public_media_path":path}
  movie=SCRATCH/f"official_{idx:02d}.mp4"
  # Actual browser-authorized HTTP GET. HEAD is invalid for a GET-signed S3 URL,
  # so an earlier HEAD 403 must not be confused with denied video access.
  with s.get(media,timeout=(30,120),stream=True) as response:
   entry["get_status"]=response.status_code
   entry["final_host"]=urllib.parse.urlparse(response.url).hostname
   response.raise_for_status()
   assert entry["final_host"] in ("studio.blender.org","cloud.blender.org")
   with movie.open("wb") as o:
    n=0
    for block in response.iter_content(2**20):
     if block:
      n+=len(block);total+=len(block)
      if n>SIZE_CAP_PER or total>SIZE_CAP_AGGREGATE:
       raise RuntimeError("Source size over fixed no-cost single-study cap")
      o.write(block)
  assert movie.stat().st_size>10000
  entry["original_media_bytes_ephemeral"]=movie.stat().st_size
  entry["original_media_sha256_ephemeral"]=hashlib.sha256(movie.read_bytes()).hexdigest()
  info=json.loads(run("ffprobe","-v","error","-show_format","-show_streams","-of","json",str(movie)))
  duration=float(info["format"]["duration"]);entry["duration_sec"]=duration
  entry["audio_stream_present"]=any(x.get("codec_type")=="audio" for x in info["streams"])
  entry["video_codec"]=[x.get("codec_name") for x in info["streams"] if x.get("codec_type")=="video"]
  # For each recorded segment make every-2-second contact and near-sample if short.
  rate=.5 if duration>50 else 1
  tmp=SCRATCH/f"frames_{idx:02d}";tmp.mkdir(exist_ok=True)
  run("ffmpeg","-y","-v","error","-i",str(movie),
      "-vf",f"fps={rate},scale=320:-2","-q:v","5",str(tmp/"frame_%04d.jpg"))
  imgs=sorted(tmp.glob("frame_*.jpg"));assert imgs
  entry["frames_sampled"]=len(imgs);entry["sample_rate_fps"]=rate
  board_dir=OUT/"temporary_private_contact";board_dir.mkdir(exist_ok=True)
  sheets=[]
  per=32;col=4;rows=8;w=300;h=215
  for chunkno in range(math.ceil(len(imgs)/per)):
   canvas=Image.new("RGB",(col*w,rows*h),(22,25,32));d=ImageDraw.Draw(canvas)
   for j,f in enumerate(imgs[chunkno*per:(chunkno+1)*per]):
    im=Image.open(f).convert("RGB");im.thumbnail((w-8,h-25))
    x=(j%col)*w;y=(j//col)*h
    canvas.paste(im,(x+(w-im.width)//2,y))
    second=(chunkno*per+j)/rate
    d.text((x+5,y+h-21),f"{second/60:.1f} min",fill="white")
   filepath=board_dir/f"TEACHER_{idx:02d}_CONTACT_{chunkno:02d}.jpg"
   canvas.save(filepath,quality=72,optimize=True)
   sheets.append(filepath.name)
  entry["temporary_private_contact_sheets"]=sheets
  rec["segments"].append(entry)
 rec["status"]="PUBLIC_ORIGINAL_VIDEO_BYTES_ACCESSED_AND_TEMP_CONTACTS_CREATED; MODEL_VISUAL_REVIEW_PENDING"
except Exception as e:
 rec["status"]="SOURCE_ACCESS_HOLD_NO_FALSE_REVIEW"
 rec["error"]=repr(e)[:500]
(OUT/"V081_REAL_TEACHER_VIDEO_CAPTURE_RECEIPT.json").write_text(json.dumps(rec,ensure_ascii=False,indent=2)+"\n")
print("V081_ACTUAL_SOURCE_VIDEO",json.dumps(rec,ensure_ascii=False)[:20000],flush=True)
if rec["status"].startswith("SOURCE_ACCESS_HOLD"):raise SystemExit(81)
