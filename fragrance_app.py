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
# Streamlit Cloud wipes the filesystem on many redeploys. We still write to disk
# for same-session / same-container survival, keep a .bak, refuse to overwrite a
# larger vault with a smaller one, and push the user to Export JSON often.
DATA_FILE = Path(__file__).parent / "scented_dead_girl_data.json"
DATA_BAK = Path(__file__).parent / "scented_dead_girl_data.bak.json"
# Secondary path survives some process restarts on the same container
DATA_TMP = Path("/tmp") / "scented_dead_girl_data.json"


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
    """Load the best available vault: main file, then .bak, then /tmp copy."""
    candidates = []
    for p in (DATA_FILE, DATA_BAK, DATA_TMP):
        data = _safe_json_load(p)
        if data and _vault_count(data) > 0:
            candidates.append(( _vault_count(data), str(p), data ))
    if not candidates:
        # still try empty main for reactions-only etc.
        data = _safe_json_load(DATA_FILE)
        return data if data else {}
    # Prefer the largest vault (most bottles). Tie-break: main > bak > tmp order already
    candidates.sort(key=lambda x: x[0], reverse=True)
    best = candidates[0][2]
    return best


def save_persisted_data(force: bool = False):
    """Save current session data to disk (atomic write + .bak + /tmp mirror).

    Refuses to overwrite a larger on-disk vault with a smaller session vault
    unless force=True (used after intentional batch delete / restore).
    """
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
            "his_sun": st.session_state.get("chart_his_sun"),
            "his_moon": st.session_state.get("chart_his_moon"),
            "his_rising": st.session_state.get("chart_his_rising"),
            "his_venus": st.session_state.get("chart_his_venus"),
            "his_full": st.session_state.get("birth_calc_his_full"),
        },
        "wishlist": st.session_state.get("wishlist", []),
        "vault_log": st.session_state.get("vault_log", []),
        "bottle_count": session_n,
    }

    # Guard: never wipe non-empty disk wishlist/recipes with empty session copies
    if not force:
        try:
            on_disk_pre = load_persisted_data()
            disk_wl = on_disk_pre.get("wishlist") or []
            sess_wl = data.get("wishlist") or []
            if len(disk_wl) > 0 and len(sess_wl) == 0:
                data["wishlist"] = disk_wl
                st.session_state["wishlist"] = list(disk_wl)
            disk_lr = on_disk_pre.get("layer_recipes") or []
            sess_lr = data.get("layer_recipes") or []
            if len(disk_lr) > 0 and len(sess_lr) == 0:
                data["layer_recipes"] = disk_lr
                st.session_state["layer_recipes"] = list(disk_lr)
        except Exception:
            pass

    # Guard: never clobber a bigger saved vault with a thinner session
    if not force and session_n > 0:
        on_disk = load_persisted_data()
        disk_n = _vault_count(on_disk)
        # Allow small shrink (1-2 deletes) but block catastrophic wipe
        if disk_n >= 10 and session_n < max(5, int(disk_n * 0.85)):
            st.session_state["_save_blocked"] = (
                f"Save blocked: session has **{session_n}** bottles but disk has **{disk_n}**. "
                f"Export JSON from Vault, or use Restore. "
                f"(Accidental wipe protection.)"
            )
            # Restore session from disk so the UI stops looking empty
            if on_disk.get("fragrances_db"):
                st.session_state["fragrances_db"] = on_disk["fragrances_db"]
                if on_disk.get("user_reactions") is not None:
                    st.session_state["user_reactions"] = on_disk.get("user_reactions") or {}
            return False
    elif not force and session_n == 0:
        on_disk = load_persisted_data()
        if _vault_count(on_disk) > 0:
            st.session_state["_save_blocked"] = (
                "Save blocked: session vault is empty but disk has bottles."
            )
            st.session_state["fragrances_db"] = on_disk.get("fragrances_db") or []
            if on_disk.get("wishlist"):
                st.session_state["wishlist"] = on_disk.get("wishlist") or []
            return False

    payload = json.dumps(data, indent=2, ensure_ascii=False)
    ok = False
    err_msgs = []
    for target in (DATA_FILE, DATA_TMP):
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            # Atomic-ish: write temp then replace
            tmp = target.with_suffix(target.suffix + ".tmp")
            with open(tmp, "w", encoding="utf-8") as f:
                f.write(payload)
                f.flush()
            tmp.replace(target)
            ok = True
        except Exception as e:
            err_msgs.append(f"{target.name}: {e}")

    # Keep a .bak of the last good main file
    try:
        if DATA_FILE.exists() and DATA_FILE.stat().st_size > 50:
            import shutil
            shutil.copy2(DATA_FILE, DATA_BAK)
    except Exception:
        pass

    if not ok:
        st.session_state["_save_error"] = "; ".join(err_msgs) or "unknown write error"
        try:
            st.sidebar.warning(f"Could not save data: {st.session_state['_save_error']}")
        except Exception:
            pass
        return False

    st.session_state.pop("_save_blocked", None)
    st.session_state.pop("_save_error", None)
    st.session_state["_last_disk_count"] = session_n
    st.session_state["_vault_fp"] = vault_fingerprint()
    return True


def vault_fingerprint() -> str:
    """Stable hash of everything we care to auto-save."""
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
            "his_sun": st.session_state.get("chart_his_sun"),
            "his_moon": st.session_state.get("chart_his_moon"),
            "his_rising": st.session_state.get("chart_his_rising"),
            "his_venus": st.session_state.get("chart_his_venus"),
            "his_full": st.session_state.get("birth_calc_his_full"),
        },
        "last_export_date": st.session_state.get("last_export_date"),
    }
    try:
        raw = json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str)
    except Exception:
        raw = str(payload)
    return hashlib.md5(raw.encode("utf-8", errors="replace")).hexdigest()


def mark_vault_dirty():
    """Optional explicit dirty flag (auto-save also uses fingerprint diff)."""
    st.session_state["_vault_dirty"] = True


def autosave_if_changed(force: bool = False) -> bool:
    """Save when vault data changed during this script run (or force)."""
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


