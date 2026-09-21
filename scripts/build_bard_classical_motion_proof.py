import hashlib
import json
import math
import pathlib
import subprocess
import wave

import cv2
import numpy as np
from PIL import Image, ImageFile

ROOT = pathlib.Path(".")
CONFIG_PATH = ROOT / "config/bard_classical_motion_proof_001.json"
IMAGE_PATH = ROOT / "assets/bard_ref_320.jpg"
AUDIO_PATH = ROOT / "tmp/bard_test_4s.wav"
OUTDIR = ROOT / "outputs_classical"
OUTDIR.mkdir(parents=True, exist_ok=True)
RAW_VIDEO = OUTDIR / "BARD_CLASSICAL_MOTION_PROOF_001_RAW.mp4"
OUTPUT = OUTDIR / "BARD_CLASSICAL_MOTION_PROOF_001.mp4"
RECEIPT = OUTDIR / "BARD_CLASSICAL_MOTION_PROOF_001_RECEIPT.json"

def sha256(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def clamp_rect(rect, width, height):
    x, y, w, h = [int(round(v)) for v in rect]
    x = max(0, min(width - 2, x))
    y = max(0, min(height - 2, y))
    w = max(2, min(width - x, w))
    h = max(2, min(height - y, h))
    return x, y, w, h

def detect_face(img, fallback_norm):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    faces = cascade.detectMultiScale(
        gray,
        scaleFactor=1.05,
        minNeighbors=3,
        minSize=(28, 28),
        flags=cv2.CASCADE_SCALE_IMAGE,
    )
    H, W = img.shape[:2]
    if len(faces):
        face = max(faces, key=lambda r: int(r[2]) * int(r[3]))
        return clamp_rect(face, W, H), True
    fx, fy, fw, fh = fallback_norm
    return clamp_rect((fx * W, fy * H, fw * W, fh * H), W, H), False

def audio_envelope(wav_path, fps, frame_count, smoothing):
    with wave.open(str(wav_path), "rb") as wf:
        channels = wf.getnchannels()
        rate = wf.getframerate()
        sampwidth = wf.getsampwidth()
        if sampwidth != 2:
            raise RuntimeError(f"Expected 16-bit WAV, got sample width {sampwidth}")
        raw = wf.readframes(wf.getnframes())
    audio = np.frombuffer(raw, dtype=np.int16).astype(np.float32)
    if channels > 1:
        audio = audio.reshape(-1, channels).mean(axis=1)
    samples_per_frame = rate / fps
    env = np.zeros(frame_count, dtype=np.float32)
    for i in range(frame_count):
        a = int(round(i * samples_per_frame))
        b = int(round((i + 1) * samples_per_frame))
        chunk = audio[a:b]
        if chunk.size:
            env[i] = float(np.sqrt(np.mean(np.square(chunk / 32768.0))))
    nz = env[env > 1e-6]
    ref = float(np.percentile(nz, 95)) if nz.size else 1.0
    env = np.clip(env / max(ref, 1e-6), 0.0, 1.25)
    out = np.zeros_like(env)
    if len(env):
        out[0] = env[0]
    alpha = float(smoothing)
    for i in range(1, len(env)):
        out[i] = alpha * env[i] + (1.0 - alpha) * out[i - 1]
    return np.clip(out, 0.0, 1.0)

def feather_rect_mask(shape, rect, feather_ratio=0.18):
    H, W = shape[:2]
    x, y, w, h = clamp_rect(rect, W, H)
    mask = np.zeros((H, W), dtype=np.float32)
    mask[y:y+h, x:x+w] = 1.0
    k = int(max(3, round(min(w, h) * feather_ratio)))
    if k % 2 == 0:
        k += 1
    mask = cv2.GaussianBlur(mask, (k, k), 0)
    m = mask.max()
    if m > 0:
        mask /= m
    return mask[..., None]

def blend(base, altered, mask):
    return np.clip(base.astype(np.float32) * (1.0 - mask) + altered.astype(np.float32) * mask, 0, 255).astype(np.uint8)

def region_scale(frame, rect, sx=1.0, sy=1.0, feather=0.20):
    H, W = frame.shape[:2]
    x, y, w, h = clamp_rect(rect, W, H)
    cx = x + w / 2.0
    cy = y + h / 2.0
    M = np.array([
        [sx, 0.0, (1.0 - sx) * cx],
        [0.0, sy, (1.0 - sy) * cy],
    ], dtype=np.float32)
    altered = cv2.warpAffine(frame, M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT_101)
    mask = feather_rect_mask(frame.shape, (x, y, w, h), feather)
    return blend(frame, altered, mask)

def region_affine(frame, rect, angle=0.0, dx=0.0, dy=0.0, feather=0.22):
    H, W = frame.shape[:2]
    x, y, w, h = clamp_rect(rect, W, H)
    cx = x + w / 2.0
    cy = y + h / 2.0
    M = cv2.getRotationMatrix2D((cx, cy), angle, 1.0)
    M[0, 2] += dx
    M[1, 2] += dy
    altered = cv2.warpAffine(frame, M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT_101)
    mask = feather_rect_mask(frame.shape, (x, y, w, h), feather)
    return blend(frame, altered, mask)

def blink_strength(t, times, half_width):
    strength = 0.0
    for center in times:
        d = abs(t - center)
        if d < half_width:
            strength = max(strength, 1.0 - d / half_width)
    return strength

def main():
    cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    fps = int(cfg["fps"])
    duration = float(cfg["duration_seconds"])
    frame_count = int(round(fps * duration))

    ImageFile.LOAD_TRUNCATED_IMAGES = True
    try:
        pil = Image.open(IMAGE_PATH).convert("RGB")
        base = cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)
    except Exception as e:
        raise RuntimeError(f"Could not load {IMAGE_PATH}: {e}") from e
    H, W = base.shape[:2]
    face, face_detected = detect_face(base, cfg["face_fallback_norm"])
    fx, fy, fw, fh = face

    mouth_cfg = cfg["mouth"]
    mouth = clamp_rect((
        fx + fw * mouth_cfg["x0"],
        fy + fh * mouth_cfg["y0"],
        fw * (mouth_cfg["x1"] - mouth_cfg["x0"]),
        fh * (mouth_cfg["y1"] - mouth_cfg["y0"]),
    ), W, H)

    eye_rect = clamp_rect((fx + fw * 0.10, fy + fh * 0.22, fw * 0.80, fh * 0.33), W, H)

    breath_cfg = cfg["torso_breath"]
    torso = clamp_rect((
        fx + fw * breath_cfg["x0"],
        fy + fh * (1.0 + breath_cfg["y0_from_face_bottom"]),
        fw * (breath_cfg["x1"] - breath_cfg["x0"]),
        fh * breath_cfg["height_face_units"],
    ), W, H)

    # Slightly wider face/hood region for head micro-motion.
    face_motion = clamp_rect((fx - fw * 0.16, fy - fh * 0.16, fw * 1.32, fh * 1.34), W, H)

    env = audio_envelope(AUDIO_PATH, fps, frame_count, mouth_cfg["smoothing"])

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(RAW_VIDEO), fourcc, fps, (W, H))
    if not writer.isOpened():
        raise RuntimeError("Could not open VideoWriter")

    face_motion_cfg = cfg["face_micro_motion"]
    blink_cfg = cfg["blink"]

    for i in range(frame_count):
        t = i / fps
        frame = base.copy()

        # Mechanical breathing: only the torso region changes.
        breath_phase = 2.0 * math.pi * t / float(breath_cfg["period_seconds"])
        sx = 1.0 + float(breath_cfg["horizontal_scale_amplitude"]) * math.sin(breath_phase)
        frame = region_scale(frame, torso, sx=sx, sy=1.0, feather=0.28)

        # Tiny controlled head/hood motion.
        phase = 2.0 * math.pi * t / float(face_motion_cfg["period_seconds"])
        angle = float(face_motion_cfg["rotation_degrees"]) * math.sin(phase)
        dx = float(face_motion_cfg["shift_x_pixels"]) * math.sin(phase * 0.83)
        dy = float(face_motion_cfg["shift_y_pixels"]) * math.sin(phase * 1.21)
        frame = region_affine(frame, face_motion, angle=angle, dx=dx, dy=dy, feather=0.28)

        # Two explicit blink events.
        b = blink_strength(t, blink_cfg["times_seconds"], float(blink_cfg["half_width_seconds"]))
        eye_sy = 1.0 - b * (1.0 - float(blink_cfg["min_vertical_scale"]))
        if b > 0.001:
            frame = region_scale(frame, eye_rect, sx=1.0, sy=eye_sy, feather=0.24)

        # Singing mouth is driven only by the frozen audio envelope.
        mouth_scale = float(mouth_cfg["min_scale"]) + float(mouth_cfg["audio_gain"]) * float(env[i])
        frame = region_scale(frame, mouth, sx=1.0, sy=mouth_scale, feather=0.30)

        writer.write(frame)

    writer.release()

    render_cfg = cfg["render"]
    cmd = [
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-i", str(RAW_VIDEO),
        "-i", str(AUDIO_PATH),
        "-c:v", str(render_cfg["video_codec"]),
        "-crf", str(render_cfg["crf"]),
        "-pix_fmt", str(render_cfg["pixel_format"]),
        "-c:a", "aac", "-b:a", "160k",
        "-shortest",
        str(OUTPUT),
    ]
    subprocess.run(cmd, check=True)

    receipt = {
        "proof_id": cfg["proof_id"],
        "method": "deterministic_region_rig_v001",
        "image": str(IMAGE_PATH),
        "audio": str(AUDIO_PATH),
        "image_sha256": sha256(IMAGE_PATH),
        "audio_sha256": sha256(AUDIO_PATH),
        "output_sha256": sha256(OUTPUT),
        "width": W,
        "height": H,
        "fps": fps,
        "duration_seconds": duration,
        "frame_count": frame_count,
        "face_detected_by_haar": bool(face_detected),
        "face_rect": list(map(int, face)),
        "mouth_rect": list(map(int, mouth)),
        "eye_rect": list(map(int, eye_rect)),
        "torso_rect": list(map(int, torso)),
        "audio_envelope_peak": round(float(env.max()), 6),
        "channels": {
            "mouth": "audio_rms_envelope",
            "blink": "explicit_keyframes",
            "face_micro_motion": "deterministic_sine",
            "torso_breath": "deterministic_sine"
        },
        "output": str(OUTPUT),
        "output_bytes": OUTPUT.stat().st_size,
    }
    RECEIPT.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    print(json.dumps(receipt, indent=2), flush=True)
    print("BARD_CLASSICAL_MOTION_PROOF_001_OK", flush=True)

if __name__ == "__main__":
    main()
