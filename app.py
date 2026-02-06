# app.py
import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from sqlalchemy.exc import SQLAlchemyError

from db import engine, SessionLocal, Base
from models import StudyEntry, WeeklyPlannerEntry # Updated import
import ml
import weekly_ml # New import

# --- Setup ---
Base.metadata.create_all(bind=engine)

app = Flask(__name__)
CORS(app)


# --- Health Check ---
@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "message": "AI Study Planner backend running"}), 200


# === Existing Daily Planner Endpoints ===

# --- Create Study Entry ---
@app.route("/api/study", methods=["POST", "OPTIONS"])
def create_study_entry():
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200
    payload = request.get_json(force=True)
    required = ["subject", "hours", "difficulty"]
    for k in required:
        if k not in payload:
            return jsonify({"error": f"Missing field: {k}"}), 400
    try:
        db = SessionLocal()
        entry = StudyEntry(
            subject=str(payload.get("subject")).strip(),
            hours=float(payload.get("hours")),
            difficulty=str(payload.get("difficulty")).strip(),
            notes=str(payload.get("notes") or "")
        )
        db.add(entry)
        db.commit()
        db.refresh(entry)
        return jsonify({
            "id": entry.id,
            "subject": entry.subject,
            "hours": entry.hours,
            "difficulty": entry.difficulty,
            "notes": entry.notes,
            "created_at": entry.created_at.isoformat()
        }), 201
    except (ValueError, SQLAlchemyError) as e:
        db.rollback()
        return jsonify({"error": "db_error", "message": str(e)}), 500
    finally:
        db.close()


# --- List All Study Entries ---
@app.route("/api/study", methods=["GET", "OPTIONS"])
def list_study_entries():
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200
        
    db = SessionLocal()
    try:
        entries = db.query(StudyEntry).order_by(StudyEntry.created_at.desc()).all()
        result = [
            {
                "id": e.id, "subject": e.subject, "hours": e.hours,
                "difficulty": e.difficulty, "notes": e.notes,
                "created_at": e.created_at.isoformat()
            } for e in entries
        ]
        return jsonify(result)
    except SQLAlchemyError as e:
        db.rollback()
        return jsonify({"error": "db_error", "message": str(e)}), 500
    finally:
        db.close()


# --- Get One Entry ---
@app.route("/api/study/<int:entry_id>", methods=["GET", "OPTIONS"])
def get_entry(entry_id):
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200
    db = SessionLocal()
    try:
        e = db.query(StudyEntry).filter(StudyEntry.id == entry_id).first()
        if not e:
            return jsonify({"error": "not_found"}), 404
        return jsonify({
            "id": e.id,
            "subject": e.subject,
            "hours": e.hours,
            "difficulty": e.difficulty,
            "notes": e.notes,
            "created_at": e.created_at.isoformat()
        })
    except SQLAlchemyError as e:
        db.rollback()
        return jsonify({"error": "db_error", "message": str(e)}), 500
    finally:
        db.close()


# --- Delete Entry ---
@app.route("/api/study/<int:entry_id>", methods=["DELETE", "OPTIONS"])
def delete_entry(entry_id):
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200

    db = SessionLocal()
    try:
        e = db.query(StudyEntry).filter(StudyEntry.id == entry_id).first()
        if not e:
            return jsonify({"error": "not_found"}), 404
        db.delete(e)
        db.commit()
        return jsonify({"status": "deleted"})
    except SQLAlchemyError as e:
        db.rollback()
        return jsonify({"error": "db_error", "message": str(e)}), 500
    finally:
        db.close()


# --- Offline AI Recommendation Endpoint ---
@app.route("/api/predict", methods=["POST", "OPTIONS"])
def predict():
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200
    payload = request.get_json(force=True)
    subject = payload.get("subject")
    difficulty = payload.get("difficulty", "Medium")
    hours = payload.get("hours", 1.0)
    days_remaining = payload.get("days_remaining", 7)

    if not subject:
        return jsonify({"error": "subject_required"}), 400

    try:
        result = ml.recommend(
            subject=subject,
            hours=hours,
            difficulty=difficulty,
            days_remaining=days_remaining
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": "prediction_failed", "message": str(e)}), 500


# === New Weekly Planner Endpoints ===

@app.route("/api/weekly_schedule", methods=["POST", "OPTIONS"])
def create_weekly_schedule():
    """
    Receives JSON with settings and a list of subjects,
    returns a generated weekly schedule.
    """
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200
    payload = request.get_json(force=True)
    settings = payload.get("settings")
    subjects = payload.get("subjects")

    if not settings or not subjects:
        return jsonify({"error": "settings_and_subjects_required"}), 400
    
    try:
        # Call the new offline weekly schedule generator
        result = weekly_ml.generate_schedule(settings, subjects)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": "schedule_generation_failed", "message": str(e)}), 500


# --- Creator Info ---
@app.route("/api/creators", methods=["GET"])
def get_creators():
    return jsonify({
        "creators": [
            {"id": "10", "name": "Amrut Dabir"},
            {"id": "59", "name": "Rushikesh Katare"}
        ]
    })


# --- App Runner ---
if __name__ == "__main__":
    print(" Starting AI Study Planner backend (offline mode)...")
    app.run(host="0.0.0.0", port=5000, debug=True)

