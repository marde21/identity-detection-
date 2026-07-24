"""
scan_photo.py
Scan a single photo (e.g. a group/crowd photo) against the watchlist.
Detects every face in the image, compares each to watchlist.pkl, and reports
matches - reusing the same alert/logging/telegram pipeline as the live camera,
including case metadata (case number, crime, danger level).

Usage:
  python scan_photo.py path/to/group_photo.jpg
"""

import os
import sys
import datetime
import cv2
import numpy as np
from insightface.app import FaceAnalysis

import config
from main import load_watchlist, trigger_alert  # reuse the same pipeline as the live camera

SCAN_RESULTS_DIR = os.path.join(config.ALERTS_DIR, "scan_results")


def scan_faces(image_path, app=None):
    if not os.path.exists(image_path):
        print(f"Error: file not found: {image_path}")
        return None

    names, embeddings, metadata = load_watchlist()

    if app is None:
        print("Loading face analysis model...")
        app = FaceAnalysis(name="buffalo_l", providers=["CPUExecutionProvider"])
        app.prepare(ctx_id=0, det_size=config.DET_SIZE)

    frame = cv2.imread(image_path)
    if frame is None:
        print(f"Error: could not read image at {image_path}")
        return None

    print(f"\nScanning {image_path} ...")
    faces = app.get(frame)
    print(f"Detected {len(faces)} face(s) in the photo.\n")

    annotated = frame.copy()
    last_alert_time = {}  # local to this scan, so cooldown doesn't block a fresh scan
    match_count = 0
    unknown_count = 0
    results = []

    for face in faces:
        embedding = face.normed_embedding
        box = face.bbox.astype(int)
        x1, y1, x2, y2 = box

        if len(names) > 0:
            similarities = embeddings @ embedding
            best_idx = int(np.argmax(similarities))
            best_score = float(similarities[best_idx])
        else:
            best_score = 0.0
            best_idx = None

        if best_idx is not None and best_score >= config.SIMILARITY_THRESHOLD:
            matched_name = names[best_idx]
            case_info = metadata.get(matched_name)
            color = (0, 0, 255)
            label = f"{matched_name} ({best_score:.2f})"
            match_count += 1
            results.append((matched_name, best_score, True, case_info))
            trigger_alert(matched_name, best_score, frame, box, last_alert_time, case_info)
        else:
            color = (0, 200, 0)
            label = "unknown"
            unknown_count += 1
            results.append((None, best_score, False, None))

        cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
        cv2.putText(annotated, label, (x1, max(y1 - 10, 20)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

    os.makedirs(SCAN_RESULTS_DIR, exist_ok=True)
    timestamp_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    result_path = os.path.join(SCAN_RESULTS_DIR, f"scan_{timestamp_str}.jpg")
    cv2.imwrite(result_path, annotated)

    print("--- Scan summary ---")
    for name, score, is_match, case_info in results:
        if is_match:
            print(f"  MATCH: {name} (confidence={score:.3f}) - "
                  f"Case #{case_info['case_number']} - {case_info['crime']} - "
                  f"Danger: {case_info['danger_level']}")
        else:
            print(f"  unknown face (best score={score:.3f})")

    print(f"\nTotal faces detected: {len(faces)}")
    print(f"Matches found:        {match_count}")
    print(f"Unrecognized:         {unknown_count}")
    print(f"Annotated result saved to: {result_path}")
    if match_count > 0:
        print(f"Individual match snapshots saved under: {config.ALERTS_DIR}\\<name>\\")

    # Format matches for frontend
    formatted_matches = []
    for name, score, is_match, case_info in results:
        if is_match:
            formatted_matches.append({
                "name": name,
                "confidence": score,
                "case_number": case_info["case_number"],
                "crime": case_info["crime"],
                "danger_level": case_info["danger_level"]
            })
            
    return {
        "matches": formatted_matches,
        "total_faces": len(faces),
        "unknown_count": unknown_count,
        "result_image": result_path
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scan_photo.py path/to/photo.jpg")
        sys.exit(1)
    scan_faces(sys.argv[1])