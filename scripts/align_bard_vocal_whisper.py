import json, pathlib, os
from faster_whisper import WhisperModel

AUDIO=pathlib.Path("tmp/bard_test_8s_align.wav")
OUT=pathlib.Path("outputs_alignment")
OUT.mkdir(parents=True,exist_ok=True)

lyrics="""Breves dies hominis
mundi vita
humane propaginis
que sit vita, cogita!
Nitimur in vetitum
caro contra spiritum."""

model=WhisperModel("small",device="cpu",compute_type="int8")
segments,info=model.transcribe(
    str(AUDIO),
    beam_size=5,
    best_of=5,
    word_timestamps=True,
    vad_filter=False,
    initial_prompt=lyrics,
    condition_on_previous_text=False
)
result={
  "language":getattr(info,"language",None),
  "language_probability":getattr(info,"language_probability",None),
  "duration":getattr(info,"duration",None),
  "segments":[]
}
for seg in segments:
    row={"start":seg.start,"end":seg.end,"text":seg.text,"words":[]}
    if seg.words:
        for w in seg.words:
            row["words"].append({"start":w.start,"end":w.end,"word":w.word,"probability":w.probability})
    result["segments"].append(row)

(OUT/"BARD_VOCAL_ALIGNMENT_WHISPER_SMALL.json").write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding="utf-8")
print(json.dumps(result,indent=2,ensure_ascii=False))
