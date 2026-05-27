# instagram.py
"""
Instagram Graph API Reels publishing pipeline.
Handles creating media containers, polling status until compilation, and publishing.
"""

import os
import time
import json
import glob
import requests
from datetime import datetime

import config
from utils import mask_token
from questions import get_next_question
from video import generate_video
from uploader import upload_to_cloudinary

def post_to_instagram(video_url):
    """
    Submits the Cloudinary video URL to the Instagram Reels API,
    polls the processing container status, and publishes it directly to Reels.
    """
    print("[*] Initializing Instagram Graph API publishing...")
    user_id = os.getenv("INSTAGRAM_USER_ID")
    access_token = os.getenv("INSTAGRAM_ACCESS_TOKEN")
    
    if not all([user_id, access_token]):
        raise ValueError(
            "Instagram credentials missing in .env. "
            "Please configure INSTAGRAM_USER_ID and INSTAGRAM_ACCESS_TOKEN."
        )
        
    print(f"[*] Target Instagram User ID: {user_id}")
    print(f"[*] Access Token (masked): {mask_token(access_token)}")
    
    # -------------------------------------------------------------
    # Step 1: Create Video Container
    # -------------------------------------------------------------
    print("[*] Initializing Reels media container upload...")
    container_url = f"https://graph.instagram.com/v21.0/{user_id}/media"
    container_payload = {
        "media_type": "REELS",
        "video_url": video_url,
        "caption": config.FIXED_CAPTION,
        "access_token": access_token
    }
    
    try:
        response = requests.post(container_url, data=container_payload)
        res_json = response.json()
    except Exception as e:
        raise RuntimeError(f"Failed connection to Instagram Graph API: {e}")
        
    if response.status_code != 200:
        print("[-] Instagram Media Container Creation Failed!")
        print(f"[-] HTTP Status: {response.status_code}")
        print("[-] Exact API Error Response JSON:")
        print(json.dumps(res_json, indent=2))
        raise RuntimeError("Instagram container creation failed.")
        
    creation_id = res_json.get("id")
    if not creation_id:
        print("[-] Response did not return creation container ID:", json.dumps(res_json, indent=2))
        raise RuntimeError("Instagram container API response is invalid.")
        
    print(f"[+] Container successfully initialized! Container ID: {creation_id}")
    
    # -------------------------------------------------------------
    # Step 2: Poll Container Processing Status
    # -------------------------------------------------------------
    print("[*] Polling Reels container processing status until FINISHED...")
    status_url = f"https://graph.instagram.com/v21.0/{creation_id}"
    status_params = {
        "fields": "status_code",
        "access_token": access_token
    }
    
    max_polls = 24  # 24 * 5 seconds = 2 minutes timeout limit
    poll_interval = 5
    is_finished = False
    
    for attempt in range(1, max_polls + 1):
        print(f"[*] Check #{attempt}: Querying state...")
        try:
            status_res = requests.get(status_url, params=status_params)
            status_json = status_res.json()
        except Exception as e:
            print(f"[!] Warning: Connection glitch on poll attempt {attempt}: {e}. Retrying.")
            time.sleep(poll_interval)
            continue
            
        if status_res.status_code != 200:
            print(f"[-] Status check failed (HTTP {status_res.status_code}):", json.dumps(status_json, indent=2))
            time.sleep(poll_interval)
            continue
            
        status_code = status_json.get("status_code")
        print(f"[*] Current API status_code: {status_code}")
        
        if status_code == "FINISHED":
            print("[+] Instagram has fully processed the video Reel!")
            is_finished = True
            break
        elif status_code == "ERROR":
            print("[-] Instagram video container processing encountered an ERROR!")
            print("[-] Exact API Error Details:")
            print(json.dumps(status_json, indent=2))
            raise RuntimeError("Instagram Reels container processing failed.")
        else:
            # Code is likely 'IN_PROGRESS', wait and try again
            time.sleep(poll_interval)
            
    if not is_finished:
        raise TimeoutError("Timed out waiting for Instagram to compile the video container (exceeded 2 minutes).")
        
    # -------------------------------------------------------------
    # Step 3: Publish the Completed Reels Container
    # -------------------------------------------------------------
    print("[*] Triggering direct Reels publish post...")
    publish_url = f"https://graph.instagram.com/v21.0/{user_id}/media_publish"
    publish_payload = {
        "creation_id": creation_id,
        "access_token": access_token
    }
    
    try:
        pub_response = requests.post(publish_url, data=publish_payload)
        pub_json = pub_response.json()
    except Exception as e:
        raise RuntimeError(f"Failed Direct Reels Publish request: {e}")
        
    if pub_response.status_code != 200:
        print("[-] Direct Reel Media Publishing Failed!")
        print(f"[-] HTTP Status: {pub_response.status_code}")
        print("[-] Exact API Error Response JSON:")
        print(json.dumps(pub_json, indent=2))
        raise RuntimeError("Instagram Direct Reels publishing failed.")
        
    post_id = pub_json.get("id")
    print("[+] DIRECT POST COMPLETED SUCCESSFULLY!")
    print(f"[+] Instagram Post Media ID: {post_id}")
    return post_id


