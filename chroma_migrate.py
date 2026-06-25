import sqlite3
import pandas as pd
import chromadb
from chromadb.config import Settings

DB_PATH    = "song_dna.db"
CHROMA_DIR = "chroma_store"

con = sqlite3.connect(DB_PATH)
df  = pd.read_sql("SELECT song, artist, combined_text, embedding_json FROM sentiment_embeddings", con)
con.close()

client     = chromadb.PersistentClient(path=CHROMA_DIR)
collection = client.get_or_create_collection(
    name="evaris_songs",
    metadata={"hnsw:space": "cosine"}
)

for _, row in df.iterrows():
    embedding = eval(row["embedding_json"])
    collection.upsert(
        ids        =[f"{row['song']}_{row['artist']}"],
        embeddings =[embedding],
        documents  =[row["combined_text"]],
        metadatas  =[{"song": row["song"], "artist": row["artist"]}]
    )
    print(f"✅ Migrated: {row['song']} — {row['artist']}")

print(f"\n🎵 {collection.count()} tracks in ChromaDB → {CHROMA_DIR}/")