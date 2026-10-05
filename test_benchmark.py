import cv2
import numpy as np
import time

CHAR_RAMP = (
    " `.-':_,^=;><+!rc*/z?sLTv)J7(|Fi{C}fI31tlu[neoZ5Yxjya]"
    "2ESwqkP6h9d4VpOGbUAKXHm8RD#$Bg0MNWQ%&@"
)
_RAMP_ARRAY = np.array(list(CHAR_RAMP))
_RAMP_LEN = len(CHAR_RAMP)
ASPECT_CORRECTION = 0.45

def method_pure_loop(rgb_frame, width):
    h, w = rgb_frame.shape[:2]
    new_height = max(1, int((h / w) * width * ASPECT_CORRECTION))
    resized = cv2.resize(rgb_frame, (width, new_height), interpolation=cv2.INTER_AREA)
    gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
    
    indices = (gray.astype(np.float32) * ((_RAMP_LEN - 1) / 255.0)).astype(np.int32)
    char_grid = _RAMP_ARRAY[indices]
    
    rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
    # Slight quantization step of 6 (or bitmask 0xFA / 0xF8)
    # 0xF8 keeps top 5 bits (32 levels per channel)
    rgb = (rgb // 6) * 6
    
    t0 = time.perf_counter()
    
    lines = []
    for y in range(new_height):
        row_rgb = rgb[y]
        row_chars = char_grid[y]
        parts = []
        pr, pg, pb = -1, -1, -1
        for x in range(width):
            r, g, b = row_rgb[x]
            if r != pr or g != pg or b != pb:
                parts.append(f"\033[38;2;{r};{g};{b}m{row_chars[x]}")
                pr, pg, pb = r, g, b
            else:
                parts.append(row_chars[x])
        lines.append("".join(parts))
        
    result = "\033[0m\n".join(lines) + "\033[0m"
    t1 = time.perf_counter()
    return t1 - t0, len(result)

# Test with actual image
img = np.zeros((480, 640, 3), dtype=np.uint8)
cv2.circle(img, (320, 240), 150, (200, 100, 50), -1)
cv2.rectangle(img, (50, 50), (250, 350), (30, 180, 220), -1)
noise = np.random.normal(0, 3, img.shape).astype(np.int16)
noisy_img = np.clip(img.astype(np.int16) + noise, 0, 255).astype(np.uint8)

for w in [120, 200, 250]:
    t, l = method_pure_loop(noisy_img, w)
    print(f"Width {w}: {t*1000:.2f}ms, length: {l/1024:.1f}KB, FPS potential: {1/t:.1f}")
