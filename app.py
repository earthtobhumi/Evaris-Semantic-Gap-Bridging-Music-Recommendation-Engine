import os
import re
import requests
import streamlit as st
from difflib import SequenceMatcher
from dotenv import load_dotenv
from rag_chain import run_rag

load_dotenv()

# Manual overrides for known-bad iTunes search matches.
# Add entries here as you spot wrong cover art in the wild — cheaper than
# trying to make fuzzy-matching perfect for every edge case.
COVER_OVERRIDES = {
    # "song name": "https://...300x300bb.jpg",
}

def _title_similarity(a, b):
    """Normalized fuzzy match between two song titles (lowercase, no punctuation)."""
    norm = lambda s: re.sub(r"[^a-z0-9 ]", "", s.lower())
    return SequenceMatcher(None, norm(a), norm(b)).ratio()

def fetch_cover(song, artist):
    if song in COVER_OVERRIDES:
        return COVER_OVERRIDES[song]

    try:
        q = requests.utils.quote(f"{song} {artist}")
        r = requests.get(
            f"https://itunes.apple.com/search?term={q}&entity=song&limit=5&country=IN",
            timeout=5
        )
        res = r.json().get("results", [])
        if not res:
            return ""

        # Pick the result whose track name is the closest fuzzy match to our
        # song title, instead of blindly trusting iTunes' top hit — this is
        # what was causing wrong artwork (e.g. another track by the same
        # artist outranking the correct one in iTunes' own relevance sort).
        best = max(res, key=lambda r: _title_similarity(song, r.get("trackName", "")))

        # If even the best match is a poor fit, don't show misleading art.
        if _title_similarity(song, best.get("trackName", "")) < 0.4:
            return ""

        return best.get("artworkUrl100", "").replace("100x100", "300x300")
    except Exception:
        return ""

st.set_page_config(page_title="Evaris", page_icon="🎵", layout="centered")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Caveat:wght@400;600;700&family=Playfair+Display:ital,wght@0,400;0,700;1,400&family=JetBrains+Mono:wght@300;400;600&family=Inter:wght@300;400;500&display=swap');

/* ── DESIGN TOKENS ── */
:root {
    --accent-heart:   #ff4d6d;
    --accent-mid:     #c77dff;
    --accent-brain:   #48cae4;

    /* light mode */
    --bg-page:        #f5f4f9;
    --bg-card:        #ffffff;
    --bg-card-deep:   #f0eef8;
    --bg-input:       #ffffff;

    --text-primary:   #1a1a2e;
    --text-secondary: #4a4a6a;
    --text-muted:     #888899;
    --text-faint:     #bbbbcc;

    --border-base:    #dddde8;
    --border-subtle:  #eeeef5;
    --border-heart:   #ff4d6d55;
    --border-mid:     #c77dff44;
    --border-brain:   #48cae444;

    --shadow-card:    0 1px 4px rgba(0,0,0,0.06);
    --footer-color:   #ccccdd;
}

@media (prefers-color-scheme: dark) {
    :root {
        --bg-page:        #000000;
        --bg-card:        #050505;
        --bg-card-deep:   #04040c;
        --bg-input:       #080808;

        --text-primary:   #e8e6f0;
        --text-secondary: #9999bb;
        --text-muted:     #7777aa;
        --text-faint:     #333355;

        --border-base:    #111111;
        --border-subtle:  #0d0d1a;
        --border-heart:   #1a0a10;
        --border-mid:     #0d0d1a;
        --border-brain:   #0d1a1a;

        --shadow-card:    none;
        --footer-color:   #1a1a1a;
    }
}

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    background-color: var(--bg-page);
    color: var(--text-primary);
}

