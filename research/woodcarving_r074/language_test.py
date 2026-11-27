"""R074 controlled language hypothesis diagnostic, not validated transcription."""
import hashlib, json, pathlib, subprocess, sys, math
from faster_whisper import WhisperModel
from PIL import Image, ImageDraw
src=pathlib.Path(sys.argv[1]); out=pathlib.Path(sys.argv[2])
def sha(p,algo='sha256'):
    h=hashlib.new(algo)
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()
def run(*args):
    return subprocess.run(args,check=True,capture_output=True,text=True).stdout
assert src.stat().st_size==332428914 and sha(src,'sha1')=='8bfbbcdbe4213f844cf9af782968f09e80337520', 'Source identity mismatch'
probe=json.loads(run('ffprobe','-v','error','-show_format','-show_streams','-of','json',str(src)))
duration=float(probe['format']['duration'])
assert 1229<duration<1233
assert any(s['codec_type']=='audio' for s in probe['streams'])
out.mkdir(parents=True,exist_ok=False)
(out/'ATTRIBUTION.md').write_text('Source: Копаничари.ogv, Petrovskyz, Wikimedia Commons, 30 June 2015. CC BY-SA 4.0: https://creativecommons.org/licenses/by-sa/4.0/ . Source: https://commons.wikimedia.org/wiki/File:Копаничари.ogv . Changes: excerpt 0–70 s; sampled/resized stills, automated transcription with Macedonian language hypothesis (not verified by listening). All media-derived outputs here CC BY-SA 4.0. No endorsement. Machine output unreviewed.\n',encoding='utf-8')
wav=src.parent/'r071_excerpt.wav'
run('ffmpeg','-nostdin','-v','error','-i',str(src),'-t','70','-vn','-ac','1','-ar','16000','-c:a','pcm_s16le',str(wav))
times=[0,10,20,30,35,40,45,50,58,65,69]
sheet=Image.new('RGB',(1200,250*math.ceil(len(times)/3)),'#202020');d=ImageDraw.Draw(sheet)
frames=[]
for i,t in enumerate(times):
    p=out/f'f{i:02}.jpg'
    run('ffmpeg','-nostdin','-v','error','-ss',str(t),'-i',str(src),'-frames:v','1','-vf','scale=960:-2','-q:v','3',str(p))
    with Image.open(p) as img:
        img.thumbnail((390,220));x=i%3*400;y=i//3*250;sheet.paste(img,(x,y));d.text((x+5,y+225),f'Requested {t}s',fill='white')
    frames.append({'requested_seconds':t,'file':p.name,'sha256':sha(p)})
sheet.save(out/'CONTACT.jpg',quality=90)
model=WhisperModel('small',device='cpu',compute_type='int8',cpu_threads=4)
segments,info=model.transcribe(str(wav),language='mk',task='transcribe',beam_size=5,vad_filter=True,condition_on_previous_text=False)
rows=[{'start':s.start,'end':s.end,'text':s.text.strip(),'avg_logprob':s.avg_logprob,'no_speech_prob':s.no_speech_prob,'compression_ratio':s.compression_ratio} for s in segments]
data={'source_sha256':sha(src),'source_size':src.stat().st_size,'duration':duration,'excerpt_seconds':[0,70],'audio_sha256':sha(wav),'model':'small','engine':'faster-whisper 1.2.1','forced_language':'mk','reported_language':info.language,'language_probability_not_detection_evidence':info.language_probability,'segments':rows,'frames':frames,'contact_sha256':sha(out/'CONTACT.jpg'),'status':'RAW_ASR_UNVALIDATED','perceptual_audio_review':False,'translation_review':False}
(out/'RECEIPT.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('R074 extracted',len(rows),'segments; language',info.language,'probability',info.language_probability)
