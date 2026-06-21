# media.py
"""
Media helpers for selecting random audio soundtracks and background videos.
"""

import os
import glob
import random

def get_random_song():
    """Returns a path to a random MP3 file in assets/songs/ directory."""
    songs_dir = os.path.join("assets", "songs")
    songs = glob.glob(os.path.join(songs_dir, "*.mp3"))
    if not songs:
        return None
    return random.choice(songs)


def get_random_background_video():
    """Returns a path to a random MP4 file in assets/backgrounds/ directory, falling back to assets/background.mp4."""
    bg_dir = os.path.join("assets", "backgrounds")
    videos = glob.glob(os.path.join(bg_dir, "*.mp4"))
    if not videos:
        # Fallback to single background.mp4 if it exists
        single_bg = os.path.join("assets", "background.mp4")
        if os.path.exists(single_bg):
            return single_bg
        return None
    return random.choice(videos)


def get_random_hook_video():
    """Returns a path to a random MP4 file in assets/hooks/ directory, or None if none exist."""
    hooks_dir = os.path.join("assets", "hooks")
    if not os.path.exists(hooks_dir):
        return None
    videos = glob.glob(os.path.join(hooks_dir, "*.mp4"))
    if not videos:
        return None
    return random.choice(videos)

