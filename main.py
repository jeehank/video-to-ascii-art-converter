"""
ASCII Video Converter — Main CLI Entry Point

A feature-rich command-line tool that converts videos and live webcam
feeds into real-time ASCII art in your terminal.

Usage:
    python main.py video <path>       Play a video file as ASCII art
    python main.py webcam             Stream live webcam as ASCII art
    python main.py                    Launch interactive menu

Options are configurable via flags (see --help).
"""

import argparse
import sys
import os
import time

# Enable ANSI escape codes on Windows
if sys.platform == "win32":
    try:
        import colorama
        colorama.init()
    except ImportError:
        # Fallback: enable VT100 processing via Windows API
        import ctypes
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)

from ascii_converter import ConversionConfig, CharRamp
from video_player import VideoPlayer
from webcam_ascii import WebcamASCII


# ── Banner ───────────────────────────────────────────────────────────

BANNER = r"""
[96m
     █████╗ ███████╗ ██████╗██╗██╗    ██╗   ██╗██╗██████╗ ███████╗ ██████╗ 
    ██╔══██╗██╔════╝██╔════╝██║██║    ██║   ██║██║██╔══██╗██╔════╝██╔═══██╗
    ███████║███████╗██║     ██║██║    ██║   ██║██║██║  ██║█████╗  ██║   ██║
    ██╔══██║╚════██║██║     ██║██║    ╚██╗ ██╔╝██║██║  ██║██╔══╝  ██║   ██║
    ██║  ██║███████║╚██████╗██║██║     ╚████╔╝ ██║██████╔╝███████╗╚██████╔╝
    ╚═╝  ╚═╝╚══════╝ ╚═════╝╚═╝╚═╝      ╚═══╝  ╚═╝╚═════╝ ╚══════╝ ╚═════╝ 
[0m
[93m    ╔══════════════════════════════════════════════════════════════╗
    ║  Video → ASCII Art Converter   |   Terminal Art Engine v1.0 ║
    ╚══════════════════════════════════════════════════════════════╝[0m
"""


def print_banner():
    """Display the application banner."""
    print(BANNER)


# ── Interactive menu ─────────────────────────────────────────────────

def interactive_menu():
    """Launch the interactive menu when no CLI arguments are given."""
    print_banner()

    while True:
        print("\033[96m┌─────────────────────────────────────────┐\033[0m")
        print("\033[96m│\033[0m  \033[93m1.\033[0m 🎬  Play a video file as ASCII      \033[96m│\033[0m")
        print("\033[96m│\033[0m  \033[93m2.\033[0m 📷  Live webcam ASCII stream        \033[96m│\033[0m")
        print("\033[96m│\033[0m  \033[93m3.\033[0m ⚙️   Settings & help                 \033[96m│\033[0m")
        print("\033[96m│\033[0m  \033[93m4.\033[0m 🚪  Exit                             \033[96m│\033[0m")
        print("\033[96m└─────────────────────────────────────────┘\033[0m")
        print()

        choice = input("\033[92m  ➤ Select an option (1-4): \033[0m").strip()

        if choice == "1":
            video_menu()
        elif choice == "2":
            webcam_menu()
        elif choice == "3":
            settings_help()
        elif choice == "4":
            print("\n\033[96m  👋 Goodbye!\033[0m\n")
            sys.exit(0)
        else:
            print("\033[91m  ✖ Invalid choice. Please try again.\033[0m\n")


def video_menu():
    """Prompt user for video file and settings, then play."""
    print("\n\033[96m  ── 🎬 Video File Mode ──\033[0m\n")

    path = input("\033[92m  ➤ Enter video file path: \033[0m").strip()
    # Remove surrounding quotes if user pasted a path with quotes
    path = path.strip('"').strip("'")

    if not os.path.isfile(path):
        print(f"\033[91m  ✖ File not found: {path}\033[0m\n")
        return

    config = prompt_settings()
    player = VideoPlayer(path, config)

    # Show video info
    info = player.get_info()
    print(f"\n\033[90m  📄 {os.path.basename(path)}")
    print(f"     Resolution: {info['width']}×{info['height']}")
    print(f"     Duration:   {info['duration_sec']}s ({info['frame_count']} frames @ {info['fps']:.1f} FPS)\033[0m")
    print(f"\n\033[93m  Starting playback in 2 seconds...\033[0m")
    time.sleep(2)

    player.play()
    print()


