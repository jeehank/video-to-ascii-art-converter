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

def benchmark_converter(rgb_frame, width, quantize=False):
    h, w = rgb_frame.shape[:2]
    new_height = max(1, int((h / w) * width * ASPECT_CORRECTION))
    resized = cv2.resize(rgb_frame, (width, new_height), interpolation=cv2.INTER_AREA)
    gray = cv2.cvtColor(resized, cv2.COLOR_RGB2GRAY)
    
    indices = (gray.astype(np.float32) / 255.0 * (_RAMP_LEN - 1)).astype(np.int32)
    np.clip(indices, 0, _RAMP_LEN - 1, out=indices)
    char_grid = _RAMP_ARRAY[indices]
    
    rgb = resized
    if quantize:
        # Slight quantization (e.g. step of 6) to merge imperceptibly close colors
        # and reduce terminal ANSI blast
        rgb_q = (rgb // 6) * 6
    else:
        rgb_q = rgb

    t0 = time.perf_counter()
    
    # Check changes across columns
    color_changed = np.ones((new_height, width), dtype=bool)
    color_changed[:, 1:] = np.any(rgb_q[:, 1:] != rgb_q[:, :-1], axis=2)

    r = rgb_q[:, :, 0]
    g = rgb_q[:, :, 1]
    b = rgb_q[:, :, 2]
    
    lines = []
    for y in range(new_height):
        row_chars = char_grid[y]
        row_changed = color_changed[y]
        row_r = r[y]
        row_g = g[y]
        row_b = b[y]
        
        row_parts = []
        for x in range(width):
            if row_changed[x]:
                row_parts.append(f"\033[38;2;{row_r[x]};{row_g[x]};{row_b[x]}m{row_chars[x]}")
            else:
                row_parts.append(row_chars[x])
        lines.append("".join(row_parts))
    
    result = "\033[0m\n".join(lines) + "\033[0m"
    t1 = time.perf_counter()
    return t1 - t0, len(result), color_changed.mean()

# Test with actual image
img = np.zeros((480, 640, 3), dtype=np.uint8)
cv2.circle(img, (320, 240), 150, (200, 100, 50), -1)
cv2.rectangle(img, (50, 50), (250, 350), (30, 180, 220), -1)
# Add some camera noise
noise = np.random.normal(0, 3, img.shape).astype(np.int16)
noisy_img = np.clip(img.astype(np.int16) + noise, 0, 255).astype(np.uint8)

for w in [120, 200, 250]:
    t_no_q, len_no_q, ch_no_q = benchmark_converter(noisy_img, w, quantize=False)
    t_q, len_q, ch_q = benchmark_converter(noisy_img, w, quantize=True)
    print(f"Width {w}:")
    print(f"  Without quantize: {t_no_q*1000:.2f}ms, length: {len_no_q/1024:.1f}KB, changes: {ch_no_q*100:.1f}%")
    print(f"  With quantize:    {t_q*1000:.2f}ms, length: {len_q/1024:.1f}KB, changes: {ch_q*100:.1f}%")
