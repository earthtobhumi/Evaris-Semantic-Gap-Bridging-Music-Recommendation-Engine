# Evaris

Evaris is a semantic music recommendation system. It recommends songs based on emotion, atmosphere, and context, not genres or listening history.

It combines multilingual sentence embeddings, a human-curated emotional metadata dataset, audio signal processing, and crowd sentiment to figure out what a song *feels* like, then matches that against how a user describes their mood in plain language.

---

## Motivation

Most recommendation systems work off one idea: people who listened to this also liked that. It's collaborative filtering, and it scales well, but it needs your listening history, and it can't really tell you why a song fits a moment. Type in "I miss my hometown and it's raining" and it has nothing to say to that.

Evaris starts from a different place. Instead of behavior, it tries to model the emotional character of a song directly, its mood, its energy, its atmosphere, and matches that against how someone describes what they're feeling, in their own words, in whatever language they're comfortable in.

Every song in the dataset is manually tagged by a human listener (scene, vibe, energy, personal notes), not just labeled by genre. Those descriptions get embedded into vector space alongside whatever the user typed, so the system is matching meaning, not keywords.

---

## Architecture

Three layers, roughly:

**Data layer.** A human-curated "Song DNA" dataset, built up from three sources: semantic embeddings of scene descriptions, audio features pulled straight from the tracks (tempo, key, energy), and crowd sentiment from real listener discussions.

**Retrieval + scoring layer.** A hybrid engine, not embeddings alone. A user's mood gets expanded into a richer emotional scene by an LLM first, then embedded and compared against the song database via vector similarity search. That semantic score gets blended with an audio-energy match, so the system also checks whether a song's actual energy lines up with what the user asked for.

**Presentation layer.** A Streamlit frontend for interactive use, plus a FastAPI service exposing the same logic as REST endpoints.

New songs go through a validated, checkpointed pipeline rather than a one-off script, so growing the dataset stays repeatable.

---

## How It Works

```text
User Input (mood description + energy level)
     │
     ▼
LLM Query Expansion
  turns a short, casual mood description into a
  richer emotional scene for better semantic matching
     │
     ▼
Semantic Embedding + Vector Similarity Search
     │
     ▼
Hybrid Scoring
  blends semantic fit with the song's actual audio
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

New songs go through a single, checkpointed pipeline (`sync_pipeline.py`). Each stage also runs standalone if you need it:

| Stage | Purpose |
|-------|---------|
| Validate | Checks the curated dataset for required fields, duplicates, and data quality |
| Ingest | Loads validated data into local staging |
| Embed | Generates multilingual semantic embeddings from human-written descriptions |
| Enrich | Blends in real listener sentiment |
| Extract | Pulls audio signal features (tempo, key, energy) from the actual tracks |
| Index | Rebuilds the vector store from the current embeddings |
| Migrate | Pushes the finalized dataset to production |

Every stage is idempotent, so re-running after fixing an issue is safe. Also supports partial runs and dry-run validation.

Crowd sentiment normally comes from querying Reddit discussions per track and blending that in with the personal embedding. Reddit's public search API isn't the most reliable thing to depend on though, it goes down for stretches with no warning and no ETA. When that happens, the pipeline falls back to manually researching crowd sentiment through web search instead, hand checked against the existing vibe tags for mismatches, then blended in the same way the live Reddit data would have been. Same step in the pipeline either way, just a different way of sourcing the crowd side when the API isn't cooperating.

---

## Tech Stack

| Category         | Technologies                                      |
|-------------------|---------------------------------------------------|
| Language           | Python                                             |
| NLP / Embeddings    | Multilingual Sentence Transformers                 |
| LLM                  | Groq, via LangChain (query expansion + explanations) |
| Vector Store          | ChromaDB                                            |
| Audio Processing        | Librosa (tempo, key, energy extraction)             |
| Crowd Sentiment           | Reddit-sourced listener sentiment, with a web-search fallback when the API is down |
| Backend API                | FastAPI                                              |
| Frontend                     | Streamlit                                            |
| Database                       | PostgreSQL (Supabase)                                |