def webcam_menu():
    """Prompt user for webcam settings, then start live feed."""
    print("\n\033[96m  ── 📷 Live Webcam Mode ──\033[0m\n")

    cam_input = input("\033[92m  ➤ Camera index (default 0): \033[0m").strip()
    cam_index = int(cam_input) if cam_input.isdigit() else 0

    mirror_input = input("\033[92m  ➤ Mirror mode / selfie view? (y/n, default y): \033[0m").strip().lower()
    mirror = mirror_input != "n"

    config = prompt_settings()
    webcam = WebcamASCII(cam_index, config)

    print(f"\n\033[93m  Starting webcam in 2 seconds...\033[0m")
    time.sleep(2)

    webcam.start(mirror=mirror)
    print()


def prompt_settings() -> ConversionConfig:
    """Ask the user for conversion settings interactively."""
    print()
    print("\033[90m  ── Quick Settings (press Enter for defaults) ──\033[0m")

    # Character ramp
    print("\033[90m  Character styles:\033[0m")
    print("\033[90m    1. Standard (detailed, default)\033[0m")
    print("\033[90m    2. Minimal (clean)\033[0m")
    print("\033[90m    3. Block characters (░▒▓█)\033[0m")
    print("\033[90m    4. Dense (compact)\033[0m")
    ramp_input = input("\033[92m  ➤ Style (1-4): \033[0m").strip()
    ramp_map = {"1": CharRamp.STANDARD, "2": CharRamp.MINIMAL, "3": CharRamp.BLOCKS, "4": CharRamp.DENSE}
    char_ramp = ramp_map.get(ramp_input, CharRamp.STANDARD)

    # Color
    color_input = input("\033[92m  ➤ Enable color output? (y/n, default n): \033[0m").strip().lower()
    color_enabled = color_input == "y"

    # Invert
    invert_input = input("\033[92m  ➤ Invert brightness? (y/n, default n): \033[0m").strip().lower()
    invert = invert_input == "y"

    # Edge mode
    edge_input = input("\033[92m  ➤ Edge-detection mode? (y/n, default n): \033[0m").strip().lower()
    edge_mode = edge_input == "y"

    # Width
    width_input = input("\033[92m  ➤ ASCII width in chars (default auto): \033[0m").strip()
    width = int(width_input) if width_input.isdigit() else 120

    return ConversionConfig(
        width=width,
        char_ramp=char_ramp,
        invert=invert,
        color_enabled=color_enabled,
        edge_mode=edge_mode,
    )


def settings_help():
    """Display help information about settings."""
    print()
    print("\033[96m  ── ⚙️  Settings & Help ──\033[0m")
    print()
    print("\033[93m  Character Styles:\033[0m")
    print(f"\033[90m    Standard : {CharRamp.STANDARD.value}\033[0m")
    print(f"\033[90m    Minimal  : {CharRamp.MINIMAL.value}\033[0m")
    print(f"\033[90m    Blocks   : {CharRamp.BLOCKS.value}\033[0m")
    print(f"\033[90m    Dense    : {CharRamp.DENSE.value}\033[0m")
    print()
    print("\033[93m  Features:\033[0m")
    print("\033[90m    • Color mode     — Uses ANSI 256-color to tint ASCII chars\033[0m")
    print("\033[90m    • Invert         — Swaps dark/light character mapping\033[0m")
    print("\033[90m    • Edge detection — Shows only edges (Canny filter)\033[0m")
    print("\033[90m    • Width          — Controls output resolution (more chars = more detail)\033[0m")
    print()
    print("\033[93m  CLI Usage:\033[0m")
    print("\033[90m    python main.py video <path> [--width 120] [--style standard] [--color] [--invert] [--edges]\033[0m")
    print("\033[90m    python main.py webcam [--camera 0] [--no-mirror] [--color] [--style blocks]\033[0m")
    print()
    input("\033[92m  Press Enter to go back... \033[0m")
    print()


