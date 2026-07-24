"""
identify_suspect.py
Reverse-search use case: you have ONE unknown photo (e.g. a suspect caught on
camera) and want to find out WHO they are by comparing against a database of
known people (e.g. everyone registered in a village).

Usage:
  python identify_suspect.py suspect_photo.jpg

Looks for known people's photos in village_photos/, same layout as enroll.py:
  village_photos/person_name.jpg                 <- one photo
  village_photos/person_name/1.jpg, 2.jpg ...    <- multiple photos, averaged
"""

import os
import sys
import pickle
import cv2
import numpy as np
from insightface.app import FaceAnalysis

import config

VILLAGE_PHOTOS_DIR = "village_photos"
VILLAGE_DB_PATH = "village_database.pkl"
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


def build_village_database(app):
    """Same logic as enroll.py, but for the village population, not the wanted list."""
    print(f"Building village database from '{VILLAGE_PHOTOS_DIR}'...")
    database = {}
    entries = sorted(os.listdir(VILLAGE_PHOTOS_DIR))

    for entry in entries:
        full_path = os.path.join(VILLAGE_PHOTOS_DIR, entry)

        if os.path.isdir(full_path):
            name = entry
            embeddings = []
            for fname in sorted(os.listdir(full_path)):
                if not fname.lower().endswith((".jpg", ".jpeg", ".png")):
                    continue
                result = get_embedding(app, os.path.join(full_path, fname))
                if result is None:
                    print(f"  [skip] No face in {entry}/{fname}")
                    continue
                embeddings.append(result[0])
            if not embeddings:
                continue
            avg = np.mean(embeddings, axis=0)
            avg = avg / np.linalg.norm(avg)
            database[name] = avg
            print(f"  [ok] Added: {name} ({len(embeddings)} photos)")

        elif entry.lower().endswith((".jpg", ".jpeg", ".png")):
            name = os.path.splitext(entry)[0]
            result = get_embedding(app, full_path)
            if result is None:
                print(f"  [skip] No face detected in {entry}")
                continue
            database[name] = result[0]
            print(f"  [ok] Added: {name} (1 photo)")

    with open(VILLAGE_DB_PATH, "wb") as f:
        pickle.dump(database, f)
    print(f"Village database built: {len(database)} people -> {VILLAGE_DB_PATH}\n")
    return database


def identify_faces(suspect_path, app=None):
    if not os.path.exists(suspect_path):
        print(f"Error: file not found: {suspect_path}")
        return None

    if app is None:
        print("Loading face analysis model...")
        app = FaceAnalysis(name="buffalo_l", providers=["CPUExecutionProvider"])
        app.prepare(ctx_id=0, det_size=config.DET_SIZE)

    # Build (or rebuild) the village database from photos each run, so it always
    # reflects the current contents of village_photos/. For large villages you
    # could cache this and only rebuild when photos change.
    if not os.path.isdir(VILLAGE_PHOTOS_DIR):
        print(f"Error: '{VILLAGE_PHOTOS_DIR}' folder not found. Add village photos there first.")
        return None
        
    if os.path.exists(VILLAGE_DB_PATH):
        with open(VILLAGE_DB_PATH, "rb") as f:
            village_db = pickle.load(f)
    else:
        village_db = build_village_database(app)

    if not village_db:
        print("No village photos could be enrolled. Check your photos.")
        return None

    names = list(village_db.keys())
    embeddings = np.array(list(village_db.values()))

    # Get the suspect's embedding
    result = get_embedding(app, suspect_path)
    if result is None:
        print("Error: no face detected in the suspect photo.")
        return None
    suspect_embedding, suspect_img, suspect_box = result

    # Compare against every villager, ranked best to worst
    similarities = embeddings @ suspect_embedding
    ranked = sorted(zip(names, similarities), key=lambda x: x[1], reverse=True)

    print("--- Identification results (ranked by similarity) ---")
    for name, score in ranked[:10]:  # top 10
        flag = " <- LIKELY MATCH" if score >= config.SIMILARITY_THRESHOLD else ""
        print(f"  {name}: {score:.3f}{flag}")

    best_name, best_score = ranked[0]
    print()
    if best_score >= config.SIMILARITY_THRESHOLD:
        print(f"RESULT: Suspect identified as '{best_name}' (confidence={best_score:.3f})")
    else:
        print(f"RESULT: No confident match found. Closest candidate was '{best_name}' "
              f"(confidence={best_score:.3f}, below threshold {config.SIMILARITY_THRESHOLD}) — "
              f"treat as unidentified.")

    # Save an annotated side-by-side image: suspect photo | best candidate's photo
    os.makedirs(RESULTS_DIR, exist_ok=True)
    cv2.rectangle(suspect_img, (suspect_box[0], suspect_box[1]),
                  (suspect_box[2], suspect_box[3]), (0, 0, 255), 2)
    out_path = os.path.join(RESULTS_DIR, f"result_{os.path.basename(suspect_path)}")
    cv2.imwrite(out_path, suspect_img)
    print(f"\nAnnotated suspect photo saved to: {out_path}")
    
    formatted_ranked = [{"name": n, "score": float(s)} for n, s in ranked[:10]]
    best_match = formatted_ranked[0] if best_score >= config.SIMILARITY_THRESHOLD else None
    
    return {
        "best_match": best_match,
        "ranked": formatted_ranked,
        "result_image": out_path
    }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python identify_suspect.py suspect_photo.jpg")
        sys.exit(1)
    identify_faces(sys.argv[1])