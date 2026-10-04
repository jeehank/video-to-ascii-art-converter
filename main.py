"""
ASCII Video Converter — Main Entry Point

No questions, no settings, no hassle.
Option 1 → Opens file explorer to pick a video → plays it as dense colored ASCII.
Option 2 → Starts live webcam as dense colored ASCII.

You can also drag-and-drop a video file onto the terminal input.

Usage:
    python main.py                    Interactive menu
    python main.py video <path>       Play a video directly
    python main.py webcam             Start live webcam
"""

import sys
import os
import time
import threading

# ── Windows terminal setup ───────────────────────────────────────────
if sys.platform == "win32":
    # Enable VT100 / ANSI escape sequences on Windows 10+
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        # STD_OUTPUT_HANDLE = -11
        handle = kernel32.GetStdHandle(-11)
        # ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004
        mode = ctypes.c_ulong()
        kernel32.GetConsoleMode(handle, ctypes.byref(mode))
        kernel32.SetConsoleMode(handle, mode.value | 0x0004)
    except Exception:
        pass
    try:
        import colorama
        colorama.init(strip=False)
    except ImportError:
        pass

from video_player import VideoPlayer
from webcam_ascii import WebcamASCII


# ── Banner ───────────────────────────────────────────────────────────

BANNER = """
\033[38;2;0;255;255m
     █████╗ ███████╗ ██████╗██╗██╗    ██╗   ██╗██╗██████╗ ███████╗ ██████╗ 
    ██╔══██╗██╔════╝██╔════╝██║██║    ██║   ██║██║██╔══██╗██╔════╝██╔═══██╗
    ███████║███████╗██║     ██║██║    ██║   ██║██║██║  ██║█████╗  ██║   ██║
    ██╔══██║╚════██║██║     ██║██║    ╚██╗ ██╔╝██║██║  ██║██╔══╝  ██║   ██║
    ██║  ██║███████║╚██████╗██║██║     ╚████╔╝ ██║██████╔╝███████╗╚██████╔╝
    ╚═╝  ╚═╝╚══════╝ ╚═════╝╚═╝╚═╝      ╚═══╝  ╚═╝╚═════╝ ╚══════╝ ╚═════╝ 
\033[0m
\033[38;2;255;200;50m    ╔══════════════════════════════════════════════════════════════════╗
    ║   Terminal ASCII Art Engine v2.0  ·  True Color  ·  Dense Mode   ║
    ╚══════════════════════════════════════════════════════════════════╝\033[0m
"""


def print_banner():
    print(BANNER)


# ── File picker (opens native Windows/OS file dialog) ────────────────

def open_file_picker() -> str:
    """
    Open the native OS file explorer dialog to pick a video file.
    Returns the selected file path, or empty string if cancelled.
    Uses tkinter which is bundled with Python — no extra install needed.
    """
    try:
        # Import tkinter — hide the root window
        import tkinter as tk
        from tkinter import filedialog

        root = tk.Tk()
        root.withdraw()          # Hide the main tkinter window
        root.attributes('-topmost', True)  # Bring dialog to front

        file_path = filedialog.askopenfilename(
            title="Select a Video File",
            filetypes=[
                ("Video Files", "*.mp4 *.avi *.mkv *.mov *.wmv *.flv *.webm *.m4v *.mpg *.mpeg *.3gp"),
                ("MP4 Files", "*.mp4"),
                ("AVI Files", "*.avi"),
                ("MKV Files", "*.mkv"),
                ("MOV Files", "*.mov"),
                ("All Files", "*.*"),
            ],
        )

        root.destroy()
        return file_path if file_path else ""

    except Exception as e:
        print(f"\033[91m  ✖ Could not open file picker: {e}\033[0m")
        print("\033[90m    Falling back to manual path entry...\033[0m")
        return ""


def clean_path(raw_path: str) -> str:
    """
    Clean a file path from user input or drag-and-drop.
    Handles surrounding quotes, trailing whitespace, and escaped spaces.
    """
    path = raw_path.strip()
    # Remove surrounding quotes (drag-and-drop on Windows wraps paths in quotes)
    if (path.startswith('"') and path.endswith('"')) or \
       (path.startswith("'") and path.endswith("'")):
        path = path[1:-1]
    path = path.strip()
    return path


# ── Play a video file ────────────────────────────────────────────────

