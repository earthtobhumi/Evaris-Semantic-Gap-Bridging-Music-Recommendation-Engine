import sqlite3
import requests
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
from time import sleep

DB_PATH   = "song_dna.db"
MODEL     = "paraphrase-multilingual-MiniLM-L12-v2"
MAX_POSTS = 10
MAX_COMMENTS = 30
W_PERSONAL = 0.7
W_CROWD    = 0.3

def fetch_reddit_comments(song, artist):
    query    = f"{song} {artist}"
    url      = f"https://api.pullpush.io/reddit/search/comment/?q={requests.utils.quote(query)}&size={MAX_COMMENTS}"
    try:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        data = r.json().get("data", [])
        comments = [d["body"] for d in data if len(d.get("body","")) > 20]
        return " ".join(comments[:MAX_COMMENTS])
    except Exception as e:
        print(f"  ⚠️  PullPush error for {song}: {e}")
        return ""

def blend(personal_vec, crowd_vec):
    blended = (W_PERSONAL * personal_vec) + (W_CROWD * crowd_vec)
    return blended / np.linalg.norm(blended)

con    = sqlite3.connect(DB_PATH)
df     = pd.read_sql("SELECT song, artist, embedding_json FROM sentiment_embeddings", con)
model  = SentenceTransformer(MODEL)

updated = 0
for _, row in df.iterrows():
    print(f"🔍 Fetching Reddit comments: {row['song']} — {row['artist']}")
    crowd_text = fetch_reddit_comments(row["song"], row["artist"])

    if not crowd_text.strip():
        print(f"  ⏭️  No comments found, keeping personal embedding.")
        continue

    personal_vec = np.array(eval(row["embedding_json"]))
    crowd_vec    = model.encode([crowd_text])[0]
    blended_vec  = blend(personal_vec, crowd_vec)

    con.execute(
        "UPDATE sentiment_embeddings SET embedding_json = ? WHERE song = ? AND artist = ?",
        (str(blended_vec.tolist()), row["song"], row["artist"])
    )
    con.commit()
    updated += 1
    print(f"  ✅ Blended embedding updated.")
    sleep(1)

print(f"\n🎵 {updated}/{len(df)} embeddings enriched with Reddit crowd sentiment.")
con.close()