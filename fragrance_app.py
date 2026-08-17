import datetime
from zoneinfo import ZoneInfo
import hashlib
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
    """Save current session data to disk."""
    data = {
        "fragrances_db": st.session_state.get("fragrances_db", []),
        "user_reactions": st.session_state.get("user_reactions", {}),
        "sotd_history": st.session_state.get("sotd_history", []),
        "layer_recipes": st.session_state.get("layer_recipes", []),
        "play_stats": st.session_state.get("play_stats", {}),
        "last_export_date": st.session_state.get("last_export_date"),
        "chart": {
            "sun": st.session_state.get("chart_sun"),
            "moon": st.session_state.get("chart_moon"),
            "rising": st.session_state.get("chart_rising"),
            "venus": st.session_state.get("chart_venus"),
        },
        "wishlist": st.session_state.get("wishlist", []),
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
    page_icon="S",
    layout="centered",
)

# Custom Gothic Styling - polished, professional, mobile-friendly
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;600;700&family=Inter:ital,wght@0,300;0,400;0,500;0,600;0,700;1,400&display=swap');

:root {
    --bg-deep: #05070c;
    --bg-card: #0b101a;
    --bg-elevated: #101826;
    --border: #1e2a42;
    --border-hover: #3a5a8a;
    --text: #c8d2e4;
    --text-muted: #8a9bb8;
    --accent: #7eb0ff;
    --accent-dim: #4a7ac8;
    --success-bg: #0c1a14;
    --danger: #a04050;
}

html, body, .stApp, [class*="css"], .stMarkdown, p, span, div, label, input, textarea, button {
    font-family: 'Inter', 'Segoe UI', system-ui, -apple-system, sans-serif !important;
    letter-spacing: normal !important;
    word-spacing: normal !important;
}

