# ml.py
"""
Offline, ready-to-use 'pretrained' recommender for the Study Planner.

This module intentionally avoids any external training/data dependencies.
It supports a small, fixed set of subjects (Maths, Science, English, Social Studies)
and produces friendly, deterministic recommendations based on:
 - total planned study hours (hours),
 - difficulty (Easy/Medium/Hard),
 - days_remaining (integer >=1).

Usage:
    >>> from ml import recommend
    >>> recommend(subject="Maths", hours=6, difficulty="Medium", days_remaining=7)
    {
      "predicted_hours": 2.0,
      "recommendation_text": "Nice ...",
      "subject": "Maths",
      "difficulty": "Medium",
      "days_remaining": 7
    }
"""

from typing import Dict, Any
import math

SUPPORTED = {"maths": "Maths", "math": "Maths",
             "science": "Science",
             "english": "English",
             "social": "Social Studies", "social studies": "Social Studies", "socialstudies": "Social Studies"}

def _canonical_subject(name: str) -> str:
    if not name: return "General"
    s = name.strip().lower()
    for key in SUPPORTED:
        if key in s:
            return SUPPORTED[key]
    # fallback: capitalize first letter
    return name.strip().title()

def _difficulty_normalize(diff: str) -> str:
    if not diff: return "Medium"
    d = diff.strip().lower()
    if d.startswith("e"): return "Easy"
    if d.startswith("h"): return "Hard"
    return "Medium"

def recommend(subject: str, hours: float, difficulty: str, days_remaining: int) -> Dict[str, Any]:
    """
    Return a recommendation dict (works offline).
    - subject: string (prefer: Maths, Science, English, Social Studies)
    - hours: total planned study hours (float)
    - difficulty: 'Easy', 'Medium', 'Hard'
    - days_remaining: integer days until deadline
    """
    # sanitize inputs
    subj = _canonical_subject(subject)
    diff = _difficulty_normalize(difficulty)
    try:
        hours = float(hours)
    except Exception:
        hours = 1.0
    if hours <= 0:
        hours = 1.0
    try:
        days = max(1, int(days_remaining))
    except Exception:
        days = 7

    # Base per-day rate (simple)
    base_per_day = hours / days  # how many hours/day if evenly spread

    # Revision/effort bonus according to difficulty
    # Easy -> small or no bonus, Medium -> 1 extra hour/day buffer, Hard -> 2 extra hour buffer
    bonus_for_diff = {"Easy": 0.0, "Medium": 1.0, "Hard": 2.0}
    bonus = bonus_for_diff.get(diff, 1.0)

    # Compute daily recommendation and round to user-friendly steps (0.5h)
    raw_daily = base_per_day + bonus

    # If there's plenty of time, reduce the bonus (don't force unnecessary load)
    if days >= hours * 1.5:
        # plenty of time -> reduce bonus by half
        raw_daily = max(0.5, base_per_day + (bonus * 0.5))

    # Final rounding to nearest 0.5
    daily = round(raw_daily * 2) / 2.0

    # Minor clamps for plausibility
    if daily < 0.25:
        daily = 0.25
    if daily > 12:
        daily = 12.0

    # Friendly time-situation sentence
    if days >= hours * 1.5:
        timeSituation = "Great — you have plenty of time to cover the material comfortably."
    elif days >= hours:
        timeSituation = "Good — you have enough time if you stay consistent."
    elif days >= math.ceil(hours / 2):
        timeSituation = "Tight — you'll need focused sessions and fewer distractions."
    else:
        timeSituation = "Very tight — prioritize the most important topics and increase daily time."

    # Compose recommendation text (human-friendly)
    rec_text = (
        f"Subject: {subj}\n"
        f"{timeSituation}\n"
        f"Difficulty: {diff}\n"
        f"Total planned hours: {hours}\n"
        f"Days remaining: {days}\n\n"
        f"Recommendation: Study approximately {daily} hour(s) per day for {subj}.\n\n"
        "Practical tips:\n"
        "- Treat sessions as focused blocks (Pomodoro style helps).\n"
        "- Reserve 15–25% of each session for quick revision of previous material.\n"
        "- If difficulty is Hard, split study into shorter daily sessions with active recall.\n"
    )

    # Short message variant (can be used in UI)
    short = ""
    if daily <= 1:
        short = f"Nice — a light daily routine of ~{daily} hour(s) should work. Keep consistent!"
    elif daily <= 2.5:
        short = f"You're on track. Aim for about {daily} hour(s) daily and add a short review each day."
    else:
        short = f"Plan for {daily} hour(s) per day; break sessions and prioritize core topics."

    return {
        "predicted_hours": float(daily),
        "recommendation_text": rec_text,
        "short_text": short,
        "subject": subj,
        "difficulty": diff,
        "days_remaining": days
    }

# Convenience function: mimic a simple API entrypoint if the project uses ml.predict_hours previously
def predict_hours(subject: str, difficulty: str):
    """
    Keep signature somewhat compatible with previous code that expected predict_hours(subject, difficulty).
    This dummy will return a forced small suggestion (not used by our new endpoints).
    """
    # default fallback: 1 hour
    return {"predicted_hours": 1.0, "message": "Default fallback (no days provided). Use recommend() for detailed suggestions."}

# For quick local testing when running this file directly
if __name__ == "__main__":
    print(recommend("Maths", 6, "Medium", 7))
