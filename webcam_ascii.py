"""
ASCII Webcam — Live camera feed as dense colored ASCII art.

No configuration — always maximum quality, true color, mirror mode.
Flicker-free rendering via cursor repositioning.
"""

import cv2
import sys
import io
import time
import shutil

from ascii_converter import frame_to_ascii_color, get_terminal_size


class WebcamASCII:
    """
    Captures live video from a webcam and renders it as dense,
    true-color ASCII art in real-time.
    """

    def __init__(self, camera_index: int = 0):
        self.camera_index = camera_index

    def start(self):
        """
        Start the live ASCII webcam feed. Blocks until Ctrl+C.
        Always uses full terminal width, dense characters, true color, and mirror mode.
        """
        cap = cv2.VideoCapture(self.camera_index)
        if not cap.isOpened():
            print(f"\033[91m  ✖ Cannot open camera (index {self.camera_index})\033[0m")
            print("\033[90m    Make sure your webcam is connected and not in use.\033[0m")
            return

        # Request good resolution from camera
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        # Minimize camera buffer to reduce latency
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        cols, _ = get_terminal_size()
        ascii_width = cols - 1

        # Hide cursor and clear screen
        sys.stdout.write("\033[?25l")
        sys.stdout.write("\033[2J")
        sys.stdout.flush()

        frame_count = 0
        fps_timer = time.perf_counter()
        display_fps = 0.0
        # Reusable buffer for output
        out = sys.stdout

        try:
            while True:
                start_time = time.perf_counter()

                ret, frame = cap.read()
                if not ret:
                    continue

                # Mirror mode (selfie view)
                frame = cv2.flip(frame, 1)

                ascii_art = frame_to_ascii_color(frame, ascii_width)
                frame_count += 1

                # Calculate FPS every 15 frames
                if frame_count % 15 == 0:
                    now = time.perf_counter()
                    display_fps = 15.0 / max(now - fps_timer, 0.001)
                    fps_timer = now

                # Minimal fixed-width status — no jitter
                fps_str = f"{display_fps:4.0f}"
                status = f"\033[97;1m LIVE \033[0m \033[92m{fps_str} fps\033[0m \033[90m│ Ctrl+C quit\033[0m"

                # Build entire frame in one write to reduce syscalls
                buf = io.StringIO()
                buf.write("\033[H")       # Cursor home (no clear = no flicker)
                buf.write(status)
                buf.write("\033[K\n")     # Clear rest of status line
                buf.write(ascii_art)
                out.write(buf.getvalue())
                out.flush()

                # Target ~60 FPS
                elapsed = time.perf_counter() - start_time
                sleep_time = (1.0 / 60.0) - elapsed
                if sleep_time > 0:
                    time.sleep(sleep_time)

        except KeyboardInterrupt:
            pass
        finally:
            cap.release()
            sys.stdout.write("\033[?25h")
            sys.stdout.write("\033[0m\n\n")
            print(f"\033[96m  ■ Webcam stopped — {frame_count} frames captured\033[0m\n")