# ── CLI argument parsing ─────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="ASCII Video",
        description="Convert videos and webcam feeds into real-time ASCII art in your terminal.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                           Launch interactive menu
  python main.py video myvideo.mp4         Play a video as ASCII art
  python main.py video clip.mp4 --color    Play with color output
  python main.py webcam                    Start live webcam ASCII
  python main.py webcam --style blocks     Webcam with block characters
        """,
    )

    subparsers = parser.add_subparsers(dest="mode", help="Operating mode")

    # Video subcommand
    video_parser = subparsers.add_parser("video", help="Play a video file as ASCII art")
    video_parser.add_argument("path", type=str, help="Path to the video file")
    video_parser.add_argument("--width", type=int, default=0, help="ASCII width in characters (0 = auto)")
    video_parser.add_argument("--style", type=str, default="standard",
                              choices=["standard", "minimal", "blocks", "dense"],
                              help="Character style/ramp")
    video_parser.add_argument("--color", action="store_true", help="Enable ANSI color output")
    video_parser.add_argument("--invert", action="store_true", help="Invert brightness mapping")
    video_parser.add_argument("--edges", action="store_true", help="Enable edge-detection mode")
    video_parser.add_argument("--contrast", type=float, default=1.0, help="Contrast multiplier (0.5–2.0)")
    video_parser.add_argument("--brightness", type=float, default=0.0, help="Brightness offset (-50 to 50)")

    # Webcam subcommand
    webcam_parser = subparsers.add_parser("webcam", help="Start live webcam ASCII feed")
    webcam_parser.add_argument("--camera", type=int, default=0, help="Camera device index")
    webcam_parser.add_argument("--width", type=int, default=0, help="ASCII width in characters (0 = auto)")
    webcam_parser.add_argument("--style", type=str, default="standard",
                               choices=["standard", "minimal", "blocks", "dense"],
                               help="Character style/ramp")
    webcam_parser.add_argument("--color", action="store_true", help="Enable ANSI color output")
    webcam_parser.add_argument("--invert", action="store_true", help="Invert brightness mapping")
    webcam_parser.add_argument("--edges", action="store_true", help="Enable edge-detection mode")
    webcam_parser.add_argument("--no-mirror", action="store_true", help="Disable mirror/selfie mode")
    webcam_parser.add_argument("--contrast", type=float, default=1.0, help="Contrast multiplier (0.5–2.0)")
    webcam_parser.add_argument("--brightness", type=float, default=0.0, help="Brightness offset (-50 to 50)")

    return parser


def style_to_ramp(style: str) -> CharRamp:
    """Convert CLI style string to CharRamp enum."""
    mapping = {
        "standard": CharRamp.STANDARD,
        "minimal": CharRamp.MINIMAL,
        "blocks": CharRamp.BLOCKS,
        "dense": CharRamp.DENSE,
    }
    return mapping.get(style, CharRamp.STANDARD)


# ── Main entry point ─────────────────────────────────────────────────

def main():
    # If no arguments given, launch interactive menu
    if len(sys.argv) == 1:
        interactive_menu()
        return

    parser = build_parser()
    args = parser.parse_args()

    if args.mode == "video":
        config = ConversionConfig(
            width=args.width if args.width > 0 else 120,
            char_ramp=style_to_ramp(args.style),
            invert=args.invert,
            color_enabled=args.color,
            edge_mode=args.edges,
            contrast=args.contrast,
            brightness=args.brightness,
        )
        player = VideoPlayer(args.path, config)

        # Show info
        print_banner()
        info = player.get_info()
        print(f"\033[90m  📄 {os.path.basename(args.path)}")
        print(f"     Resolution: {info['width']}×{info['height']}")
        print(f"     Duration:   {info['duration_sec']}s ({info['frame_count']} frames @ {info['fps']:.1f} FPS)\033[0m")
        print(f"\n\033[93m  Starting playback in 2 seconds...\033[0m")
        time.sleep(2)

        player.play(auto_width=(args.width == 0))

    elif args.mode == "webcam":
        config = ConversionConfig(
            width=args.width if args.width > 0 else 120,
            char_ramp=style_to_ramp(args.style),
            invert=args.invert,
            color_enabled=args.color,
            edge_mode=args.edges,
            contrast=args.contrast,
            brightness=args.brightness,
        )
        print_banner()
        webcam = WebcamASCII(args.camera, config)
        webcam.start(auto_width=(args.width == 0), mirror=not args.no_mirror)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
