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
}

.stApp {
    background: radial-gradient(ellipse at top, #0a101c 0%, #05070c 50%, #020306 100%);
    color: var(--text);
}

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
    color: var(--text) !important;
    font-size: 0.95rem !important;
    line-height: 1.5 !important;
}

.stCaption, [data-testid="stCaptionContainer"] {
    color: var(--text-muted) !important;
    font-size: 0.85rem !important;
}

section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #060912 0%, #0a0f18 55%, #080a10 100%) !important;
    border-right: 1px solid var(--border);
}

.stButton > button {
    background: linear-gradient(180deg, #121c30 0%, #0a1220 100%) !important;
    color: var(--accent) !important;
    border: 1px solid var(--border) !important;
    border-radius: 6px !important;
    font-weight: 600 !important;
    font-size: 0.9rem !important;
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

.stTextInput > div > div > input,
.stSelectbox > div > div > select,
.stMultiSelect > div > div,
.stTextArea > div > div > textarea,
div[data-baseweb="select"] > div {
    background-color: var(--bg-card) !important;
    color: var(--text) !important;
    border: 1px solid var(--border) !important;
    border-radius: 6px !important;
}

.stTabs [data-baseweb="tab-list"] {
    gap: 0.25rem;
    border-bottom: 1px solid var(--border);
    background: transparent;
}
.stTabs [data-baseweb="tab"] {
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
</style>
""",
    unsafe_allow_html=True,
)

# ==========================================
# FRAGRANCE DATABASE & STATE SETUP
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
                "name": "Al Rehab Chocomusk",
                "brand": "Al Rehab",
                "gender": "Unisex",
                "season": "Fall, Winter",
                "notes": "Top - Warm Spicy, Amber / Heart - Sweet, Powdery, Vanilla / Base - Chocolate, Musky, Cocoa",
                "category": ["Gourmand", "Sweet"],
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
            }
        ]

if "user_reactions" not in st.session_state:
    st.session_state["user_reactions"] = _persisted.get("user_reactions", {})

if "sotd_history" not in st.session_state:
    st.session_state["sotd_history"] = _persisted.get("sotd_history", [])

if "layer_recipes" not in st.session_state:
    st.session_state["layer_recipes"] = _persisted.get("layer_recipes", [])

if "play_stats" not in st.session_state:
    st.session_state["play_stats"] = _persisted.get(
        "play_stats", {"blind_played": 0, "blind_correct": 0, "moods_drawn": 0}
    )

# ==========================================
# HELPER FUNCTIONS
# ==========================================
def pacific_today() -> datetime.date:
    return datetime.datetime.now(ZoneInfo("America/Los_Angeles")).date()

def normalize_gender(g: str) -> str:
    g = g.lower().strip()
    if "female" in g:
        return "Female-leaning" if "lean" in g or "unisex" in g else "Female"
    if "male" in g:
        return "Male-leaning" if "lean" in g or "unisex" in g else "Male"
    return "Unisex"

def matches_gender(fragrance: dict, preferred: str) -> bool:
    if preferred == "Any":
        return True
    fg = normalize_gender(fragrance["gender"])
    if preferred == "Male":
        return fg in ["Male", "Male-leaning"]
    if preferred == "Female":
        return fg in ["Female", "Female-leaning"]
    return fg in ["Unisex", "Male-leaning", "Female-leaning"]

def matches_weather(fragrance: dict, weather: str) -> bool:
    if weather == "Any":
        return True
    season_str = fragrance["season"].lower()
    weather_lower = weather.lower()
    
    if "hot" in weather_lower or "summer" in weather_lower:
        return any(s in season_str for s in ["summer", "spring", "hot", "versatile", "any"])
    if "cold" in weather_lower or "winter" in weather_lower:
        return any(s in season_str for s in ["winter", "fall", "autumn", "cold", "versatile", "any"])
    if "cool" in weather_lower or "autumn" in weather_lower:
        return any(s in season_str for s in ["fall", "autumn", "cool", "versatile", "any"])
    return True

def matches_category(fragrance: dict, category: str) -> bool:
    if category == "Any":
        return True
    return category in fragrance["category"]

def matches_occasion(fragrance: dict, occasion: str) -> bool:
    if occasion == "Any":
        return True
    return True

def score_fragrance(f: dict, gender: str, weather: str, category: str, occasion: str) -> int:
    score = 10
    if st.session_state["user_reactions"].get(f["name"]) == "fav":
        score += 30
    return score

def get_top_fragrances(gender, weather, category, occasion, top_n, favorites_only=False):
    scored = []
    for f in st.session_state["fragrances_db"]:
        if st.session_state["user_reactions"].get(f["name"]) == "dislike":
            continue
        if favorites_only and st.session_state["user_reactions"].get(f["name"]) != "fav":
            continue
        if matches_gender(f, gender) and matches_weather(f, weather) and matches_category(f, category):
            scored.append((score_fragrance(f, gender, weather, category, occasion), f))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [f for _, f in scored[:top_n]]

def sotd_streak() -> int:
    hist = st.session_state.get("sotd_history") or []
    return len(set(e.get("date") for e in hist if e.get("date")))

def render_fragrance_card(f: dict, key_prefix: str, show_actions: bool = True):
    current_reaction = st.session_state["user_reactions"].get(f["name"])
    status_badge = " [YAY]" if current_reaction == "fav" else (" [NAH]" if current_reaction == "dislike" else "")
    
    st.info(f"**{f['name']}** by *{f['brand']}*{status_badge}")
    st.write(f"**Gender:** {f['gender']}  |  **Season:** {f['season']}")
    st.write(f"**Category:** {', '.join(f['category'])}")
    st.caption(f"Notes: {f['notes']}")

    if show_actions:
        col1, col2, _ = st.columns([1, 1, 4])
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

# ==========================================
# STREAMLIT USER INTERFACE
# ==========================================
st.title("ScentedDeadGirl")
st.caption("Fragrance sanctuary  |  recommend  |  layer  |  log  |  curate")

# ---------- SIDEBAR ----------
with st.sidebar:
    st.markdown("### Recommend Filters")
    gender = st.selectbox("Gender", ["Any", "Male", "Female", "Unisex"], key="filter_gender")
    weather = st.selectbox("Season / Weather", ["Any", "Hot / Summer", "Warm / Mild", "Cool / Autumn", "Cold / Winter"], key="filter_weather")
    category = st.selectbox(
        "Category",
        ["Any", "Gourmand", "Floral", "Woody", "Oriental", "Fruity", "Fresh", "Sweet", "Spicy", "Oud", "Citrus", "Aromatic", "Leather", "Powdery"],
        key="filter_category",
    )
    occasion = st.selectbox(
        "Occasion",
        ["Any", "Daily / Casual", "Work / Office", "Date / Evening", "Formal / Event", "Outdoor / Sporty"],
        key="filter_occasion",
    )
    num_recs = st.slider("Number of recommendations", 1, 10, 3, key="filter_num_recs")
    favorites_only = st.checkbox("Only from my YAYs / favorites", key="filter_favorites_only")

    if st.button("Recommend", type="primary", use_container_width=True):
        st.session_state["last_recs"] = get_top_fragrances(gender, weather, category, occasion, num_recs, favorites_only)

    st.markdown("---")
    st.markdown("### Sanctuary Stats")
    st.metric("Total Bottles", len(st.session_state["fragrances_db"]))
    fav_count = sum(1 for v in st.session_state["user_reactions"].values() if v == "fav")
    st.metric("YAYs / Favorites", fav_count)
    st.metric("SOTD Wears Logged", len(st.session_state["sotd_history"]))

# ---------- MAIN TABS ----------
tab_recs, tab_log, tab_layer, tab_oracle, tab_collection = st.tabs(
    ["Recommend", "SOTD Log", "Layering", "Oracle & Stats", "Collection & Add"]
)

with tab_recs:
    st.subheader("Sanctuary Recommendations")
    recs = st.session_state.get("last_recs")
    if recs is None:
        recs = get_top_fragrances(gender, weather, category, occasion, 3, favorites_only)
        st.session_state["last_recs"] = recs

    if recs:
        for f in recs:
            render_fragrance_card(f, key_prefix="main_recs")
    else:
        st.info("No fragrances match your filter combination.")

with tab_log:
    st.subheader("Scent of the Day (SOTD) Log")
    with st.form("sotd_form"):
        log_date = st.date_input("Date", value=pacific_today())
        db_names = [f["name"] for f in st.session_state["fragrances_db"]]
        selected_bottles = st.multiselect("Select bottle(s) worn", options=db_names)
        mood_tag = st.selectbox("Current mood / vibe", ["Any", "Cozy", "Fierce", "Soft", "Date night", "Focus / work"])
        log_notes = st.text_area("Notes / thoughts", placeholder="How did it perform today?")
        
        if st.form_submit_button("Save SOTD Entry", type="primary"):
            if selected_bottles:
                entry = {
                    "date": log_date.isoformat(),
                    "scents": selected_bottles,
                    "scent": " + ".join(selected_bottles),
                    "mood": mood_tag,
                    "notes": log_notes,
                }
                st.session_state["sotd_history"].append(entry)
                save_persisted_data()
                st.success(f"Saved SOTD for {log_date.isoformat()}!")
                st.rerun()

with tab_layer:
    st.subheader("Layering Laboratory")
    st.write("Experiment with custom scent combinations.")
    
    db_names = [f["name"] for f in st.session_state["fragrances_db"]]
    if len(db_names) >= 2:
        layer_base = st.selectbox("Base Layer (Foundation)", options=db_names, key="layer_base")
        layer_top = st.selectbox("Top Layer (Accent)", options=db_names, key="layer_top", index=min(1, len(db_names)-1))
        
        layer_notes = st.text_area("Why does this work? (Your combo notes)", placeholder="e.g., Adds a sweet vanilla depth to a woody scent.")
        
        if st.button("Save Layering Combo", type="primary"):
            recipe = {"base": layer_base, "top": layer_top, "notes": layer_notes}
            st.session_state["layer_recipes"].append(recipe)
            save_persisted_data()
            st.success(f"Saved combo: {layer_base} + {layer_top}!")
            
        if st.session_state["layer_recipes"]:
            st.markdown("### Saved Layering Recipes")
            for idx, rec in enumerate(st.session_state["layer_recipes"]):
                st.write(f"{idx+1}. **{rec['base']}** + **{rec['top']}**")
                if rec['notes']:
                    st.caption(f"Notes: {rec['notes']}")
    else:
        st.info("Add at least two fragrances to your collection to use the Layering Lab.")

with tab_oracle:
    st.subheader("Fragrance Oracle")
    st.write("Let the sanctuary choose your scent of the day based on your current vibe.")
    
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("Draw a Random Scent", use_container_width=True):
            available = [f for f in st.session_state["fragrances_db"] if st.session_state["user_reactions"].get(f["name"]) != "dislike"]
            if available:
                chosen = random.choice(available)
                st.session_state["oracle_pick"] = chosen
            else:
                st.warning("No fragrances available.")
                
    with col_b:
        streak = sotd_streak()
        st.metric("SOTD Streak (Days Logged)", streak)
        
    if "oracle_pick" in st.session_state:
        pick = st.session_state["oracle_pick"]
        st.markdown("#### The Oracle Has Spoken:")
        render_fragrance_card(pick, key_prefix="oracle_pick_card")

with tab_collection:
    st.subheader("Collection & Sanctuary Additions")
    with st.expander("Add New Bottle", expanded=True):
        with st.form("add_bottle_form"):
            aname = st.text_input("Fragrance Name")
            abrand = st.text_input("Brand / House")
            agender = st.selectbox("Gender / Lean", ["Unisex", "Female", "Female-leaning", "Male", "Male-leaning"])
            aseason = st.selectbox("Season", ["Versatile (All year)", "Fall, Winter", "Spring, Summer", "Hot / Summer", "Cool / Autumn"])
            acat = st.multiselect("Categories", ["Gourmand", "Floral", "Woody", "Oriental", "Fruity", "Fresh", "Sweet", "Spicy", "Oud", "Citrus"])
            anotes = st.text_area("Notes Description", placeholder="e.g., Top: Vanilla / Heart: Caramel / Base: Musk")
            
            if st.form_submit_button("Add to Database", type="primary"):
                if aname and abrand:
                    new_entry = {
                        "name": aname,
                        "brand": abrand,
                        "gender": agender,
                        "season": aseason,
                        "notes": anotes if anotes else "Custom added",
                        "category": acat if acat else ["Gourmand"]
                    }
                    st.session_state["fragrances_db"].append(new_entry)
                    save_persisted_data()
                    st.success(f"Added {aname} by {abrand} to your sanctuary!")
                    st.rerun()
                else:
                    st.error("Please provide at least a name and a brand.")
