#!/usr/bin/env python3
"""
QuizTheCodeBot - Unified Execution Entrypoint.
Routes all main automation actions and auxiliary utility commands.
"""

import os
import sys
from dotenv import load_dotenv

# Add src folder to search path so internal imports resolve natively
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

def main():
    load_dotenv()
    
    if len(sys.argv) < 2:
        print("Usage: python main.py [generate | post | test-upload | test-instagram | crop-songs | schedule]")
        sys.exit(1)
        
    cmd = sys.argv[1].lower()
    
    if cmd == "crop-songs":
        print("=== STAGE 1: Running Audio Cropping Utility ===")
        try:
            from crop_songs import crop_audio_tracks
            crop_audio_tracks()
        except Exception as e:
            print(f"[-] Error executing crop_songs utility: {e}")
            sys.exit(1)
    elif cmd == "schedule":
        try:
            from schedule_posts import run_scheduler
            run_scheduler()
        except Exception as e:
            print(f"[-] Error executing scheduler daemon: {e}")
            sys.exit(1)
    else:
        # Route standard bot operations to src/bot.py
        try:
            from bot import main as run_bot
            run_bot()
        except Exception as e:
            print(f"[-] Critical execution error in bot runner: {e}")
            sys.exit(1)

if __name__ == "__main__":
    main()
