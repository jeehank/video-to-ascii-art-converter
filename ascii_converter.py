"""
ASCII Video Converter — High-Fidelity Core Engine

Produces dense, full-coverage ASCII art with 24-bit true color ANSI output.
Every pixel position is filled with a character. No settings to fiddle with —
always maximum detail.
"""

import cv2
import numpy as np
import shutil
from typing import Tuple


# Dense character ramp — 70 characters from darkest to brightest.
# Every brightness level maps to a unique, visually distinct character.
CHAR_RAMP = (
    " `.-':_,^=;><+!rc*/z?sLTv)J7(|Fi{C}fI31tlu[neoZ5Yxjya]"
    "2ESwqkP6h9d4VpOGbUAKXHm8RD#$Bg0MNWQ%&@"
)

# NumPy lookup array for vectorized brightness→character mapping
_RAMP_ARRAY = np.array(list(CHAR_RAMP))
_RAMP_LEN = len(CHAR_RAMP)

# Aspect ratio correction — terminal chars are ~2.2x taller than wide
ASPECT_CORRECTION = 0.45


def get_terminal_size() -> Tuple[int, int]:
    """Return (columns, rows) of the current terminal."""
    try:
        cols, rows = shutil.get_terminal_size()
        return cols, rows
    except Exception:
        return 120, 40


def frame_to_ascii_color(frame: np.ndarray, width: int = 0) -> str:
    """
    Convert a BGR frame to a dense, 24-bit true-color ASCII string.

    This is the highest quality mode — every character position is filled,
    and each character is colored to match the original pixel using
    \\033[38;2;R;G;Bm true-color ANSI escapes.

    Parameters
    ----------
    frame : np.ndarray
        BGR image from OpenCV (H×W×3).
    width : int
        Target character width. 0 = auto-fit to terminal.

    Returns
    -------
    str
        A single string with ANSI color codes, ready to write to stdout.
    """
    if frame is None or frame.size == 0:
        return ""

    # Auto-fit to terminal width
    if width <= 0:
        cols, rows = get_terminal_size()
        width = cols - 1  # Leave 1 col margin to prevent wrapping

    h, w = frame.shape[:2]
    new_height = max(1, int((h / w) * width * ASPECT_CORRECTION))

    # Resize frame — INTER_AREA is best for downscaling
    resized = cv2.resize(frame, (width, new_height), interpolation=cv2.INTER_AREA)

    # Convert to grayscale for character selection
    gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)

    # Vectorized brightness → character index mapping
    indices = (gray.astype(np.float32) / 255.0 * (_RAMP_LEN - 1)).astype(np.int32)
    np.clip(indices, 0, _RAMP_LEN - 1, out=indices)
    char_grid = _RAMP_ARRAY[indices]  # shape: (new_height, width)

    # Convert BGR → RGB for ANSI color codes
    rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)

    # Build the frame string with true-color ANSI escapes — vectorized
    # Detect where the color changes along each row (compare adjacent pixels)
    # shifted holds the previous pixel's color; first pixel always gets a code
    shifted = np.empty_like(rgb)
    shifted[:, 0, :] = 255 + 1          # Force mismatch on the first column
    shifted[:, 1:, :] = rgb[:, :-1, :]  # Previous pixel for columns 1..W-1

    # Boolean mask: True where we need a new ANSI color escape
    color_changed = np.any(rgb != shifted, axis=2)  # shape: (H, W)

    # Pre-format all escape codes as a flat array of strings
    # For pixels where color changed: "\033[38;2;R;G;Bm" + char
    # For pixels where color is the same: just the char
    r_flat = rgb[:, :, 0].ravel()
    g_flat = rgb[:, :, 1].ravel()
    b_flat = rgb[:, :, 2].ravel()
    chars_flat = char_grid.ravel()
    changed_flat = color_changed.ravel()

    # Build token array: pre-allocate list and fill with vectorized ops
    n_pixels = r_flat.shape[0]
    tokens = np.empty(n_pixels, dtype=object)

    # Indices where color changed vs didn't
    idx_changed = np.where(changed_flat)[0]
    idx_same = np.where(~changed_flat)[0]

    # Batch-build escape strings for changed pixels
    if idx_changed.size > 0:
        rc = r_flat[idx_changed]
        gc = g_flat[idx_changed]
        bc = b_flat[idx_changed]
        cc = chars_flat[idx_changed]
        # Use a list comprehension on numpy arrays — much faster than per-pixel loop
        tokens[idx_changed] = [
            f"\033[38;2;{rc[i]};{gc[i]};{bc[i]}m{cc[i]}"
            for i in range(idx_changed.size)
        ]

    # Same-color pixels are just the character
    if idx_same.size > 0:
        tokens[idx_same] = chars_flat[idx_same]

    # Reshape back to (H, W) and join each row
    token_grid = tokens.reshape(new_height, width)
    lines = ["".join(token_grid[y]) for y in range(new_height)]

    return "\033[0m\n".join(lines) + "\033[0m"


def frame_to_ascii_mono(frame: np.ndarray, width: int = 0) -> str:
    """
    Convert a BGR frame to a dense monochrome ASCII string.
    Fallback mode if color is not desired.
    """
    if frame is None or frame.size == 0:
        return ""

    if width <= 0:
        cols, _ = get_terminal_size()
        width = cols - 1

    h, w = frame.shape[:2]
    new_height = max(1, int((h / w) * width * ASPECT_CORRECTION))

    resized = cv2.resize(frame, (width, new_height), interpolation=cv2.INTER_AREA)
    gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)

    indices = (gray.astype(np.float32) / 255.0 * (_RAMP_LEN - 1)).astype(np.int32)
    np.clip(indices, 0, _RAMP_LEN - 1, out=indices)
    char_grid = _RAMP_ARRAY[indices]

    lines = []
    for y in range(new_height):
        lines.append("".join(char_grid[y]))
    return "\n".join(lines)


def estimate_ascii_height(frame_h: int, frame_w: int, ascii_width: int) -> int:
    """Predict how many terminal rows a frame will occupy."""
    return max(1, int((frame_h / frame_w) * ascii_width * ASPECT_CORRECTION))
