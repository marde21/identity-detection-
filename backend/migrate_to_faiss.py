import os
import sys
import pickle
import numpy as np

# Ensure CWD is backend/
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import init_db, get_db, get_faiss_index, save_faiss_index

def migrate():
    print("Initializing SQLite and FAISS databases...")
    init_db()
    conn = get_db()
    c = conn.cursor()
    
    # Check if watchlist is already populated
    c.execute("SELECT COUNT(*) FROM watchlist")
    if c.fetchone()[0] > 0:
        print("Database already populated. Exiting.")
        return

    pkl_path = "watchlist.pkl"
    if not os.path.exists(pkl_path):
        print(f"Error: {pkl_path} not found.")
        return

    print(f"Loading data from {pkl_path} (this might take a few seconds)...")
    with open(pkl_path, "rb") as f:
        db = pickle.load(f)

    names = list(db.keys())
    print(f"Found {len(names)} records. Migrating to SQLite and FAISS...")

    embeddings = []
    ids = []

    # Insert into SQLite first to get the auto-increment IDs
    for i, name in enumerate(names):
        record = db[name]
        case_number = record.get("case_number", "N/A")
        crime = record.get("crime", "N/A")
        danger_level = record.get("danger_level", "LOW")
        
        c.execute('''INSERT INTO watchlist (name, case_number, crime, danger_level) 
                     VALUES (?, ?, ?, ?)''', (name, case_number, crime, danger_level))
        
        row_id = c.lastrowid
        ids.append(row_id)
        embeddings.append(record["embedding"])
        
        if (i+1) % 10000 == 0:
            print(f"  Inserted {i+1} / {len(names)} into SQLite...")
            
    conn.commit()
    conn.close()

    # Add to FAISS index
    print("Adding vectors to FAISS index...")
    faiss_index = get_faiss_index()
    
    # Ensure vectors are float32 and 2D array
    embeddings_np = np.array(embeddings, dtype=np.float32)
    ids_np = np.array(ids, dtype=np.int64)
    
    # Check shape
    if embeddings_np.ndim == 1 and len(embeddings_np) == 0:
        print("No embeddings found.")
    else:
        # If it was a list of (512,) it becomes (N, 512)
        # Verify shape
        print(f"Embeddings shape: {embeddings_np.shape}, IDs shape: {ids_np.shape}")
        
        # Add with IDs
        faiss_index.add_with_ids(embeddings_np, ids_np)
        save_faiss_index(faiss_index)
        
        print(f"Successfully added {faiss_index.ntotal} vectors to FAISS index.")
        print("Migration complete!")

if __name__ == "__main__":
    migrate()
