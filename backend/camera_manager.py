import cv2
import threading
import time
import datetime
import os
from database import get_db
import config
from db_helpers import search_face
from main import trigger_alert

def get_simple_photo_url(name):
    folder = os.path.join(config.WANTED_PHOTOS_DIR, name)
    if os.path.exists(folder):
        for f in sorted(os.listdir(folder)):
            if f.lower().endswith(('.jpg', '.jpeg', '.png')):
                return f"/media/{config.WANTED_PHOTOS_DIR}/{name}/{f}"
    return None

class SharedCamera:
    def __init__(self, camera_id, source, face_app, socketio):
        self.camera_id = camera_id
        # Source can be an integer (0) for USB or a string ("rtsp://...")
        self.source = int(source) if str(source).isdigit() else source
        self.face_app = face_app
        self.socketio = socketio
        
        self.cap = None
        self.current_frame = None
        self.thread = None
        self.stop_event = threading.Event()
        self.clients = 0
        self.lock = threading.Lock()
        
        self.last_alert_time = {}
        self.last_criminal_seen = 0

    def start(self):
        with self.lock:
            self.clients += 1
            if self.thread is None or not self.thread.is_alive():
                self.stop_event.clear()
                self.thread = threading.Thread(target=self._capture_loop, daemon=True)
                self.thread.start()

    def stop(self):
        with self.lock:
            self.clients -= 1
            if self.clients <= 0:
                self.clients = 0
                self.stop_event.set()
                if self.thread:
                    self.thread.join(timeout=1.0)
                    self.thread = None

    def get_frame(self):
        return self.current_frame

    def _capture_loop(self):
        self.cap = cv2.VideoCapture(self.source)
        
        while not self.stop_event.is_set():
            ret, frame = self.cap.read()
            if not ret:
                time.sleep(0.1)
                # Try to reconnect
                self.cap.release()
                self.cap = cv2.VideoCapture(self.source)
                continue

            # In a multi-camera setup, inference on every frame might be too heavy.
            # We skip some frames for AI inference to save CPU, but draw on every frame.
            
            with CameraManager.ai_lock:
                faces = self.face_app.get(frame)
                
            criminal_detected_this_frame = False
            
            for face in faces:
                embedding = face.normed_embedding
                box = face.bbox.astype(int)

                match_info = search_face(embedding, threshold=config.SIMILARITY_THRESHOLD)

                if match_info:
                    criminal_detected_this_frame = True
                    matched_name = match_info["name"]
                    best_score = match_info["similarity"]
                    color = (0, 0, 255)
                    label = f"{matched_name} ({best_score:.2f})"
                    
                    case_info = {
                        "case_number": match_info["case_number"],
                        "crime": match_info["crime"],
                        "danger_level": match_info["danger_level"]
                    }
                    
                    # Instead of global latest_detected_alert, we just emit socket
                    alert_payload = {
                        "name": matched_name,
                        "similarity": best_score,
                        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "case_number": match_info["case_number"],
                        "crime": match_info["crime"],
                        "danger_level": match_info["danger_level"],
                        "camera_id": self.camera_id,
                        "photo_url": get_simple_photo_url(matched_name)
                    }
                    
                    self.socketio.emit('new_alert', alert_payload)
                    trigger_alert(matched_name, best_score, frame, box, self.last_alert_time, case_info, self.camera_id, match_info["id"])
                else:
                    color = (0, 200, 0)
                    label = "unknown"

                cv2.rectangle(frame, (box[0], box[1]), (box[2], box[3]), color, 2)
                cv2.putText(frame, label, (box[0], box[1] - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

            ok, buffer = cv2.imencode(".jpg", frame)
            if ok:
                self.current_frame = buffer.tobytes()

            # Small sleep to yield CPU
            time.sleep(0.03)

        if self.cap:
            self.cap.release()
            self.cap = None


class CameraManager:
    # Class-level lock to ensure only one camera does FaceAnalysis at a time
    ai_lock = threading.Lock()
    
    def __init__(self, face_app, socketio):
        self.face_app = face_app
        self.socketio = socketio
        self.cameras = {} # {camera_id: SharedCamera}
        self.manager_lock = threading.Lock()
        
    def _ensure_camera(self, camera_id):
        with self.manager_lock:
            if camera_id not in self.cameras:
                conn = get_db()
                c = conn.cursor()
                c.execute("SELECT source FROM cameras WHERE id=?", (camera_id,))
                row = c.fetchone()
                conn.close()
                
                if row:
                    source = row["source"]
                    self.cameras[camera_id] = SharedCamera(camera_id, source, self.face_app, self.socketio)
                else:
                    return None
            return self.cameras[camera_id]

    def get_frame(self, camera_id):
        cam = self._ensure_camera(camera_id)
        if cam:
            return cam.get_frame()
        return None
        
    def is_running(self, camera_id):
        with self.manager_lock:
            if camera_id in self.cameras:
                return not self.cameras[camera_id].stop_event.is_set()
        return False
        
    def start_client(self, camera_id):
        cam = self._ensure_camera(camera_id)
        if cam:
            cam.start()
            return True
        return False
        
    def stop_client(self, camera_id):
        with self.manager_lock:
            if camera_id in self.cameras:
                self.cameras[camera_id].stop()
                
    def force_stop_all(self):
        with self.manager_lock:
            for cam in self.cameras.values():
                with cam.lock:
                    cam.clients = 0
                    cam.stop_event.set()
                    if cam.thread:
                        cam.thread.join(timeout=1.0)
                        cam.thread = None
                
    def get_all_camera_ids(self):
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT id, name, source FROM cameras")
        rows = c.fetchall()
        conn.close()
        return [dict(r) for r in rows]
