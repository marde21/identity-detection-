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
from insightface.app import FaceAnalysis

# Ensure CWD is backend/ so config and data files are found
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
from main import load_watchlist, trigger_alert
from enroll import enroll_faces
from scan_photo import scan_faces
from identify_suspect import identify_faces

PYTHON = sys.executable
UPLOADS_DIR = "uploads"
RECORDS_PATH = "criminal_records.csv"

# Serve frontend/dist as static root
app = Flask(__name__, static_folder="../frontend/dist", static_url_path="/")
CORS(app)

os.makedirs(UPLOADS_DIR, exist_ok=True)

print("Loading face analysis model for the web app (this can take a moment)...")
FACE_APP = FaceAnalysis(name="buffalo_l", providers=["CPUExecutionProvider"])
FACE_APP.prepare(ctx_id=0, det_size=config.DET_SIZE)
print("Model loaded. API ready.")

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

def read_records():
    if not os.path.exists(RECORDS_PATH):
        return []
    with open(RECORDS_PATH, newline="") as f:
        reader = csv.DictReader(f)
        return [dict(row) for row in reader]

def write_records(records):
    with open(RECORDS_PATH, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["name", "case_number", "crime", "danger_level"])
        writer.writeheader()
        for r in records:
            writer.writerow(r)

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

# ---------------- API Endpoints ----------------

@app.route("/api/dashboard", methods=["GET"])
def api_dashboard():
    count = 0
    if os.path.exists(config.DB_PATH):
        names, _, _ = load_watchlist()
        count = len(names)

    all_rows = read_all_alert_rows()
    total_alerts = len(all_rows)
    high_danger_count = sum(1 for r in all_rows if r.get("danger_level") == "HIGH")

    return jsonify({
        "watchlist_count": count,
        "total_alerts": total_alerts,
        "high_danger_count": high_danger_count
    })

@app.route("/api/latest_alert", methods=["GET"])
def api_latest_alert():
    global latest_detected_alert
    return jsonify({"alert": latest_detected_alert})

@app.route("/api/start_camera", methods=["POST"])
def api_start_camera():
    global is_camera_active
    is_camera_active = True
    return jsonify({"status": "started"})

@app.route("/api/stop_camera", methods=["POST"])
def api_stop_camera():
    global is_camera_active
    is_camera_active = False
    return jsonify({"status": "stopped"})

def gen_camera_frames():
    global is_camera_active
    names, embeddings, metadata = load_watchlist()
    cap = cv2.VideoCapture(config.CAMERA_INDEX)
    last_alert_time = {}
    last_criminal_seen = 0
    try:
        while True:
            if not is_camera_active:
                break
                
            ret, frame = cap.read()
            if not ret:
                break

            faces = FACE_APP.get(frame)
            criminal_detected_this_frame = False
            
            for face in faces:
                embedding = face.normed_embedding
                box = face.bbox.astype(int)

                if len(names) > 0:
                    similarities = embeddings @ embedding
                    best_idx = int(np.argmax(similarities))
                    best_score = similarities[best_idx]
                else:
                    best_score, best_idx = 0.0, None

                if best_idx is not None and best_score >= config.SIMILARITY_THRESHOLD:
                    criminal_detected_this_frame = True
                    matched_name = names[best_idx]
                    color = (0, 0, 255)
                    label = f"{matched_name} ({best_score:.2f})"
                    
                    global latest_detected_alert
                    case_info = metadata.get(matched_name, {})
                    latest_detected_alert = {
                        "name": matched_name,
                        "similarity": float(best_score),
                        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "case_number": case_info.get("case_number", "N/A"),
                        "crime": case_info.get("crime", "N/A"),
                        "danger_level": case_info.get("danger_level", "N/A"),
                        "photo_url": get_person_photo_url(matched_name)
                    }
                    
                    trigger_alert(matched_name, best_score, frame, box, last_alert_time, case_info)
                else:
                    color = (0, 200, 0)
                    label = "unknown"

                cv2.rectangle(frame, (box[0], box[1]), (box[2], box[3]), color, 2)
                cv2.putText(frame, label, (box[0], box[1] - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

            if criminal_detected_this_frame:
                last_criminal_seen = time.time()
            elif time.time() - last_criminal_seen > 2.0:
                latest_detected_alert = None

            ok, buffer = cv2.imencode(".jpg", frame)
            if not ok:
                continue
            frame_bytes = buffer.tobytes()
            yield (b"--frame\r\n"
                   b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n")
    finally:
        cap.release()

@app.route("/video_feed")
def video_feed():
    return Response(gen_camera_frames(), mimetype="multipart/x-mixed-replace; boundary=frame")

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

@app.route("/api/watchlist", methods=["GET", "POST"])
def api_watchlist():
    if request.method == "GET":
        records = read_records()
        for r in records:
            r["photo_url"] = get_person_photo_url(r["name"])
        return jsonify({"records": records})
        
    action = request.form.get("action")
    records = read_records()

    if action == "add":
        name = request.form.get("name", "").strip()
        case_number = request.form.get("case_number", "").strip()
        crime = request.form.get("crime", "").strip() or "N/A"
        danger_level = request.form.get("danger_level", "LOW").strip()
        files = request.files.getlist("photos")
        
        if not name:
            return jsonify({"error": "Name is required."}), 400
            
        folder_name = sanitize_folder_name(name)
        if files and any(f.filename for f in files):
            person_dir = os.path.join(config.WANTED_PHOTOS_DIR, folder_name)
            os.makedirs(person_dir, exist_ok=True)
            for f in files:
                if f and f.filename:
                    f.save(os.path.join(person_dir, f.filename))
        
        found = False
        for r in records:
            if r["name"].strip().lower() == folder_name.lower():
                r["case_number"] = case_number
                r["crime"] = crime
                r["danger_level"] = danger_level
                found = True
        if not found:
            records.append({
                "name": folder_name, "case_number": case_number,
                "crime": crime, "danger_level": danger_level
            })
        
        write_records(records)
        enroll_faces(FACE_APP)
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

        for r in records:
            if r["name"] == original_name:
                r["name"] = new_folder_name
                r["case_number"] = request.form.get("case_number", "").strip()
                r["crime"] = request.form.get("crime", "").strip()
                r["danger_level"] = request.form.get("danger_level", "LOW").strip()
        write_records(records)
        enroll_faces(FACE_APP)
        return jsonify({"status": "success"})

    elif action == "delete":
        original_name = request.form.get("original_name")
        records = [r for r in records if r["name"] != original_name]
        write_records(records)
        
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
            
        enroll_faces(FACE_APP)
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
    app.run(debug=False, port=5000)