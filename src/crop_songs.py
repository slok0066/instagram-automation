#!/usr/bin/env python3
"""
QuizTheCodeBot - Song Cropping Utility
Prepares full-length tracks by cropping them into high-energy 6.5-second segments for Instagram Reels.
Keeps original files safe in 'assets/raw_songs/' and exports segments to 'assets/songs/'.
"""

import os
import glob
import shutil
from moviepy import AudioFileClip

def crop_audio_tracks():
    raw_dir = os.path.join("assets", "raw_songs")
    songs_dir = os.path.join("assets", "songs")
    
    os.makedirs(raw_dir, exist_ok=True)
    os.makedirs(songs_dir, exist_ok=True)
    
    # 1. Proactive Migration Helper:
    # If the user put raw songs in assets/songs/ directly, move them to assets/raw_songs/
    existing_songs = glob.glob(os.path.join(songs_dir, "*.mp3"))
    raw_songs = glob.glob(os.path.join(raw_dir, "*.mp3"))
    
    if existing_songs and not raw_songs:
        print("[*] Detected raw tracks in assets/songs/. Moving them to assets/raw_songs/ first...")
        for song_path in existing_songs:
            filename = os.path.basename(song_path)
            dest_path = os.path.join(raw_dir, filename)
            try:
                shutil.move(song_path, dest_path)
                print(f"[+] Moved: {filename} -> assets/raw_songs/")
            except Exception as e:
                print(f"[!] Warning: Could not move {filename}: {e}")
        # Refresh lists
        raw_songs = glob.glob(os.path.join(raw_dir, "*.mp3"))
        
    if not raw_songs:
        print("[-] No raw songs found in assets/raw_songs/ or assets/songs/.")
        print("[-] Please place full-length .mp3 tracks inside assets/raw_songs/ and run this script again!")
        return
        
    print(f"[*] Found {len(raw_songs)} raw tracks to process.")
    
    for track_path in raw_songs:
        filename = os.path.basename(track_path)
        dest_path = os.path.join(songs_dir, filename)
        
        print(f"\n[*] Processing track: {filename}...")
        try:
            audio = AudioFileClip(track_path)
            duration = audio.duration
            print(f"[*] Original duration: {round(duration, 2)} seconds")
            
            # Crop a high-quality 6.5-second segment
            crop_duration = 6.5
            
            if duration <= crop_duration:
                print(f"[+] Track is already shorter than 6.5s. Copying it raw...")
                audio.close()
                shutil.copy(track_path, dest_path)
                continue
                
            # Climax Detection Helper:
            # Phonk & Lofi drops are usually located in the active middle of the track.
            # We crop a 6.5-second segment starting from 30 seconds (or center if the track is short).
            if duration >= 45.0:
                # Phonk drop is highly active around the 30-second mark
                start_time = 30.0
            else:
                # Center-cut for shorter tracks
                start_time = round((duration - crop_duration) / 2, 2)
                
            end_time = start_time + crop_duration
            print(f"[*] Cropping segment from {start_time}s to {end_time}s...")
            
            if hasattr(audio, 'subclipped'):
                cropped = audio.subclipped(start_time, end_time)
            else:
                cropped = audio.subclip(start_time, end_time)
                
            print(f"[*] Writing cropped MP3 segment to assets/songs/...")
            # Save using standard audio writing options
            cropped.write_audiofile(
                dest_path,
                fps=44100,
                nbytes=2,
                buffersize=2000,
                logger=None  # suppresses moviepy verbose console logs
            )
            
            # Close clips to release file system lock tags on Windows
            cropped.close()
            audio.close()
            print(f"[+] Success! Saved: assets/songs/{filename}")
            
        except Exception as e:
            print(f"[-] Failed to crop '{filename}' due to error: {e}")
            
    print("\n[+] All tracks have been processed successfully!")

if __name__ == "__main__":
    crop_audio_tracks()
