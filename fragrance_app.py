import datetime
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
    page_icon="🖤",
    layout="centered",
)

# Custom Gothic Styling for ScentedDeadGirl Aesthetic
# Deep black, blood-crimson accents, spectral blue, floating bats
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;600;700&family=Cormorant+Garamond:ital,wght@0,400;0,500;0,600;1,400;1,500&display=swap');

/* Base - Cormorant Garamond body, emoji fonts first */
html, body, .stApp, [class*="css"], .stMarkdown, p, span, div, label, input, textarea, button {
    font-family: 'Apple Color Emoji', 'Segoe UI Emoji', 'Noto Color Emoji', 'Android Emoji', emoji, 'Cormorant Garamond', Georgia, 'Times New Roman', Times, serif !important;
}

.stApp {
    background: radial-gradient(ellipse at top, #0a0e18 0%, #020408 45%, #000000 100%);
    color: #c8d0e0;
}

/* Headings - Cinzel */
h1, h2, h3, h4, h5, h6 {
    color: #9ec5ff !important;
    font-family: 'Apple Color Emoji', 'Segoe UI Emoji', 'Noto Color Emoji', emoji, 'Cinzel', Georgia, serif !important;
    text-shadow: 0 0 12px rgba(80, 140, 255, 0.55), 0 0 4px rgba(180, 40, 60, 0.3), 2px 2px 6px rgba(0, 0, 0, 0.95);
    letter-spacing: 1.5px;
    font-weight: 600 !important;
}

h1 {
    font-size: 2.4rem !important;
    border-bottom: 1px solid #2a1a30;
    padding-bottom: 0.5rem;
    background: linear-gradient(90deg, transparent, rgba(40, 20, 50, 0.4), transparent);
    letter-spacing: 2px;
}

p, .stMarkdown, .stCaption, label, .stText, .stInfo, .stSuccess, .stWarning, .stError {
    font-family: 'Apple Color Emoji', 'Segoe UI Emoji', 'Noto Color Emoji', emoji, 'Cormorant Garamond', Georgia, serif !important;
    color: #b0c0d8 !important;
    font-size: 1.1rem !important;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #05070e 0%, #0a0f1a 50%, #08060c 100%) !important;
    border-right: 1px solid #1a1525;
    box-shadow: 4px 0 20px rgba(0, 0, 0, 0.6);
}
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {
    color: #8ab4ff !important;
    font-family: 'Apple Color Emoji', 'Segoe UI Emoji', 'Noto Color Emoji', emoji, 'Cinzel', Georgia, serif !important;
    text-shadow: 0 0 8px rgba(60, 100, 200, 0.4);
    letter-spacing: 1.2px;
}

/* Buttons */
.stButton > button {
    background: linear-gradient(180deg, #0c1528 0%, #070e1a 100%) !important;
    color: #a0c8ff !important;
    border: 1px solid #2a4068 !important;
    border-radius: 2px !important;
    font-family: 'Apple Color Emoji', 'Segoe UI Emoji', 'Noto Color Emoji', emoji, 'Cinzel', Georgia, serif !important;
    font-weight: 600 !important;
    letter-spacing: 1px;
    transition: all 0.3s ease;
    box-shadow: 0 0 8px rgba(30, 70, 150, 0.2);
}
.stButton > button:hover {
    background: linear-gradient(180deg, #152545 0%, #0c1830 100%) !important;
    border-color: #4a7ac8 !important;
    color: #e8f0ff !important;
    box-shadow: 0 0 18px rgba(70, 130, 255, 0.5);
    transform: translateY(-1px);
}
.stButton > button:active {
    background: #0a1220 !important;
}
.stButton > button[kind="primary"] {
    background: linear-gradient(180deg, #121e38 0%, #0a1428 100%) !important;
    border: 1px solid #3a6aaa !important;
    color: #d0e4ff !important;
    box-shadow: 0 0 10px rgba(50, 100, 200, 0.3);
}

/* Inputs */
.stTextInput > div > div > input,
.stSelectbox > div > div > select,
.stMultiSelect > div > div,
.stTextArea > div > div > textarea {
    background-color: #080c16 !important;
    color: #d0e0f8 !important;
    border: 1px solid #1e2a48 !important;
    border-radius: 2px !important;
    font-family: 'Apple Color Emoji', 'Segoe UI Emoji', 'Noto Color Emoji', emoji, 'Cormorant Garamond', Georgia, serif !important;
}
.stTextInput > div > div > input:focus,
.stSelectbox > div > div > select:focus {
    border-color: #4a80d0 !important;
    box-shadow: 0 0 10px rgba(60, 120, 220, 0.45) !important;
}

.stRadio label, .stCheckbox label {
    font-family: 'Apple Color Emoji', 'Segoe UI Emoji', 'Noto Color Emoji', emoji, 'Cormorant Garamond', Georgia, serif !important;
    color: #a8bdd8 !important;
}

.stAlert {
    background-color: #0a101c !important;
    border: 1px solid #1e2a48 !important;
    color: #b8cce8 !important;
    font-family: 'Apple Color Emoji', 'Segoe UI Emoji', 'Noto Color Emoji', emoji, 'Cormorant Garamond', Georgia, serif !important;
}

/* Expanders - hide broken material icon text */
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
    font-family: 'Apple Color Emoji', 'Segoe UI Emoji', 'Noto Color Emoji', emoji, 'Cinzel', Georgia, serif !important;
    color: #9ec5ff !important;
    background: linear-gradient(90deg, #0a0e18 0%, #0c1220 100%) !important;
    border: 1px solid #1e2a48 !important;
    border-radius: 4px !important;
    padding: 0.6rem 1rem !important;
    letter-spacing: 1px;
    text-shadow: 0 0 8px rgba(80, 140, 255, 0.35);
    overflow: hidden !important;
}
[data-testid="stExpander"] summary:hover {
    border-color: #3a6aaa !important;
    box-shadow: 0 0 12px rgba(60, 120, 220, 0.25);
}
[data-testid="stExpander"] summary p,
[data-testid="stExpander"] summary div {
    color: #9ec5ff !important;
    font-size: 1rem !important;
}

.stDownloadButton > button {
    background: linear-gradient(180deg, #0c1528 0%, #070e1a 100%) !important;
    color: #a0c8ff !important;
    border: 1px solid #2a4068 !important;
    font-family: 'Apple Color Emoji', 'Segoe UI Emoji', 'Noto Color Emoji', emoji, 'Cinzel', Georgia, serif !important;
}

.stFileUploader {
    border: 1px dashed #2a3050 !important;
    background-color: #060a12 !important;
}

hr {
    border-color: #1a2035 !important;
    opacity: 0.7;
}

/* Floating bats */
@keyframes flyBats {
    0% { transform: translateY(0px) translateX(0px) rotate(0deg); opacity: 0; }
    15% { opacity: 1; }
    85% { opacity: 1; }
    100% { transform: translateY(-420px) translateX(160px) rotate(25deg); opacity: 0; }
}
.bat-container {
    position: relative;
    height: 130px;
    width: 100%;
    overflow: hidden;
    margin-bottom: 12px;
}
.floating-bat {
    position: absolute;
    bottom: 0px;
    font-size: 26px;
    animation: flyBats 3.2s ease-in-out infinite;
    filter: drop-shadow(0 0 4px rgba(100, 60, 180, 0.5));
}
.bat1 { left: 8%; animation-delay: 0s; }
.bat2 { left: 32%; animation-delay: 0.55s; }
.bat3 { left: 58%; animation-delay: 0.25s; }
.bat4 { left: 82%; animation-delay: 0.85s; }

::-webkit-scrollbar { width: 8px; height: 8px; }
::-webkit-scrollbar-track { background: #030508; }
::-webkit-scrollbar-thumb { background: #1a2540; border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: #2a4068; }

div[data-testid="stNotification"] {
    border-left: 3px solid #6a2030 !important;
}
</style>
""",
    unsafe_allow_html=True,
)

# ==========================================
# FRAGRANCE DATABASE (Stored in Session State)
# ==========================================
_persisted = load_persisted_data()

if "fragrances_db" not in st.session_state:
    if _persisted.get("fragrances_db"):
        st.session_state["fragrances_db"] = _persisted["fragrances_db"]
    else:
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
                "name": "Al Rehab Soft",
                "brand": "Al Rehab",
                "gender": "Unisex (leans feminine)",
                "season": "Fall, Winter",
                "notes": "Top - Citruses / Heart - Orchid, Jasmine, Vanilla, Caramel / Base - White Musk, Woody Notes, Vetiver",
                "category": ["Floral", "Sweet", "Gourmand"],
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
                "name": "Lattafa Khamrah Original",
                "brand": "Lattafa",
                "gender": "Unisex",
                "season": "Fall, Winter",
                "notes": "Top - Cinnamon, Nutmeg, Bergamot / Heart - Dates, Praline, Tuberose / Base - Vanilla, Tonka Bean, Amberwood",
                "category": ["Oriental", "Spicy", "Sweet"],
            },
            {
                "name": "Lattafa Nebras",
                "brand": "Lattafa",
                "gender": "Unisex",
                "season": "Fall, Winter",
                "notes": "Top - Red Berries, Mandarin Orange / Heart - Vanilla, Cacao, Rose / Base - Sugar, Tonka Bean, Amber, Musk",
                "category": ["Gourmand", "Fruity", "Sweet"],
            },
        ]

if "user_reactions" not in st.session_state:
    st.session_state["user_reactions"] = _persisted.get("user_reactions", {})

if "sotd_history" not in st.session_state:
    st.session_state["sotd_history"] = _persisted.get("sotd_history", [])

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
def normalize_gender(g: str) -> str:
    g = g.lower().strip()
    if re.search(r"\bfemale[- ]?leaning\b|\bleans feminine\b|\bleans female\b", g):
        return "Female-leaning"
    if re.search(r"\bmale[- ]?leaning\b|\bleans masculine\b|\bleans male\b", g):
        return "Male-leaning"
    if g in ["unisex/male", "male/unisex", "male / unisex"]:
        return "Male-leaning"
    if g in [
        "unisex/female",
        "female/unisex",
        "women/unisex",
        "unisex / female-leaning",
    ]:
        return "Female-leaning"
    if g == "male":
        return "Male"
    if g in ["female", "women"]:
        return "Female"
    return "Unisex"


def matches_gender(fragrance: dict, preferred: str) -> bool:
    if preferred == "Any":
        return True
    fg = normalize_gender(fragrance["gender"])
    if preferred == "Male":
        return fg in ["Male", "Male-leaning"]
    if preferred == "Female":
        return fg in ["Female", "Female-leaning"]
    if preferred == "Unisex":
        return fg in ["Unisex", "Male-leaning", "Female-leaning"]
    return True


def matches_weather(fragrance: dict, weather: str) -> bool:
    season = fragrance["season"].lower()
    if weather == "Any":
        return True

    is_summer_target = "summer" in weather.lower() or "hot" in weather.lower()
    is_winter_target = "winter" in weather.lower() or "cold" in weather.lower()

    if is_summer_target:
        if (
            ("winter" in season or "fall" in season or "autumn" in season)
            and "summer" not in season
            and "spring" not in season
            and "versatile" not in season
            and "year-round" not in season
        ):
            return False
        return (
            "summer" in season
            or "spring" in season
            or "versatile" in season
            or "year-round" in season
            or "mild" in season
        )

    if is_winter_target:
        if (
            ("summer" in season or "spring" in season)
            and "winter" not in season
            and "fall" not in season
            and "autumn" not in season
            and "cooler" not in season
            and "versatile" not in season
            and "year-round" not in season
        ):
            return False
        return (
            "winter" in season
            or "fall" in season
            or "autumn" in season
            or "cooler" in season
            or "versatile" in season
            or "year-round" in season
        )
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
    h = hashlib.md5(name.encode("utf-8")).hexdigest()
    return int(h[:4], 16) % 4


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
        if g in ["Male", "Male-leaning"]:
            score += 15
    elif gender == "Female":
        if g in ["Female", "Female-leaning"]:
            score += 15

    if category == "Any":
        score += 5
    elif category in cats:
        score += 15

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


GOOD_LAYER_PAIRS = [
    ("Gourmand", "Fresh"),
    ("Gourmand", "Floral"),
    ("Gourmand", "Woody"),
    ("Gourmand", "Fruity"),
    ("Sweet", "Fresh"),
    ("Floral", "Woody"),
    ("Oriental", "Floral"),
    ("Spicy", "Sweet"),
]


def layer_score(f1: dict, f2: dict) -> int:
    if f1["name"] == f2["name"]:
        return -100
    cats1 = set(f1["category"])
    cats2 = set(f2["category"])
    score = 0
    for a, b in GOOD_LAYER_PAIRS:
        if (a in cats1 and b in cats2) or (b in cats1 and a in cats2):
            score += 15
    return score


def suggest_layering_combos(pool: list, num_combos: int = 3) -> list:
    source_pool = pool if len(pool) >= 5 else st.session_state["fragrances_db"]
    if len(source_pool) < 2:
        return []

    candidates = []
    for i, f1 in enumerate(source_pool):
        for f2 in source_pool[i + 1 :]:
            s = layer_score(f1, f2)
            reason = f"Combines {', '.join(f1['category'])} with {', '.join(f2['category'])} notes."
            candidates.append((s, f1, f2, reason))

    candidates.sort(key=lambda x: x[0], reverse=True)
    return [(f1, f2, r) for _, f1, f2, r in candidates[:num_combos]]


def render_fragrance_card(f: dict, key_prefix: str, show_actions: bool = True):
    current_reaction = st.session_state["user_reactions"].get(f["name"])
    status_badge = (
        " 🖤 Favorite"
        if current_reaction == "fav"
        else (" 🚫 Disliked" if current_reaction == "dislike" else "")
    )

    st.info(f"**{f['name']}** by *{f['brand']}*{status_badge}")
    st.write(f"**Gender:** {f['gender']}  |  **Season:** {f['season']}")
    st.write(f"**Category:** {', '.join(f['category'])}")
    st.caption(f"Notes: {f['notes']}")

    if show_actions:
        col1, col2, _ = st.columns([1, 1, 4])
        with col1:
            if st.button("Love", key=f"{key_prefix}_fav_{f['name']}"):
                st.session_state["user_reactions"][f["name"]] = "fav"
                save_persisted_data()
                st.rerun()
        with col2:
            if st.button("Trash", key=f"{key_prefix}_dislike_{f['name']}"):
                st.session_state["user_reactions"][f["name"]] = "dislike"
                save_persisted_data()
                st.rerun()
    st.markdown("---")


def get_wear_counts() -> dict:
    counts = {}
    for entry in st.session_state.get("sotd_history", []):
        scents = entry.get("scents") or []
        for s in scents:
            counts[s] = counts.get(s, 0) + 1
    return counts


# ==========================================
# STREAMLIT USER INTERFACE
# ==========================================
st.title("ScentedDeadGirl Sanctuary")
st.caption("A gothic-toned fragrance vault & recommendation engine")

st.markdown(
    """
    *Enter the crypt of scent...*  
    Filter your vault, cherish or banish bottles, log your Scent of the Day,  
    and weave forbidden layering combinations under the watch of the bats.
    """
)

# Sidebar Search & Filters
st.sidebar.header("Search Your Collection")
search_query = st.sidebar.text_input(
    "Type name or brand...",
    value=st.session_state["search_input"],
    placeholder="e.g. Lattafa, Eclaire",
    label_visibility="collapsed",
)
st.session_state["search_input"] = search_query

st.sidebar.markdown("---")
st.sidebar.header("Filter Options")
gender = st.sidebar.selectbox("Gender Preference", ["Any", "Male", "Female", "Unisex"])
weather = st.sidebar.selectbox("Weather / Season", ["Any", "Hot / Summer", "Warm / Mild", "Cool / Autumn", "Cold / Winter"])
category = st.sidebar.selectbox("Preferred Category", ["Any", "Gourmand", "Floral", "Woody", "Oriental", "Fresh", "Fruity", "Spicy"])
occasion = st.sidebar.selectbox("Occasion", ["Any", "Daily / Casual", "Work / Office", "Date / Evening", "Formal / Event"])
num_recs = st.sidebar.radio("Number of Recommendations", [1, 3, 5], index=1)
favorites_only = st.sidebar.checkbox("Favorites only", value=False)

if search_query:
    st.markdown("---")
    st.subheader(f"Search Results for: '{search_query}'")
    query_lower = search_query.lower()
    matching = [f for f in st.session_state["fragrances_db"] if query_lower in f["name"].lower() or query_lower in f["brand"].lower()]
    for f in matching:
        render_fragrance_card(f, key_prefix=f"search_{search_query}")

if st.sidebar.button("Generate Recommendations", type="primary"):
    selected = get_top_fragrances(gender, weather, category, occasion, num_recs, favorites_only=favorites_only)
    st.markdown("---")
    st.subheader(f"Top {num_recs} Recommendation(s)")
    for i, f in enumerate(selected, 1):
        render_fragrance_card(f, key_prefix=f"rec_{i}")

# ==========================================
# FRAGRANCE ROULETTE
# ==========================================
st.markdown("---")
st.subheader("Fragrance Roulette")
if st.button("Spin the Roulette", type="primary", key="spin_roulette_btn"):
    pool = st.session_state["fragrances_db"]
    if pool:
        st.session_state["last_roulette"] = random.choice(pool)

if "last_roulette" in st.session_state and st.session_state["last_roulette"]:
    chosen = st.session_state["last_roulette"]
    st.markdown(
        """
        <div class="bat-container">
            <span class="floating-bat bat1">🦇</span>
            <span class="floating-bat bat2">🦇</span>
            <span class="floating-bat bat3">🦇</span>
            <span class="floating-bat bat4">🦇</span>
        </div>
    """,
        unsafe_allow_html=True,
    )
    st.success("### The roulette has spoken...")
    render_fragrance_card(chosen, key_prefix="roulette")

# ==========================================
# SCENT OF THE DAY (SOTD) LOGGER
# ==========================================
st.markdown("---")
st.subheader("Scent of the Day (SOTD)")

all_names = [f["name"] for f in st.session_state["fragrances_db"]]
col_sotd1, col_sotd2 = st.columns([3, 1])
with col_sotd1:
    chosen_sotd = st.multiselect("What are you wearing today?", all_names, default=st.session_state["sotd_prefill"])
with col_sotd2:
    st.write("")
    st.write("")
    if st.button("Log SOTD", type="primary"):
        if chosen_sotd:
            entry = {
                "date": datetime.date.today().strftime("%Y-%m-%d"),
                "scents": chosen_sotd
            }
            st.session_state["sotd_history"].insert(0, entry)
            save_persisted_data()
            st.success(f"Logged SOTD: {', '.join(chosen_sotd)}")
            st.session_state["sotd_prefill"] = []
        else:
            st.warning("Please pick at least one fragrance to log.")

if st.session_state["sotd_history"]:
    with st.expander("View SOTD History & Stats"):
        wear_counts = get_wear_counts()
        if wear_counts:
            sorted_wears = sorted(wear_counts.items(), key=lambda x: x[1], reverse=True)
            st.write("**Most Worn Bottles:**")
            for name, count in sorted_wears[:5]:
                st.write(f"- {name}: {count} wear(s)")
            st.markdown("---")
        st.write("**Recent Logs:**")
        for entry in st.session_state["sotd_history"][:10]:
            st.caption(f"{entry['date']} — {', '.join(entry['scents'])}")

# ==========================================
# LAYERIGN SANCTUARY
# ==========================================
st.markdown("---")
st.subheader("Forbidden Layering Lab")
st.write("Generate custom pairing combinations from your collection.")
if st.button("Suggest Layering Combos", type="primary"):
    combos = suggest_layering_combos(st.session_state["fragrances_db"], num_combos=3)
    if combos:
        for i, (f1, f2, reason) in enumerate(combos, 1):
            st.info(f"**Combo {i}: {f1['name']}** + **{f2['name']}**")
            st.write(f"- {f1['name']} ({', '.join(f1['category'])})")
            st.write(f"- {f2['name']} ({', '.join(f2['category'])})")
            st.caption(reason)
            st.markdown("---")
    else:
        st.warning("Not enough fragrances in the vault to generate layering combos yet!")

# ==========================================
# NOTE & BRAND QUICK LOOKUP
# ==========================================
st.markdown("---")
st.subheader("Note & Brand Quick Lookup")
quick_input = st.text_input("Search specific notes (e.g., vanilla, caramel, oud, rose)...", key="quick_lookup_input")
if quick_input:
    q_low = quick_input.lower()
    matches = [
        f for f in st.session_state["fragrances_db"]
        if q_low in f["notes"].lower() or q_low in f["brand"].lower() or q_low in f["name"].lower()
        or any(q_low in c.lower() for c in f["category"])
    ]
    if matches:
        st.write(f"Found {len(matches)} matching bottle(s):")
        for f in matches:
            render_fragrance_card(f, key_prefix=f"quick_{quick_input}")
    else:
        st.info("No matching notes or brands found in your vault.")

# ==========================================
# COLLECTION BROWSER & VAULT MANAGEMENT
# ==========================================
st.markdown("---")
st.subheader("Collection Browser & Vault Management")
col_m1, col_m2, col_m3 = st.columns(3)
with col_m1:
    st.metric("Total Bottles", len(st.session_state["fragrances_db"]))
with col_m2:
    st.metric("Favorites", len([s for s in st.session_state["user_reactions"].values() if s == "fav"]))
with col_m3:
    st.metric("Banished", len([s for s in st.session_state["user_reactions"].values() if s == "dislike"]))

with st.expander("Add New Bottle to Vault"):
    with st.form("add_bottle_form"):
        new_name = st.text_input("Fragrance Name", key="add_name")
        new_brand = st.text_input("Brand / House", key="add_brand")
        new_gender = st.selectbox("Gender", ["Unisex", "Female", "Female-leaning", "Male", "Male-leaning"])
        new_season = st.text_input("Season / Weather", value="Fall, Winter", key="add_season")
        new_notes = st.text_area("Notes Breakdown", key="add_notes")
        new_cats = st.multiselect("Categories", ["Gourmand", "Floral", "Woody", "Oriental", "Fresh", "Fruity", "Spicy", "Sweet", "Oud", "Leather"])
        
        if st.form_submit_button("Summon Bottle"):
            if new_name and new_brand:
                new_item = {
                    "name": new_name,
                    "brand": new_brand,
                    "gender": new_gender,
                    "season": new_season,
                    "notes": new_notes if new_notes else "Not specified",
                    "category": new_cats if new_cats else ["Uncategorized"]
                }
                st.session_state["fragrances_db"].append(new_item)
                save_persisted_data()
                st.success(f"Successfully added '{new_name}' to your vault!")
                st.rerun()
            else:
                st.error("Please provide at least a name and brand.")

with st.expander("Edit or Banish Existing Bottle"):
    manage_names = sorted([f["name"] for f in st.session_state["fragrances_db"]])
    selected_manage = st.selectbox("Choose a bottle to manage...", ["- select -"] + manage_names)

    if selected_manage != "- select -":
        idx = next((i for i, f in enumerate(st.session_state["fragrances_db"]) if f["name"] == selected_manage), None)
        if idx is not None:
            frag = st.session_state["fragrances_db"][idx]
            with st.form(key=f"edit_form_{selected_manage}"):
                e_name = st.text_input("Name", value=frag["name"])
                e_brand = st.text_input("Brand", value=frag["brand"])
                e_gender = st.selectbox("Gender", ["Unisex", "Female", "Female-leaning", "Male", "Male-leaning"], index=0)
                e_season = st.text_input("Season", value=frag["season"])
                e_notes = st.text_area("Notes", value=frag["notes"])
                
                col_sub1, col_sub2 = st.columns(2)
                with col_sub1:
                    save_btn = st.form_submit_button("Save Changes")
                with col_sub2:
                    delete_btn = st.form_submit_button("Banish Bottle Forever")

                if save_btn:
                    frag["name"] = e_name
                    frag["brand"] = e_brand
                    frag["gender"] = e_gender
                    frag["season"] = e_season
                    frag["notes"] = e_notes
                    save_persisted_data()
                    st.success("Vault updated successfully!")
                    st.rerun()

                if delete_btn:
                    st.session_state["fragrances_db"].pop(idx)
                    if frag["name"] in st.session_state["user_reactions"]:
                        del st.session_state["user_reactions"][frag["name"]]
                    save_persisted_data()
                    st.success(f"Banished '{selected_manage}' from your vault.")
                    st.rerun()

# ==========================================
# EXPORT / IMPORT VAULT DATA
# ==========================================
st.markdown("---")
with st.expander("Backup / Export Sanctuary Data"):
    export_data = {
        "fragrances_db": st.session_state["fragrances_db"],
        "user_reactions": st.session_state["user_reactions"],
        "sotd_history": st.session_state["sotd_history"]
    }
    json_str = json.dumps(export_data, indent=2, ensure_ascii=False)
    st.download_button(
        label="Download Sanctuary JSON Backup",
        data=json_str,
        file_name="scented_dead_girl_backup.json",
        mime="application/json"
    )
