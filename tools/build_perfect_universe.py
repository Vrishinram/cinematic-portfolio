import os
import cv2
import numpy as np
import imageio_ffmpeg
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_ORIG = os.path.join(ROOT, "public", "media", "universe_orig.mp4")
TOOLS_DIR = os.path.join(ROOT, "public", "tools")
OUT_VIDEO = os.path.join(ROOT, "public", "media", "universe.mp4")
OUT_POSTER = os.path.join(ROOT, "public", "media", "universe.jpg")

XC, YC = 705.6, 379.6

CARDS_CONFIG = [
    # (tool_name, x1, y1, x2, y2, scale_factor)
    ("wireshark",  324, 0,        492, 127, 0.75),
    ("splunk",     133, 169,      302, 361, 0.72),
    ("nmap",       411, 247,      492, 319, 0.76),
    ("metasploit", 352, 333,      429, 411, 0.74),
    ("burpsuite",  272, 421,      371, 524, 0.75),
    ("docker",     380, 520,      500, 670, 0.74),
    ("langchain",  980, 220,     1130, 340, 0.74),
    ("snort",      939, 388,     1062, 451, 0.76),
    ("python",     738, 403,      819, 491, 0.74),
    ("linux",      829, 478,      927, 571, 0.75),
]

EXTRA_PATCHES = [
    (440, 420, 535, 495),      # small slab above lightroom
    (640, 580, 750, 700),      # lower slab behind figure
    (10, 615, 250, 715),       # bottom-left role tag (PRODUCT DESIGNER)
    (5, 170, 80, 480),         # left edge slogan
    (1200, 170, 1275, 480),    # right edge slogan
    (1175, 575, 1275, 700),    # bottom-right impact slogan
]

def make_feather(h, w, b=6):
    feather = np.ones((h, w), dtype=np.float32)
    for i in range(b):
        factor = float(i) / float(b)
        feather[i, :] = np.minimum(feather[i, :], factor)
        feather[h - 1 - i, :] = np.minimum(feather[h - 1 - i, :], factor)
        feather[:, i] = np.minimum(feather[:, i], factor)
        feather[:, w - 1 - i] = np.minimum(feather[:, w - 1 - i], factor)
    return feather[:, :, np.newaxis]

def build_static_assets(f0):
    # 1. Clean extra patches
    clean_extras = []
    for x1, y1, x2, y2 in EXTRA_PATCHES:
        w = x2 - x1
        h = y2 - y1
        patch = f0[y1:y2, x1:x2].copy()
        mask = (np.max(patch, axis=2) > 28).astype(np.uint8) * 255
        if np.any(mask):
            k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
            mask = cv2.dilate(mask, k)
            clean = cv2.inpaint(patch, mask, 5, cv2.INPAINT_TELEA)
        else:
            clean = patch.copy()
        clean_extras.append({
            "x1": x1, "y1": y1, "w": w, "h": h,
            "patch": clean,
            "feather": make_feather(h, w, b=5)
        })

    # 2. Clean card overlays
    card_overlays = []
    for tool_name, x1, y1, x2, y2, scale in CARDS_CONFIG:
        w = x2 - x1
        h = y2 - y1
        patch = f0[y1:y2, x1:x2].copy()

        # Inpaint old glyph off card face once
        mask = (np.max(patch, axis=2) > 35).astype(np.uint8) * 255
        border = 4
        mask[:border, :] = 0
        mask[-border:, :] = 0
        mask[:, :border] = 0
        mask[:, -border:] = 0

        if np.any(mask):
            k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
            mask = cv2.dilate(mask, k)
            clean_slab = cv2.inpaint(patch, mask, 5, cv2.INPAINT_TELEA)
        else:
            clean_slab = patch.copy()

        # Place new tool logo
        logo_path = os.path.join(TOOLS_DIR, f"{tool_name}.png")
        logo = cv2.imread(logo_path, cv2.IMREAD_UNCHANGED)

        target_w = int(w * scale)
        sc = target_w / logo.shape[1]
        target_h = int(logo.shape[0] * sc)
        if target_h > int(h * 0.88):
            sc = int(h * 0.88) / logo.shape[0]
            target_h = int(logo.shape[0] * sc)
            target_w = int(logo.shape[1] * sc)

        logo_resized = cv2.resize(logo, (target_w, target_h), interpolation=cv2.INTER_AREA)

        ox = (w - target_w) // 2
        oy = (h - target_h) // 2

        alpha = (logo_resized[:, :, 3] / 255.0)[:, :, np.newaxis]
        logo_rgb = logo_resized[:, :, :3]

        slab_roi = clean_slab[oy:oy+target_h, ox:ox+target_w]
        clean_slab[oy:oy+target_h, ox:ox+target_w] = (alpha * logo_rgb + (1.0 - alpha) * slab_roi).astype(np.uint8)

        card_overlays.append({
            "tool": tool_name,
            "x1": x1, "y1": y1, "w": w, "h": h,
            "overlay": clean_slab,
            "feather": make_feather(h, w, b=6)
        })

    return clean_extras, card_overlays

