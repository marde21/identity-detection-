"""
identify_suspect.py
Reverse-search: given an unknown suspect photo, find them in the
population database using FAISS.
"""

import os
import sys
import cv2
import numpy as np
from insightface.app import FaceAnalysis

import config
from db_helpers import search_population_face

RESULTS_DIR = "identification_results"


def get_embedding(app, image_path):
    img = cv2.imread(image_path)
    if img is None:
        return None
    faces = app.get(img)
    if not faces:
        return None
    faces.sort(key=lambda f: (f.bbox[2]-f.bbox[0]) * (f.bbox[3]-f.bbox[1]), reverse=True)
    return faces[0].normed_embedding, img, faces[0].bbox.astype(int)


def identify_faces(suspect_path, app=None):
    if not os.path.exists(suspect_path):
        print(f"Error: file not found: {suspect_path}")
        return None

    if app is None:
        print("Loading face analysis model...")
        app = FaceAnalysis(name="buffalo_l", providers=["CPUExecutionProvider"])
        app.prepare(ctx_id=0, det_size=config.DET_SIZE)

    # Get the suspect's embedding
    result = get_embedding(app, suspect_path)
    if result is None:
        print("Error: no face detected in the suspect photo.")
        return None
    suspect_embedding, suspect_img, suspect_box = result

    # Search against SQLite Population Database using FAISS
    results = search_population_face(suspect_embedding, k=10)
    
    if not results:
        print("No match found in the population database.")
        return None

    best_match = results[0] if results[0]["score"] >= config.SIMILARITY_THRESHOLD else None

    # Save an annotated side-by-side image: suspect photo | best candidate's photo
    os.makedirs(RESULTS_DIR, exist_ok=True)
    cv2.rectangle(suspect_img, (suspect_box[0], suspect_box[1]),
                  (suspect_box[2], suspect_box[3]), (0, 0, 255), 2)
    out_path = os.path.join(RESULTS_DIR, f"result_{os.path.basename(suspect_path)}")
    cv2.imwrite(out_path, suspect_img)
    
    # Extract only the filename part from out_path for the URL
    out_filename = os.path.basename(out_path)
    
    return {
        "best_match": best_match,
        "ranked": results,
        "result_image": f"/media/identification_results/{out_filename}"
    }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python identify_suspect.py suspect_photo.jpg")
        sys.exit(1)
    identify_faces(sys.argv[1])