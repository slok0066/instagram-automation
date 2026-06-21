#!/usr/bin/env python3
"""
QuizTheCodeBot - Instagram Coding Quiz Video Automation Bot
Lightweight entry point and router for QuizTheCodeBot operations.
"""

import os
import sys
from dotenv import load_dotenv

from utils import check_and_download_font
from questions import get_next_question
from video import generate_video
from uploader import upload_to_cloudinary
from instagram import post_to_instagram, test_instagram_connection, test_upload, post_comment_on_reel

def main():
    # Load settings from .env file
    load_dotenv()
    
    # Scaffold directories if they do not exist
    os.makedirs("assets", exist_ok=True)
    os.makedirs("assets/fonts", exist_ok=True)
    os.makedirs("assets/songs", exist_ok=True)
    os.makedirs("assets/backgrounds", exist_ok=True)
    os.makedirs("assets/hooks", exist_ok=True)
    os.makedirs("output", exist_ok=True)
    
    # Ensure premium font assets are installed
    check_and_download_font()
    
    if len(sys.argv) < 2:
        print("Usage: python main.py [generate | post | test-upload | test-instagram]")
        sys.exit(1)
        
    cmd = sys.argv[1].lower()
    
    if cmd == "generate":
        print("=== STAGE 1: Picking Question ===")
        question = get_next_question()
        print(f"[+] Question Picked (ID: {question['id']}, Language: {question['language']})")
        print(f"[+] Correct Answer (Logs only): {question['answer']}")
        
        print("\n=== STAGE 2: Generating Reel Video ===")
        video_name = f"{question['id']}.mp4"
        output_video_path = os.path.join("output", video_name)
        generate_video(question, output_video_path)
        print(f"\n[+] Local Reel generated successfully at: {output_video_path}")
        
    elif cmd == "post":
        print("=== STAGE 1: Picking Question ===")
        question = get_next_question()
        print(f"[+] Question Picked (ID: {question['id']}, Language: {question['language']})")
        print(f"[+] Correct Answer (Logs only): {question['answer']}")
        
        print("\n=== STAGE 2: Generating Reel Video ===")
        video_name = f"{question['id']}.mp4"
        output_video_path = os.path.join("output", video_name)
        generate_video(question, output_video_path)
        print(f"[+] Local Reel generated at: {output_video_path}")
        
        print("\n=== STAGE 3: Uploading to Cloudinary ===")
        cloudinary_url = upload_to_cloudinary(output_video_path)
        
        print("\n=== STAGE 4: Direct Publishing to Instagram ===")
        post_id = post_to_instagram(cloudinary_url)
        
        # Post the automated correct answer comment on the published Reel
        correct_answer = question.get("answer", "")
        comment_text = (
            f"💡 The correct answer is: {correct_answer}!\n\n"
            "Did you guess it right? Let us know in the comments below! 👇"
        )
        print("\n=== STAGE 5: Posting Automated Correct Answer Comment ===")
        post_comment_on_reel(post_id, comment_text)
        
        print("\n[+] Direct post workflow completed successfully!")
        
    elif cmd == "test-upload":
        print("=== STAGE 1: Cloudinary Test Upload ===")
        test_upload()
        
    elif cmd == "test-instagram":
        print("=== STAGE 1: Instagram API Token Test ===")
        success = test_instagram_connection()
        if success:
            print("[+] Test completed successfully!")
        else:
            print("[-] Test failed. Please check credentials or permissions.")
            sys.exit(1)
            
    else:
        print(f"[-] Unknown command: '{cmd}'")
        print("Available commands: generate, post, test-upload, test-instagram")
        sys.exit(1)

if __name__ == "__main__":
    main()