def play_video(path: str):
    """Play a video file as dense colored ASCII art. No questions asked."""
    if not os.path.isfile(path):
        print(f"\033[91m  ✖ File not found: {path}\033[0m\n")
        return

    player = VideoPlayer(path)
    info = player.get_info()

    duration = info["duration_sec"]
    dur_str = f"{int(duration // 60):02d}:{int(duration % 60):02d}"

    print(f"\n\033[97;1m  🎬 {info['filename']}\033[0m")
    print(f"\033[90m     {info['width']}×{info['height']}  ·  {info['fps']:.1f} FPS  ·  {info['frame_count']} frames  ·  {dur_str}\033[0m")
    print(f"\033[38;2;255;200;50m\n  Starting in 2 seconds... (maximize your terminal for best quality)\033[0m")
    time.sleep(2)

    player.play()


# ── Interactive menu ─────────────────────────────────────────────────

def interactive_menu():
    """Main interactive menu. Simple, no unnecessary questions."""
    print_banner()

    while True:
        print()
        print("\033[38;2;0;255;255m  ┌──────────────────────────────────────────────────────────────┐\033[0m")
        print("\033[38;2;0;255;255m  │\033[0m                                                              \033[38;2;0;255;255m│\033[0m")
        print("\033[38;2;0;255;255m  │\033[0m   \033[97;1m1.\033[0m  🎬  \033[97mPlay a video file\033[0m  \033[90m(opens file explorer)\033[0m           \033[38;2;0;255;255m│\033[0m")
        print("\033[38;2;0;255;255m  │\033[0m   \033[97;1m2.\033[0m  📷  \033[97mLive webcam\033[0m  \033[90m(real-time ASCII from camera)\033[0m       \033[38;2;0;255;255m│\033[0m")
        print("\033[38;2;0;255;255m  │\033[0m   \033[97;1m3.\033[0m  🚪  \033[97mExit\033[0m                                             \033[38;2;0;255;255m│\033[0m")
        print("\033[38;2;0;255;255m  │\033[0m                                                              \033[38;2;0;255;255m│\033[0m")
        print("\033[38;2;0;255;255m  │\033[0m  \033[90m  Or drag & drop a video file here and press Enter\033[0m          \033[38;2;0;255;255m│\033[0m")
        print("\033[38;2;0;255;255m  │\033[0m                                                              \033[38;2;0;255;255m│\033[0m")
        print("\033[38;2;0;255;255m  └──────────────────────────────────────────────────────────────┘\033[0m")
        print()

        choice = input("\033[38;2;0;255;170m  ➤ \033[0m").strip()

        if choice == "1":
            # Open native file picker
            print("\033[90m  Opening file explorer...\033[0m")
            path = open_file_picker()
            if path:
                play_video(path)
            else:
                print("\033[93m  No file selected.\033[0m")

        elif choice == "2":
            # Start webcam — no questions, just go
            print(f"\033[38;2;255;200;50m\n  Starting webcam in 2 seconds... (maximize your terminal)\033[0m")
            time.sleep(2)
            webcam = WebcamASCII()
            webcam.start()

        elif choice == "3":
            print("\n\033[38;2;0;255;255m  👋 Goodbye!\033[0m\n")
            sys.exit(0)

        else:
            # Check if the user dragged and dropped a file path
            cleaned = clean_path(choice)
            if os.path.isfile(cleaned):
                play_video(cleaned)
            else:
                print("\033[91m  ✖ Invalid option or file not found. Try again.\033[0m")


# ── CLI mode ─────────────────────────────────────────────────────────

def cli_mode():
    """Handle command-line arguments for direct usage."""
    if len(sys.argv) < 2:
        interactive_menu()
        return

    command = sys.argv[1].lower()

    if command == "video":
        if len(sys.argv) < 3:
            print("\033[91m  ✖ Usage: python main.py video <path>\033[0m")
            sys.exit(1)
        path = clean_path(sys.argv[2])
        print_banner()
        play_video(path)

    elif command == "webcam":
        print_banner()
        print(f"\033[38;2;255;200;50m\n  Starting webcam in 2 seconds...\033[0m")
        time.sleep(2)
        webcam = WebcamASCII()
        webcam.start()

    else:
        # Maybe they passed a file path directly
        path = clean_path(sys.argv[1])
        if os.path.isfile(path):
            print_banner()
            play_video(path)
        else:
            print(f"\033[91m  ✖ Unknown command: {command}\033[0m")
            print("\033[90m  Usage:\033[0m")
            print("\033[90m    python main.py                  Interactive menu\033[0m")
            print("\033[90m    python main.py video <path>     Play a video\033[0m")
            print("\033[90m    python main.py webcam           Live webcam\033[0m")
            sys.exit(1)


# ── Entry point ──────────────────────────────────────────────────────

if __name__ == "__main__":
    cli_mode()
