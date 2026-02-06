# weekly_ml.py
"""
Offline, "pre-trained" scheduler for the Weekly Planner.

This module contains the logic to generate a balanced weekly study schedule
based on user settings and a list of subjects with their total hours and difficulty.
It operates entirely offline, with no external dependencies for its core logic.
"""

import random
from typing import Dict, Any, List
from collections import defaultdict

def generate_schedule(settings: Dict[str, Any], subjects: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Generates a weekly study schedule using a more robust algorithm.
    """
    # --- 1. Sanitize and Prepare Inputs ---
    try:
        max_daily_hours = float(settings.get("daily_study_hours", 8))
        start_hour, start_minute = map(int, settings.get("start_time", "09:00").split(':'))
        # Ensure study_days are correctly identified
        study_days = [day for day, is_active in settings.get("study_days", {}).items() if is_active]
    except (ValueError, TypeError):
        max_daily_hours, start_hour, start_minute = 8, 9, 0
        study_days = ["mon", "tue", "wed", "thu", "fri"]

    if not study_days:
        return {"error": "No study days selected."}

    # --- 2. Create Prioritized 1-Hour Study Blocks ---
    difficulty_order = {"Hard": 3, "Medium": 2, "Easy": 1}
    study_blocks = []
    for subject in subjects:
        try:
            # Ensure hours are integers for block creation
            hours = int(round(float(subject.get("total_hours", 1))))
            for _ in range(hours):
                study_blocks.append({
                    "subject": subject.get("subject_name", "Unnamed"),
                    "difficulty": subject.get("difficulty", "Medium"),
                    "priority": difficulty_order.get(subject.get("difficulty", "Medium"), 2)
                })
        except (ValueError, TypeError):
            continue
            
    # Sort by priority, then shuffle within the same priority to vary schedule
    study_blocks.sort(key=lambda x: x['priority'], reverse=True)

    # --- 3. Distribute Blocks into the Schedule ---
    schedule = {day: [] for day in ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]}
    daily_hours_spent = defaultdict(float)
    day_cycle = [day.lower() for day in study_days] # e.g., ['mon', 'tue', ...]
    day_idx = 0

    def format_time(h, m):
        return f"{int(h):02d}:{int(m):02d}"

    for block in study_blocks:
        placed = False
        for _ in range(len(day_cycle)):
            current_day = day_cycle[day_idx]
            if daily_hours_spent[current_day] < max_daily_hours:
                h = start_hour + daily_hours_spent[current_day]
                block['start_time'] = format_time(h, start_minute)
                block['end_time'] = format_time(h + 1, start_minute)
                
                schedule[current_day].append(block)
                daily_hours_spent[current_day] += 1
                placed = True
                break
            day_idx = (day_idx + 1) % len(day_cycle)
        
        if not placed:
            print(f"Warning: Could not place a block for {block['subject']}. Total hours may exceed capacity.")
        
        # Move to the next available day for the next block to ensure distribution
        day_idx = (day_idx + 1) % len(day_cycle)


    # --- 4. Consolidate Consecutive Blocks (FIXED LOGIC) ---
    final_schedule = {}
    for day, sessions in schedule.items():
        if not sessions:
            final_schedule[day] = []
            continue

        # Defensive sort, in case distribution logic changes
        sessions.sort(key=lambda x: x['start_time'])

        consolidated = []
        if sessions:
            current_session = sessions[0].copy()

            for next_session in sessions[1:]:
                # Check if sessions are consecutive and for the same subject
                if (next_session['subject'] == current_session['subject'] and
                    next_session['difficulty'] == current_session['difficulty'] and
                    next_session['start_time'] == current_session['end_time']):
                    # Merge by extending the end time
                    current_session['end_time'] = next_session['end_time']
                else:
                    # Finalize and append the previous session
                    start_h = int(current_session['start_time'].split(':')[0])
                    end_h = int(current_session['end_time'].split(':')[0])
                    current_session['duration_hs'] = f"{float(end_h - start_h)}h"
                    consolidated.append(current_session)
                    # Start a new session
                    current_session = next_session.copy()
            
            # Append the very last session after the loop
            start_h = int(current_session['start_time'].split(':')[0])
            end_h = int(current_session['end_time'].split(':')[0])
            current_session['duration_hs'] = f"{float(end_h - start_h)}h"
            consolidated.append(current_session)

        final_schedule[day] = consolidated

    return final_schedule

