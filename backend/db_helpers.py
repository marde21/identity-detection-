import os
import sqlite3
import numpy as np
from database import get_db, get_faiss_index, save_faiss_index, get_population_faiss_index, save_population_faiss_index

def search_face(embedding_1d, threshold=0.5):
    """Searches FAISS for a single face embedding and returns metadata if match >= threshold."""
    faiss_index = get_faiss_index()
    if faiss_index.ntotal == 0:
        return None
        
    embedding_2d = np.array([embedding_1d], dtype=np.float32)
    scores, ids = faiss_index.search(embedding_2d, 1)
    
    best_score = float(scores[0][0])
    best_id = int(ids[0][0])
    
    if best_id != -1 and best_score >= threshold:
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT * FROM watchlist WHERE id=?", (best_id,))
        row = c.fetchone()
        conn.close()
        
        if row:
            return {
                "id": row["id"],
                "name": row["name"],
                "case_number": row["case_number"],
                "crime": row["crime"],
                "danger_level": row["danger_level"],
                "similarity": best_score
            }
    return None

def add_person(name, case_number, crime, danger_level, embedding_1d):
    """Adds a person to SQLite and their embedding to FAISS."""
    conn = get_db()
    c = conn.cursor()
    try:
        c.execute('''INSERT INTO watchlist (name, case_number, crime, danger_level) 
                     VALUES (?, ?, ?, ?)''', (name, case_number, crime, danger_level))
        row_id = c.lastrowid
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        raise ValueError(f"Person {name} already exists in database.")
    finally:
        conn.close()
        
    faiss_index = get_faiss_index()
    emb_2d = np.array([embedding_1d], dtype=np.float32)
    id_1d = np.array([row_id], dtype=np.int64)
    faiss_index.add_with_ids(emb_2d, id_1d)
    save_faiss_index(faiss_index)
    return row_id

def delete_person_by_name(name):
    """Deletes a person from SQLite and FAISS."""
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id FROM watchlist WHERE name=?", (name,))
    row = c.fetchone()
    if not row:
        conn.close()
        return False
        
    person_id = row["id"]
    c.execute("DELETE FROM watchlist WHERE id=?", (person_id,))
    conn.commit()
    conn.close()
    
    # Remove from FAISS
    faiss_index = get_faiss_index()
    try:
        faiss_index.remove_ids(np.array([person_id], dtype=np.int64))
        save_faiss_index(faiss_index)
    except Exception as e:
        print(f"Warning: Failed to remove ID {person_id} from FAISS. {e}")
        
    return True

def update_person(old_name, new_name, case_number, crime, danger_level):
    """Updates a person's metadata in SQLite."""
    conn = get_db()
    c = conn.cursor()
    c.execute('''UPDATE watchlist 
                 SET name=?, case_number=?, crime=?, danger_level=?
                 WHERE name=?''', 
              (new_name, case_number, crime, danger_level, old_name))
    conn.commit()
    conn.close()

def search_population_face(embedding_1d, k=10):
    """Searches FAISS population index and returns top k matches."""
    faiss_index = get_population_faiss_index()
    if faiss_index.ntotal == 0:
        return []
        
    embedding_2d = np.array([embedding_1d], dtype=np.float32)
    scores, ids = faiss_index.search(embedding_2d, k)
    
    results = []
    conn = get_db()
    c = conn.cursor()
    
    for i in range(k):
        score = float(scores[0][i])
        pid = int(ids[0][i])
        if pid != -1:
            c.execute("SELECT name, photo_url FROM population WHERE id=?", (pid,))
            row = c.fetchone()
            if row:
                results.append({
                    "id": pid,
                    "name": row["name"],
                    "photo_url": row["photo_url"],
                    "score": score
                })
    conn.close()
    return results

def add_population_person(name, photo_url, embedding_1d):
    """Adds a person to SQLite population table and FAISS index."""
    conn = get_db()
    c = conn.cursor()
    try:
        c.execute('''INSERT INTO population (name, photo_url) VALUES (?, ?)''', (name, photo_url))
        row_id = c.lastrowid
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        # Already exists, just return the existing ID
        c = get_db().cursor()
        c.execute("SELECT id FROM population WHERE name=?", (name,))
        row_id = c.fetchone()["id"]
        return row_id
    finally:
        conn.close()
        
    faiss_index = get_population_faiss_index()
    emb_2d = np.array([embedding_1d], dtype=np.float32)
    id_1d = np.array([row_id], dtype=np.int64)
    faiss_index.add_with_ids(emb_2d, id_1d)
    save_population_faiss_index(faiss_index)
    return row_id
