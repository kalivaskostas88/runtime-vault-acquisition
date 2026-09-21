import hashlib
import json
import pathlib
import shutil
import time

from gradio_client import Client, handle_file

IMAGE = pathlib.Path("assets/bard_ref_valid_384.jpg")
VIDEO = pathlib.Path("tmp/bard_ref_static_4s.mp4")
AUDIO = pathlib.Path("tmp/bard_test_4s.wav")
OUTDIR = pathlib.Path("outputs_musetalk")
OUTDIR.mkdir(parents=True, exist_ok=True)
OUTPUT = OUTDIR / "BARD_LIPSYNC_PROOF_002_MUSETALK15.mp4"
RECEIPT = OUTDIR / "BARD_LIPSYNC_PROOF_002_MUSETALK15_RECEIPT.json"

def sha256(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def find_video_path(value):
    if isinstance(value, str):
        p = pathlib.Path(value)
        if p.exists() and p.suffix.lower() in {".mp4", ".webm", ".mov", ".mkv"}:
            return p
    if isinstance(value, dict):
        for key in ("video", "path"):
            if key in value:
                found = find_video_path(value[key])
                if found:
                    return found
        for v in value.values():
            found = find_video_path(v)
            if found:
                return found
    if isinstance(value, (list, tuple)):
        for v in value:
            found = find_video_path(v)
            if found:
                return found
    return None

print("BARD_LIPSYNC_PROOF_002_MUSETALK15_START", flush=True)
print("image_sha256=", sha256(IMAGE), flush=True)
print("video_sha256=", sha256(VIDEO), flush=True)
print("audio_sha256=", sha256(AUDIO), flush=True)

client = Client("henrybit/musetalk-1-5", verbose=True)
print("MUSETALK_CLIENT_CONNECTED", flush=True)

t0 = time.time()
result = client.predict(
    audio_path=handle_file(str(AUDIO)),
    video_path=handle_file(str(VIDEO)),
    bbox_shift=0,
    extra_margin=10,
    parsing_mode="jaw",
    left_cheek_width=90,
    right_cheek_width=90,
    api_name="/generate",
)
elapsed = time.time() - t0
print("MUSETALK_RAW_RESULT=", repr(result), flush=True)

video_path = find_video_path(result)
if video_path is None:
    raise RuntimeError(f"Could not locate generated video in result: {result!r}")

shutil.copy2(video_path, OUTPUT)
receipt = {
    "proof_id": "BARD_LIPSYNC_PROOF_002_MUSETALK15",
    "space": "henrybit/musetalk-1-5",
    "api_name": "/generate",
    "bbox_shift": 0,
    "extra_margin": 10,
    "parsing_mode": "jaw",
    "left_cheek_width": 90,
    "right_cheek_width": 90,
    "image_sha256": sha256(IMAGE),
    "video_sha256": sha256(VIDEO),
    "audio_sha256": sha256(AUDIO),
    "elapsed_seconds": round(elapsed, 3),
    "output": str(OUTPUT),
    "output_sha256": sha256(OUTPUT),
    "output_bytes": OUTPUT.stat().st_size,
}
RECEIPT.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
print(json.dumps(receipt, indent=2), flush=True)
print("BARD_LIPSYNC_PROOF_002_MUSETALK15_OK", flush=True)
