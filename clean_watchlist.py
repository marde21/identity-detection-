import os
import sqlite3
import numpy as np
import faiss
from insightface.app import FaceAnalysis

# Initialize FaceAnalysis to get embeddings
app = FaceAnalysis(name="buffalo_l", providers=["CPUExecutionProvider"])
app.prepare(ctx_id=0, det_size=(640, 640))

db_path = 'backend/data/system.sqlite'
faiss_path = 'backend/data/index.faiss'
photos_dir = 'backend/wanted_photos'

conn = sqlite3.connect(db_path)
c = conn.cursor()

# 1. Delete Mock Citizens from watchlist table
c.execute("DELETE FROM watchlist WHERE name LIKE 'Mock Citizen%'")
print(f"Deleted Mock Citizens.")
conn.commit()

# 2. Get remaining valid watchlist users
c.execute("SELECT id, name FROM watchlist")
valid_users = c.fetchall()
print(f"Valid users: {valid_users}")

# 3. Rebuild index.faiss
import cv2

# Create new index
index = faiss.IndexFlatIP(512)
index = faiss.IndexIDMap(index)

for uid, name in valid_users:
    folder = os.path.join(photos_dir, name)
    if os.path.exists(folder):
        for fname in os.listdir(folder):
            if fname.lower().endswith(('.jpg', '.jpeg', '.png')):
                img_path = os.path.join(folder, fname)
                img = cv2.imread(img_path)
                if img is not None:
                    faces = app.get(img)
                    if faces:
                        faces = sorted(faces, key=lambda x: (x.bbox[2]-x.bbox[0])*(x.bbox[3]-x.bbox[1]), reverse=True)
                        emb = faces[0].normed_embedding
                        emb_2d = np.array([emb], dtype=np.float32)
                        id_1d = np.array([uid], dtype=np.int64)
                        index.add_with_ids(emb_2d, id_1d)
                        print(f"Added {name} to FAISS")
                        break

faiss.write_index(index, faiss_path)
print("Saved clean index.faiss")
conn.close()