.stApp {
    background: radial-gradient(ellipse at top, #0a101c 0%, #05070c 50%, #020306 100%);
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
    background: linear-gradient(180deg, #060912 0%, #0a0f18 55%, #080a10 100%) !important;
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
    border-left: 3px solid #6a2030 !important;
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
    filter: drop-shadow(0 0 3px rgba(100, 60, 180, 0.5));
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
    """Map outdoor temperature (Â°F) to the app's weather band."""
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



# Typical daytime outdoor temps (Â°F) by month for inland / Southern California
# (FontanaâLA basin style: warm dry summers, mild winters)
# Typical daytime outdoor temps (Â°F) â Victorville, CA (High Desert / Mojave)
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
    """Suggested outdoor Â°F for Victorville, CA today (Pacific date)."""
    d = day or pacific_today()
    return int(CA_MONTHLY_TEMP_F.get(d.month, 75))


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

    # Chart Big Three + Venus (beauty planet â strong for fragrance)
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
        bits.append(f"{day_prof.get('planet', day)} day Â· {', '.join(day_hits[:2])}")
    notes_l = (f.get("notes") or "").lower()
    kw_hits = [kw for kw in day_prof.get("notes_keywords", []) if kw.lower() in notes_l]
    venus = venus or sun
    for sign, label in ((sun, "Sun"), (moon, "Moon"), (rising, "Rising"), (venus, "Venus")):
        for kw in SIGN_SCENT_PROFILE.get(sign, {}).get("notes_keywords", []):
            if kw.lower() in notes_l and kw not in kw_hits:
                kw_hits.append(kw)
                bits.append(f"{label} {sign} Â· {kw}")
                break
    if kw_hits and not any("Â·" in b and "day" not in b for b in bits):
        bits.append("notes: " + ", ".join(kw_hits[:3]))
    return " Â· ".join(bits[:3]) if bits else "chart + day blend"


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
                "Venus day flatters your beauty placements â soft florals, polished sweetness, and skin-close musk."
            )
        else:
            echoes.append(
                "Venus day invites charm: floral-fruity or creamy gourmand, whichever feels like a compliment."
            )
    elif day == "Saturday":
        if moon == "Capricorn" or sun == "Capricorn" or rising == "Capricorn":
            echoes.append(
                "Saturn day steadies Capricorn energy â amber, woods, and structured gourmands feel like armor."
            )
        else:
            echoes.append(
                "Saturn day favors polish and depth â woody, oriental, or ambered bottles over pure fluff."
            )
    elif day == "Sunday":
        if rising == "Leo" or sun == "Leo" or moon == "Leo":
            echoes.append(
                "Sun day turns up Leo heat â radiant vanilla, honey, and warm florals read as main-character."
            )
        else:
            echoes.append(
                "Sun day asks for confidence and glow â warm gourmand, golden floral, or a bold oriental."
            )
    elif day == "Monday":
        if moon_p.get("element") == "Water":
            echoes.append(
                "Moon day over a water Moon favors milky, musky comfort over sharp edges."
            )
        else:
            echoes.append(
                "Moon day softens the pace â powder, milk, white florals, or a gentle gourmand hug."
            )
    elif day == "Tuesday":
        if sun_p.get("element") == "Fire" or rise_p.get("element") == "Fire":
            echoes.append(
                "Mars day stokes fire placements â spice, projection, and heat without apology."
            )
        else:
            echoes.append(
                "Mars day wants drive â pepper, ginger, dark fruit, or a spicy oriental edge."
            )
    elif day == "Wednesday":
        if sun_p.get("element") == "Air" or rise_p.get("element") == "Air":
            echoes.append(
                "Mercury day loves air signs â keep it light, citrus-bright, or softly floral."
            )
        else:
            echoes.append(
                "Mercury day stays curious and clean â citrus, green, pear, or a breezy floral."
            )
    elif day == "Thursday":
        if any(SIGN_SCENT_PROFILE.get(s, {}).get("element") == "Fire" for s in (sun, rising)):
            echoes.append(
                "Jupiter day expands fire energy â golden, honeyed, or warmly spiced trails."
            )
        else:
            echoes.append(
                "Jupiter day goes generous â amber, vanilla, tonka, or a lush oriental-gourmand."
            )

    chart_cats = set()
    for sign in (sun, moon, rising, venus):
        chart_cats.update(SIGN_SCENT_PROFILE.get(sign, {}).get("categories", []))
    overlap = list(day_cats & chart_cats)[:3]
    if overlap:
        echoes.append(f"Chart overlap with today: **{', '.join(overlap)}** â lean there first.")

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
        f"**{day} â ruled by {planet}.** {vibe}{nl}{nl}"
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


def get_mood_picks(mood: str, top_n: int = 3) -> list:
    scored = []
    for f in st.session_state["fragrances_db"]:
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
    "All-floral day â no woody bases if you can help it.",
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
        notes = f" â {entry['notes']}" if entry.get("notes") else ""
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


# ==========================================
# STREAMLIT USER INTERFACE
# ==========================================
st.title("ScentedDeadGirl")
st.caption("Fragrance sanctuary  |  recommend  |  layer  |  log  |  curate")

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
    st.markdown("### Temp search")
    st.caption("Victorville, CA High Desert - pick degrees (F) + gender, then search.")
    ca_default = int(default_ca_temp_f())
    if st.session_state.pop("_reset_temp_search", False):
        st.session_state["temp_search_f"] = ca_default
        st.session_state["temp_search_gender"] = "Any"
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
    st.caption(
        f"{int(temp_search_f)} F -> {temp_band_label(float(temp_search_f))} | "
        f"Victorville typical this month: {ca_default} F"
    )
    ts1, ts2 = st.columns(2)
    with ts1:
        temp_search_clicked = st.button(
            "Search by temp", type="primary", use_container_width=True, key="temp_search_btn"
        )
    with ts2:
        if st.button("Reset temp", use_container_width=True, key="temp_search_reset"):
            st.session_state["_reset_temp_search"] = True
            st.session_state.pop("last_temp_search", None)
            st.rerun()
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
    with st.form("add_fragrance_form", clear_on_submit=True):
        new_name = st.text_input("Name")
        new_brand = st.text_input("Brand")
        new_gender = st.selectbox(
            "Gender",
            ["Unisex", "Female", "Male", "Female-leaning", "Male-leaning"],
        )
        new_season = st.text_input("Season", value="Fall, Winter")
        new_notes = st.text_input("Notes", placeholder="Top - ... / Heart - ... / Base - ...")
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
                name_lower = new_name.strip().lower()
                brand_lower = new_brand.strip().lower()
                already_exists = any(
                    f["name"].strip().lower() == name_lower
                    and f["brand"].strip().lower() == brand_lower
                    for f in st.session_state["fragrances_db"]
                )
                if already_exists:
                    st.error(f"'{new_name}' by {new_brand} is already in the vault.")
                else:
                    st.session_state["fragrances_db"].append(
                        {
                            "name": new_name.strip(),
                            "brand": new_brand.strip(),
                            "gender": new_gender,
                            "season": new_season or "Versatile",
                            "notes": new_notes if new_notes else "Not specified",
                            "category": new_cats if new_cats else ["Gourmand"],
                        }
                    )
                    save_persisted_data()
                    st.session_state["_add_flash"] = f"Added **{new_name.strip()}**."
                    st.rerun()
            else:
                st.error("Name and brand are required.")

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
                st.warning(f"Last export was {days} days ago â consider backing up.")
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
            st.caption(f"{len(matching)} match(es) Â· ranked by favorites, wears, note quality")
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
            st.caption(f"{len(matching_notes)} match(es) Â· ranked by favorites, wears, note quality")
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
    st.write(
        "Pick a base bottle for partner ideas, or generate free combos from filters."
    )

    # Clear layer studio state before widgets if flagged
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

    lp1, lp2 = st.columns(2)
    with lp1:
        layer_partner_gender = st.selectbox(
            "Filter by gender",
            ["Any", "Male", "Female", "Unisex"],
            key="layer_partner_gender",
            help="Limits the base list and partner suggestions.",
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
                st.warning(
                    "No strong partners for this bottle with the current gender filter."
                )
            else:
                st.markdown(f"#### Partners for **{base_choice}**")
                for pi, (pf, reason) in enumerate(partners, 1):
                    st.info(
                        f"**{pi}. {pf['name']}** ({pf['brand']})\n\n"
                        f"{pf.get('gender', '')} | {', '.join(pf.get('category', []))}\n\n"
                        f"*{reason}*"
                    )
                    if st.button("Use in SOTD", key=f"layer_base_use_{pi}"):
                        st.session_state["sotd_prefill"] = [base_choice, pf["name"]]
                        st.rerun()

    st.markdown("---")
    st.markdown("#### Free combos from filters")
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
    layer_n = st.radio("How many combos", [1, 3, 5], index=1, horizontal=True, key="layer_n")

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
            st.warning(
                "Need at least two matching bottles. Loosen filters or add favorites."
            )
        else:
            for i, (f1, f2, reason) in enumerate(combos, 1):
                st.info(
                    f"**Combo {i}**\n\n"
                    f"**Base:** {f1['name']} ({f1['brand']})\n\n"
                    f"**Layer:** {f2['name']} ({f2['brand']})\n\n"
                    f"*{reason}*"
                )
                b1, b2, _ = st.columns([1, 1, 3])
                with b1:
                    if st.button("Use in SOTD", key=f"layer_use_{i}"):
                        st.session_state["sotd_prefill"] = [f1["name"], f2["name"]]
                        st.rerun()
            st.caption("Tip: spray the richer scent first, then the lighter one.")
        if st.button("Clear combo results", key="layer_clear_results"):
            st.session_state.pop("last_layer", None)
            st.rerun()
    else:
        st.info("Set filters and hit **Suggest layering combos** to get pairings.")


    st.markdown("---")
    st.markdown("#### Saved layer recipes")
    rec_name = st.text_input("Recipe name", placeholder="e.g. Office armor", key="recipe_name_in")
    rec_pick = st.multiselect(
        "Bottles in recipe",
        sorted(f["name"] for f in st.session_state["fragrances_db"]),
        key="recipe_bottles_in",
    )
    if st.button("Save recipe", key="save_recipe_btn"):
        if rec_name.strip() and len(rec_pick) >= 2:
            st.session_state["layer_recipes"].insert(
                0,
                {"name": rec_name.strip(), "bottles": list(rec_pick)},
            )
            save_persisted_data()
            st.success(f"Saved **{rec_name.strip()}**")
            st.rerun()
        else:
            st.warning("Need a name and at least two bottles.")

    for ri, recipe in enumerate(st.session_state.get("layer_recipes") or []):
        st.write(f"**{recipe['name']}** Â· {' + '.join(recipe.get('bottles') or [])}")
        rb1, rb2 = st.columns(2)
        with rb1:
            if st.button("Use in SOTD", key=f"recipe_use_{ri}"):
                st.session_state["sotd_prefill"] = list(recipe.get("bottles") or [])
                st.rerun()
        with rb2:
            if st.button("Delete", key=f"recipe_del_{ri}"):
                st.session_state["layer_recipes"].pop(ri)
                save_persisted_data()
                st.rerun()


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
        st.session_state["sotd_sillage"] = 0
        st.session_state["sotd_longevity"] = 0
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
    perf_c1, perf_c2, perf_c3 = st.columns(3)
    with perf_c1:
        sotd_sillage = st.select_slider(
            "Sillage (projection)",
            options=[0, 1, 2, 3, 4, 5],
            value=0,
            key="sotd_sillage",
            help="0 = skip Â· 1 soft Â· 5 room-filling",
        )
    with perf_c2:
        sotd_longevity = st.select_slider(
            "Longevity (hours feel)",
            options=[0, 1, 2, 3, 4, 5],
            value=0,
            key="sotd_longevity",
            help="0 = skip Â· 1 brief Â· 5 all-day",
        )
    with perf_c3:
        all_names_his = sorted(f["name"] for f in st.session_state["fragrances_db"])
        sotd_his = st.selectbox(
            "His scent (optional)",
            ["- none -"] + all_names_his,
            key="sotd_his_select",
        )


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
                            f"**{pf['name']}** Â· *{pf['brand']}*{mark}  \n"
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
        st.markdown("#### His match")
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
                    f"**{hf['name']}** Â· *{hf['brand']}*\n\n"
                    f"{hf['gender']} Â· {hf['season']} Â· {', '.join(hf.get('category', []))}\n\n"
                    f"*{reason}*\n\n"
                    f"Notes: {hf['notes']}"
                )
                st.markdown("---")

    with st.expander("Quick layering combos"):
        fav_names = [
            n for n, s in st.session_state["user_reactions"].items() if s == "fav"
        ]
        pool = (
            [f for f in st.session_state["fragrances_db"] if f["name"] in fav_names]
            if fav_names
            else st.session_state["fragrances_db"]
        )
        if len(pool) < 2:
            pool = st.session_state["fragrances_db"]
        quick_combos = suggest_layering_combos(pool, num_combos=4)
        if not quick_combos:
            st.write("Need at least two bottles to suggest layers.")
        else:
            for i, (f1, f2, reason) in enumerate(quick_combos, 1):
                ca, cb = st.columns([4, 1])
                with ca:
                    st.markdown(
                        f"**{i}.** `{f1['name']}` + `{f2['name']}`  \n*{reason}*"
                    )
                with cb:
                    if st.button("Use", key=f"use_combo_{i}"):
                        st.session_state["sotd_prefill"] = [f1["name"], f2["name"]]
                        st.rerun()

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
            if sotd_sillage and sotd_sillage > 0:
                entry["sillage"] = int(sotd_sillage)
            if sotd_longevity and sotd_longevity > 0:
                entry["longevity"] = int(sotd_longevity)
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

    st.markdown("#### Weekly SOTD PDF")
    today = pacific_today()
    monday = today - datetime.timedelta(days=today.weekday())
    # Build recent week options (current + last 7 weeks)
    week_opts = []
    for wback in range(0, 8):
        m = monday - datetime.timedelta(weeks=wback)
        iso = m.isocalendar()
        key = f"{iso[0]}-W{iso[1]:02d}"
        label = f"{key} ({m.isoformat()} - {(m + datetime.timedelta(days=6)).isoformat()})"
        week_opts.append((label, key))
    week_labels = [x[0] for x in week_opts]
    pick_label = st.selectbox("Week", week_labels, key="sotd_week_pick")
    pick_key = dict(week_opts)[pick_label]
    try:
        pdf_bytes = build_sotd_week_pdf(pick_key)
        st.download_button(
            "Download week as PDF",
            data=pdf_bytes,
            file_name=f"sotd_{pick_key}.pdf",
            mime="application/pdf",
            key="sotd_week_pdf_btn",
        )
    except Exception as ex:
        st.caption(f"PDF unavailable: {ex}")

    if st.session_state["sotd_history"]:
        with st.expander("Journal history", expanded=True):
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
                    perf_txt = f" Â· {', '.join(perf_bits)}" if perf_bits else ""
                    his_txt = f" Â· his: {entry['his_scent']}" if entry.get("his_scent") else ""
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

    if st.button("Save chart", key="chart_save_btn"):
        save_persisted_data()
        st.success("Chart saved.")
        st.rerun()

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
    st.caption("Mood, blind, twins, this-or-that, family roulette, note match, and more.")

    play_mode = st.radio(
        "Game",
        [
            "Mood board",
            "Blind bottle",
            "Twin finder",
            "Antipode",
            "Least worn",
            "Compare two",
            "This or that",
            "Family roulette",
            "Note match",
            "Badges",
        ],
        horizontal=True,
        key="play_mode",
    )

    name_map = {f["name"]: f for f in st.session_state["fragrances_db"]}
    all_names = sorted(name_map.keys())

    if play_mode == "Mood board":
        mood = st.selectbox("Mood", list(MOOD_PROFILES.keys()), key="play_mood")
        st.write(f"Lean: {', '.join(MOOD_PROFILES[mood]['categories'])}")
        if st.button("Draw mood scents", type="primary", key="mood_draw"):
            picks = get_mood_picks(mood, top_n=3)
            st.session_state["last_mood"] = {"mood": mood, "picks": picks}
            st.session_state["play_stats"]["moods_drawn"] = (
                st.session_state["play_stats"].get("moods_drawn", 0) + 1
            )
            save_persisted_data()
        last_mood = st.session_state.get("last_mood")
        if last_mood:
            st.caption(f"Mood: {last_mood.get('mood')}")
            for i, f in enumerate(last_mood.get("picks") or [], 1):
                badge = " YAY" if st.session_state["user_reactions"].get(f["name"]) == "fav" else ""
                st.success(f"**#{i} - {f['name']}** by *{f['brand']}*{badge}")
                st.write(f"{f['gender']} | {f['season']} | {', '.join(f['category'])}")
                st.caption(f["notes"])
                if st.button("Wear today", key=f"mood_wear_{i}"):
                    st.session_state["sotd_prefill"] = [f["name"]]
                    st.rerun()

    elif play_mode == "Blind bottle":
        st.write("Notes only. Guess the bottle, then reveal.")
        blind_diff = st.selectbox(
            "Difficulty",
            ["Normal (full notes)", "Hard (top notes only)", "Expert (base notes only)", "Scrambled keywords"],
            key="blind_diff",
        )
        if st.button("Draw a mystery bottle", type="primary", key="blind_draw"):
            pool = [
                f
                for f in st.session_state["fragrances_db"]
                if st.session_state["user_reactions"].get(f["name"]) != "dislike"
            ]
            if pool:
                chosen = random.choice(pool)
                st.session_state["blind_bottle"] = chosen
                st.session_state["blind_revealed"] = False
                st.session_state["blind_guess"] = ""
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
                    shown = notes_full.split("Heart")[0].replace("Top -", "").replace("Top:", "").strip(" /")
                else:
                    shown = notes_full[: max(20, len(notes_full)//3)]
                shown = f"Top-ish: {shown}"
            elif "Expert" in diff:
                if "Base" in notes_full:
                    shown = notes_full.split("Base")[-1].strip(" -:")
                else:
                    shown = notes_full[-max(20, len(notes_full)//3):]
                shown = f"Base-ish: {shown}"
            elif "Scrambled" in diff:
                tokens = re.findall(r"[A-Za-z]{3,}", notes_full)
                random.shuffle(tokens)
                shown = ", ".join(tokens[:12])
            else:
                shown = notes_full
            st.info(
                f"**Clue:** {shown}\n\n"
                f"**Season:** {mystery['season']} Â· **Category:** {', '.join(mystery['category'])}"
            )
            guess = st.selectbox(
                "Your guess",
                ["- pick -"] + all_names,
                key="blind_guess_select",
            )
            if st.button("Reveal", key="blind_reveal"):
                st.session_state["blind_revealed"] = True
                if guess == mystery["name"]:
                    st.session_state["play_stats"]["blind_correct"] = (
                        st.session_state["play_stats"].get("blind_correct", 0) + 1
                    )
                    st.session_state["blind_result"] = "correct"
                else:
                    st.session_state["blind_result"] = "miss"
                save_persisted_data()
                st.rerun()
        elif mystery and st.session_state.get("blind_revealed"):
            result = st.session_state.get("blind_result")
            if result == "correct":
                st.success(f"Correct - **{mystery['name']}** by {mystery['brand']}")
            else:
                st.warning(f"It was **{mystery['name']}** by {mystery['brand']}")
            st.write(f"{mystery['gender']} | {mystery['season']} | {', '.join(mystery['category'])}")
            st.caption(mystery["notes"])

    elif play_mode == "Twin finder":
        base_n = st.selectbox("Find twins of", all_names, key="twin_base")
        if st.button("Find twins", type="primary", key="twin_go"):
            base = name_map.get(base_n)
            if base:
                st.session_state["last_twins"] = {
                    "base": base_n,
                    "twins": find_twins(base, top_n=5),
                }
        last_twins = st.session_state.get("last_twins")
        if last_twins:
            st.caption(f"Twins of {last_twins.get('base')}")
            for s, f in last_twins.get("twins") or []:
                st.info(
                    f"**{f['name']}** ({f['brand']}) Â· score {s}\\n\\n"
                    f"{', '.join(f['category'])}\\n\\n{f['notes']}"
                )

    elif play_mode == "Antipode":
        st.write("Find bottles that are the *opposite* of a chosen one â different families, opposite lean.")
        anti_base = st.selectbox("Opposite of", all_names, key="anti_base")
        if st.button("Find antipodes", type="primary", key="anti_go"):
            base = name_map.get(anti_base)
            if base:
                st.session_state["last_antipodes"] = {
                    "base": anti_base,
                    "items": find_antipodes(base, top_n=5),
                }
        last_anti = st.session_state.get("last_antipodes")
        if last_anti:
            st.caption(f"Antipodes of {last_anti.get('base')}")
            for s, f in last_anti.get("items") or []:
                st.info(
                    f"**{f['name']}** ({f['brand']}) Â· contrast {s}\n\n"
                    f"{f['gender']} | {', '.join(f['category'])}\n\n{f['notes']}"
                )
                if st.button("Wear today", key=f"anti_wear_{f['name']}"):
                    st.session_state["sotd_prefill"] = [f["name"]]
                    st.rerun()

    elif play_mode == "Least worn":
        st.write("Bottles that need love (lowest SOTD counts, DEL skipped).")
        if st.button("Show neglected bottles", type="primary", key="least_go"):
            st.session_state["last_least"] = least_worn(top_n=8)
        for wears, f in st.session_state.get("last_least") or []:
            st.write(
                f"**{f['name']}** Â· *{f['brand']}* Â· worn {wears}x  \\n"
                f"{f['gender']} | {', '.join(f['category'])}"
            )
            if st.button("Wear today", key=f"least_wear_{f['name']}"):
                st.session_state["sotd_prefill"] = [f["name"]]
                st.rerun()
            st.markdown("---")

    elif play_mode == "Compare two":
        c1, c2 = st.columns(2)
        with c1:
            left = st.selectbox("Bottle A", all_names, key="cmp_a")
        with c2:
            right = st.selectbox("Bottle B", all_names, key="cmp_b")
        if left and right and left != right:
            fa, fb = name_map[left], name_map[right]
            counts = get_wear_counts()
            col_a, col_b = st.columns(2)
            with col_a:
                st.markdown(f"### {fa['name']}")
                st.write(f"*{fa['brand']}*")
                st.write(f"**Gender:** {fa['gender']}")
                st.write(f"**Season:** {fa['season']}")
                st.write(f"**Category:** {', '.join(fa['category'])}")
                st.write(f"**Worn:** {counts.get(fa['name'], 0)}x")
                st.caption(fa["notes"])
            with col_b:
                st.markdown(f"### {fb['name']}")
                st.write(f"*{fb['brand']}*")
                st.write(f"**Gender:** {fb['gender']}")
                st.write(f"**Season:** {fb['season']}")
                st.write(f"**Category:** {', '.join(fb['category'])}")
                st.write(f"**Worn:** {counts.get(fb['name'], 0)}x")
                st.caption(fb["notes"])
            shared = set(fa["category"]) & set(fb["category"])
            if shared:
                st.caption(f"Shared families: {', '.join(shared)}")


    elif play_mode == "This or that":
        st.write("Two bottles. Pick one. Builds a quick preference lean.")
        if st.button("Draw pair", type="primary", key="tot_draw"):
            pool = [
                f
                for f in st.session_state["fragrances_db"]
                if st.session_state["user_reactions"].get(f["name"]) != "dislike"
            ]
            if len(pool) >= 2:
                a, b = random.sample(pool, 2)
                st.session_state["tot_pair"] = (a["name"], b["name"])
        pair = st.session_state.get("tot_pair")
        if pair:
            a, b = name_map.get(pair[0]), name_map.get(pair[1])
            if a and b:
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown(f"### {a['name']}")
                    st.caption(f"{a['brand']} | {', '.join(a.get('category', []))}")
                    if st.button("Choose A", key="tot_a"):
                        st.session_state["user_reactions"][a["name"]] = "fav"
                        save_persisted_data()
                        st.success(f"Leaning {a['name']}")
                        st.rerun()
                with c2:
                    st.markdown(f"### {b['name']}")
                    st.caption(f"{b['brand']} | {', '.join(b.get('category', []))}")
                    if st.button("Choose B", key="tot_b"):
                        st.session_state["user_reactions"][b["name"]] = "fav"
                        save_persisted_data()
                        st.success(f"Leaning {b['name']}")
                        st.rerun()

    elif play_mode == "Family roulette":
        st.write("Spin a fragrance family, get three bottles from it.")
        families = sorted(
            {
                c
                for f in st.session_state["fragrances_db"]
                for c in (f.get("category") or [])
            }
        )
        if st.button("Spin family", type="primary", key="fam_spin"):
            if families:
                fam = random.choice(families)
                pool = [
                    f
                    for f in st.session_state["fragrances_db"]
                    if fam in (f.get("category") or [])
                    and st.session_state["user_reactions"].get(f["name"]) != "dislike"
                ]
                random.shuffle(pool)
                st.session_state["last_family_spin"] = {
                    "family": fam,
                    "picks": pool[:3],
                }
        last_fs = st.session_state.get("last_family_spin")
        if last_fs:
            st.success(f"Family: **{last_fs.get('family')}**")
            for i, f in enumerate(last_fs.get("picks") or [], 1):
                st.write(
                    f"**{i}. {f['name']}** ({f['brand']}) - {', '.join(f.get('category', []))}"
                )
                if st.button("Wear today", key=f"fam_wear_{i}"):
                    st.session_state["sotd_prefill"] = [f["name"]]
                    st.rerun()

    elif play_mode == "Note match":
        st.write("We show one note keyword. Find a bottle that contains it.")
        if st.button("Draw a note", type="primary", key="note_match_draw"):
            words = []
            for f in st.session_state["fragrances_db"]:
                words.extend(re.findall(r"[A-Za-z]{4,}", f.get("notes", "")))
            stop = {"with", "from", "notes", "heart", "base", "top", "leaning", "style"}
            words = [w for w in words if w.lower() not in stop]
            if words:
                st.session_state["note_match_kw"] = random.choice(words)
        kw = st.session_state.get("note_match_kw")
        if kw:
            st.info(f"Find a bottle with: **{kw}**")
            guess = st.selectbox(
                "Your pick", ["- pick -"] + all_names, key="note_match_guess"
            )
            if st.button("Check", key="note_match_check"):
                fr = name_map.get(guess)
                if fr and kw.lower() in (fr.get("notes") or "").lower():
                    st.success(f"Yes - {guess} has {kw}.")
                    st.session_state["play_stats"]["note_match_wins"] = (
                        st.session_state["play_stats"].get("note_match_wins", 0) + 1
                    )
                    save_persisted_data()
                else:
                    hits = [
                        f["name"]
                        for f in st.session_state["fragrances_db"]
                        if kw.lower() in (f.get("notes") or "").lower()
                    ][:5]
                    st.warning(
                        "Not in that bottle."
                        + (f" Examples: {', '.join(hits)}" if hits else "")
                    )

    else:  # Badges
        streak = sotd_streak()
        badges = compute_badges()
        stats = st.session_state.get("play_stats") or {}
        m1, m2, m3 = st.columns(3)
        m1.metric("SOTD streak", streak)
        m2.metric("Blind plays", stats.get("blind_played", 0))
        m3.metric("Blind correct", stats.get("blind_correct", 0))
        if badges:
            st.success(" Â· ".join(badges))
        else:
            st.info("Log a scent, star bottles, layer, or play blind bottle to earn badges.")

# ===== COLLECTION =====
with tab_collection:
    st.subheader("Collection browser")
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

    badges = compute_badges()
    if badges:
        st.caption("Badges: " + " Â· ".join(badges))


    # ----- Wishlist -----
    with st.expander("Wishlist", expanded=False):
        st.caption("Track bottles you want - check off when acquired, download a PDF list.")
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
        for wi, item in enumerate(list(st.session_state.get("wishlist") or [])):
            c1, c2, c3 = st.columns([1, 5, 1])
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
                if st.button("DEL", key=f"wl_del_{wi}"):
                    st.session_state["wishlist"].pop(wi)
                    save_persisted_data()
                    st.rerun()
        if not st.session_state.get("wishlist"):
            st.caption("Wishlist is empty.")

    # Favorite notes cloud
    fav_notes = get_favorite_notes(10)
    if fav_notes:
        cloud = " Â· ".join(f"**{n}** ({c})" for n, c in fav_notes)
        st.markdown(f"**Your note cloud (from YAY):** {cloud}")

    # 30-day family summary (simple heatmap substitute)
    fam = season_family_summary()
    if fam:
        st.caption("Last 30 days Â· families worn")
        fam_bits = " Â· ".join(f"{k}: {v}" for k, v in list(fam.items())[:8])
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
                    st.write(f"**{name}** Â· {avg:.1f}/5 ({n} log{'s' if n != 1 else ''})")
        with c2:
            st.markdown("**Longest wear (longevity)**")
            if not board["longevity"]:
                st.caption("Log longevity on SOTD entries to unlock.")
            else:
                for avg, n, name in board["longevity"]:
                    st.write(f"**{name}** Â· {avg:.1f}/5 ({n} log{'s' if n != 1 else ''})")


    filter_col, sort_col, flag_col = st.columns(3)
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
                st.caption(f"{frag.get('brand', '')} Â· current: {frag.get('notes', '')[:120]}")
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
            incomplete = " Â· needs notes" if is_incomplete_notes(f) else ""
            perf = average_performance(f["name"])
            perf_str = ""
            if perf["sillage"] or perf["longevity"]:
                bits = []
                if perf["sillage"]:
                    bits.append(f"sil {perf['sillage']}")
                if perf["longevity"]:
                    bits.append(f"lon {perf['longevity']}")
                perf_str = " Â· avg " + "/".join(bits)
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
    st.write(f"Bottles in the vault: **{len(st.session_state['fragrances_db'])}**")

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
    if favs:
        st.write(f"**Cherished:** {', '.join(sorted(favs))}")
    if dislikes:
        st.write(f"**Banished:** {', '.join(sorted(dislikes))}")

    if st.button("Clear all reactions", key="clear_all_rx"):
        st.session_state["user_reactions"] = {}
        save_persisted_data()
        st.rerun()

    st.markdown("---")
    st.markdown("#### Find a bottle")
    st.caption("Shared search for Edit and Remove below.")

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

    ms1, ms2 = st.columns(2)
    with ms1:
        manage_search = st.text_input(
            "Search name or notes",
            key="manage_search",
            placeholder="e.g. Eclaire, vanilla, oud",
        )
    with ms2:
        manage_gender = st.selectbox(
            "Gender",
            ["Any", "Male", "Female", "Unisex"],
            key="manage_gender",
        )

    brands = sorted(
        {
            (f.get("brand") or "").strip()
            for f in st.session_state["fragrances_db"]
            if (f.get("brand") or "").strip()
        }
    )
    ms3, ms4 = st.columns(2)
    with ms3:
        manage_brand = st.selectbox(
            "Brand",
            ["Any"] + brands,
            key="manage_brand",
        )
    with ms4:
        manage_sort = st.selectbox(
            "Sort",
            ["Name (A-Z)", "Brand (A-Z)", "Gender"],
            key="manage_sort",
        )

    if st.button("Clear find filters", key="manage_clear_btn"):
        st.session_state["_clear_manage"] = True
        st.rerun()

    manage_pool = list(st.session_state["fragrances_db"])
    if manage_gender != "Any":
        manage_pool = [f for f in manage_pool if matches_gender(f, manage_gender)]
    if manage_brand != "Any":
        manage_pool = [
            f for f in manage_pool if (f.get("brand") or "").strip() == manage_brand
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

    st.caption(f"{len(manage_labels)} bottle(s) match")
    manage_options = ["- select -"] + manage_labels

    # ---------- EDIT (only) ----------
    st.markdown("---")
    st.markdown("#### Edit bottle")
    st.caption("Update name, brand, gender, season, notes, or categories.")

    if st.session_state.get("edit_select") not in manage_options:
        st.session_state["edit_select"] = "- select -"

    edit_label = st.selectbox(
        "Bottle to edit",
        manage_options,
        key="edit_select",
    )
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
                        st.session_state["fragrances_db"][idx] = {
                            "name": e_name.strip(),
                            "brand": e_brand.strip(),
                            "gender": e_gender,
                            "season": e_season,
                            "notes": e_notes,
                            "category": e_cats if e_cats else ["Gourmand"],
                        }
                        if (
                            e_name != edit_name
                            and edit_name in st.session_state["user_reactions"]
                        ):
                            st.session_state["user_reactions"][e_name] = (
                                st.session_state["user_reactions"].pop(edit_name)
                            )
                        save_persisted_data()
                        st.success(f"Updated **{e_name}**")
                        st.rerun()

    # ---------- REMOVE (only) ----------
    st.markdown("---")
    st.markdown("#### Remove bottle")
    st.caption("Permanently delete a bottle from the vault. This cannot be undone.")

    if st.session_state.get("remove_select") not in manage_options:
        st.session_state["remove_select"] = "- select -"

    remove_label = st.selectbox(
        "Bottle to remove",
        manage_options,
        key="remove_select",
    )
    remove_name = (
        label_to_name.get(remove_label, "- select -")
        if remove_label != "- select -"
        else "- select -"
    )

    if remove_name != "- select -":
        frag_rm = next(
            (f for f in st.session_state["fragrances_db"] if f["name"] == remove_name),
            None,
        )
        if frag_rm:
            st.warning(
                f"About to remove **{frag_rm.get('name')}** by *{frag_rm.get('brand')}* "
                f"({frag_rm.get('gender')})."
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
                save_persisted_data()
                st.session_state["remove_select"] = "- select -"
                st.success(f"Banished **{remove_name}**.")
                st.rerun()

    st.markdown("---")
    st.markdown("#### Backup & restore")
    export_data = {
        "fragrances_db": st.session_state["fragrances_db"],
        "user_reactions": st.session_state["user_reactions"],
        "sotd_history": st.session_state["sotd_history"],
        "layer_recipes": st.session_state.get("layer_recipes", []),
        "play_stats": st.session_state.get("play_stats", {}),
        "last_export_date": st.session_state.get("last_export_date"),
        "chart": {
            "sun": st.session_state.get("chart_sun"),
            "moon": st.session_state.get("chart_moon"),
            "rising": st.session_state.get("chart_rising"),
            "venus": st.session_state.get("chart_venus"),
        },
        "wishlist": st.session_state.get("wishlist", []),
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
            save_persisted_data()
            st.success("Vault restored.")
            st.rerun()
        except Exception as e:
            st.error(f"Restore failed: {e}")
