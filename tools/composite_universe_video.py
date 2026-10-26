import os
import cv2
import numpy as np
import imageio_ffmpeg
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_VIDEO = os.path.join(ROOT, "public", "media", "universe.mp4")
# We use the original universe backup if available, or current
SRC_ORIG = os.path.join(ROOT, "public", "media", "universe_orig.mp4")
if not os.path.exists(SRC_ORIG):
    # check if section 2 image or git show can give us pristine video
    SRC_ORIG = SRC_VIDEO

TOOLS_DIR = os.path.join(ROOT, "public", "tools")
OUT_VIDEO = os.path.join(ROOT, "public", "media", "universe.mp4")
OUT_POSTER = os.path.join(ROOT, "public", "media", "universe.jpg")

# The 10 prominent cards to replace with Vrishin's cybersecurity & AI stack
CARDS_CONFIG = [
    # (tool_name, old_name, x1, y1, x2, y2, scale_factor)
    ("wireshark",  "photoshop",    324, 0,        492, 127, 0.75),
    ("splunk",     "figma",        133, 169,      302, 361, 0.72),
    ("nmap",       "aftereffects", 411, 247,      492, 319, 0.76),
    ("metasploit", "premiere",     352, 333,      429, 411, 0.74),
    ("burpsuite",  "notion",       272, 421,      371, 524, 0.75),
    ("docker",     "lightroom",    380, 520,      500, 670, 0.74),
    ("langchain",  "midjourney",   980, 220,     1130, 340, 0.74),
    ("snort",      "spline",       939, 388,     1062, 451, 0.76),
    ("python",     "framer",       738, 403,      819, 491, 0.74),
    ("linux",      "webflow",      829, 478,      927, 571, 0.75),
]

# Additional regions to inpaint clean on each frame (secondary slabs & corner text)
EXTRA_INPAINT = [
    (440, 420, 535, 495),      # small slab above lightroom
    (640, 580, 750, 700),      # lower slab behind figure
    (10, 615, 250, 715),       # bottom-left role tag (PRODUCT DESIGNER)
    (5, 170, 80, 480),         # left edge slogan
    (1200, 170, 1275, 480),    # right edge slogan
    (1175, 575, 1275, 700),    # bottom-right impact slogan
]

def load_logos():
    logos = {}
    for tool_name, _, _, _, _, _, _ in CARDS_CONFIG:
        path = os.path.join(TOOLS_DIR, f"{tool_name}.png")
        if not os.path.exists(path):
            raise FileNotFoundError(f"Missing logo: {path}")
        img = cv2.imread(path, cv2.IMREAD_UNCHANGED)
        logos[tool_name] = img
    return logos

def track_all_cards(cap, total_frames):
    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
    ret, f0 = cap.read()
    if not ret:
        raise RuntimeError("Failed to read frame 0")

    card_state = []
    for tool_name, old_name, x1, y1, x2, y2, scale in CARDS_CONFIG:
        w = x2 - x1
        h = y2 - y1
        crop = f0[y1:y2, x1:x2]
        card_state.append({
            "tool": tool_name,
            "crop": crop,
            "cur_x": x1,
            "cur_y": y1,
            "w": w,
            "h": h,
            "scale": scale,
            "traj": [(x1, y1)]
        })

    print(f"Tracking {len(card_state)} cards over {total_frames} frames...")
    for frame_idx in range(1, total_frames):
        ret, frame = cap.read()
        if not ret:
            break
        for s in card_state:
            sx1 = max(0, s["cur_x"] - 25)
            sy1 = max(0, s["cur_y"] - 20)
            sx2 = min(1280, s["cur_x"] + s["w"] + 25)
            sy2 = min(720, s["cur_y"] + s["h"] + 20)
            roi = frame[sy1:sy2, sx1:sx2]
            res = cv2.matchTemplate(roi, s["crop"], cv2.TM_CCOEFF_NORMED)
            _, mv, _, loc = cv2.minMaxLoc(res)
            nx = sx1 + loc[0]
            ny = sy1 + loc[1]
            s["cur_x"] = nx
            s["cur_y"] = ny
            s["traj"].append((nx, ny))

    return card_state

