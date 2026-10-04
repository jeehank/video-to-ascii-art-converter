"""
ASCII Webcam — Live camera feed rendered as ASCII art in the terminal.

Captures from the default (or specified) camera device and streams
the ASCII output in real-time with an FPS counter.
"""

import cv2
import sys
import time
import shutil
from typing import Optional

from ascii_converter import ASCIIConverter, ConversionConfig


class WebcamASCII:
    """
    Captures live video from a webcam and renders it as a continuous
    ASCII art stream in the terminal.
    """

    def __init__(self, camera_index: int = 0, config: Optional[ConversionConfig] = None):
        self.camera_index = camera_index
        self.config = config or ConversionConfig()
        self.converter = ASCIIConverter(self.config)
        self.cap: Optional[cv2.VideoCapture] = None

    def _auto_width(self) -> int:
        """Determine optimal character width from terminal size."""
        try:
            cols, _ = shutil.get_terminal_size()
            return min(cols - 2, 200)
        except Exception:
            return self.config.width

    def start(self, auto_width: bool = True, mirror: bool = True):
        """
        Start the live ASCII webcam feed. Blocks until user presses Ctrl+C.

        Parameters
        ----------
        auto_width : bool
            Automatically fit to terminal width.
        mirror : bool
            Horizontally flip the feed (selfie-mode).
        """
        self.cap = cv2.VideoCapture(self.camera_index)
        if not self.cap.isOpened():
            print(f"\033[91m✖ Cannot open camera (index {self.camera_index})\033[0m")
            print("\033[90m  Make sure your webcam is connected and not in use by another app.\033[0m")
            return

        # Try to set camera resolution for better quality
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        if auto_width:
            self.config.width = self._auto_width()
            self.converter.update_config(self.config)

        actual_w = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        actual_h = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        print(f"\033[96m📷 Live ASCII Webcam\033[0m")
        print(f"\033[90m  Camera: {actual_w}×{actual_h} | ASCII Width: {self.config.width} chars\033[0m")
        print(f"\033[90m  Mirror: {'ON' if mirror else 'OFF'} | Color: {'ON' if self.config.color_enabled else 'OFF'}\033[0m")
        print(f"\033[90m  Press Ctrl+C to stop\033[0m\n")
        time.sleep(1)

        frame_count = 0
        fps_timer = time.perf_counter()
        display_fps = 0.0

        try:
            while True:
                start_time = time.perf_counter()

                ret, frame = self.cap.read()
                if not ret:
                    continue

                if mirror:
                    frame = cv2.flip(frame, 1)

                ascii_art = self.converter.frame_to_ascii(frame)
                frame_count += 1

                # Calculate FPS every 10 frames
                if frame_count % 10 == 0:
                    now = time.perf_counter()
                    display_fps = 10.0 / (now - fps_timer)
                    fps_timer = now

                # Clear and render
                sys.stdout.write("\033[H\033[J")
                status = (
                    f"\033[96m📷 LIVE\033[0m  "
                    f"\033[92m{display_fps:5.1f} FPS\033[0m  "
                    f"\033[90mFrame #{frame_count}\033[0m  "
                    f"\033[93m[Ctrl+C to quit]\033[0m"
                )
                sys.stdout.write(status + "\n\n")
                sys.stdout.write(ascii_art)
                sys.stdout.flush()

                # Small delay to prevent CPU overload; target ~30 FPS
                elapsed = time.perf_counter() - start_time
                target_delay = 1.0 / 30.0
                sleep_time = target_delay - elapsed
                if sleep_time > 0:
                    time.sleep(sleep_time)

        except KeyboardInterrupt:
            pass
        finally:
            self.cap.release()
            sys.stdout.write("\033[0m\n")
            print(f"\n\033[96m■ Webcam stopped after {frame_count} frames\033[0m")
