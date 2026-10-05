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

def method_vectorized(rgb_frame, width):
    h, w = rgb_frame.shape[:2]
    new_height = max(1, int((h / w) * width * ASPECT_CORRECTION))
    resized = cv2.resize(rgb_frame, (width, new_height), interpolation=cv2.INTER_AREA)
    gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
    
    indices = (gray.astype(np.float32) * ((_RAMP_LEN - 1) / 255.0)).astype(np.int32)
    char_grid = _RAMP_ARRAY[indices]
    
    rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
    # Slight quantization step of 6 merges noisy micro-variations
    rgb = (rgb // 6) * 6
    
    t0 = time.perf_counter()
    
    color_changed = np.ones((new_height, width), dtype=bool)
    color_changed[:, 1:] = np.any(rgb[:, 1:] != rgb[:, :-1], axis=2)
    
    r_flat = rgb[:, :, 0].ravel()
    g_flat = rgb[:, :, 1].ravel()
    b_flat = rgb[:, :, 2].ravel()
    chars_flat = char_grid.ravel()
    changed_flat = color_changed.ravel()

    n_pixels = r_flat.shape[0]
    tokens = np.empty(n_pixels, dtype=object)

    idx_changed = np.where(changed_flat)[0]
    idx_same = np.where(~changed_flat)[0]

    if idx_changed.size > 0:
        rc = r_flat[idx_changed]
        gc = g_flat[idx_changed]
        bc = b_flat[idx_changed]
        cc = chars_flat[idx_changed]
        tokens[idx_changed] = [
            f"\033[38;2;{rc[i]};{gc[i]};{bc[i]}m{cc[i]}"
            for i in range(idx_changed.size)
        ]

    if idx_same.size > 0:
        tokens[idx_same] = chars_flat[idx_same]

    token_grid = tokens.reshape(new_height, width)
    lines = ["".join(token_grid[y]) for y in range(new_height)]
    result = "\033[0m\n".join(lines) + "\033[0m"
    t1 = time.perf_counter()
    return t1 - t0, len(result)

# Test with actual image
img = np.zeros((480, 640, 3), dtype=np.uint8)
cv2.circle(img, (320, 240), 150, (200, 100, 50), -1)
cv2.rectangle(img, (50, 50), (250, 350), (30, 180, 220), -1)
noise = np.random.normal(0, 3, img.shape).astype(np.int16)
noisy_img = np.clip(img.astype(np.int16) + noise, 0, 255).astype(np.uint8)

for w in [120, 200, 250, 300]:
    t, l = method_vectorized(noisy_img, w)
    print(f"Width {w}: {t*1000:.2f}ms, length: {l/1024:.1f}KB, FPS potential: {1/t:.1f}")