def clean_frame_extras(frame):
    for x1, y1, x2, y2 in EXTRA_INPAINT:
        patch = frame[y1:y2, x1:x2]
        # Detect any bright or colored pixels (white logos, red letters)
        mask = (np.max(patch, axis=2) > 28).astype(np.uint8) * 255
        if np.any(mask):
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
            mask = cv2.dilate(mask, kernel)
            clean = cv2.inpaint(patch, mask, 5, cv2.INPAINT_TELEA)
            frame[y1:y2, x1:x2] = clean
    return frame

def composite_frame(frame, frame_idx, card_state, logos):
    frame = clean_frame_extras(frame)

    for s in card_state:
        tool_name = s["tool"]
        w = s["w"]
        h = s["h"]
        cx, cy = s["traj"][frame_idx]

        if cx < 0 or cy < 0 or cx + w > 1280 or cy + h > 720:
            continue

        patch = frame[cy:cy+h, cx:cx+w]

        # Inpaint old glyph off card face
        mask = (np.max(patch, axis=2) > 35).astype(np.uint8) * 255
        # Keep border intact
        border = 4
        mask[:border, :] = 0
        mask[-border:, :] = 0
        mask[:, :border] = 0
        mask[:, -border:] = 0

        if np.any(mask):
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
            mask = cv2.dilate(mask, kernel)
            clean_slab = cv2.inpaint(patch, mask, 5, cv2.INPAINT_TELEA)
        else:
            clean_slab = patch.copy()

        # Place new logo
        logo = logos[tool_name]
        target_w = int(w * s["scale"])
        scale = target_w / logo.shape[1]
        target_h = int(logo.shape[0] * scale)
        if target_h > int(h * 0.88):
            scale = int(h * 0.88) / logo.shape[0]
            target_h = int(logo.shape[0] * scale)
            target_w = int(logo.shape[1] * scale)

        logo_resized = cv2.resize(logo, (target_w, target_h), interpolation=cv2.INTER_AREA)

        ox = (w - target_w) // 2
        oy = (h - target_h) // 2

        alpha = (logo_resized[:, :, 3] / 255.0)[:, :, np.newaxis]
        logo_rgb = logo_resized[:, :, :3]

        slab_roi = clean_slab[oy:oy+target_h, ox:ox+target_w]
        blended = (alpha * logo_rgb + (1.0 - alpha) * slab_roi).astype(np.uint8)
        clean_slab[oy:oy+target_h, ox:ox+target_w] = blended

        frame[cy:cy+h, cx:cx+w] = clean_slab

    return frame

def run():
    logos = load_logos()
    cap = cv2.VideoCapture(SRC_VIDEO)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 24.0
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"Source video: {w}x{h}, {total_frames} frames @ {fps} fps")

    # Step 1: Track all cards
    card_state = track_all_cards(cap, total_frames)

    # Step 2: Render sample frame 0 to inspect
    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
    ret, f0 = cap.read()
    test_f0 = composite_frame(f0.copy(), 0, card_state, logos)
    cv2.imwrite("tools/test_composite_f0.jpg", test_f0)
    print("Saved tools/test_composite_f0.jpg for inspection!")

    # Step 3: Setup ffmpeg pipe to write new universe.mp4
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    temp_out = os.path.join(ROOT, "public", "media", "universe_cyber.mp4")

    cmd = [
        ffmpeg_exe,
        "-y",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-s", f"{w}x{h}",
        "-pix_fmt", "bgr24",
        "-r", str(fps),
        "-i", "-",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-preset", "medium",
        "-crf", "18",
        "-movflags", "+faststart",
        temp_out
    ]

    pipe = subprocess.Popen(cmd, stdin=subprocess.PIPE)

    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
    print("Processing all 240 frames...")
    for i in range(total_frames):
        ret, frame = cap.read()
        if not ret:
            break
        composited = composite_frame(frame, i, card_state, logos)
        pipe.stdin.write(composited.tobytes())
        if i % 30 == 0:
            print(f"Rendered frame {i}/{total_frames}...")

    pipe.stdin.close()
    pipe.wait()
    cap.release()
    print("Video encoding complete!")

    if os.path.exists(temp_out) and os.path.getsize(temp_out) > 100000:
        cv2.imwrite(OUT_POSTER, test_f0)
        os.replace(temp_out, OUT_VIDEO)
        print(f"Successfully replaced {OUT_VIDEO} and {OUT_POSTER}!")

if __name__ == "__main__":
    run()
