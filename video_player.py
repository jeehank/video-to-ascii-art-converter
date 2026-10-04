"""
ASCII Video Player — Plays video files as ASCII art in the terminal.

Handles frame timing, terminal clearing, and graceful playback controls.
"""

import cv2
import sys
import time
import os
import shutil
from typing import Optional

from ascii_converter import ASCIIConverter, ConversionConfig


class VideoPlayer:
    """
    Reads frames from a video file and renders them as ASCII art
    in the terminal at the correct frame rate.
    """

    def __init__(self, video_path: str, config: Optional[ConversionConfig] = None):
        if not os.path.isfile(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")

        self.video_path = video_path
        self.config = config or ConversionConfig()
        self.converter = ASCIIConverter(self.config)
        self.cap: Optional[cv2.VideoCapture] = None

    def _auto_width(self) -> int:
        """Determine optimal character width from terminal size."""
        try:
            cols, _ = shutil.get_terminal_size()
            return min(cols - 2, 200)  # Leave 2-col margin, cap at 200
        except Exception:
            return self.config.width

    def play(self, auto_width: bool = True):
        """
        Start playback. Blocks until the video ends or user presses Ctrl+C.

        Parameters
        ----------
        auto_width : bool
            If True, automatically fit ASCII width to current terminal width.
        """
        self.cap = cv2.VideoCapture(self.video_path)
        if not self.cap.isOpened():
            print(f"\033[91m✖ Cannot open video: {self.video_path}\033[0m")
            return

        fps = self.cap.get(cv2.CAP_PROP_FPS) or 30.0
        total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        frame_delay = 1.0 / fps

        if auto_width:
            self.config.width = self._auto_width()
            self.converter.update_config(self.config)

        print(f"\033[96m▶ Playing: {os.path.basename(self.video_path)}\033[0m")
        print(f"\033[90m  FPS: {fps:.1f} | Frames: {total_frames} | Width: {self.config.width} chars\033[0m")
        print(f"\033[90m  Press Ctrl+C to stop\033[0m\n")
        time.sleep(1.5)

        frame_num = 0
        try:
            while True:
                start_time = time.perf_counter()

                ret, frame = self.cap.read()
                if not ret:
                    break

                ascii_art = self.converter.frame_to_ascii(frame)
                frame_num += 1

                # Clear screen and move cursor to top-left
                sys.stdout.write("\033[H\033[J")
                # Status bar
                progress = frame_num / total_frames * 100 if total_frames > 0 else 0
                bar_len = 30
                filled = int(bar_len * frame_num / total_frames) if total_frames > 0 else 0
                bar = "█" * filled + "░" * (bar_len - filled)
                status = (
                    f"\033[96m▶ {os.path.basename(self.video_path)}\033[0m  "
                    f"\033[93m[{bar}]\033[0m  "
                    f"\033[92m{progress:5.1f}%\033[0m  "
                    f"\033[90mFrame {frame_num}/{total_frames}\033[0m"
                )
                sys.stdout.write(status + "\n\n")
                sys.stdout.write(ascii_art)
                sys.stdout.flush()

                # Maintain correct frame rate
                elapsed = time.perf_counter() - start_time
                sleep_time = frame_delay - elapsed
                if sleep_time > 0:
                    time.sleep(sleep_time)

        except KeyboardInterrupt:
            pass
        finally:
            self.cap.release()
            sys.stdout.write("\033[0m\n")
            print(f"\n\033[96m■ Playback stopped at frame {frame_num}/{total_frames}\033[0m")

    def get_info(self) -> dict:
        """Return metadata about the video file."""
        cap = cv2.VideoCapture(self.video_path)
        info = {
            "path": self.video_path,
            "fps": cap.get(cv2.CAP_PROP_FPS),
            "frame_count": int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
            "width": int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            "height": int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            "duration_sec": int(cap.get(cv2.CAP_PROP_FRAME_COUNT) / max(cap.get(cv2.CAP_PROP_FPS), 1)),
        }
        cap.release()
        return info
