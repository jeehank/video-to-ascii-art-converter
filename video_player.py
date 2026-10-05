"""
ASCII Video Player — Plays video files as dense colored ASCII art.

No questions asked — always maximum quality, true color, dense characters.
Uses cursor repositioning instead of screen clearing to eliminate flicker.
"""

import cv2
import sys
import time
import os
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
        Always uses full terminal width and height, dense characters, and true color.
        """
        cap = cv2.VideoCapture(self.video_path)
        if not cap.isOpened():
            print(f"\033[91m  ✖ Cannot open video: {self.video_path}\033[0m")
            return

        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        frame_delay = 1.0 / fps
        filename = os.path.basename(self.video_path)

        # Hide cursor and clear screen
        sys.stdout.write("\033[?25l")  # Hide cursor
        sys.stdout.write("\033[2J")    # Clear screen
        sys.stdout.flush()

        frame_num = 0
        last_size = (0, 0)
        try:
            while True:
                start_time = time.perf_counter()

                ret, frame = cap.read()
                if not ret:
                    break

                # Check if terminal was resized or zoomed
                cols, rows = get_terminal_size()
                if (cols, rows) != last_size:
                    sys.stdout.write("\033[2J")  # Clear screen on resize/zoom to prevent ghost characters
                    last_size = (cols, rows)

                # Fits the entire screen in any shape or zoom (edge-to-edge)
                ascii_art = frame_to_ascii_color(frame, width=cols - 1, height=rows - 1)
                frame_num += 1

                # Move cursor to home position and render frame (atomic write, zero flicker)
                sys.stdout.write("\033[H" + ascii_art)
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
