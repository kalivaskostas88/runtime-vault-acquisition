#!/usr/bin/env python3
"""V083 actual visual professional demonstration: Voxel Remesher and Limits of Remeshing.
Official public Blender Studio sources only. Temporary original videos /tmp on GitHub,
derivative contact sheets 1-day private workflow artifact, not saved to Library/repo.
This is 1 FPS visual frame analysis, NOT continuous viewing or listened audio.
"""
import requests,bs4,json,pathlib,os,math,hashlib,urllib.parse,subprocess
from PIL import Image,ImageDraw
O=pathlib.Path("research/animation_v083");O.mkdir(parents=True,exist_ok=True)
TMP=pathlib.Path(os.environ.get("RUNNER_TEMP","/tmp"))/"v083_internal_original_av";TMP.mkdir(exist_ok=True)
SOURCES=[
 {"title":"The Voxel Remesher","url":"https://studio.blender.org/training/blender-fundamentals-45-lts/basic-sculpting/","video_index":5},
 {"title":"The Limits of Remeshing","url":"https://studio.blender.org/training/blender-fundamentals-45-lts/detailed-sculpting/","video_index":0}]
CAP_ONE=95_000_000; CAP_TOTAL=165_000_000; total=0
r={"schema":"V083_REAL_PUBLIC_KASPAR_VOXEL_REMESH_VIDEO_VISUAL_SOURCE",
 "source_provenance":"Original Blender Studio publicly embedded lesson clips",
 "teacher":"Julien Kaspar",
 "no_redistribution_of_source_video":True,"private_derived_frames_only":True,
 "media_republication_license":"UNVERIFIED; NO MEDIA ADDED TO LIBRARY",
 "continuous_full_av_seen":False,"audio_listened":False,
 "frames_really_examined_by_model":False,"status":"INIT","videos":[]}
def command(*args,timeout=240):
 p=subprocess.run(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=timeout)
 if p.returncode:raise RuntimeError("command failed "+str(args[:4])+" "+p.stderr[-1200:])
 return p.stdout
session=requests.Session();session.headers["User-Agent"]="Mozilla/5.0 (educational study of publicly embedded training videos)"
try:
 for src in SOURCES:
  page=session.get(src["url"],timeout=45);page.raise_for_status()
  soup=bs4.BeautifulSoup(page.text,"html.parser")
  videos=soup.select("video");i=src["video_index"]
  assert len(videos)>i,(src["title"],len(videos),i)
  v=videos[i];source=v.find("source");assert source and source.get("src")
  header=v.find_previous(["h2","h3","h4","h5"])
  title=header.get_text(" ",strip=True) if header else ""
  assert title==src["title"],(title,src["title"])
  uri=urllib.parse.urljoin(src["url"],source["src"])
  assert urllib.parse.urlsplit(uri).hostname=="studio.blender.org"
  dest=TMP/(f"kaspar_{i}_{'basic' if 'basic-' in src['url'] else 'detailed'}.mp4")
  entry={"title":title,"source":src["url"],"public_media_path":urllib.parse.urlsplit(uri).path,
      "index":i}
  with session.get(uri,timeout=(30,120),stream=True) as response:
   entry["http_get_status"]=response.status_code
   response.raise_for_status()
   with dest.open("wb") as f:
    n=0
    for chunk in response.iter_content(2**20):
     if chunk:
      n+=len(chunk);total+=len(chunk)
      if n>CAP_ONE or total>CAP_TOTAL:raise RuntimeError("fixed budget cap exceeded")
      f.write(chunk)
  assert dest.stat().st_size>15000
  entry["original_video_ephemeral_bytes"]=dest.stat().st_size
  entry["original_video_ephemeral_sha256"]=hashlib.sha256(dest.read_bytes()).hexdigest()
  meta=json.loads(command("ffprobe","-v","error","-show_format","-show_streams","-of","json",str(dest)))
  duration=float(meta["format"]["duration"]);entry["duration_sec"]=duration
  entry["audio_present"]=any(t.get("codec_type")=="audio" for t in meta["streams"])
  frames_dir=TMP/(dest.stem+"_frames");frames_dir.mkdir(exist_ok=True)
  command("ffmpeg","-y","-v","error","-i",str(dest),"-vf","fps=1,scale=360:-2",
          "-q:v","4",str(frames_dir/"f_%04d.jpg"),timeout=250)
  imgs=sorted(frames_dir.glob("f_*.jpg"));assert imgs
  entry["frame_count_1fps"]=len(imgs)
  contact=O/"private_transient_visual_frames";contact.mkdir(exist_ok=True)
  boards=[];cols,rows=4,8;w,h=340,235;per=cols*rows
  for j in range(math.ceil(len(imgs)/per)):
   board=Image.new("RGB",(cols*w,rows*h),(20,22,27));draw=ImageDraw.Draw(board)
   for k,path in enumerate(imgs[j*per:(j+1)*per]):
    im=Image.open(path).convert("RGB");im.thumbnail((w-10,h-25))
    x=(k%cols)*w;y=(k//cols)*h
    board.paste(im,(x+(w-im.width)//2,y))
    seconds=j*per+k
    draw.text((x+6,y+h-20),f"{seconds//60:02d}:{seconds%60:02d}",fill="white")
   q=contact/f"{'BASIC' if 'basic-' in src['url'] else 'DETAILED'}_{j:02d}.jpg"
   board.save(q,quality=74,optimize=True);boards.append(q.name)
  entry["transient_contact_sheets"]=boards
  r["videos"].append(entry)
 r["status"]="ORIGINAL_PUBLIC_TEACHER_VIDEO_CAPTURED_AND_TIMECODED_FRAMES_AVAILABLE_FOR_PRIVATE_REVIEW"
except BaseException as e:
 r["status"]="ACCESS_HOLD_DO_NOT_CLAIM_STUDY";r["error"]=repr(e)[:900]
(O/"V083_REAL_TEACHER_VOXEL_VIDEO_RECEIPT.json").write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n")
print("V083_REAL_KASPAR_VISUAL_VIDEO",json.dumps(r,ensure_ascii=False)[:15500],flush=True)
if r["status"].startswith("ACCESS_HOLD"):raise SystemExit(83)
