import librosa
import numpy as np
import sqlite3
import pandas as pd
from pathlib import Path

DB_PATH    = "song_dna.db"
AUDIO_DIR  = "audio"
AUDIO_EXTS = {".mp3", ".wav", ".flac", ".m4a"}

pitch_classes = ['C','C#','D','D#','E','F','F#','G','G#','A','A#','B']
major_profile = np.array([6.35,2.23,3.48,2.33,4.38,4.09,2.52,5.19,2.39,3.66,2.29,2.88])
minor_profile = np.array([6.35,2.23,3.48,2.33,4.38,4.09,2.52,5.19,2.39,3.66,2.29,2.88])

def extract(path):
    y, sr = librosa.load(path, mono=True)
    tempo  = float(np.atleast_1d(librosa.beat.beat_track(y=y, sr=sr)[0])[0])
    chroma = librosa.feature.chroma_cqt(y=y, sr=sr).mean(axis=1)
    root   = np.argmax(chroma)
    is_min = np.dot(chroma, np.roll(minor_profile, root)) < np.dot(chroma, np.roll(major_profile, root))
    key    = f"{pitch_classes[root]} {'minor' if is_min else 'major'}"
    rms    = float(librosa.feature.rms(y=y).mean())
    return tempo, key, rms

con = sqlite3.connect(DB_PATH)
songs_df = pd.read_sql("SELECT song, artist FROM songs", con)

records = []
for _, row in songs_df.iterrows():
    db_song_clean = row["song"].strip().lower()
    
    matches = [
        p for ext in AUDIO_EXTS
        for p in Path(AUDIO_DIR).glob(f"*{ext}")
        if (
            # Match directly with spaces vs underscores
            db_song_clean in p.stem.strip().lower().replace("_", " ") or
            db_song_clean.replace(" ", "_") in p.stem.strip().lower() or
            # Bidirectional absolute match fallback (for files like Sapphire)
            p.stem.strip().lower() in db_song_clean or
            p.stem.strip().lower().replace("_", " ") in db_song_clean
        )
    ]
    if not matches:
        print(f"⚠️  No file found for: {row['song']}")
        continue
    try:
        tempo, key, rms = extract(matches[0])
        records.append({"song": row["song"], "artist": row["artist"],
                         "tempo_bpm": round(tempo, 2), "key": key, "rms_energy": round(rms, 6)})
        print(f"✅ {row['song']} — {tempo:.1f} BPM | {key} | RMS {rms:.6f}")
    except Exception as e:
        print(f"❌ {row['song']} — {e}")

if records:
    pd.DataFrame(records).to_sql("audio_features", con, if_exists="replace", index=False)
    print(f"\n🎵 {len(records)} tracks written → audio_features table in {DB_PATH}")

con.close()