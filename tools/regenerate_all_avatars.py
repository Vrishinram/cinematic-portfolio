"""
Step 1: Remove background from the new Vrishin photo to create a clean RGBA cutout.
Step 2: Regenerate all scene avatars from the cutout.
Step 3: Regenerate packed-alpha hero video (hero.mp4 + hero.webm).
"""

import json
import os
import subprocess
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from rembg import remove

# ---- paths ----
SCRATCH = r"C:\Users\vrish\.gemini\antigravity-ide\scratch"
ROOT = os.path.join(SCRATCH, "vrishin-cinematic-portfolio")
PUBLIC = os.path.join(ROOT, "public")
MEDIA = os.path.join(PUBLIC, "media")
MANIFEST = os.path.join(MEDIA, "manifest.json")

PHOTO = os.path.join(SCRATCH, "vrishin_new_photo.png")
CUTOUT = os.path.join(SCRATCH, "vrishin_cutout_suit.png")

# ========================================================================
# STEP 1: Background removal
# ========================================================================
def create_cutout():
    print("=== STEP 1: Creating background-removed cutout ===")
    photo = Image.open(PHOTO).convert("RGBA")
    print(f"  Photo size: {photo.size}")

    # Use rembg to remove background
    result = remove(photo, alpha_matting=True, alpha_matting_foreground_threshold=240,
                    alpha_matting_background_threshold=10, alpha_matting_erode_size=10)
    result.save(CUTOUT, "PNG")
    print(f"  Saved cutout: {CUTOUT} ({result.size})")
    return result

# ========================================================================
# STEP 2: Generate scene figure images
# ========================================================================
def generate_scene_figures():
    print("\n=== STEP 2: Generating scene figure images ===")
    cutout = Image.open(CUTOUT).convert("RGBA")
    bbox = cutout.getbbox()
    if not bbox:
        print("ERROR: cutout has no visible content")
        return
    cropped = cutout.crop(bbox)
    print(f"  Cropped subject: {cropped.size}")

    scenes = [
        ("fin/man.png",          450, 730, 1.02, 0.85),  # Scene 6 Finale
        ("projects/person.png",  160, 335, 0.98, 0.88),  # Scene 4 Arsenal
        ("tools/figure.png",     155, 434, 0.96, 0.85),  # Scene 2 Universe
        ("years/figure.png",     123, 317, 0.96, 0.86),  # Scene 3 Chrono
    ]

    for rel_path, tw, th, fill, fade_pct in scenes:
        scale = (th * fill) / cropped.height
        new_w = int(cropped.width * scale)
        new_h = int(cropped.height * scale)
        scaled = cropped.resize((new_w, new_h), Image.Resampling.LANCZOS)

        img = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
        px = (tw - new_w) // 2
        py = th - new_h
        img.paste(scaled, (px, py), scaled)

        arr = np.array(img)
        fade_start = int(th * fade_pct)
        for y in range(fade_start, th):
            factor = (th - y) / (th - fade_start)
            arr[y, :, 3] = (arr[y, :, 3].astype(float) * factor).astype(np.uint8)

        out_path = os.path.join(PUBLIC, rel_path)
        Image.fromarray(arr).save(out_path, "PNG")
        print(f"  Saved: {rel_path} ({tw}x{th})")

    # Hero poster: 720x1280
    hero_w, hero_h = 720, 1280
    scale_hero = (hero_h * 0.82) / cropped.height
    w_h = int(cropped.width * scale_hero)
    h_h = int(cropped.height * scale_hero)
    scaled_hero = cropped.resize((w_h, h_h), Image.Resampling.LANCZOS)
    hero_img = Image.new("RGB", (hero_w, hero_h), (0, 0, 0))
    px_h = (hero_w - w_h) // 2
    py_h = int(hero_h * 0.22)
    hero_img.paste(scaled_hero, (px_h, py_h), scaled_hero)
    hero_path = os.path.join(MEDIA, "hero.jpg")
    hero_img.save(hero_path, "JPEG", quality=90)
    print(f"  Saved: media/hero.jpg ({hero_w}x{hero_h})")

