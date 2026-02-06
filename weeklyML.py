# weekly_ml.py
"""
Offline, "pre-trained" weekly schedule generator.
This module creates a balanced study schedule based on user settings and a list of subjects.
It is designed to work offline without external dependencies.
"""
from datetime import datetime, timedelta

def generate_schedule(settings, subjects):
    """
    Generates a weekly study schedule.

    Args:
        settings (dict): User preferences including:
            - daily_hours (float): Max hours to study per day.
            - start_time (str): Preferred study start time (e.g., "09:00").
            - study_days (list): List of days to study (e.g., ["Mon", "Tue"]).
        subjects (list): A list of dictionaries, where each is a subject:
            - name (str): The name of the subject/topic.
            - hours (float): Total hours needed for the subject.
            - difficulty (str): "Easy", "Medium", or "Hard".

    Returns:
        dict: A dictionary representing the weekly schedule, or None if impossible.
    """
    # Initialize the schedule dictionary for the chosen study days
    schedule = {day: [] for day in settings.get("study_days", [])}
    if not schedule:
        return {} # No study days selected

    # Create a mutable list of subjects with remaining hours
    subjects_to_schedule = [dict(s, remaining_hours=s.get("hours", 0)) for s in subjects]
    
    # Sort subjects to prioritize harder ones first, then longer ones
    subjects_to_schedule.sort(key=lambda x: ({"Hard": 0, "Medium": 1, "Easy": 2}[x.get("difficulty", "Medium")], -x.get("remaining_hours", 0)))

    max_daily_hours = settings.get("daily_hours", 8)
    start_time_str = settings.get("start_time", "09:00")
    
    # Iterate through each available study day
    for day in schedule.keys():
        hours_scheduled_today = 0
        
        # Set the starting time for the day
        try:
            current_time = datetime.strptime(start_time_str, "%H:%M")
        except ValueError:
            current_time = datetime.strptime("09:00", "%H:%M")

        # Keep scheduling sessions until the day is full or all subjects are done
        while hours_scheduled_today < max_daily_hours:
            # Find the next subject that still needs study time
            subject_to_schedule = next((s for s in subjects_to_schedule if s["remaining_hours"] > 0), None)

            if not subject_to_schedule:
                break # All subjects have been scheduled

            # Determine session duration: max 2 hours, but not exceeding daily limit or remaining hours
            duration = min(
                subject_to_schedule["remaining_hours"],
                2, # Max session length in hours
                max_daily_hours - hours_scheduled_today
            )
            
            if duration <= 0.25: # Don't schedule tiny blocks
                break

            # Calculate session start and end times
            start_session_time = current_time
            end_session_time = start_session_time + timedelta(minutes=duration * 60)
            
            # Add session to the schedule
            schedule[day].append({
                "subject": subject_to_schedule["name"],
                "time": f"{start_session_time.strftime('%H:%M')} - {end_session_time.strftime('%H:%M')}",
                "duration": round(duration, 2),
                "difficulty": subject_to_schedule["difficulty"]
            })

            # Update state
            hours_scheduled_today += duration
            subject_to_schedule["remaining_hours"] -= duration
            current_time = end_session_time # Next session starts after this one ends

    total_remaining_hours = sum(s["remaining_hours"] for s in subjects_to_schedule)
    if total_remaining_hours > 0.1: # Check if all subjects were scheduled (with a small tolerance)
        print(f"Warning: Could not schedule all hours. {total_remaining_hours:.2f} hours remaining.")


    return {"schedule": schedule}