/* ── HERO ── */
.hero {
    text-align: center;
    padding: 2.5rem 0 1rem;
    position: relative;
}
.hero-eyebrow {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.6rem;
    letter-spacing: 0.25em;
    color: var(--text-muted);
    text-transform: uppercase;
    margin-bottom: 0.75rem;
}
.hero-title {
    font-family: 'Playfair Display', serif;
    font-size: 3.5rem;
    font-weight: 700;
    letter-spacing: -0.02em;
    line-height: 1;
    margin-bottom: 0.5rem;
    background: linear-gradient(90deg, #ff4d6d 0%, #c77dff 50%, #48cae4 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.hero-tagline {
    font-family: 'Playfair Display', serif;
    font-style: italic;
    font-size: 0.9rem;
    color: var(--text-muted);
    margin-bottom: 1rem;
}

/* ── WAVEFORM SVG ── */
.waveform-wrap {
    width: 100%;
    height: 60px;
    margin: 0.5rem 0 1.5rem;
    position: relative;
    overflow: hidden;
}
.waveform-wrap svg { width: 100%; height: 100%; }

/* ── BRIDGE BAR ── */
.bridge {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin: 1.2rem 0 0.5rem;
    padding: 0 0.25rem;
}
.bridge-dot {
    width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0;
}
.bridge-dot.heart { background: var(--accent-heart); box-shadow: 0 0 8px var(--accent-heart); }
.bridge-dot.brain { background: var(--accent-brain); box-shadow: 0 0 8px var(--accent-brain); }
.bridge-line { flex: 1; height: 1px; background: linear-gradient(90deg, #ff4d6d, #c77dff, #48cae4); }
.bridge-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.58rem;
    color: var(--text-muted);
    letter-spacing: 0.15em;
    text-transform: uppercase;
    flex-shrink: 0;
}

/* ── INPUT PANEL ── */
.panel-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.58rem;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    margin-bottom: 0.4rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}
.panel-label .dot { width: 6px; height: 6px; border-radius: 50%; }
.panel-label.heart-label { color: var(--accent-heart); }
.panel-label.heart-label .dot { background: var(--accent-heart); box-shadow: 0 0 6px var(--accent-heart); }
.panel-label.brain-label { color: var(--accent-brain); }
.panel-label.brain-label .dot { background: var(--accent-brain); box-shadow: 0 0 6px var(--accent-brain); }

.stTextArea textarea {
    background: var(--bg-input) !important;
    border: 1px solid var(--border-heart) !important;
    border-left: 3px solid var(--accent-heart) !important;
    border-radius: 2px !important;
    color: var(--text-primary) !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.85rem !important;
    font-style: normal !important;
    padding: 1rem !important;
    line-height: 1.6 !important;
}
.stTextArea textarea:focus {
    border-color: var(--accent-heart) !important;
    box-shadow: 0 0 12px rgba(255,77,109,0.1) !important;
}
.stTextArea textarea::placeholder { color: var(--text-faint) !important; font-style: italic; }

/* ── SLIDER ── */
.slider-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin: 1rem 0 0.3rem;
}
.slider-tag {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.58rem;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: var(--text-muted);
}

/* ── BUTTON ── */
.stButton > button {
    width: 100%;
    background: linear-gradient(90deg, #ff4d6d22, #c77dff22, #48cae422);
    color: var(--text-primary);
    border: 1px solid var(--border-base);
    border-radius: 2px;
    padding: 0.75rem;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    margin-top: 0.75rem;
    transition: all 0.2s;
}
.stButton > button:hover {
    border-color: var(--accent-mid);
    box-shadow: 0 0 20px rgba(199,125,255,0.15);
    color: var(--accent-mid);
}

/* ── EXPAND BOX ── */
.expand-box {
    background: var(--bg-card-deep);
    border: 1px solid var(--border-subtle);
    border-left: 3px solid var(--accent-mid);
    padding: 1rem 1.1rem;
    margin: 1.2rem 0;
    border-radius: 0 2px 2px 0;
}
.expand-eyebrow {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.55rem;
    color: var(--accent-mid);
    letter-spacing: 0.2em;
    text-transform: uppercase;
    margin-bottom: 0.5rem;
}
.expand-text {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.78rem;
    color: var(--text-secondary);
    line-height: 1.8;
}

/* ── SECTION DIVIDER ── */
.section-div {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin: 1.5rem 0 1rem;
}
.section-div-line { flex: 1; height: 1px; background: var(--border-base); }
.section-div-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.55rem;
    color: var(--text-muted);
    letter-spacing: 0.2em;
    text-transform: uppercase;
    flex-shrink: 0;
}

