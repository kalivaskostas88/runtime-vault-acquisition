import hashlib
import json
import pathlib
import shutil
import time

from gradio_client import Client, handle_file

IMAGE = pathlib.Path("assets/bard_ref_320.jpg")
AUDIO = pathlib.Path("tmp/bard_test_4s.wav")
OUTDIR = pathlib.Path("outputs")
OUTDIR.mkdir(parents=True, exist_ok=True)
OUTPUT = OUTDIR / "BARD_WAN_S2V_PROOF_001A.mp4"
RECEIPT = OUTDIR / "BARD_WAN_S2V_PROOF_001A_RECEIPT.json"

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

print("BARD_WAN_S2V_PROOF_001A_START", flush=True)
print("image_sha256=", sha256(IMAGE), flush=True)
print("audio_sha256=", sha256(AUDIO), flush=True)

t0 = time.time()
client = Client("Wan-AI/Wan2.2-S2V", verbose=True)
print("WAN_CLIENT_CONNECTED", flush=True)

result = client.predict(
    ref_img=handle_file(str(IMAGE)),
    audio=handle_file(str(AUDIO)),
    resolution="480P",
    api_name="/predict",
)
elapsed = time.time() - t0
print("WAN_RAW_RESULT=", repr(result), flush=True)

video_path = find_video_path(result)
if video_path is None:
    raise RuntimeError(f"Could not locate generated video in result: {result!r}")

shutil.copy2(video_path, OUTPUT)
receipt = {
    "proof_id": "BARD_WAN_S2V_PROOF_001A",
    "space": "Wan-AI/Wan2.2-S2V",
    "api_name": "/predict",
    "resolution": "480P",
    "image": str(IMAGE),
    "image_sha256": sha256(IMAGE),
    "audio": str(AUDIO),
    "audio_sha256": sha256(AUDIO),
    "elapsed_seconds": round(elapsed, 3),
    "output": str(OUTPUT),
    "output_sha256": sha256(OUTPUT),
    "output_bytes": OUTPUT.stat().st_size,
}
RECEIPT.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
print(json.dumps(receipt, indent=2), flush=True)
print("BARD_WAN_S2V_PROOF_001A_OK", flush=True)
