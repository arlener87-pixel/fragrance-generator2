import datetime
from zoneinfo import ZoneInfo
import hashlib
import urllib.parse
import json
import random
import re
from pathlib import Path

import streamlit as st

# ==========================================
# PERSISTENCE (auto-save / auto-load)
# ==========================================
DATA_FILE = Path(__file__).parent / "scented_dead_girl_data.json"


def load_persisted_data():
    """Load reactions, SOTD history, and any user-added fragrances."""
    if DATA_FILE.exists():
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_persisted_data():
    """Save current session data to disk. Edits survive script updates when this file exists."""
    now = datetime.datetime.now(ZoneInfo("America/Los_Angeles")).isoformat(timespec="seconds")
    st.session_state["last_saved_at"] = now
    data = {
        "fragrances_db": st.session_state.get("fragrances_db", []),
        "user_reactions": st.session_state.get("user_reactions", {}),
        "sotd_history": st.session_state.get("sotd_history", []),
        "layer_recipes": st.session_state.get("layer_recipes", []),
        "play_stats": st.session_state.get("play_stats", {}),
        "last_export_date": st.session_state.get("last_export_date"),
        "last_saved_at": now,
        "chart": {
            "sun": st.session_state.get("chart_sun"),
            "moon": st.session_state.get("chart_moon"),
            "rising": st.session_state.get("chart_rising"),
            "venus": st.session_state.get("chart_venus"),
            "full": st.session_state.get("birth_calc_full"),
        },
        "wishlist": st.session_state.get("wishlist", []),
        "vault_log": st.session_state.get("vault_log", []),
    }
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        st.sidebar.warning(f"Could not save data: {e}")


# ==========================================
# PAGE CONFIGURATION & CUSTOM GOTHIC THEME
# ==========================================
st.set_page_config(
    page_title="ScentedDeadGirl Fragrance Sanctuary",
    page_icon="ð",
    layout="centered",
    initial_sidebar_state="expanded",
)

# Custom Gothic Styling - polished, professional, mobile-friendly
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;600;700&family=Inter:ital,wght@0,300;0,400;0,500;0,600;0,700;1,400&display=swap');

:root {
    --bg-deep: #03050a;
    --bg-card: #080d16;
    --bg-elevated: #0c1422;
    --border: #1a2740;
    --border-hover: #3d6cb0;
    --text: #c5d0e4;
    --text-muted: #7f91b0;
    --accent: #6ea4ff;
    --accent-dim: #3d6cb0;
    --success-bg: #0a1520;
    --danger: #4a6a9a;
}

html, body, .stApp, [class*="css"], .stMarkdown, p, span, div, label, input, textarea, button {
    font-family: 'Inter', 'Segoe UI', system-ui, -apple-system, sans-serif !important;
    letter-spacing: normal !important;
    word-spacing: normal !important;
}

