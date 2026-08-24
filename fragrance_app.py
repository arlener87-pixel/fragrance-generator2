# ============================================================
# ScentedDeadGirl Fragrance Sanctuary  –  Full Rebuild
# New logo integrated | Original features preserved
# ============================================================

import datetime
from zoneinfo import ZoneInfo
import hashlib
import json
import random
from pathlib import Path

import streamlit as st

# ==========================================
# PATHS & PERSISTENCE
# ==========================================
DATA_FILE = Path(__file__).parent / "scented_dead_girl_data.json"
DATA_BAK  = Path(__file__).parent / "scented_dead_girl_data.bak.json"
DATA_TMP  = Path("/tmp") / "scented_dead_girl_data.json"
LOGO_PATH = Path(__file__).parent / "logo.jpg"


def _safe_json_load(path: Path) -> dict:
    try:
        if not path or not Path(path).exists():
            return {}
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _vault_count(data: dict) -> int:
    db = (data or {}).get("fragrances_db") or []
    return len(db) if isinstance(db, list) else 0


def load_persisted_data():
    candidates = []
    for p in (DATA_FILE, DATA_BAK, DATA_TMP):
        data = _safe_json_load(p)
        if data and _vault_count(data) > 0:
            candidates.append((_vault_count(data), str(p), data))
    if not candidates:
        data = _safe_json_load(DATA_FILE)
        return data if data else {}
    candidates.sort(key=lambda x: x[0], reverse=True)
    return candidates[0][2]


def save_persisted_data(force: bool = False):
    now = datetime.datetime.now(ZoneInfo("America/Los_Angeles")).isoformat(timespec="seconds")
    st.session_state["last_saved_at"] = now
    session_db = st.session_state.get("fragrances_db") or []
    if not isinstance(session_db, list):
        session_db = []
    session_n = len(session_db)

    data = {
        "fragrances_db": session_db,
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
        "bottle_count": session_n,
    }

    # Guard against accidental wipe
    if not force and session_n > 0:
        on_disk = load_persisted_data()
        disk_n = _vault_count(on_disk)
        if disk_n >= 10 and session_n < max(5, int(disk_n * 0.85)):
            st.session_state["_save_blocked"] = (
                f"Save blocked: session has **{session_n}** bottles but disk has **{disk_n}**. "
                f"Export JSON from Vault, or use Restore."
            )
            if on_disk.get("fragrances_db"):
                st.session_state["fragrances_db"] = on_disk["fragrances_db"]
                if on_disk.get("user_reactions") is not None:
                    st.session_state["user_reactions"] = on_disk.get("user_reactions") or {}
            return False
    elif not force and session_n == 0:
        on_disk = load_persisted_data()
        if _vault_count(on_disk) > 0:
            st.session_state["_save_blocked"] = "Save blocked: session vault is empty but disk has bottles."
            st.session_state["fragrances_db"] = on_disk.get("fragrances_db") or []
            return False

    payload = json.dumps(data, indent=2, ensure_ascii=False)
    ok = False
    for target in (DATA_FILE, DATA_TMP):
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            tmp = target.with_suffix(target.suffix + ".tmp")
            with open(tmp, "w", encoding="utf-8") as f:
                f.write(payload)
                f.flush()
            tmp.replace(target)
            ok = True
        except Exception:
            pass

    try:
        if DATA_FILE.exists() and DATA_FILE.stat().st_size > 50:
            import shutil
            shutil.copy2(DATA_FILE, DATA_BAK)
    except Exception:
        pass

    if ok:
        st.session_state.pop("_save_blocked", None)
        st.session_state.pop("_save_error", None)
        st.session_state["_last_disk_count"] = session_n
        st.session_state["_vault_fp"] = vault_fingerprint()
    return ok


