"""
main.py
Live camera watchlist matching. Run enroll.py first to build watchlist.pkl.
Press 'q' to quit.
"""

import os
import csv
import time
import pickle
import datetime
import cv2
import numpy as np
import requests
from insightface.app import FaceAnalysis

import config
from database import get_db


def load_watchlist():
    """
    Returns:
      names: list of person names
      embeddings: np.array of shape (N, 512)
      metadata: dict name -> {case_number, crime, danger_level}
    """
    if not os.path.exists(config.DB_PATH):
        print(f"Error: {config.DB_PATH} not found. Run enroll.py first.")
        exit(1)
    with open(config.DB_PATH, "rb") as f:
        db = pickle.load(f)

    names = list(db.keys())
    embeddings = np.array([db[n]["embedding"] for n in names])
    metadata = {n: {"case_number": db[n].get("case_number", "N/A"),
                     "crime": db[n].get("crime", "N/A"),
                     "danger_level": db[n].get("danger_level", "N/A")} for n in names}
    print(f"Loaded {len(names)} people from watchlist.")
    return names, embeddings, metadata


def log_alert_csv(person_dir, name, similarity, timestamp_str, filename, case_info):
    log_path = os.path.join(person_dir, "log.csv")
    file_exists = os.path.exists(log_path)
    with open(log_path, "a", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["name", "similarity", "timestamp", "snapshot_path",
                              "case_number", "crime", "danger_level"])
        writer.writerow([name, f"{similarity:.3f}", timestamp_str, filename,
                          case_info["case_number"], case_info["crime"], case_info["danger_level"]])


def send_telegram_alert(name, similarity, timestamp_str, photo_path, case_info):
    if not config.ENABLE_TELEGRAM:
        return
    if not config.TELEGRAM_BOT_TOKEN or not config.TELEGRAM_CHAT_ID:
        print("  [telegram] Skipped: bot token / chat id not set in config.py")
        return
    try:
        caption = (
            f"MATCH: {name}\n"
            f"Confidence: {similarity:.2f}\n"
            f"Time: {timestamp_str}\n"
            f"Case #: {case_info['case_number']}\n"
            f"Crime: {case_info['crime']}\n"
            f"Danger level: {case_info['danger_level']}"
        )
        url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendPhoto"
        with open(photo_path, "rb") as photo:
            resp = requests.post(
                url,
                data={"chat_id": config.TELEGRAM_CHAT_ID, "caption": caption},
                files={"photo": photo},
                timeout=10,
            )
        if resp.status_code == 200:
            print("  [telegram] Alert sent")
        else:
            print(f"  [telegram] Failed: {resp.status_code} {resp.text}")
    except Exception as e:
        print(f"  [telegram] Error: {e}")


def send_email_alert(name, similarity, timestamp_str, photo_path, case_info):
    if not config.ENABLE_EMAIL:
        return
    if not config.EMAIL_FROM or not config.EMAIL_TO or not config.EMAIL_APP_PASSWORD:
        print("  [email] Skipped: email settings not filled in config.py")
        return
    try:
        import smtplib
        from email.message import EmailMessage

        msg = EmailMessage()
        msg["Subject"] = f"Watchlist match: {name} ({case_info['danger_level']})"
        msg["From"] = config.EMAIL_FROM
        msg["To"] = config.EMAIL_TO
        msg.set_content(
            f"Match: {name}\n"
            f"Confidence: {similarity:.2f}\n"
            f"Time: {timestamp_str}\n"
            f"Case #: {case_info['case_number']}\n"
            f"Crime: {case_info['crime']}\n"
            f"Danger level: {case_info['danger_level']}"
        )

        with open(photo_path, "rb") as f:
            msg.add_attachment(f.read(), maintype="image", subtype="jpeg",
                                filename=os.path.basename(photo_path))

        with smtplib.SMTP(config.SMTP_SERVER, config.SMTP_PORT) as server:
            server.starttls()
            server.login(config.EMAIL_FROM, config.EMAIL_APP_PASSWORD)
            server.send_message(msg)
        print("  [email] Alert sent")
    except Exception as e:
        print(f"  [email] Error: {e}")