# ========================================================================
# STEP 2b: Generate fin/plate.jpg (Scene 6 VRISHIN wordmark backdrop)
# ========================================================================
def generate_fin_plate():
    print("\n=== STEP 2b: Generating fin/plate.jpg ===")
    W, H = 1600, 900

    plate = np.zeros((H, W, 3), dtype=np.float32)

    grunge_path = os.path.join(PUBLIC, "tex", "grunge.png")
    grunge = cv2.imread(grunge_path, cv2.IMREAD_GRAYSCALE)
    if grunge is not None:
        grunge = cv2.resize(grunge, (W, H)).astype(np.float32) / 255.0
    else:
        grunge = np.full((H, W), 0.5, dtype=np.float32)

    txt_img = Image.new("L", (W, H), 0)
    draw = ImageDraw.Draw(txt_img)
    font_path = r"C:\Windows\Fonts\impact.ttf"
    font_size = 730
    font = ImageFont.truetype(font_path, font_size)

    temp_img = Image.new("L", (2400, 900), 0)
    temp_draw = ImageDraw.Draw(temp_img)
    temp_draw.text((100, 50), "VRISHIN", font=font, fill=255)
    tbox = temp_img.getbbox()
    t_crop = temp_img.crop(tbox)
    t_resized = t_crop.resize((1180, 720), Image.Resampling.LANCZOS)

    tx = (W - 1180) // 2
    ty = (H - 720) // 2 - 20
    txt_img.paste(t_resized, (tx, ty))

    mask = np.array(txt_img).astype(np.float32) / 255.0

    gy = np.linspace(0.0, 1.0, H).reshape((H, 1, 1))
    col_top = np.array([235, 235, 255], dtype=np.float32)
    col_bot = np.array([15, 15, 190], dtype=np.float32)
    text_col = col_top * (1.0 - gy) + col_bot * gy

    wear = (grunge * 0.4 + 0.6)[:, :, None]
    text_col = text_col * wear

    m3 = mask[:, :, None]
    plate = plate * (1.0 - m3) + text_col * m3

    yy, xx = np.mgrid[0:H, 0:W]
    cx, cy = W // 2, H // 2 + 50
    dist = np.sqrt(((xx - cx) / 360.0) ** 2 + ((yy - cy) / 280.0) ** 2)
    glow = np.exp(-dist * 1.8)[:, :, None]
    red_glow = np.array([12, 10, 140], dtype=np.float32) * glow
    plate = np.clip(plate + red_glow * 0.7, 0, 255)

    vdist = np.sqrt(((xx - W//2) / (W * 0.55)) ** 2 + ((yy - H//2) / (H * 0.55)) ** 2)
    vig = np.clip(1.0 - vdist * 0.75, 0.0, 1.0)[:, :, None]
    plate = np.clip(plate * vig, 0, 255).astype(np.uint8)

    plate_path = os.path.join(PUBLIC, "fin", "plate.jpg")
    cv2.imwrite(plate_path, plate, [cv2.IMWRITE_JPEG_QUALITY, 92])
    print(f"  Saved: fin/plate.jpg ({W}x{H})")

# ========================================================================
# STEP 3: Generate packed-alpha hero video
# ========================================================================
def generate_hero_video():
    print("\n=== STEP 3: Generating packed-alpha hero video ===")
    import imageio_ffmpeg
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    print(f"  Using ffmpeg: {ffmpeg_exe}")

    cutout = Image.open(CUTOUT).convert("RGBA")
    bbox = cutout.getbbox()
    cropped = cutout.crop(bbox)
    cw, ch = cropped.size

    W, H = 720, 1280
    TOTAL_W = W * 2
    FRAMES = 120
    FPS = 24

    target_h = int(H * 0.82)
    base_scale = target_h / ch
    base_w = int(cw * base_scale)
    base_h = int(ch * base_scale)

    track = []
    mp4_out = os.path.join(MEDIA, "hero.mp4")
    webm_out = os.path.join(MEDIA, "hero.webm")

    mp4_cmd = [
        ffmpeg_exe, "-y",
        "-f", "rawvideo", "-vcodec", "rawvideo",
        "-s", f"{TOTAL_W}x{H}", "-pix_fmt", "bgr24",
        "-r", str(FPS), "-i", "-",
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-crf", "18", "-preset", "fast",
        "-movflags", "+faststart",
        mp4_out
    ]
    proc_mp4 = subprocess.Popen(mp4_cmd, stdin=subprocess.PIPE,
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    webm_cmd = [
        ffmpeg_exe, "-y",
        "-f", "rawvideo", "-vcodec", "rawvideo",
        "-s", f"{TOTAL_W}x{H}", "-pix_fmt", "bgr24",
        "-r", str(FPS), "-i", "-",
        "-c:v", "libvpx-vp9", "-b:v", "0", "-crf", "26",
        webm_out
    ]
    proc_webm = subprocess.Popen(webm_cmd, stdin=subprocess.PIPE,
                                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    print(f"  Generating {FRAMES} frames...")
    for f in range(FRAMES):
        phi = 2.0 * np.pi * f / FRAMES
        scale = 1.0 + 0.007 * np.sin(phi)
        dy = int(3.5 * np.cos(phi))

        fw = int(base_w * scale)
        fh = int(base_h * scale)
        resized = cropped.resize((fw, fh), Image.Resampling.LANCZOS)

        canvas_col = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        px = (W - fw) // 2
        py = int(H * 0.11) + dy
        canvas_col.paste(resized, (px, py), resized)

        arr = np.array(canvas_col)
        fade_y = int(H * 0.90)
        for y in range(fade_y, H):
            factor = (H - y) / (H - fade_y)
            arr[y, :, 3] = (arr[y, :, 3].astype(float) * factor).astype(np.uint8)

        alpha = arr[:, :, 3]
        nz_y, nz_x = np.nonzero(alpha > 15)
        if len(nz_y) > 0:
            x0 = float(nz_x.min()) / W
            y0 = float(nz_y.min()) / H
            x1 = float(nz_x.max()) / W
            y1 = float(nz_y.max()) / H
        else:
            x0, y0, x1, y1 = 0.25, 0.11, 0.75, 0.95
        track.append([round(x0, 4), round(y0, 4), round(x1, 4), round(y1, 4)])

        col_rgb = arr[:, :, :3]
        a_norm = (alpha.astype(float) / 255.0)[:, :, np.newaxis]
        col_rgb = (col_rgb * a_norm).astype(np.uint8)
        col_bgr = cv2.cvtColor(col_rgb, cv2.COLOR_RGB2BGR)

        matte_bgr = cv2.cvtColor(alpha, cv2.COLOR_GRAY2BGR)
        packed = np.hstack([col_bgr, matte_bgr])

        if f == 0:
            poster_path = os.path.join(MEDIA, "hero.jpg")
            cv2.imwrite(poster_path, col_bgr, [cv2.IMWRITE_JPEG_QUALITY, 88])
            print(f"  Saved poster: media/hero.jpg")

        raw_bytes = packed.tobytes()
        proc_mp4.stdin.write(raw_bytes)
        proc_webm.stdin.write(raw_bytes)

    proc_mp4.stdin.close()
    proc_mp4.wait()
    print("  MP4 encoded successfully.")

    proc_webm.stdin.close()
    proc_webm.wait()
    print("  WebM encoded successfully.")

    # Update manifest
    with open(MANIFEST, "r", encoding="utf-8") as fp:
        manifest = json.load(fp)
    manifest["clips"]["hero"]["frames"] = FRAMES
    manifest["clips"]["hero"]["track"] = track
    with open(MANIFEST, "w", encoding="utf-8") as fp:
        json.dump(manifest, fp, indent=2)
    print(f"  Updated manifest.json: frames={FRAMES}, track={len(track)}")

# ========================================================================
# MAIN
# ========================================================================
if __name__ == "__main__":
    if not os.path.exists(PHOTO):
        print(f"ERROR: Photo not found at {PHOTO}")
        sys.exit(1)

    create_cutout()
    generate_scene_figures()
    generate_fin_plate()
    generate_hero_video()
    print("\n=== ALL DONE ===")
