import os
import sqlite3
import numpy as np
import pandas as pd
import chromadb
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda, RunnablePassthrough

load_dotenv()

CHROMA_DIR  = "chroma_store"
DB_PATH     = "song_dna.db"
MODEL       = "paraphrase-multilingual-MiniLM-L12-v2"
GROQ_MODEL  = "llama-3.1-8b-instant"
TOP_K       = 5
W_SENTIMENT = 0.5
W_DSP       = 0.3
W_ENERGY    = 0.2

_embedder = None
def get_embedder():
    global _embedder
    if _embedder is None:
        _embedder = SentenceTransformer(MODEL)
    return _embedder
client     = chromadb.PersistentClient(path=CHROMA_DIR)
collection = client.get_or_create_collection(
    name="evaris_songs",
    metadata={"hnsw:space": "cosine"}
)
llm        = ChatGroq(api_key=os.getenv("GROQ_API_KEY"), model=GROQ_MODEL, temperature=0.4)

expand_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a music mood interpreter. Convert the user's message into a rich 
2-3 sentence emotional scene description for music matching. 
Return ONLY the scene description, no preamble."""),
    ("human", "{query}")
])

explain_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a music recommendation assistant. Given a user's mood and a list 
of recommended songs with their emotional descriptions, write a brief 1-2 sentence 
explanation for why each song fits. Be warm, specific, and concise.
Format: Song Name — explanation"""),
    ("human", "User mood: {query}\n\nRecommended songs:\n{songs}")
])

expand_chain  = expand_prompt | llm | StrOutputParser()
explain_chain = explain_prompt | llm | StrOutputParser()

def retrieve(expanded_query: str, user_energy: float = 0.5):
    query_vec = get_embedder().encode([expanded_query])[0].tolist()
    results   = collection.query(query_embeddings=[query_vec], n_results=TOP_K)

    con     = sqlite3.connect(DB_PATH)
    dsp_df  = pd.read_sql("SELECT song, artist, rms_energy FROM audio_features", con)
    con.close()

    rms_max = dsp_df["rms_energy"].max() if not dsp_df.empty else 1.0
    rms_min = dsp_df["rms_energy"].min() if not dsp_df.empty else 0.0

    songs = []
    for i, meta in enumerate(results["metadatas"][0]):
        sentiment_score = 1 / (1 + results["distances"][0][i])
        dsp_row = dsp_df[(dsp_df["song"] == meta["song"]) & (dsp_df["artist"] == meta["artist"])]

        if not dsp_row.empty:
            rms      = dsp_row.iloc[0]["rms_energy"]
            rms_norm = (rms - rms_min) / (rms_max - rms_min + 1e-9)
            e_match  = 1.0 - abs(rms_norm - user_energy)
            score    = (W_SENTIMENT * sentiment_score) + (W_DSP * rms_norm) + (W_ENERGY * e_match)
            has_dsp  = True
        else:
            score   = sentiment_score
            has_dsp = False

        songs.append({
            "song"    : meta["song"],
            "artist"  : meta["artist"],
            "score"   : round(score, 4),
            "doc"     : results["documents"][0][i],
            "has_dsp" : has_dsp
        })

    return sorted(songs, key=lambda x: x["score"], reverse=True)

def run_rag(query: str, user_energy: float = 0.5):
    print(f"\n🔍 Expanding query: \"{query}\"")
    expanded = expand_chain.invoke({"query": query})
    print(f"📝 Expanded: {expanded}\n")

    songs = retrieve(expanded, user_energy)

    songs_context = "\n".join([
        f"{i+1}. {s['song']} by {s['artist']} (score: {s['score']})\n   Context: {s['doc'][:200]}"
        for i, s in enumerate(songs)
    ])

    explanation = explain_chain.invoke({"query": query, "songs": songs_context})

    return {"songs": songs, "expanded_query": expanded, "explanation": explanation}

if __name__ == "__main__":
    query      = input("Describe your mood: ")
    energy_raw = input("Energy level (1-10, Enter to skip): ").strip()
    energy     = int(energy_raw) / 10 if energy_raw.isdigit() else 0.5

    result = run_rag(query, energy)

    print(f"\n🎵 Top {TOP_K} matches:\n")
    print(f"{'Rank':<6}{'Score':<10}{'DSP':<6}{'Song':<35}{'Artist'}")
    print("─" * 80)
    for i, s in enumerate(result["songs"], 1):
        print(f"{i:<6}{s['score']:<10}{'✅' if s['has_dsp'] else '—':<6}{s['song']:<35}{s['artist']}")

    print(f"\n💬 Why these songs?\n{result['explanation']}")