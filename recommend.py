import sqlite3
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer

DB_PATH = "song_dna.db"
MODEL   = "paraphrase-multilingual-MiniLM-L12-v2"
TOP_N   = 5

W_SENTIMENT = 0.5
W_DSP       = 0.3
W_ENERGY    = 0.2

def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def energy_match(rms, user_energy_norm):
    return 1.0 - abs(rms - user_energy_norm)

def recommend(query: str, user_energy: float = None):
    con     = sqlite3.connect(DB_PATH)
    emb_df  = pd.read_sql("SELECT song, artist, embedding_json FROM sentiment_embeddings", con)
    dsp_df  = pd.read_sql("SELECT song, artist, tempo_bpm, key, rms_energy FROM audio_features", con)
    con.close()

    model     = SentenceTransformer(MODEL)
    query_vec = model.encode([query])[0]

    rms_max = dsp_df["rms_energy"].max() if not dsp_df.empty else 1.0
    rms_min = dsp_df["rms_energy"].min() if not dsp_df.empty else 0.0

    scores = []
    for _, row in emb_df.iterrows():
        emb            = np.array(eval(row["embedding_json"]))
        sentiment_score = float(cosine_similarity(query_vec, emb))

        dsp_row = dsp_df[(dsp_df["song"] == row["song"]) & (dsp_df["artist"] == row["artist"])]

        if not dsp_row.empty and user_energy is not None:
            rms      = dsp_row.iloc[0]["rms_energy"]
            rms_norm = (rms - rms_min) / (rms_max - rms_min + 1e-9)
            e_match  = energy_match(rms_norm, user_energy)
            dsp_score = rms_norm
            final    = (W_SENTIMENT * sentiment_score) + (W_DSP * dsp_score) + (W_ENERGY * e_match)
            has_dsp  = True
        else:
            final   = sentiment_score
            has_dsp = False

        scores.append({
            "song"   : row["song"],
            "artist" : row["artist"],
            "score"  : round(final, 4),
            "has_dsp": has_dsp
        })

    results = sorted(scores, key=lambda x: x["score"], reverse=True)[:TOP_N]

    print(f"\n🎵 Top {TOP_N} matches for: \"{query}\" | Energy: {int(user_energy*10) if user_energy else 'N/A'}/10\n")
    print(f"{'Rank':<6}{'Score':<10}{'DSP':<6}{'Song':<35}{'Artist'}")
    print("─" * 80)
    for i, r in enumerate(results, 1):
        dsp_tag = "✅" if r["has_dsp"] else "—"
        print(f"{i:<6}{r['score']:<10}{dsp_tag:<6}{r['song']:<35}{r['artist']}")

if __name__ == "__main__":
    query      = input("Describe your current mood or scene: ")
    energy_raw = input("Energy level (1-10, or press Enter to skip): ").strip()
    user_energy = int(energy_raw) / 10 if energy_raw.isdigit() else None
    recommend(query, user_energy)