# ==========================================
# PAGE CONFIGURATION & CUSTOM GOTHIC THEME
# ==========================================
st.set_page_config(
    page_title="ScentedDeadGirl Fragrance Sanctuary",
    page_icon="SDG",
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

# Built-in list is only a seed when there is NO saved vault on disk.
# If disk has bottles, those always win on a fresh session.
if "fragrances_db" not in st.session_state:
    if _persisted.get("fragrances_db"):
        st.session_state["fragrances_db"] = list(_persisted["fragrances_db"])
    else:
        # === CLEANED SEED (177 bottles)  -  matches organized vault ===
        # Built-in sanctuary collection (seed only  -  export JSON after you edit)
        st.session_state["fragrances_db"] = [
        {"name": "8th Wonder", "brand": "French Avenue", "gender": "Unisex", "season": "Fall, Winter", "notes": "Top - Cardamom, Pink Pepper, Candy Apple / Heart - Liquor, Dates, Boozy notes, Davana, Osmanthus / Base - Myrrh, Benzoin, Styrax, Amber Xtreme, Labdanum, Patchouli", "category": ["Oriental", "Spicy", "Sweet"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Ajwad", "brand": "Lattafa", "gender": "Unisex", "season": "Versatile (cooler preferred)", "notes": "Fruity-woody-oriental (pineapple/rose/oud-leaning)", "category": ["Oriental", "Woody", "Fruity"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Angham", "brand": "Lattafa", "gender": "Unisex (leans feminine)", "season": "Fall, Winter", "notes": "Top - Ginger, Mandarin, Pink Pepper / Heart - Lavender, Praline, Cacao, Jasmine / Base - Vanilla, Amber, Musk", "category": ["Gourmand", "Spicy", "Sweet"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Ansaam Gold", "brand": "Lattafa", "gender": "Female/Unisex", "season": "Fall, Winter", "notes": "Top - Mandarin Orange, Pear / Heart - Sweet Notes, Jasmine, Rose / Base - Musk, Vanilla, Raspberry", "category": ["Fruity", "Floral", "Sweet"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Asad", "brand": "Lattafa", "gender": "Male", "season": "Fall, Winter", "notes": "Top - Black Pepper, Tobacco, Pineapple / Heart - Patchouli, Coffee, Iris / Base - Vanilla, Amber, Dry Woods, Benzoin, Labdanum", "category": ["Woody", "Spicy", "Oriental"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Badee Al Oud Noble Blush", "brand": "Lattafa", "gender": "Female", "season": "Fall, Winter", "notes": "Top - Rose Milk / Heart - Meringue, Almond / Base - Vanilla, Musk, Sandalwood", "category": ["Floral", "Gourmand", "Sweet"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Bahiya Garnet", "brand": "Arabiyat Prestige", "gender": "Female-leaning", "season": "Fall, Winter", "notes": "Top - Cherry, Mandarin, Mango, Pear, Bergamot / Heart - Amber, Fig, Jasmine / Base - Amber, Vanilla, Sandalwood, Musk", "category": ["Fruity", "Oriental", "Sweet"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Banat Dubai", "brand": "Le Chameau", "gender": "Female", "season": "Versatile to cooler", "notes": "Top - Jasmine, Bergamot, Peony / Heart - Pineapple, Peach, Plum / Base - Musk, Patchouli, Sandalwood", "category": ["Floral", "Fruity"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Berries Cream Macaron", "brand": "Arabiyat Sugar", "gender": "Female", "season": "Spring-Fall", "notes": "Top Notes: Juicy lycheeHeart (Middle) Notes: Raspberry, maltol (confectionary sweetness), and jasmineBase Notes: Ambroxan, ambergris (or dry amber), and evernyl", "category": ["Gourmand", "Fruity", "Sweet"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Bint Hooran", "brand": "Ard Al Zaafaran", "gender": "Female", "season": "Fall, Winter", "notes": "Top - Almond, Coffee, Ylang Ylang / Heart - Jasmine, Rose, Tuberose / Base - Vanilla, Musk, Tonka, Woody/Cacao", "category": ["Gourmand", "Floral", "Oriental"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Boulevard of New York", "brand": "Le Chameau", "gender": "Unisex", "season": "Fall, Winter", "notes": "Top - Roasted Coffee Beans / Heart - Praline, Rose / Base - Oakmoss, Cedar, Amber", "category": ["Gourmand", "Woody"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Cafe Bliss", "brand": "Mamlakat Al Oud", "gender": "Unisex", "season": "Fall, Winter", "notes": "Top - Black Coffee, Amaretto Liquor / Heart - Vanilla Ice Cream, Speculoos / Base - Vanilla Pods, Brown Sugar, Grey Amber", "category": ["Gourmand", "Sweet"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Cafe Latte", "brand": "Khadlaj", "gender": "Unisex", "season": "Fall, Winter", "notes": "Top - Coffee, Sweet Almond, Milk / Heart - Vanilla, Ice Cream Accord, Amber / Base - Vanilla, Almond Cream, Caramel", "category": ["Gourmand", "Sweet"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Caramel Chocolate Macaron", "brand": "Arabiyat Sugar", "gender": "Female/Unisex", "season": "Fall-Winter", "notes": "Top Notes: Caramel, Coumarin (providing a sweet, warm, almond-vanilla nuance)Middle / Heart Notes: Honey, Soft Floral NotesBase Notes: Musk", "category": ["Gourmand", "Sweet"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Caramello", "brand": "Al Rehab", "gender": "Unisex", "season": "Fall, Winter", "notes": "Top - Pistachio, Almond / Heart - Jasmine, Heliotrope / Base - Caramel, Vanilla, Sandalwood", "category": ["Gourmand", "Sweet"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Chocomusk", "brand": "Al Rehab", "gender": "Unisex", "season": "Fall, Winter", "notes": "Top - Warm Spicy, Amber / Heart - Sweet, Powdery, Vanilla / Base - Chocolate, Musky, Cocoa", "category": ["Gourmand", "Sweet"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Chocomusk Marshmallow", "brand": "Al Rehab", "gender": "Unisex", "season": "Fall, Winter", "notes": "Top - Marshmallow, Strawberry / Heart - Cocoa, Vanilla / Base - Sweet Musk", "category": ["Gourmand", "Sweet"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Chocomusk Vanilla", "brand": "Al Rehab", "gender": "Unisex", "season": "Fall, Winter", "notes": "Top - Chocolate / Heart - Vanilla / Base - Musk", "category": ["Gourmand", "Sweet"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Club De Nuit Women", "brand": "Armaf", "gender": "Female", "season": "Spring, Fall", "notes": "Top - Apple, Citrus / Heart - Rose, Jasmine / Base - Vanilla, Musk", "category": ["Floral", "Fruity", "Fresh"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Coconut Chiffon", "brand": "Arabiyat Sugar", "gender": "Female/Unisex", "season": "Spring-Summer", "notes": "Top Notes: CoconutMiddle (Heart) Notes: Coconut, JasmineBase Notes: Vanilla, Butter, Cooked Sugar (Caramel), Musk", "category": ["Gourmand", "Sweet", "Fresh"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Confections", "brand": "Paris Corner", "gender": "Female/Unisex", "season": "Fall-Winter", "notes": "Top Notes: Pear and Whipped CreamHeart (Middle) Notes: Cashmeran, Jasmine, and Ylang-YlangBase Notes: Marshmallow, Vanilla, and Sandalwood", "category": ["Gourmand", "Sweet"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Cookie Bite", "brand": "Gulf Orchid", "gender": "Unisex", "season": "Fall, Winter", "notes": "Top - Cookie, Butter / Heart - Vanilla, Musk / Base - Caramel, Amber", "category": ["Gourmand", "Sweet"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Coral (Ana Abiyedh Coral)", "brand": "Lattafa", "gender": "Unisex (leans feminine)", "season": "Spring, Summer", "notes": "Top - Watermelon, Peach, Orange / Heart - Coconut, White Flowers / Base - Musk, Vanilla, Amber", "category": ["Fruity", "Fresh", "Sweet"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Cotton Blush", "brand": "Arabiyat Sugar", "gender": "Female", "season": "Spring, summer", "notes": "Top Notes: Strawberry, Raspberry, CoconutHeart (Middle) Notes: Marshmallow, Peony, RoseBase Notes: Vanilla, Amber, Musk", "category": ["Floral", "Fruity", "Gourmand"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Cotton Candy Delicacy", "brand": "Armaf", "gender": "Unisex", "season": "Spring, Summer", "notes": "Top Notes: Raspberry, Pink Pepper, and CocoaHeart (Middle) Notes: Jasmine and RoseBase Notes: Vanilla, Benzoin Resinoid, and Cedarwood", "category": ["Gourmand", "Fruity", "Floral"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Cream Velvet", "brand": "Khadlaj", "gender": "Unisex (leans feminine)", "season": "Fall, Winter", "notes": "Top - Caramel, Butter / Heart - Tonka, Honey, Jasmine / Base - Vanilla, Musk, Amber", "category": ["Gourmand", "Sweet"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Creme of Clouds", "brand": "Fragrance World", "gender": "Unisex", "season": "Fall, Winter, spring", "notes": "Top Notes: Coconut milk, Creamy milk, Burnt sugarHeart (Middle) Notes: Whipped cream, Vanilla, ChocolateBase Notes: Vanilla, White musk, Burnt sugar", "category": ["Gourmand", "Sweet"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Creme Caramel", "brand": "Mamlakat Al Oud", "gender": "Unisex (leans feminine)", "season": "Fall, Winter", "notes": "Top - Caramel, Vanilla Flower / Heart - Dulce de Leche, Cotton Candy, Frangipani, White Flowers / Base - Vanilla Pod, Tonka Bean, Musk", "category": ["Gourmand", "Sweet"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Cup Cake", "brand": "Al Rehab", "gender": "Unisex", "season": "Fall, Winter", "notes": "Top - Citrus, Amber / Heart - Vanilla Cake / Base - Vanilla, Amber", "category": ["Gourmand", "Sweet"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Dalal", "brand": "Lattafa", "gender": "Female", "season": "Spring", "notes": "Top - Apple (Golden Delicious), Mandarin / Heart - Jasmine, Ylang-Ylang, Orange Flower / Base - Vanilla, Musk, Oakmoss", "category": ["Floral", "Fruity", "Fresh"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Dulzura", "brand": "Paris Corner", "gender": "Female", "season": "Fall-Winter", "notes": "Top - Black pepper, buttermilk / Heart - Cake, vanilla, cream / Base - Amber, musk", "category": ["Gourmand", "Sweet"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Eclaire", "brand": "Lattafa", "gender": "Female", "season": "Fall, Winter", "notes": "Top - Caramel, Milk, Sugar / Heart - Honey, White Flowers / Base - Vanilla, Praline, Musk", "category": ["Gourmand", "Sweet"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Eclaire Banoffi", "brand": "Lattafa", "gender": "Unisex/Female", "season": "Fall-Winter", "notes": "Top Notes: Banana Cream, Dulce de LecheHeart (Middle) Notes: Whipped Cream, VanillaBase Notes: Praline, Biscuit, Musk", "category": ["Gourmand", "Sweet"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Elyssia Aura", "brand": "Riiffs", "gender": "Unisex", "season": "Fall, Winter (versatile to cooler)", "notes": "Top - Cinnamon, Orange, Nutmeg / Heart - Vanilla Cream, Cognac, Cocoa / Base - Bourbon Vanilla, Cedarwood, Patchouli", "category": ["Gourmand", "Spicy", "Woody"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Elyssia Scarlet", "brand": "Riiffs", "gender": "Female", "season": "Spring-Summer / versatile", "notes": "Top - Black Cherry, Pink Pepper / Heart - Leather, Cream, Benzoin / Base - Vanilla Absolute, Cashmeran, Amber, Iso E Super", "category": ["Fruity", "Leather", "Sweet"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Emaan", "brand": "Lattafa", "gender": "Female/Unisex", "season": "Fall, Winter", "notes": "Top - Orange Blossom, Black Currant, Bergamot / Heart - Tuberose, Jasmine, Marigold / Base - Musk, Vanilla, Cedarwood, Patchouli", "category": ["Floral", "Fruity"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Emir Pear Potion", "brand": "Paris Corner", "gender": "Unisex", "season": "Spring", "notes": "Top - Pear, Apple / Heart - Caramel, Jasmine / Base - Raspberry, Musk", "category": ["Fruity", "Gourmand", "Sweet"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Empire Najm by Risala", "brand": "Risala", "gender": "Unisex (female-leaning)", "season": "Fall, Winter", "notes": "Top - Mango, Ginger, Lemon, Red Berries / Heart - Coumarin, Jasmine, Cedar / Base - Cypriol, Amber, Musk, Oud", "category": ["Fruity", "Oriental", "Woody"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Empire Victor", "brand": "Khadlaj", "gender": "Unisex", "season": "Fall, Winter,spring", "notes": "Top Notes: Lemon, BergamotMiddle (Heart) Notes: Caramel, JasmineBase Notes: Vanilla, Musk (some variations also list sandalwood)", "category": ["Gourmand", "Floral", "Fruity"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Energize", "brand": "Heroes", "gender": "Male", "season": "Spring, Summer", "notes": "Top - Citrus, Aromatic Herbs / Heart - Light Spices / Base - Woods, Musk", "category": ["Fresh", "Citrus", "Aromatic"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Entice Extrait", "brand": "Vurv", "gender": "Female", "season": "Cooler / evening", "notes": "Top Notes: Citrus and fresh floral elements (including aromatic nuances like lilac and bergamot)Heart / Middle Notes: Rich bouquet of floral accordsBase Notes: Warm amber, sensual musk, and woody elements", "category": ["Oriental", "Sweet", "Fruity"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Entice Ruby", "brand": "Vurv", "gender": "Female", "season": "Spring-Summer / versatile", "notes": "Top Notes: Red fruits, Bergamot, MandarinHeart (Middle) Notes: Roses, Jasmine, White flowersBase Notes: Amber, Musk, Soft woods, Vanilla", "category": ["Fruity", "Floral"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Eshal Vanilla", "brand": "Paris Corner", "gender": "Female/Unisex", "season": "Fall, Winter", "notes": "Top - Sugar, Sweet Notes / Heart - Rose, Jasmine / Base - Vanilla, Caramel, Musk", "category": ["Gourmand", "Floral", "Sweet"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Espada Intense", "brand": "Le Chameau", "gender": "Male", "season": "Cooler seasons / evening", "notes": "Deeper/intensified version of Espada Prime", "category": ["Woody", "Spicy"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Espada Prime", "brand": "Le Chameau", "gender": "Male", "season": "Spring-Summer / versatile", "notes": "Top Notes (Head): Ruby, mandarin orange, grapefruit, and peppermint (mint)Middle Notes (Heart): Rose absolute, cinnamon, and mixed spicesBase Notes: Leather, patchouli, whitewoods, and amber", "category": ["Fresh", "Woody", "Spicy"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Essences", "brand": "Sara Debai", "gender": "Female", "season": "Spring-Summer", "notes": "Top - Heliotrope, orchid, tangerine / Heart - Gourmand accord, tropical fruits / Base - Vanilla, musk, sandalwood", "category": ["Floral", "Gourmand", "Fruity"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Eternal Vanille", "brand": "Lattafa", "gender": "Unisex", "season": "Year-round (best Spring/Fall)", "notes": "Top - Blackberry / Heart - Cocoapulse, Vanilla Caviar, Cacao / Base - Akigalawood, Tonka Bean, Ambrofix, Cedarwood, Benzoin, Musk", "category": ["Gourmand", "Woody", "Sweet"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Fakhama", "brand": "Amaran", "gender": "Unisex/Male", "season": "Cooler seasons", "notes": "Top Notes: Cinnamon, nutmeg, and vanillaMiddle (Heart) Notes: Dates, tuberose, praline, and mahonialBase Notes: Musk, tonka bean, amberwood, myrrh, benzoin, and akigalawood", "category": ["Oriental", "Woody"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Fakhar Black", "brand": "Lattafa", "gender": "Unisex", "season": "Fall, Winter", "notes": "Top - Dark Fruits, Spices / Heart - Woody / Base - Vanilla, Musk", "category": ["Fruity", "Woody", "Spicy"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Fakhar Gold", "brand": "Lattafa", "gender": "Unisex", "season": "Fall, Winter", "notes": "Top - Tuberose, Salt / Heart - Amber, Tonka / Base - Cedarwood, Vetiver, Labdanum", "category": ["Floral", "Woody", "Oriental"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Fakhar Silver", "brand": "Lattafa", "gender": "Unisex", "season": "Versatile", "notes": "Top Notes: Apple, Bergamot, GingerHeart (Middle) Notes: Lavender, Sage, Juniper Berries, GeraniumBase Notes: Tonka Bean, Amberwood, Cedar, Vetiver", "category": ["Gourmand"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Falak", "brand": "Nusuk", "gender": "Unisex", "season": "Fall, Winter", "notes": "Top - Brown Sugar, Caramel, Biscuit / Heart - Toffee, Vanilla Bean, Amber / Base - White Musk, Praline", "category": ["Gourmand", "Sweet"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Fatima Pink", "brand": "Zimaya", "gender": "Female", "season": "Spring, Fall", "notes": "Top - Rhubarb, Bergamot, Grapefruit, Nutmeg / Heart - Rose, Jasmine / Base - Musk, Vanilla, Vetiver, Ambergris", "category": ["Floral", "Fruity", "Fresh"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Fire on Ice", "brand": "Lattafa", "gender": "Unisex", "season": "Versatile", "notes": "Top Notes: Black raspberry, cinnamon, cognac (liquor)Middle (Heart) Notes: Frozen rose petals, caramel, mossBase Notes: Oakwood, myrrh, cedarwood, ambroxan", "category": ["Gourmand"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "French Vanilla", "brand": "Al Rehab", "gender": "Unisex", "season": "Fall, Winter", "notes": "Top - Vanilla / Heart - Creamy Sweet / Base - Vanilla, Musk", "category": ["Gourmand", "Sweet"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "French Vanilla Latte", "brand": "Arabiyat Sugar", "gender": "Unisex", "season": "Fall, Winter", "notes": "Top - Nutella, Cardamom, Rum / Heart - Cocoa, Coconut, White Flowers, Lily of the Valley / Base - Sandalwood, Ambergris, Musk", "category": ["Gourmand", "Sweet"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Ghaliya", "brand": "Zakat", "gender": "Unisex/Female", "season": "Fall-Winter", "notes": "Top Notes: Orange, Lemon, Apple, and BergamotMiddle (Heart) Notes: Caramel, Muguet (Lily of the Valley), Cedarwood, Jasmine Sambac, Bulgarian Rose, and TuberoseBase Notes: Tonka Bean, Amber, Musk, Cocoa, Sandalwood, and Patchouli", "category": ["Oriental", "Floral", "Oud"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Ghubar Al Dhahab", "brand": "Sahari", "gender": "Unisex", "season": "Fall, Winter", "notes": "Top - Cinnamon, Pear, Mandarin, Floral notes / Heart - Jasmine Sambac, Orange Blossom / Base - White Musk, Vanilla, Tonka Bean, Coffee, Patchouli", "category": ["Floral", "Spicy", "Sweet"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Habik (Women's Version)", "brand": "Lattafa", "gender": "Female", "season": "Spring, Summer", "notes": "Top - Pear, Bergamot / Heart - Lily of the Valley, Jasmine, Freesia / Base - Musk, Amber, Oakmoss", "category": ["Floral", "Fresh", "Fruity"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Hareem Al Sultan Gold", "brand": "Khadlaj", "gender": "Female", "season": "Spring, Summer", "notes": "Top - Bergamot, Jasmine, Peony / Heart - Pineapple, Peach, Plum / Base - Musk, Sandalwood, Patchouli", "category": ["Floral", "Fruity", "Fresh"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Hawas Diva", "brand": "Rasasi", "gender": "Female", "season": "Fall, Winter", "notes": "Top - Red Fruits, Rhubarb, Lychee / Heart - Rose, Frankincense, Cedar / Base - Vanilla, Musk, Ambergris", "category": ["Fruity", "Floral", "Woody"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Hawas Eclat (Eclat Hawas)", "brand": "Rasasi", "gender": "Female", "season": "Spring, Fall", "notes": "Top - Litchi/Lychee, Bergamot, Pear, Pistachio / Heart - Rose, Incense / Base - Vanilla, Amber, Musk, Woody Notes", "category": ["Fruity", "Floral", "Woody"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Hawas Elixir", "brand": "Rasasi", "gender": "Unisex", "season": "Fall-Winter", "notes": "Top - Mint, bergamot, artemisia / Heart - Dark chocolate, lavender, benzoin / Base - Vanilla, tonka bean, white musk", "category": ["Gourmand", "Fresh", "Sweet"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Hawas Ice", "brand": "Rasasi", "gender": "Male", "season": "Versatile", "notes": "Top - Apple, Italian Lemon, Sicilian Bergamot, Star Anise / Heart - Plum, Orange Blossom, Cardamom / Base - Musk, Moss, Driftwood, Amber", "category": ["Fresh", "Fruity", "Aromatic"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Hawas London", "brand": "Rasasi", "gender": "Unisex", "season": "Fall, Spring", "notes": "Top - Pink Pepper, Saffron, Pear / Heart - Rose, Frankincense, White Flowers / Base - Blonde Woods, Vanilla, Amber, Musk", "category": ["Floral", "Woody", "Spicy"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Hawas Pink", "brand": "Rasasi", "gender": "Female", "season": "Fall, Winter", "notes": "Top - Cinnamon, Nutmeg, Neroli / Heart - Marshmallow, Tuberose, Orange Blossom / Base - Cotton Candy, Vanilla, Tonka Bean", "category": ["Gourmand", "Floral", "Sweet"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Hawwa Red", "brand": "Zimaya", "gender": "Female", "season": "Fall, Winter", "notes": "Top - Cassis, Strawberry, Raspberry, Orange / Heart - Black Currant, Grapefruit, Peach, Lily / Base - Musk, Vanilla, Patchouli", "category": ["Fruity", "Floral", "Sweet"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Haya", "brand": "Lattafa", "gender": "Female", "season": "Fall, Winter", "notes": "Top - Champagne, Strawberry, Rose, Tangerine, Blood Orange / Heart - Gardenia, Jasmine, Vanilla Orchid / Base - Amber, Sandalwood", "category": ["Floral", "Fruity", "Sweet"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Heavy Cream", "brand": "Phlur", "gender": "Unisex", "season": "Fall, Winter", "notes": "Top - Marshmallow, Sugar, Citrus / Heart - Coconut, Jasmine / Base - Whipped Cream, Vanilla, Caramel", "category": ["Gourmand", "Sweet"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Her Confessions", "brand": "Lattafa", "gender": "Female", "season": "Fall, Winter", "notes": "Top - Cinnamon / Heart - Tuberose, Jasmine, Incense / Base - Vanilla, Musk, Tonka", "category": ["Floral", "Spicy", "Oriental"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "His Confessions", "brand": "Lattafa", "gender": "Male", "season": "Fall, Winter", "notes": "Top - Lavender, Cinnamon, Mandarin / Heart - Iris, Benzoin, Cypress, Mahonial / Base - Vanilla, Tonka, Amber, Incense, Cedarwood, Patchouli", "category": ["Woody", "Spicy", "Oriental"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Island Bliss", "brand": "Armaf", "gender": "Unisex", "season": "Spring, Summer", "notes": "Top - Tropical Fruits, Coconut / Heart - Sweet / Base - Musk", "category": ["Fruity", "Fresh", "Sweet"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Khair Men", "brand": "Paris Corner", "gender": "Male/Unisex", "season": "Fall, Winter", "notes": "Top - Davana, Bergamot, Pink Pepper / Heart - Agarwood (Oud), Amber, Rosemary / Base - Leather, Vetiver, Musk", "category": ["Woody", "Oud", "Spicy"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Khamrah Dukhan", "brand": "Lattafa", "gender": "Unisex", "season": "Fall, Winter", "notes": "Top - Spices, Pimento, Mandarin / Heart - Incense, Labdanum, Orange Blossom, Patchouli / Base - Tobacco, Praline, Amber, Tonka Bean, Benzoin", "category": ["Oriental", "Spicy", "Sweet"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Khamrah Original", "brand": "Lattafa", "gender": "Unisex", "season": "Fall, Winter", "notes": "Top - Cinnamon, Nutmeg, Bergamot / Heart - Dates, Praline, Tuberose, Mahonial / Base - Vanilla, Tonka Bean, Amberwood, Myrrh, Benzoin, Akigalawood", "category": ["Oriental", "Spicy", "Sweet"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Khamrah Qahwa", "brand": "Lattafa", "gender": "Unisex", "season": "Fall, Winter", "notes": "Top - Cinnamon, Cardamom, Ginger / Heart - Praline, Candied Fruits, White Flowers / Base - Coffee, Vanilla, Tonka Bean, Benzoin, Musk", "category": ["Gourmand", "Spicy", "Sweet"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Khamrah Waha", "brand": "Lattafa", "gender": "Unisex", "season": "Fall-Winter", "notes": "Spicy-sweet (date, cinnamon, vanilla family)", "category": ["Oriental", "Spicy", "Sweet"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Kiaana Angel", "brand": "Afnan", "gender": "Female", "season": "Spring, summer", "notes": "Top Notes: Pistachio Gelato (or Ice Cream), Italian BergamotMiddle (Heart) Notes: Jasmine, Raspberry, White Peach, PearBase Notes: Cedarwood, Sandalwood, Tonka Bean", "category": ["Gourmand", "Floral", "Fruity"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Le Parfum", "brand": "Blue for Men", "gender": "Male/Unisex", "season": "Fall, Winter", "notes": "Top - Cardamom / Heart - Lavender, Iris / Base - Vanilla, Oriental Woods", "category": ["Woody", "Oriental", "Spicy"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Lemon Sorbet", "brand": "Arabiyat Sugar", "gender": "Unisex", "season": "Spring, summer", "notes": "Top Notes: Zesty lemon and a subtle nuance of rumMiddle/Heart Notes: Sweet gourmand and sorbet cream accordBase Notes: Creamy vanilla and soft musk", "category": ["Gourmand", "Fruity", "Oriental"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Love & Peace", "brand": "Lattafa", "gender": "Unisex/Female", "season": "Spring-Fall", "notes": "Top Notes: Almond, Black Currant, and BergamotMiddle (Heart) Notes: Rose and TuberoseBase Notes: Sandalwood, Vanilla, and Heliotrope", "category": ["Floral", "Sweet"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Luxe Chic", "brand": "Maison Alhambra", "gender": "Female/Unisex", "season": "Spring, Fall", "notes": "Top - Tangerine, Freesia / Heart - Lily of the Valley, Jasmine, Rose / Base - Musk, Sandalwood, Amber", "category": ["Floral", "Fresh"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Maitha Oil (Attar)", "brand": "Lattafa", "gender": "Unisex", "season": "Fall, Winter", "notes": "Top - Anise / Heart - Caramel / Base - Vanilla, Tonka Bean, Musk", "category": ["Gourmand", "Sweet"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Majestic Supreme", "brand": "Le Falcone", "gender": "Women/Unisex", "season": "Fall-Winter / versatile", "notes": "Top - Rose, peony, pink pepper / Heart - Raspberry blossom, jasmine / Base - Amber, papyrus, tonka, vanilla", "category": ["Floral", "Sweet"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Malika", "brand": "Nusuk", "gender": "Female", "season": "Versatile", "notes": "Top Notes: Ozonic notes, apple, aldehydic notes, tarragon, bergamot, and orangeHeart Notes: Lily of the valley, jasmine, rose, carnation, orchid, and honeysuckleBase Notes: Musk, amber, vanilla, sandalwood, cedarwood, and orris", "category": ["Floral", "Oriental"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Mango Affogato", "brand": "Arabiyat Sugar", "gender": "Unisex", "season": "Spring-Summer / year-round", "notes": "Top - Mango, nutmeg, clove / Heart - Leather, saffron, amber, moss / Base - Akigalawood, patchouli, vetiver, cypriol", "category": ["Fruity", "Woody", "Spicy"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Mango Ice", "brand": "Gulf Orchid", "gender": "Unisex", "season": "Spring-Summer", "notes": "Top Notes: Mango, Lemon, Ginger, RhubarbHeart (Middle) Notes: White Flowers, Amber, LicoriceBase Notes: Musk, Vanilla, Caramel, Chestnut", "category": ["Fruity", "Fresh"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Marshmallow Blush", "brand": "Paris Corner", "gender": "Female/Unisex", "season": "Fall, Winter", "notes": "Top - Marshmallow, Sweet / Heart - Fruity / Base - Vanilla, Musk", "category": ["Gourmand", "Sweet", "Fruity"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Marshmallow Dreams", "brand": "NatureWell", "gender": "Female", "season": "Fall, winter", "notes": "Top Notes: Lemon Sugar & MarshmallowMid Notes: Coconut CreamBase Notes: Vanilla Mousse & Whipped Cream", "category": ["Gourmand", "Sweet"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Marshmallows Kiss", "brand": "Mamlakat Al Oud", "gender": "Unisex", "season": "Fall, Winter, Spring", "notes": "Top - Strawberry, Blackberry (or Caramel/Milk) / Heart - Jasmine, Rose, Marshmallow, Vanilla, Honey / Base - Vanilla, Musk, Praline, Tonka", "category": ["Gourmand", "Floral", "Sweet"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Mayar", "brand": "Lattafa", "gender": "Female", "season": "Spring, Summer", "notes": "Top - Lychee, Raspberry, Violet Leaf / Heart - Peony, White Rose, Jasmine / Base - Musk, Vanilla", "category": ["Floral", "Fruity", "Fresh"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Mayar Cherry Intense", "brand": "Lattafa", "gender": "Female", "season": "Fall, Winter", "notes": "Top - Strawberry, Bergamot / Heart - Cherry Jam, Cacao / Base - Vanilla, Amber, Patchouli", "category": ["Fruity", "Gourmand", "Sweet"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Milano", "brand": "Valentine", "gender": "Unisex", "season": "Fall, Winter", "notes": "Top - Raspberry, Peach, Bergamot / Heart - Rose, Jasmine, Orange Blossom / Base - Vanilla, Amber, Woods", "category": ["Floral", "Fruity", "Sweet"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Momento", "brand": "Riiffs", "gender": "Unisex", "season": "Versatile", "notes": "Top Notes: Sugar, Saffron, and Mandarin give a sweet and citrus opening.Heart (Middle) Notes: Tonka Bean, Damask Rose, and Agarwood (Oud) create a floral and rich center.Base Notes: Caramel, Amberwood, and Cedar leave a warm and woody finish.", "category": ["Aromatic"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Mystique", "brand": "Armaf", "gender": "Female", "season": "Fall, Winter", "notes": "Top - Pear, Tangerine, Bergamot, Orange / Heart - Vanilla, Strawberry, Mimosa, Rose, Ylang Ylang, Jasmine, Passionfruit / Base - Vanilla, Coffee, Tonka Bean, Patchouli, Vetiver", "category": ["Floral", "Fruity", "Gourmand"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Mystique Charm", "brand": "Dorall Collection", "gender": "Female", "season": "Spring, summer", "notes": "Top Notes: Clementine, Cappuccino, Cactus, Pepper, and BlackberryMiddle (Heart) Notes: Mimosa, Hortensia (Hydrangea), Camellia, and OrchidBase Notes: Woody Notes, Blackberry, Musk, Amber, and Red Berries", "category": ["Sweet", "Floral", "Oriental", "Fruity"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Nagham", "brand": "Atyaab", "gender": "Unisex", "season": "Versatile", "notes": "Top Notes: Rose, Jasmine, and BergamotMiddle (Heart) Notes: Amber, Vetiver, and Candied Fruit (such as sweet strawberries and cherries)Base Notes: Vanilla, Cedarwood, and Sandalwood", "category": ["Floral", "Woody", "Oriental"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Nasmaat", "brand": "Lattafa", "gender": "Unisex", "season": "Spring, Fall", "notes": "Top - Blackcurrant, Apricot, Pineapple / Heart - Magnolia, Cyclamen, Jasmine, Orange Blossom, Rose / Base - Vanilla, Cashmeran, Caramel, Sandalwood", "category": ["Floral", "Fruity", "Sweet"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Natural Intense Body Spray", "brand": "Mayar", "gender": "Female", "season": "Fall, Winter", "notes": "Top - Sweet Gourmand / Heart - Vanilla / Base - Musk", "category": ["Gourmand", "Sweet"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Nebras", "brand": "Lattafa", "gender": "Unisex", "season": "Fall, Winter", "notes": "Top - Red Berries, Mandarin Orange / Heart - Vanilla, Cacao, Rose / Base - Sugar, Tonka Bean, Amber, Musk", "category": ["Gourmand", "Fruity", "Sweet"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Nebras Elixir", "brand": "Lattafa", "gender": "Unisex", "season": "Fall, Winter, Mild Spring", "notes": "Top - Milk Candy, Whipped Cream / Heart - Sugar Cane, Heliotrope / Base - Vanilla, Ambroxan, Musk", "category": ["Gourmand", "Sweet"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Nero Xtravagant", "brand": "Valentine (Urban Collection)", "gender": "Male/Unisex (leans masculine)", "season": "Fall, Winter (versatile)", "notes": "Top - Calabrian Bergamot, Espresso Coffee Accord / Heart - Coffee / Base - Vetiver", "category": ["Woody", "Fresh", "Aromatic"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Noor", "brand": "Riiffs", "gender": "Unisex", "season": "Fall, Winter", "notes": "Top Notes: Caramel and milkMiddle (Heart) Notes: Gourmand accord and lily of the valleyBase Notes: Vanilla, musk, and praline", "category": ["Gourmand", "Floral", "Sweet"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Nuha Vanilla Pearl", "brand": "Khadlaj", "gender": "Female", "season": "Fall, Winter", "notes": "Top - Blackcurrant, Strawberry, Freesia / Heart - Raspberry, Magnolia, Cashmere Wood / Base - Vanilla, Caramel, Moss", "category": ["Fruity", "Gourmand", "Floral"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Nyla", "brand": "Arabiyat Prestige", "gender": "Female", "season": "Spring, Summer", "notes": "Top - Coconut, Peach, Bergamot, Mandarin / Heart - Tiare, White Flowers, Jasmine, Rose / Base - White Musk, Patchouli", "category": ["Floral", "Fruity", "Fresh"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Nyla Vanielle", "brand": "Arabiyat Prestige", "gender": "Female", "season": "Fall, Winter", "notes": "Top - Jasmine, Vanilla Bean / Heart - Caramel, Amber / Base - Musk, Tonka Bean, Vanilla", "category": ["Gourmand", "Sweet", "Floral"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Obsidian", "brand": "French Avenue", "gender": "Unisex/Male", "season": "Fall-Winter", "notes": "Top Notes: Aldehydes, Grapefruit, BergamotHeart Notes: Myrrh, Jasmine, LabdanumBase Notes: Vanilla, Amber, Tonka Bean", "category": ["Woody", "Oriental", "Smoky"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Odyssey Aqua", "brand": "Armaf", "gender": "Male", "season": "Spring, Summer", "notes": "Top - Orange, Grapefruit, Artemisia / Heart - Mint, Lavender / Base - Ambroxan, Cypress, Patchouli", "category": ["Fresh", "Citrus", "Aromatic"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Odyssey Candee", "brand": "Armaf", "gender": "Female-leaning", "season": "Fall, Winter", "notes": "Top - Strawberry, Raspberry, Peach, Bergamot / Heart - Caramel, Jasmine / Base - Patchouli, Musk, Amber", "category": ["Fruity", "Gourmand", "Sweet"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Odyssey Marshmallow", "brand": "Armaf", "gender": "Unisex", "season": "Spring, Fall, Winter", "notes": "Top - Apple, Lemon, Coconut, Peony, Lily of the Valley / Heart - Strawberry, Peach, Raspberry, Apricot, Marshmallow, Orange Blossom / Base - Vanilla, Praline, Tonka, Amber, Musk, Mascarpone", "category": ["Gourmand", "Fruity", "Sweet"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Opulent Dubai", "brand": "Lattafa", "gender": "Unisex", "season": "Spring, Summer (versatile year-round in mild climates)", "notes": "Top - Mango, Grapefruit, Lemon, Ginger / Heart - Jasmine, Cedarwood, Violet / Base - Woodsy notes, Ambergris, Benzoin, Oakmoss", "category": ["Fruity", "Woody", "Fresh"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Oud Mood", "brand": "Lattafa", "gender": "Unisex", "season": "Fall, Winter", "notes": "Top - Rose, Saffron, Pimento / Heart - Agarwood (Oud), Caramel, Floral Notes, Patchouli / Base - Woody Notes, Amber, Resins, Incense, Musk", "category": ["Oriental", "Oud", "Woody"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Panache Angel Dust", "brand": "Khadlaj", "gender": "Female", "season": "Spring-Fall / versatile", "notes": "Top Notes: Vanilla, Mandarin, and Red CurrantMiddle (Heart) Notes: Tuberose, Sandalwood, and RumBase Notes: Vanilla, Whipped Cream, Musk, and Benzoin", "category": ["Floral", "Sweet", "Powdery"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Peach Velvet", "brand": "Khadlaj", "gender": "Female", "season": "Spring, Summer, Fall", "notes": "Top - Guava, Peach, Nectarine / Heart - Vanilla, Ginger, Cinnamon, Amber / Base - Caramel, Musk, Sandalwood", "category": ["Fruity", "Gourmand", "Sweet"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Pecan Butter Cookie", "brand": "Arabiyat Sugar", "gender": "Unisex/Female", "season": "Fall-Winter", "notes": "Top - Pecan, coconut milk, butter / Heart - Hazelnut, almond, roasted nuts / Base - Hazelnut, vanilla, ambergris", "category": ["Gourmand", "Sweet"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Petra", "brand": "Lattafa", "gender": "Unisex", "season": "Fall, Winter", "notes": "Top Notes: Plum, RumHeart (Middle) Notes: Tuberose, CoconutBase Notes: Praline, Musk, Vanilla", "category": ["Gourmand", "Fruity", "Floral"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Pink Velvet", "brand": "Maison Alhambra", "gender": "Female", "season": "Spring-Fall", "notes": "Top Notes: Bulgarian Rose and May RoseMiddle/Heart Notes: Turkish Rose and SaffronBase Notes: Patchouli, Tonka Bean, and Vanilla", "category": ["Floral", "Sweet", "Powdery"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Pina Colada Musk Collection Body Spray", "brand": "Gulf Orchid", "gender": "Unisex", "season": "Spring, Summer", "notes": "Top - Pineapple, Coconut / Heart - Tropical / Base - Musk", "category": ["Fruity", "Fresh", "Sweet"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Prive Rose", "brand": "Ameerat Al Arab", "gender": "Female", "season": "Fall, Spring", "notes": "Top - Rose / Heart - Floral, Sweet / Base - Musk, Vanilla", "category": ["Floral", "Sweet"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Qaed Al Fursan (Original)", "brand": "Lattafa", "gender": "Unisex (leans masculine)", "season": "Versatile", "notes": "Top - Pineapple, Saffron / Heart - Balsam Fir, Jasmine / Base - Cedar, Amber, Agarwood (Oud)", "category": ["Fruity", "Woody", "Oud"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Qaed Al Fursan Unlimited", "brand": "Lattafa", "gender": "Male/Unisex", "season": "Spring, Fall", "notes": "Top - Coconut, Pineapple, Citruses / Heart - Ylang-Ylang, Frangipani, Jasmine / Base - Vanilla, Musk, Sandalwood, Sweet Notes", "category": ["Fruity", "Floral", "Sweet"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Qaed Al Fursan Untamed", "brand": "Lattafa", "gender": "Male/Unisex", "season": "Spring, Fall", "notes": "Top - Apple, Citrus / Heart - Floral / Base - Sweet, Woody", "category": ["Fruity", "Woody", "Fresh"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Raheeq", "brand": "Nusuk", "gender": "Female/Unisex", "season": "Versatile", "notes": "Top Notes: Honey, Blood Orange, Apricot, and LemonMiddle (Heart) Notes: Caramel, Coconut, and MagnoliaBase Notes: Vanilla Absolute, Musk, and Sandalwood", "category": ["Floral", "Sweet"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Raneen", "brand": "Lattafa", "gender": "Female", "season": "Fall, Winter", "notes": "Top - Fruity, Sweet / Heart - Floral / Base - Vanilla, Musk", "category": ["Floral", "Fruity", "Sweet"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Rave Now (for Women)", "brand": "Lattafa", "gender": "Female", "season": "Spring, Fall", "notes": "Top - Red Fruits, Orange / Heart - Marshmallow, Jasmine, Lily of the Valley / Base - Vanilla, Musk, Moss", "category": ["Fruity", "Gourmand", "Floral"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Rave Now Intense", "brand": "Lattafa", "gender": "Male/Unisex", "season": "Spring, Fall", "notes": "Top - Cucumber, Watermelon, Tangerine / Heart - Basil, Sage / Base - Sandalwood, Leather, Cedar", "category": ["Fresh", "Woody", "Aromatic"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Rave Rage", "brand": "Lattafa", "gender": "Unisex (leans masculine)", "season": "Year-round", "notes": "Top - Apple, mint / Heart - Geranium, cinnamon, lavender / Base - Vanilla, Peru balsam, cedarwood, guaiac wood", "category": ["Fresh", "Woody", "Spicy"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Red 500", "brand": "Baraja", "gender": "Unisex/Male", "season": "Fall, Winter", "notes": "Top - Red Fruits, Spices / Heart - Sweet Notes / Base - Woody, Musk", "category": ["Fruity", "Woody", "Spicy"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Red Velvet Delicacy", "brand": "Armaf", "gender": "Unisex", "season": "Fall, Winter", "notes": "Top - Strawberry, Lemon / Heart - Whipped Sugar, Sugarberry, Frangipani / Base - Vanilla Bean, Musk, Amber", "category": ["Gourmand", "Fruity", "Sweet"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Royal Men", "brand": "Al Rehab", "gender": "Male", "season": "Fall, Winter", "notes": "Top - Spicy, Citrus, Woody / Heart - Floral, Sweet / Base - Amber, Musk, Vanilla", "category": ["Woody", "Spicy", "Oriental"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Safa", "brand": "Nusuk", "gender": "Unisex/Female", "season": "Spring-Summer / versatile", "notes": "Top - Marshmallow, Strawberry, Lemon / Heart - Coconut, Sugar, Nectarine / Base - Vanilla, Musk, Ambroxan", "category": ["Gourmand", "Fruity", "Sweet"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Sakeena", "brand": "Lattafa", "gender": "Female/Unisex", "season": "Fall, Winter", "notes": "Top - Passionfruit, Mandarin Orange, Ozonic Notes / Heart - Raspberry, Rose, Orange Blossom, Sea Salt / Base - Toffee, Praline, Vanilla, Musk", "category": ["Fruity", "Gourmand", "Floral"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Samiya", "brand": "Khadlaj", "gender": "Female", "season": "Versatile", "notes": "Top/Head Notes: Jasmine, Lily of the ValleyMiddle/Heart Notes: Amber, VioletBase Notes: Oud, Saffron, Sandalwood", "category": ["Floral", "Oriental"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Sceptre Malachite", "brand": "Maison Alhambra", "gender": "Unisex", "season": "Spring-Summer", "notes": "Top - Green tangerine, bergamot, blackcurrant / Heart - Aromatic + spicy notes, lavender, pink pepper, jasmine / Base - Amber, musk, woody notes, vetiver", "category": ["Fresh", "Aromatic", "Woody"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Sensual Vanilla", "brand": "Maison Alhambra", "gender": "Unisex", "season": "Fall, Winter", "notes": "Top Note: Bitter AlmondMiddle Notes: Vanilla, Floral NotesBase Notes: Vanilla Absolute, Tonka Bean, Sandalwood", "category": ["Oriental", "Gourmand"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Silver", "brand": "Al Rehab", "gender": "Unisex/Male", "season": "Spring, Summer", "notes": "Top - Fresh Citrus, Metallic / Heart - Floral / Base - Musk, Sweet", "category": ["Fresh", "Citrus"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Soft", "brand": "Al Rehab", "gender": "Unisex (leans feminine)", "season": "Fall, Winter", "notes": "Top - Citruses / Heart - Orchid, Jasmine, Vanilla, Caramel / Base - White Musk, Woody Notes, Vetiver", "category": ["Floral", "Sweet", "Gourmand"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Spectre Original", "brand": "French Avenue", "gender": "Male/Unisex (leans masculine)", "season": "Fall, Winter", "notes": "Top - Incense, Guaiac Wood, Saffron / Heart - Leather, Amberwood, Violet, Sugar Cane / Base - Smoke, Patchouli, Sandalwood, Woodsy Notes, Black Musk", "category": ["Woody", "Leather", "Oriental"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Strawberries & Cream", "brand": "Royal Apothic", "gender": "Female", "season": "Spring, summer", "notes": "Top Notes: Raspberry and plum (or juicy brightness like strawberry, raspberry, apple, and nectarine)Heart / Middle Notes: Strawberry and whipped creamBase Notes: Sugar cubes, caramel, tonka vanilla, and soft amber", "category": ["Gourmand"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Strawberry Tres Leches", "brand": "Arabiyat Sugar", "gender": "Female", "season": "Spring-Summer / year-round", "notes": "Top Notes: Strawberry, Milk, Nectarine, FreesiaHeart / Middle Notes: Marshmallow, Milk Candy, Caramel, Orange BlossomBase Notes: Vanilla, White Musk, Ambergris", "category": ["Gourmand", "Fruity", "Sweet"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Sugar Crown", "brand": "Lattafa", "gender": "Female/Unisex", "season": "Fall-Winter", "notes": "Top Notes: Bitter orange, lemon, and candied fruitsMiddle Notes (Heart): Bubble gum, blueberry, peach, peach blossom, Bulgarian rose, ginger, and cinnamonBase Notes: Ambroxan, musk, and cedar", "category": ["Gourmand", "Sweet"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Sugar Me Dulce De Leche", "brand": "Maison Alhambra", "gender": "Unisex/Female", "season": "Fall-Winter", "notes": "Dulce de leche / caramel-vanilla gourmand", "category": ["Gourmand", "Sweet"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Sugarcane Vanilla", "brand": "Arabiyat Prestige", "gender": "Unisex", "season": "Fall, Winter", "notes": "Top Notes: Raspberry, Cherry, MandarinMiddle/Heart Notes: Lactones (milky/creamy notes), Vanilla, White FlowersBase Notes: Sandalwood, Musk", "category": ["Sweet", "Gourmand", "Fruity", "Floral"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Supremacy Only Intense", "brand": "Afnan", "gender": "Male", "season": "Spring, autumn", "notes": "Top Notes: Black Currant, Bergamot, and AppleMiddle (Heart) Notes: Oakmoss, Patchouli, and LavenderBase Notes: Ambergris, Musk, and Saffron", "category": ["Woody", "Fruity", "Fresh"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Sweet Surrender", "brand": "Mahajan", "gender": "Female", "season": "Fall-Winter / versatile", "notes": "Top Note: CaramelMiddle Notes: Coumarin (sweet, vanilla-like scent) and HoneyBase Notes: White Musk and Vanilla", "category": ["Gourmand", "Sweet"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Sweet Surrender Pink Parfait", "brand": "Mahajan", "gender": "Female", "season": "Spring-Summer / year-round", "notes": "Top Notes: Graham Crackers, Marshmallow, Strawberry, Blackcurrant, and Chocolate (Strawberry S'mores)Middle (Heart) Notes: Marshmallow, Orange Blossom, and JasmineBase Notes: Vanilla, Whipped Cream, Sandalwood, Amber, and Musk", "category": ["Gourmand", "Fruity", "Sweet"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Tahira", "brand": "Riiffs", "gender": "Female", "season": "Versatile", "notes": "Top Notes: Almond and Dragon fruitMiddle (Heart) Notes: Rose de Mai, Gardenia, and Praline (often listed as Rose de Mai and Gardenia with praline accents in the blend)Base Notes: Vanilla Absolute, Tonka Bean, and Patchouli", "category": ["Floral", "Oriental"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Taif", "brand": "Riiffs", "gender": "Unisex", "season": "Versatile (Spring-Summer preferred)", "notes": "Top - Ginger, Calabrian Bergamot, Lemon, Orange Blossom / Heart - Musk, Rose Petals, Tuberose / Base - Vanilla Bean, Amberwood, Clearwood", "category": ["Floral", "Fresh", "Woody"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Teriaq", "brand": "Lattafa", "gender": "Unisex (leans feminine)", "season": "Fall, Winter", "notes": "Top - Caramel, Bitter Almond, Apricot, Pink Pepper / Heart - Honey, Rhubarb, White Flowers, Rose / Base - Leather, Vanilla, Musk, Vetiver, Labdanum", "category": ["Gourmand", "Floral", "Oriental"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Teriaq Intense", "brand": "Lattafa", "gender": "Unisex", "season": "Fall, Winter", "notes": "Top - Saffron, Bergamot / Heart - Plum Liquor, Cinnamon / Base - Amber, Tonka Bean, Benzoin", "category": ["Oriental", "Spicy", "Sweet"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "The King", "brand": "Ali", "gender": "Male", "season": "Fall-Winter / versatile", "notes": "Top Notes: Plum, Ozonic notes, Grapefruit, BergamotMiddle (Heart) Notes: Hazelnut, Honey, Cedar, Cashmere Wood, Orange Blossom, JasmineBase Notes: Amberwood, Patchouli, Oakmoss, Vetiver", "category": ["Woody", "Oriental"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Tiramisu Candy", "brand": "Rizz", "gender": "Female", "season": "Spring, Fall", "notes": "Top - Bergamot / Heart - Blackcurrant, Strawberry Milk / Base - Musk, Vanilla", "category": ["Gourmand", "Fruity", "Sweet"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Tiramisu Coco", "brand": "Zimaya", "gender": "Unisex", "season": "Fall, Winter", "notes": "Top Notes: Amaretto and CoffeeMiddle Notes: Ice cream, Biscuit, and VanillaBase Notes: Vanilla, Brown sugar, and Amber", "category": ["Gourmand", "Oriental"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Toffee Ganache", "brand": "Arabiyat Sugar", "gender": "Unisex", "season": "Fall-Winter", "notes": "Top Notes: Hazelnut, Clove, Milk (or Vanilla Cream), and VanillaMiddle (Heart) Notes: Cinnamon, Toffee, and White FlowersBase Notes: Gourmand Accord, Milk, Biscuit (Speculoos/Biscoff), and Spices", "category": ["Gourmand", "Sweet"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Tubbees Tres Leches", "brand": "Grandeur", "gender": "Unisex", "season": "Fall, winter", "notes": "Top Notes: Vanilla bean, cold milk accord, sweet notes, spicy notes, and caramelMiddle Notes (Heart): Milk, chocolate, and floral notes", "category": ["Gourmand", "Sweet"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Vanilla", "brand": "Bellavita", "gender": "Female", "season": "Fall, Winter", "notes": "Top - Aldehydes, Heliotrope, Coconut, Vanilla / Heart - Vanilla, Mango / Base - White Musk, Coconut, Vanilla Absolute", "category": ["Gourmand", "Sweet"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Vanilla Addiction", "brand": "Gulf Orchid", "gender": "Unisex/Female", "season": "Fall-Winter", "notes": "Top Notes: Coconut, Lavender, and Lily of the ValleyHeart (Middle) Notes: Tonka Bean, Jasmine, Rose, and PatchouliBase Notes: Vanilla, Amber, and Musk", "category": ["Gourmand", "Sweet"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Vanilla Aura", "brand": "Maison Asrar", "gender": "Female/Unisex", "season": "Fall, Winter", "notes": "Top - Vanilla / Heart - Creamy Sweet / Base - Vanilla, Musk", "category": ["Gourmand", "Sweet"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Vanilla Ayelet", "brand": "Khayali", "gender": "Unisex", "season": "Fall-Winter", "notes": "Vanilla orchid, jasmine / Brown sugar, tonka / Amber, musk, patchouli (Kayali-inspired)", "category": ["Gourmand", "Floral", "Sweet"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Vanilla Cream Macaron", "brand": "Arabiyat Sugar", "gender": "Unisex", "season": "Versatile", "notes": "Top Note: Ripe BananaMiddle Note: Chantilly CreamBase Note: Custard Sauce (or Vanilla/Vanilla Musk)", "category": ["Gourmand"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Vanilla Dunes", "brand": "Khadlaj", "gender": "Unisex", "season": "Autumn, Winter", "notes": "Top - Vanilla, Cinnamon, Cardamom, Bergamot / Heart - Orange Blossom, Guaiac Wood, Bourbon / Base - Praline, Amber, Musk", "category": ["Gourmand", "Spicy", "Woody"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Vanilla Freak (Give Me Gourmand)", "brand": "Lattafa", "gender": "Unisex / Female-leaning", "season": "Fall, Spring", "notes": "Top - Cupcake / Heart - Sugar Frosting, Almond, Cinnamon / Base - Butter, Vanilla, Musk", "category": ["Gourmand", "Sweet"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Vanilla Madness", "brand": "Mamlakat Al Oud", "gender": "Unisex (leans feminine)", "season": "Fall, Winter (versatile year-round)", "notes": "Top - Vanilla (woody tones), Lavender, Cacao, Ginger / Heart - Vanilla Caviar / Base - Vanilla Absolute", "category": ["Gourmand", "Sweet"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Vanilla Milkshake", "brand": "Snack House", "gender": "Unisex", "season": "Fall, winter", "notes": "Top Notes: Vanilla Orchid and JasmineMiddle (Heart) Notes: Brown Sugar and Tonka BeanBase Notes: Amber, Amberwood, Musk, and Patchouli", "category": ["Gourmand", "Oriental"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Vanilla Musk", "brand": "NatureWell", "gender": "Unisex", "season": "Fall, winter", "notes": "Top Notes: Sugared Petals & Mandarin MuskMid Notes: Vanilla Cream & SpiceBase Notes: Sleek Woods & Tonka", "category": ["Gourmand"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Vanilla Seduction", "brand": "Maison Asrar", "gender": "Female/Unisex", "season": "Fall, Winter", "notes": "Top - Plum, Jasmine, Lily of the Valley / Heart - Vanilla, Brown Sugar, Caramel / Base - Tonka, Patchouli, Amber, Musk", "category": ["Gourmand", "Floral", "Sweet"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Vanilla Skin", "brand": "Phlur", "gender": "Unisex (female-leaning)", "season": "Fall, Winter", "notes": "Top - Sugar, Pink Pepper, Apple / Heart - Cashmere Wood, Jasmine, Lily / Base - Vanilla, Sandalwood, Agarwood, Benzoin", "category": ["Gourmand", "Woody", "Sweet"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Velvet Breeze", "brand": "Mamlakat Al Oud", "gender": "Unisex", "season": "Fall, Winter", "notes": "Top - Italian Bergamot, Pistachio Gelato, Hazelnut, Sweet Rum, Cardamom / Heart - Geranium, White Peony, Muguet, Jasmine / Base - Amber, Musk, Woody Notes", "category": ["Gourmand", "Floral", "Woody"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Vulcan Baie", "brand": "French Avenue", "gender": "Unisex", "season": "Spring, Summer", "notes": "Top - Blackberry, Black Currant, Rosemary, Bergamot / Heart - Raspberry, Vodka, Basil, Lily of the Valley / Base - Strawberry, Musk, Peach, Amber, Sandalwood, Patchouli, Incense", "category": ["Fruity", "Fresh", "Aromatic"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Whipped Pleasure (Give Me Gourmand)", "brand": "Lattafa", "gender": "Female", "season": "Fall, Winter", "notes": "Top - Caramel, Popcorn, Salted Caramel / Heart - Milk, Jasmine / Base - Tonka, Benzoin, Musk, Ambrofix", "category": ["Gourmand", "Sweet"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Yara Candy Body Spray", "brand": "Lattafa", "gender": "Female", "season": "Fall, Winter", "notes": "Top - Candy, Sweet / Heart - Fruity / Base - Vanilla, Musk", "category": ["Gourmand", "Sweet", "Fruity"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Yara Elixir", "brand": "Lattafa", "gender": "Female", "season": "Fall, Winter, Cool Spring Days", "notes": "Top - Strawberry S'mores, Black Currant / Heart - Jasmine, Orange Blossom / Base - Vanilla, Caramel, Amber, Musk", "category": ["Gourmand", "Floral", "Sweet"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Yara Original", "brand": "Lattafa", "gender": "Female", "season": "Spring-Summer", "notes": "Top - Orchid, heliotrope, tangerine / Heart - Gourmand accord, tropical fruits / Base - Vanilla, musk, sandalwood", "category": ["Floral", "Gourmand", "Fruity"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Yara Tous", "brand": "Lattafa", "gender": "Female", "season": "Versatile", "notes": "Top - Fruity, Sweet / Heart - Floral / Base - Vanilla, Musk", "category": ["Floral", "Fruity", "Sweet"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Zainab Oil", "brand": "Khadlaj", "gender": "Unisex", "season": "Fall, Winter", "notes": "Top - Bergamot, Gardenia, Almond / Heart - Coconut, Caramel / Base - Patchouli, Vanilla, Musk", "category": ["Gourmand", "Floral", "Sweet"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Zenith", "brand": "Riiffs", "gender": "Unisex", "season": "Spring, summer, winter", "notes": "Top Notes: Coconut, Vanilla, Creamy AccordsHeart (Middle) Notes: Fruity Notes, Jasmine, Powdery AccordsBase Notes: Vanilla, Musk, Woody Notes", "category": ["Gourmand", "Sweet", "Powdery"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        {"name": "Zukhruf Pink", "brand": "Zimaya", "gender": "Unisex", "season": "Versatile", "notes": "Top Notes: Orchid, Heliotrope, and VanillaHeart (Middle) Notes: Musk, Marshmallow, and Almond MilkBase Notes: Amber, Vanilla, and Sandalwood", "category": ["Gourmand"], "dupe_of": "", "shelf_status": "Own", "size_ml": None, "price": None},
        ]


# ==========================================
# REACTIONS & SOTD (from persisted data)
# ==========================================
if "user_reactions" not in st.session_state:
    st.session_state["user_reactions"] = _persisted.get("user_reactions", {})

if "sotd_history" not in st.session_state:
    st.session_state["sotd_history"] = _persisted.get("sotd_history", [])

if "layer_recipes" not in st.session_state:
    st.session_state["layer_recipes"] = list(_persisted.get("layer_recipes") or [])
else:
    # Recover if session wiped recipes but disk still has them
    _disk_lr = list(_persisted.get("layer_recipes") or [])
    _sess_lr = st.session_state.get("layer_recipes") or []
    if len(_disk_lr) > len(_sess_lr):
        st.session_state["layer_recipes"] = _disk_lr

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

# --- Vault recovery: if disk has more bottles than this session, reload disk ---
# Protects against a bad run that emptied session_state without a real delete.
try:
    _disk_n = _vault_count(_persisted)
    _sess_n = len(st.session_state.get("fragrances_db") or [])
    if _disk_n > _sess_n and _disk_n >= 10:
        st.session_state["fragrances_db"] = list(_persisted.get("fragrances_db") or [])
        if _persisted.get("user_reactions") is not None:
            st.session_state["user_reactions"] = _persisted.get("user_reactions") or st.session_state.get("user_reactions") or {}
        if _persisted.get("sotd_history") is not None and len(_persisted.get("sotd_history") or []) > len(st.session_state.get("sotd_history") or []):
            st.session_state["sotd_history"] = list(_persisted.get("sotd_history") or [])
        if _persisted.get("layer_recipes") is not None and len(_persisted.get("layer_recipes") or []) > len(st.session_state.get("layer_recipes") or []):
            st.session_state["layer_recipes"] = list(_persisted.get("layer_recipes") or [])
        if _persisted.get("wishlist") is not None and len(_persisted.get("wishlist") or []) > len(st.session_state.get("wishlist") or []):
            st.session_state["wishlist"] = list(_persisted.get("wishlist") or [])
        st.session_state["_vault_recovered"] = (
            f"Restored **{_disk_n}** bottles from disk (session had {_sess_n})."
        )
except Exception:
    pass

# Snapshot vault after all loads  -  any later mutation this run triggers autosave
try:
    st.session_state["_vault_fp_run_start"] = vault_fingerprint()
except Exception:
    st.session_state["_vault_fp_run_start"] = ""
st.session_state.setdefault("_vault_dirty", False)

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
if "chart_his_sun" not in st.session_state and _chart.get("his_sun"):
    st.session_state["chart_his_sun"] = _chart["his_sun"]
if "chart_his_moon" not in st.session_state and _chart.get("his_moon"):
    st.session_state["chart_his_moon"] = _chart["his_moon"]
if "chart_his_rising" not in st.session_state and _chart.get("his_rising"):
    st.session_state["chart_his_rising"] = _chart["his_rising"]
if "chart_his_venus" not in st.session_state and _chart.get("his_venus"):
    st.session_state["chart_his_venus"] = _chart["his_venus"]
if "birth_calc_his_full" not in st.session_state and _chart.get("his_full"):
    st.session_state["birth_calc_his_full"] = _chart["his_full"]


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
    Caches a successful reading for 20 minutes to avoid HTTP 429 rate limits.
    """
    import json as _json
    import time as _time
    import urllib.error
    import urllib.request

    # Reuse a recent successful reading (cuts 429s from repeated taps / reruns)
    cache = st.session_state.get("_live_temp_cache") or {}
    age = _time.time() - float(cache.get("ts") or 0)
    if cache.get("ok") and age < 20 * 60:
        out = dict(cache)
        out["detail"] = (out.get("detail") or "") + f" (cached {int(age)}s ago)"
        return out

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
        result = {
            "ok": True,
            "temp_f": temp_f,
            "source": "Open-Meteo",
            "detail": f"Victorville area ({lat:.2f}, {lon:.2f})",
            "observed": cur.get("time"),
            "ts": _time.time(),
        }
        st.session_state["_live_temp_cache"] = result
        return result
    except urllib.error.HTTPError as ex:
        if ex.code == 429:
            if cache.get("ok") and cache.get("temp_f") is not None:
                out = dict(cache)
                out["detail"] = "Rate-limited; using last live reading"
                return out
            return {
                "ok": False,
                "detail": "HTTP 429 Too Many Requests  -  wait a few minutes, or use the slider",
            }
        return {"ok": False, "detail": f"HTTP Error {ex.code}: {ex.reason}"}
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



def matches_category(fragrance: dict, category) -> bool:
    """category: 'Any', a single str, or a list of category names."""
    if not category or category == "Any":
        return True
    cats = fragrance.get("category") or []
    if isinstance(category, (list, tuple, set)):
        wanted = [c for c in category if c and c != "Any"]
        if not wanted:
            return True
        return any(c in cats for c in wanted)
    return category in cats


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

    if not category or category == "Any":
        score += 5
    elif isinstance(category, (list, tuple, set)):
        wanted = [c for c in category if c and c != "Any"]
        if not wanted:
            score += 5
        else:
            hits = sum(1 for c in wanted if c in cats)
            if hits:
                score += 12 + min(hits, 3) * 4
                if cats and cats[0] in wanted:
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



def _recent_shown(bucket: str, limit: int = 24) -> set:
    """Names recently shown in a UI bucket (play / recommend / layer)."""
    key = f"_recent_shown_{bucket}"
    lst = st.session_state.get(key) or []
    return set(lst[:limit])


def _remember_shown(bucket: str, names: list, limit: int = 40) -> None:
    key = f"_recent_shown_{bucket}"
    prev = list(st.session_state.get(key) or [])
    for n in reversed(list(names or [])):
        if not n:
            continue
        if n in prev:
            prev.remove(n)
        prev.insert(0, n)
    st.session_state[key] = prev[:limit]


def _diversify_scored(
    scored: list,
    top_n: int,
    recent: set = None,
    strength: float = 12.0,
) -> list:
    """Pick top_n from (score, frag) list with brand diversity and recent penalty."""
    if not scored:
        return []
    recent = recent or set()
    # scored items may be (score, f) or already just f - normalize
    items = []
    for row in scored:
        if isinstance(row, tuple) and len(row) >= 2:
            items.append((float(row[0]), row[1]))
        else:
            items.append((0.0, row))
    picks = []
    used_brands = set()
    used_names = set()
    pool = list(items)
    while len(picks) < top_n and pool:
        best_i = None
        best_adj = None
        for i, (s, f) in enumerate(pool):
            name = f.get("name") or ""
            brand = (f.get("brand") or "").strip().lower()
            adj = s
            if name in recent:
                adj -= strength
            if brand and brand in used_brands:
                adj -= strength * 0.75
            # light random jitter so ties and near-ties rotate
            adj += random.random() * 4.0
            if best_adj is None or adj > best_adj:
                best_adj = adj
                best_i = i
        if best_i is None:
            break
        s, f = pool.pop(best_i)
        name = f.get("name") or ""
        if name in used_names:
            continue
        used_names.add(name)
        brand = (f.get("brand") or "").strip().lower()
        if brand:
            used_brands.add(brand)
        picks.append(f)
    return picks


def suggest_seasons_from_notes(notes: str, categories: list = None) -> list:
    """Suggest season tags from notes + categories."""
    text = (notes or "").lower()
    cats = set(categories or [])
    scores = {
        "Spring": 0,
        "Summer": 0,
        "Fall": 0,
        "Winter": 0,
    }
    # category signals
    for c in cats:
        cl = c.lower()
        if cl in ("fresh", "citrus", "aquatic", "green", "fruity"):
            scores["Spring"] += 2
            scores["Summer"] += 3
        if cl in ("floral", "powdery", "musky"):
            scores["Spring"] += 2
            scores["Summer"] += 1
        if cl in ("gourmand", "sweet", "vanilla", "creamy", "spicy"):
            scores["Fall"] += 2
            scores["Winter"] += 2
        if cl in ("oriental", "oud", "smoky", "leather", "woody", "amber"):
            scores["Fall"] += 2
            scores["Winter"] += 3
    # note keywords
    hot = ["citrus", "bergamot", "lemon", "grapefruit", "aquatic", "ozone", "coconut",
           "pineapple", "mango", "mint", "green tea", "neroli"]
    warm = ["rose", "jasmine", "peony", "pear", "apple", "peach", "freesia"]
    cool = ["cinnamon", "apple", "pear", "cedar", "violet", "iris", "spice"]
    cold = ["vanilla", "amber", "oud", "incense", "leather", "tobacco", "tonka",
            "caramel", "chocolate", "coffee", "benzoin", "myrrh", "patchouli"]
    for k in hot:
        if k in text:
            scores["Summer"] += 2
            scores["Spring"] += 1
    for k in warm:
        if k in text:
            scores["Spring"] += 2
            scores["Summer"] += 1
    for k in cool:
        if k in text:
            scores["Fall"] += 2
    for k in cold:
        if k in text:
            scores["Winter"] += 2
            scores["Fall"] += 1
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    if not ranked or ranked[0][1] <= 0:
        return ["Versatile"]
    top = ranked[0][1]
    chosen = [s for s, v in ranked if v >= max(1, top - 1) and v > 0]
    # map to common vault labels
    if set(chosen) >= {"Summer", "Spring"} and len(chosen) == 2:
        return ["Spring, Summer"]
    if set(chosen) >= {"Fall", "Winter"} and len(chosen) == 2:
        return ["Fall, Winter"]
    if chosen == ["Summer"]:
        return ["Summer"]
    if chosen == ["Winter"]:
        return ["Winter"]
    if chosen == ["Spring"]:
        return ["Spring"]
    if chosen == ["Fall"]:
        return ["Fall"]
    return [", ".join(chosen[:2])]


def get_top_fragrances(
    gender: str,
    weather: str,
    category: str,
    occasion: str,
    top_n: int,
    favorites_only: bool = False,
    temp_f=None,
    shuffle: bool = False,
    exclude_names: list = None,
    concentration: str = "Any",
) -> list:
    # If a real temperature is provided, derive the weather band when set to Any
    effective_weather = weather
    if temp_f is not None and (not weather or weather == "Any"):
        effective_weather = temp_f_to_band(float(temp_f))

    exclude = set(exclude_names or [])
    scored = []
    for f in st.session_state["fragrances_db"]:
        if f.get("name") in exclude:
            continue
        if st.session_state["user_reactions"].get(f["name"]) == "dislike":
            continue
        if favorites_only and st.session_state["user_reactions"].get(f["name"]) != "fav":
            continue
        if concentration and concentration != "Any":
            fc = (f.get("concentration") or "").strip()
            if concentration == "Concentrated oil":
                if "oil" not in fc.lower():
                    continue
            elif concentration == "Spray only":
                if "oil" in fc.lower():
                    continue
            elif fc != concentration:
                # allow empty as EDP default when filtering EDP
                if concentration == "EDP" and not fc:
                    pass
                else:
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

    if not scored:
        return []

    # Always pull from a wider pool + brand/recent diversity (not the same top 3)
    recent = _recent_shown("recommend")
    # Soft-exclude recent SOTD wears
    try:
        for entry in (st.session_state.get("sotd_history") or [])[:8]:
            for n in entry.get("scents") or []:
                recent.add(n)
            if entry.get("scent") and not entry.get("scents"):
                for part in str(entry["scent"]).split(" + "):
                    recent.add(part.strip())
    except Exception:
        pass

    pool_size = min(len(scored), max(top_n * 5, top_n + 12))
    pool = scored[:pool_size]
    if shuffle:
        random.shuffle(pool)
        pool = [(s + random.random() * 8.0, f) for s, f in pool]
        pool.sort(key=lambda x: x[0], reverse=True)
    else:
        # Light jitter even on first Generate so ranking is not frozen
        pool = [(s + random.random() * 3.5, f) for s, f in pool]
        pool.sort(key=lambda x: x[0], reverse=True)

    picks = _diversify_scored(pool, top_n, recent=recent, strength=14.0)
    _remember_shown("recommend", [f.get("name") for f in picks])
    return picks



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



def bottles_for_sign(sign: str, top_n: int = 5) -> list:
    """Rank vault bottles for a zodiac sign scent profile."""
    prof = SIGN_SCENT_PROFILE.get(sign) or {}
    prefer_cats = set(prof.get("categories") or [])
    prefer_notes = [k.lower() for k in (prof.get("notes_keywords") or [])]
    scored = []
    for f in st.session_state.get("fragrances_db") or []:
        if st.session_state.get("user_reactions", {}).get(f.get("name")) == "dislike":
            continue
        cats = set(f.get("category") or [])
        notes = (f.get("notes") or "").lower()
        score = 1 + 4 * len(cats & prefer_cats)
        score += sum(3 for kw in prefer_notes if kw in notes)
        if st.session_state.get("user_reactions", {}).get(f.get("name")) == "fav":
            score += 5
        scored.append((score, f))
    scored.sort(key=lambda x: -x[0])
    return [f for _, f in scored[:top_n]]


def bottles_for_element(element: str, top_n: int = 5) -> list:
    element = (element or "").title()
    elem_map = {
        "Fire": ["Spicy", "Oriental", "Citrus", "Woody"],
        "Earth": ["Gourmand", "Woody", "Sweet", "Musky", "Vanilla"],
        "Air": ["Fresh", "Floral", "Powdery", "Citrus", "Aromatic"],
        "Water": ["Floral", "Aquatic", "Sweet", "Musky", "Oriental"],
    }
    prefer = set(elem_map.get(element, []))
    scored = []
    for f in st.session_state.get("fragrances_db") or []:
        cats = set(f.get("category") or [])
        score = 1 + 5 * len(cats & prefer)
        scored.append((score, f))
    scored.sort(key=lambda x: -x[0])
    return [f for _, f in scored[:top_n]]


def moon_phase_name(d=None) -> str:
    """Approximate moon phase name for a date (Pacific today if None)."""
    from datetime import date
    d = d or pacific_today()
    # simple known new moon reference approx cycle 29.53 days
    # ref: 2000-01-06 was near new moon
    ref = date(2000, 1, 6)
    age = (d - ref).days % 29.53058867
    if age < 1.85:
        return "New Moon"
    if age < 7.38:
        return "Waxing Crescent"
    if age < 9.23:
        return "First Quarter"
    if age < 14.77:
        return "Waxing Gibbous"
    if age < 16.61:
        return "Full Moon"
    if age < 22.15:
        return "Waning Gibbous"
    if age < 23.99:
        return "Last Quarter"
    return "Waning Crescent"


def moon_phase_scent_profile(phase: str) -> dict:
    phase = phase or ""
    if "New" in phase:
        return {
            "blurb": "Soft reset - skin scents, clean musk, quiet florals.",
            "categories": ["Musky", "Fresh", "Floral", "Powdery"],
        }
    if "Full" in phase:
        return {
            "blurb": "High volume - projection, spice, oud, date-night intensity.",
            "categories": ["Oriental", "Spicy", "Oud", "Gourmand", "Leather"],
        }
    if "Waxing" in phase:
        return {
            "blurb": "Building energy - fruity, sweet, bright florals.",
            "categories": ["Fruity", "Sweet", "Floral", "Gourmand"],
        }
    if "Waning" in phase or "Last" in phase:
        return {
            "blurb": "Release - woody, green, incense, less sugar.",
            "categories": ["Woody", "Green", "Smoky", "Aromatic", "Fresh"],
        }
    return {
        "blurb": "Balanced middle path.",
        "categories": ["Floral", "Woody", "Musky"],
    }


def bottles_for_moon_phase(phase: str = None, top_n: int = 5) -> list:
    phase = phase or moon_phase_name()
    prof = moon_phase_scent_profile(phase)
    prefer = set(prof.get("categories") or [])
    scored = []
    for f in st.session_state.get("fragrances_db") or []:
        cats = set(f.get("category") or [])
        score = 1 + 5 * len(cats & prefer)
        scored.append((score, f))
    scored.sort(key=lambda x: -x[0])
    return [f for _, f in scored[:top_n]]


def chart_elements(sun, moon, rising, venus=None) -> dict:
    from collections import Counter
    c = Counter()
    for sign in (sun, moon, rising, venus):
        if not sign:
            continue
        el = (SIGN_SCENT_PROFILE.get(sign) or {}).get("element")
        if el:
            c[el] += 1
    return dict(c)


def compatibility_blurb(her: dict, him: dict) -> str:
    """Fun scent-compatibility text from two charts."""
    bits = []
    hs, hm, hr, hv = her.get("sun"), her.get("moon"), her.get("rising"), her.get("venus")
    xs, xm, xr, xv = him.get("sun"), him.get("moon"), him.get("rising"), him.get("venus")
    if hs and xs:
        he = (SIGN_SCENT_PROFILE.get(hs) or {}).get("element")
        xe = (SIGN_SCENT_PROFILE.get(xs) or {}).get("element")
        if he and xe:
            if he == xe:
                bits.append(f"Same firepower element ({he}) on the Suns - layer shared families.")
            else:
                bits.append(f"Sun elements {he} + {xe} - contrast layers (his strength, your softness or reverse).")
    if hm and xm:
        bits.append(f"Moon {hm} meets Moon {xm} - comfort scents should overlap at least one family.")
    if hv and xv:
        bits.append(f"Venus {hv} + Venus {xv} - date-night blend lives here.")
    if hr and xr:
        bits.append(f"Rising {hr} / {xr} - first-impression scents when you walk in together.")
    if not bits:
        bits.append("Set both charts to unlock a fuller match read.")
    return " ".join(bits)


def compatibility_bottles(her: dict, him: dict, top_n: int = 4) -> list:
    """Bottles that bridge both charts."""
    signs = [her.get("sun"), her.get("venus"), him.get("sun"), him.get("venus"),
             her.get("moon"), him.get("moon")]
    prefer = set()
    for s in signs:
        if s:
            prefer |= set((SIGN_SCENT_PROFILE.get(s) or {}).get("categories") or [])
    scored = []
    for f in st.session_state.get("fragrances_db") or []:
        cats = set(f.get("category") or [])
        score = 1 + 3 * len(cats & prefer)
        scored.append((score, f))
    scored.sort(key=lambda x: -x[0])
    picks = []
    seen = set()
    for sc, f in scored:
        b = (f.get("brand") or "").lower()
        if b in seen:
            continue
        picks.append(f)
        seen.add(b)
        if len(picks) >= top_n:
            break
    return picks


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


def _note_tokens(f: dict) -> set:
    raw = (f.get("notes") or "").lower()
    toks = set(re.findall(r"[a-z]{3,}", raw))
    stop = {
        "top", "heart", "base", "and", "with", "notes", "the", "from", "for",
        "into", "style", "absolute", "oil", "extract", "leaning",
    }
    return {t for t in toks if t not in stop}


# Note families that play well / clash when layering
_NOTE_SYNERGY = [
    ({"vanilla", "caramel", "tonka", "praline", "marshmallow", "sugar"}, 8),
    ({"rose", "oud", "saffron", "amber", "patchouli"}, 8),
    ({"coffee", "cocoa", "chocolate", "almond", "tonka"}, 7),
    ({"coconut", "vanilla", "tiare", "pineapple", "mango"}, 7),
    ({"citrus", "bergamot", "lemon", "orange", "grapefruit", "mandarin"}, 6),
    ({"lavender", "mint", "aromatic", "herbal"}, 6),
    ({"leather", "tobacco", "smoke", "incense", "oud"}, 7),
    ({"iris", "violet", "powdery", "musk"}, 6),
    ({"cedar", "sandalwood", "vetiver", "wood", "woody"}, 6),
]
_NOTE_CLASH = [
    ({"citrus", "bergamot", "lemon"}, {"vanilla", "caramel", "chocolate", "cocoa"}, -4),
    ({"aquatic", "marine", "ozonic"}, {"oud", "incense", "tobacco"}, -5),
    ({"mint", "green"}, {"caramel", "praline", "marshmallow"}, -3),
]


def layer_score(f1: dict, f2: dict) -> int:
    if f1["name"] == f2["name"]:
        return -100
    if (
        st.session_state["user_reactions"].get(f1["name"]) == "dislike"
        or st.session_state["user_reactions"].get(f2["name"]) == "dislike"
    ):
        return -100

    cats1 = set(f1.get("category") or [])
    cats2 = set(f2.get("category") or [])
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

    # Notes-based synergy
    n1 = _note_tokens(f1)
    n2 = _note_tokens(f2)
    shared = n1 & n2
    if shared:
        score += min(12, 3 * len(shared))
    for family, pts in _NOTE_SYNERGY:
        if (n1 & family) and (n2 & family):
            score += pts
        elif (n1 & family) and (n2 - family) and (cats2 & {"Gourmand", "Sweet", "Woody", "Oriental", "Fresh"}):
            # bridge note on one side still helps a little
            score += max(2, pts // 3)
    for fam_a, fam_b, pen in _NOTE_CLASH:
        if (n1 & fam_a and n2 & fam_b) or (n2 & fam_a and n1 & fam_b):
            score += pen

    # Weight balance: reward clear heavy + light (better layering stack)
    w1 = fragrance_weight_score(f1)
    w2 = fragrance_weight_score(f2)
    gap = abs(w1 - w2)
    if gap >= 25:
        score += 12  # clear base vs top
    elif gap >= 15:
        score += 8
    elif gap >= 8:
        score += 4
    else:
        score -= 6  # two similar weights can muddle / fight for space

    # Soft penalty when both are very heavy
    if w1 >= 80 and w2 >= 80:
        score -= 10
    # Soft penalty when both are very light (nothing anchors)
    if w1 <= 40 and w2 <= 40:
        score -= 6

    # Stable-ish variation from names
    score += _stable_tiebreak(f1["name"] + f2["name"]) % 5 + 1
    return score


def layer_note_reasons(f1: dict, f2: dict) -> list:
    """Human-readable why this layer works or struggles."""
    reasons = []
    n1, n2 = _note_tokens(f1), _note_tokens(f2)
    shared = sorted(n1 & n2)
    if shared:
        reasons.append("Shared notes: " + ", ".join(shared[:8]))
    for family, pts in _NOTE_SYNERGY:
        a = sorted(n1 & family)
        b = sorted(n2 & family)
        if a and b:
            reasons.append(
                f"Synergy ({', '.join(list(family)[:3])}): "
                f"{f1.get('name')} has {', '.join(a[:3])}; "
                f"{f2.get('name')} has {', '.join(b[:3])}"
            )
    for fam_a, fam_b, _pen in _NOTE_CLASH:
        if (n1 & fam_a and n2 & fam_b) or (n2 & fam_a and n1 & fam_b):
            reasons.append(
                "Possible tension between "
                + "/".join(sorted(fam_a)[:2])
                + " and "
                + "/".join(sorted(fam_b)[:2])
            )
    c1 = set(f1.get("category") or [])
    c2 = set(f2.get("category") or [])
    if c1 & c2:
        reasons.append("Overlapping families: " + ", ".join(sorted(c1 & c2)))
    for a, b in GOOD_LAYER_PAIRS:
        if (a in c1 and b in c2) or (b in c1 and a in c2):
            reasons.append(f"Classic pair: {a} + {b}")
    if not reasons:
        reasons.append("No strong note overlap - rely on category contrast or skin test.")
    return reasons[:8]


def suggest_recipe_name_from_notes(bottle_names: list, *, randomize: bool = True) -> str:
    """Build a short recipe name from real notes/categories on the bottles.

    Prefers notes that appear on more than one bottle, then strong single-bottle
    notes. When randomize=True, shuffles words and templates so each check/reroll
    can produce a different name that still matches the juice.
    """
    name_map = {f["name"]: f for f in st.session_state.get("fragrances_db") or []}
    frags = [name_map[n] for n in bottle_names if n in name_map]
    if not frags:
        return "Untitled layer"

    stop = {
        "top", "heart", "base", "and", "with", "notes", "the", "from", "leaning",
        "style", "absolute", "extract", "oil", "of", "a", "an", "for", "into",
        "accord", "bean", "beans", "wood", "woods", "note", "notes", "blend",
        "composition", "fragrance", "perfume", "edp", "edt", "extrait",
        "sweet", "creamy", "warm", "dark", "light", "rich", "soft", "fresh",
        "opening", "drydown", "dry", "down", "middle", "hint", "hints", "touch",
        "touches", "whiff", "trace", "traces", "like", "very", "slightly",
    }

    # Known note words we prefer (must actually appear in notes/cats)
    preferred = [
        "Vanilla", "Coconut", "Rose", "Oud", "Amber", "Musk", "Coffee", "Caramel",
        "Jasmine", "Sandalwood", "Cherry", "Cocoa", "Tobacco", "Leather", "Iris",
        "Peach", "Honey", "Smoke", "Citrus", "Marshmallow", "Pistachio", "Tonka",
        "Praline", "Saffron", "Patchouli", "Bergamot", "Lavender", "Cedar",
        "Almond", "Strawberry", "Raspberry", "Pineapple", "Mango", "Violet",
        "Incense", "Benzoin", "Cashmere", "Orchid", "Tuberose", "Cardamom",
        "Mandarin", "Orange", "Lemon", "Grapefruit", "Pear", "Apple", "Fig",
        "Chocolate", "Caramel", "Sugar", "Cream", "Milk", "Tonka", "Benzoin",
        "Myrrh", "Frankincense", "Vetiver", "Oakmoss", "Geranium", "Ylang",
        "Gardenia", "Peony", "Lilac", "Magnolia", "Neroli", "Orange Blossom",
        "Blackcurrant", "Plum", "Date", "Praline", "Hazelnut", "Chestnut",
        "Cinnamon", "Clove", "Nutmeg", "Pepper", "Ginger", "Saffron",
        "Leather", "Suede", "Incense", "Smoke", "Tobacco", "Rum", "Whiskey",
    ]

    # Count note tokens across bottles
    from collections import Counter
    per_bottle = []
    global_counts = Counter()
    for f in frags:
        raw = (f.get("notes") or "") + " " + " ".join(f.get("category") or [])
        tokens = re.findall(r"[A-Za-z][A-Za-z\-]{2,}", raw)
        bottle_set = set()
        for t in tokens:
            tl = t.lower().replace("-", " ")
            if tl in stop or len(tl) < 3:
                continue
            bottle_set.add(tl)
        per_bottle.append(bottle_set)
        for t in bottle_set:
            global_counts[t] += 1

    # Shared notes (in 2+ bottles) rank highest
    shared = [t for t, c in global_counts.items() if c >= 2]
    # Map preferred list to what actually appears
    def title_note(n: str) -> str:
        for p in preferred:
            if p.lower() == n or p.lower().replace(" ", "") == n.replace(" ", ""):
                return p
        return n.title()

    ranked = []
    # 1) preferred words that are shared
    for p in preferred:
        pl = p.lower()
        if any(pl == s or pl in s or s in pl for s in shared):
            ranked.append(p)
    # 2) other shared tokens
    for s in shared:
        tn = title_note(s)
        if tn not in ranked and s not in stop:
            ranked.append(tn)
    # 3) preferred words that appear on at least one bottle
    for p in preferred:
        pl = p.lower()
        if p in ranked:
            continue
        if any(pl == t or pl in t or t in pl for t in global_counts):
            ranked.append(p)
    # 4) remaining frequent tokens
    for t, c in global_counts.most_common(12):
        tn = title_note(t)
        if tn not in ranked and t not in stop:
            ranked.append(tn)

    # Dedupe case-insensitive
    seen = set()
    picks = []
    for p in ranked:
        k = p.lower()
        if k in seen:
            continue
        seen.add(k)
        picks.append(p)

    if not picks:
        short = [n.split()[0] for n in bottle_names[:2] if n]
        if len(short) >= 2:
            return f"{short[0]} x {short[1]}"
        return bottle_names[0] if bottle_names else "Untitled layer"

    # Gender-aware templates (still filled with real note words)
    try:
        g = recipe_gender_from_frags(frags)
    except Exception:
        g = "Any"

    templates_female_two = [
        "{a} {b} veil",
        "Soft {a} {b}",
        "{a} {b} glow",
        "{a} {b} silk",
        "{a} {b} bloom",
        "{a} & {b} dusk",
        "Quiet {a} {b}",
        "{a} {b} haze",
        "{a} over {b}",
        "{a} {b} whisper",
        "Gilded {a} {b}",
        "{a} {b} night",
    ]
    templates_female_one = [
        "Soft {a}",
        "{a} veil",
        "Candlelit {a}",
        "{a} bloom",
        "Quiet {a}",
        "{a} silk",
        "Gilded {a}",
        "{a} glow",
        "Sanctuary {a}",
        "{a} dusk",
    ]
    templates_male_two = [
        "{a} {b} grit",
        "{a} x {b}",
        "{a} {b} smoke",
        "{a} {b} oak",
        "{a} & {b}",
        "{a} over {b}",
        "{a} {b} resin",
        "{a} {b} night",
        "{a} {b} ember",
        "{a} {b} steel",
        "{a} {b} trail",
        "{a} {b} forge",
    ]
    templates_male_one = [
        "{a} smoke",
        "{a} grit",
        "Midnight {a}",
        "{a} oak",
        "{a} resin",
        "{a} trail",
        "{a} ember",
        "Black {a}",
        "{a} steel",
        "{a} night",
    ]
    templates_uni_two = [
        "{a} {b} balance",
        "{a} x {b}",
        "{a} & {b}",
        "{a} {b} shared",
        "{a} over {b}",
        "{a} {b} air",
        "{a} {b} pulse",
        "{a} {b} layer",
        "{a} {b} blend",
        "{a} with {b}",
        "{a} {b} code",
        "{a} {b} signal",
    ]
    templates_uni_one = [
        "{a} balance",
        "{a} signal",
        "{a} pulse",
        "Shared {a}",
        "{a} layer",
        "{a} air",
        "{a} code",
        "Open {a}",
        "{a} blend",
        "{a} line",
    ]

    if g == "Male":
        templates_two, templates_one = templates_male_two, templates_male_one
    elif g == "Female":
        templates_two, templates_one = templates_female_two, templates_female_one
    else:
        templates_two, templates_one = templates_uni_two, templates_uni_one

    if randomize:
        random.shuffle(picks)
        pool = picks[: max(4, min(8, len(picks)))]
        a = random.choice(pool)
        rest = [p for p in pool if p.lower() != a.lower()]
        if rest and random.random() < 0.75:
            b = random.choice(rest)
            tmpl = random.choice(templates_two)
            return tmpl.format(a=a, b=b)
        tmpl = random.choice(templates_one)
        return tmpl.format(a=a)

    a = picks[0]
    b = picks[1] if len(picks) > 1 else None
    if b:
        return templates_two[0].format(a=a, b=b)
    return templates_one[0].format(a=a)



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




def recipes_for_band(band: str, gender: str = "Any", limit: int = 5) -> list:
    """Saved layer recipes that fit a temp/season band."""
    band = (band or "").strip()
    if not band or band == "Any":
        return list(st.session_state.get("layer_recipes") or [])[:limit]
    out = []
    for recipe in st.session_state.get("layer_recipes") or []:
        bands = recipe.get("bands") or []
        label = (recipe.get("season_label") or "").lower()
        # rebuild if missing
        if not bands:
            names = recipe.get("bottles") or []
            name_map = {f.get("name"): f for f in st.session_state.get("fragrances_db") or []}
            frags = [name_map[n] for n in names if n in name_map]
            if frags:
                season = season_for_layer_recipe(frags)
                bands = season.get("bands") or []
                label = (season.get("label") or label or "").lower()
        band_l = band.lower()
        matched = False
        for b in bands:
            if band_l in (b or "").lower() or (b or "").lower() in band_l:
                matched = True
                break
        if not matched and label:
            # partial: Hot matches Hot / Summer label
            key = band_l.split("/")[0].strip()
            if key and key in label:
                matched = True
        if not matched:
            # versatile recipes work mild/warm
            if "versatile" in label and band in ("Warm / Mild", "Hot / Summer", "Cool / Autumn"):
                matched = True
        if not matched:
            continue
        # Prefer explicit recipe gender tag when set
        rg = (recipe.get("gender") or "Any")
        if gender and gender != "Any" and rg not in ("Any", "", gender):
            continue
        # optional gender: all bottles should roughly match
        if gender and gender != "Any":
            name_map = {f.get("name"): f for f in st.session_state.get("fragrances_db") or []}
            ok = True
            for n in recipe.get("bottles") or []:
                f = name_map.get(n)
                if not f:
                    continue
                try:
                    if not matches_gender(f, gender):
                        ok = False
                        break
                except Exception:
                    g = (f.get("gender") or "").lower()
                    if gender.lower() == "female" and not any(
                        x in g for x in ("female", "feminine", "women", "unisex")
                    ):
                        ok = False
                        break
                    if gender.lower() == "male" and not any(
                        x in g for x in ("male", "masculine", "men", "unisex")
                    ):
                        ok = False
                        break
            if not ok:
                continue
        out.append(recipe)
        if len(out) >= limit:
            break
    return out



def fragrance_weight_score(f: dict) -> int:
    """Higher = heavier / denser on skin (apply earlier as base)."""
    cats = set(f.get("category") or [])
    notes = (f.get("notes") or "").lower()
    name = (f.get("name") or "").lower()
    score = 50
    heavy_cats = {"Oriental", "Oud", "Leather", "Smoky", "Woody", "Gourmand", "Amber", "Boozy"}
    light_cats = {"Fresh", "Citrus", "Aquatic", "Green", "Aromatic"}
    mid_cats = {"Floral", "Fruity", "Powdery", "Musky", "Sweet", "Spicy", "Vanilla", "Creamy"}
    score += 12 * len(cats & heavy_cats)
    score -= 12 * len(cats & light_cats)
    score += 4 * len(cats & mid_cats)
    heavy_kw = [
        "oud", "incense", "leather", "tobacco", "amber", "vanilla", "caramel",
        "chocolate", "coffee", "smoke", "patchouli", "myrrh", "tonka", "benzoin",
        "labdanum", "resin", "boozy", "rum", "cedar", "sandalwood",
    ]
    light_kw = [
        "citrus", "bergamot", "lemon", "fresh", "aquatic", "marine", "green",
        "tea", "mint", "ozonic", "light", "airy", "cucumber",
    ]
    score += sum(6 for k in heavy_kw if k in notes or k in name)
    score -= sum(6 for k in light_kw if k in notes or k in name)
    # body spray / mist often lighter
    if any(x in name for x in ("body spray", "mist", "cologne", "hair")):
        score -= 15
    if any(x in name for x in ("intense", "elixir", "extrait", "concentre", "concentre")):
        score += 10
    return score


def order_frags_heavy_to_light(frags: list) -> list:
    """Sort fragrances heaviest first (apply as base first)."""
    return sorted(
        frags,
        key=lambda f: (fragrance_weight_score(f), f.get("name") or ""),
        reverse=True,
    )


def order_names_heavy_to_light(bottle_names: list) -> list:
    """Reorder bottle name list heavy -> light using vault data."""
    name_map = {f.get("name"): f for f in st.session_state.get("fragrances_db") or []}
    frags = [name_map[n] for n in bottle_names if n in name_map]
    ranked = order_frags_heavy_to_light(frags)
    ordered = [f.get("name") for f in ranked if f.get("name")]
    # keep any unknown names at end
    for n in bottle_names:
        if n not in ordered:
            ordered.append(n)
    return ordered


def layer_application_guide(frags: list) -> dict:
    """Order, sprays, placement for a multi-bottle layer."""
    if not frags:
        return {}
    ranked = sorted(
        frags,
        key=lambda f: (fragrance_weight_score(f), f.get("name") or ""),
        reverse=True,
    )
    n = len(ranked)
    # sprays: heavier gets fewer if very heavy; lighter can take slightly more
    steps = []
    total_sprays = 0
    for i, f in enumerate(ranked):
        w = fragrance_weight_score(f)
        if w >= 85:
            sprays = 1 if n >= 3 else 2
            role = "Heaviest base"
            where = "Skin first - chest and behind knees (warm spots). Let it settle 30-60 sec."
        elif w >= 65:
            sprays = 2
            role = "Base / heart"
            where = "Pulse points - wrists, inner elbows, neck. Do not rub."
        elif w >= 45:
            sprays = 2
            role = "Mid layer"
            where = "Neck and collarbone, or one spray through hair mist-style from a distance."
        else:
            sprays = 2 if n <= 2 else 1
            role = "Light top"
            where = "Last - throat, hair, or clothing hem for a soft trail."
        total_sprays += sprays
        steps.append(
            {
                "order": i + 1,
                "name": f.get("name"),
                "brand": f.get("brand"),
                "weight": w,
                "role": role,
                "sprays": sprays,
                "where": where,
                "cats": ", ".join((f.get("category") or [])[:4]),
            }
        )
    tips = [
        "Apply heaviest first, lightest last so the top notes stay bright.",
        "Wait 30-60 seconds between bottles so they do not wet-mix into mud.",
        "Start low - you can always add one spray; hard to remove.",
        f"Suggested total around {total_sprays} sprays for this combo (adjust for heat and space).",
    ]
    if total_sprays > 6:
        tips.append("This stack is loud - for close spaces, cut each bottle by one spray.")
    if any(s["weight"] >= 90 for s in steps) and any(s["weight"] <= 40 for s in steps):
        tips.append("Strong contrast stack - keep the heavy one minimal so the light one can show.")
    return {
        "steps": steps,
        "tips": tips,
        "total_sprays": total_sprays,
        "order_names": [s["name"] for s in steps],
    }



def _extract_note_phrases(notes: str) -> dict:
    """Pull rough top / heart / base phrases from free-text notes."""
    text = notes or ""
    low = text.lower()
    out = {"top": [], "heart": [], "base": [], "all": []}
    # Common section markers
    import re as _re
    patterns = [
        ("top", r"(?:top(?:\s+notes?)?|opening)\s*[:\-]\s*([^.\n]+)"),
        ("heart", r"(?:heart|middle|mid(?:dle)?(?:\s+notes?)?)\s*[:\-]\s*([^.\n]+)"),
        ("base", r"(?:base(?:\s+notes?)?|dry[\-\s]?down)\s*[:\-]\s*([^.\n]+)"),
    ]
    for key, pat in patterns:
        m = _re.search(pat, text, flags=_re.I)
        if m:
            chunk = m.group(1).strip()
            # stop at next section word if run-on
            chunk = _re.split(
                r"(?:Top|Heart|Middle|Base|Dry)\s",
                chunk,
                maxsplit=1,
            )[0].strip(" ,;")
            parts = [p.strip() for p in _re.split(r"[,;/]| and ", chunk) if p.strip()]
            out[key] = parts[:6]
    # Fallback tokens from whole notes
    tokens = []
    for t in _re.split(r"[,;/]|\s+and\s+", text):
        t = t.strip()
        if len(t) > 2 and not t.lower().startswith(("top", "heart", "middle", "base", "notes")):
            tokens.append(t)
    out["all"] = tokens[:12]
    return out


def describe_layer_scent(frags: list) -> str:
    """What you are likely to smell after layering - from combined notes."""
    if not frags:
        return ""
    tops, hearts, bases, loose = [], [], [], []
    for f in frags:
        parsed = _extract_note_phrases(f.get("notes") or "")
        tops.extend(parsed["top"])
        hearts.extend(parsed["heart"])
        bases.extend(parsed["base"])
        loose.extend(parsed["all"])
        # also pull from category for vibe words
        for c in f.get("category") or []:
            loose.append(c)

    def _uniq(seq, limit=5):
        seen = set()
        out = []
        for x in seq:
            k = x.lower().strip()
            if not k or k in seen or len(k) < 2:
                continue
            # skip section labels
            if k in ("top", "heart", "middle", "base", "notes", "note"):
                continue
            seen.add(k)
            out.append(x.strip())
            if len(out) >= limit:
                break
        return out

    tops_u = _uniq(tops, 4)
    hearts_u = _uniq(hearts, 4)
    bases_u = _uniq(bases, 4)

    # Keyword buckets from all note text
    blob = " ".join((f.get("notes") or "") for f in frags).lower()
    opening_kw = [
        k for k in [
            "citrus", "bergamot", "orange", "lemon", "grapefruit", "raspberry",
            "strawberry", "apple", "pear", "peach", "plum", "pineapple", "mango",
            "mint", "green", "ozone", "aquatic",
        ] if k in blob
    ]
    heart_kw = [
        k for k in [
            "rose", "jasmine", "orange blossom", "lavender", "iris", "peony",
            "orchid", "ylang", "cinnamon", "saffron", "cardamom", "coffee",
            "chocolate", "pistachio", "coconut",
        ] if k in blob
    ]
    base_kw = [
        k for k in [
            "vanilla", "caramel", "tonka", "amber", "musk", "oud", "sandalwood",
            "cedar", "patchouli", "incense", "leather", "tobacco", "praline",
            "sugar", "cream", "benzoin", "labdanum",
        ] if k in blob
    ]

    if not tops_u and opening_kw:
        tops_u = opening_kw[:4]
    if not hearts_u and heart_kw:
        hearts_u = heart_kw[:4]
    if not bases_u and base_kw:
        bases_u = base_kw[:4]

    if not tops_u and not hearts_u and not bases_u:
        # last resort from loose phrases
        loose_u = _uniq(loose, 6)
        if not loose_u:
            return "On skin the blend will follow the shared DNA of both bottles - give it 20 minutes to settle."
        return (
            "What you might smell: a mix of "
            + ", ".join(loose_u)
            + " as the layer settles on skin."
        )

    parts = ["What you might smell after layering:"]
    if tops_u:
        parts.append("first hit - " + ", ".join(tops_u))
    if hearts_u:
        parts.append("as it settles - " + ", ".join(hearts_u))
    if bases_u:
        parts.append("dry-down - " + ", ".join(bases_u))
    # One line vibe
    if any(k in blob for k in ("vanilla", "caramel", "sugar", "praline", "tonka")):
        parts.append("overall edible-sweet warmth with whatever bright notes ride on top")
    elif any(k in blob for k in ("oud", "incense", "leather", "smoke")):
        parts.append("overall deeper, denser trail once the top softens")
    elif any(k in blob for k in ("citrus", "bergamot", "aquatic", "green")):
        parts.append("overall fresher open that should stay lighter in the trail")

    return ". ".join(parts) + "."


def explain_layer_combo(frags: list) -> str:
    """Richer plain-language opinion on why this layer works (or struggles)."""
    if not frags or len(frags) < 2:
        return "Pick at least two bottles to explain the combo."
    names = [f.get("name") or "?" for f in frags]
    all_cats = []
    for f in frags:
        all_cats.extend(f.get("category") or [])
    cat_set = set(all_cats)
    bits = []

    ranked = sorted(frags, key=fragrance_weight_score, reverse=True)
    heavy = ranked[0]
    light = ranked[-1]
    if heavy.get("name") != light.get("name"):
        bits.append(
            f"**{heavy.get('name')}** reads heavier (base), and **{light.get('name')}** "
            f"reads lighter (top) - so the stack has a clear bottom and a bright edge."
        )

    gourmand = cat_set & {"Gourmand", "Sweet", "Vanilla", "Creamy"}
    fresh = cat_set & {"Fresh", "Citrus", "Aquatic", "Green"}
    floral = cat_set & {"Floral", "Powdery"}
    dark = cat_set & {"Oriental", "Oud", "Smoky", "Leather", "Woody"}
    fruity = cat_set & {"Fruity"}
    spicy = cat_set & {"Spicy", "Aromatic"}

    if gourmand and fresh:
        bits.append(
            "Sweet/gourmand warmth meets a fresh lift - the fresh side keeps the dessert "
            "side from feeling too thick on skin."
        )
    elif gourmand and floral:
        bits.append(
            "Gourmand creaminess with floral lift - soft, skin-close, and a little pretty on top."
        )
    elif gourmand and dark:
        bits.append(
            "Dessert notes over woods/oud/smoke - cozy base with a darker spine so it does not stay candy-only."
        )
    elif floral and dark:
        bits.append(
            "Florals over deeper woods or oriental notes - romantic on top, grounded underneath."
        )
    elif fruity and dark:
        bits.append(
            "Juicy fruit against darker woods or oriental - playful opening, serious dry-down."
        )
    elif fruity and gourmand:
        bits.append(
            "Fruit and gourmand stack like a dessert plate - easy, sweet, and crowd-friendly."
        )
    elif spicy and gourmand:
        bits.append(
            "Spice wakes up the sweet notes - warmer projection, more evening energy."
        )
    elif len(cat_set & {"Woody", "Oriental", "Oud", "Smoky"}) >= 2:
        bits.append(
            "Deep woody/oriental families together - rich and evening-leaning; keep sprays low."
        )
    elif len(cat_set) >= 2:
        bits.append(
            "Shared or neighboring families ("
            + ", ".join(sorted(cat_set)[:6])
            + ") so the bottles speak a similar language on skin."
        )

    if len(frags) >= 2:
        reasons = layer_note_reasons(frags[0], frags[1])
        shared_line = next(
            (r for r in (reasons or []) if str(r).lower().startswith("shared")),
            None,
        )
        if shared_line:
            bits.append(str(shared_line) + ".")
        syn = [r for r in (reasons or []) if "synergy" in str(r).lower()]
        if syn:
            bits.append(str(syn[0]) + ".")

    # NEW: what you smell after layering
    scent_story = describe_layer_scent(frags)
    if scent_story:
        bits.append(scent_story)

    if dark and not fresh:
        bits.append(
            "This reads more date-night / cool weather than office heat - great for evenings."
        )
    elif fresh and not dark:
        bits.append(
            "This leans daytime and warmer weather - lighter trail, easier in close spaces."
        )
    elif gourmand and not fresh:
        bits.append(
            "Expect a cozy, edible aura - perfect for home, movies, or cooler nights."
        )

    if len(frags) == 2:
        bits.append(
            f"Together: **{names[0]}** + **{names[1]}** - use the heavier one as the skin base, "
            f"then the lighter one on pulse points so both show."
        )
    else:
        bits.append(
            "With three or more, keep the loudest bottle to 1-2 sprays so nothing drowns the rest."
        )

    bits.append(
        "Worth a skin test before a full outing - heat and your chemistry will finish the story."
    )
    return " ".join(bits)



def recipe_gender_from_frags(frags: list) -> str:
    """Infer recipe gender from bottle genders (majority). Unisex if mixed or empty."""
    if not frags:
        return "Any"
    counts = {"Female": 0, "Male": 0, "Unisex": 0}
    for f in frags:
        g = (f.get("gender") or "").strip().lower()
        if "female" in g or "women" in g or "feminine" in g:
            if "lean" in g:
                counts["Female"] += 1
            else:
                counts["Female"] += 2
        elif "male" in g or "men" in g or "masculine" in g:
            if "lean" in g:
                counts["Male"] += 1
            else:
                counts["Male"] += 2
        elif "unisex" in g or not g:
            counts["Unisex"] += 1
        else:
            counts["Unisex"] += 1
    # Majority
    top = max(counts.items(), key=lambda x: x[1])
    if top[1] <= 0:
        return "Any"
    # If Female and Male both strong, call Unisex
    if counts["Female"] > 0 and counts["Male"] > 0 and abs(counts["Female"] - counts["Male"]) <= 1:
        return "Unisex"
    if top[0] == "Unisex" and (counts["Female"] or counts["Male"]):
        # unisex bottles + one gendered -> that gender if clear
        if counts["Female"] > counts["Male"]:
            return "Female"
        if counts["Male"] > counts["Female"]:
            return "Male"
    return top[0]


def format_recipe_share_text(recipe: dict = None, ev: dict = None, bottles: list = None) -> str:
    """Plain-text block for copy/paste sharing (texts, notes, IG caption)."""
    recipe = recipe or {}
    ev = ev or {}
    names = bottles or recipe.get("bottles") or []
    if not names and ev.get("frags"):
        names = [f.get("name") for f in ev["frags"] if f.get("name")]
    title = recipe.get("name") or ev.get("suggested_name") or "Untitled layer"
    gender = recipe.get("gender") or "Any"
    season = recipe.get("season_label") or (ev.get("season") or {}).get("label") or ""
    why = recipe.get("why") or ev.get("why") or ""
    # strip markdown bold for plain share
    why_plain = why.replace("**", "")
    app = recipe.get("application") or ev.get("application") or {}
    order = app.get("order_names") or list(names)
    lines = [
        f"Layer recipe: {title}",
        f"Bottles: {' + '.join(names)}",
    ]
    if gender and gender != "Any":
        lines.append(f"Gender lean: {gender}")
    if season:
        lines.append(f"Best season/temp: {season}")
    if order:
        lines.append(f"Spray order (heavy -> light): {' -> '.join(order)}")
    steps = app.get("steps") or []
    if steps:
        lines.append("How to wear:")
        for s in steps:
            lines.append(
                f"  {s.get('order')}. {s.get('name')} - {s.get('role')} - "
                f"{s.get('sprays')} spray(s) - {s.get('where')}"
            )
    if why_plain:
        lines.append("")
        lines.append("Why it works:")
        lines.append(why_plain)
    lines.append("")
    lines.append("From ScentedDeadGirl vault")
    return "\n".join(lines)


def evaluate_layer_recipe(bottle_names: list) -> dict:
    """Score a multi-bottle layer recipe and build a short verdict."""
    # Always evaluate in heavy -> light order for accurate base/top guidance
    bottle_names = order_names_heavy_to_light(list(bottle_names or []))
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
            "application": {},
            "why": "Pick at least two bottles to explain the combo.",
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
                    "reasons": layer_note_reasons(frags[i], frags[j]),
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
    guide = layer_application_guide(frags)
    why = explain_layer_combo(frags)
    return {
        "score": round(avg, 1),
        "verdict": verdict,
        "label": label,
        "pairs": pairs,
        "frags": frags,
        "missing": missing,
        "season": season_info,
        "suggested_name": suggested_name,
        "application": guide,
        "why": why,
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







# HTML entities only - keeps the .py file ASCII-safe; browsers still render emojis
EMOJI = {
    "bat": "&#129415;",
    "pumpkin": "&#127875;",
    "ghost": "&#128123;",
    "candy": "&#127852;",
    "moon": "&#127769;",
    "skull": "&#128128;",
    "sparkles": "&#10024;",
    "fire": "&#128293;",
    "heart": "&#128151;",
    "alien": "&#128125;",
}

# Halloween mood -> emoji key
HALLOWEEN_EMOJI = {
    "Pumpkin patch": "pumpkin",
    "Candy bowl": "candy",
    "Haunted house": "ghost",
    "Witching hour": "moon",
    "Autumn fog": "ghost",
    "Vampire soiree": "skull",
}


def emoji_html(*keys: str) -> str:
    """Return HTML entity string for one or more emoji keys."""
    out = []
    for k in keys:
        if k in EMOJI:
            out.append(EMOJI[k])
        elif k in HALLOWEEN_EMOJI:
            out.append(EMOJI.get(HALLOWEEN_EMOJI[k], ""))
    return " ".join(x for x in out if x)

HALLOWEEN_PROFILES = {
    "Pumpkin patch": {
        "categories": ["Gourmand", "Sweet", "Spicy", "Woody"],
        "notes_keywords": [
            "pumpkin", "spice", "cinnamon", "nutmeg", "caramel", "vanilla",
            "praline", "apple", "clove", "tonka", "amber",
        ],
        "blurb": "Sweater weather, pumpkin spice, caramel drizzle, leaf piles.",
    },
    "Candy bowl": {
        "categories": ["Gourmand", "Sweet", "Fruity"],
        "notes_keywords": [
            "candy", "sugar", "marshmallow", "chocolate", "caramel", "berry",
            "vanilla", "cotton candy", "toffee", "praline", "cream",
        ],
        "blurb": "Trick-or-treat stash - sticky sweet, playful, dessert-forward.",
    },
    "Haunted house": {
        "categories": ["Smoky", "Oriental", "Woody", "Leather", "Oud"],
        "notes_keywords": [
            "smoke", "incense", "oud", "leather", "myrrh", "amber", "patchouli",
            "tobacco", "wood", "vetiver", "labdanum",
        ],
        "blurb": "Creaky floors, candle smoke, something in the attic.",
    },
    "Witching hour": {
        "categories": ["Oriental", "Spicy", "Floral", "Woody"],
        "notes_keywords": [
            "incense", "rose", "saffron", "pepper", "amber", "oud", "spice",
            "cinnamon", "myrrh", "violet", "iris",
        ],
        "blurb": "Midnight ritual - spicy, mysterious, a little glamorous.",
    },
    "Autumn fog": {
        "categories": ["Woody", "Fresh", "Aromatic", "Green"],
        "notes_keywords": [
            "moss", "earth", "wood", "pine", "cedar", "vetiver", "green",
            "oakmoss", "smoke", "damp", "forest",
        ],
        "blurb": "Cold air, wet leaves, fog on the trail.",
    },
    "Vampire soiree": {
        "categories": ["Oriental", "Floral", "Sweet", "Leather"],
        "notes_keywords": [
            "rose", "blood", "cherry", "dark", "amber", "vanilla", "leather",
            "incense", "plum", "oud", "musk",
        ],
        "blurb": "Dark florals, red fruit, velvet and fangs.",
    },
}


def score_for_halloween(f: dict, mode: str) -> int:
    if st.session_state.get("user_reactions", {}).get(f.get("name")) == "dislike":
        return -999
    prof = HALLOWEEN_PROFILES.get(mode, {})
    score = 0
    if st.session_state.get("user_reactions", {}).get(f.get("name")) == "fav":
        score += 20
    for c in f.get("category") or []:
        if c in prof.get("categories", []):
            score += 15
    notes_l = (f.get("notes") or "").lower()
    name_l = (f.get("name") or "").lower()
    for kw in prof.get("notes_keywords", []):
        if kw in notes_l or kw in name_l:
            score += 8
    score += _stable_tiebreak((f.get("name") or "") + mode) % 7
    return score


def get_halloween_picks(
    mode: str,
    top_n: int = 5,
    gender: str = "Any",
    season_band: str = "Any",
    salt: int = 0,
) -> list:
    scored = []
    for f in st.session_state.get("fragrances_db") or []:
        if gender and gender != "Any":
            try:
                if not matches_gender(f, gender):
                    continue
            except Exception:
                g = (f.get("gender") or "").lower()
                if gender.lower() == "female" and not any(
                    x in g for x in ("female", "feminine", "women")
                ):
                    continue
                if gender.lower() == "male" and not any(
                    x in g for x in ("male", "masculine", "men")
                ):
                    continue
                if gender.lower() == "unisex" and "unisex" not in g:
                    continue
        if season_band and season_band != "Any":
            s = (f.get("season") or "").lower()
            band = season_band.lower()
            ok = True
            if "fall" in band or "autumn" in band or "cool" in band:
                ok = any(
                    x in s
                    for x in ("fall", "autumn", "cool", "winter", "versatile", "year")
                )
            elif "cold" in band or "winter" in band:
                ok = any(x in s for x in ("winter", "fall", "cold", "cool", "versatile"))
            elif "spring" in band or "mild" in band:
                ok = any(x in s for x in ("spring", "fall", "mild", "versatile", "year"))
            elif "summer" in band or "hot" in band:
                ok = any(x in s for x in ("summer", "spring", "hot", "warm", "versatile"))
            if not ok:
                continue
        sc = score_for_halloween(f, mode)
        if sc > 0:
            scored.append((sc, f))
    scored.sort(key=lambda x: x[0], reverse=True)
    ranked = [f for _, f in scored]
    if not ranked:
        return []
    window = ranked[: max(top_n * 4, 12)]
    start = (int(salt) * top_n) % max(1, len(window))
    picks = []
    seen = set()
    i = 0
    while len(picks) < top_n and i < len(window) * 2:
        f = window[(start + i) % len(window)]
        i += 1
        b = (f.get("brand") or "").lower()
        if b in seen and len(window) > top_n:
            continue
        picks.append(f)
        seen.add(b)
    if len(picks) < top_n:
        for f in window:
            if f not in picks:
                picks.append(f)
            if len(picks) >= top_n:
                break
    return picks[:top_n]


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


def get_horror_picks(mode: str, top_n: int = 3, gender: str = "Any") -> list:
    scored = []
    for f in st.session_state.get("fragrances_db") or []:
        if gender and gender != "Any":
            if not matches_gender(f, gender):
                continue
        s = score_for_horror(f, mode)
        if s > 0:
            scored.append((s, f))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [f for _, f in scored[:top_n]]


def suggest_categories_from_notes(notes: str) -> list:
    """Suggest scent families from free-text notes using keyword matching."""
    if not notes:
        return []
    text = notes.lower()
    # keyword -> category weights
    rules = {
        "Gourmand": ["vanilla", "caramel", "chocolate", "cocoa", "praline", "toffee", "cookie", "cake", "cream", "milk", "sugar", "marshmallow", "honey", "almond", "pistachio", "coffee", "latte", "dulce", "biscoff", "speculoos", "whipped"],
        "Sweet": ["sweet", "candy", "sugar", "honey", "caramel", "vanilla", "praline", "toffee", "cotton candy", "bubble gum"],
        "Floral": ["rose", "jasmine", "tuberose", "peony", "orchid", "lily", "violet", "iris", "freesia", "gardenia", "ylang", "orange blossom", "magnolia", "heliotrope", "muguet"],
        "Woody": ["wood", "cedar", "sandalwood", "oak", "vetiver", "patchouli", "guaiac", "cypress", "fir", "pine", "cashmere wood", "clearwood"],
        "Oriental": ["oud", "incense", "amber", "myrrh", "benzoin", "labdanum", "saffron", "resin", "oriental", "balsam"],
        "Fresh": ["fresh", "clean", "aquatic", "ozonic", "marine", "cucumber", "mint", "green"],
        "Fruity": ["apple", "pear", "peach", "berry", "strawberry", "raspberry", "cherry", "mango", "pineapple", "lychee", "blackcurrant", "cassis", "plum", "banana", "coconut", "fruity"],
        "Spicy": ["pepper", "cinnamon", "cardamom", "nutmeg", "ginger", "clove", "spice", "pimento"],
        "Citrus": ["citrus", "bergamot", "lemon", "orange", "grapefruit", "mandarin", "lime", "neroli"],
        "Aromatic": ["lavender", "rosemary", "basil", "sage", "herbal", "aromatic", "anise"],
        "Leather": ["leather"],
        "Oud": ["oud", "agarwood", "agar"],
        "Boozy": ["rum", "cognac", "whiskey", "whisky", "liquor", "boozy", "wine", "champagne"],
        "Smoky": ["smoke", "smoky", "incense", "tobacco", "burnt"],
        "Powdery": ["powder", "powdery", "iris", "violet", "heliotrope", "orris"],
        "Musky": ["musk", "musky", "skin", "clean musk"],
        "Amber": ["amber", "ambergris", "ambroxan", "amberwood"],
        "Vanilla": ["vanilla"],
        "Green": ["green", "galbanum", "grass", "leaf", "ivy", "tomato leaf"],
        "Aquatic": ["aquatic", "marine", "sea", "ocean", "watery", "ozonic"],
        "Creamy": ["cream", "creamy", "milk", "butter", "lactonic", "sandalwood"],
        "Chypre": ["chypre", "oakmoss", "bergamot", "labdanum"],
        "Fougere": ["fougere", "lavender", "coumarin", "oakmoss"],
        "Animalic": ["animalic", "civet", "castoreum", "musk", "indolic"],
        "Metallic": ["metallic", "metal", "aluminum", "ink"],
    }
    scores = {}
    for cat, kws in rules.items():
        score = 0
        for kw in kws:
            if kw in text:
                score += 1 + (1 if len(kw) > 5 else 0)  # slight boost for longer/more specific
        if score:
            scores[cat] = score
    # return top categories sorted by score, limit to 5
    ranked = sorted(scores.items(), key=lambda x: (-x[1], x[0]))
    return [c for c, s in ranked[:5]]





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
    "Lazy / stay home": {
        "categories": ["Gourmand", "Sweet", "Creamy", "Musky", "Vanilla", "Powdery"],
        "notes_keywords": [
            "vanilla", "cream", "milk", "musk", "soft", "cozy", "caramel",
            "marshmallow", "cotton", "skin", "powder", "tonka", "amber",
            "cookie", "warm", "comfort",
        ],
    },
}



# Curated Middle Eastern / Arabian-inspired suggestions for weekly wishlist ideas
ME_WISHLIST_POOL = [
    {"name": "Khamrah", "brand": "Lattafa", "why": "Date + praline gourmand - cozy winter staple"},
    {"name": "Asad", "brand": "Lattafa", "why": "Spicy woody amber - bold evening wear"},
    {"name": "Qaed Al Fursan", "brand": "Lattafa", "why": "Pineapple + oud - fun fruity woody"},
    {"name": "Yara", "brand": "Lattafa", "why": "Soft gourmand floral - easy daily sweet"},
    {"name": "Eclaire", "brand": "Lattafa", "why": "Caramel milk gourmand - dessert skin scent"},
    {"name": "Nebras", "brand": "Lattafa", "why": "Berry cacao gourmand - playful sweet"},
    {"name": "Terrafuma", "brand": "Lattafa", "why": "Earthy spicy - if you like darker woods"},
    {"name": "Her Confession", "brand": "Lattafa", "why": "Floral spicy - date-night leaning"},
    {"name": "Vintage Radio", "brand": "Lattafa", "why": "Powdery iris + woods - soft unique"},
    {"name": "Ajwad Pink to Black", "brand": "Lattafa", "why": "Fruity rose oud - if you like Ajwad"},
    {"name": "Badee Al Oud Honor & Glory", "brand": "Lattafa", "why": "Pineapple creamy - tropical gourmand"},
    {"name": "Mahd Al Dhahab", "brand": "Lattafa", "why": "Rich oriental - classic Arabic vibe"},
    {"name": "Raghba Wood Intense", "brand": "Lattafa", "why": "Sweet woody - easy crowd-pleaser"},
    {"name": "Opulent Oud", "brand": "Lattafa", "why": "Oud + rose - traditional leaning"},
    {"name": "Ana Abiyedh Rouge", "brand": "Lattafa", "why": "Fruity floral musk - soft feminine"},
    {"name": "Hayaati", "brand": "Lattafa", "why": "Fresh spicy - versatile daily"},
    {"name": "Ramz Silver", "brand": "Lattafa", "why": "Fresh clean - office-safe ME pick"},
    {"name": "24 Carat Pure Gold", "brand": "Lattafa", "why": "Honey tobacco - warm evening"},
    {"name": "Art of Nature II", "brand": "Lattafa", "why": "Green woody - if you want less sweet"},
    {"name": "Eternal Oud", "brand": "Lattafa", "why": "Deep oud - pure Middle Eastern"},
    {"name": "Qissa Pink", "brand": "Paris Corner", "why": "Sweet floral - soft gourmand adjacent"},
    {"name": "Qissa Red", "brand": "Paris Corner", "why": "Fruity sweet - playful layering base"},
    {"name": "Khair Pistachio", "brand": "Paris Corner", "why": "Pistachio gourmand - nutty dessert"},
    {"name": "Emir Vibrant Seduction", "brand": "Paris Corner", "why": "Sweet fruity - easy reach"},
    {"name": "Flavia Black", "brand": "Fragrance World", "why": "Dark sweet - night-time vibe"},
    {"name": "Barakkat Soft Diamond", "brand": "Fragrance World", "why": "Powdery soft - skin-scent style"},
    {"name": "Club de Nuit Intense Man", "brand": "Armaf", "why": "Smoky pineapple - if you like bold"},
    {"name": "Odyssey Homme White Edition", "brand": "Armaf", "why": "Fresh clean - summer ME pick"},
    {"name": "Untold", "brand": "Armaf", "why": "Sweet amber - cozy daily"},
    {"name": "Oddity", "brand": "Armaf", "why": "Modern sweet - unique twist"},
    {"name": "Hawas Ice", "brand": "Rasasi", "why": "Fresh aquatic - hot weather"},
    {"name": "Daarej", "brand": "Rasasi", "why": "Soft oriental - understated"},
    {"name": "La Yuqawam", "brand": "Rasasi", "why": "Leather rose - refined ME classic"},
    {"name": "Junoon Leather", "brand": "Rasasi", "why": "Leather spicy - fierce mood"},
    {"name": "Shuhrah", "brand": "Rasasi", "why": "Woody aromatic - daily driver"},
    {"name": "Oud Al Masih", "brand": "Rasasi", "why": "Oud focused - traditional"},
    {"name": "Dirham", "brand": "Ard Al Zaafaran", "why": "Fresh spicy - budget daily"},
    {"name": "Dirham Gold", "brand": "Ard Al Zaafaran", "why": "Sweeter Dirham style - easy"},
    {"name": "Supreme Amber", "brand": "Ard Al Zaafaran", "why": "Amber vanilla - cozy home"},
    {"name": "Oud 24 Hours", "brand": "Ard Al Zaafaran", "why": "Sweet oud - beginner oud"},
    {"name": "Wasim Abiyad", "brand": "Ard Al Zaafaran", "why": "Clean musk - laundry-adjacent ME"},
    {"name": "Amber Rouge", "brand": "Orientica", "why": "Rich amber - winter evening"},
    {"name": "Rouge Absolute", "brand": "Orientica", "why": "Sweet oriental - date night"},
    {"name": "Royal Bleu", "brand": "Orientica", "why": "Fresh blue - hot weather"},
    {"name": "Ameer Al Oud", "brand": "Lattafa", "why": "Intense oud - pure Arabic"},
    {"name": "Oud Mood Elixir", "brand": "Lattafa", "why": "Oud caramel - sweet oud hybrid"},
    {"name": "Sheikh Al Shuyukh Final Edition", "brand": "Lattafa", "why": "Spicy woody - masculine lean"},
    {"name": "Raghba", "brand": "Lattafa", "why": "Sweet vanilla musk - simple comfort"},
    {"name": "Velvet Oud", "brand": "Lattafa", "why": "Soft oud - less aggressive"},
    {"name": "Maahir Black Edition", "brand": "Lattafa", "why": "Dark spicy - night out"},
    {"name": "Najdia", "brand": "Lattafa", "why": "Fresh spicy - versatile"},
    {"name": "Fakhar Rose", "brand": "Lattafa", "why": "Rose focused - floral ME"},
    {"name": "Mayar Intense", "brand": "Lattafa", "why": "Fruity floral - if you like Mayar"},
    {"name": "Atlas", "brand": "Lattafa", "why": "Woody aromatic - less gourmand"},
]

# Filter out placeholder
ME_WISHLIST_POOL = [x for x in ME_WISHLIST_POOL if "placeholder" not in (x.get("name") or "").lower() and "petite cherie" not in (x.get("name") or "").lower()]


def weekly_wishlist_suggestions(n: int = 5) -> list:
    """Suggest Middle Eastern bottles not already in vault or wishlist, biased to user tastes."""
    import datetime as _dt
    db = st.session_state.get("fragrances_db") or []
    wl = st.session_state.get("wishlist") or []
    owned = set()
    for f in db:
        owned.add(((f.get("name") or "").strip().lower(), (f.get("brand") or "").strip().lower()))
    for w in wl:
        owned.add(((w.get("name") or "").strip().lower(), (w.get("brand") or "").strip().lower()))

    # Taste from vault categories
    from collections import Counter
    cat_counts = Counter()
    for f in db:
        for c in f.get("category") or []:
            cat_counts[c] += 1
    top_cats = {c for c, _ in cat_counts.most_common(8)}

    # Score pool items
    scored = []
    for item in ME_WISHLIST_POOL:
        key = ((item.get("name") or "").strip().lower(), (item.get("brand") or "").strip().lower())
        # also skip if name alone matches owned (brand variants)
        name_owned = any(key[0] == o[0] for o in owned if key[0])
        if key in owned or name_owned:
            continue
        score = 1
        why = (item.get("why") or "").lower()
        if "gourmand" in why or "vanilla" in why or "caramel" in why or "sweet" in why:
            if "Gourmand" in top_cats or "Sweet" in top_cats or "Vanilla" in top_cats:
                score += 3
        if "oud" in why or "oriental" in why:
            if "Oriental" in top_cats or "Oud" in top_cats or "Woody" in top_cats:
                score += 2
        if "fresh" in why or "citrus" in why:
            if "Fresh" in top_cats or "Citrus" in top_cats:
                score += 2
        if "floral" in why or "rose" in why:
            if "Floral" in top_cats:
                score += 2
        if "cozy" in why or "soft" in why or "skin" in why:
            score += 1
        scored.append((score, item))

    scored.sort(key=lambda x: (-x[0], x[1].get("name") or ""))
    candidates = [it for _, it in scored]
    if not candidates:
        return []

    # Rotate by ISO week so suggestions change weekly
    today = pacific_today()
    week = int(today.strftime("%Y%W"))
    start = (week * n) % max(1, len(candidates))
    picks = []
    for i in range(min(n, len(candidates))):
        picks.append(candidates[(start + i) % len(candidates)])
    return picks




def sotd_streak() -> int:
    """Consecutive days with at least one SOTD log ending today (Pacific)."""
    hist = st.session_state.get("sotd_history") or []
    days = set()
    for e in hist:
        d = e.get("date") or e.get("when") or ""
        if d:
            days.add(str(d)[:10])
    if not days:
        return 0
    today = pacific_today()
    streak = 0
    from datetime import timedelta
    cur = today
    while cur.isoformat() in days:
        streak += 1
        cur = cur - timedelta(days=1)
    return streak


def brand_stats() -> list:
    """Return list of (brand, count) sorted by count desc."""
    from collections import Counter
    c = Counter()
    for f in st.session_state.get("fragrances_db") or []:
        b = (f.get("brand") or "Unknown").strip() or "Unknown"
        c[b] += 1
    return c.most_common()


def is_october_mode() -> bool:
    if st.session_state.get("force_october_mode"):
        return True
    try:
        return pacific_today().month == 10
    except Exception:
        return False


def halloween_countdown_text() -> str:
    from datetime import date
    today = pacific_today()
    year = today.year
    target = date(year, 10, 31)
    if today > target:
        target = date(year + 1, 10, 31)
    delta = (target - today).days
    if delta == 0:
        return "It is Halloween. The vault is open."
    if today.month == 10:
        return f"{delta} day(s) until Halloween."
    return f"{delta} day(s) until Halloween."




TAROT_CARDS = [
    {"name": "The Moon", "mood": "Soft", "blurb": "Fog, intuition, silver musk."},
    {"name": "The Tower", "mood": "Fierce", "blurb": "Smoke, spice, something breaks open."},
    {"name": "The Empress", "mood": "Date night", "blurb": "Rose, honey, full bloom."},
    {"name": "The Hermit", "mood": "Lazy / stay home", "blurb": "Candlelight, cream, quiet skin."},
    {"name": "Death", "mood": "Fierce", "blurb": "Oud, incense, transformation."},
    {"name": "The Star", "mood": "Soft", "blurb": "Clean light, soft florals, hope."},
    {"name": "The Devil", "mood": "Date night", "blurb": "Caramel, leather, temptation."},
    {"name": "Wheel of Fortune", "mood": "Main character", "blurb": "Whatever turns - wear it loud."},
    {"name": "The High Priestess", "mood": "Rainy day", "blurb": "Powder, iris, secret notes."},
    {"name": "The Magician", "mood": "Focus / work", "blurb": "Sharp citrus, green focus."},
    {"name": "The Lovers", "mood": "Date night", "blurb": "Shared air, sweet and deep."},
    {"name": "Judgement", "mood": "Main character", "blurb": "Amber wake-up call."},
]


def draw_tarot_card(salt: int = 0) -> dict:
    import hashlib
    cards = TAROT_CARDS or [
        {"name": "The Star", "mood": "Soft", "blurb": "A quiet glow."}
    ]
    today = pacific_today().isoformat()
    seed = int(hashlib.md5(f"tarot-{today}-{salt}".encode()).hexdigest()[:8], 16)
    return cards[seed % len(cards)]


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


def parse_bulk_fragrance_lines(text_block: str, default_brand: str = "") -> list:
    """Parse lines of 'Name' or 'Name | Brand' or 'Name, Brand' or 'Brand - Name'.

    Returns list of {name, brand} dicts (not yet added).
    """
    default_brand = (default_brand or "").strip()
    rows = []
    seen = set()
    for raw in (text_block or "").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        name, brand = "", default_brand
        if "|" in line:
            parts = [p.strip() for p in line.split("|", 1)]
            name, brand = parts[0], (parts[1] if len(parts) > 1 else default_brand)
        elif "\t" in line:
            parts = [p.strip() for p in line.split("\t", 1)]
            name, brand = parts[0], (parts[1] if len(parts) > 1 else default_brand)
        elif " - " in line and not line.lower().startswith("lattafa"):
            # Brand - Name  OR  Name - Brand: prefer longer right side as name if left looks like brand?
            # Safer: Name - Brand when default brand empty and left has spaces
            left, right = [p.strip() for p in line.split(" - ", 1)]
            if default_brand:
                name, brand = left, right or default_brand
            else:
                # If left is short (1-2 words) treat as brand - name
                if len(left.split()) <= 2 and len(right.split()) >= 1:
                    brand, name = left, right
                else:
                    name, brand = left, right
        elif "," in line:
            parts = [p.strip() for p in line.split(",", 1)]
            name, brand = parts[0], (parts[1] if len(parts) > 1 else default_brand)
        else:
            name = line
            brand = default_brand
        name = (name or "").strip()
        brand = (brand or default_brand or "Unknown").strip() or "Unknown"
        if not name:
            continue
        key = (name.lower(), brand.lower())
        if key in seen:
            continue
        seen.add(key)
        rows.append({"name": name, "brand": brand})
    return rows


def bulk_add_fragrances(
    text_block: str,
    default_brand: str = "",
    default_gender: str = "Unisex",
    default_season: str = "Versatile",
    skip_duplicates: bool = True,
) -> dict:
    """Add many bottles by name + brand only. Details can be edited later in Vault."""
    rows = parse_bulk_fragrance_lines(text_block, default_brand=default_brand)
    added = []
    skipped = []
    if "fragrances_db" not in st.session_state:
        st.session_state["fragrances_db"] = []
    for row in rows:
        name, brand = row["name"], row["brand"]
        dups = find_duplicate_fragrances(name, brand)
        if dups.get("exact") or dups.get("same_name"):
            if skip_duplicates:
                reason = "already in vault"
                if dups.get("exact"):
                    reason = f"exact match: {dups['exact'][0].get('name')}"
                elif dups.get("same_name"):
                    reason = f"same name exists ({dups['same_name'][0].get('brand')})"
                skipped.append({"name": name, "brand": brand, "reason": reason})
                continue
        frag = {
            "name": name,
            "brand": brand,
            "gender": default_gender or "Unisex",
            "season": default_season or "Versatile",
            "notes": "Not specified  -  edit later",
            "category": ["Gourmand"],
            "dupe_of": "",
            "shelf_status": "Own",
            "size_ml": None,
            "price": None,
        }
        st.session_state["fragrances_db"].append(frag)
        try:
            log_vault_action("added", name, f"bulk|{brand}")
        except Exception:
            pass
        added.append(frag)
    if added:
        try:
            save_persisted_data()
        except Exception:
            pass
        mark_vault_dirty()
    return {"added": added, "skipped": skipped, "parsed": len(rows)}



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



def get_mood_picks(mood: str, top_n: int = 3, pool: list = None, salt: int = 0) -> list:
    """Return top mood matches. salt rotates through the ranked list so redraw is not identical."""
    source = pool if pool is not None else st.session_state["fragrances_db"]
    scored = []
    for f in source:
        s = score_for_mood(f, mood)
        if s > 0:
            scored.append((s, f))
    scored.sort(key=lambda x: x[0], reverse=True)
    if not scored:
        return []
    recent = _recent_shown("play")
    # Wider pool + salt rotation + recent/brand diversity
    pool_size = min(len(scored), max(top_n * 6, 18))
    pool = scored[:pool_size]
    # Rotate window start by salt
    if len(pool) > top_n:
        start = (int(salt) * top_n + int(salt)) % len(pool)
        pool = pool[start:] + pool[:start]
    picks = _diversify_scored(pool, top_n, recent=recent, strength=16.0)
    _remember_shown("play", [f.get("name") for f in picks])
    return picks


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


def suggest_partners_for(
    base: dict,
    num: int = 12,
    gender: str = "Any",
    include_unisex: bool = False,
    exclude_dislikes: bool = True,
    season: str = "Any",
) -> list:
    """Best layering partners for a single selected fragrance.

    Gender is strict by default (Female = female only; no pure Unisex unless
    include_unisex=True). Season filters with matches_weather.
    """
    if not base:
        return []
    pool = st.session_state["fragrances_db"]
    candidates = []
    for f in pool:
        if f["name"] == base["name"]:
            continue
        if exclude_dislikes and st.session_state.get("user_reactions", {}).get(f["name"]) == "dislike":
            continue
        if gender and gender != "Any":
            fg = normalize_gender(f.get("gender", ""))
            if gender == "Female":
                # Strict: Female + Female-leaning only (no pure Unisex unless opted in)
                ok = fg in ("Female", "Female-leaning") or (
                    include_unisex and fg == "Unisex"
                )
            elif gender == "Male":
                ok = fg in ("Male", "Male-leaning") or (
                    include_unisex and fg == "Unisex"
                )
            elif gender == "Unisex":
                ok = fg == "Unisex" or (
                    include_unisex and fg in ("Male-leaning", "Female-leaning")
                )
            else:
                ok = matches_gender(f, gender)
            if not ok:
                continue
        if season and season != "Any":
            try:
                if not matches_weather(f, season):
                    continue
            except Exception:
                pass
        s = layer_score(base, f)
        if s <= -50:
            continue
        wb = fragrance_weight_score(base)
        wp = fragrance_weight_score(f)
        if wb >= wp + 8:
            order = (
                f"Order: **{base.get('name')}** first (heavier base, weight {wb}), "
                f"then **{f.get('name')}** on top (lighter, weight {wp})."
            )
        elif wp >= wb + 8:
            order = (
                f"Order: **{f.get('name')}** first (heavier base, weight {wp}), "
                f"then **{base.get('name')}** on top (lighter, weight {wb})."
            )
        else:
            order = (
                f"Similar weight ({wb} vs {wp}) - use fewer sprays of the denser one; "
                f"skin-test order."
            )
        cats_b = ", ".join((base.get("category") or [])[:3]) or "â"
        cats_p = ", ".join((f.get("category") or [])[:3]) or "â"
        reason = f"{order} Families: {cats_b} + {cats_p}."
        candidates.append((s, f, reason))
    candidates.sort(key=lambda x: x[0], reverse=True)
    recent = _recent_shown("layer")
    # Wider pool + brand diversity + jitter so partners rotate
    pool_size = min(len(candidates), max(num * 4, num + 10))
    pool = candidates[:pool_size]
    pool = [(s + random.random() * 5.0, f, reason) for s, f, reason in pool]
    pool.sort(key=lambda x: x[0], reverse=True)
    scored_for_div = [(s, f) for s, f, reason in pool]
    diversified = _diversify_scored(scored_for_div, num, recent=recent, strength=12.0)
    name_to_reason = {f.get("name"): (f, reason, s) for s, f, reason in pool}
    out = []
    for f in diversified:
        row = name_to_reason.get(f.get("name"))
        if row:
            out.append((row[0], row[1], row[2]))
        else:
            out.append((f, "", 0))
    _remember_shown("layer", [f.get("name") for f, _, _ in out])
    return out



def suggest_multi_layers(
    base: dict,
    size: int = 3,
    num_stacks: int = 4,
    gender: str = "Any",
    include_unisex: bool = False,
    season: str = "Any",
) -> list:
    """Build multi-bottle layer stacks ranked by combined score.

    Returns list of dicts: {names, score, reason}.
    size=3 means three bottles total (base + 2 partners).
    """
    if not base or size < 2:
        return []
    partners = suggest_partners_for(
        base,
        num=max(28, num_stacks * 8),
        gender=gender,
        include_unisex=include_unisex,
        season=season,
    )
    if not partners:
        return []
    # Shuffle partner order so stacks are not always the same combos
    random.shuffle(partners)

    stacks = []
    used_sets = set()

    if size == 2:
        for item in partners[:num_stacks]:
            pf = item[0]
            s = item[2] if len(item) > 2 else 0
            reason = item[1] if len(item) > 1 else ""
            names = order_names_heavy_to_light([base["name"], pf["name"]])
            key = tuple(names)
            if key in used_sets:
                continue
            used_sets.add(key)
            stacks.append({"names": names, "score": s, "reason": reason})
        return stacks[:num_stacks]

    for i, item1 in enumerate(partners):
        p1 = item1[0]
        r1 = item1[1] if len(item1) > 1 else ""
        s1 = item1[2] if len(item1) > 2 else 0
        for j, item2 in enumerate(partners):
            if j <= i:
                continue
            p2 = item2[0]
            s2 = item2[2] if len(item2) > 2 else 0
            if p1["name"] == p2["name"]:
                continue
            cross = layer_score(p1, p2)
            if cross <= -30:
                continue
            names = order_names_heavy_to_light(
                [base["name"], p1["name"], p2["name"]]
            )
            key = tuple(names)
            if key in used_sets:
                continue
            used_sets.add(key)
            total = s1 + s2 + max(0, cross // 2)
            ws = [
                fragrance_weight_score(base),
                fragrance_weight_score(p1),
                fragrance_weight_score(p2),
            ]
            spread = max(ws) - min(ws)
            if spread >= 20:
                total += 8
            elif spread < 8:
                total -= 5
            reason = (
                "3-way stack. Spray heavy to light: "
                + " -> ".join(names)
                + "."
            )
            stacks.append({"names": names, "score": total, "reason": reason})
            if len(stacks) >= num_stacks * 5:
                break
        if len(stacks) >= num_stacks * 5:
            break

    stacks.sort(key=lambda x: x["score"], reverse=True)
    final = []
    seen_partners = set()
    for st in stacks:
        others = [n for n in st["names"] if n != base.get("name")]
        overlap = sum(1 for n in others if n in seen_partners)
        if overlap >= 2 and len(final) >= 2:
            continue
        for n in others:
            seen_partners.add(n)
        final.append(st)
        if len(final) >= num_stacks:
            break
    return final


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


def log_sotd_immediate(names, notes: str = "", when=None) -> bool:
    """Write bottles to SOTD history now and persist (any tab can call this)."""
    if isinstance(names, str):
        names = [names]
    names = [n for n in names if n]
    if not names:
        return False
    if when is None:
        when = pacific_today()
    if hasattr(when, "isoformat"):
        when_s = when.isoformat()
    else:
        when_s = str(when)
    scent_display = " + ".join(names)
    is_layering = len(names) > 1
    entry = {
        "date": when_s,
        "scents": list(names),
        "scent": scent_display,
        "notes": (notes or "").strip()
        or ("Layered combo" if is_layering else ""),
        "is_layering": is_layering,
    }
    st.session_state.setdefault("sotd_history", []).insert(0, entry)
    try:
        mark_vault_dirty()
    except Exception:
        pass
    save_persisted_data(force=False)
    try:
        st.session_state["_vault_fp"] = vault_fingerprint()
    except Exception:
        pass
    st.session_state["_sotd_logged_flash"] = (
        f"Logged to SOTD: **{scent_display}** ({when_s})"
    )
    return True


def send_to_sotd(names, notes: str = "", log_now: bool = True) -> None:
    """Log to SOTD immediately (default) or only prefill the SOTD form.

    log_now=True (default): writes history + autosave from any tab.
    log_now=False: only prefills SOTD tab for a manual Log.
    """
    if isinstance(names, str):
        names = [names]
    names = [n for n in names if n]
    if not names:
        return
    if log_now:
        log_sotd_immediate(names, notes=notes)
        return
    st.session_state["sotd_prefill"] = list(names)
    if notes:
        st.session_state["sotd_notes_input"] = notes
    elif len(names) > 1:
        st.session_state["sotd_notes_input"] = "Layer: " + " + ".join(names)
    st.session_state["_sotd_ready_flash"] = (
        f"Ready on SOTD: **{' + '.join(names)}** - open the SOTD tab and tap Log."
    )


def render_fragrance_card(f: dict, key_prefix: str, show_actions: bool = True):
    """Consistent card display with YAY / DEL / Wear actions."""
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
    if f.get("concentration"):
        bits.append(str(f["concentration"]))
    if f.get("size_ml"):
        bits.append(f"{f['size_ml']} ml")
    if bits:
        st.caption(" | ".join(bits))

    if show_actions:
        col1, col2, col3, col4 = st.columns([1, 1, 1, 3])
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
        with col3:
            if st.button("Log SOTD", key=f"{key_prefix}_wear_{f['name']}"):
                send_to_sotd([f["name"]])
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


def note_char_count(f: dict) -> int:
    return len((f.get("notes") or "").strip())


def is_incomplete_notes(f: dict) -> bool:
    notes = (f.get("notes") or "").strip().lower()
    if len(notes) < 25:
        return True
    vague = ("limited public data", "not specified", "likely ", "typically ", "or oriental", "or floral")
    return any(v in notes for v in vague)


def short_notes_bottles(max_chars: int = 40) -> list:
    """Bottles whose notes are short or vague, sorted shortest first."""
    rows = []
    for f in st.session_state.get("fragrances_db") or []:
        n = (f.get("notes") or "").strip()
        low = n.lower()
        vague = any(
            v in low
            for v in (
                "not specified",
                "limited public data",
                "likely ",
                "typically ",
            )
        )
        chars = len(n)
        if chars < max_chars or vague or is_incomplete_notes(f):
            rows.append({"frag": f, "chars": chars, "preview": n[:80] or "(empty)"})
    rows.sort(key=lambda r: (r["chars"], (r["frag"].get("name") or "").lower()))
    return rows


def profile_gaps(f: dict) -> list:
    """List which core fields need fixing: notes, gender, season, category."""
    gaps = []
    if is_incomplete_notes(f):
        gaps.append("notes")
    g = (f.get("gender") or "").strip()
    if not g or g.lower() in ("unknown", "n/a", "na", "?"):
        gaps.append("gender")
    season = (f.get("season") or "").strip().lower()
    if (
        not season
        or season in ("unknown", "n/a", "na", "?", "not specified")
        or len(season) < 3
    ):
        gaps.append("season")
    cats = f.get("category") or []
    if not cats:
        gaps.append("category")
    return gaps


def fragrances_needing_fix(field: str = "any") -> list:
    """Bottles missing notes, gender, season, and/or category."""
    out = []
    for f in st.session_state.get("fragrances_db") or []:
        gaps = profile_gaps(f)
        if not gaps:
            continue
        if field == "any" or field in gaps:
            out.append({"frag": f, "gaps": gaps})
    out.sort(key=lambda x: (x["frag"].get("name") or "").lower())
    return out



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


def _search_normalize(s: str) -> str:
    s = (s or "").lower()
    s = re.sub(r"[^a-z0-9\s]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def fragrance_search_score(f: dict, query: str) -> int:
    """
    Name/brand relevance score. Higher = better. 0 = no match.

    Priority (high  ->  low):
      exact name  ->  exact brand  ->  name starts with query / query starts with name
       ->  full phrase inside name  ->  token matches on name/brand words
    Loose substring-inside-word matching is avoided so "Yara" does not
    pull every bottle that merely shares letters with another word.
    """
    q = _search_normalize(query)
    if not q:
        return 0
    name = _search_normalize(f.get("name"))
    brand = _search_normalize(f.get("brand"))
    if not name and not brand:
        return 0

    score = 0

    # Exact full-string matches (strongest)
    if q == name:
        return 1000
    if q == brand:
        score = max(score, 900)

    # Name begins with the query or query is the leading phrase of the name
    if name.startswith(q + " ") or name.startswith(q):
        score = max(score, 700)
    if q.startswith(name) and name and len(name) >= 3:
        score = max(score, 650)

    # Brand begins with query
    if brand.startswith(q + " ") or brand.startswith(q):
        score = max(score, 500)

    # Whole query appears as a contiguous phrase in the name
    if q in name:
        score = max(score, 400)
    if q in brand:
        score = max(score, 300)

    tokens = [t for t in q.split(" ") if t]
    name_words = name.split()
    brand_words = brand.split()
    all_words = name_words + brand_words

    token_hits = 0
    name_token_hits = 0
    for t in tokens:
        if len(t) < 2:
            continue
        hit = False
        # Exact token equality only (no "in word" fuzzy)
        if t in name_words:
            hit = True
            name_token_hits += 1
            score += 40
        elif t in brand_words:
            hit = True
            score += 25
        else:
            # Prefix match on a whole word (e.g. "ecl"  ->  "eclaire")
            for w in all_words:
                if len(w) >= 3 and len(t) >= 3 and (w.startswith(t) or t.startswith(w)):
                    hit = True
                    score += 15
                    if w in name_words:
                        name_token_hits += 1
                    break
        if hit:
            token_hits += 1

    if tokens and token_hits == 0 and score == 0:
        return 0
    if tokens and token_hits == len(tokens):
        score += 30
        if name_token_hits == len(tokens):
            score += 40
    return score


def fragrance_search_match(f: dict, query: str) -> bool:
    return fragrance_search_score(f, query) > 0


def search_fragrances_by_name_brand(query: str, exact_only: bool = False) -> list:
    """
    Return vault bottles matching name/brand.

    When any *exact name* match exists, only those exact names are returned
    (so searching "Yara Elixir" does not also list every other Yara).
    Pass exact_only=True to require exact name or exact brand only.
    """
    q = (query or "").strip()
    if not q:
        return []
    qn = _search_normalize(q)
    pool = st.session_state.get("fragrances_db") or []

    exact_name = [
        f for f in pool if _search_normalize(f.get("name")) == qn
    ]
    if exact_name:
        exact_name.sort(key=search_rank_key)
        return exact_name

    if exact_only:
        exact_brand = [
            f for f in pool if _search_normalize(f.get("brand")) == qn
        ]
        exact_brand.sort(key=search_rank_key)
        return exact_brand

    scored = []
    for f in pool:
        s = fragrance_search_score(f, q)
        if s > 0:
            scored.append((s, f))
    scored.sort(key=lambda x: (-x[0], search_rank_key(x[1])))
    return [f for _, f in scored]



def fragrance_notes_score(f: dict, query: str) -> int:
    """Inclusive notes-field score. Any matching word can hit. 0 = no match."""
    q = _search_normalize(query)
    if not q:
        return 0
    notes = _search_normalize(f.get("notes"))
    # Also allow category names as "note-like" hits
    cats = _search_normalize(" ".join(f.get("category") or []))
    blob = f"{notes} {cats}".strip()
    if not blob:
        return 0

    score = 0
    if q in notes:
        score += 80
    elif q in blob:
        score += 50

    tokens = [t for t in q.split(" ") if t]
    words = blob.split()
    token_hits = 0
    for t in tokens:
        hit = False
        if t in blob:
            hit = True
            score += 20
        else:
            for w in words:
                if len(t) >= 2 and len(w) >= 2 and (
                    w.startswith(t) or t.startswith(w) or t in w or w in t
                ):
                    hit = True
                    score += 12
                    break
        if hit:
            token_hits += 1

    if tokens and token_hits == 0 and score == 0:
        return 0
    if tokens and token_hits > 0:
        score += token_hits * 5
        if token_hits == len(tokens):
            score += 25
    return score


def search_fragrances_by_notes(query: str) -> list:
    """Return all vault bottles whose notes/categories match the query."""
    q = (query or "").strip()
    if not q:
        return []
    scored = []
    for f in st.session_state.get("fragrances_db") or []:
        s = fragrance_notes_score(f, q)
        if s > 0:
            scored.append((s, f))
    scored.sort(key=lambda x: (-x[0], search_rank_key(x[1])))
    return [f for _, f in scored]


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
    "Wear a bottle you haven't reached for in 2+ weeks.",
    "Layer two scents you've never combined before.",
    "No gourmands today  -  go dry, green, woody or citrus.",
    "Pick something with coffee, chocolate or caramel.",
    "Horror night: only smoky, incense, leather or dark woody.",
    "One spray only  -  see if it still projects on you.",
    "Wear your softest, skin-scent style bottle all day.",
    "Match the weather outside right now (hot  ->  fresh, cold  ->  cozy).",
    "Blind grab: close your eyes and pick from the shelf.",
    "Date-night intensity on a regular Tuesday.",
    "Only Female or Female-leaning bottles today.",
    "Only Male or Male-leaning bottles today.",
    "All vanilla-forward scents are banned until tomorrow.",
    "Choose a brand you almost never wear.",
    "Layer a Fresh top with a Gourmand base.",
    "Wear something that smells like dessert for dinner.",
    "Gothic fog only: incense, amber, rose, or oud.",
    "High-desert heat check: lightest, airiest bottle you own.",
    "Movie night: pick a scent that matches a horror film.",
    "Office-safe only  -  nothing loud or sweet.",
    "Revisit a bottle you once thought was 'meh'.",
    "Three words only in your SOTD notes today.",
    "Wear the opposite of whatever you wore yesterday.",
    "Powdery or iris-forward must appear in the mix.",
    "No Lattafa today  -  force the rest of the vault.",
    "Pick a body spray or lighter concentration if you have one.",
    "Coffee + desk day: soft, creamy, or skin-scent only.",
    "Fruity opening + clean dry-down  -  no heavy ambers.",
    "Leather or cedar has to show up somewhere.",
    "Skip your usual top 5  -  deep-shelf only.",
]


def _challenge_personal_pool() -> list:
    """Extra challenges built from this vault and recent SOTD."""
    extras = []
    db = st.session_state.get("fragrances_db") or []
    hist = st.session_state.get("sotd_history") or []
    reactions = st.session_state.get("user_reactions") or {}
    try:
        wears = get_wear_counts()
    except Exception:
        wears = {}

    if db:
        ranked = sorted(
            db,
            key=lambda f: (wears.get(f.get("name"), 0), f.get("name") or ""),
        )
        least = ranked[0]
        extras.append(
            f"Reach for **{least.get('name')}** ({least.get('brand')}) - it needs airtime."
        )
        if len(ranked) > 3:
            mid = ranked[len(ranked) // 2]
            extras.append(f"Mid-shelf pull: wear **{mid.get('name')}** today.")

    yay = [n for n, s in reactions.items() if s == "fav"]
    if yay:
        idx = int(hashlib.md5(pacific_today().isoformat().encode()).hexdigest()[:6], 16) % len(yay)
        extras.append(f"YAY spotlight: wear **{yay[idx]}** (or layer it).")

    if hist:
        last = hist[0]
        scents = last.get("scents") or []
        if not scents and last.get("scent"):
            scents = [p.strip() for p in str(last["scent"]).split(" + ")]
        name_map = {f["name"]: f for f in db}
        cats = set()
        for n in scents:
            f = name_map.get(n)
            if f:
                cats.update(f.get("category") or [])
        opposites = {
            "Gourmand": "Fresh",
            "Sweet": "Woody",
            "Fresh": "Oriental",
            "Floral": "Spicy",
            "Woody": "Fruity",
            "Oriental": "Citrus",
            "Citrus": "Leather",
            "Spicy": "Powdery",
        }
        for c in list(cats)[:2]:
            opp = opposites.get(c)
            if opp:
                extras.append(f"Yesterday leaned {c} - try **{opp}** today instead.")
                break
        if scents:
            extras.append(f"Do not repeat yesterday's main bottle: avoid **{scents[0]}**.")

    from collections import Counter
    cat_c = Counter()
    for f in db:
        for c in f.get("category") or []:
            cat_c[c] += 1
    if cat_c:
        rare = sorted(cat_c.items(), key=lambda x: x[1])[0][0]
        extras.append(f"Underused family in your vault: lean into **{rare}** today.")

    return extras


def draw_challenge() -> str:
    """Daily challenge - rotates by date; salt lets you reroll the same day."""
    today = pacific_today().isoformat()
    salt = st.session_state.get("challenge_salt", 0)
    deck = list(CHALLENGE_DECK) + _challenge_personal_pool()
    if not deck:
        return "Wear something that feels like High Desert night air."
    seed = int(hashlib.md5(f"challenge-{today}-{salt}".encode()).hexdigest()[:8], 16)
    return deck[seed % len(deck)]



def suggest_for_challenge(challenge: str, top_n: int = 3, salt: int = 0) -> list:
    """Pick bottles that fit the challenge. salt rotates so redraws are not identical."""
    db = st.session_state.get("fragrances_db") or []
    if not db:
        return []
    text = (challenge or "").lower()

    prefer_cats = set()
    prefer_notes = set()
    ban_cats = set()
    gender_want = None
    ban_brand = None

    if "no gourmand" in text or "gourmands are banned" in text or "no vanilla" in text:
        ban_cats.update(["Gourmand", "Sweet", "Vanilla"])
    if "no lattafa" in text:
        ban_brand = "lattafa"
    if "only male" in text or "male or male-leaning" in text or "male-leaning" in text:
        gender_want = "male"
    if "only female" in text or "female or female-leaning" in text or "female-leaning" in text:
        gender_want = "female"
    if "horror" in text or "smoky" in text or "incense" in text or "gothic" in text:
        prefer_cats.update(["Smoky", "Oriental", "Leather", "Oud", "Woody"])
        prefer_notes.update(["smoke", "incense", "leather", "oud", "amber"])
    if "coffee" in text or "desk" in text or "soft" in text or "creamy" in text or "skin-scent" in text:
        prefer_cats.update(["Gourmand", "Sweet", "Creamy", "Musky", "Vanilla"])
        prefer_notes.update(["vanilla", "cream", "milk", "musk", "coffee", "soft"])
    if "fresh" in text or "airiest" in text or "heat" in text or "summer" in text:
        prefer_cats.update(["Fresh", "Citrus", "Aquatic"])
        prefer_notes.update(["fresh", "citrus", "bergamot", "light"])
    if "floral" in text or "powdery" in text:
        prefer_cats.update(["Floral", "Powdery"])
        prefer_notes.update(["rose", "jasmine", "iris", "powder"])
    if "lazy" in text or "stay home" in text or "cozy" in text:
        prefer_cats.update(["Gourmand", "Sweet", "Creamy", "Musky", "Vanilla"])
        prefer_notes.update(["vanilla", "cream", "musk", "soft", "cozy"])

    scored = []
    for f in db:
        name = (f.get("name") or "").lower()
        brand = (f.get("brand") or "").lower()
        cats = set(f.get("category") or [])
        notes = (f.get("notes") or "").lower()
        gender = (f.get("gender") or "").lower()

        if ban_brand and ban_brand in brand:
            continue
        if ban_cats and cats & ban_cats and not (prefer_cats and cats & prefer_cats):
            if not (cats & prefer_cats):
                continue
        if gender_want == "male" and not any(x in gender for x in ["male", "masculine"]):
            continue
        if gender_want == "female" and not any(x in gender for x in ["female", "feminine"]):
            continue

        score = 1
        if prefer_cats:
            score += 3 * len(cats & prefer_cats)
        if prefer_notes:
            score += sum(2 for kw in prefer_notes if kw in notes or kw in name)
        if not gender_want and "unisex" in gender:
            score += 0.5
        # tiny name hash so ties don't always sort the same way alphabetically
        score += (_stable_tiebreak(name + brand + str(salt)) % 100) / 1000.0
        scored.append((score, f))

    scored.sort(key=lambda x: (-x[0], x[1].get("name") or ""))
    ranked = [f for _, f in scored]
    if not ranked:
        return []
    window = ranked[: max(top_n * 5, 15)]
    if len(window) <= top_n:
        return window
    start = (int(salt) * top_n) % len(window)
    # Exclude recently shown names if provided via session
    recent = set()
    try:
        for n in (st.session_state.get("_challenge_last_picks") or []):
            if n:
                recent.add(str(n).lower())
    except Exception:
        recent = set()
    picks = []
    seen_brands = set()
    i = 0
    guard = 0
    while len(picks) < top_n and guard < len(window) * 3:
        f = window[(start + i) % len(window)]
        i += 1
        guard += 1
        nm = (f.get("name") or "").lower()
        b = (f.get("brand") or "").lower()
        if nm in recent and len(window) > top_n + len(recent):
            continue
        if b in seen_brands and len(window) > top_n:
            continue
        picks.append(f)
        seen_brands.add(b)
    # fill if needed (allow recent / same brand)
    if len(picks) < top_n:
        for f in window:
            if f not in picks:
                picks.append(f)
            if len(picks) >= top_n:
                break
    return picks[:top_n]



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
CONCENTRATION_OPTIONS = [
    "EDP",
    "EDT",
    "Extrait / intense",
    "Concentrated oil",
    "Body spray / mist",
    "Other",
]


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
        f"Format: {frag.get('concentration') or 'EDP'}",
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


# Popular clone / inspired-by map (name lowercase  ->  original). Not exhaustive.
KNOWN_DUPE_OF = {
    "asad": "Dior Sauvage Elixir",
    "lattafa asad": "Dior Sauvage Elixir",
    "khamrah": "Kilian Angels' Share",
    "lattafa khamrah": "Kilian Angels' Share",
    "khamrah original": "Kilian Angels' Share",
    "lattafa khamrah original": "Kilian Angels' Share",
    "khamrah qahwa": "Kilian Angels' Share (coffee twist)",
    "lattafa khamrah qahwa": "Kilian Angels' Share (coffee twist)",
    "khamrah dukhan": "Kilian Angels' Share (smoky)",
    "lattafa khamrah dukhan": "Kilian Angels' Share (smoky)",
    "khamrah waha": "Kilian Angels' Share family",
    "club de nuit women": "Chanel Coco Mademoiselle (inspired)",
    "club de nuit intense": "Creed Aventus",
    "cdn intense": "Creed Aventus",
    "qaed al fursan": "Creed Aventus (pineapple/oud lean)",
    "lattafa qaed al fursan (original)": "Creed Aventus (inspired)",
    "lattafa qaed al fursan original": "Creed Aventus (inspired)",
    "hawas": "Invictus / Invictus Victory style",
    "rasasi hawas": "Invictus style",
    "hawas ice": "Invictus / aquatic fresh",
    "rasasi hawas ice": "Invictus / aquatic fresh",
    "yara": "Kayali / soft gourmand floral (inspired)",
    "lattafa yara": "soft gourmand floral (Kayali-adjacent)",
    "yara tous": "Lattafa Yara family / soft fruity floral",
    "pink yara / yara pink": "Lattafa Yara family",
    "yara elixir": "Lattafa Yara (richer gourmand)",
    "nebras": "Thierry Mugler Angel / sweet gourmand",
    "lattafa nebras": "Thierry Mugler Angel-style gourmand",
    "amayra / mayar": "floral fruity designer style",
    "mayar": "floral fruity (designer-inspired)",
    "eclaire": "Mugler Angel Muse / gourmand caramel",
    "lattafa eclaire": "gourmand caramel / Angel Muse lean",
    "badee al oud noble blush": "Initio / rose-gourmand lean",
    "oud mood": "oud oriental designer style",
    "lattafa oud mood": "oud oriental (designer-inspired)",
    "fakhar black": "YSL Y / dark fruity woody lean",
    "lattafa fakhar black": "YSL Y-style",
    "angham": "spicy gourmand designer style",
    "lattafa angham": "spicy gourmand (designer-inspired)",
    "teriaq": "gourmand oriental designer style",
    "lattafa teriaq": "gourmand oriental",
    "teriaq intense": "oriental spicy designer style",
    "her confessions": "floral spicy oriental",
    "his confessions": "woody spicy oriental",
    "eternal vanille": "vanilla gourmand niche style",
    "vanilla freak (give me gourmand)": "gourmand cupcake / bakery",
    "whipped pleasure (give me gourmand)": "caramel popcorn gourmand",
    "armaf odyssey aqua": "fresh aquatic designer",
    "armaf island bliss": "tropical designer style",
    "hawas elixir": "Hawas / Invictus family richer",
    "hawas pink": "gourmand marshmallow floral",
    "rasasi hawas pink": "gourmand marshmallow floral",
    "hawas diva": "fruity floral woody",
    "rasasi hawas diva": "fruity floral woody",
    "hawas eclat (eclat hawas)": "fruity floral (Hawas women line)",
    "rasasi hawas eclat (eclat hawas)": "fruity floral (Hawas women line)",
    "hawas london": "floral woody spicy",
    "rasasi hawas london": "floral woody spicy",
    "ajwad": "fruity woody oriental (designer-inspired)",
    "lattafa ajwad": "fruity woody oriental",
    "opulent dubai": "fruity woody fresh designer",
    "lattafa opulent dubai": "fruity woody fresh",
    "rave now intense": "fresh woody aromatic",
    "rave rage": "fresh woody spicy",
    "phlur heavy cream": "Phlur Heavy Cream (original; not a clone)",
"phlur vanilla skin": "Phlur Vanilla Skin (original; not a clone)",
    # --- extra common Middle East / clone house matches ---
    "lattafa badee al oud noble blush": "Initio Side Effect / rose-gourmand lean",
    "noble blush": "Initio / rose milk gourmand lean",
    "lattafa ana abiyedh coral": "light fruity coconut designer",
    "coral (ana abiyedh coral)": "light fruity coconut designer",
    "lattafa haya": "champagne strawberry floral designer",
    "lattafa emaan": "floral fruity designer",
    "lattafa sakeena": "fruity gourmand floral designer",
    "lattafa raneen": "floral fruity sweet designer",
    "lattafa maitha oil (attar)": "anise caramel gourmand attar",
    "lattafa mayar cherry intense": "cherry cacao gourmand designer",
    "mayar cherry intense": "cherry cacao gourmand designer",
    "lattafa nasmaat": "floral fruity sweet designer",
    "lattafa dalal": "floral fruity fresh designer",
    "lattafa habik (women's version)": "floral fresh fruity designer",
    "lattafa rave now (for women)": "fruity marshmallow floral designer",
    "rave now (for women)": "fruity marshmallow floral designer",
    "ameerat al arab prive rose": "rose musk sweet designer",
    "bint hooran": "almond coffee floral gourmand",
    "ard al zaafaran bint hooran": "almond coffee floral gourmand",
    "armaf club de nuit women": "Chanel Coco Mademoiselle (inspired)",
    "armaf odyssey marshmallow": "fruity marshmallow gourmand designer",
    "armaf odyssey candee": "fruity caramel gourmand designer",
    "miss armaf mystique": "fruity floral gourmand designer",
    "paris corner khair men": "oud leather woody designer",
    "paris corner qissa delicious": "whipped cream chocolate gourmand",
    "paris corner marshmallow blush": "marshmallow sweet gourmand",
    "french avenue spectre original": "smoky leather woody (Spectre/Sauvage lean)",
    "spectre / sceptre malachite": "fresh aromatic woody designer",
    "maison alhambra spectre / sceptre malachite": "fresh aromatic woody designer",
    "zimaya fatima (fatima pink)": "fruity floral fresh designer",
    "zimaya hawwa red": "fruity floral sweet designer",
    "chocomusk": "Al Rehab chocolate musk classic",
    "al rehab chocomusk": "classic chocolate musk (house signature)",
    "al rehab caramello": "pistachio caramel gourmand",
    "al rehab soft": "soft floral sweet musk",
    "al rehab silver": "fresh metallic citrus musk",
}


def resolve_known_dupe(name: str, brand: str = "") -> str:
    """Return a known original / inspired-by target if we have one on file."""
    name = (name or "").strip().lower()
    brand = (brand or "").strip().lower()
    if not name:
        return ""
    keys = [
        f"{brand} {name}".strip(),
        name,
        name.replace("lattafa ", "").replace("rasasi ", "").replace("armaf ", ""),
    ]
    # strip parentheticals for softer match
    bare = re.sub(r"\(.*?\)", "", name).strip()
    if bare and bare not in keys:
        keys.append(bare)
        if brand:
            keys.append(f"{brand} {bare}".strip())
    for k in keys:
        if k in KNOWN_DUPE_OF:
            return KNOWN_DUPE_OF[k]
    # partial: any known key contained in name or vice versa (min length 5)
    for k, v in KNOWN_DUPE_OF.items():
        if len(k) < 5:
            continue
        if k in name or name in k:
            return v
        if brand and k.startswith(brand) and k.replace(brand, "").strip() in name:
            return v
    return ""


def notes_lookup_suggestions(name: str, brand: str = "") -> dict:
    """Local vault matches + online links for notes, gender, season, categories, dupes."""
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

    # Dupe targets: vault dupe_of field + built-in known map
    dupe_hits = []
    for f in uniq:
        d = (f.get("dupe_of") or "").strip()
        if d:
            dupe_hits.append(
                {
                    "source": f.get("name"),
                    "brand": f.get("brand"),
                    "dupe_of": d,
                    "origin": "vault",
                }
            )
    known = resolve_known_dupe(name, brand)
    if known:
        # avoid duplicate line if vault already has same text
        already = any(
            (h.get("dupe_of") or "").lower() == known.lower() for h in dupe_hits
        )
        if not already:
            dupe_hits.insert(
                0,
                {
                    "source": name or q,
                    "brand": brand,
                    "dupe_of": known,
                    "origin": "known map",
                },
            )
    # Also surface other vault bottles that list this name as their dupe_of
    if name:
        nl = name.lower()
        for f in st.session_state.get("fragrances_db") or []:
            d = (f.get("dupe_of") or "").strip()
            if not d:
                continue
            if nl in d.lower() or d.lower() in nl:
                dupe_hits.append(
                    {
                        "source": f.get("name"),
                        "brand": f.get("brand"),
                        "dupe_of": d,
                        "origin": "vault reverse",
                    }
                )

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
        links["Dupe of (Google)"] = (
            f"https://www.google.com/search?q={urllib.parse.quote_plus(q + ' perfume dupe of OR clone of OR inspired by')}"
        )
        links["Dupe of (Reddit)"] = (
            f"https://www.google.com/search?q={urllib.parse.quote_plus(q + ' dupe site:reddit.com')}"
        )
        links["Fragrantica dupe / similar"] = (
            f"https://www.google.com/search?q={urllib.parse.quote_plus('site:fragrantica.com ' + q + ' similar OR dupe OR clone')}"
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

    return {
        "local": uniq[:8],
        "links": links,
        "query": q,
        "dupe_hits": dupe_hits[:12],
        "known_dupe": known,
    }


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
    gender = (item.get("gender") or "").strip() or "Unisex"
    season = (item.get("season") or "").strip() or "Versatile"
    cats = item.get("category")
    if not cats:
        cats = suggest_categories_from_notes(notes) or ["Gourmand"]
    frag = {
        "name": name,
        "brand": brand,
        "gender": gender,
        "season": season,
        "notes": notes,
        "category": list(cats),
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


# Brand logo (header)
def _show_brand_logo():
    """Show sanctuary logo at top of app."""
    import base64 as _b64
    from pathlib import Path as _P
    candidates = [
        _P(__file__).resolve().parent / "sdg_logo.jpg",
        _P(__file__).resolve().parent / "sdg_logo.png",
        _P("sdg_logo.jpg"),
        _P("sdg_logo.png"),
        _P("/home/workdir/artifacts/sdg_logo.jpg"),
    ]
    for p in candidates:
        try:
            if p.is_file():
                st.image(str(p), use_container_width=True)
                return
        except Exception:
            continue
    # Embedded fallback so Cloud still shows art if file missing from repo
    _data = "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"
    st.markdown(
        f'<div style="text-align:center;margin:0.25rem 0 0.75rem 0;">'
        f'<img src="data:image/jpeg;base64,{_data}" '
        f'style="max-width:100%;width:min(420px,100%);height:auto;'
        f'border-radius:50%;box-shadow:0 8px 28px rgba(0,0,0,0.55);" />'
        f'</div>',
        unsafe_allow_html=True,
    )

_show_brand_logo()

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

    _rec = st.session_state.pop("_vault_recovered", None)
    if _rec:
        st.warning(_rec)
    _sb = st.session_state.pop("_save_blocked", None)
    if _sb:
        st.error(_sb)
    _se = st.session_state.pop("_save_error", None)
    if _se:
        st.error(f"Save failed: {_se}")

    _logged_sb = st.session_state.get("_sotd_logged_flash")
    if _logged_sb:
        st.success(_logged_sb)

    with st.expander("Quick SOTD (any tab)", expanded=False):
        st.caption("Log what you are wearing right now - saves immediately.")
        _q_names = sorted(
            f.get("name")
            for f in (st.session_state.get("fragrances_db") or [])
            if f.get("name")
        )
        q_pick = st.multiselect(
            "Bottle(s)",
            _q_names,
            key="sidebar_sotd_pick",
            placeholder="Pick 1 or more...",
        )
        q_notes = st.text_input("Note (optional)", key="sidebar_sotd_notes")
        if st.button("Log to SOTD now", type="primary", key="sidebar_sotd_log"):
            if not q_pick:
                st.warning("Pick at least one bottle.")
            else:
                log_sotd_immediate(q_pick, notes=q_notes or "")
                st.session_state["sidebar_sotd_pick"] = []
                st.rerun()

    with st.expander("Variety / reshuffle", expanded=False):
        st.caption(
            "If the same bottles keep showing, clear memory so Recommend, Layer, and Play pick fresh ones."
        )
        if st.button("Clear recent suggestion memory", key="clear_recent_shown"):
            for k in list(st.session_state.keys()):
                if str(k).startswith("_recent_shown_"):
                    st.session_state.pop(k, None)
            st.success("Suggestion memory cleared.")
            st.rerun()

    _n_bot = len(st.session_state.get("fragrances_db") or [])
    _last = st.session_state.get("last_saved_at") or st.session_state.get("_autosaved_at") or "never"
    _exp = st.session_state.get("last_export_date") or "never"
    st.caption(f"Vault: **{_n_bot}** bottles | autosave on")
    st.caption(f"Last saved: {_last}")
    st.caption(f"Last JSON export: **{_exp}**")
    if _exp == "never" or (
        isinstance(_exp, str)
        and _exp != "never"
        and _n_bot >= 5
    ):
        # Nudge export  -  Cloud can wipe the data file on redeploy
        st.info(
            "Cloud can erase the on-server data file when the app redeploys. "
            "After edits or adds, open **Vault  ->  Backup & restore  ->  Export vault as JSON** "
            "and keep a copy on your phone. Use **Restore** after a wipe."
        )

    # Clear search fields before widgets if flagged (must run before text_input widgets).
    if st.session_state.pop("_clear_search", False):
        st.session_state["search_input"] = ""
        st.session_state["note_search_input"] = ""
        st.session_state["quick_lookup_input"] = ""

    with st.expander("Search", expanded=True):
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
            # Inclusive match on name OR brand (same engine as main search)
            matched_quick = search_fragrances_by_name_brand(quick_query)
            if matched_quick:
                st.caption(f"{len(matched_quick)} vault match(es)")
                for f in matched_quick[:8]:
                    cats = ", ".join(f.get("category") or [])
                    msg = (
                        "**" + str(f.get("name")) + "** (" + str(f.get("brand")) + ")\n\n"
                        "**Gender:** " + str(f.get("gender", "?")) + "  |  **Season:** " + str(f.get("season", "?")) + "\n\n"
                        "**Category:** " + cats + "\n\n"
                        "**Notes:** " + str(f.get("notes") or "(none)")
                    )
                    st.info(msg)
            else:
                st.warning("No match in your vault.")
                n = len(st.session_state.get("fragrances_db") or [])
                st.caption("Checked all **" + str(n) + "** bottles. Try a shorter piece of the name or brand.")

    st.markdown("---")
    # Persistence status (edits live in JSON beside the script)
    _saved = st.session_state.get("last_saved_at")
    n_now = len(st.session_state.get("fragrances_db") or [])
    if _saved:
        st.caption(f"Vault last saved: {_saved} | **{n_now}**** bottles")
    else:
        st.caption(
            f"Vault: **{n_now}** bottles (seed or session). "
            "Saves to scented_dead_girl_data.json on every edit."
        )
    st.caption(
        "Cloud redeploys wipe server data. Export JSON from Vault after big changes "
        "and keep the file on your phone/Drive."
    )

    # Temp-search widget resets must run before slider/selectbox widgets.
    ca_default = int(default_ca_temp_f())
    if st.session_state.pop("_reset_temp_search", False):
        st.session_state["temp_search_f"] = ca_default
        st.session_state["temp_search_gender"] = "Any"
        st.session_state.pop("live_temp_meta", None)
    if st.session_state.pop("_apply_live_temp", False):
        live = st.session_state.get("live_temp_meta") or {}
        if live.get("ok") and live.get("temp_f") is not None:
            st.session_state["temp_search_f"] = int(live["temp_f"])
    if "temp_search_f" not in st.session_state:
        st.session_state["temp_search_f"] = ca_default
    if "temp_search_gender" not in st.session_state:
        st.session_state["temp_search_gender"] = "Any"

    with st.expander("Temp search", expanded=False):
        st.caption(
            "Victorville, CA High Desert - use live outdoor temp or set degrees (F) + gender."
        )
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
            st.warning(f"Live temp unavailable (rate limit or network). Using slider / monthly norm.")
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


    # Reset filters to defaults before widgets if flagged
    if st.session_state.pop("_clear_filters", False):
        st.session_state["filter_gender"] = "Any"
        st.session_state["filter_weather"] = "Any"
        st.session_state["filter_categories"] = []
        st.session_state["filter_occasion"] = "Any"
        st.session_state["filter_num_recs"] = 3
        st.session_state["filter_favorites_only"] = False
        st.session_state["filter_oils_only"] = False
        st.session_state["filter_prefer_oils"] = False
        st.session_state.pop("last_recs", None)
        # legacy single-category key
        st.session_state.pop("filter_category", None)

    # Migrate old single category session value once
    if "filter_categories" not in st.session_state:
        old_c = st.session_state.get("filter_category", "Any")
        if old_c and old_c != "Any":
            st.session_state["filter_categories"] = [old_c]
        else:
            st.session_state["filter_categories"] = []

    CAT_OPTIONS = [
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
        "Smoky",
        "Powdery",
    ]


    with st.expander("Recommend", expanded=False):
        st.caption("Stack filters, pick one or more families, then generate or refresh.")
        r1, r2 = st.columns(2)
        with r1:
            gender = st.selectbox(
                "Gender",
                ["Any", "Male", "Female", "Unisex"],
                key="filter_gender",
            )
        with r2:
            weather = st.selectbox(
                "Season",
                ["Any", "Hot / Summer", "Warm / Mild", "Cool / Autumn", "Cold / Winter"],
                key="filter_weather",
                help="Hard filter for recommendations.",
            )

        categories = st.multiselect(
            "Categories (pick several)",
            CAT_OPTIONS,
            key="filter_categories",
            placeholder="Any family if empty",
            help="Leave empty for any category. Match if the bottle has at least one selected family.",
        )
        # Empty multiselect = Any
        category = categories if categories else "Any"

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

        r3, r4 = st.columns(2)
        with r3:
            num_recs = st.radio(
                "How many",
                [1, 3, 5],
                index=1,
                horizontal=True,
                key="filter_num_recs",
            )
        with r4:
            st.write("")
            favorites_only = st.checkbox(
                "YAY only",
                value=False,
                key="filter_favorites_only",
            )
        oils_only = st.checkbox(
            "Concentrated oils only",
            value=False,
            key="filter_oils_only",
            help="Recommend perfume oils from your vault (set Format on each bottle).",
        )
        prefer_oils = st.checkbox(
            "Prefer oils in ranking",
            value=False,
            key="filter_prefer_oils",
            help="Boost concentrated oils in the list without hiding sprays.",
        )

        generate_clicked = st.button(
            "Generate", type="primary", use_container_width=True, key="gen_recs_btn"
        )
        regenerate_clicked = st.button(
            "Refresh picks",
            use_container_width=True,
            key="regen_recs_btn",
            help="Same filters, different bottles.",
        )
        if st.button("Clear", use_container_width=True, key="clear_filters_btn"):
            st.session_state["_clear_filters"] = True
            st.rerun()


    with st.expander("Add fragrance", expanded=False):
        # Notes helper (outside form so links work without submitting)
        # Prefill from Collection  ->  Short notes / Needs fix "Lookup" buttons
        _pending_lu = st.session_state.pop("_pending_notes_lookup", None)
        if isinstance(_pending_lu, dict):
            if _pending_lu.get("name"):
                st.session_state["notes_help_name"] = _pending_lu["name"]
            if "brand" in _pending_lu:
                st.session_state["notes_help_brand"] = _pending_lu.get("brand") or ""
            st.session_state["notes_help_expand"] = True
            st.session_state["_auto_run_notes_lookup"] = True

        _notes_help_open = bool(
            st.session_state.get("notes_help_expand")
            or st.session_state.get("notes_help_result")
        )
        with st.expander("Fragrance lookup helper", expanded=_notes_help_open):
            st.caption(
                "Search your vault and open Google / Fragrantica / Parfumo for notes, "
                "gender, season, category, **dupe of**, and price. "
                "Sites are not auto-scraped; use the links and copy what you need. "
                "From Collection - Short notes / Needs fix, tap **Lookup** on a bottle to fill this."
            )
            if st.session_state.pop("_clear_notes_help", False):
                st.session_state["notes_help_name"] = ""
                st.session_state["notes_help_brand"] = ""
                st.session_state.pop("notes_help_result", None)
                st.session_state.pop("prefill_new_notes", None)
                st.session_state["notes_help_expand"] = False
                st.session_state.pop("notes_help_focus_dupe", None)

            h1, h2 = st.columns(2)
            with h1:
                help_name = st.text_input("Lookup name", key="notes_help_name")
            with h2:
                help_brand = st.text_input("Lookup brand", key="notes_help_brand")
            hb1, hb2, hb3 = st.columns(3)
            with hb1:
                if st.button("Look up", key="notes_help_btn", use_container_width=True):
                    st.session_state["notes_help_result"] = notes_lookup_suggestions(
                        help_name, help_brand
                    )
                    st.session_state["notes_help_expand"] = True
                    st.session_state["notes_help_focus_dupe"] = False
            with hb2:
                if st.button(
                    "Find dupe of",
                    key="notes_help_dupe_btn",
                    use_container_width=True,
                    help="Search name + brand for what original this clones / is inspired by",
                ):
                    st.session_state["notes_help_result"] = notes_lookup_suggestions(
                        help_name, help_brand
                    )
                    st.session_state["notes_help_expand"] = True
                    st.session_state["notes_help_focus_dupe"] = True
            with hb3:
                if st.button("Clear finder", key="notes_help_clear", use_container_width=True):
                    st.session_state["_clear_notes_help"] = True
                    st.rerun()

            # Auto-run when opened from Collection
            if st.session_state.pop("_auto_run_notes_lookup", False):
                nm = (st.session_state.get("notes_help_name") or "").strip()
                br = (st.session_state.get("notes_help_brand") or "").strip()
                if nm:
                    st.session_state["notes_help_result"] = notes_lookup_suggestions(nm, br)
                    st.session_state["notes_help_expand"] = True

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
                        dupe_bit = ""
                        if (f.get("dupe_of") or "").strip():
                            dupe_bit = f"  \nDupe of: **{(f.get('dupe_of') or '').strip()}**"
                        st.write(
                            f"**{f.get('name')}** ({f.get('brand')})  \n"
                            f"Gender: {f.get('gender', '?')} | Season: {f.get('season', '?')} | "
                            f"Category: {cats}{price_bit}{dupe_bit}  \n"
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

                # --- Dupe of ---
                dupe_hits = help_res.get("dupe_hits") or []
                known_dupe = (help_res.get("known_dupe") or "").strip()
                focus_dupe = bool(st.session_state.get("notes_help_focus_dupe"))
                if focus_dupe:
                    st.markdown("### Dupe of / inspired by")
                    st.caption(
                        f"Query: **{help_res.get('query') or (help_name + ' ' + help_brand).strip()}**"
                    )
                else:
                    st.markdown("**Dupe of / inspired by**")
                if dupe_hits:
                    for hi, h in enumerate(dupe_hits):
                        origin = h.get("origin") or ""
                        src = h.get("source") or "?"
                        br = h.get("brand") or ""
                        target = h.get("dupe_of") or "?"
                        st.write(
                            f"**{target}**  \n"
                            f"From: *{src}*"
                            + (f" ({br})" if br else "")
                            + (f" | {origin}" if origin else "")
                        )
                        if st.button(
                            "Save dupe_of on vault match",
                            key=f"save_dupe_{hi}_{src}",
                            help="Write this dupe target onto the matching vault bottle",
                        ):
                            updated = False
                            for i, f in enumerate(st.session_state.get("fragrances_db") or []):
                                if (f.get("name") or "") == src:
                                    st.session_state["fragrances_db"][i]["dupe_of"] = target
                                    updated = True
                                    break
                            # If lookup name matches a vault bottle not in hits as source
                            if not updated:
                                lu_name = (st.session_state.get("notes_help_name") or "").strip()
                                for i, f in enumerate(st.session_state.get("fragrances_db") or []):
                                    if (f.get("name") or "").lower() == lu_name.lower():
                                        st.session_state["fragrances_db"][i]["dupe_of"] = target
                                        updated = True
                                        src = f.get("name")
                                        break
                            if updated:
                                try:
                                    log_vault_action("edited", src, f"dupe_of={target}")
                                except Exception:
                                    pass
                                save_persisted_data()
                                st.session_state["_dupe_save_flash"] = (
                                    f"Saved dupe_of **{target}** on **{src}**"
                                )
                                st.rerun()
                            else:
                                st.warning(
                                    "No vault bottle matched to save. Add the bottle first, "
                                    "or edit dupe_of in Vault."
                                )
                if known_dupe and not dupe_hits:
                    st.success(f"Likely dupe of / inspired by: **{known_dupe}**")
                elif known_dupe and dupe_hits:
                    # also surface known map even when vault hits exist
                    st.info(f"Built-in suggestion: **{known_dupe}**")
                if not dupe_hits and not known_dupe:
                    st.caption(
                        "No built-in dupe match yet. Use the **Dupe of (Google)** / Reddit links below, "
                        "then save the original name with **Set dupe of manually** or Vault - Edit."
                    )

                _df = st.session_state.pop("_dupe_save_flash", None)
                if _df:
                    st.success(_df)

                # Optional: type a dupe target and save onto lookup name bottle
                with st.expander("Set dupe of manually", expanded=False):
                    st.caption(
                        "Enter the original / designer scent this bottle clones or is inspired by."
                    )
                    manual_dupe = st.text_input(
                        "Dupe of (original name)",
                        key="notes_help_manual_dupe",
                        placeholder="e.g. Kilian Angels' Share",
                    )
                    if st.button("Save manual dupe_of", key="notes_help_manual_dupe_btn"):
                        target = (manual_dupe or "").strip()
                        lu_name = (st.session_state.get("notes_help_name") or "").strip()
                        if not target or not lu_name:
                            st.warning("Need Lookup name and a dupe target.")
                        else:
                            updated = False
                            for i, f in enumerate(st.session_state.get("fragrances_db") or []):
                                if (f.get("name") or "").lower() == lu_name.lower():
                                    st.session_state["fragrances_db"][i]["dupe_of"] = target
                                    updated = True
                                    try:
                                        log_vault_action(
                                            "edited", f.get("name"), f"dupe_of={target}"
                                        )
                                    except Exception:
                                        pass
                                    save_persisted_data()
                                    st.session_state["_dupe_save_flash"] = (
                                        f"Saved dupe_of **{target}** on **{f.get('name')}**"
                                    )
                                    st.rerun()
                            if not updated:
                                st.warning(
                                    f"No vault bottle named **{lu_name}**. "
                                    "Add it first or pick the exact vault name."
                                )

                links = help_res.get("links") or {}
                if links:
                    st.markdown("**Search online**")
                    st.caption(
                        "Google / Fragrantica / Parfumo for notes, gender, season, category, "
                        "dupe/clone, and price. Copy what you find into the Add form. "
                        "Sites are not auto-filled."
                    )
                    # Show dupe links first
                    preferred_order = [
                        "Dupe of (Google)",
                        "Dupe of (Reddit)",
                        "Fragrantica dupe / similar",
                        "Notes (Google)",
                        "Gender (Google)",
                        "Season (Google)",
                        "Category / accords (Google)",
                        "Fragrantica search",
                        "Parfumo search",
                    ]
                    shown = set()
                    for label in preferred_order:
                        url = links.get(label)
                        if url:
                            st.markdown(f"- [{label}]({url})")
                            shown.add(label)
                    for label, url in links.items():
                        if label not in shown:
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
            new_concentration = st.selectbox(
                "Format / concentration",
                CONCENTRATION_OPTIONS,
                index=0,
                key="add_concentration",
                help="Concentrated oil, EDP, EDT, body spray, etc.",
            )
            new_size = st.text_input("Size (ml)", placeholder="e.g. 100")
            # price UI removed
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
                            "concentration": new_concentration,
                            "size_ml": (
                                float(new_size)
                                if str(new_size or "").strip().replace(".", "", 1).isdigit()
                                else None
                            ),
                            "price": None,
                        }
                        st.session_state["fragrances_db"].append(new_frag)
                        try:
                            log_vault_action("added", new_frag["name"], new_frag.get("brand") or "")
                        except Exception:
                            pass
                        save_persisted_data()
                        st.success(f"Added **{new_frag['name']}** to the vault.")
                        st.rerun()


    # (Add fragrance form / expander end above)

# ---------- MAIN TABS ----------
tab_discover, tab_layer, tab_roulette, tab_sotd, tab_horoscope, tab_play, tab_collection, tab_vault = st.tabs(
    ["Discover", "Layer", "Roulette", "SOTD", "Stars", "Play", "Collection", "Vault"]
)

# ===== DISCOVER =====
with tab_discover:
    st.caption("Search, temp picks, and generated recommendations from the sidebar.")

    # --- Generate recommendations ---
    if generate_clicked or regenerate_clicked:
        gender = st.session_state.get("filter_gender", "Any")
        weather = st.session_state.get("filter_weather", "Any")
        cats = st.session_state.get("filter_categories") or []
        category = cats if cats else "Any"
        occasion = st.session_state.get("filter_occasion", "Any")
        num_recs = st.session_state.get("filter_num_recs", 3)
        favorites_only = bool(st.session_state.get("filter_favorites_only", False))
        oils_only = bool(st.session_state.get("filter_oils_only", False))
        prefer_oils = bool(st.session_state.get("filter_prefer_oils", False))
        conc_filter = "Concentrated oil" if oils_only else "Any"
        prev = st.session_state.get("last_recs") or {}
        prev_names = [
            f.get("name")
            for f in (prev.get("selected") or [])
            if isinstance(f, dict) and f.get("name")
        ]
        selected = get_top_fragrances(
            gender,
            weather,
            category,
            occasion,
            num_recs,
            favorites_only=favorites_only,
            temp_f=None,
            shuffle=True,
            exclude_names=prev_names if regenerate_clicked else list(_recent_shown("recommend"))[:12],
            concentration=conc_filter,
        )
        if prefer_oils and selected and not oils_only:
            # Re-rank: oils first while keeping relative order
            selected = sorted(
                selected,
                key=lambda f: (
                    0 if "oil" in (f.get("concentration") or "").lower() else 1,
                ),
            )
        if regenerate_clicked and not selected:
            selected = get_top_fragrances(
                gender,
                weather,
                category,
                occasion,
                num_recs,
                favorites_only=favorites_only,
                temp_f=None,
                shuffle=True,
                concentration=conc_filter,
            )
            if prefer_oils and selected and not oils_only:
                selected = sorted(
                    selected,
                    key=lambda f: (
                        0 if "oil" in (f.get("concentration") or "").lower() else 1,
                    ),
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
                "oils_only": oils_only,
                "prefer_oils": prefer_oils,
                "shuffled": bool(regenerate_clicked),
            },
        }

    # --- Name / brand search ---
    if search_query:
        st.subheader(f'Search | "{search_query}"')
        qn = _search_normalize(search_query) if "_search_normalize" in dir() else search_query.lower().strip()
        hits = []
        for f in st.session_state.get("fragrances_db") or []:
            blob = f"{f.get('name','')} {f.get('brand','')}".lower()
            if search_query.lower() in blob or (qn and qn in blob.replace(" ", "")):
                hits.append(f)
        if not hits:
            st.warning("No name/brand matches.")
        else:
            for i, f in enumerate(hits[:30], 1):
                st.markdown(
                    f"**{i}. {f.get('name')}** - *{f.get('brand')}* | "
                    f"{f.get('gender')} | {', '.join((f.get('category') or [])[:4])}"
                )
                st.caption(str(f.get("notes") or "")[:160])

    # --- Note keyword search ---
    if note_query:
        st.subheader(f'Notes | "{note_query}"')
        nq = note_query.lower().strip()
        hits = [
            f
            for f in (st.session_state.get("fragrances_db") or [])
            if nq in (f.get("notes") or "").lower()
            or nq in " ".join(f.get("category") or []).lower()
        ]
        if not hits:
            st.warning("No note matches.")
        else:
            for i, f in enumerate(hits[:30], 1):
                st.markdown(
                    f"**{i}. {f.get('name')}** - *{f.get('brand')}* | "
                    + ", ".join((f.get("category") or [])[:4])
                )
                st.caption(str(f.get("notes") or "")[:160])

    # --- Temp search results ---
    last_temp = st.session_state.get("last_temp_search")
    if last_temp is not None:
        picks = last_temp.get("picks") or []
        st.subheader("Temp search results")
        st.caption(
            f"{int(last_temp.get('temp_f', 0))} F -> {last_temp.get('band', '')} | "
            f"Gender: {last_temp.get('gender', 'Any')}"
        )
        if not picks:
            st.warning("No bottles matched this temperature + gender.")
        else:
            for i, f in enumerate(picks, 1):
                st.success(f"**#{i} - {f.get('name')}** by *{f.get('brand')}*")
                st.caption(
                    f"{f.get('gender')} | {f.get('season')} | "
                    + ", ".join(f.get("category") or [])
                )
                if st.button("Wear", key=f"temp_wear_{f.get('name')}_{i}"):
                    send_to_sotd([f.get("name")])
                    st.rerun()
        band = last_temp.get("band") or ""
        gender_t = last_temp.get("gender") or "Any"
        try:
            matched_recipes = recipes_for_band(band, gender=gender_t, limit=5)
        except Exception:
            matched_recipes = []
        if matched_recipes:
            st.markdown("#### Layer recipes for this temp")
            for ri, recipe in enumerate(matched_recipes):
                bottles = recipe.get("bottles") or []
                st.markdown(f"**{recipe.get('name', 'Recipe')}**")
                st.caption(" + ".join(bottles))
                if st.button("Wear layer", key=f"temp_recipe_wear_{ri}"):
                    send_to_sotd(list(bottles), notes=recipe.get("name") or "Layer recipe")
                    st.rerun()
        if st.button("Clear temp results", key="clear_temp_results"):
            st.session_state.pop("last_temp_search", None)
            st.rerun()

    # --- Generated recs ---
    last_recs = st.session_state.get("last_recs")
    if last_recs is not None:
        selected = last_recs.get("selected") or []
        num_show = last_recs.get("num", 3)
        meta = last_recs.get("meta") or {}
        st.subheader(f"Top {num_show}")
        if meta:
            cat_meta = meta.get("category")
            if isinstance(cat_meta, (list, tuple)):
                cat_txt = ", ".join(cat_meta) if cat_meta else "Any"
            else:
                cat_txt = cat_meta or "Any"
            st.caption(
                f"{meta.get('gender')} | {meta.get('weather')} | "
                f"{cat_txt} | {meta.get('occasion')}"
                + (" | YAY only" if meta.get("favorites_only") else "")
                + (" | oils only" if meta.get("oils_only") else "")
                + (" | prefer oils" if meta.get("prefer_oils") else "")
                + (" | refreshed" if meta.get("shuffled") else "")
            )
        if not selected:
            st.warning(
                "Nothing matched these filters. Try **Any** on some filters or turn off YAY only."
            )
        else:
            names_all = [f.get("name") for f in selected if f.get("name")]
            ba1, ba2 = st.columns(2)
            with ba1:
                if len(names_all) >= 2:
                    if st.button(
                        "Wear all as layer on SOTD",
                        key="rec_wear_all_layer",
                        type="primary",
                        use_container_width=True,
                    ):
                        send_to_sotd(names_all)
                        st.rerun()
            with ba2:
                if len(names_all) >= 2:
                    if st.button(
                        "Send all to Layer check (score combo)",
                        key="rec_send_all_layer",
                        use_container_width=True,
                    ):
                        st.session_state["roulette_layer_pick"] = list(names_all)
                        st.session_state["last_layer_check"] = evaluate_layer_recipe(
                            list(names_all)
                        )
                        st.session_state["_seed_roulette_recipe_name"] = True
                        st.session_state["_open_layer_check"] = True
                        st.success("Loaded in Layer check - open the Layer tab.")
                        st.rerun()
            for i, f in enumerate(selected, 1):
                current_reaction = st.session_state["user_reactions"].get(f["name"])
                badge = " YAY" if current_reaction == "fav" else ""
                conc = f.get("concentration") or ""
                conc_bit = f" | {conc}" if conc else ""
                st.success(f"**#{i} - {f['name']}** by *{f['brand']}*{badge}")
                st.write(f"**Gender:** {f['gender']} | **Season:** {f['season']}{conc_bit}")
                st.write(f"**Category:** {', '.join(f['category'])}")
                st.caption(f"Notes: {f['notes']}")
                c1, c2, c3 = st.columns(3)
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
                with c3:
                    if st.button("Wear solo", key=f"rec_wear_{f['name']}_{i}"):
                        send_to_sotd([f["name"]])
                        st.rerun()

                # Individual layer options -> Layering Studio (Base + partners)
                with st.expander(
                    f"Layer matches for {f.get('name')}",
                    expanded=False,
                ):
                    st.caption(
                        "Search partners for this bottle in Layering Studio. "
                        "Each match is for this scent alone."
                    )
                    if st.button(
                        "Open in Layering Studio as base",
                        type="primary",
                        key=f"rec_studio_base_{i}",
                        use_container_width=True,
                    ):
                        st.session_state["layer_base_select"] = f["name"]
                        # Align partner filters with Recommend
                        _g = (meta.get("gender") if meta else None) or st.session_state.get(
                            "filter_gender", "Any"
                        )
                        _w = (meta.get("weather") if meta else None) or st.session_state.get(
                            "filter_weather", "Any"
                        )
                        if _g and _g != "Any":
                            st.session_state["layer_partner_gender"] = _g
                        if _w and _w != "Any":
                            st.session_state["layer_partner_season"] = _w
                        st.session_state["_layer_studio_flash"] = (
                            f"**{f['name']}** is set as the base in Layering Studio. "
                            "Open the **Layer** tab to search matches."
                        )
                        st.rerun()

                    _g = (meta.get("gender") if meta else None) or st.session_state.get(
                        "filter_gender", "Any"
                    )
                    _w = (meta.get("weather") if meta else None) or st.session_state.get(
                        "filter_weather", "Any"
                    )
                    partners = suggest_partners_for(
                        f,
                        num=5,
                        gender=_g if _g != "Any" else "Any",
                        include_unisex=False,
                        season=_w if _w != "Any" else "Any",
                    )
                    if not partners:
                        st.info(
                            "No strong partners with current filters. "
                            "Open Layering Studio and set season/gender to Any."
                        )
                    else:
                        st.markdown("**Top matches** (tap to load in Studio or wear)")
                        for pi, item in enumerate(partners, 1):
                            if len(item) >= 3:
                                pf, reason, score = item[0], item[1], item[2]
                            else:
                                pf, reason = item[0], item[1]
                                score = None
                            st.markdown(
                                f"**{pi}. {pf.get('name')}** (*{pf.get('brand')}*)"
                                + (f" | score {score}" if score is not None else "")
                            )
                            st.caption(
                                ", ".join((pf.get("category") or [])[:4])
                                + " - "
                                + str(reason)[:140]
                            )
                            p1, p2, p3 = st.columns(3)
                            with p1:
                                if st.button(
                                    "Studio",
                                    key=f"rec_studio_pair_{i}_{pi}",
                                    help="Set recommend as base; partner is listed in Studio",
                                ):
                                    st.session_state["layer_base_select"] = f["name"]
                                    if _g and _g != "Any":
                                        st.session_state["layer_partner_gender"] = _g
                                    if _w and _w != "Any":
                                        st.session_state["layer_partner_season"] = _w
                                    st.session_state["_layer_studio_flash"] = (
                                        f"Base **{f['name']}** - look for "
                                        f"**{pf['name']}** in partners on the Layer tab."
                                    )
                                    st.rerun()
                            with p2:
                                if st.button(
                                    "Check pair",
                                    key=f"rec_pair_check_{i}_{pi}",
                                ):
                                    pair = [f["name"], pf["name"]]
                                    st.session_state["roulette_layer_pick"] = pair
                                    st.session_state["last_layer_check"] = (
                                        evaluate_layer_recipe(pair)
                                    )
                                    st.session_state["_seed_roulette_recipe_name"] = True
                                    st.session_state["_open_layer_check"] = True
                                    st.success(
                                        f"**{f['name']}** + **{pf['name']}** in Layer check."
                                    )
                                    st.rerun()
                            with p3:
                                if st.button(
                                    "Wear pair",
                                    key=f"rec_pair_sotd_{i}_{pi}",
                                ):
                                    send_to_sotd(
                                        [f["name"], pf["name"]],
                                        notes=f"Layer: {f['name']} + {pf['name']}",
                                    )
                                    st.rerun()
                st.markdown("---")

    if not search_query and not note_query and last_recs is None and last_temp is None:
        st.info(
            "Use the sidebar to search, filter, or **Generate** recommendations. "
            "Roulette, SOTD, and vault tools live in the other tabs."
        )


# ===== LAYER =====
with tab_layer:
    st.subheader("Layering Studio")
    st.caption("Partners for a base bottle, free combos, or saved recipes.")
    _studio_flash = st.session_state.pop("_layer_studio_flash", None)
    if _studio_flash:
        st.success(_studio_flash)

    if st.session_state.pop("_clear_layer", False):
        st.session_state["layer_partner_gender"] = "Any"
        st.session_state["layer_partner_season"] = "Any"
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
                "Partner gender filter",
                ["Any", "Male", "Female", "Unisex"],
                key="layer_partner_gender",
                help="Filters partner suggestions only. Base list always shows the full vault.",
            )
        with lp2:
            if st.button("Clear layer studio", use_container_width=True, key="layer_clear_btn"):
                st.session_state["_clear_layer"] = True
                st.rerun()

        layer_partner_season = st.selectbox(
            "Season / temp for partners",
            [
                "Any",
                "Hot / Summer",
                "Warm / Mild",
                "Cool / Autumn",
                "Cold / Winter",
            ],
            key="layer_partner_season",
            help="Only suggest partners that fit this weather band (versatile bottles still can appear).",
        )

        include_unisex = False
        if layer_partner_gender in ("Male", "Female"):
            include_unisex = st.checkbox(
                "Include Unisex in partners",
                value=False,
                key="layer_include_unisex_v3",
                help="Off by default. Turn on only if you want pure Unisex bottles with Female/Male.",
            )

        # Base list: FULL vault so every bottle is selectable
        vault_n = len(st.session_state.get("fragrances_db") or [])
        all_layer_names = sorted(
            f["name"]
            for f in st.session_state["fragrances_db"]
            if f.get("name")
        )
        base_options = ["- select a bottle -"] + all_layer_names
        if st.session_state.get("layer_base_select") not in base_options:
            st.session_state["layer_base_select"] = "- select a bottle -"

        base_choice = st.selectbox(
            f"Base fragrance ({vault_n} in vault)",
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
                max_partners = max(5, min(40, vault_n - 1)) if vault_n > 1 else 5
                show_n = st.slider(
                    "How many partners to show",
                    min_value=5,
                    max_value=max_partners,
                    value=min(12, max_partners),
                    key="layer_partner_count",
                )
                partners = suggest_partners_for(
                    base_f,
                    num=max(int(show_n) * 3, 12),
                    gender=layer_partner_gender,
                    include_unisex=include_unisex,
                    season=layer_partner_season,
                )
                # Safety net: drop any partner that still fails gender/season
                _strict = []
                for item in partners:
                    pf = item[0]
                    if layer_partner_gender and layer_partner_gender != "Any":
                        fg = normalize_gender(pf.get("gender", ""))
                        if layer_partner_gender == "Female":
                            ok = fg in ("Female", "Female-leaning") or (
                                include_unisex and fg == "Unisex"
                            )
                        elif layer_partner_gender == "Male":
                            ok = fg in ("Male", "Male-leaning") or (
                                include_unisex and fg == "Unisex"
                            )
                        elif layer_partner_gender == "Unisex":
                            ok = fg == "Unisex"
                        else:
                            ok = True
                        if not ok:
                            continue
                    if layer_partner_season and layer_partner_season != "Any":
                        try:
                            if not matches_weather(pf, layer_partner_season):
                                continue
                        except Exception:
                            pass
                    _strict.append(item)
                partners = _strict[: int(show_n)]
                if not partners:
                    st.warning(
                        "No partners matched this gender filter. "
                        "Try **Any**, turn on **Include Unisex**, or clear DEL reactions."
                    )
                else:
                    uni_note = (
                        ", +Unisex"
                        if include_unisex and layer_partner_gender in ("Male", "Female")
                        else ""
                    )
                    st.markdown(
                        f"**Top {len(partners)} partners for {base_choice}** "
                        f"(gender: {layer_partner_gender}{uni_note}"
                        f" | season: {layer_partner_season})"
                    )
                    for pi, item in enumerate(partners, 1):
                        if len(item) >= 3:
                            pf, reason, score = item[0], item[1], item[2]
                        else:
                            pf, reason = item[0], item[1]
                            score = None
                        # Simple match label instead of long float scores
                        if score is not None:
                            sc = int(round(float(score)))
                            if sc >= 100:
                                match_lbl = "Match: Excellent"
                            elif sc >= 70:
                                match_lbl = "Match: Strong"
                            elif sc >= 40:
                                match_lbl = "Match: Good"
                            else:
                                match_lbl = "Match: Okay"
                        else:
                            match_lbl = ""
                        _wb = fragrance_weight_score(base_f)
                        _wp = fragrance_weight_score(pf)
                        if _wb >= _wp + 8:
                            _role = (
                                f"Spray: **{base_choice}** first (base), "
                                f"then **{pf['name']}** (top)"
                            )
                        elif _wp >= _wb + 8:
                            _role = (
                                f"Spray: **{pf['name']}** first (base), "
                                f"then **{base_choice}** (top)"
                            )
                        else:
                            _role = "Similar weight - light sprays, skin-test order"
                        # Short family line only (skip duplicate order text in reason)
                        cats_p = ", ".join((pf.get("category") or [])[:4])
                        cats_b = ", ".join((base_f.get("category") or [])[:3])
                        family_line = f"Families: {cats_b} + {cats_p}"
                        st.info(
                            f"**{pi}. {pf['name']}** ({pf['brand']})\n\n"
                            f"{match_lbl}\n\n"
                            f"{_role}\n\n"
                            f"{pf.get('gender', '')} | {cats_p}\n\n"
                            f"{family_line}"
                        )
                        b1, b2, b3 = st.columns(3)
                        with b1:
                            if st.button("Layer check", key=f"layer_base_check_{pi}"):
                                st.session_state["roulette_layer_pick"] = [
                                    base_choice,
                                    pf["name"],
                                ]
                                st.session_state["last_layer_check"] = evaluate_layer_recipe(
                                    [base_choice, pf["name"]]
                                )
                                st.session_state["_seed_roulette_recipe_name"] = True
                                st.session_state["_open_layer_check"] = True
                                st.rerun()
                        with b2:
                            if st.button("Save recipe", key=f"layer_base_recipe_{pi}"):
                                names = order_names_heavy_to_light([base_choice, pf["name"]])
                                ev = evaluate_layer_recipe(names)
                                final_name = (ev.get("suggested_name") or f"{base_choice} x {pf['name']}")
                                st.session_state.setdefault("layer_recipes", []).insert(
                                    0,
                                    {
                                        "name": final_name,
                                        "bottles": names,
                                        "season_label": (ev.get("season") or {}).get("label", ""),
                                        "season_detail": (ev.get("season") or {}).get("detail", ""),
                                        "bands": list((ev.get("season") or {}).get("bands") or []),
                                        "application": ev.get("application") or {},
                                        "score": ev.get("score"),
                                        "label": ev.get("label"),
                                        "verdict": ev.get("verdict"),
                                        "why": ev.get("why") or "",
                                        "gender": recipe_gender_from_frags(ev.get("frags") or []) or "Any",
                                    },
                                )
                                mark_vault_dirty()
                                save_persisted_data(force=False)
                                st.session_state["_vault_fp"] = vault_fingerprint()
                                st.success(f"Saved recipe: {final_name}")
                        with b3:
                            if st.button("SOTD", key=f"layer_base_use_{pi}"):
                                log_sotd_immediate([base_choice, pf["name"]], notes="Layer studio")
                                st.rerun()


    # --- Multi-bottle stacks (3+) ---
    with st.expander("Multi-bottle stacks (3 bottles)", expanded=False):
        st.caption(
            "Suggest full layers with more than one partner - ordered heavy to light."
        )
        stack_base_opts = ["- select a bottle -"] + sorted(
            f["name"]
            for f in st.session_state.get("fragrances_db") or []
            if f.get("name")
        )
        stack_base = st.selectbox(
            "Base for multi-bottle stack",
            stack_base_opts,
            key="multi_stack_base",
        )
        ms1, ms2 = st.columns(2)
        with ms1:
            stack_gender = st.selectbox(
                "Gender",
                ["Any", "Female", "Male", "Unisex"],
                key="multi_stack_gender",
            )
        with ms2:
            stack_season = st.selectbox(
                "Season",
                ["Any", "Hot / Summer", "Warm / Mild", "Cool / Autumn", "Cold / Winter"],
                key="multi_stack_season",
            )
        stack_unisex = False
        if stack_gender in ("Male", "Female"):
            stack_unisex = st.checkbox(
                "Include Unisex",
                value=False,
                key="multi_stack_unisex",
            )
        n_stacks = st.slider("How many stacks to show", 2, 6, 3, key="multi_stack_count")
        if stack_base != "- select a bottle -":
            base_map = {f["name"]: f for f in st.session_state.get("fragrances_db") or []}
            base_s = base_map.get(stack_base)
            if base_s and st.button("Suggest multi-bottle layers", type="primary", key="multi_stack_go"):
                stacks = suggest_multi_layers(
                    base_s,
                    size=3,
                    num_stacks=int(n_stacks),
                    gender=stack_gender,
                    include_unisex=stack_unisex,
                    season=stack_season,
                )
                st.session_state["last_multi_stacks"] = {
                    "base": stack_base,
                    "stacks": stacks,
                    "gender": stack_gender,
                    "season": stack_season,
                }
                st.rerun()
            last_ms = st.session_state.get("last_multi_stacks")
            if last_ms and last_ms.get("base") == stack_base:
                stacks = last_ms.get("stacks") or []
                if not stacks:
                    st.info("No multi-bottle stacks found - try Any season/gender.")
                else:
                    st.markdown(
                        f"**{len(stacks)} stacks for {stack_base}** "
                        f"({last_ms.get('gender')} | {last_ms.get('season')})"
                    )
                    for si, st_item in enumerate(stacks, 1):
                        names = st_item.get("names") or []
                        _sc = st_item.get("score")
                        try:
                            _sc_i = int(round(float(_sc)))
                        except Exception:
                            _sc_i = None
                        if _sc_i is not None and _sc_i >= 100:
                            _ml = "Excellent"
                        elif _sc_i is not None and _sc_i >= 70:
                            _ml = "Strong"
                        elif _sc_i is not None and _sc_i >= 40:
                            _ml = "Good"
                        else:
                            _ml = "Okay" if _sc_i is not None else ""
                        st.markdown(
                            f"**Stack {si}**"
                            + (f" - {_ml}" if _ml else "")
                            + ": "
                            + " + ".join(names)
                        )
                        st.caption(st_item.get("reason") or "")
                        st.caption("Spray order (heavy -> light): " + " -> ".join(names))
                        c1, c2, c3 = st.columns(3)
                        with c1:
                            if st.button("Layer check", key=f"multi_check_{si}"):
                                st.session_state["roulette_layer_pick"] = list(names)
                                st.session_state["last_layer_check"] = evaluate_layer_recipe(
                                    list(names)
                                )
                                st.session_state["_seed_roulette_recipe_name"] = True
                                st.success("Loaded in Layer check below.")
                                st.rerun()
                        with c2:
                            if st.button("Log SOTD", key=f"multi_sotd_{si}"):
                                log_sotd_immediate(list(names), notes="Multi-layer stack")
                                st.rerun()
                        with c3:
                            if st.button("Save recipe", key=f"multi_save_{si}"):
                                ev = evaluate_layer_recipe(list(names))
                                final_name = (
                                    ev.get("suggested_name")
                                    or " + ".join(names)
                                )
                                st.session_state.setdefault("layer_recipes", []).insert(
                                    0,
                                    {
                                        "name": final_name,
                                        "bottles": list(names),
                                        "season_label": (ev.get("season") or {}).get(
                                            "label", ""
                                        ),
                                        "season_detail": (ev.get("season") or {}).get(
                                            "detail", ""
                                        ),
                                        "bands": list(
                                            (ev.get("season") or {}).get("bands") or []
                                        ),
                                        "application": ev.get("application") or {},
                                        "score": ev.get("score"),
                                        "label": ev.get("label"),
                                        "verdict": ev.get("verdict"),
                                        "why": ev.get("why") or "",
                                        "gender": recipe_gender_from_frags(
                                            ev.get("frags") or []
                                        )
                                        or "Any",
                                    },
                                )
                                mark_vault_dirty()
                                save_persisted_data(force=False)
                                st.success(f"Saved **{final_name}**")
                                st.rerun()

    # --- Layer check (moved into Layer tab) ---
    st.markdown("---")
    st.subheader("Layer check")
    st.caption(
        "Pick two or more bottles. We score the combo from categories and notes "
        "so you can see if it is a good layer."
    )
    # Clear multiselect BEFORE the widget is created (Streamlit forbids writing
    # to a widget key after that widget has been instantiated).
    if st.session_state.pop("_clear_roulette_layer_pick", False):
        st.session_state["roulette_layer_pick"] = []
        st.session_state.pop("last_layer_check", None)

    # When results exist, show a summary at the TOP so you do not have to hunt for it
    _ev_top = st.session_state.get("last_layer_check")
    if _ev_top:
        _app_top = _ev_top.get("application") or {}
        _order = _app_top.get("order_names") or [
            fr.get("name") for fr in (_ev_top.get("frags") or []) if fr.get("name")
        ]
        _sc_raw = _ev_top.get("score")
        try:
            _sc_i = int(round(float(_sc_raw)))
        except Exception:
            _sc_i = None
        st.success(
            "**Last result: "
            + str(_ev_top.get("label") or "?")
            + "**"
            + (f" ({_sc_i}/100 style points)" if _sc_i is not None else "")
            + "  |  "
            + (" -> ".join(_order) if _order else "see details below")
        )
        if _ev_top.get("why"):
            st.caption(str(_ev_top.get("why"))[:280])
        st.caption("Full guidance, pair notes, and Save recipe are below the picker.")
        # Soft scroll toward results block on mobile/desktop when just checked
        if st.session_state.pop("_scroll_to_layer_result", False) or st.session_state.pop(
            "_open_layer_check", False
        ):
            try:
                import streamlit.components.v1 as _components
                _components.html(
                    """
                    <div id="sdg-layer-result-anchor"></div>
                    <script>
                    (function() {
                      try {
                        const doc = window.parent.document;
                        const nodes = doc.querySelectorAll('div, p, span');
                        for (const n of nodes) {
                          const t = (n.innerText || n.textContent || '');
                          if (t.indexOf('Last result:') >= 0 || t.indexOf('How to wear this layer') >= 0) {
                            n.scrollIntoView({behavior: 'smooth', block: 'start'});
                            break;
                          }
                        }
                      } catch (e) {}
                    })();
                    </script>
                    """,
                    height=0,
                )
            except Exception:
                pass

    layer_check_season = st.selectbox(
        "Season filter for layer pick list",
        [
            "Any",
            "Hot / Summer",
            "Warm / Mild",
            "Cool / Autumn",
            "Cold / Winter",
        ],
        key="layer_check_season",
        help="Narrow which bottles appear in the picker for this season.",
    )
    all_names_layer = []
    for f in st.session_state.get("fragrances_db") or []:
        n = f.get("name")
        if not n:
            continue
        if layer_check_season != "Any":
            try:
                if not matches_weather(f, layer_check_season):
                    continue
            except Exception:
                pass
        all_names_layer.append(n)
    all_names_layer = sorted(all_names_layer)
    st.caption(f"{len(all_names_layer)} bottle(s) in picker for this season filter")
    layer_pick = st.multiselect(
        "Bottles to layer",
        all_names_layer,
        key="roulette_layer_pick",
        placeholder="Choose 2+ fragrances...",
    )
    lc1, lc2 = st.columns(2)
    with lc1:
        run_layer = st.button(
            "Check layer", type="primary", key="roulette_layer_check", use_container_width=True
        )
    with lc2:
        if st.button("Clear picks", key="roulette_layer_clear", use_container_width=True):
            st.session_state["_clear_roulette_layer_pick"] = True
            st.rerun()

    if run_layer:
        if len(layer_pick) < 2:
            st.warning("Pick at least two bottles.")
        else:
            result = evaluate_layer_recipe(list(layer_pick))
            # Fresh random poetic name from notes each time you check
            result["suggested_name"] = suggest_recipe_name_from_notes(
                list(layer_pick), randomize=True
            )
            st.session_state["last_layer_check"] = result
            st.session_state["_seed_roulette_recipe_name"] = True
            st.session_state["_scroll_to_layer_result"] = True
            st.rerun()

    _rl_save_flash = st.session_state.pop("_roulette_recipe_save_flash", None)
    if _rl_save_flash:
        st.success(_rl_save_flash)

    ev = st.session_state.get("last_layer_check")
    if ev:
        label = ev.get("label") or "?"
        st.markdown("### " + str(label))
        st.write(ev.get("verdict") or "")
        if ev.get("why"):
            st.info("**Why this layer:** " + str(ev.get("why")))
        st.caption(
            "Score: **" + str(ev.get("score", 0)) + "**  |  Suggested name (from notes): *"
            + str(ev.get("suggested_name") or "")
            + "*  -  use **Reroll name from notes** for another"
        )
        season = ev.get("season") or {}
        if season.get("detail"):
            st.info(season.get("detail"))
        app = ev.get("application") or {}
        steps = app.get("steps") or []
        if steps:
            st.markdown("#### How to wear this layer")
            st.caption(
                "Order is heaviest to lightest. Apply in this order on skin."
            )
            for s in steps:
                st.markdown(
                    f"**{s.get('order')}. {s.get('name')}** (*{s.get('brand')}*)  \n"
                    f"Role: **{s.get('role')}** | Suggested sprays: **{s.get('sprays')}**  \n"
                    f"{s.get('where')}  \n"
                    f"Families: {s.get('cats') or '-'} | Weight score: {s.get('weight')}"
                )
            st.markdown("**Tips**")
            for t in app.get("tips") or []:
                st.caption("- " + t)
            if app.get("order_names"):
                st.success(
                    "Spray order: " + "  ->  ".join(app.get("order_names") or [])
                )
        for pair in ev.get("pairs") or []:
            line = (
                "**" + str(pair.get("a")) + "** + **" + str(pair.get("b"))
                + "** (pair score " + str(pair.get("score")) + ")"
            )
            st.markdown(line)
            st.caption(str(pair.get("cats") or ""))
            for r in (pair.get("reasons") or [])[:4]:
                st.caption("- " + str(r))
        share_txt = format_recipe_share_text(
            recipe={
                "name": ev.get("suggested_name"),
                "bottles": [fr.get("name") for fr in (ev.get("frags") or []) if fr.get("name")],
                "gender": st.session_state.get("roulette_layer_recipe_gender")
                or recipe_gender_from_frags(ev.get("frags") or []),
                "season_label": (ev.get("season") or {}).get("label"),
                "why": ev.get("why"),
                "application": ev.get("application"),
            },
            ev=ev,
        )
        with st.expander("Copy recipe to share", expanded=False):
            st.caption("Select all, copy, and paste into a text or note.")
            st.text_area(
                "Share text",
                value=share_txt,
                height=220,
                key="layer_check_share_text",
            )

        with st.expander("Notes side by side", expanded=False):
            for fr in ev.get("frags") or []:
                st.markdown(
                    "**" + str(fr.get("name")) + "** (*" + str(fr.get("brand")) + "*)"
                )
                st.caption(str(fr.get("notes") or "(no notes)"))

        names = [fr.get("name") for fr in (ev.get("frags") or []) if fr.get("name")]
        suggested = (ev.get("suggested_name") or "").strip()
        # Seed name once when a new layer check appears (avoid value= + key conflict)
        if st.session_state.pop("_seed_roulette_recipe_name", False) or (
            "roulette_layer_recipe_name" not in st.session_state and suggested
        ):
            st.session_state["roulette_layer_recipe_name"] = suggested
        # Reroll before the text input so the new name is applied this run
        if st.session_state.pop("_reroll_layer_name", False) and names:
            new_nm = suggest_recipe_name_from_notes(names, randomize=True)
            st.session_state["roulette_layer_recipe_name"] = new_nm
            if isinstance(st.session_state.get("last_layer_check"), dict):
                st.session_state["last_layer_check"]["suggested_name"] = new_nm
            suggested = new_nm
        save_name = st.text_input(
            "Save as recipe name",
            key="roulette_layer_recipe_name",
            placeholder=suggested or "e.g. Coconut vanilla night",
        )
        # Auto gender from bottles; allow override
        _auto_g = recipe_gender_from_frags(ev.get("frags") or [])
        recipe_gender = st.selectbox(
            "Gender for this recipe (auto from bottles)",
            ["Any", "Female", "Male", "Unisex"],
            index=["Any", "Female", "Male", "Unisex"].index(_auto_g)
            if _auto_g in ("Any", "Female", "Male", "Unisex")
            else 0,
            key="roulette_layer_recipe_gender",
            help="Detected from the bottles' genders. Change if you want a different lean.",
        )
        st.caption(f"Auto-detected from notes/bottles: **{_auto_g}**")
        if st.button("Reroll name from notes", key="roulette_layer_reroll_name"):
            st.session_state["_reroll_layer_name"] = True
            st.rerun()
        rb1, rb2 = st.columns(2)
        with rb1:
            if st.button("Wear this layer on SOTD", key="roulette_layer_to_sotd"):
                if names:
                    send_to_sotd(names, notes=suggested or "Layer check")
                    st.rerun()
        with rb2:
            if st.button("Save recipe", type="primary", key="roulette_layer_save_recipe"):
                if len(names) < 2:
                    st.warning("Need at least two bottles to save a recipe.")
                else:
                    final_name = (save_name or "").strip() or suggested or "Untitled layer"
                    # Avoid exact duplicates (same name + same bottle set)
                    existing = st.session_state.get("layer_recipes") or []
                    bottles_key = tuple(sorted(names))
                    already = any(
                        (r.get("name") or "").strip().lower() == final_name.lower()
                        and tuple(sorted(r.get("bottles") or [])) == bottles_key
                        for r in existing
                    )
                    if already:
                        st.session_state["_roulette_recipe_save_flash"] = (
                            f"Recipe **{final_name}** already saved."
                        )
                    else:
                        _ev_r = st.session_state.get("last_layer_check") or evaluate_layer_recipe(list(names))
                        st.session_state.setdefault("layer_recipes", []).insert(
                            0,
                            {
                                "name": final_name,
                                "bottles": list(names),
                                "season_label": season.get("label", "") or ((_ev_r or {}).get("season") or {}).get("label", ""),
                                "season_detail": season.get("detail", "") or ((_ev_r or {}).get("season") or {}).get("detail", ""),
                                "bands": list(((_ev_r or {}).get("season") or {}).get("bands") or season.get("bands") or []),
                                "application": (_ev_r or {}).get("application") or {},
                                "score": (_ev_r or {}).get("score"),
                                "label": (_ev_r or {}).get("label"),
                                "verdict": (_ev_r or {}).get("verdict"),
                                "why": (_ev_r or {}).get("why") or "",
                                "gender": st.session_state.get("roulette_layer_recipe_gender", "Any"),
                            },
                        )
                        mark_vault_dirty()
                        save_persisted_data(force=False)
                        st.session_state["_vault_fp"] = vault_fingerprint()
                        st.session_state["_roulette_recipe_save_flash"] = (
                            f"Saved **{final_name}** "
                            f"(season: {season.get('label', '?')}). "
                            "See Layer tab  ->  Saved layer recipes."
                        )
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
                        log_sotd_immediate([f1["name"], f2["name"]], notes="Layer")
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
        if st.session_state.pop("_apply_recipe_name", False) and len(rec_pick) >= 2:
            fresh = suggest_recipe_name_from_notes(list(rec_pick), randomize=True)
            st.session_state["recipe_name_in"] = fresh
            suggested = fresh
        rec_name = st.text_input(
            "Recipe name",
            placeholder=suggested or "e.g. Coconut vanilla night",
            key="recipe_name_in",
        )
        rn1, rn2 = st.columns(2)
        with rn1:
            if st.button(
                "Random name from notes",
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
                _ev_save = preview if preview else evaluate_layer_recipe(list(rec_pick))
                st.session_state["layer_recipes"].insert(
                    0,
                    {
                        "name": final_name,
                        "bottles": list(rec_pick),
                        "season_label": season.get("label", "") or (_ev_save or {}).get("season", {}).get("label", ""),
                        "season_detail": season.get("detail", "") or (_ev_save or {}).get("season", {}).get("detail", ""),
                        "bands": list(((_ev_save or {}).get("season") or {}).get("bands") or season.get("bands") or []),
                        "suggested_name": suggested,
                        "application": (_ev_save or {}).get("application") or {},
                        "score": (_ev_save or {}).get("score"),
                        "label": (_ev_save or {}).get("label"),
                        "verdict": (_ev_save or {}).get("verdict"),
                        "why": (_ev_save or {}).get("why") or "",
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

        rf1, rf2 = st.columns(2)
        with rf1:
            recipe_band_filter = st.selectbox(
                "Show recipes for season / temp",
                ["Any", "Hot / Summer", "Warm / Mild", "Cool / Autumn", "Cold / Winter"],
                key="recipe_band_filter",
            )
        with rf2:
            recipe_gender_filter = st.selectbox(
                "Recipe gender",
                ["Any", "Female", "Male", "Unisex"],
                key="recipe_gender_filter",
            )
        recipes_view = st.session_state.get("layer_recipes") or []
        if recipe_band_filter != "Any":
            recipes_view = recipes_for_band(
                recipe_band_filter,
                gender=recipe_gender_filter,
                limit=50,
            )
        elif recipe_gender_filter != "Any":
            recipes_view = [
                r for r in recipes_view
                if (r.get("gender") or "Any") in ("Any", recipe_gender_filter)
            ]
        st.caption(f"{len(recipes_view)} recipe(s) shown")
        for ri, recipe in enumerate(recipes_view):
            bottles = list(recipe.get("bottles") or [])
            st.markdown(f"**{recipe.get('name', 'Recipe')}**")
            st.caption(
                " + ".join(bottles)
                + (f" | Best: {recipe.get('season_label')}" if recipe.get("season_label") else "")
                + (f" | Gender: {recipe.get('gender')}" if recipe.get("gender") else "")
            )
            ev = evaluate_layer_recipe(bottles)
            why = recipe.get("why") or ev.get("why")
            if why:
                st.info("**Why this layer:** " + str(why))
            season = ev.get("season") or {}
            saved_season = recipe.get("season_label") or season.get("label")
            if saved_season:
                st.caption(
                    f"Season: **{saved_season}** - "
                    f"{recipe.get('season_detail') or season.get('detail', '')}"
                )
            # Wear guidance (saved with recipe, or rebuilt from bottles)
            app = recipe.get("application") or ev.get("application") or {}
            steps = app.get("steps") or []
            if steps:
                with st.expander("How to wear", expanded=False):
                    st.caption("Heaviest first, lightest last.")
                    for s in steps:
                        st.markdown(
                            f"**{s.get('order')}. {s.get('name')}** - "
                            f"{s.get('role')} | **{s.get('sprays')}** spray(s)  \n"
                            f"{s.get('where')}"
                        )
                    if app.get("order_names"):
                        st.caption("Order: " + " -> ".join(app.get("order_names") or []))
                    for t in app.get("tips") or []:
                        st.caption("- " + t)
            with st.expander("Copy to share", expanded=False):
                st.text_area(
                    "Share text",
                    value=format_recipe_share_text(recipe=recipe, ev=ev, bottles=bottles),
                    height=200,
                    key=f"recipe_share_{ri}",
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
                    log_sotd_immediate(bottles, notes="Saved recipe")
                    st.rerun()
            with rb2:
                if st.button("Delete", key=f"recipe_del_{ri}_{recipe.get('name','')}"):
                    full = st.session_state.get("layer_recipes") or []
                    # delete by identity, not filtered index
                    for j, r in enumerate(full):
                        if r is recipe or (
                            r.get("name") == recipe.get("name")
                            and list(r.get("bottles") or []) == list(bottles)
                        ):
                            full.pop(j)
                            break
                    st.session_state["layer_recipes"] = full
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
                    <span class="floating-bat bat1">&#129415;</span>
                    <span class="floating-bat bat2">&#129415;</span>
                    <span class="floating-bat bat3">&#129415;</span>
                    <span class="floating-bat bat4">&#129415;</span>
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
            rc1, rc2, rc3 = st.columns(3)
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
            with rc3:
                if st.button(
                    "Log to SOTD",
                    key=f"roulette_sotd_{chosen['name']}",
                    type="primary",
                ):
                    log_sotd_immediate([chosen["name"]], notes="Roulette")
                    st.rerun()

# ===== SOTD =====
with tab_sotd:
    st.subheader("Scent of the Day")
    _ready2 = st.session_state.pop("_sotd_ready_flash", None)
    if _ready2:
        st.success(_ready2)
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
        horror_gender = st.selectbox(
            "Gender filter",
            ["Any", "Female", "Male", "Unisex"],
            key="sotd_horror_gender",
        )
        hp = HORROR_SCENT_PROFILES[horror_mode]
        st.write(hp.get("blurb", ""))
        if st.button("Draw horror night scents", type="primary", key="sotd_horror_draw"):
            picks = get_horror_picks(horror_mode, top_n=3, gender=horror_gender)
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
                    log_sotd_immediate(
                        [f["name"]],
                        notes=str((last_h or {}).get("vibe") or "Horror night"),
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
            partners = suggest_partners_for(primary, num=8)
            if not partners:
                st.write("No strong partners found (or everything else is DEL).")
            else:
                for pi, item in enumerate(partners):
                    pf, reason = item[0], item[1]
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
                    log_sotd_immediate(
                        [f1["name"], f2["name"]],
                        notes=f"Layer: {f1['name']} + {f2['name']}",
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
            mark_vault_dirty()
            save_persisted_data(force=False)
            try:
                st.session_state["_vault_fp"] = vault_fingerprint()
            except Exception:
                pass
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
        st.caption("Edit a log if the wrong bottle or date was saved. Changes autosave.")
        all_names_sotd = sorted(
            f.get("name")
            for f in (st.session_state.get("fragrances_db") or [])
            if f.get("name")
        )
        hist = list(st.session_state.get("sotd_history") or [])
        if not hist:
            st.caption("No SOTD entries yet.")
        for i, entry in enumerate(hist):
            layer_badge = " | layering" if entry.get("is_layering") else ""
            notes_text = f" - {entry['notes']}" if entry.get("notes") else ""
            st.write(
                f"**{entry.get('date')}:** *{entry.get('scent')}*{layer_badge}{notes_text}"
            )
            with st.expander(f"Edit entry {i+1} - {entry.get('date', '?')}", expanded=False):
                cur_scents = entry.get("scents") or []
                if not cur_scents and entry.get("scent"):
                    cur_scents = [
                        p.strip()
                        for p in str(entry.get("scent")).split(" + ")
                        if p.strip()
                    ]
                # keep names not in vault so they are not lost
                name_opts = list(dict.fromkeys(list(all_names_sotd) + list(cur_scents)))
                new_scents = st.multiselect(
                    "Bottles",
                    name_opts,
                    default=[n for n in cur_scents if n in name_opts],
                    key=f"edit_sotd_scents_{i}_{entry.get('date')}",
                )
                try:
                    from datetime import date as _date
                    _d0 = entry.get("date") or pacific_today().isoformat()
                    if isinstance(_d0, str):
                        _parts = [int(x) for x in _d0[:10].split("-")]
                        _default_d = _date(_parts[0], _parts[1], _parts[2])
                    else:
                        _default_d = pacific_today()
                except Exception:
                    _default_d = pacific_today()
                new_date = st.date_input(
                    "Date",
                    value=_default_d,
                    key=f"edit_sotd_date_{i}_{entry.get('date')}",
                )
                new_notes = st.text_area(
                    "Notes",
                    value=entry.get("notes") or "",
                    key=f"edit_sotd_notes_{i}_{entry.get('date')}",
                )
                e1, e2 = st.columns(2)
                with e1:
                    if st.button("Save changes", type="primary", key=f"edit_sotd_save_{i}"):
                        if not new_scents:
                            st.warning("Keep at least one bottle.")
                        else:
                            when_s = (
                                new_date.isoformat()
                                if hasattr(new_date, "isoformat")
                                else str(new_date)
                            )
                            display = " + ".join(new_scents)
                            st.session_state["sotd_history"][i] = {
                                **entry,
                                "date": when_s,
                                "scents": list(new_scents),
                                "scent": display,
                                "notes": (new_notes or "").strip(),
                                "is_layering": len(new_scents) > 1,
                            }
                            mark_vault_dirty()
                            save_persisted_data(force=False)
                            try:
                                st.session_state["_vault_fp"] = vault_fingerprint()
                            except Exception:
                                pass
                            st.success(f"Updated: **{display}** on {when_s}")
                            st.rerun()
                with e2:
                    if st.button("Delete entry", key=f"del_sotd_{i}_{entry.get('date')}"):
                        st.session_state["sotd_history"].pop(i)
                        mark_vault_dirty()
                        save_persisted_data(force=False)
                        st.rerun()
        if hist and st.button("Clear entire journal", key="clear_sotd_all"):
            st.session_state["sotd_history"] = []
            mark_vault_dirty()
            save_persisted_data(force=False)
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

    # Must apply calculator / backup-restore results BEFORE chart selectboxes are created
    pending_chart = st.session_state.pop("_pending_chart_restore", None)
    if isinstance(pending_chart, dict):
        if pending_chart.get("sun") and pending_chart["sun"] in signs:
            st.session_state["chart_sun"] = pending_chart["sun"]
        if pending_chart.get("moon") and pending_chart["moon"] in signs:
            st.session_state["chart_moon"] = pending_chart["moon"]
        if pending_chart.get("rising") and pending_chart["rising"] in signs:
            st.session_state["chart_rising"] = pending_chart["rising"]
        if pending_chart.get("venus") and pending_chart["venus"] in signs:
            st.session_state["chart_venus"] = pending_chart["venus"]
        if pending_chart.get("his_sun") and pending_chart["his_sun"] in signs:
            st.session_state["chart_his_sun"] = pending_chart["his_sun"]
        if pending_chart.get("his_moon") and pending_chart["his_moon"] in signs:
            st.session_state["chart_his_moon"] = pending_chart["his_moon"]
        if pending_chart.get("his_rising") and pending_chart["his_rising"] in signs:
            st.session_state["chart_his_rising"] = pending_chart["his_rising"]
        if pending_chart.get("his_venus") and pending_chart["his_venus"] in signs:
            st.session_state["chart_his_venus"] = pending_chart["his_venus"]
        if pending_chart.get("his_full"):
            st.session_state["birth_calc_his_full"] = pending_chart["his_full"]

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

    if st.session_state.pop("_apply_birth_chart_his", False):
        calc = st.session_state.get("birth_calc_full") or {}
        if calc.get("sun") and calc["sun"] in signs:
            st.session_state["chart_his_sun"] = calc["sun"]
        if calc.get("moon") and calc["moon"] in signs:
            st.session_state["chart_his_moon"] = calc["moon"]
        if calc.get("rising") and calc["rising"] in signs:
            st.session_state["chart_his_rising"] = calc["rising"]
        if calc.get("venus") and calc["venus"] in signs:
            st.session_state["chart_his_venus"] = calc["venus"]
        st.session_state["birth_calc_his_full"] = calc
        st.session_state["_chart_apply_flash_his"] = True

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
            apply_target = st.radio(
                "Apply calculated chart to",
                ["Me (her)", "Him"],
                horizontal=True,
                key="birth_calc_apply_target",
            )
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
                target = st.session_state.get("birth_calc_apply_target") or "Me (her)"
                if target.startswith("Him"):
                    st.session_state["_apply_birth_chart_his"] = True
                else:
                    st.session_state["_apply_birth_chart"] = True
                st.rerun()
            else:
                st.warning("Calculate a chart first.")


    st.markdown("#### His chart")
    st.caption("Your husband's signs - for compatibility layers and shared picks. Save chart stores both.")
    if "chart_his_sun" not in st.session_state:
        st.session_state["chart_his_sun"] = signs[0]
    if "chart_his_moon" not in st.session_state:
        st.session_state["chart_his_moon"] = signs[0]
    if "chart_his_rising" not in st.session_state:
        st.session_state["chart_his_rising"] = signs[0]
    if "chart_his_venus" not in st.session_state:
        st.session_state["chart_his_venus"] = signs[0]

    hh1, hh2, hh3, hh4 = st.columns(4)
    with hh1:
        his_sun = st.selectbox("His Sun", signs, key="chart_his_sun")
    with hh2:
        his_moon = st.selectbox("His Moon", signs, key="chart_his_moon")
    with hh3:
        his_rise = st.selectbox("His Rising", signs, key="chart_his_rising")
    with hh4:
        his_venus = st.selectbox("His Venus", signs, key="chart_his_venus")

    if st.session_state.pop("_chart_apply_flash_his", False):
        st.success("Calculator signs applied to his chart. Save chart to keep them.")

    his_sun_p = SIGN_SCENT_PROFILE.get(his_sun, {})
    st.caption(
        f"His Sun {his_sun} ({his_sun_p.get('element', '?')} - {his_sun_p.get('vibe', '')}) | "
        f"Moon {his_moon} | Rising {his_rise} | Venus {his_venus}"
    )

    st.markdown("#### Compatibility (you + him)")
    her_c = {"sun": sun_s, "moon": moon_s, "rising": rise_s, "venus": venus_s}
    him_c = {"sun": his_sun, "moon": his_moon, "rising": his_rise, "venus": his_venus}
    st.write(compatibility_blurb(her_c, him_c))
    st.caption("Shared layer / date-night ideas from both charts:")
    for i, f in enumerate(compatibility_bottles(her_c, him_c, top_n=4), 1):
        st.markdown(
            f"**{i}. {f.get('name')}** - *{f.get('brand')}* | "
            + ", ".join((f.get("category") or [])[:3])
        )

    st.markdown("#### Chart tools")
    tool = st.radio(
        "Tool",
        ["Sign matches", "Element wardrobe", "Moon phase", "Placement of the day"],
        horizontal=True,
        key="chart_tool_mode",
    )
    if tool == "Sign matches":
        which = st.selectbox(
            "Whose placement",
            [
                f"My Sun ({sun_s})",
                f"My Moon ({moon_s})",
                f"My Rising ({rise_s})",
                f"My Venus ({venus_s})",
                f"His Sun ({his_sun})",
                f"His Moon ({his_moon})",
                f"His Venus ({his_venus})",
            ],
            key="chart_tool_sign_which",
        )
        sign = which.split("(")[-1].rstrip(")")
        st.caption((SIGN_SCENT_PROFILE.get(sign) or {}).get("vibe", ""))
        for i, f in enumerate(bottles_for_sign(sign, top_n=5), 1):
            st.markdown(
                f"**{i}. {f.get('name')}** - *{f.get('brand')}* | "
                + ", ".join((f.get("category") or [])[:3])
            )
    elif tool == "Element wardrobe":
        els = chart_elements(sun_s, moon_s, rise_s, venus_s)
        st.caption("Your chart element mix: " + (", ".join(f"{k} x{v}" for k, v in els.items()) or "set signs"))
        pick_el = st.selectbox(
            "Element",
            ["Fire", "Earth", "Air", "Water"],
            key="chart_tool_element",
        )
        for i, f in enumerate(bottles_for_element(pick_el, top_n=5), 1):
            st.markdown(
                f"**{i}. {f.get('name')}** - *{f.get('brand')}* | "
                + ", ".join((f.get("category") or [])[:3])
            )
    elif tool == "Moon phase":
        phase = moon_phase_name()
        prof = moon_phase_scent_profile(phase)
        st.write(f"**{phase}** - {prof.get('blurb')}")
        for i, f in enumerate(bottles_for_moon_phase(phase, top_n=5), 1):
            st.markdown(
                f"**{i}. {f.get('name')}** - *{f.get('brand')}* | "
                + ", ".join((f.get("category") or [])[:3])
            )
    else:
        # Placement of the day - use day ruler planet mapped loosely to chart point
        import datetime as _dt
        day_name = pacific_today().strftime("%A")
        day_prof = DAY_RULER.get(day_name, {})
        planet = day_prof.get("planet", "Moon")
        focus_map = {
            "Moon": ("My Moon", moon_s),
            "Venus": ("My Venus", venus_s),
            "Mars": ("My Sun", sun_s),
            "Mercury": ("My Rising", rise_s),
            "Sun": ("My Sun", sun_s),
            "Jupiter": ("My Sun", sun_s),
            "Saturn": ("My Rising", rise_s),
        }
        label, focus_sign = focus_map.get(planet, ("My Moon", moon_s))
        st.write(
            f"**{day_name}** ruled by **{planet}** - leaning on {label} (**{focus_sign}**). "
            f"{day_prof.get('vibe', '')}"
        )
        for i, f in enumerate(bottles_for_sign(focus_sign, top_n=5), 1):
            st.markdown(
                f"**{i}. {f.get('name')}** - *{f.get('brand')}* | "
                + ", ".join((f.get("category") or [])[:3])
            )

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
                        log_sotd_immediate([f["name"]], notes="Stars pick")
                        st.rerun()
                st.markdown("---")


# ===== PLAY =====
with tab_play:
    st.subheader("Play")
    st.caption("Three games only - Mood, Blind bottle, Family roulette.")

    # Reset invalid play_mode from older builds
    _allowed_play = ["Mood board", "Blind bottle", "Family roulette", "Halloween", "Tarot"]
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
        # salt lets you redraw different options for the same mood
        if "mood_salt" not in st.session_state:
            st.session_state["mood_salt"] = 0
        md1, md2 = st.columns(2)
        with md1:
            draw_clicked = st.button("Draw mood scents", type="primary", key="mood_draw", use_container_width=True)
        with md2:
            redraw_clicked = st.button("Redraw options", key="mood_redraw", use_container_width=True)
        if draw_clicked or redraw_clicked:
            if redraw_clicked:
                st.session_state["mood_salt"] = int(st.session_state.get("mood_salt", 0)) + 1
            elif draw_clicked:
                # fresh draw starts at current salt (or 0 if mood changed)
                if st.session_state.get("last_mood", {}).get("mood") != mood:
                    st.session_state["mood_salt"] = 0
            salt = int(st.session_state.get("mood_salt", 0))
            picks = get_mood_picks(mood, top_n=3, pool=play_pool, salt=salt)
            st.session_state["last_mood"] = {"mood": mood, "picks": picks, "salt": salt}
            st.session_state["play_stats"]["moods_drawn"] = (
                st.session_state["play_stats"].get("moods_drawn", 0) + 1
            )
            save_persisted_data()
            st.rerun()
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
                    if st.button("Log to SOTD", key=f"mood_wear_{i}"):
                        log_sotd_immediate([f["name"]], notes="Play mood")
                        st.rerun()


    elif play_mode == "Halloween":
        st.markdown(
            '<div style="border:1px solid #3a2040;border-radius:10px;padding:0.75rem 1rem;'
            'background:linear-gradient(135deg,#120810,#1a0e18);margin-bottom:0.5rem;">'
            '<div style="font-family:Cinzel,Georgia,serif;color:#c9a0ff;font-size:1.05rem;">'
            + emoji_html("pumpkin", "ghost", "bat")
            + " Halloween "
            + emoji_html("bat", "ghost", "pumpkin")
            + "</div>"
            '<div style="color:#a890b8;font-size:0.85rem;">'
            "Seasonal vibes from your vault - filter with Gender + Season above, then draw.</div>"
            '</div>',
            unsafe_allow_html=True,
        )
        hall_mode = st.selectbox(
            "Halloween mood",
            list(HALLOWEEN_PROFILES.keys()),
            key="play_halloween_mode",
        )
        hp = HALLOWEEN_PROFILES[hall_mode]
        mood_emoji = emoji_html(HALLOWEEN_EMOJI.get(hall_mode, "ghost"))
        st.markdown(
            mood_emoji + " **" + hall_mode + "** - " + (hp.get("blurb") or ""),
            unsafe_allow_html=True,
        )
        st.caption("Lean: " + ", ".join(hp.get("categories") or []))
        if "halloween_salt" not in st.session_state:
            st.session_state["halloween_salt"] = 0
        h1, h2 = st.columns(2)
        with h1:
            h_draw = st.button(
                "Draw Halloween scents",
                type="primary",
                key="halloween_draw",
                use_container_width=True,
            )
        with h2:
            h_redraw = st.button(
                "Redraw",
                key="halloween_redraw",
                use_container_width=True,
            )
        if h_draw or h_redraw:
            if h_redraw:
                st.session_state["halloween_salt"] = int(
                    st.session_state.get("halloween_salt", 0)
                ) + 1
            elif h_draw and st.session_state.get("last_halloween", {}).get("mode") != hall_mode:
                st.session_state["halloween_salt"] = 0
            salt = int(st.session_state.get("halloween_salt", 0))
            picks = get_halloween_picks(
                hall_mode,
                top_n=5,
                gender=play_gender,
                season_band=play_season,
                salt=salt,
            )
            st.session_state["last_halloween"] = {
                "mode": hall_mode,
                "picks": picks,
                "gender": play_gender,
                "season": play_season,
            }
            st.rerun()
        last_h = st.session_state.get("last_halloween")
        if last_h:
            _he = emoji_html(HALLOWEEN_EMOJI.get(last_h.get("mode") or "", "pumpkin"))
            st.markdown(
                _he
                + " Drawn for: **"
                + str(last_h.get("mode"))
                + "** | "
                + str(last_h.get("gender"))
                + " | "
                + str(last_h.get("season")),
                unsafe_allow_html=True,
            )
            picks = last_h.get("picks") or []
            if not picks:
                st.info("No matches in your vault for that filter combo - try Any gender/season.")
            for i, f in enumerate(picks):
                badge = (
                    " YAY"
                    if st.session_state.get("user_reactions", {}).get(f.get("name")) == "fav"
                    else ""
                )
                st.markdown(
                    f"**{i+1}. {f.get('name')}**{badge} - *{f.get('brand')}* | "
                    + ", ".join((f.get("category") or [])[:4])
                )
                if st.button("Log to SOTD", key=f"hall_wear_{i}_{f.get('name','')}"):
                    log_sotd_immediate([f.get("name")], notes="Halloween play")
                    st.rerun()


    elif play_mode == "Tarot":
        st.markdown(
            '<div style="border:1px solid #3a2040;border-radius:10px;padding:0.75rem 1rem;'
            'background:linear-gradient(135deg,#100818,#1a1020);margin-bottom:0.5rem;">'
            '<div style="font-family:Cinzel,Georgia,serif;color:#c9a0ff;font-size:1.05rem;">'
            + emoji_html("alien", "sparkles")
            + " Tarot draw "
            + emoji_html("sparkles", "alien")
            + "</div>"
            '<div style="color:#a890b8;font-size:0.85rem;">One card. One mood. Three bottles from your vault.</div>'
            '</div>',
            unsafe_allow_html=True,
        )
        if "tarot_salt" not in st.session_state:
            st.session_state["tarot_salt"] = 0
        t1, t2 = st.columns(2)
        with t1:
            t_draw = st.button("Draw a card", type="primary", key="tarot_draw", use_container_width=True)
        with t2:
            t_redraw = st.button("Redraw card", key="tarot_redraw", use_container_width=True)
        if t_draw or t_redraw:
            if t_redraw:
                st.session_state["tarot_salt"] = int(st.session_state.get("tarot_salt", 0)) + 1
            card = draw_tarot_card(salt=int(st.session_state.get("tarot_salt", 0)))
            mood_name = card.get("mood") or "Soft"
            # map Lazy / stay home if present
            if mood_name not in MOOD_PROFILES and mood_name == "Lazy / stay home":
                pass
            picks = []
            if mood_name in MOOD_PROFILES:
                picks = get_mood_picks(
                    mood_name,
                    top_n=3,
                    pool=play_pool,
                    salt=int(st.session_state.get("tarot_salt", 0)),
                )
            st.session_state["last_tarot"] = {"card": card, "picks": picks}
            st.rerun()
        last_t = st.session_state.get("last_tarot")
        if last_t:
            card = last_t.get("card") or {}
            st.markdown(
                emoji_html("alien", "sparkles")
                + " <strong style='font-size:1.25rem;color:#c9a0ff;'>"
                + str(card.get("name", "Card"))
                + "</strong> "
                + emoji_html("sparkles"),
                unsafe_allow_html=True,
            )
            st.caption(card.get("blurb") or "")
            st.write(f"Mood lean: **{card.get('mood')}**")
            for i, f in enumerate(last_t.get("picks") or []):
                st.markdown(
                    f"**{i+1}. {f.get('name')}** - *{f.get('brand')}* | "
                    + ", ".join((f.get("category") or [])[:3])
                )
                if st.button("Log to SOTD", key=f"tarot_wear_{i}"):
                    log_sotd_immediate([f.get("name")], notes="Tarot play")
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
            if st.button("Log to SOTD", key="blind_wear"):
                log_sotd_immediate([mystery["name"]], notes="Blind bottle")
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
                        if st.button("Log to SOTD", key=f"fam_wear_{i}"):
                            log_sotd_immediate([f["name"]], notes="Family play")
                            st.rerun()

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

    val = collection_value_summary(st.session_state["fragrances_db"])
    if val["priced"] or val["sized"] or val["by_shelf"]:
        v1, v2, v3 = st.columns(3)
        v1.metric("Logged ml", f"{val['total_ml']:.0f}" if val["sized"] else "-")
        v2.metric("Logged value", f"${val['total_price']:.0f}" if val["priced"] else "-")
        shelf_bits = ", ".join(f"{k}: {n}" for k, n in sorted(val["by_shelf"].items()))
        v3.caption(f"Shelf: {shelf_bits}" if shelf_bits else "")


    badges = compute_badges()
    if badges:
        st.caption("Badges: " + "  -  ".join(badges))

    # ----- Browse by season -----
    with st.expander("Browse by season", expanded=True):
        st.caption(
            "All vault bottles grouped by weather band. "
            "A bottle can appear in more than one season if its tags fit."
        )
        season_bands = [
            ("Hot / Summer", "Hot / Summer"),
            ("Warm / Mild", "Warm / Mild"),
            ("Cool / Autumn", "Cool / Autumn"),
            ("Cold / Winter", "Cold / Winter"),
        ]
        show_gender = st.selectbox(
            "Gender filter for season lists",
            ["Any", "Female", "Male", "Unisex"],
            key="collection_season_gender",
        )
        pool = list(st.session_state.get("fragrances_db") or [])
        if show_gender != "Any":
            pool = [f for f in pool if matches_gender(f, show_gender)]

        # Bottles with weak/empty season tags
        unclear = []
        for f in pool:
            s = (f.get("season") or "").strip()
            if not s or s.lower() in ("versatile", "any", "year-round", "year round"):
                # still may match bands via matches_weather - track for "flexible" list
                pass

        for band_label, band_key in season_bands:
            matched = []
            for f in pool:
                try:
                    if matches_weather(f, band_key):
                        matched.append(f)
                except Exception:
                    continue
            matched.sort(key=lambda x: (x.get("brand") or "").lower() + (x.get("name") or "").lower())
            with st.expander(
                f"{band_label}  -  {len(matched)} bottle(s)",
                expanded=False,
            ):
                if not matched:
                    st.caption("No bottles match this band with the current gender filter.")
                else:
                    for f in matched:
                        cats = ", ".join((f.get("category") or [])[:4])
                        conc = f.get("concentration") or ""
                        conc_bit = f" | {conc}" if conc else ""
                        line1 = "**" + str(f.get("name") or "") + "** - *" + str(f.get("brand") or "") + "*"
                        line2 = str(f.get("gender") or "?") + " | Season tags: " + str(f.get("season") or "?") + conc_bit
                        st.markdown(line1 + "\n\n" + line2 + "\n\n" + cats)
                        st.caption((f.get("notes") or "")[:160])

        # Flexible / versatile list
        flexible = []
        for f in pool:
            s = (f.get("season") or "").lower()
            if (
                "versatile" in s
                or "year-round" in s
                or "year round" in s
                or not (f.get("season") or "").strip()
            ):
                flexible.append(f)
        flexible.sort(key=lambda x: (x.get("name") or "").lower())
        with st.expander(
            f"Versatile / flexible  -  {len(flexible)} bottle(s)",
            expanded=False,
        ):
            st.caption("Tagged versatile, year-round, or missing a clear season.")
            if not flexible:
                st.caption("None.")
            else:
                for f in flexible:
                    st.markdown(
                        f"**{f.get('name')}**  -  *{f.get('brand')}* | "
                        f"{f.get('season') or 'no season tag'}"
                    )

    # ----- Wishlist -----
    with st.expander("Wishlist", expanded=False):
        st.caption("Track bottles you want. Check off, then To vault (or move all checked) to add them to your collection.")
        # --- Weekly Middle Eastern suggestions ---
        with st.expander("Weekly ME ideas for you", expanded=True):
            st.caption(
                "Middle Eastern picks based on your vault tastes. Rotates each week. "
                "Already-owned and already-wishlisted bottles are skipped."
            )
            ideas = weekly_wishlist_suggestions(n=5)
            if not ideas:
                st.info("No new ME ideas right now - your vault/wishlist may already cover the pool.")
            else:
                for j, idea in enumerate(ideas):
                    ic1, ic2 = st.columns([4, 1])
                    with ic1:
                        st.markdown(
                            f"**{idea.get('name')}** - *{idea.get('brand')}*  \n"
                            f"{idea.get('why') or ''}"
                        )
                    with ic2:
                        if st.button("Add", key=f"me_wish_add_{j}_{idea.get('name','')}"):
                            st.session_state.setdefault("wishlist", []).insert(
                                0,
                                {
                                    "name": idea.get("name") or "",
                                    "brand": idea.get("brand") or "",
                                    "notes": idea.get("why") or "Weekly ME suggestion",
                                    "checked": False,
                                },
                            )
                            save_persisted_data()
                            st.success(f"Added {idea.get('name')} to wishlist")
                            st.rerun()

        # Clear form fields before widgets if flagged
        if st.session_state.pop("_clear_wishlist_form", False):
            st.session_state["wl_name"] = ""
            st.session_state["wl_brand"] = ""
            st.session_state["wl_notes"] = ""
        wl_name = st.text_input("Name", key="wl_name")
        wl_brand = st.text_input("Brand (optional)", key="wl_brand")
        wl_notes = st.text_input("Notes (optional)", key="wl_notes")
        wl_g, wl_s = st.columns(2)
        with wl_g:
            wl_gender = st.selectbox(
                "Gender (for vault later)",
                ["Unisex", "Female", "Male", "Female-leaning", "Male-leaning"],
                key="wl_gender",
            )
        with wl_s:
            wl_season = st.selectbox(
                "Season (for vault later)",
                ["Versatile", "Fall, Winter", "Spring, Summer", "Hot / Summer", "Cool / Autumn", "Cold / Winter"],
                key="wl_season",
            )
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
                        "gender": wl_gender,
                        "season": wl_season,
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

    # Collection browser filters
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
    browse_concentration = st.selectbox(
        "Format / concentration",
        ["Any"] + CONCENTRATION_OPTIONS,
        key="browse_concentration",
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
    if browse_concentration != "Any":
        db = [
            f for f in db
            if (f.get("concentration") or "") == browse_concentration
        ]

    if browse_sort == "Name (A-Z)":
        db.sort(key=lambda x: x["name"].lower())
    elif browse_sort == "Brand (A-Z)":
        db.sort(key=lambda x: (x["brand"].lower(), x["name"].lower()))
    elif browse_sort == "Most worn":
        db.sort(key=lambda x: wear_counts.get(x["name"], 0), reverse=True)
    else:
        db.sort(key=lambda x: (",".join(x.get("category", [])), x["name"].lower()))

    # Short notes - easiest way to spot thin profiles
    short_rows = short_notes_bottles(40)
    with st.expander(
        f"Short notes ({len(short_rows)} bottles)",
        expanded=bool(short_rows),
    ):
        st.caption(
            "Sorted shortest first. Under ~40 characters (or vague text) is flagged. "
            "Pick one and expand notes with Top / Heart / Base."
        )
        if not short_rows:
            st.success("No short notes - everything looks detailed enough.")
        else:
            # Quick length legend
            st.write(
                f"**{sum(1 for r in short_rows if r['chars'] < 15)}** very short "
                f"(under 15 chars)  |  "
                f"**{sum(1 for r in short_rows if 15 <= r['chars'] < 40)}** short "
                f"(15-39)  |  "
                f"**{sum(1 for r in short_rows if r['chars'] >= 40)}** vague but longer"
            )
            for ri, r in enumerate(short_rows[:50]):
                f = r["frag"]
                c_a, c_b = st.columns([5, 1])
                with c_a:
                    st.markdown(
                        f"**{r['chars']} chars** - **{f.get('name')}** "
                        f"(*{f.get('brand', '?')}*)  \n"
                        f"`{r['preview']}`"
                    )
                with c_b:
                    if st.button(
                        "Lookup",
                        key=f"short_lu_{ri}_{f.get('name','')}",
                        help="Open Fragrance lookup helper with this bottle",
                    ):
                        st.session_state["_pending_notes_lookup"] = {
                            "name": f.get("name") or "",
                            "brand": f.get("brand") or "",
                        }
                        st.rerun()
            if len(short_rows) > 50:
                st.caption(f"...and {len(short_rows) - 50} more")

            pick_short = st.selectbox(
                "Expand notes for",
                [f"{r['frag'].get('name')} ({r['chars']} chars)" for r in short_rows],
                key="short_notes_pick",
            )
            short_name = pick_short.rsplit(" (", 1)[0] if pick_short else ""
            frag_s = next(
                (
                    f
                    for f in st.session_state["fragrances_db"]
                    if f.get("name") == short_name
                ),
                None,
            )
            if frag_s:
                st.caption(
                    f"Current ({note_char_count(frag_s)} chars): "
                    f"{(frag_s.get('notes') or '')[:160]}"
                )
                # Inline online note search links for the selected bottle
                _lu = notes_lookup_suggestions(
                    frag_s.get("name") or "", frag_s.get("brand") or ""
                )
                _links = _lu.get("links") or {}
                if _links:
                    link_bits = []
                    for label in (
                        "Notes (Google)",
                        "Fragrantica search",
                        "Parfumo search",
                        "Fragrantica (Google site)",
                    ):
                        url = _links.get(label)
                        if url:
                            link_bits.append(f"[{label}]({url})")
                    if link_bits:
                        st.markdown("Search notes: " + " | ".join(link_bits))
                if st.button(
                    "Open in Fragrance lookup",
                    key=f"short_open_lu_{short_name}",
                    help="Prefill sidebar Fragrance lookup helper",
                ):
                    st.session_state["_pending_notes_lookup"] = {
                        "name": frag_s.get("name") or "",
                        "brand": frag_s.get("brand") or "",
                    }
                    st.rerun()
                new_n = st.text_area(
                    "Fuller notes (Top / Heart / Base)",
                    value=frag_s.get("notes") or "",
                    key=f"short_notes_area_{short_name}",
                    height=110,
                )
                if st.button("Save longer notes", type="primary", key="short_notes_save"):
                    for i, f in enumerate(st.session_state["fragrances_db"]):
                        if f.get("name") == short_name:
                            st.session_state["fragrances_db"][i]["notes"] = (
                                new_n.strip() or "Not specified"
                            )
                            break
                    try:
                        log_vault_action("edited", short_name, "short-notes")
                    except Exception:
                        pass
                    save_persisted_data()
                    st.success(
                        f"Saved **{short_name}** "
                        f"({len((new_n or '').strip())} chars)"
                    )
                    st.rerun()

    # Needs fix: notes, gender, season, category
    needs_all = fragrances_needing_fix("any")
    n_notes = len(fragrances_needing_fix("notes"))
    n_gender = len(fragrances_needing_fix("gender"))
    n_season = len(fragrances_needing_fix("season"))
    n_cat = len(fragrances_needing_fix("category"))
    with st.expander(
        f"Needs fix ({len(needs_all)} bottles)",
        expanded=len(needs_all) > 0,
    ):
        st.caption(
            "Bottles missing solid notes, gender, season, or categories. "
            "Fix here or in Vault - Edit."
        )
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Notes", n_notes)
        m2.metric("Gender", n_gender)
        m3.metric("Season", n_season)
        m4.metric("Category", n_cat)

        gap_filter = st.selectbox(
            "Show",
            ["All gaps", "Notes only", "Gender only", "Season only", "Category only"],
            key="needs_fix_filter",
        )
        field_map = {
            "All gaps": "any",
            "Notes only": "notes",
            "Gender only": "gender",
            "Season only": "season",
            "Category only": "category",
        }
        filtered = fragrances_needing_fix(field_map[gap_filter])
        if not filtered:
            st.success("Nothing in this filter - profiles look complete.")
        else:
            st.write(f"**{len(filtered)}** to review")
            st.caption("Tap **Lookup** to search notes in the sidebar Fragrance lookup helper.")
            for ni, item in enumerate(filtered[:40]):
                f = item["frag"]
                gap_txt = ", ".join(item["gaps"])
                n_a, n_b = st.columns([5, 1])
                with n_a:
                    st.markdown(
                        f"- **{f.get('name')}** (*{f.get('brand', '?')}*) - needs **{gap_txt}**"
                    )
                with n_b:
                    if st.button(
                        "Lookup",
                        key=f"need_lu_{ni}_{f.get('name','')}",
                        help="Search notes / gender / season online via Fragrance lookup",
                    ):
                        st.session_state["_pending_notes_lookup"] = {
                            "name": f.get("name") or "",
                            "brand": f.get("brand") or "",
                        }
                        st.rerun()
            if len(filtered) > 40:
                st.caption(f"...and {len(filtered) - 40} more")

            pick_labels = [
                f"{it['frag'].get('name')} [{', '.join(it['gaps'])}]"
                for it in filtered
            ]
            pick = st.selectbox("Fix this bottle", pick_labels, key="needs_fix_pick")
            pick_name = pick.split(" [")[0] if pick else ""
            frag = next(
                (
                    f
                    for f in st.session_state["fragrances_db"]
                    if f.get("name") == pick_name
                ),
                None,
            )
            if frag:
                gaps = profile_gaps(frag)
                st.caption("Missing: " + ", ".join(gaps) if gaps else "Looks complete")
                _lu = notes_lookup_suggestions(
                    frag.get("name") or "", frag.get("brand") or ""
                )
                _links = _lu.get("links") or {}
                if _links:
                    link_bits = []
                    for label in (
                        "Notes (Google)",
                        "Gender (Google)",
                        "Season (Google)",
                        "Category / accords (Google)",
                        "Fragrantica search",
                        "Parfumo search",
                    ):
                        url = _links.get(label)
                        if url:
                            link_bits.append(f"[{label}]({url})")
                    if link_bits:
                        st.markdown("Search profile: " + " | ".join(link_bits))
                if st.button(
                    "Open in Fragrance lookup",
                    key=f"need_open_lu_{pick_name}",
                    help="Prefill sidebar Fragrance lookup helper",
                ):
                    st.session_state["_pending_notes_lookup"] = {
                        "name": frag.get("name") or "",
                        "brand": frag.get("brand") or "",
                    }
                    st.rerun()
                gender_opts = [
                    "Unisex",
                    "Female",
                    "Male",
                    "Female-leaning",
                    "Male-leaning",
                ]
                g_cur = frag.get("gender") or "Unisex"
                g_idx = gender_opts.index(g_cur) if g_cur in gender_opts else 0
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
                    "Musky",
                    "Amber",
                    "Vanilla",
                    "Green",
                    "Aquatic",
                    "Chypre",
                    "Fougere",
                    "Animalic",
                    "Metallic",
                    "Creamy",
                ]
                fx1, fx2 = st.columns(2)
                with fx1:
                    e_gender = st.selectbox(
                        "Gender", gender_opts, index=g_idx, key=f"need_g_{pick_name}"
                    )
                with fx2:
                    e_season = st.text_input(
                        "Season",
                        value=frag.get("season") or "",
                        key=f"need_s_{pick_name}",
                        placeholder="e.g. Fall, Winter",
                    )
                e_notes = st.text_area(
                    "Notes (Top / Heart / Base)",
                    value=frag.get("notes") or "",
                    key=f"need_n_{pick_name}",
                    height=90,
                )
                e_cats = st.multiselect(
                    "Categories",
                    cat_opts,
                    default=[c for c in (frag.get("category") or []) if c in cat_opts],
                    key=f"need_c_{pick_name}",
                )
                if st.button("Save fixes", type="primary", key="needs_fix_save"):
                    for i, f in enumerate(st.session_state["fragrances_db"]):
                        if f.get("name") == pick_name:
                            st.session_state["fragrances_db"][i]["gender"] = e_gender
                            st.session_state["fragrances_db"][i]["season"] = (
                                e_season.strip() or "Versatile"
                            )
                            st.session_state["fragrances_db"][i]["notes"] = (
                                e_notes.strip() or "Not specified"
                            )
                            st.session_state["fragrances_db"][i]["category"] = (
                                e_cats if e_cats else list(f.get("category") or ["Gourmand"])
                            )
                            break
                    try:
                        log_vault_action("edited", pick_name, "needs-fix")
                    except Exception:
                        pass
                    save_persisted_data()
                    st.success(f"Updated **{pick_name}**")
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
    _rf = st.session_state.pop("_restore_flash", None)
    if _rf:
        st.success(_rf)
    st.subheader("Sanctuary vault")
    n_bottles = len(st.session_state["fragrances_db"])
    st.write(f"**{n_bottles}** bottles in the vault")
    _need = fragrances_needing_fix("any")
    if _need:
        st.warning(
            f"**{len(_need)}** bottle(s) need notes, gender, season, or category - "
            f"see Collection - Needs fix."
        )
    if st.session_state.get("last_saved_at"):
        st.caption(f"Last saved: {st.session_state['last_saved_at']} (Pacific)")
    st.caption(
        "Edits auto-save to the data file on this server. "
        "**Streamlit Cloud can wipe that file on redeploy**  -  export JSON after big changes."
    )
    if st.button("Save vault now", key="vault_force_save_btn"):
        ok = save_persisted_data(force=True)
        if ok:
            st.success(
                f"Saved **{len(st.session_state.get('fragrances_db') or [])}** bottles "
                f"at {st.session_state.get('last_saved_at')}."
            )
        else:
            st.error("Save did not complete - check the sidebar for details.")

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
                    e_price = frag.get("price")  # price UI removed
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
                    save_persisted_data(force=True)
                    st.session_state["_reset_remove_select"] = True
                    st.session_state["_remove_flash"] = remove_name
                    st.rerun()

        st.markdown("**Batch**")
        if st.session_state.pop("_clear_batch_remove_pick", False):
            st.session_state["batch_remove_pick"] = []
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
            save_persisted_data(force=True)
            st.session_state["_clear_batch_remove_pick"] = True
            st.success(f"Banished {len(names)} bottle(s).")
            st.rerun()

    
    
    
    with st.expander("Scent family helper", expanded=False):
        st.caption(
            "Paste notes (or pick a bottle) to get suggested scent families. "
            "You can also search your vault by family."
        )
        mode = st.radio(
            "Mode",
            ["Suggest from notes", "Search vault by family", "Check a bottle", "Audit whole vault"],
            horizontal=True,
            key="family_helper_mode",
        )
        if mode == "Suggest from notes":
            notes_in = st.text_area(
                "Notes or description",
                placeholder="e.g. Top - Vanilla, caramel / Heart - Jasmine / Base - Musk, sandalwood",
                key="family_notes_in",
                height=100,
            )
            if st.button("Suggest families", key="family_suggest_btn"):
                suggested = suggest_categories_from_notes(notes_in or "")
                if suggested:
                    st.success("Suggested: **" + " | ".join(suggested) + "**")
                    st.session_state["_last_family_suggest"] = suggested
                else:
                    st.info("No strong matches - try adding more note keywords.")
            if st.session_state.get("_last_family_suggest"):
                st.caption("Last suggestion: " + ", ".join(st.session_state["_last_family_suggest"]))
        elif mode == "Search vault by family":
            all_cats = sorted({
                c
                for f in (st.session_state.get("fragrances_db") or [])
                for c in (f.get("category") or [])
            })
            pick_cat = st.selectbox("Family / category", ["Any"] + all_cats, key="family_search_cat")
            q = st.text_input("Optional name filter", key="family_search_q")
            results = []
            for f in st.session_state.get("fragrances_db") or []:
                cats = f.get("category") or []
                if pick_cat != "Any" and pick_cat not in cats:
                    continue
                if q and q.lower() not in (f.get("name") or "").lower() and q.lower() not in (f.get("brand") or "").lower():
                    continue
                results.append(f)
            st.caption(f"{len(results)} match(es)")
            for f in results[:40]:
                st.markdown(
                    f"**{f.get('name')}**  -  *{f.get('brand')}* | "
                    + ", ".join(f.get("category") or [])
                )
            if len(results) > 40:
                st.caption(f"...and {len(results)-40} more")
        elif mode == "Check a bottle":  # Check a bottle
            names = sorted(f.get("name") or "" for f in (st.session_state.get("fragrances_db") or []))
            bottle = st.selectbox("Bottle", ["- select -"] + names, key="family_check_bottle")
            if bottle and bottle != "- select -":
                frag = next((f for f in st.session_state["fragrances_db"] if f.get("name") == bottle), None)
                if frag:
                    current = frag.get("category") or []
                    st.write("Current families: **" + (", ".join(current) if current else "none") + "**")
                    suggested = suggest_categories_from_notes(frag.get("notes") or "")
                    if suggested:
                        st.write("Suggested from notes: **" + " | ".join(suggested) + "**")
                        if st.button("Apply suggested families to this bottle", key="family_apply_btn"):
                            # merge unique
                            merged = list(dict.fromkeys(list(current) + suggested))
                            for i, f in enumerate(st.session_state["fragrances_db"]):
                                if f.get("name") == bottle:
                                    st.session_state["fragrances_db"][i]["category"] = merged
                                    break
                            log_vault_action("edited", bottle, "family-helper")
                            save_persisted_data()
                            st.success(f"Updated **{bottle}** -> {', '.join(merged)}")
                            st.rerun()
                    else:
                        st.info("No strong suggestions from the current notes.")

        elif mode == "Audit whole vault":
            st.caption(
                "Scans every bottle for missing or weak notes, gender, season, and scent families. "
                "You can auto-apply suggested families to bottles that need them."
            )
            run = st.button("Run full vault audit", type="primary", key="vault_audit_run")
            apply_all = st.checkbox(
                "Also auto-apply suggested families where categories look weak",
                value=False,
                key="vault_audit_apply",
            )
            if run or st.session_state.get("_audit_results"):
                if run:
                    issues = []
                    auto_fixed = 0
                    db = st.session_state.get("fragrances_db") or []
                    for i, f in enumerate(db):
                        name = f.get("name") or "?"
                        brand = f.get("brand") or "?"
                        notes = (f.get("notes") or "").strip()
                        gender = (f.get("gender") or "").strip()
                        season = (f.get("season") or "").strip()
                        cats = f.get("category") or []
                        flags = []
                        if len(notes) < 15:
                            flags.append("weak/missing notes")
                        if not gender:
                            flags.append("missing gender")
                        if not season or season.lower() in ("versatile", "any", ""):
                            if not season:
                                flags.append("missing season")
                        if not cats:
                            flags.append("no scent family")
                        elif len(cats) == 1 and cats[0] in ("Gourmand", "Sweet"):
                            # very generic single tag - still ok but note it
                            pass
                        # Suggest families from notes
                        suggested = suggest_categories_from_notes(notes) if notes else []
                        if flags or (suggested and set(suggested) - set(cats)):
                            issues.append({
                                "idx": i,
                                "name": name,
                                "brand": brand,
                                "flags": flags,
                                "current_cats": cats,
                                "suggested": suggested,
                            })
                        # Auto-apply if requested and categories are empty/weak
                        if apply_all and suggested:
                            if not cats or len(cats) <= 1:
                                merged = list(dict.fromkeys(list(cats) + suggested))
                                st.session_state["fragrances_db"][i]["category"] = merged
                                auto_fixed += 1
                    if apply_all and auto_fixed:
                        log_vault_action("edited", f"{auto_fixed} bottles", "audit-auto-family")
                        save_persisted_data()
                    st.session_state["_audit_results"] = {
                        "issues": issues,
                        "auto_fixed": auto_fixed,
                        "total": len(db),
                    }
                res = st.session_state.get("_audit_results") or {}
                issues = res.get("issues") or []
                total = res.get("total") or 0
                auto_fixed = res.get("auto_fixed") or 0
                st.write(
                    f"Scanned **{total}** bottles. "
                    f"**{len(issues)}** need attention."
                    + (f" Auto-updated families on **{auto_fixed}**." if auto_fixed else "")
                )
                if not issues:
                    st.success("Vault looks solid - no major gaps found.")
                else:
                    show_n = st.slider("Show first N issues", 5, max(5, len(issues)), min(25, len(issues)), key="audit_show_n")
                    for item in issues[:show_n]:
                        flag_txt = ", ".join(item["flags"]) if item["flags"] else "family mismatch"
                        st.markdown(
                            f"**{item['name']}** - *{item['brand']}*  \n"
                            f"Issues: {flag_txt}  \n"
                            f"Current: {', '.join(item['current_cats']) or 'none'}  \n"
                            f"Suggested: {' | '.join(item['suggested']) or 'n/a'}"
                        )
                    if len(issues) > show_n:
                        st.caption(f"...and {len(issues) - show_n} more")
                    # One-click apply all suggested for listed issues
                    if st.button("Apply all suggested families to flagged bottles", key="audit_apply_flagged"):
                        fixed = 0
                        for item in issues:
                            sug = item.get("suggested") or []
                            if not sug:
                                continue
                            i = item["idx"]
                            cur = st.session_state["fragrances_db"][i].get("category") or []
                            merged = list(dict.fromkeys(list(cur) + sug))
                            st.session_state["fragrances_db"][i]["category"] = merged
                            fixed += 1
                        if fixed:
                            log_vault_action("edited", f"{fixed} bottles", "audit-apply-families")
                            save_persisted_data()
                            st.session_state.pop("_audit_results", None)
                            st.success(f"Updated families on {fixed} bottle(s).")
                            st.rerun()


    
    with st.expander("Season helper", expanded=False):
        st.caption(
            "Suggest season tags from notes and categories. "
            "Fix bottles that are missing or vague on season."
        )
        sh_mode = st.radio(
            "Season tool",
            ["Check one bottle", "Scan vault for weak seasons", "Apply suggestions"],
            key="season_helper_mode",
            horizontal=True,
        )
        if sh_mode == "Check one bottle":
            names = sorted(
                f.get("name") or ""
                for f in (st.session_state.get("fragrances_db") or [])
            )
            bottle = st.selectbox(
                "Bottle",
                ["- select -"] + names,
                key="season_check_bottle",
            )
            if bottle and bottle != "- select -":
                frag = next(
                    (
                        f
                        for f in st.session_state["fragrances_db"]
                        if f.get("name") == bottle
                    ),
                    None,
                )
                if frag:
                    st.write(
                        "Current season: **"
                        + (frag.get("season") or "none")
                        + "**"
                    )
                    suggested = suggest_seasons_from_notes(
                        frag.get("notes") or "",
                        frag.get("category") or [],
                    )
                    st.write(
                        "Suggested: **"
                        + " | ".join(suggested)
                        + "**"
                    )
                    if st.button("Apply suggested season", key="season_apply_one"):
                        for i, f in enumerate(st.session_state["fragrances_db"]):
                            if f.get("name") == bottle:
                                st.session_state["fragrances_db"][i]["season"] = (
                                    suggested[0] if suggested else f.get("season")
                                )
                                break
                        log_vault_action("edited", bottle, "season-helper")
                        mark_vault_dirty()
                        save_persisted_data()
                        st.success(
                            "Updated **"
                            + bottle
                            + "** -> "
                            + (suggested[0] if suggested else "")
                        )
                        st.rerun()
        else:
            # scan weak seasons
            weak = []
            for i, f in enumerate(st.session_state.get("fragrances_db") or []):
                s = (f.get("season") or "").strip()
                low = s.lower()
                if (
                    not s
                    or low in ("versatile", "any", "n/a", "na")
                    or len(s) < 3
                ):
                    sug = suggest_seasons_from_notes(
                        f.get("notes") or "",
                        f.get("category") or [],
                    )
                    weak.append(
                        {
                            "idx": i,
                            "name": f.get("name"),
                            "brand": f.get("brand"),
                            "current": s or "none",
                            "suggested": sug[0] if sug else "Versatile",
                        }
                    )
            st.write(
                f"**{len(weak)}** bottle(s) with missing or vague season tags."
            )
            show_n = min(30, len(weak)) if weak else 0
            for item in weak[:show_n]:
                st.markdown(
                    f"**{item['name']}** (*{item['brand']}*)  \n"
                    f"Now: {item['current']} -> Suggested: **{item['suggested']}**"
                )
            if len(weak) > show_n:
                st.caption(f"...and {len(weak) - show_n} more")
            if sh_mode == "Apply suggestions" and weak:
                if st.button(
                    "Apply all suggested seasons",
                    type="primary",
                    key="season_apply_all",
                ):
                    fixed = 0
                    for item in weak:
                        i = item["idx"]
                        st.session_state["fragrances_db"][i]["season"] = item[
                            "suggested"
                        ]
                        fixed += 1
                    if fixed:
                        log_vault_action(
                            "edited", f"{fixed} bottles", "season-helper-bulk"
                        )
                        mark_vault_dirty()
                        save_persisted_data()
                        st.success(f"Updated season on {fixed} bottle(s).")
                        st.rerun()

    with st.expander("Brand stats", expanded=False):
        stats = brand_stats()
        st.caption(f"{len(stats)} brands in vault")
        for brand, n in stats[:25]:
            st.write(f"**{brand}** - {n} bottle(s)")
        if len(stats) > 25:
            st.caption(f"...and {len(stats)-25} more brands")

    with st.expander("Batch edit", expanded=False):
        st.caption("Apply gender, season, or a category to several bottles at once.")
        all_names = sorted(
            (f.get("name") or "") for f in (st.session_state.get("fragrances_db") or [])
        )
        picks = st.multiselect("Bottles", all_names, key="batch_edit_picks")
        be1, be2, be3, be4 = st.columns(4)
        with be1:
            be_gender = st.selectbox(
                "Set gender",
                ["- no change -", "Female", "Male", "Unisex", "Female-leaning", "Male-leaning"],
                key="batch_edit_gender",
            )
        with be4:
            be_conc = st.selectbox(
                "Set format",
                ["- no change -"] + CONCENTRATION_OPTIONS,
                key="batch_edit_concentration",
            )
        with be2:
            be_season = st.selectbox(
                "Set season",
                [
                    "- no change -",
                    "Fall, Winter",
                    "Spring, Summer",
                    "Versatile",
                    "Hot / Summer",
                    "Cool / Autumn",
                    "Cold / Winter",
                ],
                key="batch_edit_season",
            )
        with be3:
            be_cat = st.selectbox(
                "Add category",
                ["- no change -"]
                + [
                    "Gourmand", "Sweet", "Floral", "Woody", "Oriental", "Fresh",
                    "Fruity", "Spicy", "Citrus", "Musky", "Vanilla", "Creamy",
                    "Smoky", "Oud", "Leather", "Powdery",
                ],
                key="batch_edit_cat",
            )
        if st.button("Apply batch edit", type="primary", key="batch_edit_go"):
            if not picks:
                st.warning("Pick at least one bottle.")
            else:
                changed = 0
                for i, f in enumerate(st.session_state["fragrances_db"]):
                    if f.get("name") not in picks:
                        continue
                    if be_gender != "- no change -":
                        st.session_state["fragrances_db"][i]["gender"] = be_gender
                    if be_season != "- no change -":
                        st.session_state["fragrances_db"][i]["season"] = be_season
                    if be_cat != "- no change -":
                        cats = list(f.get("category") or [])
                        if be_cat not in cats:
                            cats.append(be_cat)
                        st.session_state["fragrances_db"][i]["category"] = cats
                    if be_conc != "- no change -":
                        st.session_state["fragrances_db"][i]["concentration"] = be_conc
                    changed += 1
                if changed:
                    log_vault_action("edited", f"{changed} bottles", "batch-edit")
                    save_persisted_data()
                    st.success(f"Updated {changed} bottle(s).")
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

    with st.expander("Backup & restore", expanded=True):
        st.caption(
            "Best protection against Cloud redeploys wiping your vault. "
            "Export after every session of edits. Restore loads your full bottle list, "
            "reactions, SOTD, wishlist, and chart."
        )
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
                "full": st.session_state.get("birth_calc_full"),
                "his_sun": st.session_state.get("chart_his_sun"),
                "his_moon": st.session_state.get("chart_his_moon"),
                "his_rising": st.session_state.get("chart_his_rising"),
                "his_venus": st.session_state.get("chart_his_venus"),
                "his_full": st.session_state.get("birth_calc_his_full"),
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
        uploaded_file = st.file_uploader(
            "Restore from backup JSON", type=["json"], key="restore_upload"
        )
        if uploaded_file is not None:
            st.caption(
                f"Selected: **{getattr(uploaded_file, 'name', 'backup.json')}** "
                f"({getattr(uploaded_file, 'size', 0) // 1024} KB)"
            )
            if st.button("Apply restore", type="primary", key="restore_apply_btn"):
                try:
                    uploaded_file.seek(0)
                    imported_data = json.load(uploaded_file)
                    if not isinstance(imported_data, dict):
                        raise ValueError("Backup must be a JSON object")
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
                        # Defer chart_* keys  -  Stars widgets already ran this script cycle
                        st.session_state["_pending_chart_restore"] = imported_data["chart"]
                    if "wishlist" in imported_data:
                        st.session_state["wishlist"] = imported_data["wishlist"]
                    if "vault_log" in imported_data:
                        st.session_state["vault_log"] = imported_data["vault_log"]
                    n_bot = len(st.session_state.get("fragrances_db") or [])
                    save_persisted_data(force=True)
                    st.session_state["_restore_flash"] = (
                        f"Vault restored  -  **{n_bot}** bottles loaded. "
                        "Export JSON again and keep a copy off Cloud."
                    )
                    st.rerun()
                except Exception as e:
                    st.error(f"Restore failed: {e}")


# ==========================================
# AUTO-SAVE (any vault change this run)
# ==========================================
# AUTO-SAVE: runs at the end of every script run.
# Catches fragrances, edits, reactions, wishlist, recipes, SOTD, chart, etc.
# Any change to the vault fingerprint triggers a save to disk + .bak + /tmp.
# This protects against Streamlit Cloud redeploys wiping memory.
# even if a specific button forgot to call save_persisted_data().
try:
    _auto_ok = autosave_if_changed(force=False)
    if _auto_ok and st.session_state.get("_autosaved_at"):
        # Quiet status in sidebar area via session flag for next widgets  -  already saved
        pass
except Exception as _auto_ex:
    try:
        st.sidebar.warning(f"Autosave issue: {_auto_ex}")
    except Exception:
        pass