.stApp {
    background: radial-gradient(ellipse at top, #0a1224 0%, #04070f 45%, #010205 100%);
    color: var(--text);
}

/* Tighten default Streamlit padding on mobile */
.block-container {
    padding-top: 1.25rem !important;
    padding-bottom: 2rem !important;
    max-width: 820px !important;
}

h1, h2, h3, h4, h5, h6 {
    color: var(--accent) !important;
    font-family: 'Cinzel', Georgia, serif !important;
    text-shadow: 0 0 10px rgba(80, 140, 255, 0.35);
    letter-spacing: 0.03em !important;
    font-weight: 600 !important;
    line-height: 1.25 !important;
}

h1 {
    font-size: 1.75rem !important;
    border-bottom: 1px solid var(--border);
    padding-bottom: 0.4rem;
    margin-bottom: 0.35rem !important;
}

h2, h3 {
    font-size: 1.2rem !important;
    margin-top: 0.5rem !important;
}

p, .stMarkdown, .stCaption, label, .stText {
    font-family: 'Inter', 'Segoe UI', system-ui, sans-serif !important;
    color: var(--text) !important;
    font-size: 0.95rem !important;
    line-height: 1.5 !important;
    letter-spacing: normal !important;
}

.stCaption, [data-testid="stCaptionContainer"] {
    color: var(--text-muted) !important;
    font-size: 0.85rem !important;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #040810 0%, #070c16 55%, #03050a 100%) !important;
    border-right: 1px solid var(--border);
}
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {
    color: var(--accent) !important;
    font-family: 'Cinzel', Georgia, serif !important;
    font-size: 0.95rem !important;
    letter-spacing: 0.04em !important;
}
section[data-testid="stSidebar"] .stMarkdown p {
    font-size: 0.88rem !important;
}

/* Buttons */
.stButton > button {
    background: linear-gradient(180deg, #121c30 0%, #0a1220 100%) !important;
    color: var(--accent) !important;
    border: 1px solid var(--border) !important;
    border-radius: 6px !important;
    font-family: 'Inter', system-ui, sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.9rem !important;
    letter-spacing: 0.02em !important;
    transition: all 0.2s ease;
    box-shadow: none !important;
    padding: 0.4rem 0.9rem !important;
}
.stButton > button:hover {
    background: linear-gradient(180deg, #1a2a48 0%, #101c30 100%) !important;
    border-color: var(--border-hover) !important;
    color: #e8f0ff !important;
}
.stButton > button[kind="primary"] {
    background: linear-gradient(180deg, #1a3060 0%, #122448 100%) !important;
    border: 1px solid var(--accent-dim) !important;
    color: #e0ecff !important;
}

/* Inputs */
.stTextInput > div > div > input,
.stSelectbox > div > div > select,
.stMultiSelect > div > div,
.stTextArea > div > div > textarea,
div[data-baseweb="select"] > div {
    background-color: var(--bg-card) !important;
    color: var(--text) !important;
    border: 1px solid var(--border) !important;
    border-radius: 6px !important;
    font-family: 'Inter', system-ui, sans-serif !important;
    font-size: 0.92rem !important;
}
.stTextInput > div > div > input:focus {
    border-color: var(--accent-dim) !important;
    box-shadow: 0 0 0 1px rgba(74, 122, 200, 0.35) !important;
}

.stRadio label, .stCheckbox label {
    font-family: 'Inter', system-ui, sans-serif !important;
    color: var(--text) !important;
    font-size: 0.9rem !important;
}

/* Alerts / cards */
.stAlert {
    background-color: var(--bg-elevated) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    color: var(--text) !important;
    font-family: 'Inter', system-ui, sans-serif !important;
}
div[data-testid="stNotification"] {
    border-left: 3px solid #3a5a8a !important;
}

/* Metrics */
[data-testid="stMetricValue"] {
    font-size: 1.25rem !important;
    font-family: 'Cinzel', Georgia, serif !important;
    color: var(--accent) !important;
}
[data-testid="stMetricLabel"] {
    font-size: 0.8rem !important;
    color: var(--text-muted) !important;
}

/* Tabs - professional underline style */
.stTabs [data-baseweb="tab-list"] {
    gap: 0.25rem;
    border-bottom: 1px solid var(--border);
    background: transparent;
}
.stTabs [data-baseweb="tab"] {
    font-family: 'Inter', system-ui, sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.88rem !important;
    color: var(--text-muted) !important;
    padding: 0.55rem 0.9rem !important;
    border-radius: 6px 6px 0 0 !important;
    background: transparent !important;
}
.stTabs [aria-selected="true"] {
    color: var(--accent) !important;
    background: rgba(30, 50, 90, 0.25) !important;
    border-bottom: 2px solid var(--accent-dim) !important;
}

/* Expanders */
[data-testid="stExpanderToggleIcon"],
[data-testid="stExpander"] summary svg,
[data-testid="stIconMaterial"],
.streamlit-expanderHeader svg,
span[data-testid="stIconMaterial"],
[data-testid="baseButton-headerNoPadding"] svg {
    display: none !important;
    width: 0 !important;
    height: 0 !important;
    visibility: hidden !important;
    opacity: 0 !important;
    font-size: 0 !important;
}
[data-testid="stExpander"] summary,
.streamlit-expanderHeader {
    font-family: 'Inter', system-ui, sans-serif !important;
    color: var(--accent) !important;
    background: var(--bg-elevated) !important;
    border: 1px solid var(--border) !important;
    border-radius: 6px !important;
    padding: 0.55rem 0.9rem !important;
    letter-spacing: 0.02em !important;
    overflow: hidden !important;
}
[data-testid="stExpander"] summary:hover {
    border-color: var(--border-hover) !important;
}
[data-testid="stExpander"] summary p,
[data-testid="stExpander"] summary div {
    color: var(--accent) !important;
    font-size: 0.9rem !important;
}
[data-testid="stExpander"] summary > div > span:first-child {
    display: none !important;
    width: 0 !important;
    max-width: 0 !important;
    overflow: hidden !important;
    font-size: 0 !important;
}

.stDownloadButton > button {
    background: linear-gradient(180deg, #121c30 0%, #0a1220 100%) !important;
    color: var(--accent) !important;
    border: 1px solid var(--border) !important;
    border-radius: 6px !important;
    font-family: 'Inter', system-ui, sans-serif !important;
}

.stFileUploader {
    border: 1px dashed var(--border) !important;
    background-color: var(--bg-card) !important;
    border-radius: 6px !important;
}

hr {
    border-color: var(--border) !important;
    opacity: 0.6;
    margin: 1rem 0 !important;
}

/* Fragrance card polish */
.frag-card {
    background: var(--bg-elevated);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 0.85rem 1rem;
    margin-bottom: 0.65rem;
}

/* Floating bats */
@keyframes flyBats {
    0%   { transform: translateY(0) translateX(0) rotate(0deg); opacity: 0; }
    12%  { opacity: 0.9; }
    88%  { opacity: 0.9; }
    100% { transform: translateY(-90px) translateX(36px) rotate(16deg); opacity: 0; }
}
.bat-container {
    position: relative;
    height: 56px;
    width: 100%;
    overflow: hidden;
    margin: 2px 0 6px 0;
    pointer-events: none;
}
.floating-bat {
    position: absolute;
    bottom: 2px;
    font-size: 18px;
    line-height: 1;
    font-family: 'Apple Color Emoji', 'Segoe UI Emoji', 'Noto Color Emoji', 'Android Emoji', emoji, sans-serif !important;
    animation: flyBats 2.6s ease-in-out infinite;
    filter: drop-shadow(0 0 3px rgba(70, 120, 200, 0.45));
    letter-spacing: normal !important;
}
.bat1 { left: 12%; animation-delay: 0s; }
.bat2 { left: 36%; animation-delay: 0.45s; }
.bat3 { left: 58%; animation-delay: 0.15s; }
.bat4 { left: 80%; animation-delay: 0.7s; }

@keyframes candleFlicker {
    0%, 100% { text-shadow: 0 0 10px rgba(80, 140, 255, 0.35); }
    40% { text-shadow: 0 0 16px rgba(120, 170, 255, 0.55); }
    70% { text-shadow: 0 0 8px rgba(60, 110, 220, 0.25); }
}
h1 {
    animation: candleFlicker 4.5s ease-in-out infinite;
}

@media (max-width: 640px) {
    h1 { font-size: 1.45rem !important; }
    h2, h3 { font-size: 1.1rem !important; }
    p, .stMarkdown, label { font-size: 0.9rem !important; }
    .block-container { padding-left: 1rem !important; padding-right: 1rem !important; }
    .bat-container { height: 48px; }
    .floating-bat { font-size: 16px; }
    [data-testid="stMetricValue"] { font-size: 1.1rem !important; }
    .stTabs [data-baseweb="tab"] { font-size: 0.8rem !important; padding: 0.45rem 0.55rem !important; }
}

::-webkit-scrollbar { width: 7px; height: 7px; }
::-webkit-scrollbar-track { background: #030508; }
::-webkit-scrollbar-thumb { background: #1a2540; border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: #2a4068; }

/* ---- Design system extras ---- */
.sdg-hero {
    position: relative;
    border: 1px solid #1a2740;
    border-radius: 14px;
    padding: 1.1rem 1.15rem 1rem 1.15rem;
    margin: 0.15rem 0 1rem 0;
    background:
        radial-gradient(ellipse at 15% 0%, rgba(50, 100, 180, 0.22), transparent 55%),
        radial-gradient(ellipse at 100% 80%, rgba(20, 40, 90, 0.25), transparent 45%),
        linear-gradient(180deg, #0a101c 0%, #04070e 100%);
    box-shadow: 0 10px 32px rgba(0, 0, 0, 0.55);
}
.sdg-hero-kicker {
    font-family: 'Inter', system-ui, sans-serif !important;
    font-size: 0.72rem !important;
    letter-spacing: 0.16em !important;
    text-transform: uppercase;
    color: #8a9bb8 !important;
    margin-bottom: 0.35rem;
}
.sdg-hero-title {
    font-family: 'Cinzel', Georgia, serif !important;
    font-size: 1.55rem !important;
    font-weight: 700 !important;
    color: #9ec0ff !important;
    text-shadow: 0 0 14px rgba(100, 150, 255, 0.35);
    margin: 0 0 0.25rem 0 !important;
    line-height: 1.2 !important;
}
.sdg-hero-sub {
    font-family: 'Inter', system-ui, sans-serif !important;
    color: #a8b6cc !important;
    font-size: 0.9rem !important;
    margin: 0 !important;
}
.sdg-chip-row {
    display: flex;
    flex-wrap: wrap;
    gap: 0.4rem;
    margin-top: 0.75rem;
}
.sdg-chip {
    font-family: 'Inter', system-ui, sans-serif !important;
    font-size: 0.72rem !important;
    letter-spacing: 0.04em;
    color: #c5d4ee !important;
    border: 1px solid #2a3c5c;
    background: rgba(20, 30, 50, 0.7);
    border-radius: 999px;
    padding: 0.22rem 0.65rem;
}
.sdg-section {
    border-left: 2px solid #3a5a8a;
    padding-left: 0.75rem;
    margin: 0.75rem 0 0.5rem 0;
}
.sdg-section-title {
    font-family: 'Cinzel', Georgia, serif !important;
    color: #8eb4ff !important;
    font-size: 1.05rem !important;
    margin: 0 !important;
}
.sdg-card {
    background: linear-gradient(180deg, #101826 0%, #0b101a 100%);
    border: 1px solid #1e2a42;
    border-radius: 10px;
    padding: 0.85rem 1rem;
    margin: 0.45rem 0 0.7rem 0;
    box-shadow: 0 4px 16px rgba(0,0,0,0.22);
}
.sdg-card:hover {
    border-color: #3a5a8a;
}
.sdg-divider {
    height: 1px;
    border: 0;
    background: linear-gradient(90deg, transparent, #2a3c5c, transparent);
    margin: 1rem 0;
}
div[data-testid="stMetric"] {
    background: #0b101a;
    border: 1px solid #1e2a42;
    border-radius: 10px;
    padding: 0.55rem 0.7rem;
}
.stTabs [data-baseweb="tab-list"] {
    background: rgba(8, 12, 20, 0.6);
    border-radius: 10px 10px 0 0;
    padding: 0.15rem 0.15rem 0 0.15rem;
}
section[data-testid="stSidebar"] {
    box-shadow: 4px 0 24px rgba(0,0,0,0.25);
}
section[data-testid="stSidebar"] .block-container {
    padding-top: 1rem;
}

@media (max-width: 640px) {
    .sdg-hero-title { font-size: 1.3rem !important; }
    .sdg-hero { padding: 0.9rem; }
}

/* Cool success/info - no red/pink alerts */
div[data-testid="stAlert"] {
    background: #0a1220 !important;
    border: 1px solid #2a4570 !important;
    color: #c5d0e4 !important;
}
[data-baseweb="notification"],
div[role="alert"] {
    border-color: #2a4570 !important;
}
/* success-ish */
.stSuccess, div[data-testid="stNotificationContentSuccess"] {
    background-color: #0a1524 !important;
    color: #b8d0f0 !important;
}
.stWarning {
    background-color: #121820 !important;
    border-left: 3px solid #5a7ab0 !important;
}
.stError {
    background-color: #0e1420 !important;
    border-left: 3px solid #4a6a9a !important;
}
</style>

""",
    unsafe_allow_html=True,
)

# ==========================================
# FRAGRANCE DATABASE (Stored in Session State)
# ==========================================
# Load any previously saved data first
_persisted = load_persisted_data()

if "fragrances_db" not in st.session_state:
    if _persisted.get("fragrances_db"):
        st.session_state["fragrances_db"] = _persisted["fragrances_db"]
    else:
        # Built-in sanctuary collection
        st.session_state["fragrances_db"] = [
            {
                "name": "Ajwad",
                "brand": "Lattafa",
                "gender": "Unisex",
                "season": "Versatile (cooler preferred)",
                "notes": "Fruity-woody-oriental (pineapple/rose/oud-leaning)",
                "category": ["Oriental", "Woody", "Fruity"],
            },
            {
                "name": "Al Rehab Caramello",
                "brand": "Al Rehab",
                "gender": "Unisex",
                "season": "Fall, Winter",
                "notes": "Top - Pistachio, Almond / Heart - Jasmine, Heliotrope / Base - Caramel, Vanilla, Sandalwood",
                "category": ["Gourmand", "Sweet"],
            },
            {
                "name": "Al Rehab Chocomusk",
                "brand": "Al Rehab",
                "gender": "Unisex",
                "season": "Fall, Winter",
                "notes": "Top - Warm Spicy, Amber / Heart - Sweet, Powdery, Vanilla / Base - Chocolate, Musky, Cocoa",
                "category": ["Gourmand", "Sweet"],
            },
            {
                "name": "Al Rehab Chocomusk Marshmallow",
                "brand": "Al Rehab",
                "gender": "Unisex",
                "season": "Fall, Winter",
                "notes": "Top - Marshmallow, Strawberry / Heart - Cocoa, Vanilla / Base - Sweet Musk",
                "category": ["Gourmand", "Sweet"],
            },
            {
                "name": "Al Rehab Chocomusk Vanilla",
                "brand": "Al Rehab",
                "gender": "Unisex",
                "season": "Fall, Winter",
                "notes": "Top - Chocolate / Heart - Vanilla / Base - Musk",
                "category": ["Gourmand", "Sweet"],
            },
            {
                "name": "Al Rehab Cup Cake",
                "brand": "Al Rehab",
                "gender": "Unisex",
                "season": "Fall, Winter",
                "notes": "Top - Citrus, Amber / Heart - Vanilla Cake / Base - Vanilla, Amber",
                "category": ["Gourmand", "Sweet"],
            },
            {
                "name": "Al Rehab French Vanilla",
                "brand": "Al Rehab",
                "gender": "Unisex",
                "season": "Fall, Winter",
                "notes": "Top - Vanilla / Heart - Creamy Sweet / Base - Vanilla, Musk",
                "category": ["Gourmand", "Sweet"],
            },
            {
                "name": "Al Rehab Royal Men",
                "brand": "Al Rehab",
                "gender": "Male",
                "season": "Fall, Winter",
                "notes": "Top - Spicy, Citrus, Woody / Heart - Floral, Sweet / Base - Amber, Musk, Vanilla",
                "category": ["Woody", "Spicy", "Oriental"],
            },
            {
                "name": "Al Rehab Silver",
                "brand": "Al Rehab",
                "gender": "Unisex/Male",
                "season": "Spring, Summer",
                "notes": "Top - Fresh Citrus, Metallic / Heart - Floral / Base - Musk, Sweet",
                "category": ["Fresh", "Citrus"],
            },
            {
                "name": "Al Rehab Soft",
                "brand": "Al Rehab",
                "gender": "Unisex (leans feminine)",
                "season": "Fall, Winter",
                "notes": "Top - Citruses / Heart - Orchid, Jasmine, Vanilla, Caramel / Base - White Musk, Woody Notes, Vetiver",
                "category": ["Floral", "Sweet", "Gourmand"],
            },
            {
                "name": "Ameerat Al Arab Prive Rose",
                "brand": "Ameerat Al Arab",
                "gender": "Female",
                "season": "Fall, Spring",
                "notes": "Top - Rose / Heart - Floral, Sweet / Base - Musk, Vanilla",
                "category": ["Floral", "Sweet"],
            },
            {
                "name": "Arabiyat Prestige Bahiya Garnet",
                "brand": "Arabiyat Prestige",
                "gender": "Female-leaning",
                "season": "Fall, Winter",
                "notes": "Top - Cherry, Mandarin, Mango, Pear, Bergamot / Heart - Amber, Fig, Jasmine / Base - Amber, Vanilla, Sandalwood, Musk",
                "category": ["Fruity", "Oriental", "Sweet"],
            },
            {
                "name": "Arabiyat Prestige Nyla",
                "brand": "Arabiyat Prestige",
                "gender": "Female",
                "season": "Spring, Summer",
                "notes": "Top - Coconut, Peach, Bergamot, Mandarin / Heart - Tiare, White Flowers, Jasmine, Rose / Base - White Musk, Patchouli",
                "category": ["Floral", "Fruity", "Fresh"],
            },
            {
                "name": "Arabiyat Prestige Nyla Vanielle",
                "brand": "Arabiyat Prestige",
                "gender": "Female",
                "season": "Fall, Winter",
                "notes": "Top - Jasmine, Vanilla Bean / Heart - Caramel, Amber / Base - Musk, Tonka Bean, Vanilla",
                "category": ["Gourmand", "Sweet", "Floral"],
            },
            {
                "name": "Ard Al Zaafaran Bint Hooran",
                "brand": "Ard Al Zaafaran",
                "gender": "Female",
                "season": "Fall, Winter",
                "notes": "Top - Almond, Coffee, Ylang Ylang / Heart - Jasmine, Rose, Tuberose / Base - Vanilla, Musk, Tonka, Woody/Cacao",
                "category": ["Gourmand", "Floral", "Oriental"],
            },
            {
                "name": "Armaf Island Bliss",
                "brand": "Armaf",
                "gender": "Unisex",
                "season": "Spring, Summer",
                "notes": "Top - Tropical Fruits, Coconut / Heart - Sweet / Base - Musk",
                "category": ["Fruity", "Fresh", "Sweet"],
            },
            {
                "name": "Armaf Odyssey Aqua",
                "brand": "Armaf",
                "gender": "Male",
                "season": "Spring, Summer",
                "notes": "Top - Orange, Grapefruit, Artemisia / Heart - Mint, Lavender / Base - Ambroxan, Cypress, Patchouli",
                "category": ["Fresh", "Citrus", "Aromatic"],
            },
            {
                "name": "Armaf Odyssey Candee",
                "brand": "Armaf",
                "gender": "Female-leaning",
                "season": "Fall, Winter",
                "notes": "Top - Strawberry, Raspberry, Peach, Bergamot / Heart - Caramel, Jasmine / Base - Patchouli, Musk, Amber",
                "category": ["Fruity", "Gourmand", "Sweet"],
            },
            {
                "name": "Armaf Odyssey Marshmallow",
                "brand": "Armaf",
                "gender": "Unisex",
                "season": "Spring, Fall, Winter",
                "notes": "Top - Apple, Lemon, Coconut, Peony, Lily of the Valley / Heart - Strawberry, Peach, Raspberry, Apricot, Marshmallow, Orange Blossom / Base - Vanilla, Praline, Tonka, Amber, Musk, Mascarpone",
                "category": ["Gourmand", "Fruity", "Sweet"],
            },
            {
                "name": "Banat Dubai",
                "brand": "Le Chameau",
                "gender": "Female",
                "season": "Versatile to cooler",
                "notes": "Top - Jasmine, Bergamot, Peony / Heart - Pineapple, Peach, Plum / Base - Musk, Patchouli, Sandalwood",
                "category": ["Floral", "Fruity"],
            },
            {
                "name": "Baraja Red 500",
                "brand": "Baraja",
                "gender": "Unisex/Male",
                "season": "Fall, Winter",
                "notes": "Top - Red Fruits, Spices / Heart - Sweet Notes / Base - Woody, Musk",
                "category": ["Fruity", "Woody", "Spicy"],
            },
            {
                "name": "Bellavita Vanilla",
                "brand": "Bellavita",
                "gender": "Female",
                "season": "Fall, Winter",
                "notes": "Top - Aldehydes, Heliotrope, Coconut, Vanilla / Heart - Vanilla, Mango / Base - White Musk, Coconut, Vanilla Absolute",
                "category": ["Gourmand", "Sweet"],
            },
            {
                "name": "Berries Cream Macaron",
                "brand": "Arabiyat Sugar",
                "gender": "Female",
                "season": "Spring-Fall",
                "notes": "Berry + cream macaron gourmand",
                "category": ["Gourmand", "Fruity", "Sweet"],
            },
            {
                "name": "Black Opinion",
                "brand": "Black Opinion",
                "gender": "Male/Unisex",
                "season": "Fall-Winter",
                "notes": "Dark, bold (woody/spicy/leather)",
                "category": ["Woody", "Spicy", "Leather"],
            },
            {
                "name": "Blue for Men Le Parfum",
                "brand": "Blue for Men",
                "gender": "Male/Unisex",
                "season": "Fall, Winter",
                "notes": "Top - Cardamom / Heart - Lavender, Iris / Base - Vanilla, Oriental Woods",
                "category": ["Woody", "Oriental", "Spicy"],
            },
            {
                "name": "Caramel Chocolate Macaron",
                "brand": "Arabiyat Sugar",
                "gender": "Female/Unisex",
                "season": "Fall-Winter",
                "notes": "Caramel-chocolate-macaron gourmand",
                "category": ["Gourmand", "Sweet"],
            },
            {
                "name": "Club de Nuit Women",
                "brand": "Armaf",
                "gender": "Female",
                "season": "Spring, Fall",
                "notes": "Top - Apple, Citrus / Heart - Rose, Jasmine / Base - Vanilla, Musk",
                "category": ["Floral", "Fruity", "Fresh"],
            },
            {
                "name": "Coconut Chiffon",
                "brand": "Arabiyat Sugar",
                "gender": "Female/Unisex",
                "season": "Spring-Summer",
                "notes": "Coconut + light cake/chiffon",
                "category": ["Gourmand", "Sweet", "Fresh"],
            },
            {
                "name": "Confections",
                "brand": "Paris Corner",
                "gender": "Female/Unisex",
                "season": "Fall-Winter",
                "notes": "Gourmand/sweet, confectionery-style",
                "category": ["Gourmand", "Sweet"],
            },
            {
                "name": "Dulzura",
                "brand": "Paris Corner",
                "gender": "Female",
                "season": "Fall-Winter",
                "notes": "Top - Black pepper, buttermilk / Heart - Cake, vanilla, cream / Base - Amber, musk",
                "category": ["Gourmand", "Sweet"],
            },
            {
                "name": "Eclaire Banoffi",
                "brand": "Lattafa",
                "gender": "Unisex/Female",
                "season": "Fall-Winter",
                "notes": "Banana-toffee/Ã©clair gourmand",
                "category": ["Gourmand", "Sweet"],
            },
            {
                "name": "Ãclat Parfumerie Al Gazal",
                "brand": "Ãclat Parfumerie",
                "gender": "Unisex (leans masculine)",
                "season": "Versatile to cooler",
                "notes": "Limited public data; typically woody-oriental or spicy",
                "category": ["Woody", "Oriental"],
            },
            {
                "name": "Elyssia Aura",
                "brand": "Riiffs",
                "gender": "Unisex",
                "season": "Fall, Winter (versatile to cooler)",
                "notes": "Top - Cinnamon, Orange, Nutmeg / Heart - Vanilla Cream, Cognac, Cocoa / Base - Bourbon Vanilla, Cedarwood, Patchouli",
                "category": ["Gourmand", "Spicy", "Woody"],
            },
            {
                "name": "Elyssia Scarlet",
                "brand": "Riiffs",
                "gender": "Female",
                "season": "Spring-Summer / versatile",
                "notes": "Top - Black Cherry, Pink Pepper / Heart - Leather, Cream, Benzoin / Base - Vanilla Absolute, Cashmeran, Amber, Iso E Super",
                "category": ["Fruity", "Leather", "Sweet"],
            },
            {
                "name": "Emir Pear Potion",
                "brand": "Paris Corner",
                "gender": "Unisex",
                "season": "Spring",
                "notes": "Top - Pear, Apple / Heart - Caramel, Jasmine / Base - Raspberry, Musk",
                "category": ["Fruity", "Gourmand", "Sweet"],
            },
            {
                "name": "Empire Najm by Risala",
                "brand": "Risala",
                "gender": "Unisex (female-leaning)",
                "season": "Fall, Winter",
                "notes": "Top - Mango, Ginger, Lemon, Red Berries / Heart - Coumarin, Jasmine, Cedar / Base - Cypriol, Amber, Musk, Oud",
                "category": ["Fruity", "Oriental", "Woody"],
            },
            {
                "name": "Emper Boulevard of New York",
                "brand": "Le Chameau",
                "gender": "Unisex",
                "season": "Fall, Winter",
                "notes": "Top - Roasted Coffee Beans / Heart - Praline, Rose / Base - Oakmoss, Cedar, Amber",
                "category": ["Gourmand", "Woody"],
            },
            {
                "name": "Entice Extrait",
                "brand": "Vurv",
                "gender": "Female",
                "season": "Cooler / evening",
                "notes": "Richer/intensified sweet/fruity or oriental",
                "category": ["Oriental", "Sweet", "Fruity"],
            },
            {
                "name": "Entice Ruby",
                "brand": "Vurv",
                "gender": "Female",
                "season": "Spring-Summer / versatile",
                "notes": "Fruity-floral / berry-red fruit leaning",
                "category": ["Fruity", "Floral"],
            },
            {
                "name": "Espada Intense",
                "brand": "Le Chameau",
                "gender": "Male",
                "season": "Cooler seasons / evening",
                "notes": "Deeper/intensified version of Espada Prime",
                "category": ["Woody", "Spicy"],
            },
            {
                "name": "Espada Prime",
                "brand": "Le Chameau",
                "gender": "Male",
                "season": "Spring-Summer / versatile",
                "notes": "Fresh or spicy-woody",
                "category": ["Fresh", "Woody", "Spicy"],
            },
            {
                "name": "Fakhama",
                "brand": "Amaran",
                "gender": "Unisex/Male",
                "season": "Cooler seasons",
                "notes": "Luxury oriental or woody",
                "category": ["Oriental", "Woody"],
            },
            {
                "name": "Fragrance World CrÃ¨me of Clouds",
                "brand": "Fragrance World",
                "gender": "Unisex",
                "season": "Fall, Winter",
                "notes": "Top - Vanilla, Chocolate, Burnt Sugar / Heart - Milk, Creamy/Coconut Milk, Whipped Cream / Base - Musk",
                "category": ["Gourmand", "Sweet"],
            },
            {
                "name": "French Avenue 8th Wonder",
                "brand": "French Avenue",
                "gender": "Unisex",
                "season": "Fall, Winter",
                "notes": "Top - Cardamom, Pink Pepper, Candy Apple / Heart - Liquor, Dates, Boozy notes, Davana, Osmanthus / Base - Myrrh, Benzoin, Styrax, Amber Xtreme, Labdanum, Patchouli",
                "category": ["Oriental", "Spicy", "Sweet"],
            },
            {
                "name": "French Avenue Spectre Original",
                "brand": "French Avenue",
                "gender": "Male/Unisex (leans masculine)",
                "season": "Fall, Winter",
                "notes": "Top - Incense, Guaiac Wood, Saffron / Heart - Leather, Amberwood, Violet, Sugar Cane / Base - Smoke, Patchouli, Sandalwood, Woodsy Notes, Black Musk",
                "category": ["Woody", "Leather", "Oriental"],
            },
            {
                "name": "French Avenue Vulcan Baie",
                "brand": "French Avenue",
                "gender": "Unisex",
                "season": "Spring, Summer",
                "notes": "Top - Blackberry, Black Currant, Rosemary, Bergamot / Heart - Raspberry, Vodka, Basil, Lily of the Valley / Base - Strawberry, Musk, Peach, Amber, Sandalwood, Patchouli, Incense",
                "category": ["Fruity", "Fresh", "Aromatic"],
            },
            {
                "name": "French Vanilla Latte",
                "brand": "Arabiyat Sugar",
                "gender": "Unisex",
                "season": "Fall, Winter",
                "notes": "Top - Nutella, Cardamom, Rum / Heart - Cocoa, Coconut, White Flowers, Lily of the Valley / Base - Sandalwood, Ambergris, Musk",
                "category": ["Gourmand", "Sweet"],
            },
            {
                "name": "Ghaliya",
                "brand": "Zakat",
                "gender": "Unisex/Female",
                "season": "Fall-Winter",
                "notes": "Rich oriental/oud-floral",
                "category": ["Oriental", "Floral", "Oud"],
            },
            {
                "name": "Gulf Orchid Cookie Bite",
                "brand": "Gulf Orchid",
                "gender": "Unisex",
                "season": "Fall, Winter",
                "notes": "Top - Cookie, Butter / Heart - Vanilla, Musk / Base - Caramel, Amber",
                "category": ["Gourmand", "Sweet"],
            },
            {
                "name": "Gulf Orchid PiÃ±a Colada Musk Collection Body Spray",
                "brand": "Gulf Orchid",
                "gender": "Unisex",
                "season": "Spring, Summer",
                "notes": "Top - Pineapple, Coconut / Heart - Tropical / Base - Musk",
                "category": ["Fruity", "Fresh", "Sweet"],
            },
            {
                "name": "Hawas Elixir",
                "brand": "Rasasi",
                "gender": "Unisex",
                "season": "Fall-Winter",
                "notes": "Top - Mint, bergamot, artemisia / Heart - Dark chocolate, lavender, benzoin / Base - Vanilla, tonka bean, white musk",
                "category": ["Gourmand", "Fresh", "Sweet"],
            },
            {
                "name": "Heroes Energize",
                "brand": "Heroes",
                "gender": "Male",
                "season": "Spring, Summer",
                "notes": "Top - Citrus, Aromatic Herbs / Heart - Light Spices / Base - Woods, Musk",
                "category": ["Fresh", "Citrus", "Aromatic"],
            },
            {
                "name": "Kandy Rush",
                "brand": "Kandy Rush",
                "gender": "Female/Unisex",
                "season": "Fall-Winter / casual year-round",
                "notes": "Sweet candy/gourmand",
                "category": ["Gourmand", "Sweet"],
            },
            {
                "name": "Khadlaj Cafe Latte",
                "brand": "Khadlaj",
                "gender": "Unisex",
                "season": "Fall, Winter",
                "notes": "Top - Coffee, Sweet Almond, Milk / Heart - Vanilla, Ice Cream Accord, Amber / Base - Vanilla, Almond Cream, Caramel",
                "category": ["Gourmand", "Sweet"],
            },
            {
                "name": "Khadlaj Cream Velvet",
                "brand": "Khadlaj",
                "gender": "Unisex (leans feminine)",
                "season": "Fall, Winter",
                "notes": "Top - Caramel, Butter / Heart - Tonka, Honey, Jasmine / Base - Vanilla, Musk, Amber",
                "category": ["Gourmand", "Sweet"],
            },
            {
                "name": "Khadlaj Hareem Al Sultan Gold",
                "brand": "Khadlaj",
                "gender": "Female",
                "season": "Spring, Summer",
                "notes": "Top - Bergamot, Jasmine, Peony / Heart - Pineapple, Peach, Plum / Base - Musk, Sandalwood, Patchouli",
                "category": ["Floral", "Fruity", "Fresh"],
            },
            {
                "name": "Khadlaj Nuha Vanilla Pearl",
                "brand": "Khadlaj",
                "gender": "Female",
                "season": "Fall, Winter",
                "notes": "Top - Blackcurrant, Strawberry, Freesia / Heart - Raspberry, Magnolia, Cashmere Wood / Base - Vanilla, Caramel, Moss",
                "category": ["Fruity", "Gourmand", "Floral"],
            },
            {
                "name": "Khadlaj Peach Velvet",
                "brand": "Khadlaj",
                "gender": "Female",
                "season": "Spring, Summer, Fall",
                "notes": "Top - Guava, Peach, Nectarine / Heart - Vanilla, Ginger, Cinnamon, Amber / Base - Caramel, Musk, Sandalwood",
                "category": ["Fruity", "Gourmand", "Sweet"],
            },
            {
                "name": "Khadlaj Zainab Oil",
                "brand": "Khadlaj",
                "gender": "Unisex",
                "season": "Fall, Winter",
                "notes": "Top - Bergamot, Gardenia, Almond / Heart - Coconut, Caramel / Base - Patchouli, Vanilla, Musk",
                "category": ["Gourmand", "Floral", "Sweet"],
            },
            {
                "name": "Khamrah Waha",
                "brand": "Lattafa",
                "gender": "Unisex",
                "season": "Fall-Winter",
                "notes": "Spicy-sweet (date, cinnamon, vanilla family)",
                "category": ["Oriental", "Spicy", "Sweet"],
            },
            {
                "name": "Khayali Vanilla Ayelet",
                "brand": "Khayali",
                "gender": "Unisex",
                "season": "Fall-Winter",
                "notes": "Vanilla orchid, jasmine / Brown sugar, tonka / Amber, musk, patchouli (Kayali-inspired)",
                "category": ["Gourmand", "Floral", "Sweet"],
            },
            {
                "name": "Lattafa Angham",
                "brand": "Lattafa",
                "gender": "Unisex (leans feminine)",
                "season": "Fall, Winter",
                "notes": "Top - Ginger, Mandarin, Pink Pepper / Heart - Lavender, Praline, Cacao, Jasmine / Base - Vanilla, Amber, Musk",
                "category": ["Gourmand", "Spicy", "Sweet"],
            },
            {
                "name": "Lattafa Ansaam Gold",
                "brand": "Lattafa",
                "gender": "Female/Unisex",
                "season": "Fall, Winter",
                "notes": "Top - Mandarin Orange, Pear / Heart - Sweet Notes, Jasmine, Rose / Base - Musk, Vanilla, Raspberry",
                "category": ["Fruity", "Floral", "Sweet"],
            },
            {
                "name": "Lattafa Asad",
                "brand": "Lattafa",
                "gender": "Male",
                "season": "Fall, Winter",
                "notes": "Top - Black Pepper, Tobacco, Pineapple / Heart - Patchouli, Coffee, Iris / Base - Vanilla, Amber, Dry Woods, Benzoin, Labdanum",
                "category": ["Woody", "Spicy", "Oriental"],
            },
            {
                "name": "Lattafa Badee Al Oud Noble Blush",
                "brand": "Lattafa",
                "gender": "Female",
                "season": "Fall, Winter",
                "notes": "Top - Rose Milk / Heart - Meringue, Almond / Base - Vanilla, Musk, Sandalwood",
                "category": ["Floral", "Gourmand", "Sweet"],
            },
            {
                "name": "Lattafa Coral (Ana Abiyedh Coral)",
                "brand": "Lattafa",
                "gender": "Unisex (leans feminine)",
                "season": "Spring, Summer",
                "notes": "Top - Watermelon, Peach, Orange / Heart - Coconut, White Flowers / Base - Musk, Vanilla, Amber",
                "category": ["Fruity", "Fresh", "Sweet"],
            },
            {
                "name": "Lattafa Dalal",
                "brand": "Lattafa",
                "gender": "Female",
                "season": "Spring",
                "notes": "Top - Apple (Golden Delicious), Mandarin / Heart - Jasmine, Ylang-Ylang, Orange Flower / Base - Vanilla, Musk, Oakmoss",
                "category": ["Floral", "Fruity", "Fresh"],
            },
            {
                "name": "Lattafa Eclaire",
                "brand": "Lattafa",
                "gender": "Female",
                "season": "Fall, Winter",
                "notes": "Top - Caramel, Milk, Sugar / Heart - Honey, White Flowers / Base - Vanilla, Praline, Musk",
                "category": ["Gourmand", "Sweet"],
            },
            {
                "name": "Lattafa Emaan",
                "brand": "Lattafa",
                "gender": "Female/Unisex",
                "season": "Fall, Winter",
                "notes": "Top - Orange Blossom, Black Currant, Bergamot / Heart - Tuberose, Jasmine, Marigold / Base - Musk, Vanilla, Cedarwood, Patchouli",
                "category": ["Floral", "Fruity"],
            },
            {
                "name": "Lattafa Eternal Vanille",
                "brand": "Lattafa",
                "gender": "Unisex",
                "season": "Year-round (best Spring/Fall)",
                "notes": "Top - Blackberry / Heart - Cocoapulse, Vanilla Caviar, Cacao / Base - Akigalawood, Tonka Bean, Ambrofix, Cedarwood, Benzoin, Musk",
                "category": ["Gourmand", "Woody", "Sweet"],
            },
            {
                "name": "Lattafa Fakhar Black",
                "brand": "Lattafa",
                "gender": "Unisex",
                "season": "Fall, Winter",
                "notes": "Top - Dark Fruits, Spices / Heart - Woody / Base - Vanilla, Musk",
                "category": ["Fruity", "Woody", "Spicy"],
            },
            {
                "name": "Lattafa Fakhar Gold",
                "brand": "Lattafa",
                "gender": "Unisex",
                "season": "Fall, Winter",
                "notes": "Top - Tuberose, Salt / Heart - Amber, Tonka / Base - Cedarwood, Vetiver, Labdanum",
                "category": ["Floral", "Woody", "Oriental"],
            },
            {
                "name": "Lattafa Habik (Women's version)",
                "brand": "Lattafa",
                "gender": "Female",
                "season": "Spring, Summer",
                "notes": "Top - Pear, Bergamot / Heart - Lily of the Valley, Jasmine, Freesia / Base - Musk, Amber, Oakmoss",
                "category": ["Floral", "Fresh", "Fruity"],
            },
            {
                "name": "Lattafa Haya",
                "brand": "Lattafa",
                "gender": "Female",
                "season": "Fall, Winter",
                "notes": "Top - Champagne, Strawberry, Rose, Tangerine, Blood Orange / Heart - Gardenia, Jasmine, Vanilla Orchid / Base - Amber, Sandalwood",
                "category": ["Floral", "Fruity", "Sweet"],
            },
            {
                "name": "Lattafa Her Confessions",
                "brand": "Lattafa",
                "gender": "Female",
                "season": "Fall, Winter",
                "notes": "Top - Cinnamon / Heart - Tuberose, Jasmine, Incense / Base - Vanilla, Musk, Tonka",
                "category": ["Floral", "Spicy", "Oriental"],
            },
            {
                "name": "Lattafa His Confessions",
                "brand": "Lattafa",
                "gender": "Male",
                "season": "Fall, Winter",
                "notes": "Top - Lavender, Cinnamon, Mandarin / Heart - Iris, Benzoin, Cypress, Mahonial / Base - Vanilla, Tonka, Amber, Incense, Cedarwood, Patchouli",
                "category": ["Woody", "Spicy", "Oriental"],
            },
            {
                "name": "Lattafa Khamrah Dukhan",
                "brand": "Lattafa",
                "gender": "Unisex",
                "season": "Fall, Winter",
                "notes": "Top - Spices, Pimento, Mandarin / Heart - Incense, Labdanum, Orange Blossom, Patchouli / Base - Tobacco, Praline, Amber, Tonka Bean, Benzoin",
                "category": ["Oriental", "Spicy", "Sweet"],
            },
            {
                "name": "Lattafa Khamrah Original",
                "brand": "Lattafa",
                "gender": "Unisex",
                "season": "Fall, Winter",
                "notes": "Top - Cinnamon, Nutmeg, Bergamot / Heart - Dates, Praline, Tuberose, Mahonial / Base - Vanilla, Tonka Bean, Amberwood, Myrrh, Benzoin, Akigalawood",
                "category": ["Oriental", "Spicy", "Sweet"],
            },
            {
                "name": "Lattafa Khamrah Qahwa",
                "brand": "Lattafa",
                "gender": "Unisex",
                "season": "Fall, Winter",
                "notes": "Top - Cinnamon, Cardamom, Ginger / Heart - Praline, Candied Fruits, White Flowers / Base - Coffee, Vanilla, Tonka Bean, Benzoin, Musk",
                "category": ["Gourmand", "Spicy", "Sweet"],
            },
            {
                "name": "Lattafa Maitha Oil (Attar)",
                "brand": "Lattafa",
                "gender": "Unisex",
                "season": "Fall, Winter",
                "notes": "Top - Anise / Heart - Caramel / Base - Vanilla, Tonka Bean, Musk",
                "category": ["Gourmand", "Sweet"],
            },
            {
                "name": "Lattafa Mayar Cherry Intense",
                "brand": "Lattafa",
                "gender": "Female",
                "season": "Fall, Winter",
                "notes": "Top - Strawberry, Bergamot / Heart - Cherry Jam, Cacao / Base - Vanilla, Amber, Patchouli",
                "category": ["Fruity", "Gourmand", "Sweet"],
            },
            {
                "name": "Lattafa Nasmaat",
                "brand": "Lattafa",
                "gender": "Unisex",
                "season": "Spring, Fall",
                "notes": "Top - Blackcurrant, Apricot, Pineapple / Heart - Magnolia, Cyclamen, Jasmine, Orange Blossom, Rose / Base - Vanilla, Cashmeran, Caramel, Sandalwood",
                "category": ["Floral", "Fruity", "Sweet"],
            },
            {
                "name": "Lattafa Nebras",
                "brand": "Lattafa",
                "gender": "Unisex",
                "season": "Fall, Winter",
                "notes": "Top - Red Berries, Mandarin Orange / Heart - Vanilla, Cacao, Rose / Base - Sugar, Tonka Bean, Amber, Musk",
                "category": ["Gourmand", "Fruity", "Sweet"],
            },
            {
                "name": "Lattafa Nebras Elixir",
                "brand": "Lattafa",
                "gender": "Unisex",
                "season": "Fall, Winter, Mild Spring",
                "notes": "Top - Milk Candy, Whipped Cream / Heart - Sugar Cane, Heliotrope / Base - Vanilla, Ambroxan, Musk",
                "category": ["Gourmand", "Sweet"],
            },
            {
                "name": "Lattafa Opulent Dubai",
                "brand": "Lattafa",
                "gender": "Unisex",
                "season": "Spring, Summer (versatile year-round in mild climates)",
                "notes": "Top - Mango, Grapefruit, Lemon, Ginger / Heart - Jasmine, Cedarwood, Violet / Base - Woodsy notes, Ambergris, Benzoin, Oakmoss",
                "category": ["Fruity", "Woody", "Fresh"],
            },
            {
                "name": "Lattafa Oud Mood",
                "brand": "Lattafa",
                "gender": "Unisex",
                "season": "Fall, Winter",
                "notes": "Top - Rose, Saffron, Pimento / Heart - Agarwood (Oud), Caramel, Floral Notes, Patchouli / Base - Woody Notes, Amber, Resins, Incense, Musk",
                "category": ["Oriental", "Oud", "Woody"],
            },
            {
                "name": "Lattafa Qaed Al Fursan (Original)",
                "brand": "Lattafa",
                "gender": "Unisex (leans masculine)",
                "season": "Versatile",
                "notes": "Top - Pineapple, Saffron / Heart - Balsam Fir, Jasmine / Base - Cedar, Amber, Agarwood (Oud)",
                "category": ["Fruity", "Woody", "Oud"],
            },
            {
                "name": "Lattafa Qaed Al Fursan Unlimited",
                "brand": "Lattafa",
                "gender": "Male/Unisex",
                "season": "Spring, Fall",
                "notes": "Top - Coconut, Pineapple, Citruses / Heart - Ylang-Ylang, Frangipani, Jasmine / Base - Vanilla, Musk, Sandalwood, Sweet Notes",
                "category": ["Fruity", "Floral", "Sweet"],
            },
            {
                "name": "Lattafa Qaed Al Fursan Untamed",
                "brand": "Lattafa",
                "gender": "Male/Unisex",
                "season": "Spring, Fall",
                "notes": "Top - Apple, Citrus / Heart - Floral / Base - Sweet, Woody",
                "category": ["Fruity", "Woody", "Fresh"],
            },
            {
                "name": "Lattafa Raneen",
                "brand": "Lattafa",
                "gender": "Female",
                "season": "Fall, Winter",
                "notes": "Top - Fruity, Sweet / Heart - Floral / Base - Vanilla, Musk",
                "category": ["Floral", "Fruity", "Sweet"],
            },
            {
                "name": "Lattafa Rave Now (for Women)",
                "brand": "Lattafa",
                "gender": "Female",
                "season": "Spring, Fall",
                "notes": "Top - Red Fruits, Orange / Heart - Marshmallow, Jasmine, Lily of the Valley / Base - Vanilla, Musk, Moss",
                "category": ["Fruity", "Gourmand", "Floral"],
            },
            {
                "name": "Lattafa Rave Now Intense",
                "brand": "Lattafa",
                "gender": "Male/Unisex",
                "season": "Spring, Fall",
                "notes": "Top - Cucumber, Watermelon, Tangerine / Heart - Basil, Sage / Base - Sandalwood, Leather, Cedar",
                "category": ["Fresh", "Woody", "Aromatic"],
            },
            {
                "name": "Lattafa Sakeena",
                "brand": "Lattafa",
                "gender": "Female/Unisex",
                "season": "Fall, Winter",
                "notes": "Top - Passionfruit, Mandarin Orange, Ozonic Notes / Heart - Raspberry, Rose, Orange Blossom, Sea Salt / Base - Toffee, Praline, Vanilla, Musk",
                "category": ["Fruity", "Gourmand", "Floral"],
            },
            {
                "name": "Lattafa Teriaq",
                "brand": "Lattafa",
                "gender": "Unisex (leans feminine)",
                "season": "Fall, Winter",
                "notes": "Top - Caramel, Bitter Almond, Apricot, Pink Pepper / Heart - Honey, Rhubarb, White Flowers, Rose / Base - Leather, Vanilla, Musk, Vetiver, Labdanum",
                "category": ["Gourmand", "Floral", "Oriental"],
            },
            {
                "name": "Lattafa Teriaq Intense",
                "brand": "Lattafa",
                "gender": "Unisex",
                "season": "Fall, Winter",
                "notes": "Top - Saffron, Bergamot / Heart - Plum Liquor, Cinnamon / Base - Amber, Tonka Bean, Benzoin",
                "category": ["Oriental", "Spicy", "Sweet"],
            },
            {
                "name": "Lattafa Vanilla Freak (Give Me Gourmand)",
                "brand": "Lattafa",
                "gender": "Unisex / Female-leaning",
                "season": "Fall, Spring",
                "notes": "Top - Cupcake / Heart - Sugar Frosting, Almond, Cinnamon / Base - Butter, Vanilla, Musk",
                "category": ["Gourmand", "Sweet"],
            },
            {
                "name": "Lattafa Whipped Pleasure (Give Me Gourmand)",
                "brand": "Lattafa",
                "gender": "Female",
                "season": "Fall, Winter",
                "notes": "Top - Caramel, Popcorn, Salted Caramel / Heart - Milk, Jasmine / Base - Tonka, Benzoin, Musk, Ambrofix",
                "category": ["Gourmand", "Sweet"],
            },
            {
                "name": "Lattafa Yara Candy Body Spray",
                "brand": "Lattafa",
                "gender": "Female",
                "season": "Fall, Winter",
                "notes": "Top - Candy, Sweet / Heart - Fruity / Base - Vanilla, Musk",
                "category": ["Gourmand", "Sweet", "Fruity"],
            },
            {
                "name": "Lattafa Yara Tous",
                "brand": "Lattafa",
                "gender": "Female",
                "season": "Versatile",
                "notes": "Top - Fruity, Sweet / Heart - Floral / Base - Vanilla, Musk",
                "category": ["Floral", "Fruity", "Sweet"],
            },
            {
                "name": "Love & Peace",
                "brand": "Lattafa",
                "gender": "Unisex/Female",
                "season": "Spring-Fall",
                "notes": "Soft floral, musky, or peaceful sweet",
                "category": ["Floral", "Sweet"],
            },
            {
                "name": "Maison Alhambra Luxe Chic",
                "brand": "Maison Alhambra",
                "gender": "Female/Unisex",
                "season": "Spring, Fall",
                "notes": "Top - Tangerine, Freesia / Heart - Lily of the Valley, Jasmine, Rose / Base - Musk, Sandalwood, Amber",
                "category": ["Floral", "Fresh"],
            },
            {
                "name": "Maison Asrar Vanilla Aura",
                "brand": "Maison Asrar",
                "gender": "Female/Unisex",
                "season": "Fall, Winter",
                "notes": "Top - Vanilla / Heart - Creamy Sweet / Base - Vanilla, Musk",
                "category": ["Gourmand", "Sweet"],
            },
            {
                "name": "Maison Asrar Vanilla Seduction",
                "brand": "Maison Asrar",
                "gender": "Female/Unisex",
                "season": "Fall, Winter",
                "notes": "Top - Plum, Jasmine, Lily of the Valley / Heart - Vanilla, Brown Sugar, Caramel / Base - Tonka, Patchouli, Amber, Musk",
                "category": ["Gourmand", "Floral", "Sweet"],
            },
            {
                "name": "Majestic Supreme",
                "brand": "Le Falcone",
                "gender": "Women/Unisex",
                "season": "Fall-Winter / versatile",
                "notes": "Top - Rose, peony, pink pepper / Heart - Raspberry blossom, jasmine / Base - Amber, papyrus, tonka, vanilla",
                "category": ["Floral", "Sweet"],
            },
            {
                "name": "Malika",
                "brand": "Nusuk",
                "gender": "Female",
                "season": "Versatile",
                "notes": "Floral or oriental",
                "category": ["Floral", "Oriental"],
            },
            {
                "name": "Mango Affogato",
                "brand": "Arabiyat Sugar",
                "gender": "Unisex",
                "season": "Spring-Summer / year-round",
                "notes": "Top - Mango, nutmeg, clove / Heart - Leather, saffron, amber, moss / Base - Akigalawood, patchouli, vetiver, cypriol",
                "category": ["Fruity", "Woody", "Spicy"],
            },
            {
                "name": "Mango Ice",
                "brand": "Gulf Orchid",
                "gender": "Unisex",
                "season": "Spring-Summer",
                "notes": "Fruity mango with cool/icy facets",
                "category": ["Fruity", "Fresh"],
            },
            {
                "name": "Mayar",
                "brand": "Lattafa",
                "gender": "Female",
                "season": "Spring, Summer",
                "notes": "Top - Lychee, Raspberry, Violet Leaf / Heart - Peony, White Rose, Jasmine / Base - Musk, Vanilla",
                "category": ["Floral", "Fruity", "Fresh"],
            },
            {
                "name": "Mayar Natural Intense Body Spray",
                "brand": "Mayar",
                "gender": "Female",
                "season": "Fall, Winter",
                "notes": "Top - Sweet Gourmand / Heart - Vanilla / Base - Musk",
                "category": ["Gourmand", "Sweet"],
            },
            {
                "name": "Melt Cafe Bliss",
                "brand": "Mamlakat Al Oud / Fragrance World",
                "gender": "Unisex",
                "season": "Fall, Winter",
                "notes": "Top - Black Coffee, Amaretto Liquor / Heart - Vanilla Ice Cream, Speculoos / Base - Vanilla Pods, Brown Sugar, Grey Amber",
                "category": ["Gourmand", "Sweet"],
            },
            {
                "name": "Melt CrÃ¨me Caramel",
                "brand": "Mamlakat Al Oud",
                "gender": "Unisex (leans feminine)",
                "season": "Fall, Winter",
                "notes": "Top - Caramel, Vanilla Flower / Heart - Dulce de Leche, Cotton Candy, Frangipani, White Flowers / Base - Vanilla Pod, Tonka Bean, Musk",
                "category": ["Gourmand", "Sweet"],
            },
            {
                "name": "Melt Marshmallows Kiss",
                "brand": "Mamlakat Al Oud",
                "gender": "Unisex",
                "season": "Fall, Winter, Spring",
                "notes": "Top - Strawberry, Blackberry (or Caramel/Milk) / Heart - Jasmine, Rose, Marshmallow, Vanilla, Honey / Base - Vanilla, Musk, Praline, Tonka",
                "category": ["Gourmand", "Floral", "Sweet"],
            },
            {
                "name": "Melt Vanilla Madness",
                "brand": "Mamlakat Al Oud",
                "gender": "Unisex (leans feminine)",
                "season": "Fall, Winter (versatile year-round)",
                "notes": "Top - Vanilla (woody tones), Lavender, Cacao, Ginger / Heart - Vanilla Caviar / Base - Vanilla Absolute",
                "category": ["Gourmand", "Sweet"],
            },
            {
                "name": "Melt Velvet Breeze",
                "brand": "Mamlakat Al Oud",
                "gender": "Unisex",
                "season": "Fall, Winter",
                "notes": "Top - Italian Bergamot, Pistachio Gelato, Hazelnut, Sweet Rum, Cardamom / Heart - Geranium, White Peony, Muguet, Jasmine / Base - Amber, Musk, Woody Notes",
                "category": ["Gourmand", "Floral", "Woody"],
            },
            {
                "name": "Miss Armaf Mystique",
                "brand": "Armaf",
                "gender": "Female",
                "season": "Fall, Winter",
                "notes": "Top - Pear, Tangerine, Bergamot, Orange / Heart - Vanilla, Strawberry, Mimosa, Rose, Ylang Ylang, Jasmine, Passionfruit / Base - Vanilla, Coffee, Tonka Bean, Patchouli, Vetiver",
                "category": ["Floral", "Fruity", "Gourmand"],
            },
            {
                "name": "Momento",
                "brand": "Riiffs",
                "gender": "Unisex",
                "season": "Versatile",
                "notes": "Soft or aromatic (limited public data)",
                "category": ["Aromatic"],
            },
            {
                "name": "Mystique Charm",
                "brand": "Mystique Charm",
                "gender": "Unisex/Female",
                "season": "Cooler seasons",
                "notes": "Mysterious oriental or floral-woody",
                "category": ["Oriental", "Floral", "Woody"],
            },
            {
                "name": "Nagham",
                "brand": "Atyaab",
                "gender": "Unisex possible",
                "season": "Versatile",
                "notes": "Arabic-style (floral-woody or oriental)",
                "category": ["Floral", "Woody", "Oriental"],
            },
            {
                "name": "Nusuk Falak",
                "brand": "Nusuk",
                "gender": "Unisex",
                "season": "Fall, Winter",
                "notes": "Top - Brown Sugar, Caramel, Biscuit / Heart - Toffee, Vanilla Bean, Amber / Base - White Musk, Praline",
                "category": ["Gourmand", "Sweet"],
            },
            {
                "name": "Obsidian",
                "brand": "French Avenue",
                "gender": "Unisex/Male",
                "season": "Fall-Winter",
                "notes": "Dark, woody, or smoky-oriental",
                "category": ["Woody", "Oriental", "Smoky"],
            },
            {
                "name": "Panache Angel Dust",
                "brand": "Khadlaj",
                "gender": "Female",
                "season": "Spring-Fall / versatile",
                "notes": "Soft, powdery, musk-vanilla / angelic",
                "category": ["Floral", "Sweet", "Powdery"],
            },
            {
                "name": "Paris Corner Eshal Vanilla",
                "brand": "Paris Corner",
                "gender": "Female/Unisex",
                "season": "Fall, Winter",
                "notes": "Top - Sugar, Sweet Notes / Heart - Rose, Jasmine / Base - Vanilla, Caramel, Musk",
                "category": ["Gourmand", "Floral", "Sweet"],
            },
            {
                "name": "Paris Corner Khair Men",
                "brand": "Paris Corner",
                "gender": "Male/Unisex",
                "season": "Fall, Winter",
                "notes": "Top - Davana, Bergamot, Pink Pepper / Heart - Agarwood (Oud), Amber, Rosemary / Base - Leather, Vetiver, Musk",
                "category": ["Woody", "Oud", "Spicy"],
            },
            {
                "name": "Paris Corner Marshmallow Blush",
                "brand": "Paris Corner",
                "gender": "Female/Unisex",
                "season": "Fall, Winter",
                "notes": "Top - Marshmallow, Sweet / Heart - Fruity / Base - Vanilla, Musk",
                "category": ["Gourmand", "Sweet", "Fruity"],
            },
            {
                "name": "Paris Corner Qissa Delicious",
                "brand": "Paris Corner",
                "gender": "Female",
                "season": "Fall, Winter",
                "notes": "Top - Whipped Cream, Dark Chocolate, Orange / Heart - Marshmallow, Coconut, Jasmine / Base - Vanilla, White Musk",
                "category": ["Gourmand", "Sweet"],
            },
            {
                "name": "Pecan Butter Cookie",
                "brand": "Arabiyat Sugar",
                "gender": "Unisex/Female",
                "season": "Fall-Winter",
                "notes": "Top - Pecan, coconut milk, butter / Heart - Hazelnut, almond, roasted nuts / Base - Hazelnut, vanilla, ambergris",
                "category": ["Gourmand", "Sweet"],
            },
            {
                "name": "Phlur Heavy Cream",
                "brand": "Phlur",
                "gender": "Unisex",
                "season": "Fall, Winter",
                "notes": "Top - Marshmallow, Sugar, Citrus / Heart - Coconut, Jasmine / Base - Whipped Cream, Vanilla, Caramel",
                "category": ["Gourmand", "Sweet"],
            },
            {
                "name": "Phlur Vanilla Skin",
                "brand": "Phlur",
                "gender": "Unisex (female-leaning)",
                "season": "Fall, Winter",
                "notes": "Top - Sugar, Pink Pepper, Apple / Heart - Cashmere Wood, Jasmine, Lily / Base - Vanilla, Sandalwood, Agarwood, Benzoin",
                "category": ["Gourmand", "Woody", "Sweet"],
            },
            {
                "name": "Pink Velvet",
                "brand": "Maison Alhambra",
                "gender": "Female",
                "season": "Spring-Fall",
                "notes": "Soft, powdery, rosy, or gourmand-pink",
                "category": ["Floral", "Sweet", "Powdery"],
            },
            {
                "name": "Pink Yara / Yara Pink",
                "brand": "Lattafa",
                "gender": "Female",
                "season": "Spring-Summer",
                "notes": "Top - Orchid, heliotrope, tangerine / Heart - Gourmand accord, tropical fruits / Base - Vanilla, musk, sandalwood",
                "category": ["Floral", "Gourmand", "Fruity"],
            },
            {
                "name": "Raheeq",
                "brand": "Nusuk",
                "gender": "Female/Unisex",
                "season": "Versatile",
                "notes": "Soft, sweet, or floral",
                "category": ["Floral", "Sweet"],
            },
            {
                "name": "Rave Rage",
                "brand": "Lattafa",
                "gender": "Unisex (leans masculine)",
                "season": "Year-round",
                "notes": "Top - Apple, mint / Heart - Geranium, cinnamon, lavender / Base - Vanilla, Peru balsam, cedarwood, guaiac wood",
                "category": ["Fresh", "Woody", "Spicy"],
            },
            {
                "name": "Rasasi Hawas Diva",
                "brand": "Rasasi",
                "gender": "Female",
                "season": "Fall, Winter",
                "notes": "Top - Red Fruits, Rhubarb, Lychee / Heart - Rose, Frankincense, Cedar / Base - Vanilla, Musk, Ambergris",
                "category": ["Fruity", "Floral", "Woody"],
            },
            {
                "name": "Rasasi Hawas Eclat (Eclat Hawas)",
                "brand": "Rasasi",
                "gender": "Female",
                "season": "Spring, Fall",
                "notes": "Top - Litchi/Lychee, Bergamot, Pear, Pistachio / Heart - Rose, Incense / Base - Vanilla, Amber, Musk, Woody Notes",
                "category": ["Fruity", "Floral", "Woody"],
            },
            {
                "name": "Rasasi Hawas Ice",
                "brand": "Rasasi",
                "gender": "Male",
                "season": "Versatile",
                "notes": "Top - Apple, Italian Lemon, Sicilian Bergamot, Star Anise / Heart - Plum, Orange Blossom, Cardamom / Base - Musk, Moss, Driftwood, Amber",
                "category": ["Fresh", "Fruity", "Aromatic"],
            },
            {
                "name": "Rasasi Hawas London",
                "brand": "Rasasi",
                "gender": "Unisex",
                "season": "Fall, Spring",
                "notes": "Top - Pink Pepper, Saffron, Pear / Heart - Rose, Frankincense, White Flowers / Base - Blonde Woods, Vanilla, Amber, Musk",
                "category": ["Floral", "Woody", "Spicy"],
            },
            {
                "name": "Rasasi Hawas Pink",
                "brand": "Rasasi",
                "gender": "Female",
                "season": "Fall, Winter",
                "notes": "Top - Cinnamon, Nutmeg, Neroli / Heart - Marshmallow, Tuberose, Orange Blossom / Base - Cotton Candy, Vanilla, Tonka Bean",
                "category": ["Gourmand", "Floral", "Sweet"],
            },
            {
                "name": "Red Velvet",
                "brand": "Armaf Delights",
                "gender": "Female/Unisex",
                "season": "Fall, Winter",
                "notes": "Top - Strawberry, Lemon / Heart - Whipped Sugar, Sugarberry, Frangipani / Base - Vanilla Bean, Musk, Amber",
                "category": ["Gourmand", "Fruity", "Sweet"],
            },
            {
                "name": "Rizz Tiramisu Candy",
                "brand": "Rizz",
                "gender": "Female",
                "season": "Spring, Fall",
                "notes": "Top - Bergamot / Heart - Blackcurrant, Strawberry Milk / Base - Musk, Vanilla",
                "category": ["Gourmand", "Fruity", "Sweet"],
            },
            {
                "name": "Safa by Nusuk",
                "brand": "Nusuk",
                "gender": "Unisex/Female",
                "season": "Spring-Summer / versatile",
                "notes": "Top - Marshmallow, Strawberry, Lemon / Heart - Coconut, Sugar, Nectarine / Base - Vanilla, Musk, Ambroxan",
                "category": ["Gourmand", "Fruity", "Sweet"],
            },
            {
                "name": "Sahari Ghubar Al Dhahab",
                "brand": "Sahari",
                "gender": "Unisex",
                "season": "Fall, Winter",
                "notes": "Top - Cinnamon, Pear, Mandarin, Floral notes / Heart - Jasmine Sambac, Orange Blossom / Base - White Musk, Vanilla, Tonka Bean, Coffee, Patchouli",
                "category": ["Floral", "Spicy", "Sweet"],
            },
            {
                "name": "Samiya",
                "brand": "Khadlaj",
                "gender": "Female",
                "season": "Versatile",
                "notes": "Floral or oriental",
                "category": ["Floral", "Oriental"],
            },
            {
                "name": "Sara Debai Essences",
                "brand": "Sara Debai",
                "gender": "Female",
                "season": "Spring-Summer",
                "notes": "Top - Heliotrope, orchid, tangerine / Heart - Gourmand accord, tropical fruits / Base - Vanilla, musk, sandalwood",
                "category": ["Floral", "Gourmand", "Fruity"],
            },
            {
                "name": "Spectre / Sceptre Malachite",
                "brand": "Maison Alhambra",
                "gender": "Unisex",
                "season": "Spring-Summer",
                "notes": "Top - Green tangerine, bergamot, blackcurrant / Heart - Aromatic + spicy notes, lavender, pink pepper, jasmine / Base - Amber, musk, woody notes, vetiver",
                "category": ["Fresh", "Aromatic", "Woody"],
            },
            {
                "name": "Strawberry Tres Leches",
                "brand": "Arabiyat Sugar",
                "gender": "Female",
                "season": "Spring-Summer / year-round",
                "notes": "Strawberry + milky cake gourmand",
                "category": ["Gourmand", "Fruity", "Sweet"],
            },
            {
                "name": "Sugar Crown",
                "brand": "Lattafa",
                "gender": "Female/Unisex",
                "season": "Fall-Winter",
                "notes": "Sweet/sugar gourmand",
                "category": ["Gourmand", "Sweet"],
            },
            {
                "name": "Sugar Me Dulce de Leche",
                "brand": "Maison Alhambra",
                "gender": "Unisex/Female",
                "season": "Fall-Winter",
                "notes": "Dulce de leche / caramel-vanilla gourmand",
                "category": ["Gourmand", "Sweet"],
            },
            {
                "name": "Sweet Surrender",
                "brand": "Mahajan",
                "gender": "Female",
                "season": "Fall-Winter / versatile",
                "notes": "Soft sweet/gourmand",
                "category": ["Gourmand", "Sweet"],
            },
            {
                "name": "Sweet Surrender Pink Parfait",
                "brand": "Mahajan",
                "gender": "Female",
                "season": "Spring-Summer / year-round",
                "notes": "Pink/fruity-parfait sweet",
                "category": ["Gourmand", "Fruity", "Sweet"],
            },
            {
                "name": "Tahira",
                "brand": "Riiffs",
                "gender": "Female",
                "season": "Versatile",
                "notes": "Likely floral or oriental (limited public data)",
                "category": ["Floral", "Oriental"],
            },
            {
                "name": "Taif",
                "brand": "Riiffs",
                "gender": "Unisex",
                "season": "Versatile (Spring-Summer preferred)",
                "notes": "Top - Ginger, Calabrian Bergamot, Lemon, Orange Blossom / Heart - Musk, Rose Petals, Tuberose / Base - Vanilla Bean, Amberwood, Clearwood",
                "category": ["Floral", "Fresh", "Woody"],
            },
            {
                "name": "The King",
                "brand": "Ali",
                "gender": "Male",
                "season": "Fall-Winter / versatile",
                "notes": "Masculine woody or oriental",
                "category": ["Woody", "Oriental"],
            },
            {
                "name": "Toffee Ganache",
                "brand": "Arabiyat Sugar",
                "gender": "Unisex",
                "season": "Fall-Winter",
                "notes": "Toffee/chocolate gourmand",
                "category": ["Gourmand", "Sweet"],
            },
            {
                "name": "Valentine Milano",
                "brand": "Valentine",
                "gender": "Unisex",
                "season": "Fall, Winter",
                "notes": "Top - Raspberry, Peach, Bergamot / Heart - Rose, Jasmine, Orange Blossom / Base - Vanilla, Amber, Woods",
                "category": ["Floral", "Fruity", "Sweet"],
            },
            {
                "name": "Valentine Nero Xtravagant",
                "brand": "Valentine (Urban Collection)",
                "gender": "Male / Unisex (leans masculine)",
                "season": "Fall, Winter (versatile)",
                "notes": "Top - Calabrian Bergamot, Espresso Coffee Accord / Heart - Coffee / Base - Vetiver",
                "category": ["Woody", "Fresh", "Aromatic"],
            },
            {
                "name": "Vanilla Addiction",
                "brand": "Gulf Orchid",
                "gender": "Unisex/Female",
                "season": "Fall-Winter",
                "notes": "Vanilla-forward gourmand",
                "category": ["Gourmand", "Sweet"],
            },
            {
                "name": "Vanilla Dunes",
                "brand": "Khadlaj",
                "gender": "Unisex",
                "season": "Autumn, Winter",
                "notes": "Top - Vanilla, Cinnamon, Cardamom, Bergamot / Heart - Orange Blossom, Guaiac Wood, Bourbon / Base - Praline, Amber, Musk",
                "category": ["Gourmand", "Spicy", "Woody"],
            },
            {
                "name": "Yara Elixir",
                "brand": "Lattafa",
                "gender": "Female",
                "season": "Fall, Winter, Cool Spring Days",
                "notes": "Top - Strawberry S'mores, Black Currant / Heart - Jasmine, Orange Blossom / Base - Vanilla, Caramel, Amber, Musk",
                "category": ["Gourmand", "Floral", "Sweet"],
            },
            {
                "name": "Zenith",
                "brand": "Riiffs",
                "gender": "Unisex",
                "season": "Spring-Summer / versatile",
                "notes": "Top - Coconut, Vanilla, Cream / Heart - Rum, Saffron / Base - Cashmeran, Tonka Bean",
                "category": ["Gourmand", "Sweet", "Fresh"],
            },
            {
                "name": "Zimaya Fatima (Fatima Pink)",
                "brand": "Zimaya",
                "gender": "Female",
                "season": "Spring, Fall",
                "notes": "Top - Rhubarb, Bergamot, Grapefruit, Nutmeg / Heart - Rose, Jasmine / Base - Musk, Vanilla, Vetiver, Ambergris",
                "category": ["Floral", "Fruity", "Fresh"],
            },
            {
                "name": "Zimaya Hawwa Red",
                "brand": "Zimaya",
                "gender": "Female",
                "season": "Fall, Winter",
                "notes": "Top - Cassis, Strawberry, Raspberry, Orange / Heart - Black Currant, Grapefruit, Peach, Lily / Base - Musk, Vanilla, Patchouli",
                "category": ["Fruity", "Floral", "Sweet"],
            },
        ]

# ==========================================
# REACTIONS & SOTD (from persisted data)
# ==========================================
if "user_reactions" not in st.session_state:
    st.session_state["user_reactions"] = _persisted.get("user_reactions", {})

if "sotd_history" not in st.session_state:
    st.session_state["sotd_history"] = _persisted.get("sotd_history", [])

if "layer_recipes" not in st.session_state:
    st.session_state["layer_recipes"] = _persisted.get("layer_recipes", [])

if "wishlist" not in st.session_state:
    # list of {name, brand, notes, checked}
    st.session_state["wishlist"] = _persisted.get("wishlist", [])

if "vault_log" not in st.session_state:
    # list of {when, action, name, detail}
    st.session_state["vault_log"] = _persisted.get("vault_log", [])

if "last_saved_at" not in st.session_state:
    st.session_state["last_saved_at"] = _persisted.get("last_saved_at")

if "play_stats" not in st.session_state:
    st.session_state["play_stats"] = _persisted.get(
        "play_stats",
        {"blind_played": 0, "blind_correct": 0, "moods_drawn": 0, "challenges_done": 0},
    )
# ensure key exists on older saves
st.session_state["play_stats"].setdefault("challenges_done", 0)

if "last_export_date" not in st.session_state:
    st.session_state["last_export_date"] = _persisted.get("last_export_date")

# Restore persisted birth-chart signs (Stars tab)
_chart = _persisted.get("chart") or {}
if "chart_sun" not in st.session_state and _chart.get("sun"):
    st.session_state["chart_sun"] = _chart["sun"]
if "chart_moon" not in st.session_state and _chart.get("moon"):
    st.session_state["chart_moon"] = _chart["moon"]
if "chart_rising" not in st.session_state and _chart.get("rising"):
    st.session_state["chart_rising"] = _chart["rising"]
if "chart_venus" not in st.session_state and _chart.get("venus"):
    st.session_state["chart_venus"] = _chart["venus"]


# Session states for clearing inputs explicitly
if "search_input" not in st.session_state:
    st.session_state["search_input"] = ""

if "note_search_input" not in st.session_state:
    st.session_state["note_search_input"] = ""

if "quick_lookup_input" not in st.session_state:
    st.session_state["quick_lookup_input"] = ""

if "add_name" not in st.session_state:
    st.session_state["add_name"] = ""
if "add_brand" not in st.session_state:
    st.session_state["add_brand"] = ""
if "add_season" not in st.session_state:
    st.session_state["add_season"] = "Fall, Winter"
if "add_notes" not in st.session_state:
    st.session_state["add_notes"] = ""
if "sotd_prefill" not in st.session_state:
    st.session_state["sotd_prefill"] = []

# ==========================================
# HELPER FUNCTIONS
# ==========================================



def pacific_today() -> datetime.date:
    """Today in America/Los_Angeles so SOTD matches Pacific users."""
    return datetime.datetime.now(ZoneInfo("America/Los_Angeles")).date()


def normalize_gender(g: str) -> str:
    g = g.lower().strip()
    if re.search(r"\bfemale[- ]?leaning\b|\bleans feminine\b|\bleans female\b", g):
        return "Female-leaning"
    if re.search(r"\bmale[- ]?leaning\b|\bleans masculine\b|\bleans male\b", g):
        return "Male-leaning"
    if g in ["unisex/male", "male/unisex", "male / unisex", "unisex (leans masculine)"]:
        return "Male-leaning"
    if g in [
        "unisex/female",
        "female/unisex",
        "women/unisex",
        "unisex / female-leaning",
        "unisex / female",
        "female / unisex",
    ]:
        return "Female-leaning"
    # slash forms
    if "female" in g and "unisex" in g:
        return "Female-leaning"
    if "male" in g and "unisex" in g:
        return "Male-leaning"
    if g == "male" or g.startswith("male"):
        return "Male"
    if g in ["female", "women"] or g.startswith("female") or g.startswith("women"):
        return "Female"
    return "Unisex"


def matches_gender(fragrance: dict, preferred: str) -> bool:
    if preferred == "Any":
        return True
    fg = normalize_gender(fragrance["gender"])
    if preferred == "Male":
        # Strict: only Male and Male-leaning (no pure Unisex)
        return fg in ["Male", "Male-leaning"]
    if preferred == "Female":
        # Strict: only Female and Female-leaning (no pure Unisex)
        return fg in ["Female", "Female-leaning"]
    if preferred == "Unisex":
        # Pure Unisex + both leanings
        return fg in ["Unisex", "Male-leaning", "Female-leaning"]
    return True


def matches_weather(fragrance: dict, weather: str) -> bool:
    """Strict season matching. 'versatile' alone is NOT enough for Hot or Cold."""
    season = fragrance["season"].lower()
    if weather == "Any":
        return True

    has_summer = "summer" in season
    has_spring = "spring" in season
    has_fall = "fall" in season or "autumn" in season
    has_winter = "winter" in season
    has_cooler = "cooler" in season
    has_mild = "mild" in season
    has_year = "year-round" in season or "year round" in season
    # "versatile" only counts if not locked to the opposite extreme
    has_versatile = "versatile" in season

    is_summer_target = "summer" in weather.lower() or "hot" in weather.lower()
    is_winter_target = "winter" in weather.lower() or "cold" in weather.lower()

    if is_summer_target:
        # Must explicitly mention summer, spring, mild, or year-round.
        # Pure fall/winter (even with "versatile to cooler") is out.
        if has_summer or has_spring or has_mild or has_year:
            return True
        # versatile without cooler/winter-only lock
        if has_versatile and not has_winter and not has_cooler and not (has_fall and not has_spring):
            return True
        return False

    if is_winter_target:
        if has_winter or has_fall or has_cooler:
            return True
        if has_versatile and not has_summer:
            return True
        if has_year:
            return True
        return False

    if weather == "Warm / Mild":
        return has_spring or has_fall or has_mild or has_versatile or has_year or has_summer

    if weather == "Cool / Autumn":
        return has_fall or has_winter or has_cooler or has_versatile or has_year

    return True



def temp_f_to_band(temp_f: float) -> str:
    """Map outdoor temperature ( F) to the app's weather band."""
    if temp_f >= 85:
        return "Hot / Summer"
    if temp_f >= 70:
        return "Warm / Mild"
    if temp_f >= 55:
        return "Cool / Autumn"
    return "Cold / Winter"


def temp_c_to_f(temp_c: float) -> float:
    return temp_c * 9.0 / 5.0 + 32.0


def temp_band_label(temp_f: float) -> str:
    band = temp_f_to_band(temp_f)
    tips = {
        "Hot / Summer": "favor fresh, citrus, light floral, aquatic - go easy on heavy gourmands",
        "Warm / Mild": "versatile, fruity, soft floral, light sweet",
        "Cool / Autumn": "woody, soft spice, light gourmand, amber",
        "Cold / Winter": "gourmand, oriental, oud, vanilla, rich woods",
    }
    return f"{band} - {tips.get(band, '')}"



# Typical daytime outdoor temps ( F) by month for inland / Southern California
# (Fontana-LA basin style: warm dry summers, mild winters)
# Typical daytime outdoor temps ( F)  -  Victorville, CA (High Desert / Mojave)
# Hotter summers, cooler winters than the LA basin
CA_MONTHLY_TEMP_F = {
    1: 60,   # January
    2: 63,   # February
    3: 68,   # March
    4: 74,   # April
    5: 83,   # May
    6: 92,   # June
    7: 98,   # July
    8: 97,   # August
    9: 91,   # September
    10: 79,  # October
    11: 67,  # November
    12: 58,  # December
}

CA_LOCATION_LABEL = "Victorville, CA (High Desert)"


def default_ca_temp_f(day=None) -> int:
    """Suggested outdoor  F for Victorville, CA today (Pacific date)."""
    d = day or pacific_today()
    return int(CA_MONTHLY_TEMP_F.get(d.month, 75))


# Victorville, CA coordinates (High Desert)
CA_LAT = 34.5362
CA_LON = -117.2912


def fetch_live_temp_f(lat: float = CA_LAT, lon: float = CA_LON) -> dict:
    """
    Current outdoor temperature via Open-Meteo (no API key).
    Returns {ok, temp_f, source, detail} or ok=False on failure.
    """
    import json as _json
    import urllib.request

    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        "&current=temperature_2m"
        "&temperature_unit=fahrenheit"
        "&timezone=America%2FLos_Angeles"
    )
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "ScentedDeadGirl/1.0"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            payload = _json.loads(resp.read().decode("utf-8"))
        cur = payload.get("current") or {}
        temp = cur.get("temperature_2m")
        if temp is None:
            return {"ok": False, "detail": "No temperature in response"}
        temp_f = int(round(float(temp)))
        # clamp to slider range
        temp_f = max(30, min(115, temp_f))
        return {
            "ok": True,
            "temp_f": temp_f,
            "source": "Open-Meteo",
            "detail": f"Victorville area ({lat:.2f}, {lon:.2f})",
            "observed": cur.get("time"),
        }
    except Exception as ex:
        return {"ok": False, "detail": str(ex)}


def score_for_temperature(f: dict, temp_f: float) -> int:
    """Extra score from actual outdoor temp vs season labels + families."""
    if temp_f is None:
        return 0
    season = (f.get("season") or "").lower()
    cats = set(f.get("category") or [])
    score = 0
    band = temp_f_to_band(temp_f)

    # Season string alignment
    if band == "Hot / Summer":
        if "summer" in season:
            score += 20
        elif "spring" in season or "mild" in season:
            score += 12
        elif "year-round" in season or "year round" in season:
            score += 8
        if "winter" in season and "summer" not in season:
            score -= 18
        if "cooler" in season and "summer" not in season:
            score -= 10
        # Families that wear well in heat
        for c in ("Fresh", "Citrus", "Aromatic", "Fruity"):
            if c in cats:
                score += 10
        for c in ("Gourmand", "Oud", "Oriental", "Leather"):
            if c in cats:
                score -= 8
        if "Sweet" in cats and "Fresh" not in cats and "Fruity" not in cats:
            score -= 4
    elif band == "Warm / Mild":
        if any(x in season for x in ("spring", "fall", "autumn", "mild", "versatile")):
            score += 14
        if "year-round" in season or "year round" in season:
            score += 10
        for c in ("Floral", "Fruity", "Fresh", "Sweet"):
            if c in cats:
                score += 8
        if "Oud" in cats:
            score -= 4
    elif band == "Cool / Autumn":
        if any(x in season for x in ("fall", "autumn", "cooler")):
            score += 18
        elif "winter" in season:
            score += 12
        elif "versatile" in season or "year-round" in season:
            score += 8
        if "summer" in season and "fall" not in season and "winter" not in season:
            score -= 10
        for c in ("Woody", "Spicy", "Oriental", "Gourmand", "Sweet"):
            if c in cats:
                score += 8
        if "Citrus" in cats and not any(c in cats for c in ("Woody", "Spicy", "Gourmand")):
            score -= 3
    else:  # Cold / Winter
        if "winter" in season:
            score += 20
        elif any(x in season for x in ("fall", "autumn", "cooler")):
            score += 14
        elif "versatile" in season or "year-round" in season:
            score += 8
        if "summer" in season and "winter" not in season:
            score -= 16
        for c in ("Gourmand", "Oriental", "Oud", "Woody", "Spicy", "Sweet", "Leather"):
            if c in cats:
                score += 10
        for c in ("Fresh", "Citrus"):
            if c in cats and not any(x in cats for x in ("Woody", "Gourmand", "Oriental", "Spicy")):
                score -= 6

    return score



def matches_category(fragrance: dict, category: str) -> bool:
    if category == "Any":
        return True
    return category in fragrance["category"]


def matches_occasion(fragrance: dict, occasion: str) -> bool:
    if occasion == "Any":
        return True
    season = fragrance["season"].lower()
    cats = fragrance["category"]
    if occasion == "Daily / Casual":
        return True
    if occasion == "Work / Office":
        return not ("Gourmand" in cats and ("winter" in season or "fall" in season))
    if occasion == "Date / Evening":
        return any(
            c in cats for c in ["Oriental", "Gourmand", "Woody", "Spicy", "Leather", "Oud"]
        )
    if occasion == "Formal / Event":
        return any(c in cats for c in ["Oriental", "Woody", "Floral", "Oud"])
    if occasion == "Outdoor / Sporty":
        return any(c in cats for c in ["Fresh", "Citrus", "Aromatic", "Fruity"])
    return True


def _stable_tiebreak(name: str) -> int:
    """Deterministic small offset from name so ranking is stable across reruns."""
    h = hashlib.md5(name.encode("utf-8")).hexdigest()
    return int(h[:4], 16) % 4  # 0-3


def score_fragrance(
    f: dict, gender: str, weather: str, category: str, occasion: str, temp_f=None
) -> int:
    score = 0
    name = f["name"]

    reaction = st.session_state["user_reactions"].get(name)
    if reaction == "dislike":
        return -999
    elif reaction == "fav":
        score += 50

    season = f["season"].lower()
    cats = f["category"]
    g = normalize_gender(f["gender"])

    if gender == "Any":
        score += 5
    elif gender == "Male":
        if g == "Male":
            score += 15
        elif g == "Male-leaning":
            score += 12
        elif g == "Unisex":
            score += 8
    elif gender == "Female":
        if g == "Female":
            score += 15
        elif g == "Female-leaning":
            score += 12
        elif g == "Unisex":
            score += 8
    elif gender == "Unisex":
        if g == "Unisex":
            score += 15
        else:
            score += 8

    if weather == "Any":
        score += 5
    elif "summer" in weather.lower() or "hot" in weather.lower():
        if "summer" in season:
            score += 15
        elif any(x in season for x in ["spring", "versatile", "year-round"]):
            score += 10
    elif weather == "Warm / Mild":
        if any(x in season for x in ["spring", "fall", "autumn", "mild"]):
            score += 15
        elif any(x in season for x in ["versatile", "year-round"]):
            score += 12
    elif weather == "Cool / Autumn":
        if any(x in season for x in ["fall", "autumn"]):
            score += 15
        elif any(x in season for x in ["winter", "cooler"]):
            score += 12
    elif "winter" in weather.lower() or "cold" in weather.lower():
        if "winter" in season:
            score += 15
        elif any(x in season for x in ["fall", "autumn", "cooler"]):
            score += 12

    if category == "Any":
        score += 5
    elif category in cats:
        score += 15
        if cats and cats[0] == category:
            score += 5

    if occasion == "Any":
        score += 5
    elif occasion == "Daily / Casual":
        score += 8
    elif occasion == "Work / Office":
        score += (
            10
            if not ("Gourmand" in cats and ("winter" in season or "fall" in season))
            else 3
        )
    elif occasion == "Date / Evening":
        score += (
            15
            if any(
                c in cats
                for c in ["Oriental", "Gourmand", "Woody", "Spicy", "Leather", "Oud"]
            )
            else 5
        )
    elif occasion == "Formal / Event":
        score += (
            15
            if any(c in cats for c in ["Oriental", "Woody", "Floral", "Oud"])
            else 5
        )
    elif occasion == "Outdoor / Sporty":
        score += (
            15
            if any(c in cats for c in ["Fresh", "Citrus", "Aromatic", "Fruity"])
            else 4
        )

    # Temperature-aware fine-tuning (degrees beat vague season labels when set)
    if temp_f is not None:
        score += score_for_temperature(f, float(temp_f))

    # Stable tie-breaker instead of random so rankings don't jump every rerun
    score += _stable_tiebreak(name)
    return score


def get_top_fragrances(
    gender: str,
    weather: str,
    category: str,
    occasion: str,
    top_n: int,
    favorites_only: bool = False,
    temp_f=None,
) -> list:
    # If a real temperature is provided, derive the weather band when set to Any
    effective_weather = weather
    if temp_f is not None and (not weather or weather == "Any"):
        effective_weather = temp_f_to_band(float(temp_f))

    scored = []
    for f in st.session_state["fragrances_db"]:
        if st.session_state["user_reactions"].get(f["name"]) == "dislike":
            continue
        if favorites_only and st.session_state["user_reactions"].get(f["name"]) != "fav":
            continue
        if (
            matches_gender(f, gender)
            and matches_weather(f, effective_weather)
            and matches_category(f, category)
            and matches_occasion(f, occasion)
        ):
            s = score_fragrance(
                f, gender, effective_weather, category, occasion, temp_f=temp_f
            )
            scored.append((s, f))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [f for score, f in scored[:top_n]]



# --- Astrology / scent mapping (interpretive, for fun) ---
SIGN_SCENT_PROFILE = {
    "Aries": {
        "element": "Fire",
        "vibe": "Bold, spicy, energetic",
        "categories": ["Spicy", "Fresh", "Citrus", "Woody"],
        "notes_keywords": ["pepper", "ginger", "citrus", "cedar", "cardamom"],
    },
    "Taurus": {
        "element": "Earth",
        "vibe": "Sensual, creamy, grounded",
        "categories": ["Gourmand", "Floral", "Sweet", "Woody"],
        "notes_keywords": ["vanilla", "rose", "sandalwood", "tonka", "caramel"],
    },
    "Gemini": {
        "element": "Air",
        "vibe": "Light, playful, changeable",
        "categories": ["Fresh", "Citrus", "Fruity", "Floral"],
        "notes_keywords": ["citrus", "bergamot", "pear", "tea", "light musk"],
    },
    "Cancer": {
        "element": "Water",
        "vibe": "Soft, milky, nostalgic",
        "categories": ["Gourmand", "Floral", "Sweet", "Fresh"],
        "notes_keywords": ["milk", "coconut", "white flower", "musk", "powder"],
    },
    "Leo": {
        "element": "Fire",
        "vibe": "Warm, radiant, dramatic",
        "categories": ["Gourmand", "Floral", "Sweet", "Oriental"],
        "notes_keywords": ["vanilla", "orange blossom", "honey", "amber", "cinnamon"],
    },
    "Virgo": {
        "element": "Earth",
        "vibe": "Clean, green, precise",
        "categories": ["Fresh", "Floral", "Woody", "Aromatic"],
        "notes_keywords": ["green", "herbal", "iris", "cedar", "clean musk"],
    },
    "Libra": {
        "element": "Air",
        "vibe": "Balanced, elegant, rose-kissed",
        "categories": ["Floral", "Sweet", "Fruity", "Fresh"],
        "notes_keywords": ["rose", "iris", "pear", "musk", "soft floral"],
    },
    "Scorpio": {
        "element": "Water",
        "vibe": "Dark, magnetic, intense",
        "categories": ["Oriental", "Woody", "Oud", "Spicy"],
        "notes_keywords": ["oud", "incense", "patchouli", "dark fruit", "amber"],
    },
    "Sagittarius": {
        "element": "Fire",
        "vibe": "Adventurous, warm, expansive",
        "categories": ["Oriental", "Spicy", "Woody", "Fresh"],
        "notes_keywords": ["cinnamon", "tobacco", "pineapple", "cedar", "saffron"],
    },
    "Capricorn": {
        "element": "Earth",
        "vibe": "Polished, structured, amber-wood",
        "categories": ["Woody", "Oriental", "Gourmand", "Spicy"],
        "notes_keywords": ["amber", "vanilla", "cedar", "leather", "tonka"],
    },
    "Aquarius": {
        "element": "Air",
        "vibe": "Unusual, airy, modern",
        "categories": ["Fresh", "Aromatic", "Woody", "Citrus"],
        "notes_keywords": ["ozonic", "metallic", "violet", "ambroxan", "tea"],
    },
    "Pisces": {
        "element": "Water",
        "vibe": "Dreamy, soft, aquatic-sweet",
        "categories": ["Floral", "Gourmand", "Sweet", "Fresh"],
        "notes_keywords": ["vanilla", "aquatic", "powdery", "lilac", "musk"],
    },
}

# Default chart for sanctuary owner (Fontana CA, 1987-09-30 3:10 AM PDT)
DEFAULT_CHART = {
    "name": "Sanctuary chart",
    "birth_date": "1987-09-30",
    "birth_time": "3:10 AM PDT",
    "birth_place": "Fontana, CA",
    "sun": "Libra",
    "moon": "Capricorn",
    "rising": "Leo",
    "venus": "Libra",
    "notes": "Sun + Venus in Libra (beauty, balance). Moon in Capricorn (structure, amber-wood depth). Leo rising (warm radiance).",
}


def chart_category_weights(sun: str, moon: str, rising: str) -> dict:
    """Blend Big Three into category preference scores."""
    weights = {}
    for sign, weight in ((sun, 3), (moon, 2), (rising, 2)):
        profile = SIGN_SCENT_PROFILE.get(sign, {})
        for cat in profile.get("categories", []):
            weights[cat] = weights.get(cat, 0) + weight
    return weights


# Traditional day rulers -> scent leanings
DAY_RULER = {
    "Monday": {
        "planet": "Moon",
        "vibe": "Soft, emotional, milky-musk comfort",
        "categories": ["Gourmand", "Floral", "Sweet", "Fresh"],
        "notes_keywords": ["milk", "musk", "vanilla", "coconut", "powder", "white flower"],
    },
    "Tuesday": {
        "planet": "Mars",
        "vibe": "Bold, spicy, energetic heat",
        "categories": ["Spicy", "Oriental", "Woody", "Fruity"],
        "notes_keywords": ["pepper", "ginger", "cinnamon", "saffron", "dark fruit"],
    },
    "Wednesday": {
        "planet": "Mercury",
        "vibe": "Light, airy, clean and curious",
        "categories": ["Fresh", "Citrus", "Floral", "Fruity"],
        "notes_keywords": ["citrus", "bergamot", "green", "tea", "pear", "light musk"],
    },
    "Thursday": {
        "planet": "Jupiter",
        "vibe": "Warm, expansive, golden sweetness",
        "categories": ["Oriental", "Gourmand", "Spicy", "Sweet"],
        "notes_keywords": ["amber", "honey", "vanilla", "cinnamon", "tonka", "pineapple"],
    },
    "Friday": {
        "planet": "Venus",
        "vibe": "Romantic, floral, beauty-forward (Libra/Taurus)",
        "categories": ["Floral", "Sweet", "Gourmand", "Fruity"],
        "notes_keywords": ["rose", "iris", "vanilla", "pear", "soft floral", "musk"],
    },
    "Saturday": {
        "planet": "Saturn",
        "vibe": "Polished, structured, amber-wood depth",
        "categories": ["Woody", "Oriental", "Gourmand", "Spicy"],
        "notes_keywords": ["amber", "cedar", "vanilla", "tonka", "leather", "incense"],
    },
    "Sunday": {
        "planet": "Sun",
        "vibe": "Radiant, warm, confident glow (Leo)",
        "categories": ["Gourmand", "Floral", "Sweet", "Oriental"],
        "notes_keywords": ["vanilla", "orange blossom", "honey", "amber", "cinnamon"],
    },
}


def is_female_or_unisex(f: dict) -> bool:
    g = normalize_gender(f.get("gender", ""))
    return g in ("Female", "Female-leaning", "Unisex")


def score_fragrance_for_day(
    f: dict, day: str, sun: str, moon: str, rising: str, venus: str = None
) -> int:
    if st.session_state["user_reactions"].get(f["name"]) == "dislike":
        return -999
    if not is_female_or_unisex(f):
        return -999

    score = 0
    if st.session_state["user_reactions"].get(f["name"]) == "fav":
        score += 30

    # Day ruler categories / notes (primary)
    day_prof = DAY_RULER.get(day, {})
    for c in f.get("category", []):
        if c in day_prof.get("categories", []):
            score += 18
            if f.get("category") and f["category"][0] == c:
                score += 6

    notes_l = f.get("notes", "").lower()
    for kw in day_prof.get("notes_keywords", []):
        if kw.lower() in notes_l:
            score += 8

    # Chart Big Three + Venus (beauty planet  -  strong for fragrance)
    venus = venus or sun
    cat_weights = chart_category_weights(sun, moon, rising)
    # Venus categories get an extra nudge
    for c in SIGN_SCENT_PROFILE.get(venus, {}).get("categories", []):
        cat_weights[c] = cat_weights.get(c, 0) + 2

    for c in f.get("category", []):
        score += cat_weights.get(c, 0) * 3

    for sign in (sun, moon, rising, venus):
        for kw in SIGN_SCENT_PROFILE.get(sign, {}).get("notes_keywords", []):
            if kw.lower() in notes_l:
                score += 5

    # Prefer Female over pure Unisex slightly for this feature
    g = normalize_gender(f.get("gender", ""))
    if g == "Female":
        score += 8
    elif g == "Female-leaning":
        score += 6
    elif g == "Unisex":
        score += 3

    score += _stable_tiebreak(f["name"] + day)
    return score


def explain_day_match(f: dict, day: str, sun: str, moon: str, rising: str, venus: str = None) -> str:
    """Short why-this-bottle line for Stars results."""
    bits = []
    day_prof = DAY_RULER.get(day, {})
    cats = set(f.get("category", []))
    day_hits = [c for c in day_prof.get("categories", []) if c in cats]
    if day_hits:
        bits.append(f"{day_prof.get('planet', day)} day  -  {', '.join(day_hits[:2])}")
    notes_l = (f.get("notes") or "").lower()
    kw_hits = [kw for kw in day_prof.get("notes_keywords", []) if kw.lower() in notes_l]
    venus = venus or sun
    for sign, label in ((sun, "Sun"), (moon, "Moon"), (rising, "Rising"), (venus, "Venus")):
        for kw in SIGN_SCENT_PROFILE.get(sign, {}).get("notes_keywords", []):
            if kw.lower() in notes_l and kw not in kw_hits:
                kw_hits.append(kw)
                bits.append(f"{label} {sign}  -  {kw}")
                break
    if kw_hits and not any(" - " in b and "day" not in b for b in bits):
        bits.append("notes: " + ", ".join(kw_hits[:3]))
    return "  -  ".join(bits[:3]) if bits else "chart + day blend"


def get_day_fragrances(
    day: str, sun: str, moon: str, rising: str, top_n: int = 5, venus: str = None
) -> list:
    scored = []
    for f in st.session_state["fragrances_db"]:
        s = score_fragrance_for_day(f, day, sun, moon, rising, venus=venus)
        if s > 0:
            scored.append((s, f))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [f for _, f in scored[:top_n]]


def write_day_horoscope(day: str, sun: str, moon: str, rising: str, venus: str = None) -> str:
    """Fun interpretive scent-horoscope blurb for the selected day + chart."""
    day_prof = DAY_RULER.get(day, {})
    planet = day_prof.get("planet", "the sky")
    vibe = day_prof.get("vibe", "a shifting mood")
    sun_p = SIGN_SCENT_PROFILE.get(sun, {})
    moon_p = SIGN_SCENT_PROFILE.get(moon, {})
    rise_p = SIGN_SCENT_PROFILE.get(rising, {})
    venus = venus or sun
    ven_p = SIGN_SCENT_PROFILE.get(venus, {})

    echoes = []
    day_cats = set(day_prof.get("categories", []))

    if day == "Friday":
        if sun in ("Libra", "Taurus") or venus in ("Libra", "Taurus") or rising in ("Libra", "Taurus"):
            echoes.append(
                "Venus day flatters your beauty placements  -  soft florals, polished sweetness, and skin-close musk."
            )
        else:
            echoes.append(
                "Venus day invites charm: floral-fruity or creamy gourmand, whichever feels like a compliment."
            )
    elif day == "Saturday":
        if moon == "Capricorn" or sun == "Capricorn" or rising == "Capricorn":
            echoes.append(
                "Saturn day steadies Capricorn energy  -  amber, woods, and structured gourmands feel like armor."
            )
        else:
            echoes.append(
                "Saturn day favors polish and depth  -  woody, oriental, or ambered bottles over pure fluff."
            )
    elif day == "Sunday":
        if rising == "Leo" or sun == "Leo" or moon == "Leo":
            echoes.append(
                "Sun day turns up Leo heat  -  radiant vanilla, honey, and warm florals read as main-character."
            )
        else:
            echoes.append(
                "Sun day asks for confidence and glow  -  warm gourmand, golden floral, or a bold oriental."
            )
    elif day == "Monday":
        if moon_p.get("element") == "Water":
            echoes.append(
                "Moon day over a water Moon favors milky, musky comfort over sharp edges."
            )
        else:
            echoes.append(
                "Moon day softens the pace  -  powder, milk, white florals, or a gentle gourmand hug."
            )
    elif day == "Tuesday":
        if sun_p.get("element") == "Fire" or rise_p.get("element") == "Fire":
            echoes.append(
                "Mars day stokes fire placements  -  spice, projection, and heat without apology."
            )
        else:
            echoes.append(
                "Mars day wants drive  -  pepper, ginger, dark fruit, or a spicy oriental edge."
            )
    elif day == "Wednesday":
        if sun_p.get("element") == "Air" or rise_p.get("element") == "Air":
            echoes.append(
                "Mercury day loves air signs  -  keep it light, citrus-bright, or softly floral."
            )
        else:
            echoes.append(
                "Mercury day stays curious and clean  -  citrus, green, pear, or a breezy floral."
            )
    elif day == "Thursday":
        if any(SIGN_SCENT_PROFILE.get(s, {}).get("element") == "Fire" for s in (sun, rising)):
            echoes.append(
                "Jupiter day expands fire energy  -  golden, honeyed, or warmly spiced trails."
            )
        else:
            echoes.append(
                "Jupiter day goes generous  -  amber, vanilla, tonka, or a lush oriental-gourmand."
            )

    chart_cats = set()
    for sign in (sun, moon, rising, venus):
        chart_cats.update(SIGN_SCENT_PROFILE.get(sign, {}).get("categories", []))
    overlap = list(day_cats & chart_cats)[:3]
    if overlap:
        echoes.append(f"Chart overlap with today: **{', '.join(overlap)}**  -  lean there first.")

    if not echoes:
        echoes.append(
            f"Let {planet}'s mood lead: {vibe.lower()}. "
            f"Your {sun} Sun wants {sun_p.get('vibe', 'balance').lower()}; "
            f"your {moon} Moon reaches for {moon_p.get('vibe', 'comfort').lower()}; "
            f"{rising} rising adds {rise_p.get('vibe', 'presence').lower()}."
        )

    families = ", ".join(day_prof.get("categories", [])[:4])
    venus_line = (
        f"Venus in {venus} steers beauty toward "
        f"{', '.join(ven_p.get('categories', [])[:3]) or 'soft allure'}."
    )
    body = echoes[0]
    if len(echoes) > 1:
        body = echoes[0] + " " + echoes[1]

    nl = "\n"
    return (
        f"**{day}  -  ruled by {planet}.** {vibe}{nl}{nl}"
        f"{body}{nl}{nl}"
        f"{venus_line} Favor these families today: **{families}**."
    )





GOOD_LAYER_PAIRS = [
    ("Gourmand", "Fresh"),
    ("Gourmand", "Floral"),
    ("Gourmand", "Woody"),
    ("Gourmand", "Fruity"),
    ("Sweet", "Fresh"),
    ("Sweet", "Woody"),
    ("Floral", "Woody"),
    ("Floral", "Oriental"),
    ("Fruity", "Woody"),
    ("Fruity", "Fresh"),
    ("Oriental", "Floral"),
    ("Oriental", "Woody"),
    ("Spicy", "Sweet"),
    ("Spicy", "Woody"),
    ("Citrus", "Gourmand"),
    ("Citrus", "Floral"),
    ("Aromatic", "Gourmand"),
    ("Oud", "Floral"),
    ("Oud", "Sweet"),
    ("Gourmand", "Sweet"),
]


def layer_score(f1: dict, f2: dict) -> int:
    if f1["name"] == f2["name"]:
        return -100
    if (
        st.session_state["user_reactions"].get(f1["name"]) == "dislike"
        or st.session_state["user_reactions"].get(f2["name"]) == "dislike"
    ):
        return -100

    cats1 = set(f1["category"])
    cats2 = set(f2["category"])
    score = 0

    if st.session_state["user_reactions"].get(f1["name"]) == "fav":
        score += 10
    if st.session_state["user_reactions"].get(f2["name"]) == "fav":
        score += 10

    for a, b in GOOD_LAYER_PAIRS:
        if (a in cats1 and b in cats2) or (b in cats1 and a in cats2):
            score += 15

    if cats1 & cats2:
        score += 5

    # Stable-ish variation from names
    score += _stable_tiebreak(f1["name"] + f2["name"]) % 5 + 1
    return score


def suggest_recipe_name_from_notes(bottle_names: list) -> str:
    """Build a short poetic recipe name from shared notes and categories."""
    name_map = {f["name"]: f for f in st.session_state.get("fragrances_db") or []}
    frags = [name_map[n] for n in bottle_names if n in name_map]
    if not frags:
        return "Untitled layer"

    # Pull note tokens
    stop = {
        "top", "heart", "base", "and", "with", "notes", "the", "from", "leaning",
        "style", "absolute", "extract", "oil", "of", "a", "an", "for", "into",
    }
    tokens = []
    for f in frags:
        tokens.extend(re.findall(r"[A-Za-z]{4,}", f.get("notes") or ""))
        tokens.extend(f.get("category") or [])
    cleaned = []
    seen = set()
    for t in tokens:
        tl = t.lower()
        if tl in stop or tl in seen:
            continue
        seen.add(tl)
        cleaned.append(t.title())
        if len(cleaned) >= 6:
            break

    # Prefer evocative words
    preferred = [
        "Vanilla", "Coconut", "Rose", "Oud", "Amber", "Musk", "Coffee", "Caramel",
        "Jasmine", "Sandalwood", "Cherry", "Cocoa", "Tobacco", "Leather", "Iris",
        "Peach", "Honey", "Smoke", "Wood", "Citrus", "Marshmallow", "Pistachio",
    ]
    picks = [w for w in preferred if any(w.lower() in (c.lower()) for c in cleaned)]
    if not picks:
        picks = cleaned[:3]
    picks = picks[:3]
    if len(picks) >= 2:
        return f"{picks[0]} {picks[1]} night"
    if picks:
        return f"{picks[0]} veil"
    # Fallback from bottle names
    short = [n.split()[0] for n in bottle_names[:2] if n]
    if len(short) >= 2:
        return f"{short[0]} x {short[1]}"
    return bottle_names[0] if bottle_names else "Untitled layer"


def season_for_layer_recipe(frags: list) -> dict:
    """Guess best seasons for a layer from bottle season labels + categories."""
    if not frags:
        return {"label": "Unknown", "detail": "No bottles", "bands": []}

    band_score = {
        "Hot / Summer": 0,
        "Warm / Mild": 0,
        "Cool / Autumn": 0,
        "Cold / Winter": 0,
    }
    season_bits = []
    for f in frags:
        season = (f.get("season") or "").lower()
        season_bits.append(f.get("season") or "Versatile")
        cats = set(f.get("category") or [])
        if "summer" in season or "hot" in season:
            band_score["Hot / Summer"] += 3
        if "spring" in season or "mild" in season or "warm" in season:
            band_score["Warm / Mild"] += 2
        if "fall" in season or "autumn" in season or "cool" in season:
            band_score["Cool / Autumn"] += 3
        if "winter" in season or "cold" in season:
            band_score["Cold / Winter"] += 3
        if "versatile" in season:
            for k in band_score:
                band_score[k] += 1
        # Category leans
        if cats & {"Fresh", "Citrus", "Fruity"}:
            band_score["Hot / Summer"] += 2
            band_score["Warm / Mild"] += 1
        if cats & {"Floral"}:
            band_score["Warm / Mild"] += 1
            band_score["Cool / Autumn"] += 1
        if cats & {"Gourmand", "Sweet", "Boozy", "Oriental", "Oud", "Spicy"}:
            band_score["Cool / Autumn"] += 2
            band_score["Cold / Winter"] += 2
        if cats & {"Woody", "Leather", "Smoky"}:
            band_score["Cool / Autumn"] += 1
            band_score["Cold / Winter"] += 1

    ranked = sorted(band_score.items(), key=lambda x: x[1], reverse=True)
    top = [b for b, s in ranked if s > 0][:2]
    if not top:
        top = ["Warm / Mild"]
    label = " / ".join(top)
    detail = (
        f"Best for {label}. "
        f"From bottle seasons: {', '.join(season_bits)}."
    )
    return {"label": label, "detail": detail, "bands": top}


def evaluate_layer_recipe(bottle_names: list) -> dict:
    """Score a multi-bottle layer recipe and build a short verdict."""
    name_map = {f["name"]: f for f in st.session_state.get("fragrances_db") or []}
    frags = [name_map[n] for n in bottle_names if n in name_map]
    missing = [n for n in bottle_names if n not in name_map]
    season_info = season_for_layer_recipe(frags)
    suggested_name = suggest_recipe_name_from_notes(bottle_names)
    if len(frags) < 2:
        return {
            "score": 0,
            "verdict": "Need at least two bottles still in the vault.",
            "label": "Incomplete",
            "pairs": [],
            "frags": frags,
            "missing": missing,
            "season": season_info,
            "suggested_name": suggested_name,
        }
    pairs = []
    scores = []
    for i in range(len(frags)):
        for j in range(i + 1, len(frags)):
            s = layer_score(frags[i], frags[j])
            scores.append(s)
            c1 = ", ".join(frags[i].get("category") or [])
            c2 = ", ".join(frags[j].get("category") or [])
            pairs.append(
                {
                    "a": frags[i]["name"],
                    "b": frags[j]["name"],
                    "score": s,
                    "cats": f"{c1} + {c2}",
                }
            )
    avg = sum(scores) / max(1, len(scores))
    if avg >= 25:
        label, verdict = "Strong layer", "Categories support each other - worth wearing together."
    elif avg >= 12:
        label, verdict = "Good layer", "Solid pairing - a little contrast or overlap works."
    elif avg >= 5:
        label, verdict = "Mixed", "Wearable, but may compete. Try less sprays of the louder one."
    else:
        label, verdict = "Risky", "Families may clash. Test on skin before a full wear."
    if any(s <= -50 for s in scores):
        label, verdict = "Avoid", "Includes a DEL bottle or a very weak pair."
    return {
        "score": round(avg, 1),
        "verdict": verdict,
        "label": label,
        "pairs": pairs,
        "frags": frags,
        "missing": missing,
        "season": season_info,
        "suggested_name": suggested_name,
    }


def suggest_layering_combos(pool: list, num_combos: int = 3) -> list:
    source_pool = (
        pool if len(pool) >= 5 else st.session_state["fragrances_db"]
    )
    if len(source_pool) < 2:
        return []

    candidates = []
    for i, f1 in enumerate(source_pool):
        for f2 in source_pool[i + 1 :]:
            s = layer_score(f1, f2)
            if s > -50:
                reason = (
                    f"Combines {', '.join(f1['category'])} notes from {f1['name']} with"
                    f" {', '.join(f2['category'])} notes from {f2['name']} for a"
                    " balanced sillage."
                )
                candidates.append((s, f1, f2, reason))

    candidates.sort(key=lambda x: x[0], reverse=True)
    used = set()
    results = []
    for s, f1, f2, reason in candidates:
        key1, key2 = f1["name"], f2["name"]
        if key1 in used or key2 in used:
            continue
        results.append((f1, f2, reason))
        used.add(key1)
        used.add(key2)
        if len(results) >= num_combos:
            break
    return results





HORROR_SCENT_PROFILES = {
    "Gothic fog": {
        "categories": ["Oriental", "Woody", "Powdery", "Smoky"],
        "notes_keywords": [
            "incense", "smoke", "oud", "amber", "rose", "violet", "iris",
            "leather", "patchouli", "myrrh", "vetiver",
        ],
        "blurb": "Candlelit halls, fog machines, velvet and old churches.",
        "vibe_note": "Gothic fog - horror night",
    },
    "Cabin in the woods": {
        "categories": ["Woody", "Aromatic", "Smoky", "Fresh"],
        "notes_keywords": [
            "pine", "cedar", "wood", "smoke", "moss", "earth", "vetiver",
            "fir", "cypress", "leather",
        ],
        "blurb": "Trees, damp earth, campfire - something is outside the cabin.",
        "vibe_note": "Cabin in the woods - horror night",
    },
    "Slasher neon": {
        "categories": ["Sweet", "Fruity", "Gourmand", "Spicy"],
        "notes_keywords": [
            "cherry", "berry", "pepper", "cinnamon", "caramel",
            "plum", "rose", "metallic",
        ],
        "blurb": "Bright candy blood, 80s neon, popcorn and adrenaline.",
        "vibe_note": "Slasher neon - horror night",
    },
    "Haunted gourmand": {
        "categories": ["Gourmand", "Sweet", "Spicy", "Oriental"],
        "notes_keywords": [
            "vanilla", "cocoa", "coffee", "caramel", "smoke", "tobacco",
            "rum", "almond", "marshmallow",
        ],
        "blurb": "Warm kitchen that should not be empty - sugar and shadow.",
        "vibe_note": "Haunted gourmand - horror night",
    },
    "Vampire lounge": {
        "categories": ["Oriental", "Floral", "Woody", "Leather"],
        "notes_keywords": [
            "rose", "oud", "incense", "musk", "amber",
            "jasmine", "tobacco", "dark",
        ],
        "blurb": "Dark florals, incense, late-night velvet booths.",
        "vibe_note": "Vampire lounge - horror night",
    },
}


def score_for_horror(f: dict, mode: str) -> int:
    profile = HORROR_SCENT_PROFILES.get(mode) or {}
    score = 0
    cats = set(f.get("category") or [])
    notes = (f.get("notes") or "").lower()
    for c in profile.get("categories") or []:
        if c in cats:
            score += 18
    for kw in profile.get("notes_keywords") or []:
        if kw.lower() in notes:
            score += 8
    if st.session_state["user_reactions"].get(f.get("name")) == "fav":
        score += 10
    if st.session_state["user_reactions"].get(f.get("name")) == "dislike":
        score -= 50
    score += _stable_tiebreak((f.get("name") or "") + mode) % 5
    return score


def get_horror_picks(mode: str, top_n: int = 3) -> list:
    scored = []
    for f in st.session_state.get("fragrances_db") or []:
        s = score_for_horror(f, mode)
        if s > 0:
            scored.append((s, f))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [f for _, f in scored[:top_n]]


MOOD_PROFILES = {
    "Cozy": {
        "categories": ["Gourmand", "Sweet", "Woody"],
        "notes_keywords": ["vanilla", "caramel", "milk", "tonka", "amber", "cocoa"],
    },
    "Fierce": {
        "categories": ["Oriental", "Spicy", "Oud", "Leather", "Woody"],
        "notes_keywords": ["oud", "pepper", "incense", "leather", "tobacco", "saffron"],
    },
    "Soft": {
        "categories": ["Floral", "Fresh", "Sweet"],
        "notes_keywords": ["musk", "powder", "iris", "white flower", "pear", "cotton"],
    },
    "Date night": {
        "categories": ["Oriental", "Gourmand", "Floral", "Sweet"],
        "notes_keywords": ["rose", "vanilla", "amber", "jasmine", "praline", "honey"],
    },
    "Focus / work": {
        "categories": ["Fresh", "Citrus", "Aromatic", "Woody"],
        "notes_keywords": ["citrus", "bergamot", "green", "cedar", "tea", "mint"],
    },
    "Rainy day": {
        "categories": ["Gourmand", "Woody", "Oriental", "Floral"],
        "notes_keywords": ["amber", "vanilla", "incense", "wet", "earthy", "tonka"],
    },
    "Main character": {
        "categories": ["Oriental", "Gourmand", "Floral", "Spicy"],
        "notes_keywords": ["amber", "vanilla", "oud", "rose", "cinnamon", "honey"],
    },
}


def score_for_mood(f: dict, mood: str) -> int:
    if st.session_state["user_reactions"].get(f["name"]) == "dislike":
        return -999
    prof = MOOD_PROFILES.get(mood, {})
    score = 0
    if st.session_state["user_reactions"].get(f["name"]) == "fav":
        score += 20
    for c in f.get("category", []):
        if c in prof.get("categories", []):
            score += 15
    notes_l = f.get("notes", "").lower()
    for kw in prof.get("notes_keywords", []):
        if kw in notes_l:
            score += 8
    score += _stable_tiebreak(f["name"] + mood)
    return score


def _norm_name(s: str) -> str:
    s = (s or "").strip().lower()
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def find_duplicate_fragrances(name: str, brand: str) -> dict:
    """Detect exact and near-duplicate bottles before adding."""
    nl = _norm_name(name)
    bl = _norm_name(brand)
    exact = []
    same_name = []
    near = []
    for f in st.session_state.get("fragrances_db") or []:
        fn = _norm_name(f.get("name"))
        fb = _norm_name(f.get("brand"))
        if not fn:
            continue
        if fn == nl and fb == bl:
            exact.append(f)
        elif fn == nl:
            same_name.append(f)
        elif nl and (nl in fn or fn in nl) and (not bl or bl == fb or bl in fb or fb in bl):
            near.append(f)
    return {"exact": exact, "same_name": same_name, "near": near}


def filter_play_pool(gender: str = "Any", season: str = "Any", priced_only: bool = False) -> list:
    """Shared pool filter for Play games."""
    pool = []
    for f in st.session_state.get("fragrances_db") or []:
        if st.session_state["user_reactions"].get(f.get("name")) == "dislike":
            continue
        if gender and gender != "Any" and not matches_gender(f, gender):
            continue
        if season and season != "Any" and not matches_weather(f, season):
            continue
        if priced_only and f.get("price") is None:
            continue
        pool.append(f)
    return pool


def fragrances_in_price_range(min_p: float, max_p: float, gender: str = "Any") -> list:
    hits = []
    for f in st.session_state.get("fragrances_db") or []:
        try:
            px = float(f.get("price")) if f.get("price") is not None else None
        except (TypeError, ValueError):
            px = None
        if px is None:
            continue
        if px < min_p or px > max_p:
            continue
        if gender and gender != "Any" and not matches_gender(f, gender):
            continue
        hits.append(f)
    hits.sort(key=lambda x: float(x.get("price") or 0))
    return hits


def get_mood_picks(mood: str, top_n: int = 3, pool: list = None) -> list:
    source = pool if pool is not None else st.session_state["fragrances_db"]
    scored = []
    for f in source:
        s = score_for_mood(f, mood)
        if s > 0:
            scored.append((s, f))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [f for _, f in scored[:top_n]]


def twin_score(f1: dict, f2: dict) -> int:
    if f1["name"] == f2["name"]:
        return -1
    score = 0
    cats1 = set(f1.get("category", []))
    cats2 = set(f2.get("category", []))
    score += len(cats1 & cats2) * 20
    # shared note tokens
    t1 = set(re.findall(r"[a-zA-Z]{3,}", f1.get("notes", "").lower()))
    t2 = set(re.findall(r"[a-zA-Z]{3,}", f2.get("notes", "").lower()))
    # drop boring words
    stop = {"top", "heart", "base", "and", "with", "notes", "the", "from"}
    t1 -= stop
    t2 -= stop
    score += len(t1 & t2) * 5
    if normalize_gender(f1.get("gender", "")) == normalize_gender(f2.get("gender", "")):
        score += 5
    return score


def find_twins(base: dict, top_n: int = 5) -> list:
    scored = []
    for f in st.session_state["fragrances_db"]:
        s = twin_score(base, f)
        if s > 0:
            scored.append((s, f))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [(s, f) for s, f in scored[:top_n]]


def least_worn(top_n: int = 5) -> list:
    counts = get_wear_counts()
    items = []
    for f in st.session_state["fragrances_db"]:
        if st.session_state["user_reactions"].get(f["name"]) == "dislike":
            continue
        items.append((counts.get(f["name"], 0), f))
    items.sort(key=lambda x: (x[0], x[1]["name"].lower()))
    return items[:top_n]


def sotd_streak() -> int:
    """Consecutive days with a log ending at the most recent log (Pacific)."""
    hist = st.session_state.get("sotd_history") or []
    if not hist:
        return 0
    days = sorted({e.get("date") for e in hist if e.get("date")}, reverse=True)
    if not days:
        return 0
    streak = 1
    for i in range(len(days) - 1):
        try:
            d0 = datetime.date.fromisoformat(days[i])
            d1 = datetime.date.fromisoformat(days[i + 1])
        except ValueError:
            break
        if (d0 - d1).days == 1:
            streak += 1
        else:
            break
    return streak


def compute_badges() -> list:
    badges = []
    hist = st.session_state.get("sotd_history") or []
    favs = [n for n, s in st.session_state.get("user_reactions", {}).items() if s == "fav"]
    recipes = st.session_state.get("layer_recipes") or []
    counts = get_wear_counts()
    unique_worn = len([k for k, v in counts.items() if v > 0])
    layered = sum(1 for e in hist if e.get("is_layering"))
    stats = st.session_state.get("play_stats") or {}

    if hist:
        badges.append("First log")
    if sotd_streak() >= 3:
        badges.append(f"{sotd_streak()}-day streak")
    if layered:
        badges.append("Layer explorer")
    if len(favs) >= 5:
        badges.append("Collector heart")
    if unique_worn >= 10:
        badges.append("10 unique wears")
    if recipes:
        badges.append("Recipe keeper")
    if stats.get("blind_played", 0) >= 1:
        badges.append("Blind bottle brave")
    if stats.get("blind_correct", 0) >= 3:
        badges.append("Nose knows")
    if stats.get("moods_drawn", 0) >= 5:
        badges.append("Mood alchemist")
    if stats.get("challenges_done", 0) >= 3:
        badges.append("Challenge accepter")
    # performance logger
    logged_perf = sum(
        1 for e in hist if e.get("sillage") or e.get("longevity")
    )
    if logged_perf >= 5:
        badges.append("Performance tracker")
    return badges


def suggest_partners_for(base: dict, num: int = 4, gender: str = "Any") -> list:
    """Best layering partners for a single selected fragrance."""
    if not base:
        return []
    pool = st.session_state["fragrances_db"]
    candidates = []
    for f in pool:
        if f["name"] == base["name"]:
            continue
        if gender and gender != "Any" and not matches_gender(f, gender):
            continue
        s = layer_score(base, f)
        if s <= -50:
            continue
        reason = (
            f"Pairs {', '.join(base.get('category', []))} from {base['name']} with "
            f"{', '.join(f.get('category', []))} from {f['name']}."
        )
        candidates.append((s, f, reason))
    candidates.sort(key=lambda x: x[0], reverse=True)
    return [(f, reason) for _, f, reason in candidates[:num]]


def suggest_his_match(her_frags: list, num: int = 4) -> list:
    """Male / male-leaning bottles that complement her selected scent(s)."""
    if not her_frags:
        return []
    her_cats = set()
    her_names = set()
    for f in her_frags:
        her_names.add(f["name"])
        her_cats.update(f.get("category", []))

    # Complementary families for him relative to her profile
    boost_pairs = {
        "Gourmand": ["Woody", "Spicy", "Oriental", "Fresh"],
        "Sweet": ["Woody", "Spicy", "Fresh", "Aromatic"],
        "Floral": ["Woody", "Oriental", "Spicy", "Fresh"],
        "Fruity": ["Woody", "Fresh", "Aromatic", "Spicy"],
        "Oriental": ["Woody", "Fresh", "Spicy", "Aromatic"],
        "Fresh": ["Woody", "Oriental", "Spicy", "Gourmand"],
        "Woody": ["Fresh", "Spicy", "Oriental", "Gourmand"],
        "Spicy": ["Fresh", "Woody", "Gourmand", "Sweet"],
        "Oud": ["Fresh", "Floral", "Woody", "Spicy"],
        "Leather": ["Fresh", "Floral", "Sweet", "Woody"],
        "Citrus": ["Woody", "Oriental", "Spicy", "Aromatic"],
        "Aromatic": ["Woody", "Oriental", "Gourmand", "Fresh"],
    }

    candidates = []
    for f in st.session_state["fragrances_db"]:
        if f["name"] in her_names:
            continue
        if st.session_state["user_reactions"].get(f["name"]) == "dislike":
            continue
        g = normalize_gender(f.get("gender", ""))
        if g not in ("Male", "Male-leaning"):
            # pure Unisex ok as softer option but lower priority
            if g != "Unisex":
                continue
            gender_bonus = 2
        else:
            gender_bonus = 12 if g == "Male" else 9

        score = gender_bonus
        his_cats = set(f.get("category", []))
        # shared family = cohesive couple scent
        shared = her_cats & his_cats
        score += len(shared) * 10
        # complementary families
        for hc in her_cats:
            for good in boost_pairs.get(hc, []):
                if good in his_cats:
                    score += 8
        # layer_score against primary her bottle
        score += max(0, layer_score(her_frags[0], f))
        if st.session_state["user_reactions"].get(f["name"]) == "fav":
            score += 15
        score += _stable_tiebreak(f["name"] + her_frags[0]["name"]) % 5
        if score < 15:
            continue
        shared_txt = ", ".join(shared) if shared else "contrast"
        reason = (
            f"Complements her {', '.join(sorted(her_cats)[:3])} with his "
            f"{', '.join(f.get('category', []))} ({shared_txt})."
        )
        candidates.append((score, f, reason))

    candidates.sort(key=lambda x: x[0], reverse=True)
    return [(f, reason) for _, f, reason in candidates[:num]]


def render_fragrance_card(f: dict, key_prefix: str, show_actions: bool = True):
    """Consistent card display for a fragrance with optional Love/Trash buttons."""
    current_reaction = st.session_state["user_reactions"].get(f["name"])
    status_badge = (
        " YAY"
        if current_reaction == "fav"
        else (" NAH" if current_reaction == "dislike" else "")
    )

    st.info(f"**{f['name']}** by *{f['brand']}*{status_badge}")
    st.write(f"**Gender:** {f['gender']}  |  **Season:** {f['season']}")
    st.write(f"**Category:** {', '.join(f['category'])}")
    st.caption(f"Notes: {f['notes']}")
    bits = []
    if f.get("shelf_status"):
        bits.append(str(f["shelf_status"]))
    if f.get("size_ml"):
        bits.append(f"{f['size_ml']} ml")
    if f.get("price"):
        bits.append(f"${f['price']}")
    if bits:
        st.caption(" | ".join(bits))

    if show_actions:
        col1, col2, col3 = st.columns([1, 1, 4])
        with col1:
            if st.button("YAY", key=f"{key_prefix}_fav_{f['name']}"):
                st.session_state["user_reactions"][f["name"]] = "fav"
                save_persisted_data()
                st.rerun()
        with col2:
            if st.button("DEL", key=f"{key_prefix}_dislike_{f['name']}"):
                st.session_state["user_reactions"][f["name"]] = "dislike"
                save_persisted_data()
                st.rerun()
    st.markdown("---")



def get_last_worn_dates() -> dict:
    """Most recent wear date (YYYY-MM-DD) per fragrance name."""
    last = {}
    for entry in st.session_state.get("sotd_history", []):
        d = entry.get("date")
        if not d:
            continue
        scents = entry.get("scents") or []
        if not scents and entry.get("scent"):
            scents = [p.strip() for p in entry["scent"].split(" + ")]
        for s in scents:
            if s not in last or d > last[s]:
                last[s] = d
    return last


def days_since_worn(name: str):
    """Days since last wear (Pacific today). None if never worn."""
    last = get_last_worn_dates().get(name)
    if not last:
        return None
    try:
        d = datetime.date.fromisoformat(last)
        return (pacific_today() - d).days
    except ValueError:
        return None


def is_incomplete_notes(f: dict) -> bool:
    notes = (f.get("notes") or "").strip().lower()
    if len(notes) < 25:
        return True
    vague = ("limited public data", "not specified", "likely ", "typically ", "or oriental", "or floral")
    return any(v in notes for v in vague)



def search_rank_key(f: dict) -> tuple:
    """Sort key for search results: YAY first, then wear count, complete notes, name."""
    name = f.get("name", "")
    reaction = st.session_state.get("user_reactions", {}).get(name)
    yay = 0 if reaction == "fav" else 1
    dislike = 0 if reaction != "dislike" else 1
    wears = -get_wear_counts().get(name, 0)
    incomplete = 1 if is_incomplete_notes(f) else 0
    return (dislike, yay, incomplete, wears, name.lower())


def rank_search_results(matches: list) -> list:
    return sorted(matches, key=search_rank_key)


def performance_leaderboard(top_n: int = 5) -> dict:
    """Best average sillage / longevity from SOTD logs."""
    # Collect per-bottle samples
    sil_map = {}  # name -> list
    lon_map = {}
    for entry in st.session_state.get("sotd_history") or []:
        scents = entry.get("scents") or []
        if not scents and entry.get("scent"):
            scents = [p.strip() for p in entry["scent"].split(" + ")]
        for s in scents:
            if entry.get("sillage"):
                sil_map.setdefault(s, []).append(int(entry["sillage"]))
            if entry.get("longevity"):
                lon_map.setdefault(s, []).append(int(entry["longevity"]))

    def top_avg(m):
        rows = []
        for name, vals in m.items():
            if not vals:
                continue
            rows.append((sum(vals) / len(vals), len(vals), name))
        rows.sort(key=lambda x: (-x[0], -x[1], x[2]))
        return rows[:top_n]

    return {"sillage": top_avg(sil_map), "longevity": top_avg(lon_map)}



def get_favorite_notes(top_n: int = 12) -> list:
    """Ranked note keywords from YAY bottles."""
    from collections import Counter
    stop = {
        "top", "heart", "base", "and", "with", "notes", "the", "from", "leaning",
        "accord", "style", "family", "version", "original", "intense", "limited",
        "public", "data", "not", "specified", "for", "women", "men",
    }
    c = Counter()
    for f in st.session_state["fragrances_db"]:
        if st.session_state["user_reactions"].get(f["name"]) != "fav":
            continue
        tokens = re.findall(r"[a-zA-Z]{3,}", f.get("notes", "").lower())
        for t in tokens:
            if t not in stop:
                c[t] += 1
    return c.most_common(top_n)


def find_antipodes(base: dict, top_n: int = 5) -> list:
    """Bottles most different from base (opposite families / gender lean)."""
    if not base:
        return []
    base_cats = set(base.get("category", []))
    base_g = normalize_gender(base.get("gender", ""))
    scored = []
    for f in st.session_state["fragrances_db"]:
        if f["name"] == base["name"]:
            continue
        if st.session_state["user_reactions"].get(f["name"]) == "dislike":
            continue
        score = 0
        cats = set(f.get("category", []))
        # reward zero overlap
        score += max(0, 30 - len(base_cats & cats) * 15)
        # reward opposite lean
        g = normalize_gender(f.get("gender", ""))
        if base_g in ("Female", "Female-leaning") and g in ("Male", "Male-leaning"):
            score += 12
        elif base_g in ("Male", "Male-leaning") and g in ("Female", "Female-leaning"):
            score += 12
        # note token divergence
        t1 = set(re.findall(r"[a-zA-Z]{3,}", base.get("notes", "").lower()))
        t2 = set(re.findall(r"[a-zA-Z]{3,}", f.get("notes", "").lower()))
        stop = {"top", "heart", "base", "and", "with", "notes", "the", "from"}
        shared = (t1 - stop) & (t2 - stop)
        score += max(0, 15 - len(shared) * 3)
        score += _stable_tiebreak(base["name"] + f["name"]) % 4
        if score > 10:
            scored.append((score, f))
    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[:top_n]


def suggest_right_now(weather: str = "Any", favorites_only: bool = False, top_n: int = 3) -> list:
    """Quick pick blending today weekday + weather + reactions."""
    day = pacific_today().strftime("%A")
    sun = st.session_state.get("chart_sun", DEFAULT_CHART["sun"])
    moon = st.session_state.get("chart_moon", DEFAULT_CHART["moon"])
    rising = st.session_state.get("chart_rising", DEFAULT_CHART["rising"])
    venus = st.session_state.get("chart_venus", DEFAULT_CHART.get("venus", sun))
    day_picks = get_day_fragrances(day, sun, moon, rising, top_n=15, venus=venus)
    # re-score with weather preference
    scored = []
    for f in day_picks:
        if favorites_only and st.session_state["user_reactions"].get(f["name"]) != "fav":
            continue
        if not matches_weather(f, weather):
            continue
        s = score_fragrance_for_day(f, day, sun, moon, rising, venus=venus)
        if weather != "Any":
            s += 10 if matches_weather(f, weather) else 0
        scored.append((s, f))
    if not scored:
        # fallback to regular top
        return get_top_fragrances("Any", weather, "Any", "Any", top_n, favorites_only=favorites_only)
    scored.sort(key=lambda x: x[0], reverse=True)
    return [f for _, f in scored[:top_n]]


def get_weekly_recipe():
    """Stable layering recipe for the current ISO week."""
    today = pacific_today()
    week_key = f"{today.isocalendar()[0]}-W{today.isocalendar()[1]:02d}"
    cached = st.session_state.get("_weekly_recipe_cache")
    if cached and cached.get("week") == week_key:
        return cached

    # Prefer saved recipes first
    recipes = st.session_state.get("layer_recipes") or []
    if recipes:
        idx = int(hashlib.md5(week_key.encode()).hexdigest()[:6], 16) % len(recipes)
        rec = recipes[idx]
        out = {"week": week_key, "name": rec.get("name", "Weekly layer"), "bottles": list(rec.get("bottles") or [])}
        st.session_state["_weekly_recipe_cache"] = out
        return out

    # Generate one
    pool = get_top_fragrances("Any", "Any", "Any", "Any", 30, favorites_only=False)
    combos = suggest_layering_combos(pool, num_combos=5)
    if not combos:
        return None
    idx = int(hashlib.md5(week_key.encode()).hexdigest()[:6], 16) % len(combos)
    f1, f2, reason = combos[idx]
    out = {
        "week": week_key,
        "name": f"{f1['name']} + {f2['name']}",
        "bottles": [f1["name"], f2["name"]],
        "reason": reason,
    }
    st.session_state["_weekly_recipe_cache"] = out
    return out


CHALLENGE_DECK = [
    "Wear only something you've never layered before.",
    "No gourmands for the next 3 logs.",
    "Only Male-leaning or pure Male this weekend.",
    "Pick a bottle you haven't worn in 14+ days.",
    "Layer a Fresh with a Gourmand today.",
    "Wear your least-worn YAY bottle.",
    "No vanilla-forward scents until tomorrow.",
    "Choose something with oud, leather, or incense.",
    "All-floral day  -  no woody bases if you can help it.",
    "Blind-bottle yourself: pick without looking at the name.",
    "Wear the opposite family of yesterday's SOTD.",
    "Date-night intensity on an ordinary day.",
]


def draw_challenge() -> str:
    today = pacific_today().isoformat()
    seed = int(hashlib.md5(f"challenge-{today}".encode()).hexdigest()[:8], 16)
    return CHALLENGE_DECK[seed % len(CHALLENGE_DECK)]


def average_performance(name: str) -> dict:
    """Average sillage / longevity from SOTD logs that recorded them."""
    sil, lon, n_s, n_l = 0, 0, 0, 0
    for entry in st.session_state.get("sotd_history", []):
        scents = entry.get("scents") or []
        if not scents and entry.get("scent"):
            scents = [p.strip() for p in entry["scent"].split(" + ")]
        if name not in scents:
            continue
        if entry.get("sillage"):
            sil += int(entry["sillage"])
            n_s += 1
        if entry.get("longevity"):
            lon += int(entry["longevity"])
            n_l += 1
    return {
        "sillage": round(sil / n_s, 1) if n_s else None,
        "longevity": round(lon / n_l, 1) if n_l else None,
        "samples": max(n_s, n_l),
    }


def export_journal_markdown() -> str:
    """Pretty markdown export of SOTD history + stats."""
    lines = ["# ScentedDeadGirl Journal", ""]
    lines.append(f"_Exported {pacific_today().isoformat()} (Pacific)_")
    lines.append("")
    lines.append(f"- Bottles in vault: **{len(st.session_state['fragrances_db'])}**")
    lines.append(f"- SOTD logs: **{len(st.session_state.get('sotd_history') or [])}**")
    lines.append(f"- Current streak: **{sotd_streak()}** day(s)")
    badges = compute_badges()
    if badges:
        lines.append(f"- Badges: {', '.join(badges)}")
    fav_notes = get_favorite_notes(8)
    if fav_notes:
        lines.append(f"- Favorite notes: {', '.join(f'{n} ({c})' for n, c in fav_notes)}")
    lines.append("")
    lines.append("## History")
    lines.append("")
    for entry in st.session_state.get("sotd_history") or []:
        layer = " _(layering)_" if entry.get("is_layering") else ""
        notes = f"  -  {entry['notes']}" if entry.get("notes") else ""
        perf = ""
        if entry.get("sillage") or entry.get("longevity"):
            parts = []
            if entry.get("sillage"):
                parts.append(f"sillage {entry['sillage']}/5")
            if entry.get("longevity"):
                parts.append(f"longevity {entry['longevity']}/5")
            perf = f" [{', '.join(parts)}]"
        his = ""
        if entry.get("his_scent"):
            his = f" | his: {entry['his_scent']}"
        lines.append(f"- **{entry.get('date', '?')}**: {entry.get('scent', '?')}{layer}{his}{perf}{notes}")
    lines.append("")
    return "\n".join(lines)


def season_family_summary() -> dict:
    """Count category wears in the last 30 days for a simple heatmap-style summary."""
    from collections import Counter
    cutoff = pacific_today() - datetime.timedelta(days=30)
    cat_counts = Counter()
    name_map = {f["name"]: f for f in st.session_state["fragrances_db"]}
    for entry in st.session_state.get("sotd_history") or []:
        try:
            d = datetime.date.fromisoformat(entry.get("date", ""))
        except ValueError:
            continue
        if d < cutoff:
            continue
        scents = entry.get("scents") or []
        if not scents and entry.get("scent"):
            scents = [p.strip() for p in entry["scent"].split(" + ")]
        for s in scents:
            fr = name_map.get(s)
            if fr:
                for c in fr.get("category", []):
                    cat_counts[c] += 1
    return dict(cat_counts.most_common())



def get_wear_counts() -> dict:
    """Count how many times each fragrance appears in SOTD history."""
    counts = {}
    for entry in st.session_state.get("sotd_history", []):
        scents = entry.get("scents") or []
        if not scents and entry.get("scent"):
            scents = [p.strip() for p in entry["scent"].split(" + ")]
        for s in scents:
            counts[s] = counts.get(s, 0) + 1
    return counts



def _image_to_data_url(uploaded_file, max_side: int = 640) -> str:
    """Compress uploaded image to a small JPEG data URL for SOTD storage."""
    import base64
    import io
    try:
        from PIL import Image
    except ImportError:
        raw = uploaded_file.getvalue()
        b64 = base64.b64encode(raw).decode("ascii")
        mime = getattr(uploaded_file, "type", None) or "image/jpeg"
        return f"data:{mime};base64,{b64}"
    img = Image.open(uploaded_file).convert("RGB")
    w, h = img.size
    scale = min(1.0, float(max_side) / max(w, h))
    if scale < 1.0:
        img = img.resize((int(w * scale), int(h * scale)))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=72, optimize=True)
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    return f"data:image/jpeg;base64,{b64}"


def _pdf_escape(s: str) -> str:
    return (
        str(s)
        .replace("\\", "\\\\")
        .replace("(", "\\(")
        .replace(")", "\\)")
        .replace("\r", " ")
        .replace("\n", " ")
    )


def build_simple_pdf(title: str, lines: list) -> bytes:
    """Minimal single/multi-page PDF using only the standard library (no fpdf)."""
    # Page size letter, 72 pt = 1 inch
    page_w, page_h = 612, 792
    margin = 50
    font_size = 11
    leading = 16
    max_chars = 90

    def wrap(text, width=max_chars):
        text = str(text or "")
        words = text.split()
        rows, cur = [], ""
        for w in words:
            trial = (cur + " " + w).strip()
            if len(trial) <= width:
                cur = trial
            else:
                if cur:
                    rows.append(cur)
                cur = w
        if cur:
            rows.append(cur)
        return rows or [""]

    # Build page content streams
    pages = []
    y = page_h - margin
    content = []

    def new_page():
        nonlocal y, content
        if content:
            pages.append(content)
        content = []
        y = page_h - margin

    def add_line(text, size=font_size, bold=False):
        nonlocal y
        for row in wrap(text):
            if y < margin + leading:
                new_page()
            # Helvetica
            content.append(f"BT /F1 {size} Tf 50 {y} Td ({_pdf_escape(row)}) Tj ET")
            y -= leading

    add_line(title, size=16)
    y -= 6
    for line in lines:
        add_line(line, size=11)
    new_page()
    if not pages:
        pages = [["BT /F1 11 Tf 50 742 Td (Empty) Tj ET"]]

    # Assemble PDF objects
    out = []
    out.append(b"%PDF-1.4\n")
    offsets = [0]

    def add_obj(data: bytes):
        offsets.append(sum(len(x) for x in out))
        out.append(f"{len(offsets)-1} 0 obj\n".encode("latin-1"))
        out.append(data)
        out.append(b"\nendobj\n")

    # 1: Catalog
    add_obj(b"<< /Type /Catalog /Pages 2 0 R >>")
    # 2: Pages
    kids = " ".join(f"{3+i} 0 R" for i in range(len(pages)))
    add_obj(f"<< /Type /Pages /Kids [{kids}] /Count {len(pages)} >>".encode("latin-1"))
    # Page objects + content streams
    # Layout: pages start at 3, content streams after all pages
    content_ids = []
    for i, page_ops in enumerate(pages):
        stream_id = 3 + len(pages) + i
        content_ids.append(stream_id)
        page_obj = (
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {page_w} {page_h}] "
            f"/Contents {stream_id} 0 R /Resources << /Font << /F1  {3+2*len(pages)} 0 R >> >> >>"
        )
        # Fix font id - use fixed font object after all streams
    # Rebuild with correct references
    out = [b"%PDF-1.4\n"]
    offsets = [0]
    objects = []

    def obj(data: bytes):
        objects.append(data)

    font_id = 3 + 2 * len(pages)  # after pages + streams
    obj(b"<< /Type /Catalog /Pages 2 0 R >>")  # 1
    kids = " ".join(f"{3+i} 0 R" for i in range(len(pages)))
    obj(f"<< /Type /Pages /Kids [{kids}] /Count {len(pages)} >>".encode("latin-1"))  # 2
    for i, page_ops in enumerate(pages):
        stream_id = 3 + len(pages) + i
        obj(
            (
                f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {page_w} {page_h}] "
                f"/Contents {stream_id} 0 R /Resources << /Font << /F1 {font_id} 0 R >> >> >>"
            ).encode("latin-1")
        )
    for page_ops in pages:
        body = "\n".join(page_ops).encode("latin-1", errors="replace")
        obj(f"<< /Length {len(body)} >>\nstream\n".encode("latin-1") + body + b"\nendstream")
    obj(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")

    # Write with offsets
    result = [b"%PDF-1.4\n"]
    offs = [0]
    for i, data in enumerate(objects, 1):
        offs.append(sum(len(x) for x in result))
        result.append(f"{i} 0 obj\n".encode("latin-1"))
        result.append(data)
        result.append(b"\nendobj\n")
    xref_pos = sum(len(x) for x in result)
    result.append(f"xref\n0 {len(objects)+1}\n".encode("latin-1"))
    result.append(b"0000000000 65535 f \n")
    for o in offs[1:]:
        result.append(f"{o:010d} 00000 n \n".encode("latin-1"))
    result.append(
        f"trailer\n<< /Size {len(objects)+1} /Root 1 0 R >>\nstartxref\n{xref_pos}\n%%EOF\n".encode(
            "latin-1"
        )
    )
    return b"".join(result)



SHELF_STATUSES = ["Own", "Decant", "Traveling", "Finished", "Wishlist-bound"]


def log_vault_action(action: str, name: str, detail: str = "") -> None:
    """Append a short vault activity entry (newest first)."""
    entry = {
        "when": pacific_today().isoformat(),
        "action": action,
        "name": name,
        "detail": detail or "",
    }
    log = st.session_state.setdefault("vault_log", [])
    log.insert(0, entry)
    st.session_state["vault_log"] = log[:200]  # cap


def collection_value_summary(db: list) -> dict:
    """Rough totals from optional size_ml / price fields."""
    total_ml = 0.0
    total_price = 0.0
    priced = 0
    sized = 0
    by_shelf = {}
    for f in db:
        shelf = f.get("shelf_status") or "Own"
        by_shelf[shelf] = by_shelf.get(shelf, 0) + 1
        try:
            ml = float(f.get("size_ml") or 0)
            if ml > 0:
                total_ml += ml
                sized += 1
        except (TypeError, ValueError):
            pass
        try:
            px = float(f.get("price") or 0)
            if px > 0:
                total_price += px
                priced += 1
        except (TypeError, ValueError):
            pass
    return {
        "total_ml": total_ml,
        "total_price": total_price,
        "priced": priced,
        "sized": sized,
        "by_shelf": by_shelf,
    }


def build_fragrance_sheet_pdf(frag: dict, title: str = None) -> bytes:
    """One-page PDF summary for a single bottle (add receipt / share sheet)."""
    title = title or "ScentedDeadGirl - Bottle sheet"
    lines = [
        f"Exported {pacific_today().isoformat()} (Pacific)",
        "",
        f"Name: {frag.get('name', '?')}",
        f"Brand: {frag.get('brand', '?')}",
        f"Gender: {frag.get('gender', '?')}",
        f"Season: {frag.get('season', '?')}",
        f"Categories: {', '.join(frag.get('category') or [])}",
        f"Shelf: {frag.get('shelf_status') or 'Own'}",
    ]
    if frag.get("size_ml"):
        lines.append(f"Size: {frag.get('size_ml')} ml")
    if frag.get("price"):
        lines.append(f"Price: ${frag.get('price')}")
    lines.append("")
    lines.append("Notes:")
    notes = frag.get("notes") or "Not specified"
    # soft-wrap long notes
    lines.append(notes)
    return build_simple_pdf(title, lines)


def notes_lookup_suggestions(name: str, brand: str = "") -> dict:
    """Local vault matches + online links for notes, gender, season, categories."""
    name = (name or "").strip()
    brand = (brand or "").strip()
    q = f"{brand} {name}".strip() or name
    local = []
    if name:
        nl = name.lower()
        bl = brand.lower()
        for f in st.session_state.get("fragrances_db") or []:
            fn = (f.get("name") or "").lower()
            fb = (f.get("brand") or "").lower()
            if nl in fn or fn in nl or (bl and bl in fb and len(nl) >= 3 and nl[:4] in fn):
                local.append(f)
            elif bl and bl == fb and abs(len(fn) - len(nl)) <= 3:
                local.append(f)
    seen = set()
    uniq = []
    for f in local:
        if f.get("name") not in seen:
            seen.add(f.get("name"))
            uniq.append(f)

    links = {}
    if q:
        q_enc = urllib.parse.quote_plus(q)
        links["Notes (Google)"] = (
            f"https://www.google.com/search?q={urllib.parse.quote_plus(q + ' perfume notes pyramid')}"
        )
        links["Gender (Google)"] = (
            f"https://www.google.com/search?q={urllib.parse.quote_plus(q + ' perfume for men or women unisex')}"
        )
        links["Season (Google)"] = (
            f"https://www.google.com/search?q={urllib.parse.quote_plus(q + ' perfume best season weather')}"
        )
        links["Category / accords (Google)"] = (
            f"https://www.google.com/search?q={urllib.parse.quote_plus(q + ' perfume accords main notes family')}"
        )
        links["Price (Google)"] = (
            f"https://www.google.com/search?q={urllib.parse.quote_plus(q + ' perfume price buy')}"
        )
        links["Price shopping (Google)"] = (
            f"https://www.google.com/search?tbm=shop&q={urllib.parse.quote_plus(q + ' perfume')}"
        )
        links["Fragrantica search"] = (
            f"https://www.fragrantica.com/search/?query={q_enc}"
        )
        links["Parfumo search"] = (
            f"https://www.parfumo.com/s_j_perfumes.php?in={q_enc}"
        )
        links["Fragrantica (Google site)"] = (
            f"https://www.google.com/search?q={urllib.parse.quote_plus('site:fragrantica.com ' + q)}"
        )
        links["FragranceNet (Google site)"] = (
            f"https://www.google.com/search?q={urllib.parse.quote_plus('site:fragrancenet.com ' + q)}"
        )
        links["Jomashop (Google site)"] = (
            f"https://www.google.com/search?q={urllib.parse.quote_plus('site:jomashop.com ' + q + ' perfume')}"
        )

    return {"local": uniq[:8], "links": links, "query": q}


def wishlist_item_to_vault(item: dict) -> dict:
    """Add a wishlist entry into fragrances_db if not a duplicate."""
    name = (item.get("name") or "").strip()
    brand = (item.get("brand") or "").strip() or "Unknown"
    if not name:
        return {"ok": False, "message": "Missing name", "frag": None}
    dups = find_duplicate_fragrances(name, brand)
    if dups.get("exact") or dups.get("same_name"):
        existing = (dups.get("exact") or dups.get("same_name") or [None])[0]
        label = f"{existing.get('name')} ({existing.get('brand')})" if existing else name
        return {"ok": False, "message": f"Already in vault: {label}", "frag": existing}
    notes = (item.get("notes") or "").strip() or "From wishlist"
    frag = {
        "name": name,
        "brand": brand,
        "gender": "Unisex",
        "season": "Versatile",
        "notes": notes,
        "category": ["Gourmand"],
        "dupe_of": "",
        "shelf_status": "Own",
        "size_ml": None,
        "price": None,
    }
    st.session_state["fragrances_db"].append(frag)
    try:
        log_vault_action("added", name, f"from wishlist / {brand}")
    except Exception:
        pass
    return {"ok": True, "message": f"Added {name} to vault", "frag": frag}


def build_wishlist_pdf(items: list) -> bytes:
    """PDF checklist of wishlist entries (no external PDF library required)."""
    lines = [f"Exported {pacific_today().isoformat()} (Pacific)", ""]
    if not items:
        lines.append("Wishlist is empty.")
    for item in items:
        mark = "[x]" if item.get("checked") else "[ ]"
        line = f"{mark}  {item.get('name', '?')}"
        if item.get("brand"):
            line += f"  ({item.get('brand')})"
        lines.append(line)
        if item.get("notes"):
            lines.append(f"    {item['notes']}")
        lines.append("")
    return build_simple_pdf("ScentedDeadGirl Wishlist", lines)


def build_sotd_week_pdf(week_key: str = None) -> bytes:
    """PDF of SOTD entries for one ISO week (default: current Pacific week)."""
    today = pacific_today()
    if week_key:
        try:
            year = int(week_key.split("-W")[0])
            week = int(week_key.split("-W")[1])
            monday = datetime.date.fromisocalendar(year, week, 1)
        except Exception:
            monday = today - datetime.timedelta(days=today.weekday())
            week_key = f"{monday.isocalendar()[0]}-W{monday.isocalendar()[1]:02d}"
    else:
        monday = today - datetime.timedelta(days=today.weekday())
        week_key = f"{monday.isocalendar()[0]}-W{monday.isocalendar()[1]:02d}"
    sunday = monday + datetime.timedelta(days=6)

    entries = []
    for e in st.session_state.get("sotd_history") or []:
        d = e.get("date")
        if not d:
            continue
        try:
            dd = datetime.date.fromisoformat(d)
        except ValueError:
            continue
        if monday <= dd <= sunday:
            entries.append(e)
    entries.sort(key=lambda x: x.get("date", ""))

    lines = [
        f"Week {week_key}  ({monday.isoformat()} to {sunday.isoformat()})",
        f"Exported {today.isoformat()} (Pacific)",
        "",
    ]
    if not entries:
        lines.append("No SOTD logs in this week.")
    for e in entries:
        layer = " [layer]" if e.get("is_layering") else ""
        lines.append(f"{e.get('date', '?')}: {e.get('scent', '?')}{layer}")
        bits = []
        if e.get("his_scent"):
            bits.append(f"his: {e['his_scent']}")
        if e.get("sillage"):
            bits.append(f"sillage {e['sillage']}/5")
        if e.get("longevity"):
            bits.append(f"longevity {e['longevity']}/5")
        if e.get("notes"):
            bits.append(str(e["notes"]))
        if bits:
            lines.append("  " + " | ".join(bits))
        lines.append("")
    return build_simple_pdf("ScentedDeadGirl SOTD - Weekly", lines)



def sun_sign_from_date(month: int, day: int) -> str:
    """Tropical sun sign from month/day (no birth time needed)."""
    md = (month, day)
    ranges = [
        (1, 19, "Capricorn"),
        (2, 18, "Aquarius"),
        (3, 20, "Pisces"),
        (4, 19, "Aries"),
        (5, 20, "Taurus"),
        (6, 20, "Gemini"),
        (7, 22, "Cancer"),
        (8, 22, "Leo"),
        (9, 22, "Virgo"),
        (10, 22, "Libra"),
        (11, 21, "Scorpio"),
        (12, 21, "Sagittarius"),
        (12, 31, "Capricorn"),
    ]
    for em, ed, sign in ranges:
        if md <= (em, ed):
            return sign
    return "Capricorn"


_SIGN_ABBREV = {
    "ari": "Aries",
    "tau": "Taurus",
    "gem": "Gemini",
    "can": "Cancer",
    "leo": "Leo",
    "vir": "Virgo",
    "lib": "Libra",
    "sco": "Scorpio",
    "sag": "Sagittarius",
    "cap": "Capricorn",
    "aqu": "Aquarius",
    "pis": "Pisces",
}


def normalize_sign_name(sign: str) -> str:
    if not sign:
        return ""
    s = str(sign).strip()
    if s in SIGN_SCENT_PROFILE:
        return s
    key = s[:3].lower()
    return _SIGN_ABBREV.get(key, s.title())


def geocode_birth_place(city: str, country: str = "United States") -> dict:
    """Resolve city to lat/lon via Open-Meteo geocoding (no API key)."""
    import json as _json
    import urllib.request

    city = (city or "").strip()
    if not city:
        return {"ok": False, "detail": "City is required"}
    q = urllib.parse.quote_plus(f"{city}")
    url = (
        "https://geocoding-api.open-meteo.com/v1/search"
        f"?name={q}&count=5&language=en&format=json"
    )
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "ScentedDeadGirl/1.0"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            payload = _json.loads(resp.read().decode("utf-8"))
        results = payload.get("results") or []
        if not results:
            return {"ok": False, "detail": f"No location found for '{city}'"}
        # Prefer matching country name when possible
        country_l = (country or "").strip().lower()
        chosen = results[0]
        if country_l:
            for r in results:
                ctry = (r.get("country") or "").lower()
                if country_l in ctry or ctry in country_l:
                    chosen = r
                    break
        lat = float(chosen["latitude"])
        lon = float(chosen["longitude"])
        label = ", ".join(
            p
            for p in [
                chosen.get("name"),
                chosen.get("admin1"),
                chosen.get("country"),
            ]
            if p
        )
        # Simple US timezone guess by longitude bands (good enough for chart calc input)
        tz = "UTC"
        ctry = (chosen.get("country") or "").lower()
        if "united states" in ctry or ctry == "usa":
            if lon <= -115:
                tz = "America/Los_Angeles"
            elif lon <= -100:
                tz = "America/Denver"
            elif lon <= -85:
                tz = "America/Chicago"
            else:
                tz = "America/New_York"
        elif "canada" in ctry:
            tz = "America/Toronto"
        elif "united kingdom" in ctry or ctry == "uk":
            tz = "Europe/London"
        return {
            "ok": True,
            "lat": lat,
            "lon": lon,
            "label": label,
            "tz_str": tz,
            "country": chosen.get("country") or country,
        }
    except Exception as ex:
        return {"ok": False, "detail": str(ex)}


def _norm360(x: float) -> float:
    return x % 360.0


def _longitude_to_sign(lon: float) -> str:
    signs = [
        "Aries",
        "Taurus",
        "Gemini",
        "Cancer",
        "Leo",
        "Virgo",
        "Libra",
        "Scorpio",
        "Sagittarius",
        "Capricorn",
        "Aquarius",
        "Pisces",
    ]
    return signs[int(_norm360(lon) // 30) % 12]


def _julian_day_utc(year, month, day, hour, minute, second=0.0) -> float:
    """Julian Day for a UTC datetime."""
    y = year
    m = month
    if m <= 2:
        y -= 1
        m += 12
    A = int(y / 100)
    B = 2 - A + int(A / 4)
    day_frac = (hour + minute / 60.0 + second / 3600.0) / 24.0
    return (
        int(365.25 * (y + 4716))
        + int(30.6001 * (m + 1))
        + day
        + day_frac
        + B
        - 1524.5
    )


def _local_to_jd_utc(year, month, day, hour, minute, tz_str: str) -> float:
    """Convert local civil time in tz_str to Julian Day (UTC)."""
    try:
        tz = ZoneInfo(tz_str) if tz_str else ZoneInfo("UTC")
    except Exception:
        tz = ZoneInfo("UTC")
    local_dt = datetime.datetime(
        int(year), int(month), int(day), int(hour), int(minute), 0, tzinfo=tz
    )
    utc_dt = local_dt.astimezone(ZoneInfo("UTC"))
    return _julian_day_utc(
        utc_dt.year,
        utc_dt.month,
        utc_dt.day,
        utc_dt.hour,
        utc_dt.minute,
        utc_dt.second,
    )


def _sun_longitude(jd: float) -> float:
    """Approximate apparent Sun longitude (degrees), good to ~0.01 deg."""
    import math

    T = (jd - 2451545.0) / 36525.0
    L0 = _norm360(280.46646 + 36000.76983 * T + 0.0003032 * T * T)
    M = math.radians(
        _norm360(357.52911 + 35999.05029 * T - 0.0001537 * T * T)
    )
    C = (
        (1.914602 - 0.004817 * T - 0.000014 * T * T) * math.sin(M)
        + (0.019993 - 0.000101 * T) * math.sin(2 * M)
        + 0.000289 * math.sin(3 * M)
    )
    true_long = L0 + C
    # omega / nutation simplified (aberation-ish)
    omega = math.radians(_norm360(125.04 - 1934.136 * T))
    lam = true_long - 0.00569 - 0.00478 * math.sin(omega)
    return _norm360(lam)


def _moon_longitude(jd: float) -> float:
    """Approximate Moon ecliptic longitude (degrees). Sign-level accuracy."""
    import math

    T = (jd - 2451545.0) / 36525.0
    Lp = math.radians(
        _norm360(218.3164477 + 481267.88123421 * T - 0.0015786 * T * T)
    )
    D = math.radians(
        _norm360(297.8501921 + 445267.1114034 * T - 0.0018819 * T * T)
    )
    M = math.radians(
        _norm360(357.5291092 + 35999.0502909 * T - 0.0001536 * T * T)
    )
    Mp = math.radians(
        _norm360(134.9633964 + 477198.8675055 * T + 0.0087414 * T * T)
    )
    F = math.radians(
        _norm360(93.2720950 + 483202.0175233 * T - 0.0036539 * T * T)
    )
    # Major periodic terms (degrees)
    lon = (
        6.288774 * math.sin(Mp)
        + 1.274027 * math.sin(2 * D - Mp)
        + 0.658314 * math.sin(2 * D)
        + 0.213618 * math.sin(2 * Mp)
        - 0.185116 * math.sin(M)
        - 0.114332 * math.sin(2 * F)
        + 0.058793 * math.sin(2 * D - 2 * Mp)
        + 0.057212 * math.sin(2 * D - M - Mp)
        + 0.053320 * math.sin(2 * D + Mp)
        + 0.045874 * math.sin(2 * D - M)
        + 0.041024 * math.sin(Mp - M)
        - 0.034718 * math.sin(D)
        - 0.030465 * math.sin(M + Mp)
    )
    return _norm360(math.degrees(Lp) + lon)


def _helio_planet_longitude(jd: float, L0, nL, M0, nM, e_c1, e_c2=0.0) -> float:
    """Very simplified mean heliocentric longitude + equation of center."""
    import math
    T = (jd - 2451545.0) / 36525.0
    L = _norm360(L0 + nL * T)
    M = math.radians(_norm360(M0 + nM * T))
    C = e_c1 * math.sin(M) + e_c2 * math.sin(2 * M)
    return _norm360(L + C)


def _venus_longitude(jd: float) -> float:
    import math
    T = (jd - 2451545.0) / 36525.0
    L = _norm360(181.979801 + 58517.8156760 * T)
    M = math.radians(_norm360(50.4161 + 58517.803863 * T))
    C = 0.775 * math.sin(M) + 0.003 * math.sin(2 * M)
    earth_L = _norm360(100.46435 + 35999.37297 * T)
    helio = L + C
    return _norm360(helio + 1.2 * math.sin(math.radians(helio - earth_L)))


def _mercury_longitude(jd: float) -> float:
    import math
    T = (jd - 2451545.0) / 36525.0
    L = _norm360(252.250906 + 149472.6746358 * T)
    M = math.radians(_norm360(174.7948 + 149472.5153 * T))
    C = 23.4400 * math.sin(M) + 2.9818 * math.sin(2 * M)
    earth_L = _norm360(100.46435 + 35999.37297 * T)
    helio = L + C
    return _norm360(helio + 3.0 * math.sin(math.radians(helio - earth_L)))


def _mars_longitude(jd: float) -> float:
    import math
    T = (jd - 2451545.0) / 36525.0
    L = _norm360(355.433 + 19140.3023 * T)
    M = math.radians(_norm360(19.3730 + 19140.2993 * T))
    C = 10.691 * math.sin(M) + 0.623 * math.sin(2 * M)
    earth_L = _norm360(100.46435 + 35999.37297 * T)
    helio = L + C
    return _norm360(helio + 1.5 * math.sin(math.radians(earth_L - helio)))


def _jupiter_longitude(jd: float) -> float:
    return _helio_planet_longitude(jd, 34.351519, 3034.9057, 19.8950, 3034.6920, 5.555, 0.168)


def _saturn_longitude(jd: float) -> float:
    return _helio_planet_longitude(jd, 50.0774, 1222.1138, 317.0207, 1221.5515, 6.406, 0.223)


def _uranus_longitude(jd: float) -> float:
    return _helio_planet_longitude(jd, 314.0550, 428.4669, 141.0498, 428.4952, 5.347, 0.0)


def _neptune_longitude(jd: float) -> float:
    return _helio_planet_longitude(jd, 304.3487, 218.4862, 256.2250, 218.4862, 1.024, 0.0)


def _pluto_longitude(jd: float) -> float:
    # Very rough mean motion for sign-level only
    return _helio_planet_longitude(jd, 238.958, 145.178, 14.862, 145.178, 10.0, 0.0)


def _lilith_longitude(jd: float) -> float:
    """Mean Black Moon Lilith (lunar apogee) approximation, degrees."""
    import math
    T = (jd - 2451545.0) / 36525.0
    # Mean longitude of lunar apogee (Meeus-style approx)
    return _norm360(
        83.353 + 4069.0137 * T - 0.01032 * T * T
        - 0.00015 * T * T * T
    )


def _obliquity(jd: float) -> float:
    import math
    T = (jd - 2451545.0) / 36525.0
    return math.radians(23.439291 - 0.0130042 * T)


def _gmst_degrees(jd: float) -> float:
    T = (jd - 2451545.0) / 36525.0
    gmst = (
        280.46061837
        + 360.98564736629 * (jd - 2451545.0)
        + 0.000387933 * T * T
        - T * T * T / 38710000.0
    )
    return _norm360(gmst)


def _ascendant_longitude(jd: float, lat_deg: float, lon_deg: float) -> float:
    import math
    eps = _obliquity(jd)
    lst = math.radians(_norm360(_gmst_degrees(jd) + lon_deg))
    lat = math.radians(lat_deg)
    y = math.cos(lst)
    x = -(math.sin(lst) * math.cos(eps) + math.tan(lat) * math.sin(eps))
    return _norm360(math.degrees(math.atan2(y, x)))


def _equal_houses_from_asc(asc_lon: float) -> dict:
    """Equal house system: House 1 cusp = Ascendant, each house +30 deg."""
    houses = {}
    for n in range(1, 13):
        cusp = _norm360(asc_lon + (n - 1) * 30.0)
        houses[n] = {
            "cusp": round(cusp, 2),
            "sign": _longitude_to_sign(cusp),
        }
    return houses


def _planet_block(lon: float) -> dict:
    return {
        "lon": round(_norm360(lon), 2),
        "sign": _longitude_to_sign(lon),
        "deg_in_sign": round(_norm360(lon) % 30.0, 2),
    }


def calculate_full_chart(
    year: int,
    month: int,
    day: int,
    hour: int,
    minute: int,
    city: str,
    nation: str = "US",
    lat: float = None,
    lon: float = None,
    tz_str: str = None,
) -> dict:
    """
    Tropical chart: luminaries, classical + modern planets, Lilith, 12 equal houses.
    Sign-level accuracy for fragrance / vibe use (not a pro natal service).
    """
    sun_fallback = sun_sign_from_date(month, day)
    result = {
        "ok": True,
        "sun": sun_fallback,
        "moon": None,
        "rising": None,
        "venus": None,
        "planets": {},
        "houses": {},
        "lilith": None,
        "engine": "built-in",
        "detail": "",
        "place_label": city,
    }

    # Optional kerykeion enrichment for core points if installed
    try:
        from kerykeion import AstrologicalSubject
        kwargs = {}
        if lat is not None and lon is not None:
            kwargs["lat"] = float(lat)
            kwargs["lng"] = float(lon)
        if tz_str:
            kwargs["tz_str"] = tz_str
        subject = AstrologicalSubject(
            "ScentedDeadGirl",
            int(year), int(month), int(day), int(hour), int(minute),
            city or "Unknown", nation or "US", **kwargs,
        )
        def _sign(obj):
            if obj is None:
                return None
            if isinstance(obj, dict):
                return normalize_sign_name(obj.get("sign") or "")
            return normalize_sign_name(getattr(obj, "sign", "") or "")
        result["sun"] = _sign(getattr(subject, "sun", None)) or sun_fallback
        result["moon"] = _sign(getattr(subject, "moon", None))
        result["rising"] = _sign(getattr(subject, "first_house", None)) or _sign(
            getattr(subject, "ascendant", None)
        )
        result["venus"] = _sign(getattr(subject, "venus", None))
        result["engine"] = "kerykeion+built-in"
    except Exception:
        pass

    try:
        tz = tz_str or "UTC"
        jd = _local_to_jd_utc(year, month, day, hour, minute, tz)
        bodies = {
            "Sun": _sun_longitude(jd),
            "Moon": _moon_longitude(jd),
            "Mercury": _mercury_longitude(jd),
            "Venus": _venus_longitude(jd),
            "Mars": _mars_longitude(jd),
            "Jupiter": _jupiter_longitude(jd),
            "Saturn": _saturn_longitude(jd),
            "Uranus": _uranus_longitude(jd),
            "Neptune": _neptune_longitude(jd),
            "Pluto": _pluto_longitude(jd),
            "Lilith": _lilith_longitude(jd),
        }
        planets = {name: _planet_block(lon) for name, lon in bodies.items()}
        result["planets"] = planets
        result["lilith"] = planets.get("Lilith")
        result["sun"] = planets["Sun"]["sign"]
        result["moon"] = planets["Moon"]["sign"]
        result["venus"] = planets["Venus"]["sign"]

        rising_s = None
        houses = {}
        if lat is not None and lon is not None:
            asc_lon = _ascendant_longitude(jd, float(lat), float(lon))
            rising_s = _longitude_to_sign(asc_lon)
            houses = _equal_houses_from_asc(asc_lon)
            planets["Ascendant"] = _planet_block(asc_lon)
            # Midheaven approx: RAMC-based rough MC = LST projected - use asc+90 for equal
            mc_lon = _norm360(asc_lon + 90.0)
            planets["MC"] = _planet_block(mc_lon)
        result["rising"] = rising_s
        result["houses"] = houses
        result["engine"] = "built-in-full"
        result["detail"] = (
            "Tropical signs for Sun through Pluto, Mean Lilith, and 12 equal houses "
            "(House 1 = Rising). Sign-level accuracy for sanctuary use."
        )
        if rising_s is None:
            result["detail"] += " Rising/houses need a successful place lookup."
        return result
    except Exception as ex:
        result["engine"] = "sun-only"
        result["detail"] = f"Full chart failed ({ex}). Sun from calendar date only."
        return result


# ==========================================
# STREAMLIT USER INTERFACE
# ==========================================
st.markdown(
    """
<div class="sdg-hero">
  <div class="sdg-hero-kicker">Fragrance sanctuary</div>
  <div class="sdg-hero-title">ScentedDeadGirl</div>
  <p class="sdg-hero-sub">Recommend - layer - log - curate - High Desert nights, bottle by bottle.</p>
  <div class="sdg-chip-row">
    <span class="sdg-chip">Victorville - F</span>
    <span class="sdg-chip">Navy vault</span>
    <span class="sdg-chip">Night palette</span>
  </div>
</div>
""",
    unsafe_allow_html=True,
)

# ---------- SIDEBAR ----------
with st.sidebar:
    _add_flash = st.session_state.pop("_add_flash", None)
    if _add_flash:
        st.success(_add_flash)

    st.markdown("### Search")
    # Clear search fields before widgets if flagged
    if st.session_state.pop("_clear_search", False):
        st.session_state["search_input"] = ""
        st.session_state["note_search_input"] = ""
        st.session_state["quick_lookup_input"] = ""

    search_query = st.text_input(
        "Name or brand",
        placeholder="e.g. Lattafa, Eclaire",
        key="search_input",
    )
    note_query = st.text_input(
        "Note keyword",
        placeholder="e.g. Vanilla, Coffee",
        key="note_search_input",
    )
    quick_query = st.text_input(
        "Quick notes lookup",
        placeholder="e.g. Ajwad",
        key="quick_lookup_input",
    )
    if st.button("Clear search", use_container_width=True, key="clear_search_btn"):
        st.session_state["_clear_search"] = True
        st.rerun()

    if quick_query:
        matched_quick = [
            f
            for f in st.session_state["fragrances_db"]
            if quick_query.lower() in f["name"].lower()
        ]
        if matched_quick:
            for f in matched_quick[:5]:
                st.info(
                    f"**{f['name']}** ({f['brand']})\n\n"
                    f"**Notes:** {f['notes']}\n\n**Season:** {f['season']}"
                )
        else:
            st.warning("No match.")

    st.markdown("---")
    # Persistence status (edits live in JSON beside the script)
    _saved = st.session_state.get("last_saved_at")
    if _saved:
        st.caption(f"Vault last saved: {_saved}")
    else:
        st.caption("Vault saves to scented_dead_girl_data.json on every edit.")
    st.caption("Export JSON from Vault after big changes so Cloud redeploys cannot wipe edits.")

    st.markdown("### Temp search")
    st.caption(
        "Victorville, CA High Desert - use live outdoor temp or set degrees (F) + gender."
    )
    ca_default = int(default_ca_temp_f())
    if st.session_state.pop("_reset_temp_search", False):
        st.session_state["temp_search_f"] = ca_default
        st.session_state["temp_search_gender"] = "Any"
        st.session_state.pop("live_temp_meta", None)
    # Apply live temp BEFORE slider widget exists
    if st.session_state.pop("_apply_live_temp", False):
        live = st.session_state.get("live_temp_meta") or {}
        if live.get("ok") and live.get("temp_f") is not None:
            st.session_state["temp_search_f"] = int(live["temp_f"])
    if "temp_search_f" not in st.session_state:
        st.session_state["temp_search_f"] = ca_default
    if "temp_search_gender" not in st.session_state:
        st.session_state["temp_search_gender"] = "Any"

    temp_search_gender = st.selectbox(
        "Gender for temp search",
        ["Any", "Male", "Female", "Unisex"],
        key="temp_search_gender",
    )
    temp_search_f = st.slider(
        "Temperature (F)",
        min_value=30,
        max_value=115,
        key="temp_search_f",
    )
    band = temp_f_to_band(float(temp_search_f))
    live_meta = st.session_state.get("live_temp_meta") or {}
    live_note = ""
    if live_meta.get("ok"):
        live_note = (
            f" | Live: {live_meta.get('temp_f')} F"
            f" ({live_meta.get('source', 'weather')}"
            f"{', ' + live_meta['observed'] if live_meta.get('observed') else ''})"
        )
    st.caption(
        f"{int(temp_search_f)} F -> {temp_band_label(float(temp_search_f))} | "
        f"Monthly norm: {ca_default} F{live_note}"
    )
    ts1, ts2, ts3 = st.columns(3)
    with ts1:
        temp_search_clicked = st.button(
            "Search by temp", type="primary", use_container_width=True, key="temp_search_btn"
        )
    with ts2:
        if st.button("Use live temp", use_container_width=True, key="temp_live_btn"):
            result = fetch_live_temp_f()
            st.session_state["live_temp_meta"] = result
            if result.get("ok"):
                st.session_state["_apply_live_temp"] = True
                st.rerun()
            else:
                st.session_state["_live_temp_error"] = result.get("detail", "Lookup failed")
                st.rerun()
    with ts3:
        if st.button("Reset temp", use_container_width=True, key="temp_search_reset"):
            st.session_state["_reset_temp_search"] = True
            st.session_state.pop("last_temp_search", None)
            st.rerun()
    _live_err = st.session_state.pop("_live_temp_error", None)
    if _live_err:
        st.warning(f"Live temp unavailable: {_live_err}. Using slider / monthly norm.")
    if temp_search_clicked:
        picks = get_top_fragrances(
            temp_search_gender,
            "Any",
            "Any",
            "Any",
            5,
            favorites_only=False,
            temp_f=float(temp_search_f),
        )
        st.session_state["last_temp_search"] = {
            "picks": picks,
            "temp_f": float(temp_search_f),
            "gender": temp_search_gender,
            "band": band,
        }
        st.rerun()

    st.markdown("---")
    st.markdown("### Price lookup")
    st.caption("Bottles with a logged price in range.")
    if st.session_state.pop("_clear_price_sb", False):
        st.session_state["price_sb_min"] = 0
        st.session_state["price_sb_max"] = 100
        st.session_state["price_sb_gender"] = "Any"
        st.session_state.pop("price_sb_hits", None)
    if "price_sb_min" not in st.session_state:
        st.session_state["price_sb_min"] = 0
    if "price_sb_max" not in st.session_state:
        st.session_state["price_sb_max"] = 100
    if "price_sb_gender" not in st.session_state:
        st.session_state["price_sb_gender"] = "Any"

    st.number_input("Min $", min_value=0, max_value=2000, key="price_sb_min")
    st.number_input("Max $", min_value=0, max_value=5000, key="price_sb_max")
    st.selectbox(
        "Gender",
        ["Any", "Male", "Female", "Unisex"],
        key="price_sb_gender",
    )
    psb1, psb2 = st.columns(2)
    with psb1:
        if st.button("Find prices", type="primary", use_container_width=True, key="price_sb_btn"):
            lo = float(min(st.session_state["price_sb_min"], st.session_state["price_sb_max"]))
            hi = float(max(st.session_state["price_sb_min"], st.session_state["price_sb_max"]))
            hits = fragrances_in_price_range(lo, hi, st.session_state["price_sb_gender"])
            st.session_state["price_sb_hits"] = {"hits": hits, "lo": lo, "hi": hi}
    with psb2:
        if st.button("Reset", use_container_width=True, key="price_sb_reset"):
            st.session_state["_clear_price_sb"] = True
            st.rerun()
    priced_n = sum(
        1
        for f in st.session_state.get("fragrances_db") or []
        if f.get("price") is not None
    )
    st.caption(f"{priced_n} priced bottle(s) in vault")
    psb = st.session_state.get("price_sb_hits")
    if psb is not None:
        hits = psb.get("hits") or []
        st.write(f"**{len(hits)}** in ${psb.get('lo'):.0f}-${psb.get('hi'):.0f}")
        if not hits:
            st.caption("None in range. Add prices in Edit bottle.")
        else:
            for f in hits[:12]:
                st.caption(
                    f"${float(f.get('price')):.0f} - {f.get('name')} ({f.get('brand')})"
                )
            if len(hits) > 12:
                st.caption(f"...and {len(hits) - 12} more (see Collection tab)")

    st.markdown("---")
    st.markdown("### Recommend filters")

    # Reset filters to defaults before widgets if flagged
    if st.session_state.pop("_clear_filters", False):
        st.session_state["filter_gender"] = "Any"
        st.session_state["filter_weather"] = "Any"
        st.session_state["filter_category"] = "Any"
        st.session_state["filter_occasion"] = "Any"
        st.session_state["filter_num_recs"] = 3
        st.session_state["filter_favorites_only"] = False
        st.session_state.pop("last_recs", None)

    gender = st.selectbox(
        "Gender",
        ["Any", "Male", "Female", "Unisex"],
        key="filter_gender",
    )

    weather = st.selectbox(
        "Season / weather",
        ["Any", "Hot / Summer", "Warm / Mild", "Cool / Autumn", "Cold / Winter"],
        key="filter_weather",
        help="Season band used as a hard filter for recommendations.",
    )
    category = st.selectbox(
        "Category",
        [
            "Any",
            "Gourmand",
            "Floral",
            "Woody",
            "Oriental",
            "Fresh",
            "Fruity",
            "Spicy",
            "Citrus",
            "Aromatic",
            "Sweet",
            "Oud",
            "Leather",
            "Boozy",
        ],
        key="filter_category",
    )
    occasion = st.selectbox(
        "Occasion",
        [
            "Any",
            "Daily / Casual",
            "Work / Office",
            "Date / Evening",
            "Formal / Event",
            "Outdoor / Sporty",
        ],
        key="filter_occasion",
    )
    num_recs = st.radio(
        "How many",
        [1, 3, 5],
        index=1,
        horizontal=True,
        key="filter_num_recs",
    )
    favorites_only = st.checkbox(
        "Favorites only",
        value=False,
        key="filter_favorites_only",
    )
    generate_clicked = st.button(
        "Generate recommendations", type="primary", use_container_width=True
    )
    if st.button("Clear filters", use_container_width=True, key="clear_filters_btn"):
        st.session_state["_clear_filters"] = True
        st.rerun()

    st.markdown("---")
    st.markdown("### Add fragrance")

    # Notes helper (outside form so links work without submitting)
    with st.expander("Fragrance lookup helper", expanded=False):
        st.caption(
            "Search your vault and open Google / Fragrantica / Parfumo for notes, "
            "gender, season, category, and price. Sites are not auto-scraped; "
            "use the links and copy what you need into the form."
        )
        if st.session_state.pop("_clear_notes_help", False):
            st.session_state["notes_help_name"] = ""
            st.session_state["notes_help_brand"] = ""
            st.session_state.pop("notes_help_result", None)
            st.session_state.pop("prefill_new_notes", None)

        h1, h2 = st.columns(2)
        with h1:
            help_name = st.text_input("Lookup name", key="notes_help_name")
        with h2:
            help_brand = st.text_input("Lookup brand", key="notes_help_brand")
        hb1, hb2 = st.columns(2)
        with hb1:
            if st.button("Look up", key="notes_help_btn", use_container_width=True):
                st.session_state["notes_help_result"] = notes_lookup_suggestions(
                    help_name, help_brand
                )
        with hb2:
            if st.button("Clear finder", key="notes_help_clear", use_container_width=True):
                st.session_state["_clear_notes_help"] = True
                st.rerun()

        help_res = st.session_state.get("notes_help_result")
        if help_res:
            if help_res.get("local"):
                st.markdown("**Similar in your vault**")
                for f in help_res["local"]:
                    cats = ", ".join(f.get("category") or [])
                    price_bit = ""
                    if f.get("price") is not None:
                        try:
                            price_bit = f" | Price: ${float(f.get('price')):.0f}"
                        except (TypeError, ValueError):
                            price_bit = ""
                    st.write(
                        f"**{f.get('name')}** ({f.get('brand')})  \n"
                        f"Gender: {f.get('gender', '?')} | Season: {f.get('season', '?')} | "
                        f"Category: {cats}{price_bit}  \n"
                        f"Notes: {(f.get('notes') or '')[:160]}"
                    )
                    b1, b2 = st.columns(2)
                    with b1:
                        if st.button(
                            "Use notes",
                            key=f"use_notes_{f.get('name')}",
                        ):
                            st.session_state["prefill_new_notes"] = f.get("notes") or ""
                            st.session_state["add_notes_field"] = f.get("notes") or ""
                            st.success("Notes prefilled in the Add form.")
                            st.rerun()
                    with b2:
                        if st.button(
                            "Use full profile",
                            key=f"use_profile_{f.get('name')}",
                        ):
                            st.session_state["prefill_new_notes"] = f.get("notes") or ""
                            st.session_state["add_notes_field"] = f.get("notes") or ""
                            st.session_state["lookup_profile_hint"] = {
                                "gender": f.get("gender"),
                                "season": f.get("season"),
                                "category": list(f.get("category") or []),
                                "price": f.get("price"),
                                "from": f.get("name"),
                            }
                            st.success(
                                "Notes prefilled. Gender / season / category / price shown below "
                                "to copy into the Add form."
                            )
                            st.rerun()

            hint = st.session_state.get("lookup_profile_hint")
            if hint:
                price_line = ""
                if hint.get("price") is not None:
                    try:
                        price_line = f"  \n**Price:** ${float(hint.get('price')):.0f}"
                    except (TypeError, ValueError):
                        price_line = ""
                st.info(
                    f"Suggested from **{hint.get('from')}**:  \n"
                    f"**Gender:** {hint.get('gender')}  \n"
                    f"**Season:** {hint.get('season')}  \n"
                    f"**Categories:** {', '.join(hint.get('category') or [])}"
                    f"{price_line}"
                )

            links = help_res.get("links") or {}
            if links:
                st.markdown("**Search online**")
                st.caption(
                    "Google / Fragrantica / Parfumo for notes, gender, season, category, and price. "
                    "Copy what you find into the Add form. Sites are not auto-filled."
                )
                for label, url in links.items():
                    st.markdown(f"- [{label}]({url})")
            st.caption("Clear finder resets lookup fields and results.")

    # Prefill notes if helper requested it
    if "prefill_new_notes" in st.session_state and "add_notes_field" not in st.session_state:
        st.session_state["add_notes_field"] = st.session_state.pop("prefill_new_notes")

    with st.form("add_fragrance_form", clear_on_submit=True):
        new_name = st.text_input("Name")
        new_brand = st.text_input("Brand")
        new_gender = st.selectbox(
            "Gender",
            ["Unisex", "Female", "Male", "Female-leaning", "Male-leaning"],
        )
        new_season = st.text_input("Season", value="Fall, Winter")
        new_notes = st.text_input(
            "Notes",
            placeholder="Top - ... / Heart - ... / Base - ...",
            key="add_notes_field",
        )
        new_shelf = st.selectbox("Shelf status", SHELF_STATUSES, index=0)
        new_size = st.text_input("Size (ml)", placeholder="e.g. 100")
        new_price = st.text_input("Price (optional)", placeholder="e.g. 35")
        new_cats = st.multiselect(
            "Categories",
            [
                "Gourmand",
                "Sweet",
                "Floral",
                "Woody",
                "Oriental",
                "Fresh",
                "Fruity",
                "Spicy",
                "Citrus",
                "Aromatic",
                "Leather",
                "Oud",
                "Boozy",
                "Smoky",
                "Powdery",
            ],
        )
        c_add, c_clear = st.columns(2)
        with c_add:
            submit_added = st.form_submit_button(
                "Add to collection", use_container_width=True
            )
        with c_clear:
            # clear_on_submit=True clears fields after any form submit
            clear_add_form = st.form_submit_button(
                "Clear form", use_container_width=True
            )

        if clear_add_form:
            st.session_state["_add_flash"] = "Form cleared."
            # fields are cleared by clear_on_submit; no vault change

        if submit_added:
            if new_name and new_brand:
                dups = find_duplicate_fragrances(new_name, new_brand)
                if dups["exact"]:
                    st.error(
                        f"Already in the vault: **{dups['exact'][0].get('name')}** by "
                        f"*{dups['exact'][0].get('brand')}*. Duplicate not added."
                    )
                elif dups["same_name"]:
                    brands = ", ".join(
                        sorted({(x.get("brand") or "?") for x in dups["same_name"]})
                    )
                    st.error(
                        f"A bottle named **{new_name.strip()}** already exists "
                        f"(brand: {brands}). Change the name or edit the existing entry."
                    )
                else:
                    if dups["near"]:
                        near_list = ", ".join(
                            f"{x.get('name')} ({x.get('brand')})" for x in dups["near"][:3]
                        )
                        st.warning(f"Similar bottles already in vault: {near_list}")
                    new_frag = {
                        "name": new_name.strip(),
                        "brand": new_brand.strip(),
                        "gender": new_gender,
                        "season": new_season or "Versatile",
                        "notes": new_notes if new_notes else "Not specified",
                        "category": new_cats if new_cats else ["Gourmand"],
                        "dupe_of": "",
                        "shelf_status": new_shelf,
                        "size_ml": (
                            float(new_size)
                            if str(new_size or "").strip().replace(".", "", 1).isdigit()
                            else None
                        ),
                        "price": (
                            float(new_price)
                            if str(new_price or "").strip().replace(".", "", 1).isdigit()
                            else None
                        ),
                    }
                    st.session_state["fragrances_db"].append(new_frag)
                    try:
                        log_vault_action("added", new_frag["name"], new_frag["brand"])
                    except Exception:
                        pass
                    st.session_state["last_added_frag"] = new_frag
                    save_persisted_data()
                    st.session_state["_add_flash"] = f"Added **{new_frag['name']}**."
                    st.rerun()
            else:
                st.error("Name and brand are required.")


    # Receipt for last added bottle
    last_added = st.session_state.get("last_added_frag")
    if last_added:
        st.markdown("#### Just added")
        st.success(
            f"**{last_added.get('name')}** by *{last_added.get('brand')}* | "
            f"{last_added.get('gender')} | {', '.join(last_added.get('category') or [])}"
        )
        st.caption(f"Notes: {last_added.get('notes', '')}")
        try:
            pdf_bytes = build_fragrance_sheet_pdf(
                last_added, title=f"Added - {last_added.get('name', 'bottle')}"
            )
            st.download_button(
                "Download PDF sheet for this bottle",
                data=pdf_bytes,
                file_name=f"added_{last_added.get('name', 'bottle').replace(' ', '_')}.pdf",
                mime="application/pdf",
                key="last_added_pdf",
            )
        except Exception as ex:
            st.caption(f"PDF unavailable: {ex}")
        if st.button("Dismiss", key="dismiss_last_added"):
            st.session_state.pop("last_added_frag", None)
            st.rerun()

    st.markdown("---")
    st.markdown("### Today")
    # Daily challenge
    challenge = draw_challenge()
    st.caption("Daily challenge")
    st.info(challenge)
    if st.button("Mark challenge done", key="challenge_done_btn", use_container_width=True):
        st.session_state["play_stats"]["challenges_done"] = (
            st.session_state["play_stats"].get("challenges_done", 0) + 1
        )
        save_persisted_data()
        st.success("Challenge noted.")
        st.rerun()

    # Weekly recipe
    weekly = get_weekly_recipe()
    if weekly:
        st.caption(f"Recipe of the week ({weekly.get('week', '')})")
        bottles = weekly.get("bottles") or []
        st.write(f"**{weekly.get('name', 'Layer')}**")
        if bottles:
            st.caption(" + ".join(bottles))
        if weekly.get("reason"):
            st.caption(weekly["reason"])
        if st.button("Use weekly recipe in SOTD", key="weekly_use_btn", use_container_width=True):
            st.session_state["sotd_prefill"] = list(bottles)
            st.rerun()

    # Backup reminder
    st.markdown("---")
    last_export = st.session_state.get("last_export_date")
    if not last_export:
        st.caption("Sanctuary tip: export your vault from the Vault tab.")
    else:
        try:
            days = (pacific_today() - datetime.date.fromisoformat(last_export)).days
            if days >= 30:
                st.warning(f"Last export was {days} days ago  -  consider backing up.")
        except ValueError:
            pass


# ---------- MAIN TABS ----------
tab_discover, tab_layer, tab_roulette, tab_sotd, tab_horoscope, tab_play, tab_collection, tab_vault = st.tabs(
    ["Discover", "Layer", "Roulette", "SOTD", "Stars", "Play", "Collection", "Vault"]
)

# ===== DISCOVER =====
with tab_discover:
    st.markdown(
        "Filter from the sidebar, search by name or note, then generate picks and layering ideas."
    )

    # Results from dedicated Temp search (sidebar)
    last_temp = st.session_state.get("last_temp_search")
    if last_temp is not None:
        picks = last_temp.get("picks") or []
        st.subheader("Temp search results")
        st.caption(
            f"{int(last_temp.get('temp_f', 0))} F -> {last_temp.get('band', '')} | "
            f"Gender: {last_temp.get('gender', 'Any')}"
        )
        if not picks:
            st.warning("No bottles matched this temperature + gender. Try Any gender or nudge the slider.")
        else:
            for i, f in enumerate(picks, 1):
                badge = " YAY" if st.session_state["user_reactions"].get(f["name"]) == "fav" else ""
                st.success(f"**#{i} - {f['name']}** by *{f['brand']}*{badge}")
                st.write(f"**Gender:** {f['gender']} | **Season:** {f['season']}")
                st.write(f"**Category:** {', '.join(f['category'])}")
                st.caption(f"Notes: {f['notes']}")
                b1, b2, b3, _ = st.columns([1, 1, 1, 3])
                with b1:
                    if st.button("YAY", key=f"temp_fav_{f['name']}_{i}"):
                        st.session_state["user_reactions"][f["name"]] = "fav"
                        save_persisted_data()
                        st.rerun()
                with b2:
                    if st.button("DEL", key=f"temp_dislike_{f['name']}_{i}"):
                        st.session_state["user_reactions"][f["name"]] = "dislike"
                        save_persisted_data()
                        st.rerun()
                with b3:
                    if st.button("Wear", key=f"temp_wear_{f['name']}_{i}"):
                        st.session_state["sotd_prefill"] = [f["name"]]
                        st.rerun()
                st.markdown("---")
        if st.button("Clear temp results", key="clear_temp_results"):
            st.session_state.pop("last_temp_search", None)
            st.rerun()

    # Name / brand search (ranked: YAY â most worn â complete notes)
    if search_query:
        st.subheader(f'Search | "{search_query}"')
        query_lower = search_query.lower()
        matching = [
            f
            for f in st.session_state["fragrances_db"]
            if query_lower in f["name"].lower() or query_lower in f["brand"].lower()
        ]
        matching = rank_search_results(matching)
        if not matching:
            st.warning("No fragrances matched that name or brand.")
        else:
            st.caption(f"{len(matching)} match(es)  -  ranked by favorites, wears, note quality")
            for f in matching:
                render_fragrance_card(f, key_prefix=f"search_{search_query}")

    # Note search (same ranking)
    if note_query:
        st.subheader(f'Notes | "{note_query}"')
        note_q = note_query.lower()
        matching_notes = [
            f
            for f in st.session_state["fragrances_db"]
            if note_q in f["notes"].lower()
        ]
        matching_notes = rank_search_results(matching_notes)
        if not matching_notes:
            st.warning("No fragrances contain that note.")
        else:
            st.caption(f"{len(matching_notes)} match(es)  -  ranked by favorites, wears, note quality")
            for f in matching_notes:
                render_fragrance_card(f, key_prefix=f"note_{note_query}")

    # Recommendations (persist so Love/Trash does not wipe the list)
    if generate_clicked:
        selected = get_top_fragrances(
            gender,
            weather,
            category,
            occasion,
            num_recs,
            favorites_only=favorites_only,
            temp_f=None,
        )
        st.session_state["last_recs"] = {
            "selected": selected,
            "num": num_recs,
            "meta": {
                "gender": gender,
                "weather": weather,
                "category": category,
                "occasion": occasion,
                "favorites_only": favorites_only,
            },
        }

    last_recs = st.session_state.get("last_recs")
    if last_recs is not None:
        selected = last_recs.get("selected") or []
        num_show = last_recs.get("num", 3)
        meta = last_recs.get("meta") or {}
        st.subheader(f"Top {num_show}")
        if meta:
            st.caption(
                f"{meta.get('gender')} | {meta.get('weather')} | "
                f"{meta.get('category')} | {meta.get('occasion')}"
                + (" | favorites only" if meta.get("favorites_only") else "")
            )
        if not selected:
            st.warning(
                "Nothing matched these filters (or everything is disliked / "
                "not favorited). Try **Any** on some filters or turn off Favorites only."
            )
        else:
            for i, f in enumerate(selected, 1):
                current_reaction = st.session_state["user_reactions"].get(f["name"])
                badge = " YAY" if current_reaction == "fav" else ""
                st.success(f"**#{i} - {f['name']}** by *{f['brand']}*{badge}")
                st.write(f"**Gender:** {f['gender']} | **Season:** {f['season']}")
                st.write(f"**Category:** {', '.join(f['category'])}")
                st.caption(f"Notes: {f['notes']}")
                c1, c2, _ = st.columns([1, 1, 4])
                with c1:
                    if st.button("YAY", key=f"rec_fav_{f['name']}_{i}"):
                        st.session_state["user_reactions"][f["name"]] = "fav"
                        save_persisted_data()
                        st.rerun()
                with c2:
                    if st.button("DEL", key=f"rec_dislike_{f['name']}_{i}"):
                        st.session_state["user_reactions"][f["name"]] = "dislike"
                        save_persisted_data()
                        st.rerun()
                st.markdown("---")



    if not search_query and not note_query and last_recs is None:
        st.info(
            "Use the sidebar to search, filter, or **Generate recommendations**. "
            "Roulette, SOTD, and vault tools live in the other tabs."
        )



# ===== LAYER =====
with tab_layer:
    st.subheader("Layering Studio")
    st.caption("Partners for a base bottle, free combos, or saved recipes.")

    if st.session_state.pop("_clear_layer", False):
        st.session_state["layer_partner_gender"] = "Any"
        st.session_state["layer_base_select"] = "- select a bottle -"
        st.session_state["layer_gender"] = "Any"
        st.session_state["layer_season"] = "Any"
        st.session_state["layer_favs_only"] = False
        st.session_state["layer_n"] = 3
        st.session_state.pop("last_layer", None)

    if "layer_partner_gender" not in st.session_state:
        st.session_state["layer_partner_gender"] = "Any"

    with st.expander("Base + partners", expanded=True):
        lp1, lp2 = st.columns(2)
        with lp1:
            layer_partner_gender = st.selectbox(
                "Filter by gender",
                ["Any", "Male", "Female", "Unisex"],
                key="layer_partner_gender",
            )
        with lp2:
            if st.button("Clear layer studio", use_container_width=True, key="layer_clear_btn"):
                st.session_state["_clear_layer"] = True
                st.rerun()

        all_layer_names = sorted(
            f["name"]
            for f in st.session_state["fragrances_db"]
            if matches_gender(f, layer_partner_gender)
        )
        base_options = ["- select a bottle -"] + all_layer_names
        if st.session_state.get("layer_base_select") not in base_options:
            st.session_state["layer_base_select"] = "- select a bottle -"

        base_choice = st.selectbox(
            "Base fragrance",
            base_options,
            key="layer_base_select",
        )

        if base_choice != "- select a bottle -":
            name_to_frag = {f["name"]: f for f in st.session_state["fragrances_db"]}
            base_f = name_to_frag.get(base_choice)
            if base_f:
                st.caption(
                    f"{base_f['brand']} | {base_f['gender']} | {base_f['season']} | "
                    f"{', '.join(base_f.get('category', []))}"
                )
                partners = suggest_partners_for(
                    base_f, num=5, gender=layer_partner_gender
                )
                if not partners:
                    st.warning("No strong partners with this gender filter.")
                else:
                    st.markdown(f"**Partners for {base_choice}**")
                    for pi, (pf, reason) in enumerate(partners, 1):
                        st.info(
                            f"**{pi}. {pf['name']}** ({pf['brand']})\n\n"
                            f"{pf.get('gender', '')} | {', '.join(pf.get('category', []))}\n\n"
                            f"*{reason}*"
                        )
                        if st.button("Use in SOTD", key=f"layer_base_use_{pi}"):
                            st.session_state["sotd_prefill"] = [base_choice, pf["name"]]
                            st.rerun()

    with st.expander("Free combos from filters", expanded=False):
        lc1, lc2 = st.columns(2)
        with lc1:
            layer_gender = st.selectbox(
                "Gender", ["Any", "Male", "Female", "Unisex"], key="layer_gender"
            )
        with lc2:
            layer_season = st.selectbox(
                "Season / weather",
                ["Any", "Hot / Summer", "Warm / Mild", "Cool / Autumn", "Cold / Winter"],
                key="layer_season",
            )
        layer_favs_only = st.checkbox("Favorites only", value=False, key="layer_favs_only")
        layer_n = st.radio(
            "How many combos", [1, 3, 5], index=1, horizontal=True, key="layer_n"
        )

        if st.button("Suggest layering combos", type="primary", key="layer_gen_btn"):
            pool = get_top_fragrances(
                layer_gender,
                layer_season,
                "Any",
                "Any",
                min(40, len(st.session_state["fragrances_db"])),
                favorites_only=layer_favs_only,
            )
            combos = suggest_layering_combos(pool, num_combos=layer_n)
            st.session_state["last_layer"] = {
                "combos": combos,
                "meta": {
                    "gender": layer_gender,
                    "season": layer_season,
                    "favorites_only": layer_favs_only,
                    "pool": len(pool),
                },
            }

        last_layer = st.session_state.get("last_layer")
        if last_layer is not None:
            combos = last_layer.get("combos") or []
            meta = last_layer.get("meta") or {}
            st.caption(
                f"{meta.get('gender')} | {meta.get('season')} | pool {meta.get('pool', '?')}"
                + (" | favorites only" if meta.get("favorites_only") else "")
            )
            if not combos:
                st.warning("Need at least two matching bottles.")
            else:
                for i, (f1, f2, reason) in enumerate(combos, 1):
                    st.info(
                        f"**Combo {i}**\n\n"
                        f"**Base:** {f1['name']} ({f1['brand']})\n\n"
                        f"**Layer:** {f2['name']} ({f2['brand']})\n\n"
                        f"*{reason}*"
                    )
                    if st.button("Use in SOTD", key=f"layer_use_{i}"):
                        st.session_state["sotd_prefill"] = [f1["name"], f2["name"]]
                        st.rerun()
                st.caption("Tip: spray the richer scent first, then the lighter one.")
            if st.button("Clear combo results", key="layer_clear_results"):
                st.session_state.pop("last_layer", None)
                st.rerun()

    with st.expander("Saved layer recipes", expanded=False):
        rec_pick = st.multiselect(
            "Bottles in recipe",
            sorted(f["name"] for f in st.session_state["fragrances_db"]),
            key="recipe_bottles_in",
        )
        preview = evaluate_layer_recipe(list(rec_pick)) if len(rec_pick) >= 1 else None
        suggested = (preview or {}).get("suggested_name") or ""
        if preview and len(rec_pick) >= 2:
            season = preview.get("season") or {}
            st.caption(
                f"Suggested name from notes: **{suggested}** | "
                f"Season: **{season.get('label', '?')}**"
            )
            st.caption(season.get("detail", ""))

        # Name field - can use suggested
        if st.session_state.pop("_apply_recipe_name", False) and suggested:
            st.session_state["recipe_name_in"] = suggested
        rec_name = st.text_input(
            "Recipe name",
            placeholder=suggested or "e.g. Coconut vanilla night",
            key="recipe_name_in",
        )
        rn1, rn2 = st.columns(2)
        with rn1:
            if st.button(
                "Use name from notes",
                key="recipe_use_suggested_name",
                disabled=len(rec_pick) < 2,
            ):
                st.session_state["_apply_recipe_name"] = True
                st.rerun()
        with rn2:
            save_clicked = st.button("Save recipe", key="save_recipe_btn")

        if save_clicked:
            final_name = (rec_name or "").strip() or suggested or "Untitled layer"
            if len(rec_pick) >= 2:
                season = (preview or {}).get("season") or {}
                st.session_state["layer_recipes"].insert(
                    0,
                    {
                        "name": final_name,
                        "bottles": list(rec_pick),
                        "season_label": season.get("label", ""),
                        "season_detail": season.get("detail", ""),
                        "suggested_name": suggested,
                    },
                )
                save_persisted_data()
                st.session_state["_recipe_save_flash"] = (
                    f"Saved **{final_name}** - best season: {season.get('label', '?')}"
                )
                st.rerun()
            else:
                st.warning("Need at least two bottles.")

        _rsf = st.session_state.pop("_recipe_save_flash", None)
        if _rsf:
            st.success(_rsf)

        for ri, recipe in enumerate(st.session_state.get("layer_recipes") or []):
            bottles = list(recipe.get("bottles") or [])
            st.markdown(f"**{recipe.get('name', 'Recipe')}**")
            st.caption(" + ".join(bottles))
            ev = evaluate_layer_recipe(bottles)
            season = ev.get("season") or {}
            saved_season = recipe.get("season_label") or season.get("label")
            if saved_season:
                st.caption(
                    f"Season: **{saved_season}** - "
                    f"{recipe.get('season_detail') or season.get('detail', '')}"
                )
            # Verdict banner
            if ev["label"] in ("Strong layer", "Good layer"):
                st.success(f"{ev['label']} (score {ev['score']}) - {ev['verdict']}")
            elif ev["label"] == "Mixed":
                st.warning(f"{ev['label']} (score {ev['score']}) - {ev['verdict']}")
            else:
                st.info(f"{ev['label']} (score {ev['score']}) - {ev['verdict']}")
            # Notes for each bottle
            for f in ev.get("frags") or []:
                cats = ", ".join(f.get("category") or [])
                st.markdown(
                    f"**{f.get('name')}** ({f.get('brand', '?')})  \n"
                    f"*{f.get('gender', '')} | {f.get('season', '')} | {cats}*  \n"
                    f"Notes: {f.get('notes') or 'Not specified'}"
                )
            if ev.get("missing"):
                st.caption(
                    "Missing from vault: " + ", ".join(ev["missing"])
                )
            rb1, rb2 = st.columns(2)
            with rb1:
                if st.button("Use in SOTD", key=f"recipe_use_{ri}"):
                    st.session_state["sotd_prefill"] = bottles
                    st.rerun()
            with rb2:
                if st.button("Delete", key=f"recipe_del_{ri}"):
                    st.session_state["layer_recipes"].pop(ri)
                    save_persisted_data()
                    st.rerun()
            st.markdown("---")


# ===== ROULETTE =====
with tab_roulette:
    st.subheader("Fragrance Roulette")
    st.write("Let chance pick from your vault - still respecting gender and season.")

    r1, r2 = st.columns(2)
    with r1:
        roulette_gender = st.selectbox(
            "Gender", ["Any", "Male", "Female", "Unisex"], key="roulette_gender"
        )
    with r2:
        roulette_season = st.selectbox(
            "Season / weather",
            ["Any", "Hot / Summer", "Warm / Mild", "Cool / Autumn", "Cold / Winter"],
            key="roulette_season",
        )
    roulette_mode = st.selectbox(
        "Mode",
        [
            "Standard (skip recent)",
            "YAY only",
            "Never worn",
            "Opposite of yesterday",
        ],
        key="roulette_mode",
    )

    if st.button("Spin the roulette", type="primary", key="spin_roulette_btn"):
        recent_worn = set()
        for entry in st.session_state.get("sotd_history", [])[:5]:
            if entry.get("scents"):
                recent_worn.update(entry["scents"])
            elif entry.get("scent"):
                for part in entry["scent"].split(" + "):
                    recent_worn.add(part.strip())

        yesterday_cats = set()
        hist = st.session_state.get("sotd_history") or []
        if hist:
            last = hist[0]
            names = last.get("scents") or []
            if not names and last.get("scent"):
                names = [p.strip() for p in last["scent"].split(" + ")]
            name_map = {f["name"]: f for f in st.session_state["fragrances_db"]}
            for n in names:
                fr = name_map.get(n)
                if fr:
                    yesterday_cats.update(fr.get("category", []))

        wear_counts = get_wear_counts()
        pool = []
        for f in st.session_state["fragrances_db"]:
            if st.session_state["user_reactions"].get(f["name"]) == "dislike":
                continue
            if not (matches_gender(f, roulette_gender) and matches_weather(f, roulette_season)):
                continue
            mode = roulette_mode
            if mode == "Standard (skip recent)" and f["name"] in recent_worn:
                continue
            if mode == "YAY only" and st.session_state["user_reactions"].get(f["name"]) != "fav":
                continue
            if mode == "Never worn" and wear_counts.get(f["name"], 0) > 0:
                continue
            if mode == "Opposite of yesterday":
                if not yesterday_cats:
                    pass  # no history - allow all
                elif set(f.get("category", [])) & yesterday_cats:
                    continue  # skip overlapping families
            pool.append(f)

        if not pool:
            st.warning(
                f"No bottles match gender **{roulette_gender}** and "
                f"season **{roulette_season}**. Loosen filters or clear some dislikes."
            )
            st.session_state["last_roulette"] = None
            st.session_state["last_roulette_meta"] = None
        else:
            chosen = random.choice(pool)
            st.session_state["last_roulette"] = chosen
            st.session_state["last_roulette_meta"] = {
                "gender": roulette_gender,
                "season": roulette_season,
                "pool_size": len(pool),
            }

    if st.session_state.get("last_roulette"):
        chosen = st.session_state["last_roulette"]
        if not any(f["name"] == chosen.get("name") for f in st.session_state["fragrances_db"]):
            st.session_state["last_roulette"] = None
            chosen = None
        if chosen:
            current_reaction = st.session_state["user_reactions"].get(chosen["name"])
            status_badge = (
                " YAY"
                if current_reaction == "fav"
                else (" NAH" if current_reaction == "dislike" else "")
            )
            st.markdown(
                """
                <div class="bat-container">
                    <span class="floating-bat bat1">Ã°ÂÂ¦Â</span>
                    <span class="floating-bat bat2">Ã°ÂÂ¦Â</span>
                    <span class="floating-bat bat3">Ã°ÂÂ¦Â</span>
                    <span class="floating-bat bat4">Ã°ÂÂ¦Â</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.success("### The roulette has spoken...")
            st.markdown(f"## **{chosen['name']}**{status_badge}")
            st.markdown(f"### by *{chosen['brand']}*")
            st.write(
                f"**Gender:** {chosen['gender']}  |  **Season:** {chosen['season']}"
            )
            st.write(f"**Category:** {', '.join(chosen['category'])}")
            st.caption(f"Notes: {chosen['notes']}")
            meta = st.session_state.get("last_roulette_meta") or {}
            if meta:
                st.caption(
                    f"Filters | {meta.get('gender', '-')} | {meta.get('season', '-')} | "
                    f"pool {meta.get('pool_size', '?')}"
                )
            rc1, rc2, _ = st.columns([1, 1, 2])
            with rc1:
                if st.button("YAY", key=f"roulette_fav_{chosen['name']}"):
                    st.session_state["user_reactions"][chosen["name"]] = "fav"
                    save_persisted_data()
                    st.rerun()
            with rc2:
                if st.button("DEL", key=f"roulette_dislike_{chosen['name']}"):
                    st.session_state["user_reactions"][chosen["name"]] = "dislike"
                    save_persisted_data()
                    st.rerun()

# ===== SOTD =====
with tab_sotd:
    st.subheader("Scent of the Day")
    streak = sotd_streak()
    if streak:
        st.caption(f"Current log streak: **{streak}** day(s)")
    all_frag_names = sorted(f["name"] for f in st.session_state["fragrances_db"])

    # Clear form on next run AFTER log (must happen before widgets are created)
    if st.session_state.pop("_clear_sotd_form", False):
        st.session_state["sotd_multiselect"] = []
        st.session_state["sotd_notes_input"] = ""
        st.session_state["sotd_date"] = pacific_today()
        st.session_state["sotd_his_select"] = "- none -"

    # Prefill from quick layering combo (also before widgets)
    if st.session_state.get("sotd_prefill"):
        st.session_state["sotd_multiselect"] = list(st.session_state["sotd_prefill"])
        st.session_state["sotd_prefill"] = []
        if len(st.session_state.get("sotd_multiselect", [])) > 1:
            st.session_state["sotd_notes_input"] = "Layered combo"

    st.caption("Pick one bottle, or several for a layering day.")
    # Default to Pacific "today" so the date matches the user, not the server UTC clock
    if "sotd_date" not in st.session_state:
        st.session_state["sotd_date"] = pacific_today()
    sotd_date = st.date_input(
        "Date",
        value=st.session_state.get("sotd_date", pacific_today()),
        key="sotd_date",
        help="Calendar uses your selected day. Defaults to Pacific time today.",
    )
    sotd_choices = st.multiselect(
        "Wearing today",
        options=all_frag_names,
        placeholder="Choose fragrance(s)...",
        key="sotd_multiselect",
    )
    sotd_notes = st.text_input(
        "Notes / vibe (optional)",
        placeholder="Rainy afternoon | office | date night",
        key="sotd_notes_input",
    )
    all_names_his = sorted(f["name"] for f in st.session_state["fragrances_db"])
    sotd_his = st.selectbox(
        "His scent (optional)",
        ["- none -"] + all_names_his,
        key="sotd_his_select",
    )

    with st.expander("Horror night vibes", expanded=False):
        st.caption(
            "Scary-movie nights - gothic fog, cabin woods, slashers, haunted gourmand, vampires."
        )
        horror_mode = st.selectbox(
            "Horror mood",
            list(HORROR_SCENT_PROFILES.keys()),
            key="sotd_horror_mode",
        )
        hp = HORROR_SCENT_PROFILES[horror_mode]
        st.write(hp.get("blurb", ""))
        if st.button("Draw horror night scents", type="primary", key="sotd_horror_draw"):
            picks = get_horror_picks(horror_mode, top_n=3)
            st.session_state["last_horror_picks"] = {
                "mode": horror_mode,
                "picks": picks,
                "vibe": hp.get("vibe_note", horror_mode),
            }
        last_h = st.session_state.get("last_horror_picks")
        if last_h:
            st.caption(f"Mode: {last_h.get('mode')}")
            for i, f in enumerate(last_h.get("picks") or [], 1):
                st.markdown(
                    f"**{i}. {f.get('name')}** ({f.get('brand')}) - "
                    f"{', '.join(f.get('category') or [])}"
                )
                if st.button("Use tonight", key=f"horror_use_{i}"):
                    st.session_state["sotd_prefill"] = [f["name"]]
                    st.session_state["sotd_notes_input"] = last_h.get(
                        "vibe", "Horror night"
                    )
                    st.rerun()



    # Layering partners based on current selection
    if sotd_choices:
        name_to_frag = {f["name"]: f for f in st.session_state["fragrances_db"]}
        primary_name = sotd_choices[0]
        primary = name_to_frag.get(primary_name)
        if primary:
            st.markdown(f"#### Layer with **{primary_name}**")
            st.caption("Suggestions for the first bottle you selected. Tap Add to include it today.")
            partners = suggest_partners_for(primary, num=4)
            if not partners:
                st.write("No strong partners found (or everything else is DEL).")
            else:
                for pi, (pf, reason) in enumerate(partners):
                    already = pf["name"] in sotd_choices
                    row_a, row_b = st.columns([4, 1])
                    with row_a:
                        mark = " (already selected)" if already else ""
                        st.markdown(
                            f"**{pf['name']}**  -  *{pf['brand']}*{mark}  \n"
                            f"{', '.join(pf.get('category', []))}  \n"
                            f"*{reason}*"
                        )
                    with row_b:
                        if not already:
                            if st.button("Add", key=f"sotd_add_layer_{pi}_{pf['name']}"):
                                st.session_state["sotd_prefill"] = list(sotd_choices) + [pf["name"]]
                                if not st.session_state.get("sotd_notes_input"):
                                    st.session_state["sotd_notes_input"] = "Layered combo"
                                st.rerun()
                    st.markdown("---")

        # Husband / male match for her selection
        with st.expander("His match", expanded=False):
            st.caption(
                "Male (and unisex) bottles from the vault that sit well beside what you're wearing."
            )
            his_matches = suggest_his_match(
                [name_to_frag[n] for n in sotd_choices if n in name_to_frag],
                num=4,
            )
            if not his_matches:
                st.write(
                    "No strong male matches right now. Add more male bottles or loosen DEL marks."
                )
            else:
                for hi, (hf, reason) in enumerate(his_matches):
                    st.info(
                        f"**{hf['name']}** | *{hf['brand']}*\n\n"
                        f"{hf['gender']} | {hf['season']} | {', '.join(hf.get('category', []))}\n\n"
                        f"*{reason}*\n\n"
                        f"Notes: {hf['notes']}"
                    )

    with st.expander("Quick layering combos", expanded=False):
        st.caption(
            "Clear base + layer pairs (prefers YAY). Use fills Wearing today with two separate bottles."
        )
        fav_names = [
            n for n, s in st.session_state["user_reactions"].items() if s == "fav"
        ]
        pool = [
            f
            for f in st.session_state["fragrances_db"]
            if f["name"] in fav_names
            and st.session_state["user_reactions"].get(f["name"]) != "dislike"
        ]
        if len(pool) < 2:
            pool = [
                f
                for f in st.session_state["fragrances_db"]
                if st.session_state["user_reactions"].get(f["name"]) != "dislike"
            ]
        quick_combos = suggest_layering_combos(pool, num_combos=4)
        if not quick_combos:
            st.write("Need at least two bottles to suggest layers.")
        else:
            for i, (f1, f2, reason) in enumerate(quick_combos, 1):
                if f1.get("name") == f2.get("name"):
                    continue
                st.markdown(
                    f"**Pair {i}**  \n"
                    f"Base: **{f1['name']}** ({f1.get('brand', '')})  \n"
                    f"Layer: **{f2['name']}** ({f2.get('brand', '')})  \n"
                    f"*{reason}*"
                )
                if st.button(
                    "Use this pair",
                    key=f"use_combo_{i}_{f1['name']}_{f2['name']}",
                ):
                    st.session_state["sotd_prefill"] = [f1["name"], f2["name"]]
                    st.session_state["sotd_notes_input"] = (
                        f"Layer: {f1['name']} + {f2['name']}"
                    )
                    st.rerun()
                st.markdown("---")

    sotd_photo = st.file_uploader(
        "Optional photo (bottle / flat lay)",
        type=["jpg", "jpeg", "png", "webp"],
        key="sotd_photo_up",
        help="Stored as a small compressed image with this log.",
    )

    if st.button("Log today's scent", type="primary"):
        if sotd_choices:
            today_date = sotd_date.strftime("%Y-%m-%d") if hasattr(sotd_date, "strftime") else str(sotd_date)
            scent_display = " + ".join(sotd_choices)
            is_layering = len(sotd_choices) > 1
            entry = {
                "date": today_date,
                "scent": scent_display,
                "scents": sotd_choices,
                "is_layering": is_layering,
                "notes": sotd_notes,
            }
            if sotd_his and sotd_his != "- none -":
                entry["his_scent"] = sotd_his
            if sotd_photo is not None:
                try:
                    entry["photo"] = _image_to_data_url(sotd_photo)
                except Exception as ex:
                    st.warning(f"Photo skipped: {ex}")
            st.session_state["sotd_history"].insert(0, entry)
            save_persisted_data()
            st.session_state["_clear_sotd_form"] = True
            st.session_state["_sotd_flash"] = (
                f"Logged layering: **{scent_display}**"
                if is_layering
                else f"Logged **{scent_display}**"
            )
            st.rerun()
        else:
            st.warning("Select at least one fragrance.")

    _flash = st.session_state.pop("_sotd_flash", None)
    if _flash:
        st.success(_flash)

    with st.expander("Weekly SOTD browser", expanded=False):
        st.caption("Browse past weeks on screen and download a PDF if you want a copy.")
        today = pacific_today()
        monday = today - datetime.timedelta(days=today.weekday())
        week_opts = []
        for wback in range(0, 16):
            m = monday - datetime.timedelta(weeks=wback)
            iso = m.isocalendar()
            key = f"{iso[0]}-W{iso[1]:02d}"
            label = f"{key} ({m.isoformat()} - {(m + datetime.timedelta(days=6)).isoformat()})"
            week_opts.append((label, key, m))
        week_labels = [x[0] for x in week_opts]
        pick_label = st.selectbox("Week", week_labels, key="sotd_week_pick")
        pick_key = next(x[1] for x in week_opts if x[0] == pick_label)
        pick_monday = next(x[2] for x in week_opts if x[0] == pick_label)
        pick_sunday = pick_monday + datetime.timedelta(days=6)

        week_entries = []
        for e in st.session_state.get("sotd_history") or []:
            d = e.get("date")
            if not d:
                continue
            try:
                dd = datetime.date.fromisoformat(d)
            except ValueError:
                continue
            if pick_monday <= dd <= pick_sunday:
                week_entries.append(e)
        week_entries.sort(key=lambda x: x.get("date", ""))

        st.write(
            f"**{len(week_entries)}** log(s) in {pick_key} "
            f"({pick_monday.isoformat()} to {pick_sunday.isoformat()})"
        )
        if not week_entries:
            st.info("No SOTD entries in this week yet.")
        else:
            for entry in week_entries:
                layer_badge = " [layer]" if entry.get("is_layering") else ""
                his_txt = f" | his: {entry['his_scent']}" if entry.get("his_scent") else ""
                perf_bits = []
                if entry.get("sillage"):
                    perf_bits.append(f"sil {entry['sillage']}")
                if entry.get("longevity"):
                    perf_bits.append(f"lon {entry['longevity']}")
                perf_txt = (" | " + "/".join(perf_bits)) if perf_bits else ""
                notes_text = f" | {entry['notes']}" if entry.get("notes") else ""
                st.markdown(
                    f"**{entry.get('date')}:** *{entry.get('scent')}*{layer_badge}"
                    f"{his_txt}{perf_txt}{notes_text}"
                )
                if entry.get("photo"):
                    try:
                        st.image(entry["photo"], width=160)
                    except Exception:
                        pass

        try:
            pdf_bytes = build_sotd_week_pdf(pick_key)
            st.download_button(
                "Download this week as PDF",
                data=pdf_bytes,
                file_name=f"sotd_{pick_key}.pdf",
                mime="application/pdf",
                key="sotd_week_pdf_btn",
            )
        except Exception as ex:
            st.caption(f"PDF unavailable: {ex}")

    with st.expander("Journal history", expanded=False):
            for i, entry in enumerate(st.session_state["sotd_history"]):
                layer_badge = " | layering" if entry.get("is_layering") else ""
                notes_text = f" - {entry['notes']}" if entry.get("notes") else ""
                hcol, xcol = st.columns([6, 1])
                with hcol:
                    perf_bits = []
                    if entry.get("sillage"):
                        perf_bits.append(f"sil {entry['sillage']}/5")
                    if entry.get("longevity"):
                        perf_bits.append(f"lon {entry['longevity']}/5")
                    perf_txt = f"  -  {', '.join(perf_bits)}" if perf_bits else ""
                    his_txt = f"  -  his: {entry['his_scent']}" if entry.get("his_scent") else ""
                    st.write(
                        f"**{entry['date']}:** *{entry['scent']}*{layer_badge}{his_txt}{perf_txt}{notes_text}"
                    )
                    if entry.get("photo"):
                        try:
                            st.image(entry["photo"], width=180)
                        except Exception:
                            pass
                with xcol:
                    if st.button("DEL", key=f"del_sotd_{i}_{entry['date']}", help="Remove entry"):
                        st.session_state["sotd_history"].pop(i)
                        save_persisted_data()
                        st.rerun()
            if st.button("Clear entire journal", key="clear_sotd_all"):
                st.session_state["sotd_history"] = []
                save_persisted_data()
                st.rerun()


# ===== STARS / HOROSCOPE =====
with tab_horoscope:
    st.subheader("Stars & scent")
    st.caption("Your birth chart signs - saved with the vault.")

    st.markdown("#### Your chart")
    st.caption(
        f"Default sanctuary chart - born {DEFAULT_CHART['birth_date']} "
        f"{DEFAULT_CHART['birth_time']} - {DEFAULT_CHART['birth_place']}. "
        "Adjust signs below anytime; Save chart stores them."
    )

    signs = list(SIGN_SCENT_PROFILE.keys())

    # Must apply calculator results BEFORE chart selectboxes are created
    if st.session_state.pop("_apply_birth_chart", False):
        calc = st.session_state.get("birth_calc_full") or {}
        if calc.get("sun") and calc["sun"] in signs:
            st.session_state["chart_sun"] = calc["sun"]
        if calc.get("moon") and calc["moon"] in signs:
            st.session_state["chart_moon"] = calc["moon"]
        if calc.get("rising") and calc["rising"] in signs:
            st.session_state["chart_rising"] = calc["rising"]
        if calc.get("venus") and calc["venus"] in signs:
            st.session_state["chart_venus"] = calc["venus"]
        st.session_state["_chart_apply_flash"] = True

    # Seed session defaults once so selectboxes don't fight index= vs key=
    if "chart_sun" not in st.session_state:
        st.session_state["chart_sun"] = DEFAULT_CHART["sun"]
    if "chart_moon" not in st.session_state:
        st.session_state["chart_moon"] = DEFAULT_CHART["moon"]
    if "chart_rising" not in st.session_state:
        st.session_state["chart_rising"] = DEFAULT_CHART["rising"]
    if "chart_venus" not in st.session_state:
        st.session_state["chart_venus"] = DEFAULT_CHART.get("venus", DEFAULT_CHART["sun"])

    hc1, hc2, hc3, hc4 = st.columns(4)
    with hc1:
        sun_s = st.selectbox("Sun", signs, key="chart_sun")
    with hc2:
        moon_s = st.selectbox("Moon", signs, key="chart_moon")
    with hc3:
        rise_s = st.selectbox("Rising", signs, key="chart_rising")
    with hc4:
        venus_s = st.selectbox("Venus", signs, key="chart_venus")

    # Live chart vibe summary
    sun_p = SIGN_SCENT_PROFILE.get(sun_s, {})
    moon_p = SIGN_SCENT_PROFILE.get(moon_s, {})
    rise_p = SIGN_SCENT_PROFILE.get(rise_s, {})
    ven_p = SIGN_SCENT_PROFILE.get(venus_s, {})
    st.caption(
        f"Sun {sun_s} ({sun_p.get('element', '?')} - {sun_p.get('vibe', '')}) | "
        f"Moon {moon_s} ({moon_p.get('element', '?')} - {moon_p.get('vibe', '')}) | "
        f"Rising {rise_s} ({rise_p.get('element', '?')} - {rise_p.get('vibe', '')}) | "
        f"Venus {venus_s} ({ven_p.get('vibe', '')})"
    )

    if st.session_state.pop("_chart_apply_flash", False):
        st.success("Calculator signs applied to your chart. Save chart to keep them.")

    if st.button("Save chart", key="chart_save_btn"):
        save_persisted_data()
        st.success("Chart saved.")
        st.rerun()

    with st.expander("Birth chart calculator", expanded=False):
        st.caption(
            "Enter birth date, time, and place for Sun, Moon, Rising, and Venus. "
            "Uses a built-in tropical calculator (no extra install required)."
        )
        if st.session_state.pop("_clear_birth_calc", False):
            for k, v in [
                ("birth_calc_year", 1990),
                ("birth_calc_month", 1),
                ("birth_calc_day", 1),
                ("birth_calc_hour12", 12),
                ("birth_calc_minute", 0),
                ("birth_calc_ampm", "PM"),
                ("birth_calc_city", "Victorville"),
                ("birth_calc_country", "United States"),
                ("birth_calc_nation", "US"),
            ]:
                st.session_state[k] = v
            st.session_state.pop("birth_calc_full", None)
            st.session_state.pop("birth_geo", None)

        r1, r2, r3 = st.columns(3)
        with r1:
            b_year = st.number_input("Year", 1920, 2030, 1990, key="birth_calc_year")
        with r2:
            b_month = st.number_input("Month", 1, 12, 1, key="birth_calc_month")
        with r3:
            b_day = st.number_input("Day", 1, 31, 1, key="birth_calc_day")
        r4, r5, r6ampm = st.columns(3)
        with r4:
            b_hour12 = st.number_input("Hour", 1, 12, 12, key="birth_calc_hour12")
        with r5:
            b_minute = st.number_input("Minute", 0, 59, 0, key="birth_calc_minute")
        with r6ampm:
            b_ampm = st.selectbox("AM / PM", ["AM", "PM"], key="birth_calc_ampm")
        r6, r7 = st.columns(2)
        with r6:
            b_city = st.text_input("Birth city", key="birth_calc_city", placeholder="Victorville")
        with r7:
            b_country = st.text_input(
                "Country", key="birth_calc_country", placeholder="United States"
            )
        b_nation = st.text_input(
            "Country code (for chart engine)",
            key="birth_calc_nation",
            placeholder="US",
            help="Two-letter code when possible, e.g. US, GB, MX.",
        )

        bc1, bc2, bc3 = st.columns(3)
        with bc1:
            do_calc = st.button(
                "Calculate chart", type="primary", key="birth_calc_btn", use_container_width=True
            )
        with bc2:
            if st.button("Clear", key="birth_calc_clear", use_container_width=True):
                st.session_state["_clear_birth_calc"] = True
                st.rerun()
        with bc3:
            apply_btn = st.button(
                "Apply to chart", key="birth_calc_apply", use_container_width=True
            )

        if do_calc:
            import calendar

            max_d = calendar.monthrange(int(b_year), int(b_month))[1]
            day_use = min(int(b_day), max_d)
            geo = geocode_birth_place(b_city or "Victorville", b_country or "United States")
            st.session_state["birth_geo"] = geo
            lat = geo.get("lat") if geo.get("ok") else None
            lon = geo.get("lon") if geo.get("ok") else None
            tz = geo.get("tz_str") if geo.get("ok") else None
            # Convert 12-hour + AM/PM to 24-hour for the engine
            h12 = int(b_hour12) % 12
            if b_ampm == "PM":
                h24 = h12 + 12
            else:
                h24 = h12  # 12 AM -> 0
            calc = calculate_full_chart(
                int(b_year),
                int(b_month),
                day_use,
                h24,
                int(b_minute),
                b_city or "Unknown",
                (b_nation or "US").strip() or "US",
                lat=lat,
                lon=lon,
                tz_str=tz,
            )
            if geo.get("ok"):
                calc["place_label"] = geo.get("label") or calc.get("place_label")
                calc["geo_detail"] = f"{geo.get('lat'):.3f}, {geo.get('lon'):.3f} | {geo.get('tz_str')}"
            else:
                calc["geo_detail"] = geo.get("detail", "Place lookup failed")
            st.session_state["birth_calc_full"] = calc

        calc = st.session_state.get("birth_calc_full")
        if calc:
            st.markdown(
                f"**Place:** {calc.get('place_label', '?')}  \n"
                f"**Engine:** {calc.get('engine', '?')}  \n"
                f"{calc.get('geo_detail', '')}"
            )
            s1, s2, s3, s4 = st.columns(4)
            s1.metric("Sun", calc.get("sun") or "-")
            s2.metric("Moon", calc.get("moon") or "-")
            s3.metric("Rising", calc.get("rising") or "-")
            s4.metric("Venus", calc.get("venus") or "-")

            planets = calc.get("planets") or {}
            if planets:
                st.markdown("**Planets & points**")
                order = [
                    "Sun", "Moon", "Mercury", "Venus", "Mars",
                    "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto",
                    "Lilith", "Ascendant", "MC",
                ]
                rows = []
                for name in order:
                    p = planets.get(name)
                    if not p:
                        continue
                    rows.append(
                        f"**{name}** {p.get('sign', '?')} "
                        f"({p.get('deg_in_sign', '?')} deg)"
                    )
                # show in two columns of text
                mid = (len(rows) + 1) // 2
                c_a, c_b = st.columns(2)
                with c_a:
                    for line in rows[:mid]:
                        st.markdown(line)
                with c_b:
                    for line in rows[mid:]:
                        st.markdown(line)

            houses = calc.get("houses") or {}
            if houses:
                st.markdown("**12 houses (equal system)**")
                st.caption("House 1 cusp = Rising. Each house is 30 degrees.")
                hcols = st.columns(4)
                for n in range(1, 13):
                    h = houses.get(n) or houses.get(str(n)) or {}
                    with hcols[(n - 1) % 4]:
                        st.markdown(
                            f"**H{n}** {h.get('sign', '-')}"
                        )

            if calc.get("detail"):
                st.caption(calc["detail"])
            st.caption(
                "Fragrance picks still use Sun, Moon, Rising, and Venus. "
                "Full chart is for reference and Save/Apply of those four."
            )

        if apply_btn:
            if st.session_state.get("birth_calc_full"):
                st.session_state["_apply_birth_chart"] = True
                st.rerun()
            else:
                st.warning("Calculate a chart first.")

    st.markdown("#### Chart scent picks")
    st.caption(
        "Female / Unisex bottles ranked for your Sun, Moon, Rising, and Venus. "
        "Uses today's planetary day quietly in the background (no weekday picker)."
    )
    chart_n = st.radio("How many", [3, 5, 8], index=1, horizontal=True, key="chart_n_picks")
    if st.button("Draw chart scents", type="primary", key="chart_draw_btn"):
        save_persisted_data()
        today_name = pacific_today().strftime("%A")
        picks = get_day_fragrances(
            today_name, sun_s, moon_s, rise_s, top_n=chart_n, venus=venus_s
        )
        st.session_state["last_chart_picks"] = {
            "picks": picks,
            "sun": sun_s,
            "moon": moon_s,
            "rising": rise_s,
            "venus": venus_s,
            "day": today_name,
        }
        st.rerun()

    last_cp = st.session_state.get("last_chart_picks")
    if last_cp is not None:
        st.caption(
            f"Sun {last_cp.get('sun')} | Moon {last_cp.get('moon')} | "
            f"Rising {last_cp.get('rising')} | Venus {last_cp.get('venus')} | "
            f"{last_cp.get('day', '')}"
        )
        picks = last_cp.get("picks") or []
        if not picks:
            st.warning("No matching Female / Unisex bottles for this chart right now.")
        else:
            for i, f in enumerate(picks, 1):
                badge = " YAY" if st.session_state["user_reactions"].get(f["name"]) == "fav" else ""
                st.success(f"**#{i} - {f['name']}** by *{f['brand']}*{badge}")
                st.write(f"**Gender:** {f['gender']} | **Season:** {f['season']}")
                st.write(f"**Category:** {', '.join(f['category'])}")
                st.caption(f"Notes: {f['notes']}")
                b1, b2, b3, _ = st.columns([1, 1, 1, 3])
                with b1:
                    if st.button("YAY", key=f"chart_fav_{f['name']}_{i}"):
                        st.session_state["user_reactions"][f["name"]] = "fav"
                        save_persisted_data()
                        st.rerun()
                with b2:
                    if st.button("DEL", key=f"chart_dislike_{f['name']}_{i}"):
                        st.session_state["user_reactions"][f["name"]] = "dislike"
                        save_persisted_data()
                        st.rerun()
                with b3:
                    if st.button("Wear", key=f"chart_wear_{f['name']}_{i}"):
                        st.session_state["sotd_prefill"] = [f["name"]]
                        st.rerun()
                st.markdown("---")


# ===== PLAY =====
with tab_play:
    st.subheader("Play")
    st.caption("Three games only - Mood, Blind bottle, Family roulette.")

    # Reset invalid play_mode from older builds
    _allowed_play = ["Mood board", "Blind bottle", "Family roulette"]
    if st.session_state.get("play_mode") not in _allowed_play:
        st.session_state["play_mode"] = "Mood board"

    play_mode = st.radio(
        "Game",
        _allowed_play,
        horizontal=True,
        key="play_mode",
    )

    # Shared gender + season filters for all Play games
    if st.session_state.pop("_clear_play_filters", False):
        st.session_state["play_gender"] = "Any"
        st.session_state["play_season"] = "Any"
    pf1, pf2, pf3 = st.columns([2, 2, 1])
    with pf1:
        play_gender = st.selectbox(
            "Gender",
            ["Any", "Male", "Female", "Unisex"],
            key="play_gender",
        )
    with pf2:
        play_season = st.selectbox(
            "Season / weather",
            ["Any", "Hot / Summer", "Warm / Mild", "Cool / Autumn", "Cold / Winter"],
            key="play_season",
        )
    with pf3:
        st.write("")
        st.write("")
        if st.button("Clear", key="play_filter_clear"):
            st.session_state["_clear_play_filters"] = True
            st.rerun()

    play_pool = filter_play_pool(play_gender, play_season)
    st.caption(f"Play pool: **{len(play_pool)}** bottle(s) after filters")

    name_map = {f["name"]: f for f in play_pool}
    # Guess list can still show full vault so hard-mode blind is fair? use filtered
    all_names = sorted(name_map.keys())

    MOOD_VISUAL = {
        "Cozy": ("#3d2a1a", "Warm amber glow"),
        "Seductive": ("#2a1520", "Deep rose & shadow"),
        "Fresh": ("#152530", "Cool air & light"),
        "Power": ("#1a2030", "Steel & spice"),
        "Soft": ("#222030", "Powder & quiet"),
        "Gourmand": ("#2a2218", "Sugar & cocoa"),
    }

    FAMILY_COLOR = {
        "Gourmand": "#4a3020",
        "Sweet": "#4a2840",
        "Floral": "#3a2040",
        "Woody": "#2a3018",
        "Oriental": "#302018",
        "Fresh": "#183040",
        "Fruity": "#402030",
        "Spicy": "#402018",
        "Citrus": "#303818",
        "Aromatic": "#203028",
        "Leather": "#281818",
        "Oud": "#201810",
        "Boozy": "#302010",
        "Smoky": "#181818",
        "Powdery": "#282838",
    }

    if play_mode == "Mood board":
        st.markdown(
            '<div style="border:1px solid #1e2a42;border-radius:10px;padding:0.75rem 1rem;'
            'background:linear-gradient(135deg,#12101a,#0b101a);margin-bottom:0.5rem;">'
            '<div style="font-family:Cinzel,Georgia,serif;color:#7eb0ff;font-size:1.05rem;">Mood board</div>'
            '<div style="color:#8a9bb8;font-size:0.85rem;">Pick a feeling - three bottles that match the vibe.</div>'
            '</div>',
            unsafe_allow_html=True,
        )
        mood = st.selectbox("Mood", list(MOOD_PROFILES.keys()), key="play_mood")
        bg, vibe = MOOD_VISUAL.get(mood, ("#101826", MOOD_PROFILES[mood].get("vibe", "")))
        st.markdown(
            f'<div style="border-radius:8px;padding:0.65rem 0.9rem;margin:0.35rem 0 0.75rem 0;'
            f'background:{bg};border:1px solid #2a3a58;">'
            f'<strong style="color:#c8d2e4;">{mood}</strong> '
            f'<span style="color:#8a9bb8;">- {vibe}</span><br>'
            f'<span style="color:#a0b4d0;font-size:0.85rem;">Lean: {", ".join(MOOD_PROFILES[mood]["categories"])}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )
        if st.button("Draw mood scents", type="primary", key="mood_draw"):
            picks = get_mood_picks(mood, top_n=3, pool=play_pool)
            st.session_state["last_mood"] = {"mood": mood, "picks": picks}
            st.session_state["play_stats"]["moods_drawn"] = (
                st.session_state["play_stats"].get("moods_drawn", 0) + 1
            )
            save_persisted_data()
        last_mood = st.session_state.get("last_mood")
        if last_mood:
            st.caption(f"Drawn for: {last_mood.get('mood')}")
            cols = st.columns(min(3, max(1, len(last_mood.get("picks") or []))))
            for i, f in enumerate(last_mood.get("picks") or []):
                badge = " YAY" if st.session_state["user_reactions"].get(f["name"]) == "fav" else ""
                with cols[i % len(cols)]:
                    st.markdown(
                        f'<div style="border:1px solid #1e2a42;border-radius:8px;padding:0.7rem;'
                        f'background:#0b101a;min-height:120px;">'
                        f'<div style="color:#7eb0ff;font-weight:600;">#{i+1} {f["name"]}{badge}</div>'
                        f'<div style="color:#8a9bb8;font-size:0.8rem;">{f["brand"]}</div>'
                        f'<div style="color:#c8d2e4;font-size:0.82rem;margin-top:0.35rem;">'
                        f'{", ".join(f.get("category", []))}</div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
                    if st.button("Wear today", key=f"mood_wear_{i}"):
                        st.session_state["sotd_prefill"] = [f["name"]]
                        st.rerun()

    elif play_mode == "Blind bottle":
        st.markdown(
            '<div style="border:1px solid #1e2a42;border-radius:10px;padding:0.75rem 1rem;'
            'background:linear-gradient(135deg,#0e1018,#12101c);margin-bottom:0.5rem;">'
            '<div style="font-family:Cinzel,Georgia,serif;color:#7eb0ff;font-size:1.05rem;">Blind bottle</div>'
            '<div style="color:#8a9bb8;font-size:0.85rem;">Mystery card - notes only. Guess, then reveal.</div>'
            '</div>',
            unsafe_allow_html=True,
        )
        blind_diff = st.selectbox(
            "Difficulty",
            [
                "Normal (full notes)",
                "Hard (top notes only)",
                "Expert (base notes only)",
                "Scrambled keywords",
            ],
            key="blind_diff",
        )
        if st.button("Draw a mystery bottle", type="primary", key="blind_draw"):
            pool = list(play_pool)
            if pool:
                chosen = random.choice(pool)
                st.session_state["blind_bottle"] = chosen
                st.session_state["blind_revealed"] = False
                st.session_state["play_stats"]["blind_played"] = (
                    st.session_state["play_stats"].get("blind_played", 0) + 1
                )
                save_persisted_data()
        mystery = st.session_state.get("blind_bottle")
        if mystery and not st.session_state.get("blind_revealed"):
            notes_full = mystery.get("notes", "")
            diff = st.session_state.get("blind_diff", "Normal (full notes)")
            if "Hard" in diff:
                if "Heart" in notes_full:
                    shown = (
                        notes_full.split("Heart")[0]
                        .replace("Top -", "")
                        .replace("Top:", "")
                        .strip(" /")
                    )
                else:
                    shown = notes_full[: max(20, len(notes_full) // 3)]
                shown = f"Top-ish: {shown}"
            elif "Expert" in diff:
                if "Base" in notes_full:
                    shown = notes_full.split("Base")[-1].strip(" -:")
                else:
                    shown = notes_full[-max(20, len(notes_full) // 3) :]
                shown = f"Base-ish: {shown}"
            elif "Scrambled" in diff:
                tokens = re.findall(r"[A-Za-z]{3,}", notes_full)
                random.shuffle(tokens)
                shown = ", ".join(tokens[:12])
            else:
                shown = notes_full
            st.markdown(
                f'<div style="border:1px dashed #3a5a8a;border-radius:12px;padding:1rem;'
                f'background:#080c14;text-align:center;margin:0.5rem 0;">'
                f'<div style="font-size:2rem;letter-spacing:0.2em;color:#4a7ac8;">?</div>'
                f'<div style="color:#c8d2e4;margin-top:0.5rem;"><strong>Clue</strong></div>'
                f'<div style="color:#a0b4d0;font-size:0.9rem;margin-top:0.35rem;">{shown}</div>'
                f'<div style="color:#8a9bb8;font-size:0.8rem;margin-top:0.5rem;">'
                f'{mystery.get("season", "")} | {", ".join(mystery.get("category") or [])}'
                f'</div></div>',
                unsafe_allow_html=True,
            )
            guess = st.selectbox(
                "Your guess",
                ["- pick -"] + all_names,
                key="blind_guess_select",
            )
            c1, c2 = st.columns(2)
            with c1:
                if st.button("Check guess", key="blind_check"):
                    if guess == mystery["name"]:
                        st.session_state["play_stats"]["blind_correct"] = (
                            st.session_state["play_stats"].get("blind_correct", 0) + 1
                        )
                        save_persisted_data()
                        st.session_state["blind_revealed"] = True
                        st.success("Correct.")
                    elif guess != "- pick -":
                        st.warning("Not that one.")
            with c2:
                if st.button("Reveal", key="blind_reveal"):
                    st.session_state["blind_revealed"] = True
                    st.rerun()
        if mystery and st.session_state.get("blind_revealed"):
            st.markdown(
                f'<div style="border:1px solid #3a5a8a;border-radius:12px;padding:1rem;'
                f'background:#0c1420;margin:0.5rem 0;">'
                f'<div style="color:#7eb0ff;font-size:1.1rem;font-weight:600;">{mystery["name"]}</div>'
                f'<div style="color:#8a9bb8;">{mystery.get("brand", "")}</div>'
                f'<div style="color:#c8d2e4;font-size:0.88rem;margin-top:0.4rem;">{mystery.get("notes", "")}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
            if st.button("Wear today", key="blind_wear"):
                st.session_state["sotd_prefill"] = [mystery["name"]]
                st.rerun()

    elif play_mode == "Family roulette":
        st.markdown(
            '<div style="border:1px solid #1e2a42;border-radius:10px;padding:0.75rem 1rem;'
            'background:linear-gradient(135deg,#141018,#0b101a);margin-bottom:0.5rem;">'
            '<div style="font-family:Cinzel,Georgia,serif;color:#7eb0ff;font-size:1.05rem;">Family roulette</div>'
            '<div style="color:#8a9bb8;font-size:0.85rem;">Spin a category - three bottles land on the board.</div>'
            '</div>',
            unsafe_allow_html=True,
        )
        families = sorted(
            {
                c
                for f in play_pool
                for c in (f.get("category") or [])
            }
        )
        if st.button("Spin family", type="primary", key="fam_spin"):
            if families:
                fam = random.choice(families)
                pool = [
                    f
                    for f in play_pool
                    if fam in (f.get("category") or [])
                ]
                random.shuffle(pool)
                st.session_state["last_family_spin"] = {
                    "family": fam,
                    "picks": pool[:3],
                }
            else:
                st.warning("No families in the filtered play pool.")
        last_fs = st.session_state.get("last_family_spin")
        if last_fs:
            fam = last_fs.get("family") or "?"
            color = FAMILY_COLOR.get(fam, "#1a2030")
            st.markdown(
                f'<div style="text-align:center;margin:0.6rem 0;">'
                f'<div style="display:inline-block;padding:0.55rem 1.25rem;border-radius:999px;'
                f'background:{color};border:1px solid #3a5a8a;color:#e8f0ff;'
                f'font-family:Cinzel,Georgia,serif;font-size:1.05rem;">{fam}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
            picks = last_fs.get("picks") or []
            if not picks:
                st.warning("No bottles in that family right now.")
            else:
                cols = st.columns(min(3, len(picks)))
                for i, f in enumerate(picks):
                    with cols[i]:
                        st.markdown(
                            f'<div style="border:1px solid #1e2a42;border-radius:8px;padding:0.7rem;'
                            f'background:#0b101a;min-height:110px;">'
                            f'<div style="color:#7eb0ff;font-weight:600;">{f["name"]}</div>'
                            f'<div style="color:#8a9bb8;font-size:0.8rem;">{f.get("brand", "")}</div>'
                            f'<div style="color:#a0b4d0;font-size:0.78rem;margin-top:0.3rem;">'
                            f'{", ".join(f.get("category") or [])}</div>'
                            f'</div>',
                            unsafe_allow_html=True,
                        )
                        if st.button("Wear today", key=f"fam_wear_{i}"):
                            st.session_state["sotd_prefill"] = [f["name"]]
                            st.rerun()

# ===== COLLECTION =====
with tab_collection:
    st.subheader("Collection browser")

    with st.expander("Price range lookup", expanded=True):
        st.caption(
            "Find bottles you logged a price for. Leave wide range to see all priced bottles."
        )
        if st.session_state.pop("_clear_price_lookup", False):
            st.session_state["price_min"] = 0
            st.session_state["price_max"] = 500
            st.session_state["price_gender"] = "Any"
        pr1, pr2, pr3 = st.columns(3)
        with pr1:
            price_min = st.number_input("Min $", min_value=0, max_value=2000, value=0, key="price_min")
        with pr2:
            price_max = st.number_input("Max $", min_value=0, max_value=5000, value=500, key="price_max")
        with pr3:
            price_gender = st.selectbox(
                "Gender",
                ["Any", "Male", "Female", "Unisex"],
                key="price_gender",
            )
        pc1, pc2 = st.columns(2)
        with pc1:
            do_price = st.button("Search prices", type="primary", key="price_search_btn")
        with pc2:
            if st.button("Clear", key="price_clear_btn"):
                st.session_state["_clear_price_lookup"] = True
                st.session_state.pop("price_lookup_hits", None)
                st.rerun()
        if do_price:
            lo, hi = float(min(price_min, price_max)), float(max(price_min, price_max))
            hits = fragrances_in_price_range(lo, hi, price_gender)
            st.session_state["price_lookup_hits"] = {
                "hits": hits,
                "lo": lo,
                "hi": hi,
                "gender": price_gender,
            }
        priced_n = sum(
            1
            for f in st.session_state.get("fragrances_db") or []
            if f.get("price") is not None
        )
        st.caption(f"{priced_n} bottle(s) in the vault have a price logged.")
        pl = st.session_state.get("price_lookup_hits")
        if pl is not None:
            hits = pl.get("hits") or []
            st.write(
                f"**{len(hits)}** match ${pl.get('lo'):.0f} - ${pl.get('hi'):.0f}"
                f" ({pl.get('gender')})"
            )
            if not hits:
                st.info("No priced bottles in that range. Add prices when editing bottles.")
            else:
                for f in hits:
                    st.write(
                        f"**${float(f.get('price')):.0f}** - **{f.get('name')}** "
                        f"({f.get('brand')}) | {f.get('gender')} | "
                        f"{', '.join(f.get('category') or [])}"
                    )
    wear_counts = get_wear_counts()
    favs = [
        name
        for name, status in st.session_state["user_reactions"].items()
        if status == "fav"
    ]
    dislikes = [
        name
        for name, status in st.session_state["user_reactions"].items()
        if status == "dislike"
    ]

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Bottles", len(st.session_state["fragrances_db"]))
    m2.metric("Favorites", len(favs))
    m3.metric("Banished", len(dislikes))
    m4.metric("SOTD logs", len(st.session_state["sotd_history"]))

    # Gender breakdown (using normalize_gender for consistency)
    female_count = 0
    male_count = 0
    unisex_count = 0
    for f in st.session_state["fragrances_db"]:
        g = normalize_gender(f.get("gender", ""))
        if g in ("Female", "Female-leaning"):
            female_count += 1
        elif g in ("Male", "Male-leaning"):
            male_count += 1
        else:
            unisex_count += 1

    g1, g2, g3 = st.columns(3)
    g1.metric("Women / F-leaning", female_count)
    g2.metric("Unisex", unisex_count)
    g3.metric("Men / M-leaning", male_count)

    val = collection_value_summary(st.session_state["fragrances_db"])
    if val["priced"] or val["sized"] or val["by_shelf"]:
        v1, v2, v3 = st.columns(3)
        v1.metric("Logged ml", f"{val['total_ml']:.0f}" if val["sized"] else "-")
        v2.metric("Logged value", f"${val['total_price']:.0f}" if val["priced"] else "-")
        shelf_bits = ", ".join(f"{k}: {n}" for k, n in sorted(val["by_shelf"].items()))
        v3.caption(f"Shelf: {shelf_bits}" if shelf_bits else "")


    badges = compute_badges()
    badges = compute_badges()
    if badges:
        st.caption("Badges: " + "  -  ".join(badges))


    # ----- Wishlist -----
    with st.expander("Wishlist", expanded=False):
        st.caption("Track bottles you want. Check off, then To vault (or move all checked) to add them to your collection.")
        # Clear form fields before widgets if flagged
        if st.session_state.pop("_clear_wishlist_form", False):
            st.session_state["wl_name"] = ""
            st.session_state["wl_brand"] = ""
            st.session_state["wl_notes"] = ""
        wl_name = st.text_input("Name", key="wl_name")
        wl_brand = st.text_input("Brand (optional)", key="wl_brand")
        wl_notes = st.text_input("Notes (optional)", key="wl_notes")
        wa, wb = st.columns(2)
        with wa:
            add_clicked = st.button("Add to wishlist", key="wl_add", use_container_width=True)
        with wb:
            if st.button("Clear fields", key="wl_clear_fields", use_container_width=True):
                st.session_state["_clear_wishlist_form"] = True
                st.rerun()
        if add_clicked:
            if (wl_name or "").strip():
                st.session_state["wishlist"].insert(
                    0,
                    {
                        "name": wl_name.strip(),
                        "brand": (wl_brand or "").strip(),
                        "notes": (wl_notes or "").strip(),
                        "checked": False,
                    },
                )
                save_persisted_data()
                st.session_state["_clear_wishlist_form"] = True
                st.rerun()
            else:
                st.warning("Name is required.")
        if st.session_state.get("wishlist"):
            try:
                st.download_button(
                    "Download wishlist PDF",
                    data=build_wishlist_pdf(st.session_state["wishlist"]),
                    file_name="wishlist.pdf",
                    mime="application/pdf",
                    key="wl_pdf",
                )
            except Exception as ex:
                st.caption(f"PDF unavailable: {ex}")
        # Move all checked items into the vault
        checked_items = [
            (i, it)
            for i, it in enumerate(st.session_state.get("wishlist") or [])
            if it.get("checked")
        ]
        if checked_items:
            st.caption(
                f"{len(checked_items)} checked - move into your real collection when you own them."
            )
            if st.button(
                f"Add {len(checked_items)} checked to vault",
                type="primary",
                key="wl_move_checked",
            ):
                added = 0
                skipped = []
                to_remove = []
                for i, it in checked_items:
                    result = wishlist_item_to_vault(it)
                    if result.get("ok"):
                        added += 1
                        to_remove.append(i)
                    else:
                        skipped.append(result.get("message") or "Skipped")
                for i in sorted(to_remove, reverse=True):
                    if 0 <= i < len(st.session_state["wishlist"]):
                        st.session_state["wishlist"].pop(i)
                save_persisted_data()
                msg = f"Moved {added} to vault."
                if skipped:
                    msg += " " + " | ".join(skipped[:3])
                st.session_state["_wl_move_flash"] = msg
                st.rerun()

        _wl_flash = st.session_state.pop("_wl_move_flash", None)
        if _wl_flash:
            st.success(_wl_flash)

        for wi, item in enumerate(list(st.session_state.get("wishlist") or [])):
            c1, c2, c3, c4 = st.columns([1, 4, 2, 1])
            with c1:
                checked = st.checkbox(
                    "got",
                    value=bool(item.get("checked")),
                    key=f"wl_chk_{wi}_{item.get('name','')}",
                    label_visibility="collapsed",
                )
                if checked != bool(item.get("checked")):
                    st.session_state["wishlist"][wi]["checked"] = checked
                    save_persisted_data()
                    st.rerun()
            with c2:
                mark = "[x]" if item.get("checked") else "[ ]"
                extra = f" - {item.get('brand')}" if item.get("brand") else ""
                line = f"{mark} **{item.get('name')}**{extra}"
                if item.get("notes"):
                    line = line + "  \n*" + str(item.get("notes")) + "*"
                st.markdown(line)
            with c3:
                if item.get("checked"):
                    if st.button("To vault", key=f"wl_to_vault_{wi}"):
                        result = wishlist_item_to_vault(item)
                        if result.get("ok"):
                            st.session_state["wishlist"].pop(wi)
                            save_persisted_data()
                            st.session_state["_wl_move_flash"] = result["message"]
                            st.rerun()
                        else:
                            st.session_state["_wl_move_flash"] = result.get(
                                "message", "Could not add"
                            )
                            st.rerun()
            with c4:
                if st.button("DEL", key=f"wl_del_{wi}"):
                    st.session_state["wishlist"].pop(wi)
                    save_persisted_data()
                    st.rerun()
        if not st.session_state.get("wishlist"):
            st.caption("Wishlist is empty.")


    # Favorite notes cloud
    fav_notes = get_favorite_notes(10)
    if fav_notes:
        cloud = "  -  ".join(f"**{n}** ({c})" for n, c in fav_notes)
        st.markdown(f"**Your note cloud (from YAY):** {cloud}")

    # 30-day family summary (simple heatmap substitute)
    fam = season_family_summary()
    if fam:
        st.caption("Last 30 days  -  families worn")
        fam_bits = "  -  ".join(f"{k}: {v}" for k, v in list(fam.items())[:8])
        st.write(fam_bits)

    # Performance leaderboard from logged sillage / longevity
    with st.expander("Performance leaderboard (from SOTD logs)", expanded=False):
        board = performance_leaderboard(top_n=5)
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Best projection (sillage)**")
            if not board["sillage"]:
                st.caption("Log sillage on SOTD entries to unlock.")
            else:
                for avg, n, name in board["sillage"]:
                    st.write(f"**{name}**  -  {avg:.1f}/5 ({n} log{'s' if n != 1 else ''})")
        with c2:
            st.markdown("**Longest wear (longevity)**")
            if not board["longevity"]:
                st.caption("Log longevity on SOTD entries to unlock.")
            else:
                for avg, n, name in board["longevity"]:
                    st.write(f"**{name}**  -  {avg:.1f}/5 ({n} log{'s' if n != 1 else ''})")


    filter_col, sort_col, flag_col, shelf_col = st.columns(4)
    with filter_col:
        browse_gender = st.selectbox(
            "Filter by gender",
            ["Any", "Women / F-leaning", "Unisex", "Men / M-leaning"],
            key="browse_gender",
        )
    with sort_col:
        browse_sort = st.selectbox(
            "Sort by",
            ["Name (A-Z)", "Brand (A-Z)", "Most worn", "Category"],
            key="browse_sort",
        )
    with flag_col:
        browse_incomplete = st.checkbox(
            "Needs notes only",
            key="browse_incomplete",
            help="Show bottles with thin or vague note text.",
        )
    with shelf_col:
        browse_shelf = st.selectbox(
            "Shelf",
            ["Any"] + SHELF_STATUSES,
            key="browse_shelf",
        )

    db = list(st.session_state["fragrances_db"])

    # Apply gender filter
    if browse_gender == "Women / F-leaning":
        db = [
            f
            for f in db
            if normalize_gender(f.get("gender", "")) in ("Female", "Female-leaning")
        ]
    elif browse_gender == "Men / M-leaning":
        db = [
            f
            for f in db
            if normalize_gender(f.get("gender", "")) in ("Male", "Male-leaning")
        ]
    elif browse_gender == "Unisex":
        db = [
            f
            for f in db
            if normalize_gender(f.get("gender", "")) == "Unisex"
        ]

    if browse_incomplete:
        db = [f for f in db if is_incomplete_notes(f)]
    if browse_shelf != "Any":
        db = [f for f in db if (f.get("shelf_status") or "Own") == browse_shelf]

    if browse_sort == "Name (A-Z)":
        db.sort(key=lambda x: x["name"].lower())
    elif browse_sort == "Brand (A-Z)":
        db.sort(key=lambda x: (x["brand"].lower(), x["name"].lower()))
    elif browse_sort == "Most worn":
        db.sort(key=lambda x: wear_counts.get(x["name"], 0), reverse=True)
    else:
        db.sort(key=lambda x: (",".join(x.get("category", [])), x["name"].lower()))

    # Quick-edit incomplete notes without full Vault form
    incomplete_list = [f for f in st.session_state["fragrances_db"] if is_incomplete_notes(f)]
    with st.expander(
        f"Quick-edit notes ({len(incomplete_list)} need work)", expanded=False
    ):
        if not incomplete_list:
            st.caption("All bottles have solid notes. Nice.")
        else:
            edit_names = sorted(f["name"] for f in incomplete_list)
            pick = st.selectbox("Bottle to fill in", edit_names, key="quick_edit_pick")
            frag = next(
                (f for f in st.session_state["fragrances_db"] if f["name"] == pick),
                None,
            )
            if frag:
                st.caption(f"{frag.get('brand', '')}  -  current: {frag.get('notes', '')[:120]}")
                new_notes = st.text_area(
                    "Notes (Top / Heart / Base)",
                    value=frag.get("notes") or "",
                    key=f"quick_notes_{pick}",
                    height=100,
                )
                if st.button("Save notes", key="quick_notes_save"):
                    for i, f in enumerate(st.session_state["fragrances_db"]):
                        if f["name"] == pick:
                            st.session_state["fragrances_db"][i]["notes"] = new_notes.strip() or "Not specified"
                            break
                    save_persisted_data()
                    st.success(f"Updated notes for **{pick}**")
                    st.rerun()

    with st.expander(f"Browse {len(db)} bottles", expanded=False):

        if not db:
            st.info("No bottles match this gender filter.")
        for i, f in enumerate(db):
            wears = wear_counts.get(f["name"], 0)
            since = days_since_worn(f["name"])
            if since is None:
                since_str = " | never worn"
            elif since == 0:
                since_str = " | worn today"
            else:
                since_str = f" | {since}d ago"
            wear_str = f" | worn {wears}x{since_str}" if wears else since_str
            incomplete = "  -  needs notes" if is_incomplete_notes(f) else ""
            perf = average_performance(f["name"])
            perf_str = ""
            if perf["sillage"] or perf["longevity"]:
                bits = []
                if perf["sillage"]:
                    bits.append(f"sil {perf['sillage']}")
                if perf["longevity"]:
                    bits.append(f"lon {perf['longevity']}")
                perf_str = "  -  avg " + "/".join(bits)
            current_reaction = st.session_state["user_reactions"].get(f["name"])
            status = (
                " YAY"
                if current_reaction == "fav"
                else (" NAH" if current_reaction == "dislike" else "")
            )
            st.markdown(
                f"**{f['name']}**{status} - *{f['brand']}*{incomplete}  \n"
                f"{f['gender']} | {f['season']} | {', '.join(f['category'])}{wear_str}{perf_str}  \n"
                f"<small style='opacity:0.75'>{f['notes']}</small>",
                unsafe_allow_html=True,
            )
            b1, b2, _ = st.columns([1, 1, 4])
            safe_key = f"{i}_{f['name']}"
            with b1:
                if current_reaction == "fav":
                    if st.button("NAH", key=f"col_unfav_{safe_key}"):
                        st.session_state["user_reactions"].pop(f["name"], None)
                        save_persisted_data()
                        st.rerun()
                else:
                    if st.button("YAY", key=f"col_fav_{safe_key}"):
                        st.session_state["user_reactions"][f["name"]] = "fav"
                        save_persisted_data()
                        st.rerun()
            with b2:
                if current_reaction == "dislike":
                    if st.button("UNDO", key=f"col_restore_{safe_key}"):
                        st.session_state["user_reactions"].pop(f["name"], None)
                        save_persisted_data()
                        st.rerun()
                else:
                    if st.button("DEL", key=f"col_dislike_{safe_key}"):
                        st.session_state["user_reactions"][f["name"]] = "dislike"
                        save_persisted_data()
                        st.rerun()
            st.markdown("---")


# ===== VAULT =====
with tab_vault:
    st.subheader("Sanctuary vault")
    n_bottles = len(st.session_state["fragrances_db"])
    st.write(f"**{n_bottles}** bottles in the vault")
    if st.session_state.get("last_saved_at"):
        st.caption(f"Last saved: {st.session_state['last_saved_at']} (Pacific)")
    st.caption("Edits save to the data file. Export JSON after big changes.")

    favs = [
        name
        for name, status in st.session_state["user_reactions"].items()
        if status == "fav"
    ]
    dislikes = [
        name
        for name, status in st.session_state["user_reactions"].items()
        if status == "dislike"
    ]
    c1, c2, c3 = st.columns(3)
    c1.metric("YAY", len(favs))
    c2.metric("DEL", len(dislikes))
    c3.metric("Neutral", max(0, n_bottles - len(favs) - len(dislikes)))
    if st.button("Clear all reactions", key="clear_all_rx"):
        st.session_state["user_reactions"] = {}
        save_persisted_data()
        st.rerun()

    # ----- shared finder (once) -----
    if st.session_state.pop("_clear_manage", False):
        st.session_state["manage_search"] = ""
        st.session_state["manage_gender"] = "Any"
        st.session_state["manage_brand"] = "Any"
        st.session_state["manage_sort"] = "Name (A-Z)"
        st.session_state["edit_select"] = "- select -"
        st.session_state["remove_select"] = "- select -"

    if "manage_search" not in st.session_state:
        st.session_state["manage_search"] = ""
    if "manage_gender" not in st.session_state:
        st.session_state["manage_gender"] = "Any"
    if "manage_brand" not in st.session_state:
        st.session_state["manage_brand"] = "Any"
    if "manage_sort" not in st.session_state:
        st.session_state["manage_sort"] = "Name (A-Z)"

    with st.expander("Find bottles", expanded=True):
        manage_search = st.text_input(
            "Search", key="manage_search", placeholder="Name, brand, or notes"
        )
        ms1, ms2, ms3 = st.columns(3)
        with ms1:
            manage_gender = st.selectbox(
                "Gender", ["Any", "Male", "Female", "Unisex"], key="manage_gender"
            )
        with ms2:
            brands = sorted(
                {
                    (f.get("brand") or "").strip()
                    for f in st.session_state["fragrances_db"]
                    if (f.get("brand") or "").strip()
                }
            )
            manage_brand = st.selectbox("Brand", ["Any"] + brands, key="manage_brand")
        with ms3:
            manage_sort = st.selectbox(
                "Sort",
                ["Name (A-Z)", "Brand (A-Z)", "Gender"],
                key="manage_sort",
            )
        if st.button("Clear filters", key="manage_clear_btn"):
            st.session_state["_clear_manage"] = True
            st.rerun()

        manage_pool = list(st.session_state["fragrances_db"])
        if manage_gender != "Any":
            manage_pool = [f for f in manage_pool if matches_gender(f, manage_gender)]
        if manage_brand != "Any":
            manage_pool = [
                f
                for f in manage_pool
                if (f.get("brand") or "").strip() == manage_brand
            ]
        q = (manage_search or "").strip().lower()
        if q:
            manage_pool = [
                f
                for f in manage_pool
                if q in (f.get("name") or "").lower()
                or q in (f.get("brand") or "").lower()
                or q in (f.get("notes") or "").lower()
            ]
        if manage_sort == "Brand (A-Z)":
            manage_pool.sort(
                key=lambda f: (
                    (f.get("brand") or "").lower(),
                    (f.get("name") or "").lower(),
                )
            )
        elif manage_sort == "Gender":
            manage_pool.sort(
                key=lambda f: (
                    normalize_gender(f.get("gender", "")),
                    (f.get("name") or "").lower(),
                )
            )
        else:
            manage_pool.sort(key=lambda f: (f.get("name") or "").lower())

        label_to_name = {}
        manage_labels = []
        for f in manage_pool:
            label = f"{f.get('name', '?')} - {f.get('brand', '?')}"
            if label in label_to_name:
                label = f"{label} [{normalize_gender(f.get('gender', ''))}]"
            label_to_name[label] = f.get("name")
            manage_labels.append(label)
        st.caption(f"{len(manage_labels)} match(es)")

    manage_options = ["- select -"] + manage_labels

    # ----- EDIT -----
    with st.expander("Edit a bottle", expanded=False):
        if st.session_state.get("edit_select") not in manage_options:
            st.session_state["edit_select"] = "- select -"
        edit_label = st.selectbox("Bottle", manage_options, key="edit_select")
        edit_name = (
            label_to_name.get(edit_label, "- select -")
            if edit_label != "- select -"
            else "- select -"
        )
        if edit_name != "- select -":
            idx = next(
                (
                    i
                    for i, f in enumerate(st.session_state["fragrances_db"])
                    if f["name"] == edit_name
                ),
                None,
            )
            if idx is not None:
                frag = st.session_state["fragrances_db"][idx]
                gender_opts = [
                    "Unisex",
                    "Female",
                    "Male",
                    "Female-leaning",
                    "Male-leaning",
                ]
                g_idx = (
                    gender_opts.index(frag["gender"])
                    if frag["gender"] in gender_opts
                    else 0
                )
                with st.form(key=f"edit_form_{edit_name}"):
                    e_name = st.text_input("Name", value=frag["name"])
                    e_brand = st.text_input("Brand", value=frag["brand"])
                    e_gender = st.selectbox("Gender", gender_opts, index=g_idx)
                    e_season = st.text_input("Season", value=frag["season"])
                    e_notes = st.text_area("Notes", value=frag["notes"])
                    shelf_opts = SHELF_STATUSES
                    cur_shelf = frag.get("shelf_status") or "Own"
                    s_idx = (
                        shelf_opts.index(cur_shelf) if cur_shelf in shelf_opts else 0
                    )
                    e_shelf = st.selectbox("Shelf status", shelf_opts, index=s_idx)
                    e_size = st.text_input(
                        "Size (ml)",
                        value=str(frag.get("size_ml") or ""),
                        placeholder="e.g. 100",
                    )
                    e_price = st.text_input(
                        "Price (optional)",
                        value=str(frag.get("price") or ""),
                        placeholder="e.g. 35",
                    )
                    cat_opts = [
                        "Gourmand",
                        "Sweet",
                        "Floral",
                        "Woody",
                        "Oriental",
                        "Fresh",
                        "Fruity",
                        "Spicy",
                        "Citrus",
                        "Aromatic",
                        "Leather",
                        "Oud",
                        "Boozy",
                        "Smoky",
                        "Powdery",
                    ]
                    e_cats = st.multiselect(
                        "Categories",
                        cat_opts,
                        default=[c for c in frag.get("category", []) if c in cat_opts],
                    )
                    save_edit = st.form_submit_button("Save changes", type="primary")
                    if save_edit:
                        name_lower = e_name.strip().lower()
                        brand_lower = e_brand.strip().lower()
                        conflict = any(
                            i != idx
                            and f["name"].strip().lower() == name_lower
                            and f["brand"].strip().lower() == brand_lower
                            for i, f in enumerate(st.session_state["fragrances_db"])
                        )
                        if conflict:
                            st.error(
                                f"Another bottle already uses '{e_name}' by {e_brand}."
                            )
                        else:
                            def _num(v):
                                try:
                                    return float(str(v).strip()) if str(v).strip() else None
                                except ValueError:
                                    return None

                            st.session_state["fragrances_db"][idx] = {
                                "name": e_name.strip(),
                                "brand": e_brand.strip(),
                                "gender": e_gender,
                                "season": e_season,
                                "notes": e_notes,
                                "category": e_cats if e_cats else ["Gourmand"],
                                "dupe_of": frag.get("dupe_of") or "",
                                "shelf_status": e_shelf,
                                "size_ml": _num(e_size),
                                "price": _num(e_price),
                            }
                            if (
                                e_name != edit_name
                                and edit_name in st.session_state["user_reactions"]
                            ):
                                st.session_state["user_reactions"][e_name] = (
                                    st.session_state["user_reactions"].pop(edit_name)
                                )
                            log_vault_action("edited", e_name.strip(), e_brand.strip())
                            save_persisted_data()
                            st.success(f"Updated **{e_name}**")
                            st.rerun()

    # ----- REMOVE -----
    with st.expander("Remove bottles", expanded=False):
        st.markdown("**Single**")
        if st.session_state.pop("_reset_remove_select", False):
            st.session_state["remove_select"] = "- select -"
        if st.session_state.get("remove_select") not in manage_options:
            st.session_state["remove_select"] = "- select -"
        _rm_flash = st.session_state.pop("_remove_flash", None)
        if _rm_flash:
            st.success(f"Banished **{_rm_flash}**.")
        remove_label = st.selectbox(
            "Bottle to remove", manage_options, key="remove_select"
        )
        remove_name = (
            label_to_name.get(remove_label, "- select -")
            if remove_label != "- select -"
            else "- select -"
        )
        if remove_name != "- select -":
            frag_rm = next(
                (
                    f
                    for f in st.session_state["fragrances_db"]
                    if f["name"] == remove_name
                ),
                None,
            )
            if frag_rm:
                st.warning(
                    f"Remove **{frag_rm.get('name')}** by *{frag_rm.get('brand')}*?"
                )
                confirm = st.checkbox(
                    f"Yes, permanently remove {remove_name}",
                    key=f"remove_confirm_{remove_name}",
                )
                if st.button(
                    "Banish forever",
                    type="primary",
                    key="remove_btn",
                    disabled=not confirm,
                ):
                    st.session_state["fragrances_db"] = [
                        f
                        for f in st.session_state["fragrances_db"]
                        if f["name"] != remove_name
                    ]
                    st.session_state["user_reactions"].pop(remove_name, None)
                    log_vault_action("removed", remove_name)
                    save_persisted_data()
                    st.session_state["_reset_remove_select"] = True
                    st.session_state["_remove_flash"] = remove_name
                    st.rerun()

        st.markdown("**Batch**")
        batch_pick = st.multiselect(
            "Select bottles", manage_labels, key="batch_remove_pick"
        )
        batch_confirm = st.checkbox(
            f"Yes, remove {len(batch_pick)} selected",
            key="batch_remove_confirm",
            disabled=not batch_pick,
        )
        if st.button(
            "Banish selected",
            type="primary",
            key="batch_remove_btn",
            disabled=not (batch_pick and batch_confirm),
        ):
            names = [label_to_name[l] for l in batch_pick if l in label_to_name]
            st.session_state["fragrances_db"] = [
                f
                for f in st.session_state["fragrances_db"]
                if f.get("name") not in names
            ]
            for n in names:
                st.session_state["user_reactions"].pop(n, None)
                log_vault_action("removed", n, "batch")
            save_persisted_data()
            st.session_state["batch_remove_pick"] = []
            st.success(f"Banished {len(names)} bottle(s).")
            st.rerun()

    with st.expander("Activity log", expanded=False):
        vlog = st.session_state.get("vault_log") or []
        if not vlog:
            st.caption("No activity yet.")
        else:
            for entry in vlog[:20]:
                detail = f" - {entry.get('detail')}" if entry.get("detail") else ""
                st.write(
                    f"**{entry.get('when', '?')}** | {entry.get('action', '?')} | "
                    f"**{entry.get('name', '?')}**{detail}"
                )
            if st.button("Clear activity log", key="clear_vault_log"):
                st.session_state["vault_log"] = []
                save_persisted_data()
                st.rerun()

    with st.expander("Backup & restore", expanded=False):
        st.caption("Best protection so Cloud redeploys do not wipe your vault.")
        export_data = {
            "fragrances_db": st.session_state["fragrances_db"],
            "user_reactions": st.session_state["user_reactions"],
            "sotd_history": st.session_state["sotd_history"],
            "layer_recipes": st.session_state.get("layer_recipes", []),
            "play_stats": st.session_state.get("play_stats", {}),
            "last_export_date": st.session_state.get("last_export_date"),
            "last_saved_at": st.session_state.get("last_saved_at"),
            "chart": {
                "sun": st.session_state.get("chart_sun"),
                "moon": st.session_state.get("chart_moon"),
                "rising": st.session_state.get("chart_rising"),
                "venus": st.session_state.get("chart_venus"),
            },
            "wishlist": st.session_state.get("wishlist", []),
            "vault_log": st.session_state.get("vault_log", []),
        }
        json_string = json.dumps(export_data, indent=2, ensure_ascii=False)
        if st.download_button(
            label="Export vault as JSON",
            data=json_string,
            file_name="scented_dead_girl_backup.json",
            mime="application/json",
        ):
            st.session_state["last_export_date"] = pacific_today().isoformat()
            save_persisted_data()
        md_journal = export_journal_markdown()
        st.download_button(
            label="Export journal as Markdown",
            data=md_journal,
            file_name="scented_dead_girl_journal.md",
            mime="text/markdown",
            key="export_md_btn",
        )
        uploaded_file = st.file_uploader("Restore from backup JSON", type=["json"])
        if uploaded_file is not None:
            try:
                imported_data = json.load(uploaded_file)
                if "fragrances_db" in imported_data:
                    st.session_state["fragrances_db"] = imported_data["fragrances_db"]
                if "user_reactions" in imported_data:
                    st.session_state["user_reactions"] = imported_data["user_reactions"]
                if "sotd_history" in imported_data:
                    st.session_state["sotd_history"] = imported_data["sotd_history"]
                if "layer_recipes" in imported_data:
                    st.session_state["layer_recipes"] = imported_data["layer_recipes"]
                if "play_stats" in imported_data:
                    st.session_state["play_stats"] = imported_data["play_stats"]
                if "last_export_date" in imported_data:
                    st.session_state["last_export_date"] = imported_data["last_export_date"]
                if "chart" in imported_data and isinstance(imported_data["chart"], dict):
                    ch = imported_data["chart"]
                    if ch.get("sun"):
                        st.session_state["chart_sun"] = ch["sun"]
                    if ch.get("moon"):
                        st.session_state["chart_moon"] = ch["moon"]
                    if ch.get("rising"):
                        st.session_state["chart_rising"] = ch["rising"]
                    if ch.get("venus"):
                        st.session_state["chart_venus"] = ch["venus"]
                if "wishlist" in imported_data:
                    st.session_state["wishlist"] = imported_data["wishlist"]
                if "vault_log" in imported_data:
                    st.session_state["vault_log"] = imported_data["vault_log"]
                save_persisted_data()
                st.success("Vault restored.")
                st.rerun()
            except Exception as e:
                st.error(f"Restore failed: {e}")
