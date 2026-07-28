# Evaris

Evaris is a semantic music recommendation system that recommends songs based on emotion, atmosphere, and context — instead of genre tags or listening history.

It combines multilingual sentence embeddings, a human-curated emotional metadata dataset, audio signal processing, and crowd sentiment to understand what a song *feels* like, and match it against a user's natural-language description of their mood.

---

## Motivation

Most music recommendation systems answer one question:

> "People who listened to this also liked..."

That's collaborative filtering — it works well at scale, but it needs your listening history, and it has nothing to say about *why* a song fits a moment. It can't take "I miss my hometown and it's raining" and understand that as an emotional query.

Evaris takes a different starting point: instead of behavior, it models the **emotional character of a song directly** — its mood, its energy, its atmosphere — and matches that against how a person describes what they're feeling, in their own words, in any of several languages. The goal isn't to replace collaborative filtering, but to explore what a recommendation engine looks like when it's built around emotional similarity instead of listening behavior.

Every song in the dataset isn't just tagged with a genre — it's manually described (scene, vibe, energy, personal notes) by a human listener, then embedded into vector space alongside the semantic meaning of what the user typed. The system is trying to bridge the gap between how a person describes a feeling and how a song actually sounds and feels.

---

## Architecture

Evaris is built as three connected layers:

- **Data layer** — a human-curated "Song DNA" dataset, enriched by three independent signal sources: semantic embeddings of scene descriptions, audio signal features extracted directly from the tracks (tempo, key, energy), and real crowd sentiment pulled from listener discussions.

- **Retrieval + scoring layer** — a hybrid engine that doesn't rely on embeddings alone. A user's mood is expanded into a richer emotional scene by an LLM, embedded, and compared against the song database using vector similarity search. That semantic score is then blended with an audio-energy match, so the system also accounts for how sonically energetic a song actually is versus how energetic the user says they feel.

- **Presentation layer** — a Streamlit frontend for interactive use, backed by a FastAPI service exposing the same recommendation logic as REST endpoints.

The dataset is maintained through a validated, checkpointed pipeline, so adding new songs is a repeatable process rather than a one-off script.

---

## How It Works

```text
User Input (mood description + energy level)
     │
     ▼
LLM Query Expansion
  — turns a short, casual mood description into a
    richer emotional scene for better semantic matching
     │
     ▼
Semantic Embedding + Vector Similarity Search
     │
     ▼
Hybrid Scoring
  — blends semantic fit with the song's actual audio
    energy against what the user asked for
     │
     ▼
Ranked Recommendations, with a short LLM-generated
explanation for why each song fits
```

---

## Project Structure

```text
Evaris/
│
├── app.py                 # Streamlit frontend
├── api.py                  # FastAPI backend
├── rag_chain.py              # Retrieval + LLM query expansion + explanations
├── recommend.py                # Standalone CLI scoring script
├── db.py                         # Database models + engine
│
├── sync_pipeline.py              # End-to-end dataset sync pipeline
├── ingest_song_dna.py              # Pipeline step
├── nlp_embed.py                      # Pipeline step
├── reddit_blend.py                     # Pipeline step
├── dsp_batch.py                          # Pipeline step
├── dsp_extract.py                          # Audio feature extraction helper
├── chroma_migrate.py                         # Pipeline step
├── migrate_to_pg.py                            # Pipeline step
│
├── chroma_store/                                # Vector store
├── audio/                                         # Source audio files
├── song_dna.db                                      # Local staging database
├── song_dna_finder.xlsx                               # Curated source dataset
└── README.md
```

---

## Data Pipeline

New songs enter the system through a single, checkpointed pipeline (`sync_pipeline.py`), with each stage also available as a standalone script:

| Stage | Purpose |
|-------|---------|
| Validate | Checks the curated dataset for required fields, duplicates, and data quality before anything else runs |
| Ingest | Loads validated data into local staging |
| Embed | Generates multilingual semantic embeddings from human-written descriptions |
| Enrich | Blends in real listener sentiment |
| Extract | Pulls audio signal features (tempo, key, energy) from the actual tracks |
| Index | Rebuilds the vector store from the current embeddings |
| Migrate | Pushes the finalized dataset to production |

Every stage is idempotent, so re-running the pipeline after fixing an issue is always safe. The pipeline also supports partial runs and dry-run validation.

---

## Tech Stack

| Category            | Technologies                                      |
|----------------------|---------------------------------------------------|
| Language              | Python                                             |
| NLP / Embeddings       | Multilingual Sentence Transformers                 |
| LLM                      | Groq, via LangChain — query expansion + explanations |
| Vector Store              | ChromaDB                                            |
| Audio Processing           | Librosa (tempo, key, energy extraction)             |
| Crowd Sentiment              | Reddit-sourced listener sentiment                    |
| Backend API                    | FastAPI                                              |
| Frontend                         | Streamlit                                            |
| Database                          | PostgreSQL (Supabase)                                |