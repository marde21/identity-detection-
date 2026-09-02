import os
import pickle
import sys

# Ensure we are in the correct directory
current_dir = os.path.dirname(os.path.abspath(__file__))
if not current_dir.endswith("backend"):
    os.chdir(os.path.join(current_dir, "backend"))
else:
    os.chdir(current_dir)

from database import init_db
from db_helpers import add_population_person

VILLAGE_DB_PATH = "village_database.pkl"

def migrate():
    print("Initializing databases...")
    init_db()
    
    if not os.path.exists(VILLAGE_DB_PATH):
        print(f"No {VILLAGE_DB_PATH} found. Nothing to migrate.")
        return
        
    print(f"Loading {VILLAGE_DB_PATH}...")
    with open(VILLAGE_DB_PATH, "rb") as f:
        village_db = pickle.load(f)
        
    print(f"Found {len(village_db)} people in pickle file.")
    print("Migrating to SQLite and FAISS...")
    
    count = 0
    for name, embedding in village_db.items():
        # Look for photo in village_photos/
        photo_url = f"/api/photo/{name}"  # Fallback to the existing endpoint if we don't know the exact path
        
        try:
            add_population_person(name, photo_url, embedding)
            count += 1
        except Exception as e:
            print(f"Error migrating {name}: {e}")
            
    print(f"Successfully migrated {count} people to the new population database!")

if __name__ == "__main__":
    migrate()
