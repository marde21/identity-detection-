"""
app.py
REST API for the Face Watchlist system.
Serves the Vue frontend SPA and exposes /api endpoints.
"""

import os
import re
import csv
import sys
import importlib
import subprocess
import cv2
import numpy as np
import datetime
import time
from flask import Flask, request, Response, send_from_directory, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO
from insightface.app import FaceAnalysis

# Ensure CWD is backend/ so config and data files are found
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
from main import trigger_alert
from db_helpers import search_face, add_person, update_person, delete_person_by_name
from database import get_db
from camera_manager import CameraManager
from scan_photo import scan_faces
from identify_suspect import identify_faces

PYTHON = sys.executable
UPLOADS_DIR = "uploads"

# Serve frontend/dist as static root
app = Flask(__name__, static_folder="../frontend/dist", static_url_path="/")
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

os.makedirs(UPLOADS_DIR, exist_ok=True)

print("Loading face analysis model for the web app (this can take a moment)...")
FACE_APP = FaceAnalysis(name="buffalo_l", providers=["CPUExecutionProvider"])
FACE_APP.prepare(ctx_id=0, det_size=config.DET_SIZE)
print("Model loaded. API ready.")

camera_manager = CameraManager(FACE_APP, socketio)

latest_detected_alert = None
is_camera_active = False

# ---------------- Shared helpers ----------------

