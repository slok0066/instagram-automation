# questions.py
"""
Question manager module that queries unique programming questions sequentially and tracks history.
"""

import os
import json

def get_next_question():
    """
    Reads questions.json, handles unused questions tracking in used_questions.json,
    and returns the next sequential unused question. Resets state when all questions have been used.
    """
    questions_file = "questions.json"
    used_file = "used_questions.json"
    
    if not os.path.exists(questions_file):
        raise FileNotFoundError(f"Critical Error: Questions database not found at {questions_file}")
        
    try:
        with open(questions_file, "r") as f:
            questions = json.load(f)
    except Exception as e:
        raise RuntimeError(f"Error reading questions.json: {e}")
        
    if not questions:
        raise ValueError("Questions list is empty in questions.json")
        
    used_ids = []
    if os.path.exists(used_file):
        try:
            with open(used_file, "r") as f:
                used_ids = json.load(f)
        except Exception as e:
            print(f"[!] Warning: Error reading used_questions.json: {e}. Starting fresh.")
            used_ids = []
            
    # Filter for unused questions
    unused_questions = [q for q in questions if q.get("id") not in used_ids]
    
    if not unused_questions:
        print("[*] All questions have been used! Resetting used questions database list.")
        used_ids = []
        unused_questions = questions
        
    # Select the next question in order (minimum ID)
    unused_questions.sort(key=lambda q: q.get("id", 0))
    selected_question = unused_questions[0]
    
    # Save the selected ID to the used list
    used_ids.append(selected_question.get("id"))
    try:
        with open(used_file, "w") as f:
            json.dump(used_ids, f, indent=2)
    except Exception as e:
        print(f"[!] Warning: Could not save used question state to {used_file}: {e}")
        
    return selected_question
