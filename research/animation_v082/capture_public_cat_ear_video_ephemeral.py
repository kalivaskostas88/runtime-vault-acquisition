#!/usr/bin/env python3
"""V082 teacher-first Blender Secrets official YouTube cat-ear/base mesh lesson.
Fetch ONLY openly accessible public version using yt-dlp no auth and no credits.
Full video temporary in GitHub $RUNNER_TEMP, never commit or upload original.
Timecoded frame contacts private 1-day tool artifact ONLY for self-study.
No captions/audio listening claim by sampling frames. Don't evade access controls.
"""
import pathlib,os,subprocess,json,hashlib,math,sys
from PIL import Image,ImageDraw
URL="https://www.youtube.com/watch?v=YFzmfoxHuyM"
ID="YFzmfoxHuyM"
O=pathlib.Path("research/animation_v082");O.mkdir(parents=True,exist_ok=True)
scratch=pathlib.Path(os.environ.get("RUNNER_TEMP","/tmp"))/"v082_private_video";scratch.mkdir(exist_ok=True)
rec={"schema":"V082_BLENDER_SECRETS_ACTUAL_ANIMAL_EAR_VISUAL_TEACHER_STUDY",
"video_id":ID,"source":URL,
"teacher":"Jan van den Hemel, Blender Secrets",
"license":"Video public on YouTube, NOT licensed for redistribution",
"source_video_redistributed":False,"audio_listened":False,
"visual_frames_personally_examined":False,"continuous_full_av_watched":False,
"status":"INIT"}
def run(*args,timeout=300):
 return subprocess.run(args,check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=timeout).stdout
try:
 meta=json.loads(run("yt-dlp","--no-warnings","--no-playlist","--dump-single-json",URL,timeout=90))
 rec["video_metadata"]={k:meta.get(k) for k in ("title","uploader","duration","webpage_url","license","is_live")}
 assert meta.get("id")==ID and not meta.get("is_live")
 assert 5<float(meta.get("duration",0))<1800
 path=scratch/"teacher_animal_ear.%(ext)s"
 run("yt-dlp","--no-warnings","--no-playlist","--no-progress",
     "-f","best[height<=720]/best","--merge-output-format","mp4",
     "--max-filesize","95000000","-o",str(path),URL,timeout=240)
 files=[q for q in scratch.glob("teacher_animal_ear.*") if q.suffix in (".mp4",".webm",".mkv")]
 assert len(files)==1,files
 movie=files[0]
 rec["source_bytes"]=movie.stat().st_size
 assert 100000<rec["source_bytes"]<95000000
 rec["original_sha256_private"]=hashlib.sha256(movie.read_bytes()).hexdigest()
 info=json.loads(run("ffprobe","-v","error","-show_format","-show_streams","-of","json",str(movie)))
 rec["duration_sec"]=float(info["format"]["duration"])
 rec["has_audio_stream"]=any(st.get("codec_type")=="audio" for st in info["streams"])
 frames=scratch/"contact_frames";frames.mkdir()
 rate=1.0
 run("ffmpeg","-y","-v","error","-i",str(movie),"-vf","fps=1,scale=350:-2","-q:v","5",str(frames/"f_%04d.jpg"),timeout=180)
 imgs=sorted(frames.glob("f_*.jpg"));assert len(imgs)>3
 rec["sampled_frames_at_1fps"]=len(imgs)
 contact=O/"internal_contact_sheets";contact.mkdir(exist_ok=True)
 per=24;cols=4;rows=6;w=340;h=255
 names=[]
 for idx in range(math.ceil(len(imgs)/per)):
  sheet=Image.new("RGB",(cols*w,rows*h),(24,24,28));draw=ImageDraw.Draw(sheet)
  for j,frame in enumerate(imgs[idx*per:(idx+1)*per]):
   im=Image.open(frame).convert("RGB")
   im.thumbnail((w-8,h-30));x=(j%cols)*w;y=(j//cols)*h
   sheet.paste(im,(x+(w-im.width)//2,y))
   sec=idx*per+j
   draw.text((x+8,y+h-23),f"{sec//60:02d}:{sec%60:02d}",fill="white")
  q=contact/f"V082_TEACHER_ACTUAL_{idx:02d}.jpg"
  sheet.save(q,quality=75,optimize=True);names.append(q.name)
 rec["private_contact_sheets"]=names
 rec["status"]="PUBLIC_ORIGINAL_VIDEO_CAPTURED_REAL_TIMECODED_FRAMES_PENDING_VISUAL_REVIEW"
except BaseException as e:
 rec["status"]="SOURCE_ACCESS_HOLD_NO_FAKE_VIEWING"
 rec["error"]=repr(e)[:950]
(O/"V082_OFFICIAL_VIDEO_SOURCE_RECEIPT.json").write_text(json.dumps(rec,ensure_ascii=False,indent=2)+"\n")
print("V082_VIDEO_TEACHER_FIRST",json.dumps(rec,ensure_ascii=False)[:6000],flush=True)
if rec["status"].startswith("SOURCE_ACCESS_HOLD"):sys.exit(82)
