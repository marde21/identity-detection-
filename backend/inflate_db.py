import os
import pickle
import numpy as np
import config

print(f"Loading {config.DB_PATH}...")
if os.path.exists(config.DB_PATH):
    with open(config.DB_PATH, "rb") as f:
        db = pickle.load(f)
else:
    db = {}

current_count = len(db)
target_count = 100000
needed = target_count - current_count

if needed > 0:
    print(f"Current population: {current_count}. Generating {needed} mock vectors to reach {target_count}...")
    
    # Generate random normalized 512-dim vectors in batch for speed
    print("Generating random vectors (this will take a few seconds)...")
    np.random.seed(42) # For reproducibility
    batch_size = needed
    random_vectors = np.random.randn(batch_size, 512).astype(np.float32)
    # Normalize vectors
    norms = np.linalg.norm(random_vectors, axis=1, keepdims=True)
    random_vectors = random_vectors / norms
    
    print("Adding to database...")
    for i in range(needed):
        name = f"Mock Citizen {i+1}"
        db[name] = {
            "embedding": random_vectors[i],
            "case_number": "N/A",
            "crime": "N/A",
            "danger_level": "LOW"
        }
        
    print(f"Saving {len(db)} total records to {config.DB_PATH}...")
    with open(config.DB_PATH, "wb") as f:
        pickle.dump(db, f)
        
    print("Success! Database inflated to 100,000 people.")
else:
    print(f"Database already has {current_count} people. No need to inflate.")
