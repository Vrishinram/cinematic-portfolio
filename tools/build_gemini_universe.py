import os
import cv2
import numpy as np
import imageio_ffmpeg
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ART_PATH = r"C:\Users\vrish\.gemini\antigravity-ide\brain\2f9345f3-43bf-4f16-8d18-8de3265f3537\cyber_universe_artwork_1793028657658.jpg"
OUT_VIDEO = os.path.join(ROOT, "public", "media", "universe.mp4")
OUT_POSTER = os.path.join(ROOT, "public", "media", "universe.jpg")

W, H = 1280, 720
FPS = 24.0
TOTAL_FRAMES = 480  # 20 seconds @ 24fps

def clean_ceiling(img):
    clean = img.copy()
    h_art, w_art = img.shape[:2]
    x1 = int(w_art * 0.30)
    x2 = int(w_art * 0.70)
    y1 = 0
    y2 = int(h_art * 0.34)
    bg = np.array([2, 2, 4], dtype=np.uint8)
    patch = clean[y1:y2, x1:x2].copy()
    mask = np.zeros((y2 - y1, x2 - x1), dtype=np.float32)
    mask[0:y2-15, 10:x2-x1-10] = 1.0
    mask = cv2.GaussianBlur(mask, (21, 21), 0)[:, :, np.newaxis]
    clean[y1:y2, x1:x2] = (mask * bg + (1.0 - mask) * patch).astype(np.uint8)
    return clean

def generate_embers(num_embers=75):
    # Ethereal floating embers rising from the reflective floor
    np.random.seed(42)
    embers = []
    for _ in range(num_embers):
        embers.append({
            "x": np.random.uniform(100, W - 100),
            "y": np.random.uniform(H * 0.4, H * 0.95),
            "speed_y": np.random.uniform(0.3, 1.2),
            "drift_x": np.random.uniform(-0.25, 0.25),
            "size": np.random.uniform(1.2, 3.2),
            "alpha": np.random.uniform(0.4, 0.85),
            "phase": np.random.uniform(0, 2 * np.pi)
        })
    return embers

def draw_embers(frame, embers, t):
    overlay = frame.copy()
    for emb in embers:
        # compute animated position
        y = (emb["y"] - t * emb["speed_y"] * 8.0) % (H * 0.65) + (H * 0.35)
        x = emb["x"] + np.sin(t * 0.5 + emb["phase"]) * 18.0
        alpha = emb["alpha"] * (0.65 + 0.35 * np.sin(t * 1.5 + emb["phase"]))
        
        # ember glow (red-orange with golden core)
        pt = (int(round(x)), int(round(y)))
        if 0 <= pt[0] < W and 0 <= pt[1] < H:
            rad = int(round(emb["size"]))
            # outer glow
            cv2.circle(overlay, pt, rad * 3, (15, 25, 180), -1)
            # bright core
            cv2.circle(overlay, pt, max(1, rad), (120, 180, 255), -1)
            
    return cv2.addWeighted(overlay, 0.35, frame, 0.65, 0)

def run():
    print(f"Loading generated artwork: {ART_PATH}")
    art = cv2.imread(ART_PATH)
    if art is None:
        raise FileNotFoundError(f"Cannot load artwork from {ART_PATH}")
        
    cleaned_art = clean_ceiling(art)
    base_1280 = cv2.resize(cleaned_art, (W, H), interpolation=cv2.INTER_LANCZOS4)
    
    # Save master poster frame
    cv2.imwrite(OUT_POSTER, base_1280)
    print(f"Saved master poster to {OUT_POSTER}")
    
    embers = generate_embers(70)
    
    temp_out = os.path.join(ROOT, "public", "media", "universe_gen.mp4")
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    
    cmd = [
        ffmpeg_exe,
        "-y",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-s", f"{W}x{H}",
        "-pix_fmt", "bgr24",
        "-r", str(FPS),
        "-i", "-",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-preset", "slow",
        "-crf", "16",
        "-movflags", "+faststart",
        temp_out
    ]
    
    pipe = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    
    xc, yc = W * 0.5, H * 0.52
    
    print("Rendering 480 continuous frames of cinematic 3D cyber universe...")
    for idx in range(TOTAL_FRAMES):
        # 20s seamless loop: forward 10s, reverse 10s
        if idx < 240:
            t_ratio = float(idx) / 239.0
            t_sec = float(idx) / FPS
        else:
            rev_idx = 479 - idx
            t_ratio = float(rev_idx) / 239.0
            t_sec = float(rev_idx) / FPS
            
        # Subtle, elegant breathing dolly zoom: 1.000 to 1.035
        ease = 0.5 * (1.0 - np.cos(np.pi * t_ratio))
        s = 1.0 + 0.035 * ease
        
        # Sub-pixel zoom centered on figure
        M = np.float32([
            [s, 0, (1.0 - s) * xc],
            [0, s, (1.0 - s) * yc]
        ])
        warped = cv2.warpAffine(base_1280, M, (W, H), flags=cv2.INTER_LANCZOS4, borderMode=cv2.BORDER_REFLECT_101)
        
        # Subtle laser ribbon glow pulse
        pulse = 1.0 + 0.08 * np.sin(2 * np.pi * (float(idx) / 120.0))
        if pulse != 1.0:
            r_chan = warped[:, :, 2].astype(float)
            g_chan = warped[:, :, 1].astype(float)
            b_chan = warped[:, :, 0].astype(float)
            laser_mask = (r_chan > 140) & (r_chan > 1.8 * g_chan) & (r_chan > 1.8 * b_chan)
            if np.any(laser_mask):
                warped[laser_mask, 2] = np.clip(r_chan[laser_mask] * pulse, 0, 255).astype(np.uint8)
                
        # Add ambient floating embers
        framed = draw_embers(warped, embers, t_sec)
        
        pipe.stdin.write(framed.tobytes())
        if idx % 60 == 0:
            print(f"Rendered frame {idx}/{TOTAL_FRAMES} (scale={s:.4f})...")
            
    pipe.stdin.close()
    pipe.wait()
    print("Encoding complete!")
    
    if os.path.exists(temp_out) and os.path.getsize(temp_out) > 500000:
        os.replace(temp_out, OUT_VIDEO)
        print(f"Successfully deployed cinematic cyber universe to {OUT_VIDEO}!")

if __name__ == "__main__":
    run()
