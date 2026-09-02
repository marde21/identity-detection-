import sqlite3
import faiss
import os
import numpy as np

# We ensure we are in the backend/ directory or root directory.
# Since app.py chdirs into backend/, we can use relative paths safely.
DATA_DIR = "data"
SQLITE_DB = os.path.join(DATA_DIR, "system.sqlite")
FAISS_DB = os.path.join(DATA_DIR, "index.faiss")
POPULATION_FAISS_DB = os.path.join(DATA_DIR, "population_index.faiss")

def init_db():
    os.makedirs(DATA_DIR, exist_ok=True)
    
    # Initialize SQLite
    conn = sqlite3.connect(SQLITE_DB)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS watchlist
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT UNIQUE,
                  case_number TEXT,
                  crime TEXT,
                  danger_level TEXT)''')
                  
    c.execute('''CREATE TABLE IF NOT EXISTS population
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT UNIQUE,
                  photo_url TEXT)''')
                  
    c.execute('''CREATE TABLE IF NOT EXISTS cameras
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT,
                  source TEXT)''')
                  
    c.execute('''CREATE TABLE IF NOT EXISTS alert_logs
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  watchlist_id INTEGER,
                  camera_id INTEGER,
                  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                  confidence REAL,
                  photo_path TEXT,
                  FOREIGN KEY(watchlist_id) REFERENCES watchlist(id))''')
                  
    # Seed default camera if empty
    c.execute("SELECT COUNT(*) FROM cameras")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO cameras (name, source) VALUES (?, ?)", ("Main Gate (USB)", "0"))
        
    conn.commit()
    conn.close()

    # Initialize FAISS (512 dimensions for InsightFace, Inner Product for cosine similarity)
    if not os.path.exists(FAISS_DB):
        index = faiss.IndexFlatIP(512)
        index = faiss.IndexIDMap(index)
        faiss.write_index(index, FAISS_DB)
        
    if not os.path.exists(POPULATION_FAISS_DB):
        pop_index = faiss.IndexFlatIP(512)
        pop_index = faiss.IndexIDMap(pop_index)
        faiss.write_index(pop_index, POPULATION_FAISS_DB)

def get_db():
    conn = sqlite3.connect(SQLITE_DB)
    conn.row_factory = sqlite3.Row
    return conn

def get_faiss_index():
    if not os.path.exists(FAISS_DB):
        init_db()
    return faiss.read_index(FAISS_DB)

def save_faiss_index(index):
    faiss.write_index(index, FAISS_DB)

def get_population_faiss_index():
    if not os.path.exists(POPULATION_FAISS_DB):
        init_db()
    return faiss.read_index(POPULATION_FAISS_DB)

def save_population_faiss_index(index):
    faiss.write_index(index, POPULATION_FAISS_DB)
