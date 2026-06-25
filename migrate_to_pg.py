import sqlite3
import pandas as pd
from db import engine, init_db

SQLITE_PATH = "song_dna.db"

init_db()

con      = sqlite3.connect(SQLITE_PATH)
songs_df = pd.read_sql("SELECT * FROM songs", con)
dsp_df   = pd.read_sql("SELECT * FROM audio_features", con)
con.close()

songs_df.to_sql("songs", engine, if_exists="replace", index=False)
print(f"✅ {len(songs_df)} songs migrated → Supabase")

dsp_df.to_sql("audio_features", engine, if_exists="replace", index=False)
print(f"✅ {len(dsp_df)} audio features migrated → Supabase")