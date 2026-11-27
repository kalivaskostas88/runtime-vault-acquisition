"""R078 independent audio extraction and timestamped raw ASR. No claim of translation validity."""
import pathlib as p, subprocess as sp, hashlib, json, sys, wave
from faster_whisper import WhisperModel
src=p.Path(sys.argv[1]);out=p.Path(sys.argv[2]);out.mkdir(parents=True,exist_ok=False)
assert src.stat().st_size==34865152 and hashlib.sha256(src.read_bytes()).hexdigest()=='ce7495ac832a8309ba6e478b00412fece90d39f930750c9c53a27004bf1755ac'
wav=src.parent/'audio.wav'
r=sp.run(['ffmpeg','-nostdin','-v','warning','-i',str(src),'-map','0:a:0','-vn','-ac','1','-ar','16000','-c:a','pcm_s16le',str(wav)],capture_output=True,text=True,timeout=120)
assert wav.is_file() and wav.stat().st_size>32000
with wave.open(str(wav)) as w: dur=w.getnframes()/w.getframerate()
assert 0<dur<500
data={'source_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'audio_sha256':hashlib.sha256(wav.read_bytes()).hexdigest(),'audio_seconds':dur,'ffmpeg_exit':r.returncode,'ffmpeg_warnings':r.stderr[-3000:],'declared_duration':496.925,'prior_video_last_pts':313.104,'asr_model':'small','status':'RAW_ASR_UNVALIDATED','windows':[]}
(out/'ATTRIBUTION.md').write_text('Ise agbegilere.webm — Yoruba Wikimedians User Group, CC BY-SA 4.0 https://creativecommons.org/licenses/by-sa/4.0/ ; original and full credits https://commons.wikimedia.org/wiki/File:Ise_agbegilere.webm . Changes: independent audio extraction and automated timestamped transcription; derived transcript CC BY-SA 4.0; no endorsement. No audio uploaded.\n')
model=WhisperModel('small',device='cpu',compute_type='int8',cpu_threads=4)
for a,b in [(85,165),(170,240),(240,313)]:
    b=min(b,dur)
    if b<=a:continue
    clip=src.parent/f'a{a}.wav'
    sp.run(['ffmpeg','-nostdin','-v','error','-ss',str(a),'-i',str(wav),'-t',str(b-a),str(clip)],check=True,capture_output=True)
    seg,info=model.transcribe(str(clip),language=None,task='transcribe',beam_size=5,vad_filter=True,condition_on_previous_text=False)
    rows=[{'start':round(a+s.start,3),'end':round(a+s.end,3),'text':s.text,'avg_logprob':s.avg_logprob,'no_speech_prob':s.no_speech_prob} for s in seg]
    data['windows'].append({'range':[a,b],'language':info.language,'language_probability':info.language_probability,'segments':rows})
    print(a,b,info.language,info.language_probability,len(rows),flush=True)
(out/'RECEIPT.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
