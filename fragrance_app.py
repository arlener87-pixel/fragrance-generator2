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
    font-family: 'Source Sans 3', 'Segoe UI', system-ui, sans-serif !important;
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
    f: dict, gender: str, weather: str, category: str, occasion: str
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

    # Stable tie-breaker instead of random so rankings don't jump every rerun
    score += _stable_tiebreak(name)
    return score


def get_top_fragrances(
    gender: str, weather: str, category: str, occasion: str, top_n: int, favorites_only: bool = False
) -> list:
    scored = []
    for f in st.session_state["fragrances_db"]:
        if st.session_state["user_reactions"].get(f["name"]) == "dislike":
            continue
        if favorites_only and st.session_state["user_reactions"].get(f["name"]) != "fav":
            continue
        if (
            matches_gender(f, gender)
            and matches_weather(f, weather)
            and matches_category(f, category)
            and matches_occasion(f, occasion)
        ):
            s = score_fragrance(f, gender, weather, category, occasion)
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


def score_fragrance_for_day(f: dict, day: str, sun: str, moon: str, rising: str) -> int:
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

    # Chart Big Three (secondary blend)
    cat_weights = chart_category_weights(sun, moon, rising)
    for c in f.get("category", []):
        score += cat_weights.get(c, 0) * 3

    for sign in (sun, moon, rising):
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


def get_day_fragrances(day: str, sun: str, moon: str, rising: str, top_n: int = 5) -> list:
    scored = []
    for f in st.session_state["fragrances_db"]:
        s = score_fragrance_for_day(f, day, sun, moon, rising)
        if s > 0:
            scored.append((s, f))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [f for _, f in scored[:top_n]]



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

# ---------- MAIN TABS ----------
tab_discover, tab_layer, tab_roulette, tab_sotd, tab_horoscope, tab_collection, tab_vault = st.tabs(
    ["Discover", "Layer", "Roulette", "SOTD", "Stars", "Collection", "Vault"]
)

