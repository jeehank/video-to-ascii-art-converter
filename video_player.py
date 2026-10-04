"""
ASCII Video Player — Plays video files as dense colored ASCII art.

No questions asked — always maximum quality, true color, dense characters.
Uses cursor repositioning instead of screen clearing to eliminate flicker.
"""

import cv2
import sys
import time
import os
import shutil

from ascii_converter import frame_to_ascii_color, get_terminal_size


class VideoPlayer:
    """
    Reads frames from a video file and renders them as high-fidelity
    colored ASCII art in the terminal at the correct frame rate.
    """

    def __init__(self, video_path: str):
        if not os.path.isfile(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")
        self.video_path = video_path

    def play(self):
        """
        Start playback. Blocks until the video ends or user presses Ctrl+C.
        Always uses full terminal width, dense characters, and true color.
        """
        cap = cv2.VideoCapture(self.video_path)
        if not cap.isOpened():
            print(f"\033[91m  ✖ Cannot open video: {self.video_path}\033[0m")
            return

        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        frame_delay = 1.0 / fps
        filename = os.path.basename(self.video_path)

        # Get terminal width
        cols, _ = get_terminal_size()
        ascii_width = cols - 1

        # Hide cursor and clear screen
        sys.stdout.write("\033[?25l")  # Hide cursor
        sys.stdout.write("\033[2J")    # Clear screen
        sys.stdout.flush()

        frame_num = 0
        try:
            while True:
                start_time = time.perf_counter()

                ret, frame = cap.read()
                if not ret:
                    break

                ascii_art = frame_to_ascii_color(frame, ascii_width)
                frame_num += 1

                # Build status bar
                progress = frame_num / total_frames * 100 if total_frames > 0 else 0
                bar_len = 40
                filled = int(bar_len * frame_num / total_frames) if total_frames > 0 else 0
                bar = "█" * filled + "░" * (bar_len - filled)

                elapsed_sec = frame_num / fps
                total_sec = total_frames / fps if fps > 0 else 0
                time_str = f"{int(elapsed_sec // 60):02d}:{int(elapsed_sec % 60):02d}"
                total_str = f"{int(total_sec // 60):02d}:{int(total_sec % 60):02d}"

                status = (
                    f"\033[97;1m ▶ {filename}\033[0m  "
                    f"\033[93m{bar}\033[0m  "
                    f"\033[96m{time_str}/{total_str}\033[0m  "
                    f"\033[92m{progress:5.1f}%\033[0m  "
                    f"\033[90m[Ctrl+C to stop]\033[0m"
                )

                # Move cursor to home position (no clearing = no flicker)
                sys.stdout.write("\033[H")
                sys.stdout.write(status + "\n")
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
            cap.release()
            sys.stdout.write("\033[?25h")  # Show cursor
            sys.stdout.write("\033[0m\n\n")
            print(f"\033[96m  ■ Playback finished — {frame_num}/{total_frames} frames\033[0m\n")

    def get_info(self) -> dict:
        """Return metadata about the video file."""
        cap = cv2.VideoCapture(self.video_path)
        fps = cap.get(cv2.CAP_PROP_FPS) or 1
        fc = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        info = {
            "path": self.video_path,
            "filename": os.path.basename(self.video_path),
            "fps": fps,
            "frame_count": fc,
            "width": int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            "height": int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            "duration_sec": fc / fps,
        }
        cap.release()
        return info
