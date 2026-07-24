"""
enroll.py
Builds watchlist.pkl from wanted_photos/, merging in case metadata from
criminal_records.csv if present.

Supports two photo layouts (can mix both):
  wanted_photos/john_doe.jpg               <- one photo
  wanted_photos/jane_smith/1.jpg, 2.jpg    <- multiple photos, averaged for accuracy

criminal_records.csv format:
  name,case_number,crime,danger_level
  john_doe,2024-0113,Armed Robbery,HIGH

The 'name' column must match the photo filename / folder name (case-insensitive).
People without a matching CSV row are enrolled with "N/A" metadata - the system
still works, it just won't show case details for them.

Run this once whenever you add/update wanted photos or the records CSV.
"""

import os
import csv
import pickle
import cv2
import numpy as np
from insightface.app import FaceAnalysis

import config

RECORDS_CSV = "criminal_records.csv"


def get_embedding(app, image_path):
    img = cv2.imread(image_path)
    if img is None:
        return None
    faces = app.get(img)
    if not faces:
        return None
    faces.sort(key=lambda f: (f.bbox[2]-f.bbox[0]) * (f.bbox[3]-f.bbox[1]), reverse=True)
    return faces[0].normed_embedding


def load_records():
    """Returns dict: lowercased name -> {case_number, crime, danger_level}"""
    records = {}
    if not os.path.exists(RECORDS_CSV):
        print(f"Note: '{RECORDS_CSV}' not found - enrolling without case metadata.")
        return records
    with open(RECORDS_CSV, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name_key = row["name"].strip().lower()
            records[name_key] = {
                "case_number": row.get("case_number", "N/A").strip(),
                "crime": row.get("crime", "N/A").strip(),
                "danger_level": row.get("danger_level", "N/A").strip(),
            }
    print(f"Loaded {len(records)} case record(s) from {RECORDS_CSV}")
    return records


def default_metadata():
    return {"case_number": "N/A", "crime": "N/A", "danger_level": "N/A"}


def enroll_faces(app=None):
    if app is None:
        print("Loading face analysis model (first run downloads ~300MB, be patient)...")
        app = FaceAnalysis(name="buffalo_l", providers=["CPUExecutionProvider"])
        app.prepare(ctx_id=0, det_size=config.DET_SIZE)

    enrolled = []
    skipped = []

    if not os.path.isdir(config.WANTED_PHOTOS_DIR):
        print(f"Error: '{config.WANTED_PHOTOS_DIR}' folder not found. Create it and add photos.")
        return enrolled, skipped

    records = load_records()
    database = {}
    entries = sorted(os.listdir(config.WANTED_PHOTOS_DIR))

    if not entries:
        print(f"'{config.WANTED_PHOTOS_DIR}' is empty. Add photos or per-person folders.")
        return enrolled, skipped

    for entry in entries:
        full_path = os.path.join(config.WANTED_PHOTOS_DIR, entry)

        if os.path.isdir(full_path):
            name = entry
            embeddings = []
            for fname in sorted(os.listdir(full_path)):
                if not fname.lower().endswith((".jpg", ".jpeg", ".png")):
                    continue
                emb = get_embedding(app, os.path.join(full_path, fname))
                if emb is None:
                    skipped.append(f"No face in {entry}/{fname}")
                    print(f"  [skip] No face in {entry}/{fname}")
                    continue
                embeddings.append(emb)

            if not embeddings:
                skipped.append(f"No usable photos for {name}")
                print(f"  [skip] No usable photos for {name}")
                continue

            avg = np.mean(embeddings, axis=0)
            avg = avg / np.linalg.norm(avg)
            metadata = records.get(name.lower(), default_metadata())
            database[name] = {"embedding": avg, **metadata}
            
            enrolled.append({
                "name": name,
                "photo_count": len(embeddings),
                "crime": metadata['crime'],
                "danger_level": metadata['danger_level']
            })
            print(f"  [ok] Enrolled: {name} ({len(embeddings)} photos averaged) "
                  f"- {metadata['crime']} ({metadata['danger_level']})")

        elif entry.lower().endswith((".jpg", ".jpeg", ".png")):
            name = os.path.splitext(entry)[0]
            emb = get_embedding(app, full_path)
            if emb is None:
                skipped.append(f"No face detected in {entry}")
                print(f"  [skip] No face detected in {entry}")
                continue
            metadata = records.get(name.lower(), default_metadata())
            database[name] = {"embedding": emb, **metadata}
            enrolled.append({
                "name": name,
                "photo_count": 1,
                "crime": metadata['crime'],
                "danger_level": metadata['danger_level']
            })
            print(f"  [ok] Enrolled: {name} (1 photo) - {metadata['crime']} ({metadata['danger_level']})")

    if not database:
        print("No one enrolled. Add photos to wanted_photos/ and try again.")
        return enrolled, skipped

    with open(config.DB_PATH, "wb") as f:
        pickle.dump(database, f)

    print(f"\nDone. {len(database)} people enrolled -> saved to {config.DB_PATH}")
    return enrolled, skipped

if __name__ == "__main__":
    enroll_faces()