def vault_fingerprint() -> str:
    payload = {
        "fragrances_db": st.session_state.get("fragrances_db"),
        "user_reactions": st.session_state.get("user_reactions"),
        "sotd_history": st.session_state.get("sotd_history"),
        "layer_recipes": st.session_state.get("layer_recipes"),
        "play_stats": st.session_state.get("play_stats"),
        "wishlist": st.session_state.get("wishlist"),
        "vault_log": st.session_state.get("vault_log"),
        "chart": {
            "sun": st.session_state.get("chart_sun"),
            "moon": st.session_state.get("chart_moon"),
            "rising": st.session_state.get("chart_rising"),
            "venus": st.session_state.get("chart_venus"),
            "full": st.session_state.get("birth_calc_full"),
        },
        "last_export_date": st.session_state.get("last_export_date"),
    }
    try:
        raw = json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str)
    except Exception:
        raw = str(payload)
    return hashlib.md5(raw.encode("utf-8", errors="replace")).hexdigest()


def mark_vault_dirty():
    st.session_state["_vault_dirty"] = True


def autosave_if_changed(force: bool = False) -> bool:
    try:
        current = vault_fingerprint()
    except Exception:
        current = ""
    start = st.session_state.get("_vault_fp_run_start")
    dirty = bool(st.session_state.get("_vault_dirty"))
    if force or dirty or (start and current and current != start):
        ok = save_persisted_data(force=force)
        st.session_state["_vault_dirty"] = False
        if ok:
            st.session_state["_vault_fp_run_start"] = vault_fingerprint()
            st.session_state["_autosaved_at"] = st.session_state.get("last_saved_at")
        return bool(ok)
    return False


def log_vault_action(action: str, name: str, detail: str = ""):
    entry = {
        "when": datetime.datetime.now(ZoneInfo("America/Los_Angeles")).strftime("%Y-%m-%d %H:%M"),
        "action": action,
        "name": name,
        "detail": detail,
    }
    log = st.session_state.get("vault_log") or []
    log.insert(0, entry)
    st.session_state["vault_log"] = log[:100]
    mark_vault_dirty()


def pacific_today():
    return datetime.datetime.now(ZoneInfo("America/Los_Angeles")).date()


# ==========================================
# PAGE CONFIG + THEME
# ==========================================
st.set_page_config(
    page_title="ScentedDeadGirl Fragrance Sanctuary",
    page_icon="logo.jpg" if LOGO_PATH.exists() else "🌙",
    layout="centered",
    initial_sidebar_state="expanded",
)

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
}

html, body, .stApp, [class*="css"], .stMarkdown, p, span, div, label {
    font-family: 'Inter', system-ui, sans-serif !important;
}

.stApp {
    background: radial-gradient(ellipse at top, #0a1224 0%, #04070f 45%, #010205 100%);
    color: var(--text);
}

.block-container {
    padding-top: 1.1rem !important;
    padding-bottom: 2.5rem !important;
    max-width: 860px !important;
}

h1, h2, h3, h4 {
    font-family: 'Cinzel', Georgia, serif !important;
    color: var(--accent) !important;
    letter-spacing: 0.03em !important;
}

section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #040810 0%, #070c16 55%, #03050a 100%) !important;
    border-right: 1px solid var(--border);
}

