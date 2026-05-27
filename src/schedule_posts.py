# schedule_posts.py
"""
Automated scheduling daemon for QuizTheCodeBot.
Runs continuously, sleeping precisely until prime Instagram activity times, 
and triggers the automated Reel publishing pipeline.
"""

import os
import sys
import time
from datetime import datetime, timedelta

def run_scheduler():
    # Prime active slots (24-hour format):
    # - 09:00 AM (Morning commute / early rush)
    # - 01:00 PM (Lunch scrolling)
    # - 08:00 PM (Leisure scrolling / prime evening traffic)
    slots = [(9, 0), (13, 0), (20, 0)]
    
    print("=" * 50)
    print("   QuizTheCodeBot AUTONOMOUS DAILY SCHEDULER   ")
    print("=" * 50)
    print("Scheduling Reel uploads 3 times daily at peak active hours:")
    print("  - Slot 1: 09:00 AM (Morning rush)")
    print("  - Slot 2: 01:00 PM (Lunch break)")
    print("  - Slot 3: 08:00 PM (Prime evening scrolls)")
    print("Press Ctrl+C to terminate the daemon safely.\n")
    
    while True:
        now = datetime.now()
        upcoming_times = []
        
        for hour, minute in slots:
            target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if target <= now:
                # Target has already passed today, schedule for tomorrow
                target += timedelta(days=1)
            upcoming_times.append((target, hour, minute))
            
        # Sort to find the nearest upcoming target slot
        upcoming_times.sort(key=lambda t: t[0])
        next_target, target_hour, target_min = upcoming_times[0]
        
        sleep_seconds = (next_target - now).total_seconds()
        next_target_str = next_target.strftime("%Y-%m-%d %I:%M:%S %p")
        
        print(f"[*] Next scheduled publish: {next_target_str}")
        print(f"[*] Sleeping for {round(sleep_seconds / 3600, 2)} hours...")
        
        # Sleep until the exact target time slot
        time.sleep(sleep_seconds)
        
        print(f"\n[!] Scheduled target time reached! Triggering direct Reel publish...")
        try:
            # Dynamically import the bot controller to evaluate fresh database states
            from bot import main as run_bot
            
            # Mock CLI sys.argv parameters to execute standard 'post' cleanly
            sys.argv = ["main.py", "post"]
            run_bot()
            print("[+] Scheduled Reel published successfully!\n")
        except Exception as e:
            print(f"[!] Error during scheduled execution: {e}\n")
            # Wait a short cooling interval to prevent spam loops if an API outage occurs
            time.sleep(60)
