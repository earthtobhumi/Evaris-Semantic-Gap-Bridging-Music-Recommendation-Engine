import os
import numpy as np
import pandas as pd
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import text
from db import engine
from rag_chain import run_rag

load_dotenv()

app = FastAPI(title="Evaris API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

class RecommendRequest(BaseModel):
    mood        : str
    energy_level: int = 5

class RecommendResponse(BaseModel):
    expanded_query: str
    explanation   : str
    songs         : list[dict]

@app.get("/health")
def health():
    return {"status": "online", "service": "Evaris API", "version": "1.0"}

@app.get("/songs")
def get_songs():
    with engine.connect() as con:
        df = pd.read_sql("SELECT song, artist, language, genre, primary_vibe FROM songs", con)
    return df.to_dict(orient="records")

@app.get("/songs/{song_name}")
def get_song(song_name: str):
    with engine.connect() as con:
        df = pd.read_sql(
            text("SELECT * FROM songs WHERE LOWER(song) = LOWER(:name)"),
            con, params={"name": song_name}
        )
    if df.empty:
        raise HTTPException(status_code=404, detail=f"Song '{song_name}' not found")
    return df.iloc[0].to_dict()

@app.get("/audio-features")
def get_audio_features():
    with engine.connect() as con:
        df = pd.read_sql("SELECT * FROM audio_features", con)
    return df.to_dict(orient="records")

@app.post("/recommend", response_model=RecommendResponse)
def recommend(req: RecommendRequest):
    if not req.mood.strip():
        raise HTTPException(status_code=400, detail="Mood cannot be empty")
    user_energy = max(1, min(10, req.energy_level)) / 10
    result      = run_rag(req.mood.strip(), user_energy)
    return RecommendResponse(
        expanded_query=result["expanded_query"],
        explanation   =result["explanation"],
        songs         =result["songs"]
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)