/* ── RESULT CARD ── */
.result-card {
    background: var(--bg-card);
    border: 1px solid var(--border-base);
    border-radius: 3px;
    padding: 1rem 1.2rem;
    margin-bottom: 0.5rem;
    display: grid;
    grid-template-columns: 2rem 1fr auto;
    align-items: center;
    gap: 1rem;
    position: relative;
    overflow: hidden;
    box-shadow: var(--shadow-card);
}
.result-card::before {
    content: '';
    position: absolute;
    left: 0; top: 0; bottom: 0;
    width: 3px;
}
.result-card.rank-1::before { background: linear-gradient(180deg, #ff4d6d, #c77dff); box-shadow: 0 0 12px #c77dff44; }
.result-card.rank-2::before { background: #c77dff88; }
.result-card.rank-3::before { background: #48cae488; }
.result-card.rank-other::before { background: var(--border-base); }

.result-rank {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.7rem;
    color: var(--text-faint);
    text-align: center;
    font-weight: 600;
}
.result-rank.top { color: var(--accent-mid); }

.result-name {
    font-size: 0.95rem;
    font-weight: 600;
    color: var(--text-primary);
    margin-bottom: 0.2rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}
.result-artist {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.65rem;
    color: var(--text-secondary);
}
.dsp-tag {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.5rem;
    color: var(--accent-brain);
    border: 1px solid var(--border-brain);
    padding: 0.1rem 0.3rem;
    border-radius: 1px;
    letter-spacing: 0.08em;
}

.result-score-block { text-align: right; }
.result-score {
    font-family: 'JetBrains Mono', monospace;
    font-weight: 700;
    font-size: 1.1rem;
    letter-spacing: -0.02em;
}
.result-score.high { color: var(--accent-mid); text-shadow: 0 0 12px #c77dff44; }
.result-score.mid  { color: var(--accent-brain); }
.result-score.low  { color: var(--text-faint); }
.result-score-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.5rem;
    color: var(--text-muted);
    letter-spacing: 0.1em;
    text-transform: uppercase;
}

/* ── SIGNAL BARS ── */
.signal-bars {
    display: flex;
    align-items: flex-end;
    gap: 2px;
    height: 16px;
    margin-top: 4px;
    justify-content: flex-end;
}
.signal-bar { width: 4px; border-radius: 1px 1px 0 0; }

/* ── WHY BOX ── */
.why-box {
    background: var(--bg-card-deep);
    border: 1px solid var(--border-subtle);
    border-top: 2px solid var(--accent-brain);
    padding: 1.2rem 1.3rem;
    margin-top: 1.2rem;
    border-radius: 0 0 3px 3px;
}
.why-eyebrow {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.55rem;
    color: var(--accent-brain);
    letter-spacing: 0.2em;
    text-transform: uppercase;
    margin-bottom: 0.75rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}
.why-eyebrow::after { content: ''; flex: 1; height: 1px; background: var(--border-subtle); }
.why-content {
    font-size: 0.83rem;
    color: var(--text-secondary);
    line-height: 1.8;
}
.why-content strong { color: var(--accent-mid); font-weight: 500; }

/* ── FOOTER ── */
.footer {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.55rem;
    color: var(--footer-color);
    text-align: center;
    letter-spacing: 0.2em;
    padding: 2rem 0 1rem;
    margin-top: 2rem;
}
</style>
""", unsafe_allow_html=True)

# ── HERO
st.markdown("""
<div class="hero">
    <div class="hero-eyebrow">heart · music · brain</div>
    <div class="hero-title">Evaris</div>
    <div class="hero-tagline">where feeling finds its frequency</div>
</div>
""", unsafe_allow_html=True)

# ── ANIMATED WAVEFORM
st.markdown("""
<div class="waveform-wrap">
<svg viewBox="0 0 800 60" preserveAspectRatio="none" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="wg" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%"   stop-color="#ff4d6d" stop-opacity="0.8"/>
      <stop offset="50%"  stop-color="#c77dff" stop-opacity="0.9"/>
      <stop offset="100%" stop-color="#48cae4" stop-opacity="0.8"/>
    </linearGradient>
    <style>
      .wave-path {
        stroke-dasharray: 1200;
        stroke-dashoffset: 1200;
        animation: draw 2.5s ease forwards, pulse 3s ease-in-out 2.5s infinite;
      }
      @keyframes draw {
        to { stroke-dashoffset: 0; }
      }
      @keyframes pulse {
        0%, 100% { opacity: 0.7; }
        50%       { opacity: 1; }
      }
      .ecg-left {
        stroke-dasharray: 300;
        stroke-dashoffset: 300;
        animation: draw 1s ease forwards;
      }
      .ecg-right {
        stroke-dasharray: 300;
        stroke-dashoffset: 300;
        animation: draw 1s ease 2s forwards;
      }
    </style>
  </defs>
  <polyline class="ecg-left"
    points="0,30 60,30 75,10 85,48 95,20 105,38 120,30 200,30"
    fill="none" stroke="#ff4d6d" stroke-width="1.5" stroke-opacity="0.6"/>
  <path class="wave-path"
    d="M200,30 Q230,8 260,30 Q290,52 320,30 Q350,8 380,30 Q410,52 440,30 Q470,8 500,30 Q530,52 560,30 Q590,8 620,30"
    fill="none" stroke="url(#wg)" stroke-width="1.5"/>
  <polyline class="ecg-right"
    points="620,30 680,30 695,5 700,55 705,15 710,42 720,30 800,30"
    fill="none" stroke="#48cae4" stroke-width="1.5" stroke-opacity="0.6"/>
  <circle cx="400" cy="30" r="3" fill="#c77dff" opacity="0.9">
    <animate attributeName="opacity" values="0.4;1;0.4" dur="2s" repeatCount="indefinite"/>
    <animate attributeName="r" values="2;4;2" dur="2s" repeatCount="indefinite"/>
  </circle>
</svg>
</div>
""", unsafe_allow_html=True)

# ── INPUT
st.markdown('<div class="panel-label heart-label"><span class="dot"></span>emotional input</div>', unsafe_allow_html=True)
query = st.text_area(
    label="", height=95, label_visibility="collapsed",
    placeholder="how does your heart feel right now..."
)

st.markdown("""
<div class="slider-row">
    <span class="slider-tag">◂ low energy</span>
    <span class="slider-tag">signal intensity</span>
    <span class="slider-tag">high energy ▸</span>
</div>""", unsafe_allow_html=True)
energy_val = st.slider("", min_value=1, max_value=10, value=5, label_visibility="collapsed")

if st.button("⟡  transmit to brain"):
    if not query.strip():
        st.warning("// no emotional signal detected")
    else:
        with st.spinner("// translating feeling into frequency..."):
            user_energy = energy_val / 10
            result = run_rag(query.strip(), user_energy)

        # ── BRIDGE
        st.markdown("""
        <div class="bridge">
            <span class="bridge-dot heart"></span>
            <span class="bridge-label">felt</span>
            <span class="bridge-line"></span>
            <span class="bridge-label">processed</span>
            <span class="bridge-dot brain"></span>
        </div>""", unsafe_allow_html=True)

        # ── EXPAND BOX
        st.markdown(f"""
        <div class="expand-box">
            <div class="expand-eyebrow">// neural interpretation</div>
            <div class="expand-text">{result['expanded_query']}</div>
        </div>""", unsafe_allow_html=True)

        # ── RESULTS
        st.markdown("""
        <div class="section-div">
            <div class="section-div-line"></div>
            <div class="section-div-label">resonant frequencies</div>
            <div class="section-div-line"></div>
        </div>""", unsafe_allow_html=True)

        rank_cls_map = ["rank-1", "rank-2", "rank-3", "rank-other", "rank-other"]
        rank_top_map = ["top", "", "", "", ""]

        for i, r in enumerate(result["songs"]):
            score     = r["score"]
            score_cls = "high" if score > 0.6 else ("mid" if score > 0.4 else "low")
            dsp_tag   = '<span class="dsp-tag">DSP</span>' if r["has_dsp"] else ""
            rank_num  = str(i + 1).zfill(2)
            song_name = r["song"]
            artist    = r["artist"]
            score_str = f"{score:.3f}"
            rank_cls  = rank_cls_map[i]
            rank_top  = rank_top_map[i]

            bar_colors  = ["#ff4d6d", "#e05aff", "#c77dff", "#8a9ff5", "#48cae4"]
            bar_heights = [
                max(3, int(score * 16)),
                max(3, int(score * 24)),
                max(3, int(score * 16)),
                max(3, int(score * 20)),
                max(3, int(score * 12)),
            ]
            bars = "".join([
                f'<div class="signal-bar" style="height:{bar_heights[j]}px;background:{bar_colors[j]};opacity:0.7"></div>'
                for j in range(5)
            ])

            html = (
                f'<div class="result-card {rank_cls}">'
                f'<div class="result-rank {rank_top}">{rank_num}</div>'
                f'<div class="result-info">'
                f'<div class="result-name">{song_name} {dsp_tag}</div>'
                f'<div class="result-artist">{artist}</div>'
                f'</div>'
                f'<div class="result-score-block">'
                f'<div class="result-score {score_cls}">{score_str}</div>'
                f'<div class="signal-bars">{bars}</div>'
                f'<div class="result-score-label">resonance</div>'
                f'</div>'
                f'</div>'
            )

            cover_url = ""
            try:
                with st.spinner(""):
                    cover_url = fetch_cover(song_name, artist)
            except Exception:
                pass
            col_img, col_card = st.columns([1, 4])
            with col_img:
                if cover_url:
                    st.image(cover_url, width=80)
                else:
                    st.markdown('<div style="width:80px;height:80px;background:var(--bg-card-deep);border-radius:3px;"></div>', unsafe_allow_html=True)
            with col_card:
                st.markdown(html, unsafe_allow_html=True)

        # ── WHY BOX
        why_html = result["explanation"].replace("\n", "<br>")
        why_html = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', why_html)
        st.markdown(f"""
        <div class="why-box">
            <div class="why-eyebrow">brain signal analysis</div>
            <div class="why-content">{why_html}</div>
        </div>""", unsafe_allow_html=True)

st.markdown('<div class="footer">EVARIS · HEART → MUSIC → BRAIN · v0.3</div>', unsafe_allow_html=True)