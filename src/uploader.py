# uploader.py
"""
Cloudinary uploading module for posting generated videos to a secure CDN.
"""

import os
import cloudinary
import cloudinary.uploader
import cloudinary.api

def upload_to_cloudinary(video_path):
    """
    Uploads a generated video to Cloudinary using chunked upload (large),
    and returns a secure public streaming HTTPS URL.
    """
    print("[*] Extracting Cloudinary API credentials...")
    cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME")
    api_key = os.getenv("CLOUDINARY_API_KEY")
    api_secret = os.getenv("CLOUDINARY_API_SECRET")
    
    if not all([cloud_name, api_key, api_secret]):
        raise ValueError(
            "Cloudinary credentials missing in .env. "
            "Configure CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, and CLOUDINARY_API_SECRET."
        )
        
    cloudinary.config(
        cloud_name=cloud_name,
        api_key=api_key,
        api_secret=api_secret,
        secure=True
    )
    
    filename = os.path.basename(video_path)
    print(f"[*] Starting upload of {filename} to Cloudinary...")
    try:
        # Standard upload is extremely reliable and supports files up to 100MB natively
        response = cloudinary.uploader.upload(
            video_path,
            resource_type="video",
            folder="quiz_the_code_reels"
        )
        
        secure_url = response.get("secure_url")
        if not secure_url:
            raise KeyError("Upload succeeded but secure_url is missing from Cloudinary response.")
            
        print("[+] Upload completed successfully!")
        print(f"[+] Streaming Video URL: {secure_url}")
        
        # Rolling FIFO cache rotation logic: Keep at most the 5 most recent videos in Cloudinary
        try:
            print("[*] Performing rolling FIFO database cleanup checks in Cloudinary...")
            res_list = cloudinary.api.resources(
                resource_type="video",
                type="upload",
                prefix="quiz_the_code_reels/",
                max_results=100
            )
            resources = res_list.get("resources", [])
            print(f"[*] Found {len(resources)} total videos in your Cloudinary repository.")
            
            if len(resources) > 5:
                # Sort resources by creation date in ascending order (oldest first)
                resources.sort(key=lambda r: r.get("created_at", ""))
                
                # Delete older videos until only 5 remain
                excess_count = len(resources) - 5
                print(f"[!] Target limit (5) exceeded! Deleting {excess_count} oldest video(s)...")
                for i in range(excess_count):
                    old_video = resources[i]
                    pub_id = old_video.get("public_id")
                    print(f"[*] Deleting oldest video: '{pub_id}' (Created at: {old_video.get('created_at')})...")
                    cloudinary.uploader.destroy(pub_id, resource_type="video")
                    print(f"[+] Deleted successfully!")
            else:
                print("[*] Cloudinary count is within safe bounds (<= 5). No deletion required.")
        except Exception as api_err:
            print(f"[!] Warning: Cloudinary rolling cleanup check encountered an error: {api_err}. Skipping cleanup.")
            
        return secure_url
        
    except Exception as e:
        print(f"[-] Cloudinary uploading encountered an error: {e}")
        raise
