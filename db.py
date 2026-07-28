import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, String, Float, Integer, Text, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.sql import func

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("❌ CRITICAL: DATABASE_URL is not set! Check your .env file or environment variables.")

engine       = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base         = declarative_base()

class Song(Base):
    __tablename__ = "songs"
    id             = Column(Integer, primary_key=True, autoincrement=True)
    song           = Column(String)
    artist         = Column(String)
    language       = Column(String)
    genre          = Column(String)
    primary_vibe   = Column(String)
    secondary_vibe = Column(String)
    energy_1_10    = Column(Float)
    weather        = Column(String)
    time_of_day    = Column(String)
    scene_description = Column(Text)
    personal_notes = Column(Text)
    tag_confidence = Column(Integer)
    release_year   = Column(Integer)

class AudioFeature(Base):
    __tablename__ = "audio_features"
    id         = Column(Integer, primary_key=True, autoincrement=True)
    song       = Column(String)
    artist     = Column(String)
    tempo_bpm  = Column(Float)
    key        = Column(String)
    rms_energy = Column(Float)

class Visit(Base):
    __tablename__ = "visits"
    id          = Column(Integer, primary_key=True, autoincrement=True)
    visited_at  = Column(DateTime(timezone=True), server_default=func.now())
    query_text  = Column(Text, nullable=True)

def init_db():
    Base.metadata.create_all(engine)
    print("✅ Tables created in Supabase")

if __name__ == "__main__":
    init_db()