def read_all_alert_rows():
    rows = []
    if not os.path.isdir(config.ALERTS_DIR):
        return rows
    for name in sorted(os.listdir(config.ALERTS_DIR)):
        person_dir = os.path.join(config.ALERTS_DIR, name)
        if not os.path.isdir(person_dir) or name == "scan_results":
            continue
        log_path = os.path.join(person_dir, "log.csv")
        if not os.path.exists(log_path):
            continue
        with open(log_path, newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                row["name"] = name
                rows.append(row)
    return rows

def sanitize_folder_name(name):
    name = name.strip()
    return re.sub(r'[\\/:*?"<>|]', '', name)

def get_person_photo_path(name):
    for base_dir in [config.WANTED_PHOTOS_DIR, config.VILLAGE_PHOTOS_DIR]:
        folder = os.path.join(base_dir, name)
        if os.path.isdir(folder):
            for fname in sorted(os.listdir(folder)):
                if fname.lower().endswith((".jpg", ".jpeg", ".png")):
                    return os.path.join(folder, fname)
        for ext in (".jpg", ".jpeg", ".png"):
            candidate = os.path.join(base_dir, name + ext)
            if os.path.exists(candidate):
                return candidate
    return None

def get_person_photo_url(name):
    path = get_person_photo_path(name)
    if path:
        return f"/media/{path}"
    return None

def extract_embedding_from_image(image_path):
    img = cv2.imread(image_path)
    if img is None:
        return None
    faces = FACE_APP.get(img)
    if not faces:
        return None
    # Get largest face
    faces = sorted(faces, key=lambda x: (x.bbox[2]-x.bbox[0])*(x.bbox[3]-x.bbox[1]), reverse=True)
    return faces[0].normed_embedding

# ---------------- API Endpoints ----------------

@app.route("/api/dashboard", methods=["GET"])
def api_dashboard():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM watchlist")
    count = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM alert_logs")
    total_alerts = c.fetchone()[0]
    
    c.execute('''
        SELECT COUNT(*) FROM alert_logs a
        JOIN watchlist w ON a.watchlist_id = w.id
        WHERE w.danger_level = "HIGH"
    ''')
    high_danger_count = c.fetchone()[0]
    
    conn.close()

    return jsonify({
        "watchlist_count": count,
        "total_alerts": total_alerts,
        "high_danger_count": high_danger_count
    })

@app.route("/api/latest_alert", methods=["GET"])
def api_latest_alert():
    global latest_detected_alert
    return jsonify({"alert": latest_detected_alert})

@app.route("/api/cameras", methods=["GET", "POST"])
def api_cameras():
    if request.method == "GET":
        return jsonify(camera_manager.get_all_camera_ids())
        
    action = request.form.get("action")
    if action == "add":
        name = request.form.get("name")
        source = request.form.get("source")
        conn = get_db()
        c = conn.cursor()
        c.execute("INSERT INTO cameras (name, source) VALUES (?, ?)", (name, source))
        conn.commit()
        conn.close()
        return jsonify({"status": "success"})
    elif action == "delete":
        camera_id = request.form.get("camera_id")
        camera_manager.stop_client(int(camera_id))
        conn = get_db()
        c = conn.cursor()
        c.execute("DELETE FROM cameras WHERE id=?", (camera_id,))
        conn.commit()
        conn.close()
        return jsonify({"status": "success"})
        
    return jsonify({"error": "invalid action"}), 400

@app.route("/video_feed/<int:camera_id>")
def video_feed(camera_id):
    def generate():
        started = camera_manager.start_client(camera_id)
        if not started:
            return
        try:
            while camera_manager.is_running(camera_id):
                frame_bytes = camera_manager.get_frame(camera_id)
                if frame_bytes:
                    yield (b"--frame\r\n"
                           b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n")
                time.sleep(0.05)
        finally:
            camera_manager.stop_client(camera_id)
            
    return Response(generate(), mimetype="multipart/x-mixed-replace; boundary=frame")

@app.route("/api/monitoring/stop", methods=["POST"])
def api_monitoring_stop():
    camera_manager.force_stop_all()
    return jsonify({"status": "success"})

@app.route("/api/search", methods=["POST"])
def api_search():
    search_type = request.form.get("search_type", "watchlist")
    file = request.files.get("photo")
    if not file or not file.filename:
        return jsonify({"error": "No photo uploaded"}), 400

    save_path = os.path.join(UPLOADS_DIR, file.filename)
    file.save(save_path)
    
    if search_type == "watchlist":
        result_dict = scan_faces(save_path, FACE_APP)
        if result_dict:
            for match in result_dict.get("matches", []):
                match["photo_url"] = get_person_photo_url(match["name"])
        return jsonify(result_dict)
        
    elif search_type == "village":
        result_dict = identify_faces(save_path, FACE_APP)
        if result_dict:
            for r in result_dict.get("ranked", []):
                r["photo_url"] = get_person_photo_url(r["name"])
        return jsonify(result_dict)
        
    return jsonify({"error": "Invalid search type"}), 400

@app.route("/api/alerts", methods=["GET"])
def api_alerts():
    people = []
    if os.path.isdir(config.ALERTS_DIR):
        for name in sorted(os.listdir(config.ALERTS_DIR)):
            person_dir = os.path.join(config.ALERTS_DIR, name)
            if not os.path.isdir(person_dir) or name == "scan_results":
                continue
            log_path = os.path.join(person_dir, "log.csv")
            rows = []
            if os.path.exists(log_path):
                with open(log_path, newline="") as f:
                    reader = csv.DictReader(f)
                    rows = list(reader)
            rows.reverse()
            people.append({"name": name, "rows": rows, "photo_url": get_person_photo_url(name)})
    return jsonify({"people": people})

@app.route("/api/analytics", methods=["GET"])
def api_analytics():
    all_rows = read_all_alert_rows()
    total_alerts = len(all_rows)

    per_person_counts = {}
    danger_counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
    confidences = []

    for row in all_rows:
        name = row.get("name", "unknown")
        per_person_counts[name] = per_person_counts.get(name, 0) + 1
        level = row.get("danger_level", "N/A")
        if level in danger_counts:
            danger_counts[level] += 1
        try:
            confidences.append(float(row.get("similarity", 0)))
        except ValueError:
            pass

    per_person = sorted(per_person_counts.items(), key=lambda x: x[1], reverse=True)
    max_count = max(per_person_counts.values()) if per_person_counts else 0
    avg_confidence = f"{(sum(confidences) / len(confidences)):.2f}" if confidences else "N/A"

    recent_alerts = sorted(all_rows, key=lambda r: r.get("timestamp", ""), reverse=True)[:10]

    return jsonify({
        "total_alerts": total_alerts,
        "unique_people": len(per_person_counts),
        "high_danger_count": danger_counts["HIGH"],
        "avg_confidence": avg_confidence,
        "per_person": [{"name": k, "count": v} for k, v in per_person],
        "max_count": max_count,
        "danger_counts": danger_counts,
        "recent_alerts": recent_alerts
    })

@app.route("/api/alert_history", methods=["GET"])
def api_alert_history():
    conn = get_db()
    c = conn.cursor()
    c.execute('''
        SELECT a.id, a.timestamp, a.confidence, a.photo_path,
               w.name as person_name, w.case_number, w.crime, w.danger_level,
               c.name as camera_name
        FROM alert_logs a
        JOIN watchlist w ON a.watchlist_id = w.id
        LEFT JOIN cameras c ON a.camera_id = c.id
        ORDER BY a.timestamp DESC
        LIMIT 100
    ''')
    rows = c.fetchall()
    conn.close()
    
    history = []
    for r in rows:
        d = dict(r)
        if d.get("photo_path"):
            d["photo_url"] = "/media/" + d["photo_path"].replace("\\", "/")
        else:
            d["photo_url"] = None
        history.append(d)
        
    return jsonify({"history": history})

@app.route("/api/watchlist", methods=["GET", "POST"])
def api_watchlist():
    if request.method == "GET":
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT * FROM watchlist")
        rows = c.fetchall()
        conn.close()
        records = [dict(r) for r in rows]
        for r in records:
            r["photo_url"] = get_person_photo_url(r["name"])
        return jsonify({"records": records})
        
    action = request.form.get("action")

    if action == "add":
        name = request.form.get("name", "").strip()
        case_number = request.form.get("case_number", "").strip()
        crime = request.form.get("crime", "").strip() or "N/A"
        danger_level = request.form.get("danger_level", "LOW").strip()
        files = request.files.getlist("photos")
        
        if not name:
            return jsonify({"error": "Name is required."}), 400
            
        folder_name = sanitize_folder_name(name)
        person_dir = os.path.join(config.WANTED_PHOTOS_DIR, folder_name)
        os.makedirs(person_dir, exist_ok=True)
        
        photo_path = None
        if files and any(f.filename for f in files):
            for f in files:
                if f and f.filename:
                    save_path = os.path.join(person_dir, f.filename)
                    f.save(save_path)
                    photo_path = save_path
                    
        if not photo_path:
            return jsonify({"error": "Photo is required for adding a person."}), 400
            
        embedding = extract_embedding_from_image(photo_path)
        if embedding is None:
            return jsonify({"error": "No face found in uploaded photo."}), 400
            
        try:
            add_person(folder_name, case_number, crime, danger_level, embedding)
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
            
        return jsonify({"status": "success"})

    elif action == "update":
        original_name = request.form.get("original_name")
        new_name = request.form.get("name", original_name).strip()
        new_folder_name = sanitize_folder_name(new_name)
        old_folder_name = sanitize_folder_name(original_name)
        
        if new_folder_name != old_folder_name:
            old_dir = os.path.join(config.WANTED_PHOTOS_DIR, old_folder_name)
            new_dir = os.path.join(config.WANTED_PHOTOS_DIR, new_folder_name)
            if os.path.exists(old_dir) and os.path.isdir(old_dir):
                os.rename(old_dir, new_dir)
            else:
                for ext in (".jpg", ".jpeg", ".png"):
                    old_file = os.path.join(config.WANTED_PHOTOS_DIR, old_folder_name + ext)
                    new_file = os.path.join(config.WANTED_PHOTOS_DIR, new_folder_name + ext)
                    if os.path.exists(old_file):
                        os.rename(old_file, new_file)

        case_number = request.form.get("case_number", "").strip()
        crime = request.form.get("crime", "").strip()
        danger_level = request.form.get("danger_level", "LOW").strip()
        
        update_person(original_name, new_folder_name, case_number, crime, danger_level)
        return jsonify({"status": "success"})

    elif action == "delete":
        original_name = request.form.get("original_name")
        
        delete_person_by_name(original_name)
        
        import shutil
        import stat
        def remove_readonly(func, path, _):
            try:
                os.chmod(path, stat.S_IWRITE)
                func(path)
            except Exception:
                pass

        folder_name = sanitize_folder_name(original_name)
        person_dir = os.path.join(config.WANTED_PHOTOS_DIR, folder_name)
        if os.path.exists(person_dir) and os.path.isdir(person_dir):
            try:
                shutil.rmtree(person_dir, onerror=remove_readonly)
            except Exception:
                pass
                
        for ext in (".jpg", ".jpeg", ".png"):
            p = os.path.join(config.WANTED_PHOTOS_DIR, folder_name + ext)
            if os.path.exists(p): 
                try:
                    os.remove(p)
                except Exception:
                    pass
            
        return jsonify({"status": "success"})
        
    return jsonify({"error": "Invalid action"}), 400

@app.route("/api/settings", methods=["GET", "POST"])
def api_settings():
    if request.method == "GET":
        return jsonify({
            "threshold": config.SIMILARITY_THRESHOLD,
            "cooldown": config.ALERT_COOLDOWN,
            "camera_index": config.CAMERA_INDEX,
            "enable_telegram": config.ENABLE_TELEGRAM,
            "telegram_token": config.TELEGRAM_BOT_TOKEN,
            "telegram_chat_id": config.TELEGRAM_CHAT_ID,
        })
        
    threshold = request.form.get("threshold", str(config.SIMILARITY_THRESHOLD)).strip() or str(config.SIMILARITY_THRESHOLD)
    cooldown = request.form.get("cooldown", str(config.ALERT_COOLDOWN)).strip() or str(config.ALERT_COOLDOWN)
    camera_index = request.form.get("camera_index", str(config.CAMERA_INDEX)).strip()
    if not camera_index.isdigit():
        camera_index = "0"
    enable_telegram = str("enable_telegram" in request.form)
    telegram_token = request.form.get("telegram_token", "")
    telegram_chat_id = request.form.get("telegram_chat_id", "")

    with open("config.py", "r") as f:
        text = f.read()

    text = re.sub(r"SIMILARITY_THRESHOLD\s*=\s*[^\n]+", f"SIMILARITY_THRESHOLD = {threshold}", text)
    text = re.sub(r"ALERT_COOLDOWN\s*=\s*[^\n]+", f"ALERT_COOLDOWN = {cooldown}", text)
    text = re.sub(r"CAMERA_INDEX\s*=\s*[^\n]+", f"CAMERA_INDEX = {camera_index}", text)
    text = re.sub(r"ENABLE_TELEGRAM\s*=\s*[^\n]+", f"ENABLE_TELEGRAM = {enable_telegram}", text)
    text = re.sub(r'TELEGRAM_BOT_TOKEN\s*=\s*"[^"]*"', f'TELEGRAM_BOT_TOKEN = "{telegram_token}"', text)
    text = re.sub(r'TELEGRAM_CHAT_ID\s*=\s*"[^"]*"', f'TELEGRAM_CHAT_ID = "{telegram_chat_id}"', text)

    with open("config.py", "w") as f:
        f.write(text)

    importlib.reload(config)
    return jsonify({"status": "success"})

@app.route("/media/<path:filepath>")
def media(filepath):
    if ".." in filepath:
        return "Invalid path", 400
    directory = os.path.dirname(filepath) or "."
    filename = os.path.basename(filepath)
    return send_from_directory(directory, filename)

# Catch-all route for Vue SPA
@app.route("/", defaults={'path': ''})
@app.route("/<path:path>")
def serve_spa(path):
    if path and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    return send_from_directory(app.static_folder, "index.html")

if __name__ == "__main__":
    socketio.run(app, debug=False, port=5000, allow_unsafe_werkzeug=True)