# ===== DISCOVER =====
with tab_discover:
    st.markdown(
        "Filter from the sidebar, search by name or note, then generate picks and layering ideas."
    )

    # Name / brand search
    if search_query:
        st.subheader(f'Search | "{search_query}"')
        query_lower = search_query.lower()
        matching = [
            f
            for f in st.session_state["fragrances_db"]
            if query_lower in f["name"].lower() or query_lower in f["brand"].lower()
        ]
        if not matching:
            st.warning("No fragrances matched that name or brand.")
        else:
            st.caption(f"{len(matching)} match(es)")
            for f in matching:
                render_fragrance_card(f, key_prefix=f"search_{search_query}")

    # Note search
    if note_query:
        st.subheader(f'Notes | "{note_query}"')
        note_q = note_query.lower()
        matching_notes = [
            f
            for f in st.session_state["fragrances_db"]
            if note_q in f["notes"].lower()
        ]
        if not matching_notes:
            st.warning("No fragrances contain that note.")
        else:
            st.caption(f"{len(matching_notes)} match(es)")
            for f in matching_notes:
                render_fragrance_card(f, key_prefix=f"note_{note_query}")

    # Recommendations (persist so Love/Trash does not wipe the list)
    if generate_clicked:
        selected = get_top_fragrances(
            gender, weather, category, occasion, num_recs, favorites_only=favorites_only
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
    st.write("Build a duo from your vault. Filters narrow the pool; stars get a boost.")

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
    else:
        st.info("Set filters and hit **Suggest layering combos** to get pairings.")

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

    if st.button("Spin the roulette", type="primary", key="spin_roulette_btn"):
        recent_worn = set()
        for entry in st.session_state.get("sotd_history", [])[:5]:
            if entry.get("scents"):
                recent_worn.update(entry["scents"])
            elif entry.get("scent"):
                for part in entry["scent"].split(" + "):
                    recent_worn.add(part.strip())

        pool = []
        for f in st.session_state["fragrances_db"]:
            if st.session_state["user_reactions"].get(f["name"]) == "dislike":
                continue
            if f["name"] in recent_worn:
                continue
            if matches_gender(f, roulette_gender) and matches_weather(f, roulette_season):
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
                    <span class="floating-bat bat1">ð¦</span>
                    <span class="floating-bat bat2">ð¦</span>
                    <span class="floating-bat bat3">ð¦</span>
                    <span class="floating-bat bat4">ð¦</span>
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
    all_frag_names = sorted(f["name"] for f in st.session_state["fragrances_db"])

    # Clear form on next run AFTER log (must happen before widgets are created)
    if st.session_state.pop("_clear_sotd_form", False):
        st.session_state["sotd_multiselect"] = []
        st.session_state["sotd_notes_input"] = ""
        st.session_state["sotd_date"] = pacific_today()

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

    if st.button("Log today's scent", type="primary"):
        if sotd_choices:
            today_date = sotd_date.strftime("%Y-%m-%d") if hasattr(sotd_date, "strftime") else str(sotd_date)
            scent_display = " + ".join(sotd_choices)
            is_layering = len(sotd_choices) > 1
            st.session_state["sotd_history"].insert(
                0,
                {
                    "date": today_date,
                    "scent": scent_display,
                    "scents": sotd_choices,
                    "is_layering": is_layering,
                    "notes": sotd_notes,
                },
            )
            save_persisted_data()
            # Flag form clear for the NEXT run (cannot mutate widget keys after widgets exist)
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

    if st.session_state["sotd_history"]:
        with st.expander("Journal history", expanded=True):
            for i, entry in enumerate(st.session_state["sotd_history"]):
                layer_badge = " | layering" if entry.get("is_layering") else ""
                notes_text = f" - {entry['notes']}" if entry.get("notes") else ""
                hcol, xcol = st.columns([6, 1])
                with hcol:
                    st.write(
                        f"**{entry['date']}:** *{entry['scent']}*{layer_badge}{notes_text}"
                    )
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
    st.caption(
        "Day-of-week horoscope picks for Female and Unisex bottles, "
        "blended with your birth chart."
    )

    st.markdown("#### Your chart")
    st.info(
        f"**Born** {DEFAULT_CHART['birth_date']} Â· {DEFAULT_CHART['birth_time']} Â· "
        f"{DEFAULT_CHART['birth_place']}\n\n"
        f"**Sun** {DEFAULT_CHART['sun']} Â· **Moon** {DEFAULT_CHART['moon']} Â· "
        f"**Rising** {DEFAULT_CHART['rising']} Â· **Venus** {DEFAULT_CHART['venus']}\n\n"
        f"*{DEFAULT_CHART['notes']}*"
    )

    signs = list(SIGN_SCENT_PROFILE.keys())
    hc1, hc2, hc3 = st.columns(3)
    with hc1:
        sun_s = st.selectbox(
            "Sun",
            signs,
            index=signs.index(DEFAULT_CHART["sun"]),
            key="chart_sun",
        )
    with hc2:
        moon_s = st.selectbox(
            "Moon",
            signs,
            index=signs.index(DEFAULT_CHART["moon"]),
            key="chart_moon",
        )
    with hc3:
        rise_s = st.selectbox(
            "Rising",
            signs,
            index=signs.index(DEFAULT_CHART["rising"]),
            key="chart_rising",
        )

    st.markdown("#### Day of the week")
    weekdays = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    ]
    # Default to Pacific "today" weekday
    today_name = pacific_today().strftime("%A")
    default_day_idx = weekdays.index(today_name) if today_name in weekdays else 0
    if "chart_day" not in st.session_state:
        st.session_state["chart_day"] = today_name

    day_s = st.selectbox(
        "Choose day",
        weekdays,
        key="chart_day",
        help="Each day is ruled by a planet that steers the scent mood.",
    )
    day_prof = DAY_RULER[day_s]
    st.write(
        f"**{day_s}** Â· ruled by **{day_prof['planet']}**  \n"
        f"{day_prof['vibe']}  \n"
        f"Families: {', '.join(day_prof['categories'])}"
    )

    chart_n = st.radio("How many picks", [3, 5, 7], index=1, horizontal=True, key="chart_n")
    if st.button("Draw day scents", type="primary", key="chart_draw_btn"):
        picks = get_day_fragrances(day_s, sun_s, moon_s, rise_s, top_n=chart_n)
        st.session_state["last_chart_picks"] = {
            "picks": picks,
            "meta": {
                "day": day_s,
                "planet": day_prof["planet"],
                "sun": sun_s,
                "moon": moon_s,
                "rising": rise_s,
            },
        }

    last_chart = st.session_state.get("last_chart_picks")
    if last_chart is not None:
        meta = last_chart.get("meta") or {}
        picks = last_chart.get("picks") or []
        st.subheader(f"{meta.get('day', 'Day')} scents")
        st.caption(
            f"{meta.get('day')} Â· {meta.get('planet')}  |  "
            f"Sun {meta.get('sun')} Â· Moon {meta.get('moon')} Â· Rising {meta.get('rising')}  |  "
            f"Female / Unisex only"
        )
        if not picks:
            st.warning(
                "No Female/Unisex matches for this day + chart blend. "
                "Try another day or clear some DEL marks."
            )
        else:
            for i, f in enumerate(picks, 1):
                current_reaction = st.session_state["user_reactions"].get(f["name"])
                badge = " YAY" if current_reaction == "fav" else ""
                st.success(f"**#{i} - {f['name']}** by *{f['brand']}*{badge}")
                st.write(f"**Gender:** {f['gender']} | **Season:** {f['season']}")
                st.write(f"**Category:** {', '.join(f['category'])}")
                st.caption(f"Notes: {f['notes']}")
                c1, c2, _ = st.columns([1, 1, 4])
                with c1:
                    if st.button("YAY", key=f"chart_fav_{f['name']}_{i}"):
                        st.session_state["user_reactions"][f["name"]] = "fav"
                        save_persisted_data()
                        st.rerun()
                with c2:
                    if st.button("DEL", key=f"chart_dislike_{f['name']}_{i}"):
                        st.session_state["user_reactions"][f["name"]] = "dislike"
                        save_persisted_data()
                        st.rerun()
                st.markdown("---")
            st.caption(
                "Friday (Venus) loves your Libra Sun; Saturday (Saturn) echoes Capricorn Moon; "
                "Sunday (Sun) amplifies Leo rising."
            )
    else:
        st.info(
            f"Today is **{today_name}**. Pick a day and hit **Draw day scents** "
            "for Female / Unisex recommendations."
        )

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

    browse_sort = st.selectbox(
        "Sort by",
        ["Name (A-Z)", "Brand (A-Z)", "Most worn", "Category"],
        key="browse_sort",
    )
    db = list(st.session_state["fragrances_db"])
    if browse_sort == "Name (A-Z)":
        db.sort(key=lambda x: x["name"].lower())
    elif browse_sort == "Brand (A-Z)":
        db.sort(key=lambda x: (x["brand"].lower(), x["name"].lower()))
    elif browse_sort == "Most worn":
        db.sort(key=lambda x: wear_counts.get(x["name"], 0), reverse=True)
    else:
        db.sort(key=lambda x: (",".join(x.get("category", [])), x["name"].lower()))

    with st.expander(f"Browse all {len(db)} bottles", expanded=False):
        for i, f in enumerate(db):
            wears = wear_counts.get(f["name"], 0)
            wear_str = f" | worn {wears}x" if wears else ""
            current_reaction = st.session_state["user_reactions"].get(f["name"])
            status = (
                " YAY"
                if current_reaction == "fav"
                else (" NAH" if current_reaction == "dislike" else "")
            )
            st.markdown(
                f"**{f['name']}**{status} - *{f['brand']}*  \n"
                f"{f['gender']} | {f['season']} | {', '.join(f['category'])}{wear_str}  \n"
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
    st.markdown("#### Edit or remove")
    manage_names = sorted(f["name"] for f in st.session_state["fragrances_db"])
    selected_manage = st.selectbox(
        "Choose a bottle",
        ["- select -"] + manage_names,
        key="manage_select",
    )

    if selected_manage != "- select -":
        idx = next(
            (
                i
                for i, f in enumerate(st.session_state["fragrances_db"])
                if f["name"] == selected_manage
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
            with st.form(key=f"edit_form_{selected_manage}"):
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
                col_save, col_del = st.columns(2)
                with col_save:
                    save_edit = st.form_submit_button("Save changes")
                with col_del:
                    delete_it = st.form_submit_button("Banish forever")

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
                            e_name != selected_manage
                            and selected_manage in st.session_state["user_reactions"]
                        ):
                            st.session_state["user_reactions"][e_name] = (
                                st.session_state["user_reactions"].pop(selected_manage)
                            )
                        save_persisted_data()
                        st.success(f"Updated **{e_name}**")
                        st.rerun()

                if delete_it:
                    st.session_state["fragrances_db"].pop(idx)
                    st.session_state["user_reactions"].pop(selected_manage, None)
                    save_persisted_data()
                    st.success(f"Banished **{selected_manage}**.")
                    st.rerun()

    st.markdown("---")
    st.markdown("#### Backup & restore")
    export_data = {
        "fragrances_db": st.session_state["fragrances_db"],
        "user_reactions": st.session_state["user_reactions"],
        "sotd_history": st.session_state["sotd_history"],
    }
    json_string = json.dumps(export_data, indent=2, ensure_ascii=False)
    st.download_button(
        label="Export vault as JSON",
        data=json_string,
        file_name="scented_dead_girl_backup.json",
        mime="application/json",
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
            save_persisted_data()
            st.success("Vault restored.")
            st.rerun()
        except Exception as e:
            st.error(f"Restore failed: {e}")
