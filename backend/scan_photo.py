import os
import sys
import datetime
import cv2
import numpy as np
from insightface.app import FaceAnalysis

import config
from db_helpers import search_face

SCAN_RESULTS_DIR = os.path.join(config.ALERTS_DIR, "scan_results")


def scan_faces(image_path, app=None):
    if not os.path.exists(image_path):
        print(f"Error: file not found: {image_path}")
        return None

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
    match_count = 0
    unknown_count = 0
    results = []

    for face in faces:
        embedding = face.normed_embedding
        box = face.bbox.astype(int)
        x1, y1, x2, y2 = box

        match_info = search_face(embedding, threshold=config.SIMILARITY_THRESHOLD)

        if match_info:
            matched_name = match_info["name"]
            best_score = match_info["similarity"]
            color = (0, 0, 255)
            label = f"{matched_name} ({best_score:.2f})"
            match_count += 1
            results.append({
                "name": matched_name,
                "similarity": best_score,
                "case_number": match_info["case_number"],
                "crime": match_info["crime"],
                "danger_level": match_info["danger_level"]
            })
        else:
            color = (0, 200, 0)
            label = "unknown"
            unknown_count += 1

        cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
        cv2.putText(annotated, label, (x1, max(y1 - 10, 20)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

    os.makedirs(SCAN_RESULTS_DIR, exist_ok=True)
    timestamp_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    result_path = os.path.join(SCAN_RESULTS_DIR, f"scan_{timestamp_str}.jpg")
    cv2.imwrite(result_path, annotated)

    print(f"Total faces detected: {len(faces)}")
    print(f"Matches found:        {match_count}")
    print(f"Unrecognized:         {unknown_count}")

    return {
        "matches": results,
        "total_faces": len(faces),
        "unknown_count": unknown_count,
        "result_image": f"/media/{result_path}"
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scan_photo.py path/to/photo.jpg")
        sys.exit(1)
    scan_faces(sys.argv[1])