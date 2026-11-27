import json, subprocess as sp, pathlib as p, hashlib, sys, collections, math
from PIL import Image,ImageDraw
src=p.Path(sys.argv[1]);out=p.Path(sys.argv[2]);out.mkdir(exist_ok=False,parents=True)
assert src.stat().st_size==34865152 and hashlib.sha1(src.read_bytes()).hexdigest()=='d055223722e2a511fdf211f13d01ab5004ed290a'
def probe(*args):
    return json.loads(sp.check_output(['ffprobe','-v','error',*args,'-of','json',str(src)]))
meta=probe('-show_format','-show_streams')
v=probe('-select_streams','v:0','-show_frames','-show_entries','frame=best_effort_timestamp_time,pkt_duration_time,width,height')
ts=[float(f['best_effort_timestamp_time']) for f in v['frames'] if 'best_effort_timestamp_time' in f]
assert ts and len(ts)<100000 and all(math.isfinite(t) for t in ts)
gaps=[(a,b,round(b-a,6)) for a,b in zip(ts,ts[1:]) if b-a>2 or b<a]
report={'source_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'format':meta['format'],'streams':meta['streams'],'decoded_probe_frames':len(ts),'first_pts':ts[0],'last_pts':ts[-1],'gaps':gaps[:100],'gap_count':len(gaps),'dimension_counts':dict(collections.Counter(str((f.get('width'),f.get('height'))) for f in v['frames']))}
(out/'DIAGNOSTIC.json').write_text(json.dumps(report,indent=2))
print(json.dumps({k:report[k] for k in ('decoded_probe_frames','first_pts','last_pts','gap_count','gaps','dimension_counts')}))
# Extract using frame index selection with source PTS from same filter invocation, not assumed duration.
tmp=src.parent/'r077frames';tmp.mkdir()
cmd=['ffmpeg','-nostdin','-v','info','-threads','2','-i',str(src),'-map','0:v:0','-vf',"select='isnan(prev_selected_t)+gte(t-prev_selected_t,5)',showinfo,scale=640:-2",'-fps_mode','vfr','-filter_threads','1','-threads','1','-q:v','4','-start_number','0',str(tmp/'f%04d.jpg')]
r=sp.run(cmd,capture_output=True,text=True,timeout=180)
import re
pts=[float(x) for x in re.findall(r'\bn:\s*\d+\s+pts:\s*-?\d+\s+pts_time:\s*([-\d.e+]+)',r.stderr)]
files=sorted(tmp.glob('f*.jpg'))
report2={'exit':r.returncode,'files':len(files),'pts_count':len(pts),'stderr_tail':r.stderr[-2000:],'frames':[],'sheets':{},'status':'HOLD'}
if r.returncode==0 and len(files)==len(pts) and 0<len(files)<=105:
    for j in range(0,len(files),12):
        sheet=Image.new('RGB',(1200,250*math.ceil(len(files[j:j+12])/3)),'#202020');d=ImageDraw.Draw(sheet)
        for k,f in enumerate(files[j:j+12]):
            t=pts[j+k];x=k%3*400;y=k//3*250
            with Image.open(f) as im:
                im.thumbnail((390,220));sheet.paste(im,(x,y))
            d.text((x+5,y+225),f'Filter PTS {t:.3f}s',fill='white')
            report2['frames'].append({'pts_seconds':t,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()})
        name=f'CONTACT_{j//12:02}.jpg';sheet.save(out/name,quality=85);report2['sheets'][name]=hashlib.sha256((out/name).read_bytes()).hexdigest()
    report2['status']='SAMPLED_VIDEO_PARTIAL_OR_FULL_UNREVIEWED'
(out/'CAPTURE.json').write_text(json.dumps(report2,indent=2))
(out/'ATTRIBUTION.md').write_text('Ise agbegilere.webm — Yoruba Wikimedians User Group, CC BY-SA 4.0 https://creativecommons.org/licenses/by-sa/4.0/ ; source and full credits: https://commons.wikimedia.org/wiki/File:Ise_agbegilere.webm . Changes: sampled, resized, labelled stills and contact sheets; all media-derived outputs CC BY-SA 4.0. No endorsement. Filter PTS, no assumed full coverage.\n')
print(json.dumps({k:report2[k] for k in ('exit','files','pts_count','status','sheets')}))
