"""R076 licensed documentary overview. Sampled images, not continuous observation."""
import hashlib,json,pathlib,subprocess,sys,math
from PIL import Image,ImageDraw
src=pathlib.Path(sys.argv[1]);out=pathlib.Path(sys.argv[2])
def sha(p,alg='sha256'):
    h=hashlib.new(alg)
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()
def run(*a):return subprocess.run(a,check=True,capture_output=True,text=True).stdout
if src.stat().st_size!=34865152 or sha(src,'sha1')!='d055223722e2a511fdf211f13d01ab5004ed290a':raise ValueError('Identity mismatch')
probe=json.loads(run('ffprobe','-v','error','-show_format','-show_streams','-of','json',str(src)))
dur=float(probe['format']['duration'])
if not 495<dur<499:raise ValueError('Duration mismatch')
out.mkdir(parents=True,exist_ok=False)
(out/'ATTRIBUTION.md').write_text("""Ise agbegilere.webm — Yoruba Wikimedians User Group CC-BY-SA/Yoruba Wikimedians User Group. Source: https://commons.wikimedia.org/wiki/File:Ise_agbegilere.webm (29 September 2022). Tunde Oladimeji, producer/director; Mikaeel Sodiq and Dansu Peter, executive producers; Isaac Olatunde, supervising producer; Bayo Ajibola, cinematography and sound; Olabode Lawal, editor and montage; Adijat Moboluwaduro, chants; Toba Jegede, backing tracks; Fadare Faniyi Tayo, location manager; Olaniyan Olushola, advisor. License https://creativecommons.org/licenses/by-sa/4.0/. Changes: sampled stills, resized, labelled and assembled; no endorsement. All media-derived outputs CC BY-SA 4.0. Original not stored. Nominal five-second filter grid, not verified original PTS.\n""",encoding='utf-8')
times=[]
frames=[];sheets={}
tmp=src.parent/'r076_frames';tmp.mkdir(exist_ok=False)
# Single sequential decode, bounded threads; filter grid is not exact original PTS.
cmd=['ffmpeg','-nostdin','-v','error','-threads','2','-i',str(src),'-map','0:v:0','-vf','fps=1/5:start_time=0:round=near','-filter_threads','1','-threads','1','-q:v','3','-start_number','0',str(tmp/'f%03d.jpg')]
proc=subprocess.run(cmd,capture_output=True,text=True)
if proc.returncode:raise RuntimeError(proc.stderr[-2000:])
files=sorted(tmp.glob('f*.jpg'))
if abs(len(files)-dur/5)>1.5:raise ValueError('Unexpected grid coverage')
times=[i*5 for i in range(len(files))]
for j in range(0,len(times),12):
    chunk=times[j:j+12];sheet=Image.new('RGB',(1440,300*math.ceil(len(chunk)/3)),'#202020');d=ImageDraw.Draw(sheet)
    for k,t in enumerate(chunk):
        p=tmp/f'f{j+k:03}.jpg'
        if not p.exists():raise ValueError('Missing grid image')
        with Image.open(p) as img:
            img.thumbnail((470,265));x=k%3*480;y=k//3*300;sheet.paste(img,(x,y));d.text((x+5,y+270),f'Grid {t:.3f}s',fill='white')
        frames.append({'nominal_grid_seconds':t,'temporary_frame_sha256':sha(p)})
    name=f'CONTACT_{j//12:02}.jpg';sheet.save(out/name,quality=90);sheets[name]=sha(out/name)
r={'source_sha256':sha(src),'source_bytes':src.stat().st_size,'duration_seconds':dur,'streams':[{'codec_type':s['codec_type'],'codec_name':s['codec_name'],'width':s.get('width'),'height':s.get('height')} for s in probe['streams']],'sample_count':len(frames),'requested_interval_seconds':5,'frames':frames,'contact_sha256':sheets,'time_kind':'nominal five-second filter grid; original decoded PTS not verified','visual_review':'NOT_PERFORMED','audio_review':'NOT_PERFORMED','transcript':'NOT_PERFORMED','status':'CAPTURE_ONLY'}
(out/'CAPTURE.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8')
print('Captured',len(frames),'samples',len(sheets),'sheets')
