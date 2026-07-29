import os
import sqlite3
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

SQLITE_PATH = "song_dna.db"
CHUNK_SIZE = 20  # small batches so each transaction is short-lived

# This migration needs the session/direct connection, not the transaction
# pooler (DATABASE_URL, port 6543) that the rest of the app uses. The
# transaction pooler doesn't reliably hold state across a DROP/CREATE
# followed by many chunked inserts in the same run. Falls back to
# DATABASE_URL only if DIRECT_DATABASE_URL hasn't been set yet, so this
# still runs (just less reliably) before you've added the new var.
db_url = os.getenv("DIRECT_DATABASE_URL") or os.getenv("DATABASE_URL")
if not db_url:
    raise RuntimeError("Neither DIRECT_DATABASE_URL nor DATABASE_URL is set in .env")
if not os.getenv("DIRECT_DATABASE_URL"):
    print("WARNING: DIRECT_DATABASE_URL not set - falling back to DATABASE_URL (transaction pooler).")
    print("   This is the config that caused errors before; add DIRECT_DATABASE_URL to .env.")

engine = create_engine(db_url)

con = sqlite3.connect(SQLITE_PATH)
emb_df = pd.read_sql("SELECT song, artist, combined_text, embedding_json FROM sentiment_embeddings", con)
con.close()

print(f"Read {len(emb_df)} rows from local SQLite.")

# drop + recreate in its own short transaction
with engine.begin() as conn:
    conn.execute(text("DROP TABLE IF EXISTS sentiment_embeddings"))
    conn.execute(text("""
        CREATE TABLE sentiment_embeddings (
            song TEXT,
            artist TEXT,
            combined_text TEXT,
            embedding_json TEXT
        )
    """))
print("Table dropped and recreated.")

# insert in small chunks, each its own transaction
rows = emb_df.to_dict(orient="records")
for i in range(0, len(rows), CHUNK_SIZE):
    chunk = rows[i:i + CHUNK_SIZE]
    with engine.begin() as conn:
        conn.execute(
            text("""
                INSERT INTO sentiment_embeddings (song, artist, combined_text, embedding_json)
                VALUES (:song, :artist, :combined_text, :embedding_json)
            """),
            chunk
        )
    print(f"  rows {i+1}-{i+len(chunk)} inserted")

print(f"{len(emb_df)} sentiment embeddings migrated -> Supabase")
