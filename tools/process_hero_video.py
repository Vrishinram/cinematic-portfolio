import os
import sys
import json
import time
import subprocess
import cv2
import numpy as np
from PIL import Image
import rembg
import imageio_ffmpeg

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MEDIA = os.path.join(ROOT, "public", "media")
SOURCE = r"C:\Users\vrish\Downloads\gemini_generated_video_5c3a6cfb.mp4"

def process_hero():
    print(f"Loading source video: {SOURCE}")
    cap = cv2.VideoCapture(SOURCE)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 24.0
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"Source: {w}x{h}, {total_frames} frames at {fps} fps")

    # Target size: 720x1280
    out_w, out_h = 720, 1280
    packed_w = out_w * 2

    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    mp4_out = os.path.join(MEDIA, "hero.mp4")
    webm_out = os.path.join(MEDIA, "hero.webm")
    poster_out = os.path.join(MEDIA, "hero.jpg")
    manifest_path = os.path.join(MEDIA, "manifest.json")

    os.makedirs(MEDIA, exist_ok=True)

    # Initialize rembg session
    print("Initializing u2netp matting session...")
    session = rembg.new_session("u2netp")

    # Start ffmpeg encoder for mp4 and webm
    cmd_mp4 = [
        ffmpeg_exe, "-v", "error", "-y",
        "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{packed_w}x{out_h}",
        "-r", str(fps), "-i", "-",
        "-an", "-c:v", "libx264", "-preset", "medium", "-crf", "18",
        "-pix_fmt", "yuv420p", "-profile:v", "high", "-level", "4.1",
        "-color_range", "pc", "-movflags", "+faststart", mp4_out
    ]
    proc_mp4 = subprocess.Popen(cmd_mp4, stdin=subprocess.PIPE)

    raw_boxes = []
    prev_alpha = None
    first_frame_color = None

    t0 = time.time()
    for idx in range(total_frames):
        ret, frame = cap.read()
        if not ret:
            break

        if frame.shape[1] != out_w or frame.shape[0] != out_h:
            frame = cv2.resize(frame, (out_w, out_h), interpolation=cv2.INTER_AREA)

        if idx == 0:
            first_frame_color = frame.copy()

        # RGB for PIL / rembg
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(rgb)
        mask_pil = rembg.remove(pil_img, session=session, only_mask=True)
        alpha = np.array(mask_pil, dtype=np.float32) / 255.0

        # Remove small disconnected noise flecks
        mask_u8 = (alpha > 0.15).astype(np.uint8)
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(mask_u8)
        if num_labels > 2:
            # find largest component excluding background (label 0)
            largest_label = 1 + np.argmax(stats[1:, cv2.CC_STAT_AREA])
            clean_mask = (labels == largest_label).astype(np.float32)
            # dilate slightly to preserve soft fringe
            clean_mask = cv2.dilate(clean_mask, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7)))
            alpha = alpha * clean_mask

        # Motion-adaptive temporal smoothing
        if prev_alpha is not None:
            diff = np.abs(alpha - prev_alpha)
            weight = np.clip(0.35 + diff * 2.0, 0.0, 1.0)
            alpha = weight * alpha + (1.0 - weight) * prev_alpha
        prev_alpha = alpha.copy()

        # Soft edge anti-aliasing
        alpha_smooth = cv2.GaussianBlur(alpha, (3, 3), 0.7)

        # Floor fade at the very bottom 2% so shoe contact doesn't hard-clip at canvas boundary
        fade_start = int(out_h * 0.985)
        for y in range(fade_start, out_h):
            t = (y - fade_start) / max(out_h - fade_start, 1)
            alpha_smooth[y, :] *= max(0.0, 1.0 - t * t)

        # Measure subject bounding box
        thresh = alpha_smooth > 0.12
        rows = np.nonzero(thresh.any(1))[0]
        cols = np.nonzero(thresh.any(0))[0]
        if len(rows) > 0 and len(cols) > 0:
            box = [
                round(float(cols[0]) / out_w, 4),
                round(float(rows[0]) / out_h, 4),
                round(float(cols[-1] + 1) / out_w, 4),
                round(float(rows[-1] + 1) / out_h, 4),
            ]
        else:
            box = [0.25, 0.06, 0.75, 0.98]
        raw_boxes.append(box)

        # Side-by-side packed layout: [Colour | Matte]
        matte_u8 = np.clip(alpha_smooth * 255.0, 0, 255).astype(np.uint8)
        matte_3ch = cv2.cvtColor(matte_u8, cv2.COLOR_GRAY2BGR)

        # Left = clean color frame, Right = matte
        packed = np.concatenate([frame, matte_3ch], axis=1)

        proc_mp4.stdin.write(packed.tobytes())

        if (idx + 1) % 30 == 0 or idx == total_frames - 1:
            elapsed = time.time() - t0
            fps_proc = (idx + 1) / elapsed
            print(f"Processed {idx + 1}/{total_frames} frames ({fps_proc:.1f} fps) | box={box}")

    cap.release()
    proc_mp4.stdin.close()
    proc_mp4.wait()
    print("H.264 MP4 encode completed!")

    # Write poster frame
    if first_frame_color is not None:
        cv2.imwrite(poster_out, first_frame_color, [cv2.IMWRITE_JPEG_QUALITY, 90])
        print(f"Poster frame saved to {poster_out}")

    # Generate WebM (VP9) from MP4 using ffmpeg
    print("Encoding VP9 WebM...")
    cmd_webm = [
        ffmpeg_exe, "-v", "error", "-y",
        "-i", mp4_out,
        "-c:v", "libvpx-vp9", "-crf", "26", "-b:v", "0",
        "-row-mt", "1", "-cpu-used", "3", "-pix_fmt", "yuv420p",
        webm_out
    ]
    subprocess.run(cmd_webm, check=True)
    print("VP9 WebM encode completed!")

    # Smooth tracking bounding boxes over time (9-frame moving average)
    boxes_arr = np.array(raw_boxes, dtype=np.float32)
    k = 9
    pad = np.pad(boxes_arr, ((k // 2, k // 2), (0, 0)), mode="edge")
    smoothed = np.stack([
        np.convolve(pad[:, i], np.ones(k) / k, mode="valid")
        for i in range(4)
    ], axis=1)
    track_boxes = np.round(smoothed, 4).tolist()

    # Update manifest.json
    if os.path.exists(manifest_path):
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
    else:
        manifest = {"clips": {}}

    manifest["clips"]["hero"] = {
        "name": "hero",
        "frames": len(track_boxes),
        "w": out_w,
        "h": out_h,
        "mp4": "hero.mp4",
        "webm": "hero.webm",
        "poster": "hero.jpg",
        "packed": "side-by-side: colour | matte",
        "track": track_boxes
    }

    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    print(f"manifest.json updated with {len(track_boxes)} tracking boxes!")

    mp4_size = os.path.getsize(mp4_out) / 1e6
    webm_size = os.path.getsize(webm_out) / 1e6
    print(f"Final MP4: {mp4_size:.2f} MB | WebM: {webm_size:.2f} MB")
    print("HERO PROCESSING COMPLETE!")

if __name__ == "__main__":
    process_hero()
