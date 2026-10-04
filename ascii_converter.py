"""
ASCII Video Converter — Core Engine

Handles frame-to-ASCII conversion with multiple character density ramps,
optional color support, and edge-detection mode.
"""

import cv2
import numpy as np
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class CharRamp(Enum):
    """Character density ramps from sparse to dense."""
    MINIMAL = " .:-=+*#%@"
    STANDARD = " .'`^\",:;Il!i><~+_-?][}{1)(|\\/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$"
    BLOCKS = " ░▒▓█"
    DENSE = " .,:;i1tfLCG08@"


@dataclass
class ConversionConfig:
    """Configuration for ASCII frame conversion."""
    width: int = 120                          # Output character width
    char_ramp: CharRamp = CharRamp.STANDARD   # Character density ramp
    invert: bool = False                      # Invert brightness mapping
    color_enabled: bool = False               # Enable ANSI color output
    edge_mode: bool = False                   # Use edge-detection filter
    contrast: float = 1.0                     # Contrast multiplier (0.5–2.0)
    brightness: float = 0.0                   # Brightness offset (-50 to 50)


class ASCIIConverter:
    """
    Converts image frames (NumPy arrays from OpenCV) into ASCII character grids.

    Supports grayscale mapping, ANSI 256-color output, edge-detection mode,
    and adjustable contrast/brightness.
    """

    # Correction factor: terminal characters are ~2x taller than wide
    ASPECT_RATIO_CORRECTION = 0.45

    def __init__(self, config: Optional[ConversionConfig] = None):
        self.config = config or ConversionConfig()
        self._ramp = self.config.char_ramp.value
        if self.config.invert:
            self._ramp = self._ramp[::-1]
        self._ramp_len = len(self._ramp)

    def update_config(self, config: ConversionConfig):
        """Hot-swap configuration (e.g. when user changes settings at runtime)."""
        self.config = config
        self._ramp = config.char_ramp.value
        if config.invert:
            self._ramp = self._ramp[::-1]
        self._ramp_len = len(self._ramp)

    def frame_to_ascii(self, frame: np.ndarray) -> str:
        """
        Convert a single BGR frame to an ASCII string.

        Parameters
        ----------
        frame : np.ndarray
            BGR image from OpenCV (H×W×3).

        Returns
        -------
        str
            Multi-line ASCII art string ready to print.
        """
        if frame is None or frame.size == 0:
            return ""

        # Resize to target width, maintaining corrected aspect ratio
        h, w = frame.shape[:2]
        new_width = self.config.width
        new_height = int((h / w) * new_width * self.ASPECT_RATIO_CORRECTION)
        new_height = max(1, new_height)

        resized = cv2.resize(frame, (new_width, new_height), interpolation=cv2.INTER_AREA)

        # Apply contrast & brightness adjustments
        if self.config.contrast != 1.0 or self.config.brightness != 0.0:
            resized = cv2.convertScaleAbs(
                resized,
                alpha=self.config.contrast,
                beta=self.config.brightness,
            )

        # Convert to grayscale for character mapping
        gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)

        # Optional edge-detection mode
        if self.config.edge_mode:
            gray = cv2.Canny(gray, 100, 200)
            # Canny gives 0/255; invert so edges are bright
            gray = 255 - gray

        if self.config.color_enabled:
            return self._build_color_frame(resized, gray)
        else:
            return self._build_mono_frame(gray)

    # ── Private helpers ──────────────────────────────────────────────

    def _pixel_to_char(self, brightness: int) -> str:
        """Map a 0-255 brightness value to an ASCII character."""
        index = int(brightness / 256 * self._ramp_len)
        index = min(index, self._ramp_len - 1)
        return self._ramp[index]

    def _build_mono_frame(self, gray: np.ndarray) -> str:
        """Build a plain monochrome ASCII frame (fast path)."""
        lines = []
        ramp = self._ramp
        ramp_len = self._ramp_len
        for row in gray:
            chars = []
            for pixel in row:
                idx = int(pixel / 256 * ramp_len)
                idx = min(idx, ramp_len - 1)
                chars.append(ramp[idx])
            lines.append("".join(chars))
        return "\n".join(lines)

    def _build_color_frame(self, bgr: np.ndarray, gray: np.ndarray) -> str:
        """Build an ANSI-256 color ASCII frame."""
        lines = []
        ramp = self._ramp
        ramp_len = self._ramp_len

        for y in range(gray.shape[0]):
            row_chars = []
            for x in range(gray.shape[1]):
                # Character from brightness
                idx = int(gray[y, x] / 256 * ramp_len)
                idx = min(idx, ramp_len - 1)
                char = ramp[idx]

                # ANSI 256-color from BGR pixel
                b, g, r = int(bgr[y, x, 0]), int(bgr[y, x, 1]), int(bgr[y, x, 2])
                ansi_code = 16 + (36 * (r * 5 // 255)) + (6 * (g * 5 // 255)) + (b * 5 // 255)
                row_chars.append(f"\033[38;5;{ansi_code}m{char}")

            lines.append("".join(row_chars) + "\033[0m")
        return "\n".join(lines)


def get_frame_ascii_lines_count(frame: np.ndarray, width: int) -> int:
    """Predict how many terminal lines a converted frame will occupy."""
    if frame is None:
        return 0
    h, w = frame.shape[:2]
    return max(1, int((h / w) * width * ASCIIConverter.ASPECT_RATIO_CORRECTION))