def apply_composite(frame, s, clean_extras, card_overlays):
    H, W = frame.shape[:2]

    # Apply clean extra patches with analytic sub-pixel scaling
    for ex in clean_extras:
        w_cur = int(round(ex["w"] * s))
        h_cur = int(round(ex["h"] * s))
        x_cur = int(round(XC + s * (ex["x1"] - XC)))
        y_cur = int(round(YC + s * (ex["y1"] - YC)))

        x_start = max(0, x_cur)
        y_start = max(0, y_cur)
        x_end = min(W, x_cur + w_cur)
        y_end = min(H, y_cur + h_cur)

        if x_end <= x_start or y_end <= y_start:
            continue

        patch_scaled = cv2.resize(ex["patch"], (w_cur, h_cur), interpolation=cv2.INTER_LANCZOS4)
        feather_scaled = cv2.resize(ex["feather"], (w_cur, h_cur), interpolation=cv2.INTER_LANCZOS4)[:, :, np.newaxis]

        # Crop to frame bounds
        px_s = x_start - x_cur
        py_s = y_start - y_cur
        px_e = px_s + (x_end - x_start)
        py_e = py_s + (y_end - y_start)

        p = patch_scaled[py_s:py_e, px_s:px_e]
        f = feather_scaled[py_s:py_e, px_s:px_e]
        roi = frame[y_start:y_end, x_start:x_end]
        frame[y_start:y_end, x_start:x_end] = (f * p + (1.0 - f) * roi).astype(np.uint8)

    # Apply card overlays with analytic sub-pixel scaling
    for card in card_overlays:
        w_cur = int(round(card["w"] * s))
        h_cur = int(round(card["h"] * s))
        x_cur = int(round(XC + s * (card["x1"] - XC)))
        y_cur = int(round(YC + s * (card["y1"] - YC)))

        x_start = max(0, x_cur)
        y_start = max(0, y_cur)
        x_end = min(W, x_cur + w_cur)
        y_end = min(H, y_cur + h_cur)

        if x_end <= x_start or y_end <= y_start:
            continue

        ov_scaled = cv2.resize(card["overlay"], (w_cur, h_cur), interpolation=cv2.INTER_LANCZOS4)
        feather_scaled = cv2.resize(card["feather"], (w_cur, h_cur), interpolation=cv2.INTER_LANCZOS4)[:, :, np.newaxis]

        px_s = x_start - x_cur
        py_s = y_start - y_cur
        px_e = px_s + (x_end - x_start)
        py_e = py_s + (y_end - y_start)

        c = ov_scaled[py_s:py_e, px_s:px_e]
        f = feather_scaled[py_s:py_e, px_s:px_e]
        roi = frame[y_start:y_end, x_start:x_end]

        # Blend card face
        blended = (f * c + (1.0 - f) * roi).astype(np.uint8)

        # Preserve bright red laser highlights passing in front
        r = roi[:, :, 2]
        g = roi[:, :, 1]
        b = roi[:, :, 0]
        laser = (r > 130) & (r > 1.8 * g) & (r > 1.8 * b)
        if np.any(laser):
            laser_alpha = ((r.astype(float) - 130.0) / 125.0).clip(0, 1)[:, :, np.newaxis]
            blended = (laser_alpha * roi + (1.0 - laser_alpha) * blended).astype(np.uint8)

        frame[y_start:y_end, x_start:x_end] = blended

    return frame

def run():
    cap = cv2.VideoCapture(SRC_ORIG)
    total_orig = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 24.0
    W = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    H = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"Loaded {SRC_ORIG}: {W}x{H}, {total_orig} frames @ {fps} fps")

    # Read all pristine original frames into memory (240 frames is ~660 MB, easily fits in RAM)
    print("Buffering 240 original frames...")
    orig_frames = []
    while True:
        ret, f = cap.read()
        if not ret:
            break
        orig_frames.append(f)
    cap.release()

    if len(orig_frames) < 240:
        raise RuntimeError(f"Expected 240 frames, got {len(orig_frames)}")

    # Build clean static assets once off frame 0
    clean_extras, card_overlays = build_static_assets(orig_frames[0])
    print("Built all static assets.")

    # 480 frames seamless ping-pong loop:
    # 0..239 forward, 240..479 reverse
    total_loop_frames = 480
    temp_out = os.path.join(ROOT, "public", "media", "universe_perfect.mp4")

    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    cmd = [
        ffmpeg_exe,
        "-y",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-s", f"{W}x{H}",
        "-pix_fmt", "bgr24",
        "-r", str(fps),
        "-i", "-",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-preset", "slow",
        "-crf", "17",
        "-movflags", "+faststart",
        temp_out
    ]

    pipe = subprocess.Popen(cmd, stdin=subprocess.PIPE)

    print("Rendering 480 continuous frames with 0% flicker...")
    poster_frame = None

    for idx in range(total_loop_frames):
        if idx < 240:
            frame_raw = orig_frames[idx].copy()
            # Smooth cosine easing for camera zoom to prevent any jerk at extremes
            # phase from 0 to pi: zoom goes 1.0 to 1.1505
            t_ratio = float(idx) / 239.0
        else:
            rev_idx = 479 - idx
            frame_raw = orig_frames[rev_idx].copy()
            t_ratio = float(rev_idx) / 239.0

        # Continuous smooth ease: 0.5 * (1 - cos(pi * t))
        ease = 0.5 * (1.0 - np.cos(np.pi * t_ratio))
        s = 1.0 + 0.1505 * ease

        out_frame = apply_composite(frame_raw, s, clean_extras, card_overlays)

        if idx == 0:
            poster_frame = out_frame.copy()

        pipe.stdin.write(out_frame.tobytes())

        if idx % 60 == 0:
            print(f"Rendered frame {idx}/{total_loop_frames} (zoom={s:.4f})...")

    pipe.stdin.close()
    pipe.wait()
    print("Video encoding complete!")

    if os.path.exists(temp_out) and os.path.getsize(temp_out) > 500000:
        cv2.imwrite(OUT_POSTER, poster_frame)
        os.replace(temp_out, OUT_VIDEO)
        print(f"Successfully deployed flicker-free {OUT_VIDEO} and {OUT_POSTER}!")

if __name__ == "__main__":
    run()