def trigger_alert(name, similarity, frame, box, last_alert_time, case_info=None, camera_id=None, watchlist_id=None):
    if case_info is None:
        case_info = {"case_number": "N/A", "crime": "N/A", "danger_level": "N/A"}

    now = time.time()
    if now - last_alert_time.get(name, 0) < config.ALERT_COOLDOWN:
        return  # still in cooldown, skip
    last_alert_time[name] = now

    timestamp_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n*** MATCH DETECTED: {name} (similarity={similarity:.3f}) at {timestamp_str} ***")
    print(f"    Case #{case_info['case_number']} - {case_info['crime']} - Danger: {case_info['danger_level']}")

    person_dir = os.path.join(config.ALERTS_DIR, name)
    os.makedirs(person_dir, exist_ok=True)
    filename = os.path.join(person_dir, f"{int(now)}.jpg")

    annotated = frame.copy()
    x1, y1, x2, y2 = box
    cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 0, 255), 3)
    label = f"MATCH: {name} ({similarity:.2f})"
    cv2.putText(annotated, label, (x1, max(y1 - 40, 20)),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
    cv2.putText(annotated, f"{case_info['crime']} | {case_info['danger_level']}", (x1, max(y1 - 15, 40)),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 255), 2)
    cv2.putText(annotated, timestamp_str, (10, annotated.shape[0] - 15),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

    cv2.imwrite(filename, annotated)
    print(f"Snapshot saved: {filename}")

    log_alert_csv(person_dir, name, similarity, timestamp_str, filename, case_info)
    
    if watchlist_id and camera_id is not None:
        conn = get_db()
        c = conn.cursor()
        c.execute('''INSERT INTO alert_logs (watchlist_id, camera_id, confidence, photo_path)
                     VALUES (?, ?, ?, ?)''', (watchlist_id, camera_id, similarity, filename))
        conn.commit()
        conn.close()
        
    send_telegram_alert(name, similarity, timestamp_str, filename, case_info)
    send_email_alert(name, similarity, timestamp_str, filename, case_info)


def main():
    names, embeddings, metadata = load_watchlist()

    print("Loading face analysis model...")
    app = FaceAnalysis(name="buffalo_l", providers=["CPUExecutionProvider"])
    app.prepare(ctx_id=0, det_size=config.DET_SIZE)

    cap = cv2.VideoCapture(config.CAMERA_INDEX)
    if not cap.isOpened():
        print("Error: could not open camera.")
        return

    last_alert_time = {}
    print("Camera running. Press 'q' to quit.\n")

    prev_time = time.time()
    fps = 0.0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        faces = app.get(frame)

        for face in faces:
            embedding = face.normed_embedding
            box = face.bbox.astype(int)

            if len(names) > 0:
                similarities = embeddings @ embedding
                best_idx = int(np.argmax(similarities))
                best_score = similarities[best_idx]
            else:
                best_score = 0.0
                best_idx = None

            if best_idx is not None and best_score >= config.SIMILARITY_THRESHOLD:
                matched_name = names[best_idx]
                color = (0, 0, 255)  # red box = match
                label = f"{matched_name} ({best_score:.2f})"
                trigger_alert(matched_name, best_score, frame, box, last_alert_time,
                              metadata.get(matched_name))
            else:
                color = (0, 200, 0)  # green box = unknown, no alert
                label = "unknown"

            cv2.rectangle(frame, (box[0], box[1]), (box[2], box[3]), color, 2)
            cv2.putText(frame, label, (box[0], box[1] - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

        now = time.time()
        fps = 0.9 * fps + 0.1 * (1 / max(now - prev_time, 1e-6))
        prev_time = now
        cv2.putText(frame, f"FPS: {fps:.1f}", (10, 25),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.putText(frame, f"Watchlist size: {len(names)}", (10, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        cv2.imshow("Watchlist Camera", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()