.stButton > button {
    background: linear-gradient(180deg, #121c30 0%, #0a1220 100%) !important;
    color: var(--accent) !important;
    border: 1px solid var(--border) !important;
    border-radius: 6px !important;
    font-weight: 600 !important;
}
.stButton > button:hover {
    border-color: var(--border-hover) !important;
    color: #e8f0ff !important;
}
.stButton > button[kind="primary"] {
    background: linear-gradient(180deg, #1a3060 0%, #122448 100%) !important;
    border-color: var(--accent-dim) !important;
}

.sdg-card {
    background: linear-gradient(180deg, #101826 0%, #0b101a 100%);
    border: 1px solid #1e2a42;
    border-radius: 12px;
    padding: 0.9rem 1.1rem;
    margin: 0.5rem 0 0.9rem 0;
}

.sdg-divider {
    height: 1px;
    background: linear-gradient(90deg, transparent, #2a3c5c, transparent);
    margin: 1rem 0;
    border: 0;
}

.logo-wrap {
    text-align: center;
    margin: 0.15rem 0 0.6rem 0;
}
.logo-caption {
    font-family: 'Cinzel', Georgia, serif !important;
    color: #8a9bb8 !important;
    font-size: 0.72rem !important;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    margin-top: 0.35rem;
}

div[data-testid="stMetric"] {
    background: #0b101a;
    border: 1px solid #1e2a42;
    border-radius: 10px;
    padding: 0.5rem 0.65rem;
}

.stTabs [data-baseweb="tab"] {
    font-weight: 600 !important;
    color: var(--text-muted) !important;
}
.stTabs [aria-selected="true"] {
    color: var(--accent) !important;
    border-bottom: 2px solid var(--accent-dim) !important;
}

[data-testid="stExpander"] summary {
    background: var(--bg-elevated) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
}
</style>
""",
    unsafe_allow_html=True,
)

# ==========================================
# SESSION STATE INIT
# ==========================================
_persisted = load_persisted_data()

if "fragrances_db" not in st.session_state:
    if _persisted.get("fragrances_db"):
        st.session_state["fragrances_db"] = list(_persisted["fragrances_db"])
    else:
        # === SEED (starter set – replace/expand with your full 177+ list) ===
        st.session_state["fragrances_db"] = [
            {"name": "8th Wonder", "brand": "French Avenue", "gender": "Unisex", "season": "Fall, Winter",
             "notes": "Top - Cardamom, Pink Pepper, Candy Apple / Heart - Liquor, Dates / Base - Myrrh, Benzoin, Amber",
             "category": ["Oriental", "Spicy", "Sweet"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
            {"name": "Ajwad", "brand": "Lattafa", "gender": "Unisex", "season": "Versatile (cooler preferred)",
             "notes": "Fruity-woody-oriental (pineapple/rose/oud-leaning)",
             "category": ["Oriental", "Woody", "Fruity"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
            {"name": "Asad", "brand": "Lattafa", "gender": "Male", "season": "Fall, Winter",
             "notes": "Top - Black Pepper, Tobacco, Pineapple / Heart - Patchouli, Coffee, Iris / Base - Vanilla, Amber, Woods",
             "category": ["Woody", "Spicy", "Oriental"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
            {"name": "Eclaire", "brand": "Lattafa", "gender": "Female", "season": "Fall, Winter",
             "notes": "Top - Caramel, Milk, Sugar / Heart - Honey, White Flowers / Base - Vanilla, Praline, Musk",
             "category": ["Gourmand", "Sweet"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
            {"name": "Chocomusk", "brand": "Al Rehab", "gender": "Unisex", "season": "Fall, Winter",
             "notes": "Top - Warm Spicy, Amber / Heart - Sweet, Powdery, Vanilla / Base - Chocolate, Musky, Cocoa",
             "category": ["Gourmand", "Sweet"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
            # Add the rest of your bottles here or restore from JSON backup
        ]

if "user_reactions" not in st.session_state:
    st.session_state["user_reactions"] = _persisted.get("user_reactions") or {}
if "sotd_history" not in st.session_state:
    st.session_state["sotd_history"] = _persisted.get("sotd_history") or []
if "layer_recipes" not in st.session_state:
    st.session_state["layer_recipes"] = _persisted.get("layer_recipes") or []
if "play_stats" not in st.session_state:
    st.session_state["play_stats"] = _persisted.get("play_stats") or {}
if "wishlist" not in st.session_state:
    st.session_state["wishlist"] = _persisted.get("wishlist") or []
if "vault_log" not in st.session_state:
    st.session_state["vault_log"] = _persisted.get("vault_log") or []
if "last_export_date" not in st.session_state:
    st.session_state["last_export_date"] = _persisted.get("last_export_date")
if "_vault_fp_run_start" not in st.session_state:
    st.session_state["_vault_fp_run_start"] = vault_fingerprint()

# ==========================================
# HELPERS
# ==========================================
def normalize_gender(g: str) -> str:
    g = (g or "").lower()
    if "female" in g or "women" in g:
        return "Female"
    if "male" in g or "men" in g:
        return "Male"
    return "Unisex"


def matches_gender(frag: dict, filter_g: str) -> bool:
    if filter_g == "Any":
        return True
    return normalize_gender(frag.get("gender", "")) == filter_g


def is_incomplete_notes(frag: dict) -> bool:
    notes = (frag.get("notes") or "").strip()
    return len(notes) < 12 or notes.lower() in ("not specified", "n/a", "")


def profile_gaps(frag: dict) -> list:
    gaps = []
    if is_incomplete_notes(frag):
        gaps.append("notes")
    if not (frag.get("gender") or "").strip():
        gaps.append("gender")
    if not (frag.get("season") or "").strip():
        gaps.append("season")
    if not (frag.get("category") or []):
        gaps.append("category")
    return gaps


def suggest_categories_from_notes(notes: str) -> list:
    notes = (notes or "").lower()
    suggestions = []
    mapping = {
        "Gourmand": ["vanilla", "caramel", "chocolate", "cocoa", "praline", "tonka", "sugar", "cookie", "cake", "cream", "milk", "honey", "almond"],
        "Sweet": ["sweet", "candy", "marshmallow", "cotton candy"],
        "Floral": ["rose", "jasmine", "tuberose", "peony", "lily", "ylang", "orange blossom", "heliotrope"],
        "Woody": ["cedar", "sandalwood", "oak", "wood", "vetiver", "patchouli"],
        "Oriental": ["amber", "myrrh", "benzoin", "oud", "labdanum", "incense"],
        "Fruity": ["apple", "pear", "berry", "peach", "pineapple", "mango", "cherry", "raspberry", "blackcurrant"],
        "Spicy": ["pepper", "cinnamon", "cardamom", "nutmeg", "ginger", "clove"],
        "Fresh": ["citrus", "bergamot", "lemon", "grapefruit", "mint", "aquatic"],
        "Leather": ["leather"],
        "Oud": ["oud", "agarwood"],
        "Boozy": ["cognac", "rum", "whiskey", "liquor", "wine"],
    }
    for cat, keys in mapping.items():
        if any(k in notes for k in keys):
            suggestions.append(cat)
    return suggestions[:6]


SHELF_STATUSES = ["Own", "Decant", "Sample", "Wishlist", "Sold", "Finished"]

# ==========================================
# SIDEBAR
# ==========================================
with st.sidebar:
    if LOGO_PATH.exists():
        st.image(str(LOGO_PATH), use_container_width=True)
    else:
        st.warning("Place **logo.jpg** next to this script.")
    st.markdown("---")
    st.caption("ScentedDeadGirl")
    st.caption("scent is eternal · souls linger")
    st.markdown("---")

    if st.session_state.get("last_saved_at"):
        st.caption(f"Last saved: {st.session_state['last_saved_at']}")
    if st.session_state.get("_save_blocked"):
        st.warning(st.session_state["_save_blocked"])

# ==========================================
# MAIN LOGO HERO
# ==========================================
if LOGO_PATH.exists():
    st.markdown('<div class="logo-wrap">', unsafe_allow_html=True)
    st.image(str(LOGO_PATH), use_container_width=True)
    st.markdown('<p class="logo-caption">Fragrance Sanctuary</p>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
else:
    st.title("ScentedDeadGirl Fragrance Sanctuary")

st.markdown('<hr class="sdg-divider">', unsafe_allow_html=True)

# ==========================================
# TABS
# ==========================================
tab_collection, tab_vault, tab_about = st.tabs(["Collection", "Vault", "About"])

# ---------- COLLECTION ----------
with tab_collection:
    st.subheader("Collection")
    db = st.session_state.get("fragrances_db") or []
    reactions = st.session_state.get("user_reactions") or {}

    colf1, colf2 = st.columns([2, 1])
    with colf1:
        search = st.text_input("Search name / brand / notes", key="col_search")
    with colf2:
        gfilter = st.selectbox("Gender", ["Any", "Female", "Male", "Unisex"], key="col_gender")

    filtered = []
    for f in db:
        if not matches_gender(f, gfilter):
            continue
        q = (search or "").lower().strip()
        if q and not (q in (f.get("name") or "").lower() or q in (f.get("brand") or "").lower() or q in (f.get("notes") or "").lower()):
            continue
        filtered.append(f)

    st.caption(f"{len(filtered)} bottle(s)")

    for i, f in enumerate(filtered):
        name = f.get("name") or "?"
        brand = f.get("brand") or "?"
        rx = reactions.get(name)
        status = "  ★ YAY" if rx == "fav" else ("  ✕ DEL" if rx == "dislike" else "")
        incomplete = "  · needs notes" if is_incomplete_notes(f) else ""

        st.markdown(
            f"**{name}**{status} — *{brand}*{incomplete}  \n"
            f"{f.get('gender','')} · {f.get('season','')} · {', '.join(f.get('category') or [])}  \n"
            f"<small style='opacity:0.75'>{f.get('notes','')}</small>",
            unsafe_allow_html=True,
        )

        b1, b2, _ = st.columns([1, 1, 4])
        with b1:
            if rx == "fav":
                if st.button("Remove YAY", key=f"unfav_{i}_{name}"):
                    st.session_state["user_reactions"].pop(name, None)
                    save_persisted_data()
                    st.rerun()
            else:
                if st.button("YAY", key=f"fav_{i}_{name}"):
                    st.session_state["user_reactions"][name] = "fav"
                    save_persisted_data()
                    st.rerun()
        with b2:
            if rx == "dislike":
                if st.button("Undo DEL", key=f"undel_{i}_{name}"):
                    st.session_state["user_reactions"].pop(name, None)
                    save_persisted_data()
                    st.rerun()
            else:
                if st.button("DEL", key=f"del_{i}_{name}"):
                    st.session_state["user_reactions"][name] = "dislike"
                    save_persisted_data()
                    st.rerun()
        st.markdown("---")

# ---------- VAULT ----------
with tab_vault:
    st.subheader("Sanctuary Vault")
    n_bottles = len(st.session_state.get("fragrances_db") or [])
    st.write(f"**{n_bottles}** bottles in the vault")

    if st.session_state.get("last_saved_at"):
        st.caption(f"Last saved: {st.session_state['last_saved_at']} (Pacific)")

    if st.button("Save vault now", key="force_save"):
        if save_persisted_data(force=True):
            st.success(f"Saved {n_bottles} bottles.")
        else:
            st.error("Save blocked or failed — check sidebar.")

    favs = [n for n, s in (st.session_state.get("user_reactions") or {}).items() if s == "fav"]
    dislikes = [n for n, s in (st.session_state.get("user_reactions") or {}).items() if s == "dislike"]
    c1, c2, c3 = st.columns(3)
    c1.metric("YAY", len(favs))
    c2.metric("DEL", len(dislikes))
    c3.metric("Neutral", max(0, n_bottles - len(favs) - len(dislikes)))

    # --- Find / Edit ---
    with st.expander("Edit a bottle", expanded=False):
        names = sorted(f.get("name") or "" for f in (st.session_state.get("fragrances_db") or []))
        edit_name = st.selectbox("Bottle", ["- select -"] + names, key="edit_select")
        if edit_name != "- select -":
            idx = next((i for i, f in enumerate(st.session_state["fragrances_db"]) if f.get("name") == edit_name), None)
            if idx is not None:
                frag = st.session_state["fragrances_db"][idx]
                with st.form(key=f"edit_form_{edit_name}"):
                    e_name = st.text_input("Name", value=frag.get("name", ""))
                    e_brand = st.text_input("Brand", value=frag.get("brand", ""))
                    gender_opts = ["Unisex", "Female", "Male", "Female-leaning", "Male-leaning"]
                    g_idx = gender_opts.index(frag.get("gender")) if frag.get("gender") in gender_opts else 0
                    e_gender = st.selectbox("Gender", gender_opts, index=g_idx)
                    e_season = st.text_input("Season", value=frag.get("season", ""))
                    e_notes = st.text_area("Notes", value=frag.get("notes", ""), height=100)
                    cat_opts = ["Gourmand", "Sweet", "Floral", "Woody", "Oriental", "Fresh", "Fruity",
                                "Spicy", "Citrus", "Aromatic", "Leather", "Oud", "Boozy", "Smoky", "Powdery"]
                    e_cats = st.multiselect("Categories", cat_opts, default=[c for c in (frag.get("category") or []) if c in cat_opts])
                    if st.form_submit_button("Save changes", type="primary"):
                        st.session_state["fragrances_db"][idx] = {
                            **frag,
                            "name": e_name.strip(),
                            "brand": e_brand.strip(),
                            "gender": e_gender,
                            "season": e_season.strip() or "Versatile",
                            "notes": e_notes.strip() or "Not specified",
                            "category": e_cats or ["Gourmand"],
                        }
                        if e_name != edit_name and edit_name in st.session_state["user_reactions"]:
                            st.session_state["user_reactions"][e_name] = st.session_state["user_reactions"].pop(edit_name)
                        log_vault_action("edited", e_name.strip(), e_brand.strip())
                        save_persisted_data()
                        st.success(f"Updated **{e_name}**")
                        st.rerun()

    # --- Remove ---
    with st.expander("Remove bottles", expanded=False):
        names = sorted(f.get("name") or "" for f in (st.session_state.get("fragrances_db") or []))
        remove_name = st.selectbox("Bottle to remove", ["- select -"] + names, key="remove_select")
        if remove_name != "- select -":
            confirm = st.checkbox(f"Yes, permanently remove {remove_name}", key="rm_confirm")
            if st.button("Banish forever", type="primary", disabled=not confirm, key="rm_btn"):
                st.session_state["fragrances_db"] = [f for f in st.session_state["fragrances_db"] if f.get("name") != remove_name]
                st.session_state["user_reactions"].pop(remove_name, None)
                log_vault_action("removed", remove_name)
                save_persisted_data(force=True)
                st.success(f"Banished **{remove_name}**")
                st.rerun()

    # --- Compare ---
    with st.expander("Compare two bottles", expanded=False):
        names = sorted(f.get("name") or "" for f in (st.session_state.get("fragrances_db") or []) if f.get("name"))
        c1, c2 = st.columns(2)
        with c1:
            left = st.selectbox("Bottle A", ["- select -"] + names, key="cmp_a")
        with c2:
            right = st.selectbox("Bottle B", ["- select -"] + names, key="cmp_b")
        if left != "- select -" and right != "- select -":
            fa = next((f for f in st.session_state["fragrances_db"] if f.get("name") == left), None)
            fb = next((f for f in st.session_state["fragrances_db"] if f.get("name") == right), None)
            if fa and fb:
                def _row(label, va, vb):
                    st.markdown(f"**{label}**")
                    r1, r2 = st.columns(2)
                    with r1: st.write(va or "—")
                    with r2: st.write(vb or "—")
                _row("Brand", fa.get("brand"), fb.get("brand"))
                _row("Gender", fa.get("gender"), fb.get("gender"))
                _row("Season", fa.get("season"), fb.get("season"))
                _row("Families", ", ".join(fa.get("category") or []), ", ".join(fb.get("category") or []))
                st.markdown("**Notes**")
                n1, n2 = st.columns(2)
                with n1: st.write(fa.get("notes") or "—")
                with n2: st.write(fb.get("notes") or "—")

    # --- Family helper ---
    with st.expander("Scent family helper", expanded=False):
        mode = st.radio("Mode", ["Suggest from notes", "Check a bottle", "Audit vault"], horizontal=True, key="fam_mode")
        if mode == "Suggest from notes":
            notes_in = st.text_area("Notes or description", height=90, key="fam_notes")
            if st.button("Suggest families"):
                sug = suggest_categories_from_notes(notes_in)
                if sug:
                    st.success("Suggested: **" + " | ".join(sug) + "**")
                else:
                    st.info("No strong matches.")
        elif mode == "Check a bottle":
            names = sorted(f.get("name") or "" for f in (st.session_state.get("fragrances_db") or []))
            bottle = st.selectbox("Bottle", ["- select -"] + names, key="fam_check")
            if bottle != "- select -":
                frag = next((f for f in st.session_state["fragrances_db"] if f.get("name") == bottle), None)
                if frag:
                    current = frag.get("category") or []
                    st.write("Current: **" + (", ".join(current) if current else "none") + "**")
                    sug = suggest_categories_from_notes(frag.get("notes") or "")
                    if sug:
                        st.write("Suggested: **" + " | ".join(sug) + "**")
                        if st.button("Apply suggested"):
                            merged = list(dict.fromkeys(list(current) + sug))
                            for i, f in enumerate(st.session_state["fragrances_db"]):
                                if f.get("name") == bottle:
                                    st.session_state["fragrances_db"][i]["category"] = merged
                                    break
                            log_vault_action("edited", bottle, "family-helper")
                            save_persisted_data()
                            st.success(f"Updated → {', '.join(merged)}")
                            st.rerun()
        else:  # Audit
            if st.button("Run vault audit", type="primary"):
                issues = []
                for i, f in enumerate(st.session_state.get("fragrances_db") or []):
                    flags = profile_gaps(f)
                    sug = suggest_categories_from_notes(f.get("notes") or "")
                    if flags or (sug and set(sug) - set(f.get("category") or [])):
                        issues.append({"name": f.get("name"), "brand": f.get("brand"), "flags": flags, "suggested": sug})
                st.session_state["_audit"] = issues
            issues = st.session_state.get("_audit") or []
            st.write(f"**{len(issues)}** bottles need attention")
            for item in issues[:30]:
                st.markdown(f"**{item['name']}** — *{item['brand']}*  \nIssues: {', '.join(item['flags']) or 'family'}  \nSuggested: {' | '.join(item['suggested']) or 'n/a'}")

    # --- Activity log ---
    with st.expander("Activity log", expanded=False):
        vlog = st.session_state.get("vault_log") or []
        if not vlog:
            st.caption("No activity yet.")
        else:
            for entry in vlog[:25]:
                detail = f" — {entry.get('detail')}" if entry.get("detail") else ""
                st.write(f"**{entry.get('when')}** | {entry.get('action')} | **{entry.get('name')}**{detail}")
            if st.button("Clear log"):
                st.session_state["vault_log"] = []
                save_persisted_data()
                st.rerun()

    # --- Backup & Restore ---
    with st.expander("Backup & restore", expanded=True):
        st.caption("Export regularly — Streamlit Cloud can wipe the filesystem on redeploy.")
        export_data = {
            "fragrances_db": st.session_state.get("fragrances_db"),
            "user_reactions": st.session_state.get("user_reactions"),
            "sotd_history": st.session_state.get("sotd_history"),
            "layer_recipes": st.session_state.get("layer_recipes"),
            "play_stats": st.session_state.get("play_stats"),
            "wishlist": st.session_state.get("wishlist"),
            "vault_log": st.session_state.get("vault_log"),
            "last_export_date": st.session_state.get("last_export_date"),
            "last_saved_at": st.session_state.get("last_saved_at"),
            "chart": {
                "sun": st.session_state.get("chart_sun"),
                "moon": st.session_state.get("chart_moon"),
                "rising": st.session_state.get("chart_rising"),
                "venus": st.session_state.get("chart_venus"),
            },
        }
        json_str = json.dumps(export_data, indent=2, ensure_ascii=False)
        if st.download_button("Export vault as JSON", data=json_str, file_name="scented_dead_girl_backup.json", mime="application/json"):
            st.session_state["last_export_date"] = pacific_today().isoformat()
            save_persisted_data()

        uploaded = st.file_uploader("Restore from backup JSON", type=["json"], key="restore_up")
        if uploaded is not None:
            if st.button("Apply restore", type="primary"):
                try:
                    uploaded.seek(0)
                    imp = json.load(uploaded)
                    if "fragrances_db" in imp:
                        st.session_state["fragrances_db"] = imp["fragrances_db"]
                    if "user_reactions" in imp:
                        st.session_state["user_reactions"] = imp["user_reactions"]
                    if "sotd_history" in imp:
                        st.session_state["sotd_history"] = imp["sotd_history"]
                    if "layer_recipes" in imp:
                        st.session_state["layer_recipes"] = imp["layer_recipes"]
                    if "wishlist" in imp:
                        st.session_state["wishlist"] = imp["wishlist"]
                    if "vault_log" in imp:
                        st.session_state["vault_log"] = imp["vault_log"]
                    save_persisted_data(force=True)
                    st.success(f"Restored **{len(st.session_state.get('fragrances_db') or [])}** bottles.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Restore failed: {e}")

# ---------- ABOUT ----------
with tab_about:
    st.subheader("About")
    st.markdown(
        """
        **ScentedDeadGirl Fragrance Sanctuary**  
        Personal gothic fragrance vault.

        - New emblem logo  
        - Auto-save + backup protection  
        - Collection reactions (YAY / DEL)  
        - Edit · Remove · Compare · Family helper · Audit  
        - Full JSON export / restore  

        *scent is eternal · souls linger*
        """
    )

# ==========================================
# AUTO-SAVE
# ==========================================
try:
    autosave_if_changed(force=False)
except Exception as e:
    try:
        st.sidebar.warning(f"Autosave issue: {e}")
    except Exception:
        pass
