import sqlite3
import pandas as pd

con = sqlite3.connect("song_dna.db")
df  = pd.DataFrame([{
    "song"       : "Georgia",
    "artist"     : "Vance Joy",
    "tempo_bpm"  : 143.55,
    "key"        : "B major",
    "rms_energy" : 0.261293
}])
df.to_sql("audio_features", con, if_exists="replace", index=False)
print(pd.read_sql("SELECT * FROM audio_features", con).to_string())
con.close()