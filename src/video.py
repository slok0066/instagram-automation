# video.py
"""
Video rendering module using MoviePy to assemble timelines and generate high-fidelity MP4 Reels.
"""

import os
import random
from moviepy import ImageClip, AudioFileClip, VideoFileClip, CompositeVideoClip

from media import get_random_song, get_random_background_video;
from graphics import generate_graphics

def generate_video(question_data, output_video_path):
    """
    Creates a 6 to 7 second vertical video by overlaying Pillow-generated transparent card
    graphics on top of a dynamic moving background video or fallback image,
    and mixing a random loopable MP3 lofi beat from assets/songs/.
    """
    os.makedirs("output", exist_ok=True)
    temp_img_path = os.path.join("output", "temp_frame.png")
    
    bg_video_path = get_random_background_video()
    has_video_bg = bg_video_path is not None
    
    if has_video_bg:
        print(f"[*] Background video detected: '{os.path.basename(bg_video_path)}'! Rendering transparent overlays...")
    else:
        print("[*] Rendering static background image...")
        
    generate_graphics(question_data, temp_img_path, transparent_bg=has_video_bg)
    
    # Select random float duration between 6.0 and 7.0 seconds
    duration = round(random.uniform(6.0, 7.0), 2)
    print(f"[*] Chosen video duration: {duration} seconds")
    
    print("[*] Compositing video timeline using MoviePy...")
    bg_clip = None
    overlay_clip = None
    try:
        if has_video_bg:
            print("[*] Processing background video clip...")
            bg_clip = VideoFileClip(bg_video_path)
            
            # Mute original video track so the background music plays cleanly
            bg_clip = bg_clip.without_audio()
            
            # Resize video to 1080x1920
            if hasattr(bg_clip, 'resized'):
                bg_clip = bg_clip.resized((1080, 1920))
            else:
                bg_clip = bg_clip.resize((1080, 1920))
                
            # Cut or loop video clip to match selected duration
            if bg_clip.duration < duration:
                print("[*] Background video is shorter than target duration. Looping video...")
                try:
                    from moviepy.video.fx import Loop
                    bg_clip = bg_clip.with_effects([Loop(duration=duration)])
                except Exception:
                    bg_clip = bg_clip.loop(duration=duration)
            else:
                max_start = max(0.0, bg_clip.duration - duration)
                start_time = round(random.uniform(0, max_start), 2) if max_start > 0 else 0.0
                print(f"[*] Cutting background video: segment from {start_time}s to {start_time + duration}s")
                if hasattr(bg_clip, 'subclipped'):
                    bg_clip = bg_clip.subclipped(start_time, start_time + duration)
                else:
                    bg_clip = bg_clip.subclip(start_time, start_time + duration)
            
            # Load transparent Pillow graphics frame
            if hasattr(ImageClip, 'with_duration'):
                overlay_clip = ImageClip(temp_img_path).with_duration(duration)
            else:
                overlay_clip = ImageClip(temp_img_path).set_duration(duration)
                
            if hasattr(overlay_clip, 'with_fps'):
                overlay_clip = overlay_clip.with_fps(24)
            else:
                overlay_clip = overlay_clip.set_fps(24)
                
            # Combine background video and overlay
            clip = CompositeVideoClip([bg_clip, overlay_clip])
            if hasattr(clip, 'with_duration'):
                clip = clip.with_duration(duration)
            else:
                clip = clip.set_duration(duration)
        else:
            # Fallback static image mode
            if hasattr(ImageClip, 'with_duration'):
                clip = ImageClip(temp_img_path).with_duration(duration)
            else:
                clip = ImageClip(temp_img_path).set_duration(duration)
                
            if hasattr(clip, 'with_fps'):
                clip = clip.with_fps(24)
            else:
                clip = clip.set_fps(24)
        
        # Retrieve and process background music
        song_path = get_random_song()
        audio_clip = None
        
        if song_path:
            print(f"[*] Selected background soundtrack: '{os.path.basename(song_path)}'")
            try:
                audio = AudioFileClip(song_path)
                
                # Loop song if shorter than video, else clip a random segment
                if audio.duration < duration:
                    print("[*] Song length is shorter than video. Setting to audio loop...")
                    try:
                        from moviepy.audio.fx import AudioLoop
                        audio_clip = audio.with_effects([AudioLoop(duration=duration)])
                    except ImportError:
                        from moviepy.video.fx.all import loop
                        audio_clip = audio.fx(loop, duration=duration)
                else:
                    max_start = max(0.0, audio.duration - duration)
                    start_time = round(random.uniform(0, max_start), 2) if max_start > 0 else 0.0
                    print(f"[*] Cutting sound block: start at {start_time}s to {start_time + duration}s")
                    if hasattr(audio, 'subclipped'):
                        audio_clip = audio.subclipped(start_time, start_time + duration)
                    else:
                        audio_clip = audio.subclip(start_time, start_time + duration)
                
                # Level volume to 35%
                try:
                    from moviepy.audio.fx import MultiplyVolume
                    audio_clip = audio_clip.with_effects([MultiplyVolume(0.35)])
                except ImportError:
                    if hasattr(audio_clip, 'volumex'):
                        audio_clip = audio_clip.volumex(0.35)
                    else:
                        audio_clip = audio_clip.multiply_volume(0.35)
                    
            except Exception as e:
                print(f"[!] Warning: Failed to process background music: {e}. Generating silent video instead.")
                audio_clip = None
        else:
            print("[!] assets/songs/ is empty or song missing. Creating silent video clip.")
            
        if audio_clip:
            if hasattr(clip, 'with_audio'):
                clip = clip.with_audio(audio_clip)
            else:
                clip = clip.set_audio(audio_clip)
            
        print(f"[*] Exporting final optimized MP4 to: {output_video_path}...")
        clip.write_videofile(
            output_video_path,
            fps=24,
            codec="libx264",
            audio_codec="aac" if audio_clip else None,
            temp_audiofile=os.path.join("output", "temp_audio.m4a") if audio_clip else None,
            remove_temp=True,
            logger=None  # Cleans up MoviePy verbose output logs
        )
        
        # Critical on Windows: Close clips to release file system lock tags
        clip.close()
        if bg_clip:
            bg_clip.close()
        if overlay_clip:
            overlay_clip.close()
        if audio_clip:
            audio_clip.close()
            
        print("[+] Video compiled successfully!")
        
    finally:
        # Clean up temporary PNG graphics frame
        if os.path.exists(temp_img_path):
            try:
                os.remove(temp_img_path)
            except Exception as e:
                print(f"[!] Warning: Could not clean up temp image file '{temp_img_path}': {e}")
