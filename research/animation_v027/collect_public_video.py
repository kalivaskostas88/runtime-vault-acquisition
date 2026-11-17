#!/usr/bin/env python3
"""Private educational audit of a public YouTube Blender retopology tutorial.
No remote write, no original MP4 persistence; output is bounded evidence.
This is media capture, not human/AI comprehension or Blender skill proof.
"""
import hashlib,json,os,pathlib,re,subprocess,sys,tempfile,zipfile
from PIL import Image,ImageOps,ImageDraw
VID="xzZFQgLdKWk"
WINDOWS=[
("eye_loop_start",432,492,3),
("second_eye_loop",560,620,3),
("connect_loops",785,855,3),
("refine_mesh",1932,1972,3),
("final_refinement",2555,2600,3)
]
OUT=pathlib.Path("research/animation_v027/evidence")
OUT.mkdir(parents=True,exist_ok=True)
def call(args,timeout=360):
 p=subprocess.run(args,text=True,capture_output=True,timeout=timeout)
 if p.returncode:raise RuntimeError(args[0]+" "+p.stderr[-550:])
 return p.stdout
def sha(path):
 h=hashlib.sha256()
 with open(path,"rb") as f:
  for b in iter(lambda:f.read(1048576),b""):h.update(b)
 return h.hexdigest()
def probe(path):
 return json.loads(call(["ffprobe","-v","error","-show_streams","-show_format","-of","json",str(path)]))
def stamp(t):return f"{t//60:02d}:{t%60:02d}"
status={"source":"https://www.youtube.com/watch?v="+VID,"video_id":VID,"run_type":"source_learning_evidence_only","claim_not_made":["complete_lesson_watched","audio_listened_by_researcher","blender_application_pass","art_pass"]}
try:
 with tempfile.TemporaryDirectory() as temp:
  base=pathlib.Path(temp)
  yurl="https://www.youtube.com/watch?v="+VID
  call(["yt-dlp","--no-playlist","--no-progress","--no-warnings","--socket-timeout","20","--retries","2","--fragment-retries","2","--js-runtimes","node","-f","bv*[height<=720]+ba/b[height<=720]/b","--merge-output-format","mp4","--max-filesize","300M","-o",str(base/"source.%(ext)s"),yurl],timeout=540)
  candidates=[p for p in base.glob("source.*") if p.suffix.lower() in [".mp4",".mkv",".webm"]]
  if not candidates:raise RuntimeError("no_video")
  src=candidates[0]
  meta=probe(src)
  duration=float(meta["format"]["duration"])
  if duration<2600 or duration>4000:raise RuntimeError("unexpected_video_duration")
  status.update({"capture":"SUCCESS","duration":duration,"source_sha256":sha(src),"source_bytes":src.stat().st_size,"streams":[{"kind":x.get("codec_type"),"codec":x.get("codec_name"),"width":x.get("width"),"height":x.get("height")} for x in meta["streams"]]})
  for name,start,end,step in WINDOWS:
   if end>duration:continue
   wd=OUT/name
   wd.mkdir(exist_ok=True)
   frames=[]
   for t in range(start,end,step):
    f=wd/f"t{t:04d}.jpg"
    call(["ffmpeg","-hide_banner","-loglevel","error","-y","-ss",str(t),"-i",str(src),"-frames:v","1","-vf","scale=960:-2","-q:v","4",str(f)],timeout=45)
    if not f.is_file():raise RuntimeError("missing_image")
    frames.append({"t":t,"stamp":stamp(t),"path":str(f),"sha256":sha(f)})
   cols=4;cellw=400;cellh=260
   sheet=Image.new("RGB",(cols*cellw,((len(frames)+cols-1)//cols)*cellh),(245,245,245))
   d=ImageDraw.Draw(sheet)
   for i,entry in enumerate(frames):
    with Image.open(entry["path"]) as img:
     img=ImageOps.contain(img.convert("RGB"),(390,225))
     x=i%cols*cellw+(cellw-img.width)//2;y=i//cols*cellh+5
     sheet.paste(img,(x,y))
    d.text((i%cols*cellw+8,i//cols*cellh+233),entry["stamp"],fill=(0,0,0))
   contact=OUT/f"{name}_contact_sheet.jpg";sheet.save(contact,quality=89)
   opus=OUT/f"{name}_audio.opus"
   call(["ffmpeg","-hide_banner","-loglevel","error","-y","-ss",str(start),"-i",str(src),"-t",str(end-start),"-vn","-c:a","libopus","-b:a","48k",str(opus)],timeout=90)
   status[name]={"window_sec":[start,end],"interval":step,"frames":len(frames),"contact_sheet":str(contact),"contact_sha256":sha(contact),"audio":str(opus),"frames_included":frames}
  (OUT/"STATUS.json").write_text(json.dumps(status,ensure_ascii=False,indent=2),encoding="utf-8")
  print(json.dumps({"capture":"SUCCESS","duration":duration,"windows":list(status.keys()),"source_sha256":status["source_sha256"]}))
except Exception as e:
 status["capture"]="FAILED";status["error"]=str(e)[:1000]
 (OUT/"STATUS.json").write_text(json.dumps(status,ensure_ascii=False,indent=2),encoding="utf-8")
 print(json.dumps({"capture":"FAILED","error":str(e)[:500]}))
 sys.exit(1)