def post_comment_on_reel(post_id, text):
    """
    Submits a comment text to the published Instagram Reel post_id.
    """
    print("[*] Initializing automated Instagram comment...")
    access_token = os.getenv("INSTAGRAM_ACCESS_TOKEN")
    if not access_token:
        print("[!] Warning: Access token missing. Skipping automated comment.")
        return False
        
    comment_url = f"https://graph.instagram.com/v21.0/{post_id}/comments"
    payload = {
        "message": text,
        "access_token": access_token
    }
    
    try:
        response = requests.post(comment_url, data=payload)
        res_json = response.json()
        if response.status_code == 200:
            comment_id = res_json.get("id")
            print(f"[+] Comment posted successfully! Comment ID: {comment_id}")
            return True
        else:
            print(f"[!] Warning: Instagram comment creation failed (HTTP {response.status_code}):")
            print(json.dumps(res_json, indent=2))
            return False
    except Exception as e:
        print(f"[!] Warning: Automated comment creation encountered a connection glitch: {e}")
        return False


def test_instagram_connection():
    """
    Performs a simple validation call to the Instagram Graph API to confirm
    credentials and access rights.
    """
    print("[*] Testing Instagram API Connection...")
    user_id = os.getenv("INSTAGRAM_USER_ID")
    access_token = os.getenv("INSTAGRAM_ACCESS_TOKEN")
    
    if not all([user_id, access_token]):
        print("[-] Instagram credentials missing in .env.")
        print("[-] Please configure INSTAGRAM_USER_ID and INSTAGRAM_ACCESS_TOKEN.")
        return False
        
    print(f"[*] Target Instagram User ID: {user_id}")
    print(f"[*] Access Token (masked): {mask_token(access_token)}")
    
    url = f"https://graph.instagram.com/v21.0/{user_id}"
    params = {
        "fields": "id,username",
        "access_token": access_token
    }
    
    try:
        response = requests.get(url, params=params)
        res_json = response.json()
        
        if response.status_code == 200:
            print("[+] Connection successful!")
            print(f"[+] Linked Reels Account ID: {res_json.get('id')}")
            print(f"[+] Connected Username: @{res_json.get('username')}")
            return True
        else:
            print("[-] Instagram API Connection Test Failed!")
            print(f"[-] HTTP Status: {response.status_code}")
            print("[-] API Response:")
            print(json.dumps(res_json, indent=2))
            return False
            
    except Exception as e:
        print(f"[-] Error connecting to Instagram API endpoint: {e}")
        return False


def test_upload():
    """
    Identifies the latest video created inside the output/ folder,
    and uploads it to Cloudinary only.
    """
    print("[*] Identifying the latest generated MP4 reel inside output/...")
    videos = glob.glob(os.path.join("output", "*.mp4"))
    if not videos:
        print("[!] No pre-existing reels found inside output/.")
        print("[*] Generating a fresh video to test the uploading mechanism...")
        question = get_next_question()
        video_name = f"{question.get('id', 1)}.mp4"
        video_path = os.path.join("output", video_name)
        generate_video(question, video_path)
    else:
        # Select the latest file based on system modification time
        videos.sort(key=os.path.getmtime)
        video_path = videos[-1]
        print(f"[+] Selected latest video for upload: '{video_path}'")
        
    upload_to_cloudinary(video_path)
