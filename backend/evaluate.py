"""
evaluate.py
Measures how well the system distinguishes watchlist people from strangers.
This produces real precision/recall numbers you can show in your competition report.

Setup (run enroll.py first):
  test_photos/
    known/      <- DIFFERENT photos of people who ARE in wanted_photos
                   (not the same photo used to enroll them - that would be an unfair test)
    unknown/    <- photos of people who are NOT in wanted_photos

Run: python evaluate.py
"""

import os
import pickle
import cv2
import numpy as np
from insightface.app import FaceAnalysis

import config

TEST_DIR = "test_photos"
KNOWN_DIR = os.path.join(TEST_DIR, "known")
UNKNOWN_DIR = os.path.join(TEST_DIR, "unknown")


def score_folder(app, folder, embeddings):
    """Returns list of best-match similarity scores for every face found in folder."""
    scores = []
    if not os.path.isdir(folder):
        return scores
    for fname in sorted(os.listdir(folder)):
        if not fname.lower().endswith((".jpg", ".jpeg", ".png")):
            continue
        img = cv2.imread(os.path.join(folder, fname))
        if img is None:
            continue
        faces = app.get(img)
        if not faces:
            print(f"  [skip] No face detected in {fname}")
            continue
        emb = faces[0].normed_embedding
        best_score = float((embeddings @ emb).max()) if len(embeddings) else 0.0
        scores.append((fname, best_score))
    return scores


def main():
    if not os.path.exists(config.DB_PATH):
        print("Run enroll.py first to build watchlist.pkl.")
        return

    with open(config.DB_PATH, "rb") as f:
        db = pickle.load(f)
    embeddings = np.array(list(db.values()))

    if not os.path.isdir(KNOWN_DIR) and not os.path.isdir(UNKNOWN_DIR):
        print(f"Create '{KNOWN_DIR}' and '{UNKNOWN_DIR}' with test photos first. See file header for layout.")
        return

    print("Loading face analysis model...")
    app = FaceAnalysis(name="buffalo_l", providers=["CPUExecutionProvider"])
    app.prepare(ctx_id=0, det_size=config.DET_SIZE)

    print(f"\nThreshold being tested: {config.SIMILARITY_THRESHOLD}\n")

    known_scores = score_folder(app, KNOWN_DIR, embeddings)
    unknown_scores = score_folder(app, UNKNOWN_DIR, embeddings)

    true_positives = sum(1 for _, s in known_scores if s >= config.SIMILARITY_THRESHOLD)
    false_negatives = sum(1 for _, s in known_scores if s < config.SIMILARITY_THRESHOLD)
    false_positives = sum(1 for _, s in unknown_scores if s >= config.SIMILARITY_THRESHOLD)
    true_negatives = sum(1 for _, s in unknown_scores if s < config.SIMILARITY_THRESHOLD)

    print("--- Per-photo results ---")
    for fname, s in known_scores:
        status = "MATCH (correct)" if s >= config.SIMILARITY_THRESHOLD else "MISSED (should have matched)"
        print(f"  known/{fname}: score={s:.3f}  -> {status}")
    for fname, s in unknown_scores:
        status = "FALSE ALARM (wrongly matched)" if s >= config.SIMILARITY_THRESHOLD else "correctly ignored"
        print(f"  unknown/{fname}: score={s:.3f}  -> {status}")

    print("\n--- Summary ---")
    print(f"True positives (correct matches):    {true_positives}")
    print(f"False negatives (missed matches):    {false_negatives}")
    print(f"True negatives (correctly ignored):  {true_negatives}")
    print(f"False positives (wrong alerts):      {false_positives}")

    precision = (true_positives / (true_positives + false_positives)
                 if (true_positives + false_positives) else None)
    recall = (true_positives / (true_positives + false_negatives)
              if (true_positives + false_negatives) else None)

    print(f"\nPrecision: {precision:.2%}" if precision is not None else "\nPrecision: N/A (no positive predictions)")
    print(f"Recall:    {recall:.2%}" if recall is not None else "Recall:    N/A (no known/ test photos found)")


if __name__ == "__main__":
    main()