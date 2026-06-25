# Evaris

Evaris is a semantic music recommendation system that recommends songs based on emotion, atmosphere, and context instead of genres or listening history.

The project combines multilingual sentence embeddings, human-curated emotional metadata, audio signal processing, and crowd sentiment to understand what a song *feels* like and match it with a user's natural language description.

---

## Features

- Semantic search using natural language
- Human-curated Song DNA dataset
- Multilingual sentence embeddings
- Audio feature extraction (tempo, key, RMS energy)
- Reddit-based crowd sentiment enrichment
- Hybrid recommendation engine combining NLP and DSP
- Streamlit interface with recommendation explanations

---

## How It Works

```text
User Input
     │
     ▼
Sentence Transformer
     │
     ▼
Query Embedding
     │
     ▼
Compare Against Song Database
     ├── Semantic Embeddings
     ├── Audio Features
     └── Crowd Sentiment
     │
     ▼
Hybrid Ranking
     │
     ▼
Top Recommendations
```

---

## Tech Stack

| Category | Technologies |
|----------|--------------|
| Language | Python |
| NLP | Sentence Transformers |
| Audio Processing | Librosa |
| Backend | FastAPI |
| Frontend | Streamlit |
| Database | SQLite |
| Data Processing | Pandas, NumPy |

---

## Project Structure

```text
Evaris/
│
├── app.py
├── recommend.py
├── nlp_embed.py
├── reddit_blend.py
├── dsp_extract.py
├── ingest_song_dna.py
├── audio_features_insert.py
│
├── audio/
├── song_dna.db
└── README.md
```

---

## Current Status

The current prototype includes:

- Semantic recommendation engine
- Hybrid scoring using embeddings and audio features
- Human-curated multilingual song database
- Reddit sentiment enrichment
- Streamlit frontend

The next milestone is expanding the curated dataset before integrating larger music catalogues.

---

## Roadmap

- Expand the Song DNA database
- Improve hybrid scoring
- Playlist generation
- Spotify integration
- Production deployment

---

## Motivation

Most music recommendation systems answer:

> "People who listened to this also liked..."

Evaris explores a different approach by recommending songs based on emotional similarity rather than listening behaviour.

The long-term goal is to build a recommendation system that understands the emotional character of music instead of relying primarily on collaborative filtering.

docs: update README with comprehensive system architecture