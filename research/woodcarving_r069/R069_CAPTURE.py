"""Bounded FFmpeg evidence extraction; no interpretation and no network. R069."""
import argparse, json, hashlib, subprocess, pathlib, math
from PIL import Image, ImageDraw

def run(*a):
    return subprocess.run(a, check=True, capture_output=True, text=True).stdout

def sha(p, algo='sha256'):
    h=hashlib.new(algo)
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()

def capture(src, out, test=False):
    if not test:
        if src.stat().st_size!=23740143 or sha(src,'sha1')!='2118a39b982fe04c3aad360f8adc4f6fc4f8e2b5': raise ValueError('Original source identity mismatch')
    if out.exists(): raise ValueError('Output path already exists')
    probe=json.loads(run('ffprobe','-v','error','-show_streams','-show_format','-of','json',str(src)))
    dur=float(probe['format']['duration']); v=next(s for s in probe['streams'] if s['codec_type']=='video')
    if not 0<dur<=35: raise ValueError('Pilot duration out of bounds')
    out.mkdir(parents=True); (out/'frames').mkdir()
    # Explicit seek times, not inferred from filename or frame count. PTS not certified.
    times=sorted(set([float(i) for i in range(math.floor(dur))]+[max(0,dur-0.15)]))
    entries=[]
    for i,t in enumerate(times):
        p=out/'frames'/f'f{i:03}.jpg'
        run('ffmpeg','-nostdin','-v','error','-ss',f'{t:.6f}','-i',str(src),'-frames:v','1','-vf','scale=960:-2','-q:v','3',str(p))
        if not p.is_file(): raise ValueError(f'Missing image for request {t}')
        with Image.open(p) as im: im.verify()
        entries.append({'requested_seconds':round(t,6),'path':str(p.relative_to(out)),'sha256':sha(p)})
    for j in range(0,len(entries),12):
        subset=entries[j:j+12]; sheet=Image.new('RGB',(1200,250*math.ceil(len(subset)/3)), '#202020'); d=ImageDraw.Draw(sheet)
        for k,e in enumerate(subset):
            with Image.open(out/e['path']) as img:
                img.thumbnail((390,220)); x=k%3*400; y=k//3*250; sheet.paste(img,(x,y)); d.text((x+5,y+225),f"Requested {e['requested_seconds']:.3f}s", fill='white')
        sheet.save(out/f'CONTACT_{j//12:02}.jpg',quality=90)
    r={'mode':'SYNTHETIC_TEST' if test else 'CC0_CAPTURE','source_sha256':sha(src),'source_bytes':src.stat().st_size,'duration_seconds':dur,'resolution':[v['width'],v['height']],'audio_streams':sum(s['codec_type']=='audio' for s in probe['streams']),'frame_count':len(entries),'frames':entries,'contact_sha256':{p.name:sha(p) for p in sorted(out.glob('CONTACT_*.jpg'))},'frame_time_kind':'requested seek time; exact decoded PTS not established','visual_review':'NOT_PERFORMED','motion_review':'NOT_PERFORMED','transcript':'NOT_PERFORMED','status':'CAPTURE_ONLY'}
    (out/'CAPTURE.json').write_text(json.dumps(r,indent=2)+'\n'); return r
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('source',type=pathlib.Path);p.add_argument('out',type=pathlib.Path);p.add_argument('--synthetic-test',action='store_true');a=p.parse_args();print(json.dumps(capture(a.source,a.out,a.synthetic_test),indent=2))
