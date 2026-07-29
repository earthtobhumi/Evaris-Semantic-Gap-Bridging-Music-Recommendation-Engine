import sqlite3
import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer

DB_PATH = "song_dna.db"
MODEL   = "paraphrase-multilingual-MiniLM-L12-v2"

con = sqlite3.connect(DB_PATH)
df  = pd.read_sql(
    "SELECT song, artist, primary_vibe, secondary_vibe, scene_description, personal_notes FROM songs",
    con
)

# adding vibe tags here too — scene descriptions alone were pulling in
# happy rain songs for sad rain queries since they share so much imagery
df["combined_text"] = (
    df["primary_vibe"].fillna("") + " " +
    df["secondary_vibe"].fillna("") + " " +
    df["scene_description"].fillna("") + " " +
    df["personal_notes"].fillna("")
).str.strip()

print(f"🔤 Encoding {len(df)} tracks with {MODEL}...")
model      = SentenceTransformer(MODEL)
embeddings = model.encode(df["combined_text"].tolist(), show_progress_bar=True)

records = []
for i, row in df.iterrows():
    records.append({
        "song"           : row["song"],
        "artist"         : row["artist"],
        "combined_text"  : row["combined_text"],
        "embedding_json" : str(embeddings[i].tolist())
    })

emb_df = pd.DataFrame(records)
emb_df.to_sql("sentiment_embeddings", con, if_exists="replace", index=False)

count = pd.read_sql("SELECT COUNT(*) as n FROM sentiment_embeddings", con).iloc[0,0]
print(f"✅ {count} embeddings written → sentiment_embeddings table in {DB_PATH}")
print(f"📐 Embedding dimensions: {embeddings.shape[1]}")
con.close()