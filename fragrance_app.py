# -*- coding: utf-8 -*-
"""ScentedDeadGirl Fragrance Sanctuary — clean rewrite."""
import datetime
import hashlib
import json
import random
import re
from pathlib import Path
from zoneinfo import ZoneInfo

import streamlit as st

DATA_FILE = Path(__file__).parent / "scented_dead_girl_data.json"
DATA_BAK = Path(__file__).parent / "scented_dead_girl_data.bak.json"
DATA_TMP = Path("/tmp") / "scented_dead_girl_data.json"

CAT_OPTIONS = [
    "Gourmand", "Sweet", "Floral", "Woody", "Oriental", "Fresh",
    "Fruity", "Spicy", "Citrus", "Musky", "Vanilla", "Creamy",
    "Smoky", "Oud", "Leather", "Powdery", "Aquatic", "Green",
    "Amber", "Boozy", "Chypre", "Aromatic", "Fougere", "Animalic",
]
CONCENTRATION_OPTIONS = [
    "EDP", "EDT", "EDC", "Extrait", "Concentrated oil", "Body spray", "Other",
]
SEASON_CHOICES = [
    "Spring", "Summer", "Fall", "Winter",
    "Spring, Summer", "Fall, Winter", "Versatile",
]


def pacific_today():
    return datetime.datetime.now(ZoneInfo("America/Los_Angeles")).date()


def pacific_now_iso():
    return datetime.datetime.now(ZoneInfo("America/Los_Angeles")).isoformat(timespec="seconds")


def clean_text(s) -> str:
    if s is None:
        return ""
    t = str(s)
    for a, b in (
        ("\u2192", " > "), ("\u2013", "-"), ("\u2014", "-"),
        ("\u2018", "'"), ("\u2019", "'"), ("\u201c", '"'), ("\u201d", '"'),
        ("Ã±", "n"), ("Â", ""), ("â€™", "'"),
    ):
        t = t.replace(a, b)
    return " ".join(t.split())


def _safe_load(path: Path) -> dict:
    try:
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                d = json.load(f)
            return d if isinstance(d, dict) else {}
    except Exception:
        pass
    return {}


def _vault_n(data: dict) -> int:
    db = (data or {}).get("fragrances_db") or []
    return len(db) if isinstance(db, list) else 0


def load_persisted() -> dict:
    cands = []
    for p in (DATA_FILE, DATA_BAK, DATA_TMP):
        d = _safe_load(p)
        if _vault_n(d) > 0:
            cands.append((_vault_n(d), d))
    if not cands:
        return _safe_load(DATA_FILE) or {}
    cands.sort(key=lambda x: x[0], reverse=True)
    return cands[0][1]


def save_persisted(force: bool = False) -> bool:
    now = pacific_now_iso()
    st.session_state["last_saved_at"] = now
    session_db = list(st.session_state.get("fragrances_db") or [])
    n = len(session_db)
    data = {
        "fragrances_db": session_db,
        "user_reactions": st.session_state.get("user_reactions") or {},
        "sotd_history": st.session_state.get("sotd_history") or [],
        "layer_recipes": st.session_state.get("layer_recipes") or [],
        "wishlist": st.session_state.get("wishlist") or [],
        "vault_log": st.session_state.get("vault_log") or [],
        "last_saved_at": now,
        "last_export_date": st.session_state.get("last_export_date"),
        "bottle_count": n,
    }
    if not force:
        disk = load_persisted()
        dn = _vault_n(disk)
        if n == 0 and dn > 0:
            st.session_state["fragrances_db"] = disk.get("fragrances_db") or []
            return False
        if dn >= 10 and n < max(5, int(dn * 0.85)):
            st.session_state["fragrances_db"] = disk.get("fragrances_db") or []
            return False
        if (disk.get("wishlist") or []) and not data["wishlist"]:
            data["wishlist"] = disk["wishlist"]
            st.session_state["wishlist"] = list(disk["wishlist"])
        if (disk.get("layer_recipes") or []) and not data["layer_recipes"]:
            data["layer_recipes"] = disk["layer_recipes"]
            st.session_state["layer_recipes"] = list(disk["layer_recipes"])
        if (disk.get("sotd_history") or []) and not data["sotd_history"]:
            data["sotd_history"] = disk["sotd_history"]
            st.session_state["sotd_history"] = list(disk["sotd_history"])
    payload = json.dumps(data, indent=2, ensure_ascii=False)
    ok = False
    for target in (DATA_FILE, DATA_TMP):
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            tmp = target.with_suffix(target.suffix + ".tmp")
            with open(tmp, "w", encoding="utf-8") as f:
                f.write(payload)
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
    return ok


def vault_fp() -> str:
    payload = {
        "fragrances_db": st.session_state.get("fragrances_db"),
        "user_reactions": st.session_state.get("user_reactions"),
        "sotd_history": st.session_state.get("sotd_history"),
        "layer_recipes": st.session_state.get("layer_recipes"),
        "wishlist": st.session_state.get("wishlist"),
    }
    raw = json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.md5(raw.encode("utf-8", errors="replace")).hexdigest()


def mark_dirty():
    st.session_state["_vault_dirty"] = True


def autosave():
    try:
        cur = vault_fp()
        start = st.session_state.get("_fp_start")
        if st.session_state.get("_vault_dirty") or (start and cur != start):
            if save_persisted():
                st.session_state["_vault_dirty"] = False
                st.session_state["_fp_start"] = vault_fp()
    except Exception:
        pass

SEED = json.loads('{"fragrances_db": [{"name": "8th Wonder", "brand": "French Avenue", "gender": "Unisex", "season": "Fall, Winter", "notes": "Top - Cardamom, Pink Pepper, Candy Apple / Heart - Liquor, Dates, Boozy notes, Davana, Osmanthus / Base - Myrrh, Benzoin, Styrax, Amber Xtreme, Labdanum, Patchouli", "category": ["Oriental", "Spicy", "Sweet", "Boozy", "Chypre", "Woody"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Ajwad", "brand": "Lattafa", "gender": "Unisex", "season": "Versatile (cooler preferred)", "notes": "Fruity-woody-oriental (pineapple/rose/oud-leaning)", "category": ["Oriental", "Woody", "Fruity", "Floral", "Oud"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Angham", "brand": "Lattafa", "gender": "Unisex (leans feminine)", "season": "Fall, Winter", "notes": "Top - Ginger, Mandarin, Pink Pepper / Heart - Lavender, Praline, Cacao, Jasmine / Base - Vanilla, Amber, Musk", "category": ["Gourmand", "Spicy", "Sweet", "Aromatic", "Citrus"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Ansaam Gold", "brand": "Lattafa", "gender": "Female/Unisex", "season": "Fall, Winter", "notes": "Top - Mandarin Orange, Pear / Heart - Sweet Notes, Jasmine, Rose / Base - Musk, Vanilla, Raspberry", "category": ["Fruity", "Floral", "Sweet", "Citrus", "Gourmand"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Asad", "brand": "Lattafa", "gender": "Male", "season": "Fall, Winter", "notes": "Top - Black Pepper, Tobacco, Pineapple / Heart - Patchouli, Coffee, Iris / Base - Vanilla, Amber, Dry Woods, Benzoin, Labdanum", "category": ["Woody", "Spicy", "Oriental", "Gourmand", "Fruity", "Chypre"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Badee Al Oud Noble Blush", "brand": "Lattafa", "gender": "Female", "season": "Fall, Winter", "notes": "Top - Rose Milk / Heart - Meringue, Almond / Base - Vanilla, Musk, Sandalwood", "category": ["Floral", "Gourmand", "Sweet", "Creamy", "Woody", "Vanilla"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Bahiya Garnet", "brand": "Arabiyat Prestige", "gender": "Female-leaning", "season": "Fall, Winter", "notes": "Top - Cherry, Mandarin, Mango, Pear, Bergamot / Heart - Amber, Fig, Jasmine / Base - Amber, Vanilla, Sandalwood, Musk", "category": ["Fruity", "Oriental", "Sweet", "Citrus", "Woody", "Chypre", "Creamy"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Banat Dubai", "brand": "Le Chameau", "gender": "Female", "season": "Spring, fall", "notes": "Top - Jasmine, Bergamot, Peony / Heart - Pineapple, Peach, Plum / Base - Musk, Patchouli, Sandalwood", "category": ["Floral", "Fruity", "Woody", "Citrus", "Chypre"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Berries Cream Macaron", "brand": "Arabiyat Sugar", "gender": "Female", "season": "Spring-Fall", "notes": "Top Notes: Juicy lycheeHeart (Middle) Notes: Raspberry, maltol (confectionary sweetness), and jasmineBase Notes: Ambroxan, ambergris (or dry amber), and evernyl", "category": ["Gourmand", "Fruity", "Sweet", "Amber", "Floral", "Oriental"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Bint Hooran", "brand": "Ard Al Zaafaran", "gender": "Female", "season": "Fall, Winter", "notes": "Top - Almond, Coffee, Ylang Ylang / Heart - Jasmine, Rose, Tuberose / Base - Vanilla, Musk, Tonka, Woody/Cacao", "category": ["Gourmand", "Floral", "Oriental", "Sweet", "Vanilla", "Animalic"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Boulevard of New York", "brand": "Le Chameau", "gender": "Unisex", "season": "Fall, Winter", "notes": "Top - Roasted Coffee Beans / Heart - Praline, Rose / Base - Oakmoss, Cedar, Amber", "category": ["Gourmand", "Woody", "Chypre", "Fougere", "Sweet"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Cafe Bliss", "brand": "Mamlakat Al Oud", "gender": "Unisex", "season": "Fall, Winter", "notes": "Top - Black Coffee, Amaretto Liquor / Heart - Vanilla Ice Cream, Speculoos / Base - Vanilla Pods, Brown Sugar, Grey Amber", "category": ["Gourmand", "Sweet", "Boozy", "Vanilla", "Amber"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Cafe Latte", "brand": "Khadlaj", "gender": "Unisex", "season": "Fall, Winter", "notes": "Top - Coffee, Sweet Almond, Milk / Heart - Vanilla, Ice Cream Accord, Amber / Base - Vanilla, Almond Cream, Caramel", "category": ["Gourmand", "Sweet", "Creamy", "Vanilla", "Amber"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Caramel Chocolate Macaron", "brand": "Arabiyat Sugar", "gender": "Female/Unisex", "season": "Fall-Winter", "notes": "Top Notes: Caramel, Coumarin (providing a sweet, warm, almond-vanilla nuance)Middle / Heart Notes: Honey, Soft Floral NotesBase Notes: Musk", "category": ["Gourmand", "Sweet", "Fougere", "Vanilla", "Animalic"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Caramello", "brand": "Al Rehab", "gender": "Unisex", "season": "Fall, Winter", "notes": "Top - Pistachio, Almond / Heart - Jasmine, Heliotrope / Base - Caramel, Vanilla, Sandalwood", "category": ["Gourmand", "Sweet", "Floral", "Woody", "Creamy"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Chocomusk", "brand": "Al Rehab", "gender": "Unisex", "season": "Fall, Winter", "notes": "Top - Warm Spicy, Amber / Heart - Sweet, Powdery, Vanilla / Base - Chocolate, Musky, Cocoa", "category": ["Gourmand", "Sweet", "Powdery", "Musky", "Vanilla"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Chocomusk Marshmallow", "brand": "Al Rehab", "gender": "Unisex", "season": "Fall, Winter", "notes": "Top - Marshmallow, Strawberry / Heart - Cocoa, Vanilla / Base - Sweet Musk", "category": ["Gourmand", "Sweet", "Fruity", "Vanilla", "Animalic"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Chocomusk Vanilla", "brand": "Al Rehab", "gender": "Unisex", "season": "Fall, Winter", "notes": "Top - Chocolate / Heart - Vanilla / Base - Musk", "category": ["Gourmand", "Sweet", "Vanilla", "Animalic", "Musky"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Club De Nuit Women", "brand": "Armaf", "gender": "Female", "season": "Spring, Fall", "notes": "Top - Apple, Citrus / Heart - Rose, Jasmine / Base - Vanilla, Musk", "category": ["Floral", "Fruity", "Fresh", "Citrus", "Gourmand", "Sweet", "Vanilla"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Coconut Chiffon", "brand": "Arabiyat Sugar", "gender": "Female/Unisex", "season": "Spring-Summer", "notes": "Top Notes: CoconutMiddle (Heart) Notes: Coconut, JasmineBase Notes: Vanilla, Butter, Cooked Sugar (Caramel), Musk", "category": ["Gourmand", "Sweet", "Fresh", "Creamy", "Floral", "Fruity"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Confections", "brand": "Paris Corner", "gender": "Female/Unisex", "season": "Fall-Winter", "notes": "Top Notes: Pear and Whipped CreamHeart (Middle) Notes: Cashmeran, Jasmine, and Ylang-YlangBase Notes: Marshmallow, Vanilla, and Sandalwood", "category": ["Gourmand", "Sweet", "Creamy", "Floral", "Woody"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Cookie Bite", "brand": "Gulf Orchid", "gender": "Unisex", "season": "Fall, Winter", "notes": "Top - Cookie, Butter / Heart - Vanilla, Musk / Base - Caramel, Amber", "category": ["Gourmand", "Sweet", "Creamy", "Vanilla", "Amber"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Coral (Ana Abiyedh Coral)", "brand": "Lattafa", "gender": "Unisex (leans feminine)", "season": "Spring, Summer", "notes": "Top - Watermelon, Peach, Orange / Heart - Coconut, White Flowers / Base - Musk, Vanilla, Amber", "category": ["Fruity", "Fresh", "Sweet", "Citrus", "Gourmand", "Vanilla"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Cotton Blush", "brand": "Arabiyat Sugar", "gender": "Female", "season": "Spring, summer", "notes": "Top Notes: Strawberry, Raspberry, CoconutHeart (Middle) Notes: Marshmallow, Peony, RoseBase Notes: Vanilla, Amber, Musk", "category": ["Floral", "Fruity", "Gourmand", "Sweet", "Vanilla"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Cotton Candy Delicacy", "brand": "Armaf", "gender": "Unisex", "season": "Spring, Summer", "notes": "Top Notes: Raspberry, Pink Pepper, and CocoaHeart (Middle) Notes: Jasmine and RoseBase Notes: Vanilla, Benzoin Resinoid, and Cedarwood", "category": ["Gourmand", "Fruity", "Floral", "Oriental", "Spicy"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Cream Velvet", "brand": "Khadlaj", "gender": "Unisex", "season": "Fall, Winter", "notes": "Top Notes: Creamy Butter and Golden CaramelMiddle (Heart) Notes: Honey, Tonka Bean, and JasmineBase Notes: Smooth Vanilla, Amber, and Soft Musk", "category": ["Gourmand", "Sweet", "Floral", "Creamy", "Vanilla"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Creme of Clouds", "brand": "Fragrance World", "gender": "Unisex", "season": "Fall, Winter, spring", "notes": "Top Notes: Coconut milk, Creamy milk, Burnt sugarHeart (Middle) Notes: Whipped cream, Vanilla, ChocolateBase Notes: Vanilla, White musk, Burnt sugar", "category": ["Gourmand", "Sweet", "Creamy", "Fruity", "Vanilla"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Creme Caramel", "brand": "Mamlakat Al Oud", "gender": "Unisex", "season": "Fall, Winter", "notes": "Top - Caramel, Vanilla Flower / Heart - Dulce de Leche, Cotton Candy, Frangipani, White Flowers / Base - Vanilla Pod, Tonka Bean, Musk", "category": ["Gourmand", "Sweet", "Vanilla", "Animalic", "Musky"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Cup Cake", "brand": "Al Rehab", "gender": "Unisex", "season": "Fall, Winter", "notes": "Top - Citrus, Amber / Heart - Vanilla Cake / Base - Vanilla, Amber", "category": ["Gourmand", "Sweet", "Citrus", "Vanilla", "Amber"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Dalal", "brand": "Lattafa", "gender": "Female", "season": "Spring", "notes": "Top - Apple (Golden Delicious), Mandarin / Heart - Jasmine, Ylang-Ylang, Orange Flower / Base - Vanilla, Musk, Oakmoss", "category": ["Floral", "Fruity", "Fresh", "Citrus", "Chypre", "Fougere", "Gourmand"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Dulzura", "brand": "Paris Corner", "gender": "Female", "season": "Fall-Winter", "notes": "Top - Black pepper, buttermilk / Heart - Cake, vanilla, cream / Base - Amber, musk", "category": ["Gourmand", "Sweet", "Creamy", "Spicy", "Vanilla"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Eclaire", "brand": "Lattafa", "gender": "Female", "season": "Fall, Winter", "notes": "Top - Caramel, Milk, Sugar / Heart - Honey, White Flowers / Base - Vanilla, Praline, Musk", "category": ["Gourmand", "Sweet", "Vanilla", "Animalic", "Creamy"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Eclaire Banoffi", "brand": "Lattafa", "gender": "Unisex/Female", "season": "Fall-Winter", "notes": "Top Notes: Banana Cream, Dulce de LecheHeart (Middle) Notes: Whipped Cream, VanillaBase Notes: Praline, Biscuit, Musk", "category": ["Gourmand", "Sweet", "Fruity", "Vanilla", "Animalic"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Elyssia Aura", "brand": "Riiffs", "gender": "Unisex", "season": "Fall, Winter (versatile to cooler)", "notes": "Top - Cinnamon, Orange, Nutmeg / Heart - Vanilla Cream, Cognac, Cocoa / Base - Bourbon Vanilla, Cedarwood, Patchouli", "category": ["Gourmand", "Spicy", "Woody", "Boozy", "Citrus"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Elyssia Scarlet", "brand": "Riiffs", "gender": "Female", "season": "Spring-Summer / versatile", "notes": "Top - Black Cherry, Pink Pepper / Heart - Leather, Cream, Benzoin / Base - Vanilla Absolute, Cashmeran, Amber, Iso E Super", "category": ["Fruity", "Leather", "Sweet", "Gourmand", "Oriental", "Spicy"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Emaan", "brand": "Lattafa", "gender": "Female/Unisex", "season": "Fall, Winter", "notes": "Top - Orange Blossom, Black Currant, Bergamot / Heart - Tuberose, Jasmine, Marigold / Base - Musk, Vanilla, Cedarwood, Patchouli", "category": ["Floral", "Fruity", "Citrus", "Woody", "Chypre", "Gourmand"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Emir Pear Potion", "brand": "Paris Corner", "gender": "Unisex", "season": "Spring", "notes": "Top - Pear, Apple / Heart - Caramel, Jasmine / Base - Raspberry, Musk", "category": ["Fruity", "Gourmand", "Sweet", "Floral", "Animalic"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Empire Najm by Risala", "brand": "Risala", "gender": "Unisex (female-leaning)", "season": "Fall, Winter", "notes": "Top - Mango, Ginger, Lemon, Red Berries / Heart - Coumarin, Jasmine, Cedar / Base - Cypriol, Amber, Musk, Oud", "category": ["Fruity", "Oriental", "Woody", "Floral", "Fougere", "Spicy", "Amber"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Empire Victor", "brand": "Khadlaj", "gender": "Unisex", "season": "Fall, Winter,spring", "notes": "Top Notes: Lemon, BergamotMiddle (Heart) Notes: Caramel, JasmineBase Notes: Vanilla, Musk (some variations also list sandalwood)", "category": ["Gourmand", "Floral", "Fruity", "Sweet", "Citrus", "Woody", "Chypre"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Energize", "brand": "Heroes", "gender": "Male", "season": "Spring, Summer", "notes": "Top - Citrus, Aromatic Herbs / Heart - Light Spices / Base - Woods, Musk", "category": ["Fresh", "Citrus", "Aromatic", "Animalic", "Musky", "Spicy"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Entice Extrait", "brand": "Vurv", "gender": "Female", "season": "Cooler / evening", "notes": "Top Notes: Citrus and fresh floral elements (including aromatic nuances like lilac and bergamot)Heart / Middle Notes: Rich bouquet of floral accordsBase Notes: Warm amber, sensual musk, and woody elements", "category": ["Oriental", "Sweet", "Fruity", "Citrus", "Aromatic", "Chypre", "Amber", "Animalic"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "Extrait"}, {"name": "Entice Ruby", "brand": "Vurv", "gender": "Female", "season": "Spring-Summer / versatile", "notes": "Top Notes: Red fruits, Bergamot, MandarinHeart (Middle) Notes: Roses, Jasmine, White flowersBase Notes: Amber, Musk, Soft woods, Vanilla", "category": ["Fruity", "Floral", "Citrus", "Chypre", "Gourmand", "Sweet"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Eshal Vanilla", "brand": "Paris Corner", "gender": "Unisex", "season": "Fall, Winter", "notes": "Top Notes: Sugar, Sweet NotesHeart (Middle) Notes: Jasmine, RoseBase Notes: Vanilla, Caramel, Musk", "category": ["Gourmand", "Floral", "Sweet", "Vanilla", "Animalic"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Espada Intense", "brand": "Le Chameau", "gender": "Male", "season": "Cooler seasons / evening", "notes": "Deeper/intensified version of Espada Prime", "category": ["Woody", "Spicy"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Espada Prime", "brand": "Le Chameau", "gender": "Male", "season": "Spring-Summer / versatile", "notes": "Top Notes (Head): Ruby, mandarin orange, grapefruit, and peppermint (mint)Middle Notes (Heart): Rose absolute, cinnamon, and mixed spicesBase Notes: Leather, patchouli, whitewoods, and amber", "category": ["Fresh", "Woody", "Spicy", "Citrus", "Leather", "Amber"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Essences", "brand": "Sara Debai", "gender": "Female", "season": "Spring-Summer", "notes": "Top - Heliotrope, orchid, tangerine / Heart - Gourmand accord, tropical fruits / Base - Vanilla, musk, sandalwood", "category": ["Floral", "Gourmand", "Fruity", "Woody", "Creamy", "Powdery"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Eternal Vanille", "brand": "Lattafa", "gender": "Unisex", "season": "Year-round (best Spring/Fall)", "notes": "Top - Blackberry / Heart - Cocoapulse, Vanilla Caviar, Cacao / Base - Akigalawood, Tonka Bean, Ambrofix, Cedarwood, Benzoin, Musk", "category": ["Gourmand", "Woody", "Sweet", "Oriental", "Vanilla"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Fakhama", "brand": "Amaran", "gender": "Unisex/Male", "season": "Cooler seasons", "notes": "Top Notes: Cinnamon, nutmeg, and vanillaMiddle (Heart) Notes: Dates, tuberose, praline, and mahonialBase Notes: Musk, tonka bean, amberwood, myrrh, benzoin, and akigalawood", "category": ["Oriental", "Woody", "Gourmand", "Spicy", "Sweet", "Amber"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Fakhar Black", "brand": "Lattafa", "gender": "Unisex", "season": "Fall, Winter", "notes": "Top - Dark Fruits, Spices / Heart - Woody / Base - Vanilla, Musk", "category": ["Fruity", "Woody", "Spicy", "Gourmand", "Sweet", "Vanilla", "Animalic", "Musky"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Fakhar Gold", "brand": "Lattafa", "gender": "Unisex", "season": "Fall, Winter", "notes": "Top - Tuberose, Salt / Heart - Amber, Tonka / Base - Cedarwood, Vetiver, Labdanum", "category": ["Floral", "Woody", "Oriental", "Chypre", "Amber"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Fakhar Silver", "brand": "Lattafa", "gender": "Unisex", "season": "Spring , summer", "notes": "Top Notes: Apple, Bergamot, GingerHeart (Middle) Notes: Lavender, Sage, Juniper Berries, GeraniumBase Notes: Tonka Bean, Amberwood, Cedar, Vetiver", "category": ["Gourmand", "Woody", "Aromatic", "Citrus", "Amber", "Chypre"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Falak", "brand": "Nusuk", "gender": "Unisex", "season": "Fall, Winter", "notes": "Top - Brown Sugar, Caramel, Biscuit / Heart - Toffee, Vanilla Bean, Amber / Base - White Musk, Praline", "category": ["Gourmand", "Sweet", "Vanilla", "Amber", "Animalic"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Fatima Pink", "brand": "Zimaya", "gender": "Female", "season": "Spring, Fall", "notes": "Top - Rhubarb, Bergamot, Grapefruit, Nutmeg / Heart - Rose, Jasmine / Base - Musk, Vanilla, Vetiver, Ambergris", "category": ["Floral", "Fruity", "Fresh", "Citrus", "Amber", "Chypre", "Gourmand"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Fire on Ice", "brand": "Lattafa", "gender": "Unisex", "season": "Fall, Winter", "notes": "Top Notes: Black raspberry, cinnamon, cognac (liquor)Middle (Heart) Notes: Frozen rose petals, caramel, mossBase Notes: Oakwood, myrrh, cedarwood, ambroxan", "category": ["Gourmand", "Boozy", "Fruity", "Woody", "Amber"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "French Vanilla", "brand": "Al Rehab", "gender": "Unisex", "season": "Fall, Winter", "notes": "Top - Vanilla / Heart - Creamy Sweet / Base - Vanilla, Musk", "category": ["Gourmand", "Sweet", "Creamy", "Vanilla", "Animalic"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "French Vanilla Latte", "brand": "Arabiyat Sugar", "gender": "Unisex", "season": "Fall, Winter", "notes": "Top - Nutella, Cardamom, Rum / Heart - Cocoa, Coconut, White Flowers, Lily of the Valley / Base - Sandalwood, Ambergris, Musk", "category": ["Gourmand", "Sweet", "Amber", "Woody", "Creamy", "Fruity", "Spicy"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Ghaliya", "brand": "Zakat", "gender": "Unisex/Female", "season": "Fall-Winter", "notes": "Top Notes: Orange, Lemon, Apple, and BergamotMiddle (Heart) Notes: Caramel, Muguet (Lily of the Valley), Cedarwood, Jasmine Sambac, Bulgarian Rose, and TuberoseBase Notes: Tonka Bean, Amber, Musk, Cocoa, Sandalwood, and Patchouli", "category": ["Oriental", "Floral", "Oud", "Woody", "Citrus", "Gourmand", "Chypre"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Ghubar Al Dhahab", "brand": "Sahari", "gender": "Unisex", "season": "Fall, Winter", "notes": "Top - Cinnamon, Pear, Mandarin, Floral notes / Heart - Jasmine Sambac, Orange Blossom / Base - White Musk, Vanilla, Tonka Bean, Coffee, Patchouli", "category": ["Floral", "Spicy", "Sweet", "Citrus", "Gourmand"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Habik (Women\'s Version)", "brand": "Lattafa", "gender": "Female", "season": "Spring, Summer", "notes": "Top - Pear, Bergamot / Heart - Lily of the Valley, Jasmine, Freesia / Base - Musk, Amber, Oakmoss", "category": ["Floral", "Fresh", "Fruity", "Chypre", "Citrus", "Fougere", "Amber"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Hareem Al Sultan Gold", "brand": "Khadlaj", "gender": "Female", "season": "Spring, Summer", "notes": "Top - Bergamot, Jasmine, Peony / Heart - Pineapple, Peach, Plum / Base - Musk, Sandalwood, Patchouli", "category": ["Floral", "Fruity", "Fresh", "Woody", "Chypre", "Citrus"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Hawas Diva", "brand": "Rasasi", "gender": "Female", "season": "Fall, Winter", "notes": "Top - Red Fruits, Rhubarb, Lychee / Heart - Rose, Frankincense, Cedar / Base - Vanilla, Musk, Ambergris", "category": ["Fruity", "Floral", "Woody", "Amber", "Oriental", "Gourmand", "Smoky"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Hawas Eclat (Eclat Hawas)", "brand": "Rasasi", "gender": "Female", "season": "Spring, Fall", "notes": "Top - Litchi/Lychee, Bergamot, Pear, Pistachio / Heart - Rose, Incense / Base - Vanilla, Amber, Musk, Woody Notes", "category": ["Fruity", "Floral", "Woody", "Gourmand", "Oriental", "Chypre", "Citrus"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Hawas Elixir", "brand": "Rasasi", "gender": "Unisex", "season": "Fall-Winter", "notes": "Top - Mint, bergamot, artemisia / Heart - Dark chocolate, lavender, benzoin / Base - Vanilla, tonka bean, white musk", "category": ["Gourmand", "Fresh", "Sweet", "Aromatic", "Chypre", "Citrus", "Fougere"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Hawas Ice", "brand": "Rasasi", "gender": "Male", "season": "Spring , summer", "notes": "Top - Apple, Italian Lemon, Sicilian Bergamot, Star Anise / Heart - Plum, Orange Blossom, Cardamom / Base - Musk, Moss, Driftwood, Amber", "category": ["Fresh", "Fruity", "Aromatic", "Citrus", "Floral", "Spicy", "Chypre"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Hawas London", "brand": "Rasasi", "gender": "Unisex", "season": "Fall, Spring", "notes": "Top - Pink Pepper, Saffron, Pear / Heart - Rose, Frankincense, White Flowers / Base - Blonde Woods, Vanilla, Amber, Musk", "category": ["Floral", "Woody", "Spicy", "Oriental", "Gourmand", "Smoky", "Sweet"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Hawas Pink", "brand": "Rasasi", "gender": "Female", "season": "Fall, Winter", "notes": "Top - Cinnamon, Nutmeg, Neroli / Heart - Marshmallow, Tuberose, Orange Blossom / Base - Cotton Candy, Vanilla, Tonka Bean", "category": ["Gourmand", "Floral", "Sweet", "Citrus", "Spicy"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Hawwa Red", "brand": "Zimaya", "gender": "Female", "season": "Fall, Winter", "notes": "Top - Cassis, Strawberry, Raspberry, Orange / Heart - Black Currant, Grapefruit, Peach, Lily / Base - Musk, Vanilla, Patchouli", "category": ["Fruity", "Floral", "Sweet", "Citrus", "Gourmand", "Vanilla"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Haya", "brand": "Lattafa", "gender": "Female", "season": "Fall, Winter", "notes": "Top - Champagne, Strawberry, Rose, Tangerine, Blood Orange / Heart - Gardenia, Jasmine, Vanilla Orchid / Base - Amber, Sandalwood", "category": ["Floral", "Fruity", "Sweet", "Woody", "Boozy", "Citrus"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Heavy Cream", "brand": "Phlur", "gender": "Unisex", "season": "Fall, Winter", "notes": "Top - Marshmallow, Sugar, Citrus / Heart - Coconut, Jasmine / Base - Whipped Cream, Vanilla, Caramel", "category": ["Gourmand", "Sweet", "Citrus", "Floral", "Fruity"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Her Confessions", "brand": "Lattafa", "gender": "Female", "season": "Fall, Winter", "notes": "Top - Cinnamon / Heart - Tuberose, Jasmine, Incense / Base - Vanilla, Musk, Tonka", "category": ["Floral", "Spicy", "Oriental", "Gourmand", "Smoky"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "His Confessions", "brand": "Lattafa", "gender": "Male", "season": "Fall, Winter", "notes": "Top - Lavender, Cinnamon, Mandarin / Heart - Iris, Benzoin, Cypress, Mahonial / Base - Vanilla, Tonka, Amber, Incense, Cedarwood, Patchouli", "category": ["Woody", "Spicy", "Oriental", "Aromatic", "Citrus", "Fougere"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Island Bliss", "brand": "Armaf", "gender": "Unisex", "season": "Spring, Summer", "notes": "Top - Tropical Fruits, Coconut / Heart - Sweet / Base - Musk", "category": ["Fruity", "Fresh", "Sweet", "Animalic", "Musky"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Khair Men", "brand": "Paris Corner", "gender": "Male/Unisex", "season": "Fall, Winter", "notes": "Top - Davana, Bergamot, Pink Pepper / Heart - Agarwood (Oud), Amber, Rosemary / Base - Leather, Vetiver, Musk", "category": ["Woody", "Oud", "Spicy", "Aromatic", "Chypre", "Citrus"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Khamrah Dukhan", "brand": "Lattafa", "gender": "Unisex", "season": "Fall, Winter", "notes": "Top - Spices, Pimento, Mandarin / Heart - Incense, Labdanum, Orange Blossom, Patchouli / Base - Tobacco, Praline, Amber, Tonka Bean, Benzoin", "category": ["Oriental", "Spicy", "Sweet", "Citrus", "Smoky", "Chypre"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Khamrah Original", "brand": "Lattafa", "gender": "Unisex", "season": "Fall, Winter", "notes": "Top - Cinnamon, Nutmeg, Bergamot / Heart - Dates, Praline, Tuberose, Mahonial / Base - Vanilla, Tonka Bean, Amberwood, Myrrh, Benzoin, Akigalawood", "category": ["Oriental", "Spicy", "Sweet", "Gourmand", "Amber"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Khamrah Qahwa", "brand": "Lattafa", "gender": "Unisex", "season": "Fall, Winter", "notes": "Top - Cinnamon, Cardamom, Ginger / Heart - Praline, Candied Fruits, White Flowers / Base - Coffee, Vanilla, Tonka Bean, Benzoin, Musk", "category": ["Gourmand", "Spicy", "Sweet", "Oriental", "Vanilla"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Khamrah Waha", "brand": "Lattafa", "gender": "Unisex", "season": "Fall-Winter", "notes": "Spicy-sweet (date, cinnamon, vanilla family)", "category": ["Oriental", "Spicy", "Sweet", "Gourmand", "Vanilla"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Kiaana Angel", "brand": "Afnan", "gender": "Female", "season": "Spring, summer", "notes": "Top Notes: Pistachio Gelato (or Ice Cream), Italian BergamotMiddle (Heart) Notes: Jasmine, Raspberry, White Peach, PearBase Notes: Cedarwood, Sandalwood, Tonka Bean", "category": ["Gourmand", "Floral", "Fruity", "Woody", "Creamy", "Chypre"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Le Parfum", "brand": "Blue for Men", "gender": "Male/Unisex", "season": "Fall, Winter", "notes": "Top - Cardamom / Heart - Lavender, Iris / Base - Vanilla, Oriental Woods", "category": ["Woody", "Oriental", "Spicy", "Aromatic", "Fougere", "Gourmand"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Lemon Sorbet", "brand": "Arabiyat Sugar", "gender": "Unisex", "season": "Spring, summer", "notes": "Top Notes: Zesty lemon and a subtle nuance of rumMiddle/Heart Notes: Sweet gourmand and sorbet cream accordBase Notes: Creamy vanilla and soft musk", "category": ["Gourmand", "Fruity", "Oriental", "Creamy", "Sweet", "Vanilla", "Animalic"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Love & Peace", "brand": "Lattafa", "gender": "Unisex/Female", "season": "Spring-Fall", "notes": "Top Notes: Almond, Black Currant, and BergamotMiddle (Heart) Notes: Rose and TuberoseBase Notes: Sandalwood, Vanilla, and Heliotrope", "category": ["Floral", "Sweet", "Gourmand", "Woody", "Chypre", "Citrus"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Luxe Chic", "brand": "Maison Alhambra", "gender": "Female/Unisex", "season": "Spring, Fall", "notes": "Top - Tangerine, Freesia / Heart - Lily of the Valley, Jasmine, Rose / Base - Musk, Sandalwood, Amber", "category": ["Floral", "Fresh", "Woody", "Creamy", "Amber", "Animalic"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Maitha Oil (Attar)", "brand": "Lattafa", "gender": "Unisex", "season": "Fall, Winter", "notes": "Top - Anise / Heart - Caramel / Base - Vanilla, Tonka Bean, Musk", "category": ["Gourmand", "Sweet", "Vanilla", "Animalic", "Aromatic"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "Concentrated oil"}, {"name": "Majestic Supreme", "brand": "Le Falcone", "gender": "Women/Unisex", "season": "Fall-Winter / versatile", "notes": "Top - Rose, peony, pink pepper / Heart - Raspberry blossom, jasmine / Base - Amber, papyrus, tonka, vanilla", "category": ["Floral", "Sweet", "Fruity", "Gourmand", "Spicy"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Malika", "brand": "Nusuk", "gender": "Female", "season": "Fall , winter ", "notes": "Top Notes: Ozonic notes, apple, aldehydic notes, tarragon, bergamot, and orangeHeart Notes: Lily of the valley, jasmine, rose, carnation, orchid, and honeysuckleBase Notes: Musk, amber, vanilla, sandalwood, cedarwood, and orris", "category": ["Floral", "Oriental", "Citrus", "Woody", "Gourmand", "Sweet"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Mango Affogato", "brand": "Arabiyat Sugar", "gender": "Unisex", "season": "Spring-Summer / year-round", "notes": "Top - Mango, nutmeg, clove / Heart - Leather, saffron, amber, moss / Base - Akigalawood, patchouli, vetiver, cypriol", "category": ["Fruity", "Woody", "Spicy", "Oriental", "Leather", "Amber"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Mango Ice", "brand": "Gulf Orchid", "gender": "Unisex", "season": "Spring-Summer", "notes": "Top Notes: Mango, Lemon, Ginger, RhubarbHeart (Middle) Notes: White Flowers, Amber, LicoriceBase Notes: Musk, Vanilla, Caramel, Chestnut", "category": ["Fruity", "Fresh", "Gourmand", "Sweet", "Spicy", "Vanilla", "Amber"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Marshmallow Blush", "brand": "Paris Corner", "gender": "Female/Unisex", "season": "Fall, Winter", "notes": "Top - Marshmallow, Sweet / Heart - Fruity / Base - Vanilla, Musk", "category": ["Gourmand", "Sweet", "Fruity", "Vanilla", "Animalic"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Marshmallow Dreams", "brand": "NatureWell", "gender": "Female", "season": "Fall, winter", "notes": "Top Notes: Lemon Sugar & MarshmallowMid Notes: Coconut CreamBase Notes: Vanilla Mousse & Whipped Cream", "category": ["Gourmand", "Sweet", "Fruity", "Vanilla", "Citrus"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Marshmallows Kiss", "brand": "Mamlakat Al Oud", "gender": "Unisex", "season": "Fall, Winter, Spring", "notes": "Top - Strawberry, Blackberry (or Caramel/Milk) / Heart - Jasmine, Rose, Marshmallow, Vanilla, Honey / Base - Vanilla, Musk, Praline, Tonka", "category": ["Gourmand", "Floral", "Sweet", "Fruity", "Vanilla"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Mayar", "brand": "Lattafa", "gender": "Female", "season": "Spring, Summer", "notes": "Top - Lychee, Raspberry, Violet Leaf / Heart - Peony, White Rose, Jasmine / Base - Musk, Vanilla", "category": ["Floral", "Fruity", "Fresh", "Gourmand", "Powdery", "Sweet"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Mayar Cherry Intense", "brand": "Lattafa", "gender": "Female", "season": "Fall, Winter", "notes": "Top - Strawberry, Bergamot / Heart - Cherry Jam, Cacao / Base - Vanilla, Amber, Patchouli", "category": ["Fruity", "Gourmand", "Sweet", "Chypre", "Citrus"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Milano", "brand": "Valentine", "gender": "Unisex", "season": "Fall, Winter", "notes": "Top - Raspberry, Peach, Bergamot / Heart - Rose, Jasmine, Orange Blossom / Base - Vanilla, Amber, Woods", "category": ["Floral", "Fruity", "Sweet", "Citrus", "Chypre", "Gourmand"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Momento", "brand": "Riiffs", "gender": "Unisex", "season": "Winter", "notes": "Top Notes: Sugar, Saffron, and Mandarin give a sweet and citrus opening.Heart (Middle) Notes: Tonka Bean, Damask Rose, and Agarwood (Oud) create a floral and rich center.Base Notes: Caramel, Amberwood, and Cedar leave a warm and woody finish.", "category": ["Aromatic", "Citrus", "Oriental", "Oud", "Sweet", "Amber"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Mystique", "brand": "Armaf", "gender": "Female", "season": "Fall, Winter", "notes": "Top - Pear, Tangerine, Bergamot, Orange / Heart - Vanilla, Strawberry, Mimosa, Rose, Ylang Ylang, Jasmine, Passionfruit / Base - Vanilla, Coffee, Tonka Bean, Patchouli, Vetiver", "category": ["Floral", "Fruity", "Gourmand", "Citrus", "Woody"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Mystique Charm", "brand": "Dorall Collection", "gender": "Female", "season": "Spring, summer", "notes": "Top Notes: Clementine, Cappuccino, Cactus, Pepper, and BlackberryMiddle (Heart) Notes: Mimosa, Hortensia (Hydrangea), Camellia, and OrchidBase Notes: Woody Notes, Blackberry, Musk, Amber, and Red Berries", "category": ["Sweet", "Floral", "Oriental", "Fruity", "Spicy", "Amber", "Animalic"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Nagham", "brand": "Atyaab", "gender": "Unisex", "season": "Winter", "notes": "Top Notes: Rose, Jasmine, and BergamotMiddle (Heart) Notes: Amber, Vetiver, and Candied Fruit (such as sweet strawberries and cherries)Base Notes: Vanilla, Cedarwood, and Sandalwood", "category": ["Floral", "Woody", "Oriental", "Sweet", "Chypre", "Citrus"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Nasmaat", "brand": "Lattafa", "gender": "Unisex", "season": "Spring, Fall", "notes": "Top - Blackcurrant, Apricot, Pineapple / Heart - Magnolia, Cyclamen, Jasmine, Orange Blossom, Rose / Base - Vanilla, Cashmeran, Caramel, Sandalwood", "category": ["Floral", "Fruity", "Sweet", "Gourmand", "Woody"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Natural Intense Body Spray", "brand": "Mayar", "gender": "Female", "season": "Fall, Winter", "notes": "Top - Sweet Gourmand / Heart - Vanilla / Base - Musk", "category": ["Gourmand", "Sweet", "Vanilla", "Animalic", "Musky"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "Body spray"}, {"name": "Nebras", "brand": "Lattafa", "gender": "Unisex", "season": "Fall, Winter", "notes": "Top - Red Berries, Mandarin Orange / Heart - Vanilla, Cacao, Rose / Base - Sugar, Tonka Bean, Amber, Musk", "category": ["Gourmand", "Fruity", "Sweet", "Citrus", "Vanilla", "Amber"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Nebras Elixir", "brand": "Lattafa", "gender": "Unisex", "season": "Fall, Winter, Mild Spring", "notes": "Top - Milk Candy, Whipped Cream / Heart - Sugar Cane, Heliotrope / Base - Vanilla, Ambroxan, Musk", "category": ["Gourmand", "Sweet", "Amber", "Creamy", "Floral"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Nero Xtravagant", "brand": "Valentine (Urban Collection)", "gender": "Male/Unisex (leans masculine)", "season": "Fall, Winter (versatile)", "notes": "Top - Calabrian Bergamot, Espresso Coffee Accord / Heart - Coffee / Base - Vetiver", "category": ["Woody", "Fresh", "Aromatic", "Chypre", "Citrus", "Gourmand"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Noor", "brand": "Riiffs", "gender": "Unisex", "season": "Fall, Winter", "notes": "Top Notes: Caramel and milkMiddle (Heart) Notes: Gourmand accord and lily of the valleyBase Notes: Vanilla, musk, and praline", "category": ["Gourmand", "Floral", "Sweet", "Vanilla", "Animalic", "Creamy"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Nuha Vanilla Pearl", "brand": "Khadlaj", "gender": "Female", "season": "Fall, Winter", "notes": "Top - Blackcurrant, Strawberry, Freesia / Heart - Raspberry, Magnolia, Cashmere Wood / Base - Vanilla, Caramel, Moss", "category": ["Fruity", "Gourmand", "Floral", "Sweet", "Woody"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Nyla", "brand": "Arabiyat Prestige", "gender": "Female", "season": "Spring, Summer", "notes": "Top Notes: Coconut, Peach, Bergamot, and Mandarin (offering a fresh, sun-kissed fruit opening)Heart Notes: Tiare Flower, White Flowers, Jasmine, and Rose (providing an exotic and romantic floral bouquet)Base Notes: White Musk, Patchouli, Sandalwood, and Heliotrope (delivering a creamy, soft, and sensual woody finish)", "category": ["Floral", "Fruity", "Fresh", "Citrus", "Woody", "Creamy"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Nyla Vanielle", "brand": "Arabiyat Prestige", "gender": "Female", "season": "Fall, Winter", "notes": "Top - Jasmine, Vanilla Bean / Heart - Caramel, Amber / Base - Musk, Tonka Bean, Vanilla", "category": ["Gourmand", "Sweet", "Floral", "Vanilla", "Amber"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Obsidian", "brand": "French Avenue", "gender": "Unisex/Male", "season": "Fall-Winter", "notes": "Top Notes: Aldehydes, Grapefruit, BergamotHeart Notes: Myrrh, Jasmine, LabdanumBase Notes: Vanilla, Amber, Tonka Bean", "category": ["Woody", "Oriental", "Smoky", "Chypre", "Citrus", "Floral", "Gourmand"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Odyssey Candee", "brand": "Armaf", "gender": "Female-leaning", "season": "Fall, Winter", "notes": "Top - Strawberry, Raspberry, Peach, Bergamot / Heart - Caramel, Jasmine / Base - Patchouli, Musk, Amber", "category": ["Fruity", "Gourmand", "Sweet", "Chypre", "Citrus", "Floral"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Odyssey Marshmallow", "brand": "Armaf", "gender": "Unisex", "season": "Spring, Fall, Winter", "notes": "Top - Apple, Lemon, Coconut, Peony, Lily of the Valley / Heart - Strawberry, Peach, Raspberry, Apricot, Marshmallow, Orange Blossom / Base - Vanilla, Praline, Tonka, Amber, Musk, Mascarpone", "category": ["Gourmand", "Fruity", "Sweet", "Floral", "Citrus"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Opulent Dubai", "brand": "Lattafa", "gender": "Unisex", "season": "Spring, Summer (versatile year-round in mild climates)", "notes": "Top - Mango, Grapefruit, Lemon, Ginger / Heart - Jasmine, Cedarwood, Violet / Base - Woodsy notes, Ambergris, Benzoin, Oakmoss", "category": ["Fruity", "Woody", "Fresh", "Floral", "Amber", "Citrus", "Oriental"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Oud Mood", "brand": "Lattafa", "gender": "Unisex", "season": "Fall, Winter", "notes": "Top - Rose, Saffron, Pimento / Heart - Agarwood (Oud), Caramel, Floral Notes, Patchouli / Base - Woody Notes, Amber, Resins, Incense, Musk", "category": ["Oriental", "Oud", "Woody", "Gourmand", "Smoky"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Panache Angel Dust", "brand": "Khadlaj", "gender": "Female", "season": "Spring, winter , fall", "notes": "Top Notes: Vanilla, Mandarin, and Red CurrantMiddle (Heart) Notes: Tuberose, Sandalwood, and RumBase Notes: Vanilla, Whipped Cream, Musk, and Benzoin", "category": ["Floral", "Sweet", "Powdery", "Gourmand", "Woody", "Citrus", "Creamy"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Peach Velvet", "brand": "Khadlaj", "gender": "Female", "season": "Spring, Summer, Fall", "notes": "Top - Guava, Peach, Nectarine / Heart - Vanilla, Ginger, Cinnamon, Amber / Base - Caramel, Musk, Sandalwood", "category": ["Fruity", "Gourmand", "Sweet", "Spicy", "Woody", "Creamy"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Pecan Butter Cookie", "brand": "Arabiyat Sugar", "gender": "Unisex/Female", "season": "Fall-Winter", "notes": "Top - Pecan, coconut milk, butter / Heart - Hazelnut, almond, roasted nuts / Base - Hazelnut, vanilla, ambergris", "category": ["Gourmand", "Sweet", "Amber", "Creamy", "Fruity"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Petra", "brand": "Lattafa", "gender": "Unisex", "season": "Fall, Winter", "notes": "Top Notes: Plum, RumHeart (Middle) Notes: Tuberose, CoconutBase Notes: Praline, Musk, Vanilla", "category": ["Gourmand", "Fruity", "Floral", "Sweet", "Vanilla"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Pink Velvet", "brand": "Maison Alhambra", "gender": "Female", "season": "Spring-Fall", "notes": "Top Notes: Bulgarian Rose and May RoseMiddle/Heart Notes: Turkish Rose and SaffronBase Notes: Patchouli, Tonka Bean, and Vanilla", "category": ["Floral", "Sweet", "Powdery", "Gourmand", "Oriental", "Vanilla", "Woody"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Piña Colada Musk Collection Body Spray", "brand": "Gulf Orchid", "gender": "Unisex", "season": "Spring, Summer", "notes": "Top - Pineapple, Coconut / Heart - Tropical / Base - Musk", "category": ["Fruity", "Fresh", "Sweet", "Animalic", "Musky", "Woody"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "Body spray"}, {"name": "Prive Rose", "brand": "Ameerat Al Arab", "gender": "Female", "season": "Spring , summer", "notes": "Top Notes: Strawberry, Grapes, and OrangeMiddle (Heart) Notes: Rose, White Musk, Jasmine, Gardenia, Ylang-Ylang, and LilyBase Notes: Tonka Bean, Amber, and Sandalwood", "category": ["Floral", "Sweet", "Gourmand", "Fruity", "Woody", "Citrus", "Creamy"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Qaed Al Fursan (Original)", "brand": "Lattafa", "gender": "Unisex (leans masculine)", "season": "Fall, Winter", "notes": "Top - Pineapple, Saffron / Heart - Balsam Fir, Jasmine / Base - Cedar, Amber, Agarwood (Oud)", "category": ["Fruity", "Woody", "Oud", "Oriental", "Floral"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Qaed Al Fursan Unlimited", "brand": "Lattafa", "gender": "Male/Unisex", "season": "Spring, Fall", "notes": "Top - Coconut, Pineapple, Citruses / Heart - Ylang-Ylang, Frangipani, Jasmine / Base - Vanilla, Musk, Sandalwood, Sweet Notes", "category": ["Fruity", "Floral", "Sweet", "Woody", "Citrus"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Qaed Al Fursan Untamed", "brand": "Lattafa", "gender": "Male/Unisex", "season": "Spring, Fall", "notes": "Top - Apple, Citrus / Heart - Floral / Base - Sweet, Woody", "category": ["Fruity", "Woody", "Fresh", "Citrus", "Sweet"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Raheeq", "brand": "Nusuk", "gender": "Unisex", "season": "Fall , winter", "notes": "Top Notes: Honey, Blood Orange, Apricot, and LemonMiddle (Heart) Notes: Caramel, Coconut, and MagnoliaBase Notes: Vanilla Absolute, Musk, and Sandalwood", "category": ["Floral", "Sweet", "Gourmand", "Citrus", "Woody", "Creamy"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Raneen", "brand": "Lattafa", "gender": "Female", "season": "Fall, Winter", "notes": "Top - Fruity, Sweet / Heart - Floral / Base - Vanilla, Musk", "category": ["Floral", "Fruity", "Sweet", "Gourmand", "Vanilla", "Animalic"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Rave Now (for Women)", "brand": "Lattafa", "gender": "Female", "season": "Spring, Fall", "notes": "Top - Red Fruits, Orange / Heart - Marshmallow, Jasmine, Lily of the Valley / Base - Vanilla, Musk, Moss", "category": ["Fruity", "Gourmand", "Floral", "Citrus", "Sweet", "Vanilla"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Rave Now Intense", "brand": "Lattafa", "gender": "Male/Unisex", "season": "Spring, Fall", "notes": "Top - Cucumber, Watermelon, Tangerine / Heart - Basil, Sage / Base - Sandalwood, Leather, Cedar", "category": ["Fresh", "Woody", "Aromatic", "Creamy", "Leather"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Rave Rage", "brand": "Lattafa", "gender": "Unisex (leans masculine)", "season": "Year-round", "notes": "Top - Apple, mint / Heart - Geranium, cinnamon, lavender / Base - Vanilla, Peru balsam, cedarwood, guaiac wood", "category": ["Fresh", "Woody", "Spicy", "Aromatic", "Fougere", "Gourmand", "Oriental"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Red 500", "brand": "Baraja", "gender": "Unisex/Male", "season": "Fall, Winter", "notes": "Top - Red Fruits, Spices / Heart - Sweet Notes / Base - Woody, Musk", "category": ["Fruity", "Woody", "Spicy", "Animalic", "Musky", "Sweet"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Red Velvet Delicacy", "brand": "Armaf", "gender": "Unisex", "season": "Fall, Winter", "notes": "Top - Strawberry, Lemon / Heart - Whipped Sugar, Sugarberry, Frangipani / Base - Vanilla Bean, Musk, Amber", "category": ["Gourmand", "Fruity", "Sweet", "Vanilla", "Amber"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Royal Men", "brand": "Al Rehab", "gender": "Male", "season": "Fall, Winter", "notes": "Top - Spicy, Citrus, Woody / Heart - Floral, Sweet / Base - Amber, Musk, Vanilla", "category": ["Woody", "Spicy", "Oriental", "Sweet", "Citrus", "Gourmand", "Vanilla", "Amber"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Safa", "brand": "Nusuk", "gender": "Unisex/Female", "season": "Spring-Summer / versatile", "notes": "Top - Marshmallow, Strawberry, Lemon / Heart - Coconut, Sugar, Nectarine / Base - Vanilla, Musk, Ambroxan", "category": ["Gourmand", "Fruity", "Sweet", "Amber", "Vanilla"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Sakeena", "brand": "Lattafa", "gender": "Female/Unisex", "season": "Fall, Winter", "notes": "Top - Passionfruit, Mandarin Orange, Ozonic Notes / Heart - Raspberry, Rose, Orange Blossom, Sea Salt / Base - Toffee, Praline, Vanilla, Musk", "category": ["Fruity", "Gourmand", "Floral", "Sweet", "Citrus", "Aquatic"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Samiya", "brand": "Khadlaj", "gender": "Female", "season": "Spring , fall", "notes": "Top/Head Notes: Jasmine, Lily of the ValleyMiddle/Heart Notes: Amber, VioletBase Notes: Oud, Saffron, Sandalwood", "category": ["Floral", "Oriental", "Woody", "Powdery", "Creamy"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Sceptre Malachite", "brand": "Maison Alhambra", "gender": "Unisex", "season": "Spring-Summer", "notes": "Top - Green tangerine, bergamot, blackcurrant / Heart - Aromatic + spicy notes, lavender, pink pepper, jasmine / Base - Amber, musk, woody notes, vetiver", "category": ["Fresh", "Aromatic", "Woody", "Chypre", "Citrus", "Floral"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Sensual Vanilla", "brand": "Maison Alhambra", "gender": "Unisex", "season": "Fall, Winter", "notes": "Top Note: Bitter AlmondMiddle Notes: Vanilla, Floral NotesBase Notes: Vanilla Absolute, Tonka Bean, Sandalwood", "category": ["Oriental", "Gourmand", "Woody", "Creamy", "Sweet", "Vanilla"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Silver", "brand": "Al Rehab", "gender": "Unisex/Male", "season": "Spring, Summer", "notes": "Top - Fresh Citrus, Metallic / Heart - Floral / Base - Musk, Sweet", "category": ["Fresh", "Citrus", "Metallic", "Animalic", "Musky"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Soft", "brand": "Al Rehab", "gender": "Unisex (leans feminine)", "season": "Fall, Winter", "notes": "Top - Citruses / Heart - Orchid, Jasmine, Vanilla, Caramel / Base - White Musk, Woody Notes, Vetiver", "category": ["Floral", "Sweet", "Gourmand", "Woody", "Citrus"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Spectre Original", "brand": "French Avenue", "gender": "Male/Unisex (leans masculine)", "season": "Fall, Winter", "notes": "Top - Incense, Guaiac Wood, Saffron / Heart - Leather, Amberwood, Violet, Sugar Cane / Base - Smoke, Patchouli, Sandalwood, Woodsy Notes, Black Musk", "category": ["Woody", "Leather", "Oriental", "Amber", "Smoky", "Creamy"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Strawberries & Cream", "brand": "Royal Apothic", "gender": "Female", "season": "Spring, summer", "notes": "Top Notes: Raspberry and plum (or juicy brightness like strawberry, raspberry, apple, and nectarine)Heart / Middle Notes: Strawberry and whipped creamBase Notes: Sugar cubes, caramel, tonka vanilla, and soft amber", "category": ["Gourmand", "Fruity", "Sweet", "Vanilla", "Amber"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Strawberry Tres Leches", "brand": "Arabiyat Sugar", "gender": "Female", "season": "Spring-Summer / year-round", "notes": "Top Notes: Strawberry, Milk, Nectarine, FreesiaHeart / Middle Notes: Marshmallow, Milk Candy, Caramel, Orange BlossomBase Notes: Vanilla, White Musk, Ambergris", "category": ["Gourmand", "Fruity", "Sweet", "Floral", "Amber"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Sugar Crown", "brand": "Lattafa", "gender": "Female/Unisex", "season": "Fall-Winter", "notes": "Top Notes: Bitter orange, lemon, and candied fruitsMiddle Notes (Heart): Bubble gum, blueberry, peach, peach blossom, Bulgarian rose, ginger, and cinnamonBase Notes: Ambroxan, musk, and cedar", "category": ["Gourmand", "Sweet", "Spicy", "Citrus", "Amber", "Fruity"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Sugar Me Dulce De Leche", "brand": "Maison Alhambra", "gender": "Unisex/Female", "season": "Fall-Winter", "notes": "Dulce de leche / caramel-vanilla gourmand", "category": ["Gourmand", "Sweet", "Vanilla"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Sugarcane Vanilla", "brand": "Arabiyat Prestige", "gender": "Unisex", "season": "Fall, Winter", "notes": "Top Notes: Raspberry, Cherry, MandarinMiddle/Heart Notes: Lactones (milky/creamy notes), Vanilla, White FlowersBase Notes: Sandalwood, Musk", "category": ["Sweet", "Gourmand", "Fruity", "Floral", "Creamy", "Woody", "Citrus"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Supremacy Only Intense", "brand": "Afnan", "gender": "Male", "season": "Spring, autumn", "notes": "Top Notes: Black Currant, Bergamot, and AppleMiddle (Heart) Notes: Oakmoss, Patchouli, and LavenderBase Notes: Ambergris, Musk, and Saffron", "category": ["Woody", "Fruity", "Fresh", "Chypre", "Fougere", "Amber", "Oriental"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Sweet Surrender", "brand": "Mahajan", "gender": "Female", "season": "Fall-Winter / versatile", "notes": "Top Note: CaramelMiddle Notes: Coumarin (sweet, vanilla-like scent) and HoneyBase Notes: White Musk and Vanilla", "category": ["Gourmand", "Sweet", "Fougere", "Vanilla", "Animalic"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Sweet Surrender Pink Parfait", "brand": "Mahajan", "gender": "Female", "season": "Spring-Summer / year-round", "notes": "Top Notes: Graham Crackers, Marshmallow, Strawberry, Blackcurrant, and Chocolate (Strawberry S\'mores)Middle (Heart) Notes: Marshmallow, Orange Blossom, and JasmineBase Notes: Vanilla, Whipped Cream, Sandalwood, Amber, and Musk", "category": ["Gourmand", "Fruity", "Sweet", "Floral", "Creamy", "Woody"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Tahira", "brand": "Riiffs", "gender": "Female", "season": "Spring , summer, fall", "notes": "Top Notes: Almond and Dragon fruitMiddle (Heart) Notes: Rose de Mai, Gardenia, and Praline (often listed as Rose de Mai and Gardenia with praline accents in the blend)Base Notes: Vanilla Absolute, Tonka Bean, and Patchouli", "category": ["Floral", "Oriental", "Gourmand", "Sweet", "Woody", "Vanilla"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Taif", "brand": "Riiffs", "gender": "Unisex", "season": "Versatile (Spring-Summer preferred)", "notes": "Top - Ginger, Calabrian Bergamot, Lemon, Orange Blossom / Heart - Musk, Rose Petals, Tuberose / Base - Vanilla Bean, Amberwood, Clearwood", "category": ["Floral", "Fresh", "Woody", "Citrus", "Amber", "Chypre"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Teriaq", "brand": "Lattafa", "gender": "Unisex (leans feminine)", "season": "Fall, Winter", "notes": "Top - Caramel, Bitter Almond, Apricot, Pink Pepper / Heart - Honey, Rhubarb, White Flowers, Rose / Base - Leather, Vanilla, Musk, Vetiver, Labdanum", "category": ["Gourmand", "Floral", "Oriental", "Sweet", "Chypre", "Leather"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Teriaq Intense", "brand": "Lattafa", "gender": "Unisex", "season": "Fall, Winter", "notes": "Top - Saffron, Bergamot / Heart - Plum Liquor, Cinnamon / Base - Amber, Tonka Bean, Benzoin", "category": ["Oriental", "Spicy", "Sweet", "Boozy", "Chypre", "Citrus"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "The King", "brand": "Ali", "gender": "Male", "season": "Fall-Winter / versatile", "notes": "Top Notes: Plum, Ozonic notes, Grapefruit, BergamotMiddle (Heart) Notes: Hazelnut, Honey, Cedar, Cashmere Wood, Orange Blossom, JasmineBase Notes: Amberwood, Patchouli, Oakmoss, Vetiver", "category": ["Woody", "Oriental", "Citrus", "Chypre", "Floral", "Amber"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Tiramisu Candy", "brand": "Rizz", "gender": "Female", "season": "Fall , winter", "notes": "Top Note: BergamotMiddle Notes: Black Currant, Strawberry, and MilkBase Notes: Musk and Vanilla", "category": ["Gourmand", "Fruity", "Sweet", "Citrus"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Tiramisu Coco", "brand": "Zimaya", "gender": "Unisex", "season": "Fall, Winter", "notes": "Top Notes: Amaretto and CoffeeMiddle Notes: Ice cream, Biscuit, and VanillaBase Notes: Vanilla, Brown sugar, and Amber", "category": ["Gourmand", "Oriental", "Sweet", "Vanilla", "Amber", "Creamy"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Toffee Ganache", "brand": "Arabiyat Sugar", "gender": "Unisex", "season": "Fall-Winter", "notes": "Top Notes: Hazelnut, Clove, Milk (or Vanilla Cream), and VanillaMiddle (Heart) Notes: Cinnamon, Toffee, and White FlowersBase Notes: Gourmand Accord, Milk, Biscuit (Speculoos/Biscoff), and Spices", "category": ["Gourmand", "Sweet", "Spicy", "Creamy", "Vanilla"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Tubbees Tres Leches", "brand": "Grandeur", "gender": "Unisex", "season": "Fall, winter", "notes": "Top Notes: Vanilla bean, cold milk accord, sweet notes, spicy notes, and caramelMiddle Notes (Heart): Milk, chocolate, and floral notes", "category": ["Gourmand", "Sweet", "Vanilla", "Creamy"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Vanilla", "brand": "Bellavita", "gender": "Female", "season": "Fall, Winter", "notes": "Top - Aldehydes, Heliotrope, Coconut, Vanilla / Heart - Vanilla, Mango / Base - White Musk, Coconut, Vanilla Absolute", "category": ["Gourmand", "Sweet", "Fruity", "Floral", "Powdery"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Vanilla Addiction", "brand": "Gulf Orchid", "gender": "Unisex/Female", "season": "Fall-Winter", "notes": "Top Notes: Coconut, Lavender, and Lily of the ValleyHeart (Middle) Notes: Tonka Bean, Jasmine, Rose, and PatchouliBase Notes: Vanilla, Amber, and Musk", "category": ["Gourmand", "Sweet", "Floral", "Aromatic", "Fougere", "Fruity"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Vanilla Aura", "brand": "Maison Asrar", "gender": "Female/Unisex", "season": "Fall, Winter", "notes": "Top - Vanilla / Heart - Creamy Sweet / Base - Vanilla, Musk", "category": ["Gourmand", "Sweet", "Creamy", "Vanilla", "Animalic"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Vanilla Ayelet", "brand": "Khayali", "gender": "Unisex", "season": "Fall-Winter", "notes": "Vanilla orchid, jasmine / Brown sugar, tonka / Amber, musk, patchouli (Kayali-inspired)", "category": ["Gourmand", "Floral", "Sweet", "Vanilla", "Woody"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Vanilla Cream Macaron", "brand": "Arabiyat Sugar", "gender": "Unisex", "season": "Fall, Winter", "notes": "Top Note: Ripe BananaMiddle Note: Chantilly CreamBase Note: Custard Sauce (or Vanilla/Vanilla Musk)", "category": ["Gourmand", "Fruity", "Sweet", "Vanilla", "Animalic"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Vanilla Dunes", "brand": "Khadlaj", "gender": "Unisex", "season": "Autumn, Winter", "notes": "Top - Vanilla, Cinnamon, Cardamom, Bergamot / Heart - Orange Blossom, Guaiac Wood, Bourbon / Base - Praline, Amber, Musk", "category": ["Gourmand", "Spicy", "Woody", "Citrus", "Sweet"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Vanilla Freak (Give Me Gourmand)", "brand": "Lattafa", "gender": "Unisex / Female-leaning", "season": "Fall, Spring", "notes": "Top - Cupcake / Heart - Sugar Frosting, Almond, Cinnamon / Base - Butter, Vanilla, Musk", "category": ["Gourmand", "Sweet", "Creamy", "Spicy", "Vanilla"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Vanilla Madness", "brand": "Mamlakat Al Oud", "gender": "Unisex (leans feminine)", "season": "Fall, Winter (versatile year-round)", "notes": "Top - Vanilla (woody tones), Lavender, Cacao, Ginger / Heart - Vanilla Caviar / Base - Vanilla Absolute", "category": ["Gourmand", "Sweet", "Aromatic", "Fougere", "Spicy"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Vanilla Milkshake", "brand": "Snack House", "gender": "Unisex", "season": "Fall, winter", "notes": "Top Notes: Vanilla Orchid and JasmineMiddle (Heart) Notes: Brown Sugar and Tonka BeanBase Notes: Amber, Amberwood, Musk, and Patchouli", "category": ["Gourmand", "Oriental", "Floral", "Amber", "Sweet", "Woody"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Vanilla Musk", "brand": "NatureWell", "gender": "Unisex", "season": "Fall, winter", "notes": "Top Notes: Sugared Petals & Mandarin MuskMid Notes: Vanilla Cream & SpiceBase Notes: Sleek Woods & Tonka", "category": ["Gourmand", "Sweet", "Citrus", "Vanilla", "Animalic"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Vanilla Seduction", "brand": "Maison Asrar", "gender": "Female/Unisex", "season": "Fall, Winter", "notes": "Top - Plum, Jasmine, Lily of the Valley / Heart - Vanilla, Brown Sugar, Caramel / Base - Tonka, Patchouli, Amber, Musk", "category": ["Gourmand", "Floral", "Sweet", "Vanilla", "Woody"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Vanilla Skin", "brand": "Phlur", "gender": "Unisex (female-leaning)", "season": "Fall, Winter", "notes": "Top - Sugar, Pink Pepper, Apple / Heart - Cashmere Wood, Jasmine, Lily / Base - Vanilla, Sandalwood, Agarwood, Benzoin", "category": ["Gourmand", "Woody", "Sweet", "Floral", "Oud"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Velvet Breeze", "brand": "Mamlakat Al Oud", "gender": "Unisex", "season": "Fall, Winter", "notes": "Top - Italian Bergamot, Pistachio Gelato, Hazelnut, Sweet Rum, Cardamom / Heart - Geranium, White Peony, Muguet, Jasmine / Base - Amber, Musk, Woody Notes", "category": ["Gourmand", "Floral", "Woody", "Chypre", "Citrus", "Spicy"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Vulcan Baie", "brand": "French Avenue", "gender": "Unisex", "season": "Spring, Summer", "notes": "Top - Blackberry, Black Currant, Rosemary, Bergamot / Heart - Raspberry, Vodka, Basil, Lily of the Valley / Base - Strawberry, Musk, Peach, Amber, Sandalwood, Patchouli, Incense", "category": ["Fruity", "Fresh", "Aromatic", "Woody", "Oriental", "Chypre"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Whipped Pleasure (Give Me Gourmand)", "brand": "Lattafa", "gender": "Female", "season": "Fall, Winter", "notes": "Top - Caramel, Popcorn, Salted Caramel / Heart - Milk, Jasmine / Base - Tonka, Benzoin, Musk, Ambrofix", "category": ["Gourmand", "Sweet", "Floral", "Oriental", "Animalic"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Yara Candy Body Spray", "brand": "Lattafa", "gender": "Female", "season": "Fall, Winter", "notes": "Top - Candy, Sweet / Heart - Fruity / Base - Vanilla, Musk", "category": ["Gourmand", "Sweet", "Fruity", "Vanilla", "Animalic"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "Body spray"}, {"name": "Yara Elixir", "brand": "Lattafa", "gender": "Female", "season": "Fall, Winter, Cool Spring Days", "notes": "Top - Strawberry S\'mores, Black Currant / Heart - Jasmine, Orange Blossom / Base - Vanilla, Caramel, Amber, Musk", "category": ["Gourmand", "Floral", "Sweet", "Fruity", "Citrus"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Yara Original", "brand": "Lattafa", "gender": "Female", "season": "Spring-Summer", "notes": "Top - Orchid, heliotrope, tangerine / Heart - Gourmand accord, tropical fruits / Base - Vanilla, musk, sandalwood", "category": ["Floral", "Gourmand", "Fruity", "Woody", "Creamy", "Powdery"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Yara Tous", "brand": "Lattafa", "gender": "Female", "season": "Summer", "notes": "Top Notes: Mango, coconut, passion fruitMiddle Notes: Jasmine, orange blossom, heliotropeBase Notes: Vanilla, cashmeran, musk", "category": ["Floral", "Fruity", "Sweet", "Gourmand", "Citrus", "Powdery"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Zainab Oil", "brand": "Khadlaj", "gender": "Unisex", "season": "Fall, Winter", "notes": "Top - Bergamot, Gardenia, Almond / Heart - Coconut, Caramel / Base - Patchouli, Vanilla, Musk", "category": ["Gourmand", "Floral", "Sweet", "Chypre", "Citrus"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "Concentrated oil"}, {"name": "Zenith", "brand": "Riiffs", "gender": "Unisex", "season": "Spring, summer, winter", "notes": "Top Notes: Coconut, Vanilla, Creamy AccordsHeart (Middle) Notes: Fruity Notes, Jasmine, Powdery AccordsBase Notes: Vanilla, Musk, Woody Notes", "category": ["Gourmand", "Sweet", "Powdery", "Fruity", "Creamy", "Floral"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Zukhruf Pink", "brand": "Zimaya", "gender": "Unisex", "season": "Winter", "notes": "Top Notes: Orchid, Heliotrope, and VanillaHeart (Middle) Notes: Musk, Marshmallow, and Almond MilkBase Notes: Amber, Vanilla, and Sandalwood", "category": ["Gourmand", "Floral", "Creamy", "Woody", "Powdery"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Victoria", "brand": "Lattafa", "gender": "Unisex", "season": "Spring, summer ", "notes": "Top Notes: Lemon Meringue Pie (offering a bright, zesty, and sweet citrus opening)Middle (Heart) Notes: Neroli (lending a delicate, sophisticated, and clean floral touch)Base Notes: Vanilla (providing a smooth, creamy, and comforting warm finish)", "category": ["Gourmand", "Floral", "Fruity", "Citrus", "Creamy", "Sweet", "Vanilla"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Qimmah", "brand": "Lattafa", "gender": "Female", "season": "Fall, Winter", "notes": "Top Notes: Almond, CoffeeHeart (Middle) Notes: Jasmine, Tuberose, Tonka BeanBase Notes: Vanilla, Cacao, Sandalwood", "category": ["Gourmand", "Floral", "Woody", "Creamy", "Sweet"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Tiramisu S’mores", "brand": "Zimaya", "gender": "Female", "season": "Fall, Winter", "notes": "Top Notes: Marshmallow, Chocolate, Coffee, Bergamot, and Nectarine Blossom.Middle (Heart) Notes: Biscuit, Vanilla, Milk, Almond, and Musk.Base Notes: Sugar, Caramel, Creamy Notes, Amber, and Musk.", "category": ["Gourmand", "Sweet", "Creamy", "Chypre", "Citrus"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Tiramisu caramel", "brand": "Zimaya", "gender": "Unisex", "season": "Fall, Winter", "notes": "Top Note: CaramelMiddle (Heart) Notes: Honey, Coumarin, and Woody NotesBase Notes: Vanilla, Whiskey, and Musk", "category": ["Gourmand", "Sweet", "Boozy", "Fougere", "Vanilla"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Orhan", "brand": "Nusuk", "gender": "Unisex", "season": "Fall, Winter", "notes": "Top Notes: Blackberry, BlueberryMiddle Notes: Freesia, Lavender, RoseBase Notes: Vanilla, Raspberry, Oakmoss, Patchouli", "category": ["Gourmand", "Fougere", "Floral", "Fruity", "Woody", "Aromatic"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Nisma", "brand": "Arabiyat Prestige", "gender": "Female", "season": "Summer, spring", "notes": "Top Notes: Pistachio, Hazelnut, and Cassis (Blackcurrant bud)Middle (Heart) Notes: Raspberry, Lily of the Valley, Jasmine, and PeonyBase Notes: Sandalwood, Vanilla, Tonka Bean, Maltol, and Lactonic notes", "category": ["Gourmand", "Fruity", "Creamy", "Floral", "Woody"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}, {"name": "Lady glamour", "brand": "Arabiyat Prestige", "gender": "Female", "season": "Spring, summer ", "notes": "Top Notes: BergamotMiddle (Heart) Notes: Orange, Limonene, and RoseBase Notes: Coconut, Vanilla, White Musk, Dry Wood, and Gourmand notes", "category": ["Gourmand", "Citrus", "Chypre", "Fruity", "Sweet"], "dupe_of": "", "shelf_status": "Own", "size_ml": null, "concentration": "EDP"}], "wishlist": [{"name": "Sawaar", "brand": "Khadlaj", "notes": "", "gender": "Unisex", "season": "Versatile", "checked": false}, {"name": "Cloud candy", "brand": "Khadlaj", "notes": "", "gender": "Unisex", "season": "Versatile", "checked": false}, {"name": "Angham", "brand": "Gulf Orchid", "notes": "", "gender": "Unisex", "season": "Versatile", "checked": false}, {"name": "Queen of Arabia", "brand": "Lattafa", "notes": "Top Notes: Ylang-Ylang, Nutmeg, and Grapefruit ZestMiddle Notes: Jasmine, Rose, and White FloralsBase Notes: Vanilla, Amber, and Soft Woods", "gender": "Female", "season": "Fall, Winter", "checked": false}], "layer_recipes": [{"name": "Peach Floral whisper", "bottles": ["Sweet Surrender Pink Parfait", "Sugar Crown"], "season_label": "Cool / Autumn / Cold / Winter", "season_detail": "Best for Cool / Autumn / Cold / Winter. From bottle seasons: Spring-Summer / year-round, Fall-Winter.", "bands": ["Cool / Autumn", "Cold / Winter"], "application": {"steps": [{"order": 1, "name": "Sweet Surrender Pink Parfait", "brand": "Mahajan", "weight": 114, "role": "Heaviest base", "sprays": 2, "where": "Skin first - chest and behind knees (warm spots). Let it settle 30-60 sec.", "cats": "Gourmand, Fruity, Sweet, Floral"}, {"order": 2, "name": "Sugar Crown", "brand": "Lattafa", "weight": 74, "role": "Base / heart", "sprays": 2, "where": "Pulse points - wrists, inner elbows, neck. Do not rub.", "cats": "Gourmand, Sweet, Spicy, Citrus"}], "tips": ["Apply heaviest first, lightest last so the top notes stay bright.", "Wait 30-60 seconds between bottles so they do not wet-mix into mud.", "Start low - you can always add one spray; hard to remove.", "Suggested total around 4 sprays for this combo (adjust for heat and space)."], "total_sprays": 4, "order_names": ["Sweet Surrender Pink Parfait", "Sugar Crown"]}, "score": 100, "label": "Strong layer", "verdict": "Categories support each other - worth wearing together.", "why": "Sweet warmth meets a fresh lift so the dessert side stays wearable. Shared: blossom, musk, orange. Smells: opens strawberry/peach, heart rose/jasmine/vanilla, dries down vanilla/amber/musk. Spray **Sweet Surrender Pink Parfait** first (base), then **Sugar Crown** (top).", "gender": "Female"}, {"name": "Musk Sugar silk", "bottles": ["Eclaire", "Nyla"], "season_label": "Cool / Autumn / Cold / Winter", "season_detail": "Best for Cool / Autumn / Cold / Winter. From bottle seasons: Fall, Winter, Spring, Summer.", "bands": ["Cool / Autumn", "Cold / Winter"], "application": {"steps": [{"order": 1, "name": "Eclaire", "brand": "Lattafa", "weight": 86, "role": "Heaviest base", "sprays": 2, "where": "Skin first - chest and behind knees (warm spots). Let it settle 30-60 sec.", "cats": "Gourmand, Sweet, Vanilla, Animalic"}, {"order": 2, "name": "Nyla", "brand": "Arabiyat Prestige", "weight": 50, "role": "Mid layer", "sprays": 2, "where": "Neck and collarbone, or one spray through hair mist-style from a distance.", "cats": "Floral, Fruity, Fresh, Citrus"}], "tips": ["Apply heaviest first, lightest last so the top notes stay bright.", "Wait 30-60 seconds between bottles so they do not wet-mix into mud.", "Start low - you can always add one spray; hard to remove.", "Suggested total around 4 sprays for this combo (adjust for heat and space)."], "total_sprays": 4, "order_names": ["Eclaire", "Nyla"]}, "score": 143.0, "label": "Strong layer", "verdict": "Categories support each other - worth wearing together.", "why": "**Eclaire** reads heavier (base), and **Nyla** reads lighter (top) - so the stack has a clear bottom and a bright edge. Sweet/gourmand warmth meets a fresh lift - the fresh side keeps the dessert side from feeling too thick on skin. Shared notes: flowers, musk, white. Synergy (mango, tiare, pineapple): Eclaire has vanilla; Nyla has coconut, tiare. What you might smell after layering:. first hit - Caramel, Milk, Sugar, Coconut. as it settles - Honey, White Flowers. dry-down - Vanilla, Praline, Musk, White Musk. overall edible-sweet warmth with whatever bright notes ride on top. Together: **Eclaire** + **Nyla** - use the heavier one as the skin base, then the lighter one on pulse points so both show. Worth a skin test before a full outing - heat and your chemistry will finish the story.", "gender": "Female"}, {"name": "Pepper Apple veil", "bottles": ["Elyssia Scarlet", "Vanilla Skin"], "season_label": "Cool / Autumn / Cold / Winter", "season_detail": "Best for Cool / Autumn / Cold / Winter. From bottle seasons: Spring-Summer / versatile, Fall, Winter.", "bands": ["Cool / Autumn", "Cold / Winter"], "application": {"steps": [{"order": 1, "name": "Elyssia Scarlet", "brand": "Riiffs", "weight": 122, "role": "Heaviest base", "sprays": 2, "where": "Skin first - chest and behind knees (warm spots). Let it settle 30-60 sec.", "cats": "Fruity, Leather, Sweet, Gourmand"}, {"order": 2, "name": "Vanilla Skin", "brand": "Phlur", "weight": 112, "role": "Heaviest base", "sprays": 2, "where": "Skin first - chest and behind knees (warm spots). Let it settle 30-60 sec.", "cats": "Gourmand, Woody, Sweet, Floral"}], "tips": ["Apply heaviest first, lightest last so the top notes stay bright.", "Wait 30-60 seconds between bottles so they do not wet-mix into mud.", "Start low - you can always add one spray; hard to remove.", "Suggested total around 4 sprays for this combo (adjust for heat and space)."], "total_sprays": 4, "order_names": ["Elyssia Scarlet", "Vanilla Skin"]}, "score": 213.0, "label": "Strong layer", "verdict": "Categories support each other - worth wearing together.", "why": "**Elyssia Scarlet** reads heavier (base), and **Vanilla Skin** reads lighter (top) - so the stack has a clear bottom and a bright edge. Gourmand creaminess with floral lift - soft, skin-close, and a little pretty on top. Shared notes: benzoin, pepper, pink, vanilla. Synergy (caramel, tonka, vanilla): Elyssia Scarlet has vanilla; Vanilla Skin has sugar, vanilla. What you might smell after layering:. first hit - Black Cherry, Pink Pepper, Sugar, Apple. as it settles - Leather, Cream, Benzoin, Cashmere Wood. dry-down - Vanilla Absolute, Cashmeran, Amber, Iso E Super. overall edible-sweet warmth with whatever bright notes ride on top. This reads more date-night / cool weather than office heat - great for evenings. Together: **Elyssia Scarlet** + **Vanilla Skin** - use the heavier one as the skin base, then the lighter one on pulse points so both show. Worth a skin test before a full outing - heat and your chemistry will finish the story.", "gender": "Female"}, {"name": "Benzoin & Gourmand dusk", "bottles": ["Vanilla Skin", "Eshal Vanilla"], "season_label": "Cool / Autumn / Cold / Winter", "season_detail": "Best for Cool / Autumn / Cold / Winter. From bottle seasons: Fall, Winter, Fall, Winter.", "bands": ["Cool / Autumn", "Cold / Winter"], "application": {"steps": [{"order": 1, "name": "Vanilla Skin", "brand": "Phlur", "weight": 112, "role": "Heaviest base", "sprays": 2, "where": "Skin first - chest and behind knees (warm spots). Let it settle 30-60 sec.", "cats": "Gourmand, Woody, Sweet, Floral"}, {"order": 2, "name": "Eshal Vanilla", "brand": "Paris Corner", "weight": 86, "role": "Heaviest base", "sprays": 2, "where": "Skin first - chest and behind knees (warm spots). Let it settle 30-60 sec.", "cats": "Gourmand, Floral, Sweet, Vanilla"}], "tips": ["Apply heaviest first, lightest last so the top notes stay bright.", "Wait 30-60 seconds between bottles so they do not wet-mix into mud.", "Start low - you can always add one spray; hard to remove.", "Suggested total around 4 sprays for this combo (adjust for heat and space)."], "total_sprays": 4, "order_names": ["Vanilla Skin", "Eshal Vanilla"]}, "score": 139.0, "label": "Strong layer", "verdict": "Categories support each other - worth wearing together.", "why": "**Vanilla Skin** reads heavier (base), and **Eshal Vanilla** reads lighter (top) - so the stack has a clear bottom and a bright edge. Gourmand creaminess with floral lift - soft, skin-close, and a little pretty on top. Shared notes: jasmine, sugar, vanilla. Synergy (caramel, tonka, vanilla): Vanilla Skin has sugar, vanilla; Eshal Vanilla has caramel, sugar, vanilla. What you might smell after layering:. first hit - Sugar, Pink Pepper, Apple, Sweet Notes. as it settles - Cashmere Wood, Jasmine, Lily. dry-down - Vanilla, Sandalwood, Agarwood, Benzoin. overall edible-sweet warmth with whatever bright notes ride on top. This reads more date-night / cool weather than office heat - great for evenings. Together: **Vanilla Skin** + **Eshal Vanilla** - use the heavier one as the skin base, then the lighter one on pulse points so both show. Worth a skin test before a full outing - heat and your chemistry will finish the story.", "gender": "Female"}, {"name": "Candlelit Vanilla", "bottles": ["Vanilla Seduction", "Tiramisu S’mores"], "season_label": "Cool / Autumn / Cold / Winter", "season_detail": "Best for Cool / Autumn / Cold / Winter. From bottle seasons: Fall, Winter, Fall, Winter.", "bands": ["Cool / Autumn", "Cold / Winter"], "application": {"steps": [{"order": 1, "name": "Vanilla Seduction", "brand": "Maison Asrar", "weight": 116, "role": "Heaviest base", "sprays": 2, "where": "Skin first - chest and behind knees (warm spots). Let it settle 30-60 sec.", "cats": "Gourmand, Floral, Sweet, Vanilla"}, {"order": 2, "name": "Tiramisu S’mores", "brand": "Zimaya", "weight": 82, "role": "Base / heart", "sprays": 2, "where": "Pulse points - wrists, inner elbows, neck. Do not rub.", "cats": "Gourmand, Sweet, Creamy, Chypre"}], "tips": ["Apply heaviest first, lightest last so the top notes stay bright.", "Wait 30-60 seconds between bottles so they do not wet-mix into mud.", "Start low - you can always add one spray; hard to remove.", "Suggested total around 4 sprays for this combo (adjust for heat and space)."], "total_sprays": 4, "order_names": ["Vanilla Seduction", "Tiramisu S’mores"]}, "score": 145.0, "label": "Strong layer", "verdict": "Categories support each other - worth wearing together.", "why": "**Vanilla Seduction** reads heavier (base), and **Tiramisu S’mores** reads lighter (top) - so the stack has a clear bottom and a bright edge. Sweet/gourmand warmth meets a fresh lift - the fresh side keeps the dessert side from feeling too thick on skin. Shared notes: amber, caramel, musk, sugar, vanilla. Synergy (caramel, tonka, vanilla): Vanilla Seduction has caramel, sugar, tonka; Tiramisu S’mores has caramel, marshmallow, sugar. What you might smell after layering:. first hit - Plum, Jasmine, Lily of the Valley, Marshmallow. as it settles - Vanilla, Brown Sugar, Caramel. dry-down - Tonka, Patchouli, Amber, Musk. overall edible-sweet warmth with whatever bright notes ride on top. Together: **Vanilla Seduction** + **Tiramisu S’mores** - use the heavier one as the skin base, then the lighter one on pulse points so both show. Worth a skin test before a full outing - heat and your chemistry will finish the story.", "gender": "Female"}, {"name": "Caramel Mandarin bloom", "bottles": ["Vanilla Seduction", "Dalal"], "season_label": "Cool / Autumn / Cold / Winter", "season_detail": "Best for Cool / Autumn / Cold / Winter. From bottle seasons: Fall, Winter, Spring.", "bands": ["Cool / Autumn", "Cold / Winter"], "application": {"steps": [{"order": 1, "name": "Vanilla Seduction", "brand": "Maison Asrar", "weight": 116, "role": "Heaviest base", "sprays": 2, "where": "Skin first - chest and behind knees (warm spots). Let it settle 30-60 sec.", "cats": "Gourmand, Floral, Sweet, Vanilla"}, {"order": 2, "name": "Dalal", "brand": "Lattafa", "weight": 52, "role": "Mid layer", "sprays": 2, "where": "Neck and collarbone, or one spray through hair mist-style from a distance.", "cats": "Floral, Fruity, Fresh, Citrus"}], "tips": ["Apply heaviest first, lightest last so the top notes stay bright.", "Wait 30-60 seconds between bottles so they do not wet-mix into mud.", "Start low - you can always add one spray; hard to remove.", "Suggested total around 4 sprays for this combo (adjust for heat and space)."], "total_sprays": 4, "order_names": ["Vanilla Seduction", "Dalal"]}, "score": 190.0, "label": "Strong layer", "verdict": "Categories support each other - worth wearing together.", "why": "**Vanilla Seduction** reads heavier (base), and **Dalal** reads lighter (top) - so the stack has a clear bottom and a bright edge. Sweet/gourmand warmth meets a fresh lift - the fresh side keeps the dessert side from feeling too thick on skin. Shared notes: jasmine, musk, vanilla. Synergy (caramel, tonka, sugar): Vanilla Seduction has caramel, sugar, tonka; Dalal has vanilla. What you might smell after layering:. first hit - Plum, Jasmine, Lily of the Valley, Apple (Golden Delicious). as it settles - Vanilla, Brown Sugar, Caramel, Jasmine. dry-down - Tonka, Patchouli, Amber, Musk. overall edible-sweet warmth with whatever bright notes ride on top. Together: **Vanilla Seduction** + **Dalal** - use the heavier one as the skin base, then the lighter one on pulse points so both show. Worth a skin test before a full outing - heat and your chemistry will finish the story.", "gender": "Female"}, {"name": "Vanilla Bergamot veil", "bottles": ["Zenith", "Bahiya Garnet"], "season_label": "Cold / Winter / Cool / Autumn", "season_detail": "Best for Cold / Winter / Cool / Autumn. From bottle seasons: Spring, summer, winter, Fall, Winter.", "bands": ["Cold / Winter", "Cool / Autumn"], "application": {"steps": [{"order": 1, "name": "Zenith", "brand": "Riiffs", "weight": 88, "role": "Heaviest base", "sprays": 2, "where": "Skin first - chest and behind knees (warm spots). Let it settle 30-60 sec.", "cats": "Gourmand, Sweet, Powdery, Fruity"}, {"order": 2, "name": "Bahiya Garnet", "brand": "Arabiyat Prestige", "weight": 86, "role": "Heaviest base", "sprays": 2, "where": "Skin first - chest and behind knees (warm spots). Let it settle 30-60 sec.", "cats": "Fruity, Oriental, Sweet, Citrus"}], "tips": ["Apply heaviest first, lightest last so the top notes stay bright.", "Wait 30-60 seconds between bottles so they do not wet-mix into mud.", "Start low - you can always add one spray; hard to remove.", "Suggested total around 4 sprays for this combo (adjust for heat and space)."], "total_sprays": 4, "order_names": ["Zenith", "Bahiya Garnet"]}, "score": 188.0, "label": "Strong layer", "verdict": "Categories support each other - worth wearing together.", "why": "**Zenith** reads heavier (base), and **Bahiya Garnet** reads lighter (top) - so the stack has a clear bottom and a bright edge. Sweet/gourmand warmth meets a fresh lift - the fresh side keeps the dessert side from feeling too thick on skin. Shared notes: jasmine, musk, vanilla. Synergy (caramel, tonka, sugar): Zenith has vanilla; Bahiya Garnet has vanilla. What you might smell after layering:. first hit - Coconut, Vanilla, Creamy Accords, Cherry. as it settles - Amber, Fig, Jasmine. dry-down - Vanilla, Musk, Woody Notes, Amber. overall edible-sweet warmth with whatever bright notes ride on top. Together: **Zenith** + **Bahiya Garnet** - use the heavier one as the skin base, then the lighter one on pulse points so both show. Worth a skin test before a full outing - heat and your chemistry will finish the story.", "gender": "Female"}, {"name": "Caramel Coconut night", "bottles": ["Zenith", "Yara Elixir"], "season_label": "Cold / Winter / Cool / Autumn", "season_detail": "Best for Cold / Winter / Cool / Autumn. From bottle seasons: Spring, summer, winter, Fall, Winter, Cool Spring Days.", "bands": ["Cold / Winter", "Cool / Autumn"], "application": {"steps": [{"order": 1, "name": "Yara Elixir", "brand": "Lattafa", "weight": 90, "role": "Heaviest base", "sprays": 2, "where": "Skin first - chest and behind knees (warm spots). Let it settle 30-60 sec.", "cats": "Gourmand, Floral, Sweet, Fruity"}, {"order": 2, "name": "Zenith", "brand": "Riiffs", "weight": 88, "role": "Heaviest base", "sprays": 2, "where": "Skin first - chest and behind knees (warm spots). Let it settle 30-60 sec.", "cats": "Gourmand, Sweet, Powdery, Fruity"}], "tips": ["Apply heaviest first, lightest last so the top notes stay bright.", "Wait 30-60 seconds between bottles so they do not wet-mix into mud.", "Start low - you can always add one spray; hard to remove.", "Suggested total around 4 sprays for this combo (adjust for heat and space)."], "total_sprays": 4, "order_names": ["Yara Elixir", "Zenith"]}, "score": 114.0, "label": "Strong layer", "verdict": "Categories support each other - worth wearing together.", "why": "**Yara Elixir** reads heavier (base), and **Zenith** reads lighter (top) - so the stack has a clear bottom and a bright edge. Sweet/gourmand warmth meets a fresh lift - the fresh side keeps the dessert side from feeling too thick on skin. Shared notes: jasmine, musk, vanilla. Synergy (caramel, tonka, sugar): Zenith has vanilla; Yara Elixir has caramel, vanilla. What you might smell after layering:. first hit - Coconut, Vanilla, Creamy Accords, Strawberry S\'mores. as it settles - Jasmine, Orange Blossom. dry-down - Vanilla, Musk, Woody Notes, Caramel. overall edible-sweet warmth with whatever bright notes ride on top. This leans daytime and warmer weather - lighter trail, easier in close spaces. Together: **Zenith** + **Yara Elixir** - use the heavier one as the skin base, then the lighter one on pulse points so both show. Worth a skin test before a full outing - heat and your chemistry will finish the story.", "gender": "Female"}, {"name": "Soft Accordsbase Fruity", "bottles": ["Zenith", "Panache Angel Dust"], "season_label": "Cool / Autumn / Warm / Mild", "season_detail": "Best for Cool / Autumn / Warm / Mild. From bottle seasons: Spring, summer, winter, Spring-Fall / versatile.", "bands": ["Cool / Autumn", "Warm / Mild"], "application": {"steps": [{"order": 1, "name": "Panache Angel Dust", "brand": "Khadlaj", "weight": 102, "role": "Heaviest base", "sprays": 2, "where": "Skin first - chest and behind knees (warm spots). Let it settle 30-60 sec.", "cats": "Floral, Sweet, Powdery, Gourmand"}, {"order": 2, "name": "Zenith", "brand": "Riiffs", "weight": 88, "role": "Heaviest base", "sprays": 2, "where": "Skin first - chest and behind knees (warm spots). Let it settle 30-60 sec.", "cats": "Gourmand, Sweet, Powdery, Fruity"}], "tips": ["Apply heaviest first, lightest last so the top notes stay bright.", "Wait 30-60 seconds between bottles so they do not wet-mix into mud.", "Start low - you can always add one spray; hard to remove.", "Suggested total around 4 sprays for this combo (adjust for heat and space)."], "total_sprays": 4, "order_names": ["Panache Angel Dust", "Zenith"]}, "score": 176.0, "label": "Strong layer", "verdict": "Categories support each other - worth wearing together.", "why": "**Panache Angel Dust** reads heavier (base), and **Zenith** reads lighter (top) - so the stack has a clear bottom and a bright edge. Sweet/gourmand warmth meets a fresh lift - the fresh side keeps the dessert side from feeling too thick on skin. Shared notes: musk, vanilla. Synergy (caramel, tonka, sugar): Zenith has vanilla; Panache Angel Dust has vanilla. What you might smell after layering:. first hit - Coconut, Vanilla, Creamy Accords, Mandarin. as it settles - rose, jasmine, coconut. dry-down - Vanilla, Musk, Woody Notes, Whipped Cream. overall edible-sweet warmth with whatever bright notes ride on top. Together: **Zenith** + **Panache Angel Dust** - use the heavier one as the skin base, then the lighter one on pulse points so both show. Worth a skin test before a full outing - heat and your chemistry will finish the story.", "gender": "Female"}, {"name": "Gilded Fruity", "bottles": ["Zenith", "Raheeq"], "season_label": "Cold / Winter / Hot / Summer", "season_detail": "Best for Cold / Winter / Hot / Summer. From bottle seasons: Spring, summer, winter, Versatile.", "bands": ["Cold / Winter", "Hot / Summer"], "application": {"steps": [{"order": 1, "name": "Zenith", "brand": "Riiffs", "weight": 88, "role": "Heaviest base", "sprays": 2, "where": "Skin first - chest and behind knees (warm spots). Let it settle 30-60 sec.", "cats": "Gourmand, Sweet, Powdery, Fruity"}, {"order": 2, "name": "Raheeq", "brand": "Nusuk", "weight": 86, "role": "Heaviest base", "sprays": 2, "where": "Skin first - chest and behind knees (warm spots). Let it settle 30-60 sec.", "cats": "Floral, Sweet, Gourmand, Citrus"}], "tips": ["Apply heaviest first, lightest last so the top notes stay bright.", "Wait 30-60 seconds between bottles so they do not wet-mix into mud.", "Start low - you can always add one spray; hard to remove.", "Suggested total around 4 sprays for this combo (adjust for heat and space)."], "total_sprays": 4, "order_names": ["Zenith", "Raheeq"]}, "score": 177.0, "label": "Strong layer", "verdict": "Categories support each other - worth wearing together.", "why": "**Zenith** reads heavier (base), and **Raheeq** reads lighter (top) - so the stack has a clear bottom and a bright edge. Sweet/gourmand warmth meets a fresh lift - the fresh side keeps the dessert side from feeling too thick on skin. Shared notes: coconut, musk, vanilla. Synergy (caramel, tonka, sugar): Zenith has vanilla; Raheeq has caramel, vanilla. What you might smell after layering:. first hit - Coconut, Vanilla, Creamy Accords, Honey. as it settles - jasmine, coconut. dry-down - Vanilla, Musk, Woody Notes, Vanilla Absolute. overall edible-sweet warmth with whatever bright notes ride on top. Together: **Zenith** + **Raheeq** - use the heavier one as the skin base, then the lighter one on pulse points so both show. Worth a skin test before a full outing - heat and your chemistry will finish the story.", "gender": "Female"}, {"name": "Gilded Rose Patchouli", "bottles": ["Zenith", "Nyla"], "season_label": "Hot / Summer / Warm / Mild", "season_detail": "Best for Hot / Summer / Warm / Mild. From bottle seasons: Spring, summer, winter, Spring, Summer.", "bands": ["Hot / Summer", "Warm / Mild"], "application": {"steps": [{"order": 1, "name": "Zenith", "brand": "Riiffs", "weight": 88, "role": "Heaviest base", "sprays": 2, "where": "Skin first - chest and behind knees (warm spots). Let it settle 30-60 sec.", "cats": "Gourmand, Sweet, Powdery, Fruity"}, {"order": 2, "name": "Nyla", "brand": "Arabiyat Prestige", "weight": 46, "role": "Mid layer", "sprays": 2, "where": "Neck and collarbone, or one spray through hair mist-style from a distance.", "cats": "Floral, Fruity, Fresh, Citrus"}], "tips": ["Apply heaviest first, lightest last so the top notes stay bright.", "Wait 30-60 seconds between bottles so they do not wet-mix into mud.", "Start low - you can always add one spray; hard to remove.", "Suggested total around 4 sprays for this combo (adjust for heat and space)."], "total_sprays": 4, "order_names": ["Zenith", "Nyla"]}, "score": 194.0, "label": "Strong layer", "verdict": "Categories support each other - worth wearing together.", "why": "**Zenith** reads heavier (base), and **Nyla** reads lighter (top) - so the stack has a clear bottom and a bright edge. Sweet/gourmand warmth meets a fresh lift - the fresh side keeps the dessert side from feeling too thick on skin. Shared notes: coconut, jasmine, musk. Synergy (vanilla, mango, coconut): Zenith has coconut, vanilla; Nyla has coconut, tiare. What you might smell after layering:. first hit - Coconut, Vanilla, Creamy Accords, Peach. as it settles - Tiare, White Flowers, Jasmine, Rose. dry-down - Vanilla, Musk, Woody Notes, White Musk. overall edible-sweet warmth with whatever bright notes ride on top. Together: **Zenith** + **Nyla** - use the heavier one as the skin base, then the lighter one on pulse points so both show. Worth a skin test before a full outing - heat and your chemistry will finish the story.", "gender": "Female"}, {"name": "Woody Cinnamon bloom", "bottles": ["Elyssia Aura", "Yara Elixir"], "season_label": "Cool / Autumn / Cold / Winter", "season_detail": "Best for Cool / Autumn / Cold / Winter. From bottle seasons: Fall, Winter (versatile to cooler), Fall, Winter, Cool Spring Days.", "bands": ["Cool / Autumn", "Cold / Winter"], "application": {"steps": [{"order": 1, "name": "Elyssia Aura", "brand": "Riiffs", "weight": 96, "role": "Heaviest base", "sprays": 2, "where": "Skin first - chest and behind knees (warm spots). Let it settle 30-60 sec.", "cats": "Gourmand, Spicy, Woody, Boozy"}, {"order": 2, "name": "Yara Elixir", "brand": "Lattafa", "weight": 90, "role": "Heaviest base", "sprays": 2, "where": "Skin first - chest and behind knees (warm spots). Let it settle 30-60 sec.", "cats": "Gourmand, Floral, Sweet, Fruity"}], "tips": ["Apply heaviest first, lightest last so the top notes stay bright.", "Wait 30-60 seconds between bottles so they do not wet-mix into mud.", "Start low - you can always add one spray; hard to remove.", "Suggested total around 4 sprays for this combo (adjust for heat and space)."], "total_sprays": 4, "order_names": ["Elyssia Aura", "Yara Elixir"]}, "score": 194.0, "label": "Strong layer", "verdict": "Categories support each other - worth wearing together.", "why": "**Elyssia Aura** reads heavier (base), and **Yara Elixir** reads lighter (top) - so the stack has a clear bottom and a bright edge. Sweet/gourmand warmth meets a fresh lift - the fresh side keeps the dessert side from feeling too thick on skin. Shared notes: orange, vanilla. Synergy (caramel, tonka, sugar): Elyssia Aura has vanilla; Yara Elixir has caramel, vanilla. What you might smell after layering:. first hit - Cinnamon, Orange, Nutmeg, Strawberry S\'mores. as it settles - Vanilla Cream, Cognac, Cocoa, Jasmine. dry-down - Bourbon Vanilla, Cedarwood, Patchouli, Vanilla. overall edible-sweet warmth with whatever bright notes ride on top. Together: **Elyssia Aura** + **Yara Elixir** - use the heavier one as the skin base, then the lighter one on pulse points so both show. Worth a skin test before a full outing - heat and your chemistry will finish the story.", "gender": "Female"}], "sotd_history": [{"date": "2026-09-02", "scents": ["Vanilla Skin", "Eshal Vanilla"], "scent": "Vanilla Skin + Eshal Vanilla", "notes": "Saved recipe", "is_layering": true}, {"date": "2026-09-01", "scents": ["Zenith", "Yara Elixir"], "scent": "Zenith + Yara Elixir", "notes": "Saved recipe", "is_layering": true}, {"date": "2026-08-31", "scent": "Zenith + Panache Angel Dust", "scents": ["Zenith", "Panache Angel Dust"], "is_layering": true, "notes": "Work", "photo": "data:image/jpeg;base64,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"}, {"date": "2026-08-28", "scent": "Yara Elixir + Elyssia Aura", "scents": ["Yara Elixir", "Elyssia Aura"], "is_layering": true, "notes": "Layered combo"}], "user_reactions": {}}')
SANCTUARY_SEED_DB = list(SEED.get('fragrances_db') or [])


def normalize_gender(g: str) -> str:
    s = (g or "").strip().lower()
    if not s:
        return "Unisex"
    if "female" in s or "women" in s or "feminine" in s:
        return "Female-leaning" if ("lean" in s or "/" in s or "unisex" in s) else "Female"
    if "male" in s or ("men" in s and "women" not in s) or "masculine" in s:
        return "Male-leaning" if ("lean" in s or "/" in s or "unisex" in s) else "Male"
    return "Unisex"


def matches_gender(f: dict, preferred: str) -> bool:
    if not preferred or preferred == "Any":
        return True
    fg = normalize_gender(f.get("gender") or "")
    if preferred == "Female":
        return fg in ("Female", "Female-leaning")
    if preferred == "Male":
        return fg in ("Male", "Male-leaning")
    if preferred == "Unisex":
        return fg in ("Unisex", "Female-leaning", "Male-leaning")
    return True


def matches_weather(f: dict, weather: str) -> bool:
    if not weather or weather == "Any":
        return True
    season = (f.get("season") or "").lower()
    has_summer = "summer" in season
    has_spring = "spring" in season
    has_fall = "fall" in season or "autumn" in season
    has_winter = "winter" in season
    versatile = "versatile" in season or "year" in season
    if weather == "Hot / Summer":
        return has_summer or has_spring or (versatile and not has_winter)
    if weather == "Warm / Mild":
        return has_spring or has_summer or has_fall or versatile
    if weather == "Cool / Autumn":
        return has_fall or has_winter or has_spring or versatile
    if weather == "Cold / Winter":
        return has_winter or has_fall or (versatile and not has_summer)
    return True


def temp_f_to_band(temp_f: float) -> str:
    t = float(temp_f)
    if t >= 88:
        return "Hot / Summer"
    if t >= 72:
        return "Warm / Mild"
    if t >= 55:
        return "Cool / Autumn"
    return "Cold / Winter"


def temp_band_label(temp_f: float) -> str:
    b = temp_f_to_band(temp_f)
    tips = {
        "Hot / Summer": "fresh, citrus, light floral, aquatic",
        "Warm / Mild": "versatile, fruity, soft floral, light sweet",
        "Cool / Autumn": "woody, soft spice, light gourmand, amber",
        "Cold / Winter": "gourmand, vanilla, oriental, heavy sweet",
    }
    return b + " - " + tips.get(b, "")


def default_ca_temp_f() -> int:
    m = pacific_today().month
    table = {1: 58, 2: 62, 3: 68, 4: 75, 5: 84, 6: 93, 7: 98, 8: 97, 9: 91, 10: 79, 11: 66, 12: 56}
    return table.get(m, 80)


def fetch_live_temp_f() -> dict:
    try:
        import urllib.request
        url = (
            "https://api.open-meteo.com/v1/forecast"
            "?latitude=34.5362&longitude=-117.2928"
            "&current=temperature_2m&temperature_unit=fahrenheit&timezone=America%2FLos_Angeles"
        )
        with urllib.request.urlopen(url, timeout=8) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        cur = payload.get("current") or {}
        t = cur.get("temperature_2m")
        if t is None:
            return {"ok": False, "detail": "No temp"}
        return {"ok": True, "temp_f": float(t), "source": "Open-Meteo", "observed": str(cur.get("time") or "")}
    except Exception as e:
        return {"ok": False, "detail": str(e)}


def frag_weight(f: dict) -> int:
    cats = set(c.lower() for c in (f.get("category") or []))
    notes = (f.get("notes") or "").lower()
    w = 50
    for c in ("gourmand", "oriental", "oud", "woody", "vanilla", "amber", "spicy"):
        if c in cats:
            w += 8
    for c in ("fresh", "citrus", "aquatic", "green"):
        if c in cats:
            w -= 8
    for k in ("vanilla", "amber", "oud", "caramel", "chocolate", "coffee", "tonka"):
        if k in notes:
            w += 3
    for k in ("citrus", "bergamot", "lemon", "aquatic", "mint"):
        if k in notes:
            w -= 3
    return max(10, min(99, w))


def order_heavy_to_light(frags: list) -> list:
    return sorted(frags, key=lambda f: (-frag_weight(f), (f.get("name") or "").lower()))


def resolve_by_name(name: str):
    name = (name or "").strip()
    for f in st.session_state.get("fragrances_db") or []:
        if (f.get("name") or "").strip() == name:
            return f
    return None


def score_fragrance(f, gender, weather, categories, occasion, temp_f=None) -> float:
    if st.session_state.get("user_reactions", {}).get(f.get("name")) == "dislike":
        return -999
    s = 10.0
    if not matches_gender(f, gender):
        return -100
    band = weather
    if temp_f is not None and (not band or band == "Any"):
        band = temp_f_to_band(float(temp_f))
    if band and band != "Any":
        s += 20 if matches_weather(f, band) else -15
    cats = set(f.get("category") or [])
    if categories and categories != "Any":
        want = set(categories) if isinstance(categories, (list, tuple, set)) else {categories}
        s += 15 if (cats & want) else -5
    if st.session_state.get("user_reactions", {}).get(f.get("name")) == "fav":
        s += 18
    if occasion == "Date / Evening" and cats & {"Oriental", "Gourmand", "Sweet", "Vanilla"}:
        s += 6
    if occasion == "Work / Office" and cats & {"Fresh", "Citrus", "Woody", "Musky"}:
        s += 6
    if occasion == "Outdoor / Sporty" and cats & {"Fresh", "Citrus", "Aquatic"}:
        s += 6
    return s


def get_top_fragrances(
    gender="Any", weather="Any", category="Any", occasion="Any", top_n=3,
    favorites_only=False, temp_f=None, shuffle=False, exclude_names=None, concentration="Any",
) -> list:
    exclude = set(exclude_names or [])
    scored = []
    for f in st.session_state.get("fragrances_db") or []:
        name = f.get("name") or ""
        if not name or name in exclude:
            continue
        if favorites_only and st.session_state.get("user_reactions", {}).get(name) != "fav":
            continue
        if concentration and concentration != "Any":
            if concentration.lower() not in (f.get("concentration") or "").lower():
                continue
        sc = score_fragrance(f, gender, weather, category, occasion, temp_f=temp_f)
        if sc <= -50:
            continue
        if shuffle:
            sc += random.random() * 4
        scored.append((sc, f))
    scored.sort(key=lambda x: (-x[0], (x[1].get("name") or "").lower()))
    out, brands = [], set()
    for sc, f in scored:
        b = (f.get("brand") or "").lower()
        if b and b in brands and len(out) < top_n:
            continue
        if b:
            brands.add(b)
        out.append(f)
        if len(out) >= top_n:
            break
    if len(out) < top_n:
        for sc, f in scored:
            if f not in out:
                out.append(f)
            if len(out) >= top_n:
                break
    return out


def top_picks_for_season(season_key: str, gender="Any", top_n=5) -> list:
    band_map = {"spring": "Warm / Mild", "summer": "Hot / Summer", "fall": "Cool / Autumn", "autumn": "Cool / Autumn", "winter": "Cold / Winter"}
    key = (season_key or "").lower()
    band = band_map.get(key, "Any")
    scored = []
    for f in st.session_state.get("fragrances_db") or []:
        if st.session_state.get("user_reactions", {}).get(f.get("name")) == "dislike":
            continue
        if not matches_gender(f, gender):
            continue
        s = (f.get("season") or "").lower()
        tag = (
            (key == "spring" and "spring" in s)
            or (key == "summer" and "summer" in s)
            or (key in ("fall", "autumn") and ("fall" in s or "autumn" in s))
            or (key == "winter" and "winter" in s)
        )
        weather_ok = matches_weather(f, band)
        if not (tag or weather_ok):
            continue
        pts = 10 + (25 if tag else 0) + (10 if weather_ok else 0)
        pts += score_fragrance(f, gender, band, "Any", "Any")
        if st.session_state.get("user_reactions", {}).get(f.get("name")) == "fav":
            pts += 12
        scored.append((pts, f))
    scored.sort(key=lambda x: (-x[0], (x[1].get("name") or "").lower()))
    out, brands = [], set()
    for pts, f in scored:
        b = (f.get("brand") or "").lower()
        if b and b in brands and len(out) < top_n:
            continue
        if b:
            brands.add(b)
        out.append(f)
        if len(out) >= top_n:
            break
    return out


def shared_notes(a, b) -> list:
    def toks(f):
        raw = re.split(r"[,/;]+", (f.get("notes") or "").lower())
        out = set()
        for t in raw:
            t = re.sub(r"[^a-z0-9\s]", "", t).strip()
            for w in t.split():
                if len(w) > 3:
                    out.add(w)
        return out
    return sorted(toks(a) & toks(b))[:8]


def layer_score(a, b) -> float:
    if not a or not b:
        return 0
    s = 40.0
    ca, cb = set(a.get("category") or []), set(b.get("category") or [])
    if ca & cb:
        s += 12
    if (ca & {"Gourmand", "Sweet", "Vanilla"}) and (cb & {"Fresh", "Citrus", "Woody", "Floral"}):
        s += 10
    if (cb & {"Gourmand", "Sweet", "Vanilla"}) and (ca & {"Fresh", "Citrus", "Woody", "Floral"}):
        s += 10
    s += min(15, len(shared_notes(a, b)) * 3)
    s += max(0, 12 - abs(frag_weight(a) - frag_weight(b)) * 0.15)
    return max(0, min(100, s))


def explain_layer(frags) -> str:
    if len(frags) < 2:
        return "Pick at least two bottles."
    ordered = order_heavy_to_light(frags)
    names = [f.get("name") for f in ordered]
    sn = shared_notes(ordered[0], ordered[-1])
    bits = [f"{names[0]} is the heavier base; {names[-1]} is lighter on top."]
    if sn:
        bits.append("Shared: " + ", ".join(sn[:5]) + ".")
    cats = []
    for f in ordered:
        cats.extend((f.get("category") or [])[:2])
    if cats:
        bits.append("Families: " + ", ".join(dict.fromkeys(cats)) + ".")
    bits.append("Spray order: " + " > ".join(names) + ".")
    return " ".join(bits)


def evaluate_layer(names: list) -> dict:
    frags = [resolve_by_name(n) for n in names]
    frags = [f for f in frags if f]
    if len(frags) < 2:
        return {"ok": False, "label": "Need 2+ bottles", "score": 0, "why": "Select at least two.",
                "frags": frags, "selected_names": list(names), "spray_order": [f.get("name") for f in frags]}
    ordered = order_heavy_to_light(frags)
    scores = []
    for i in range(len(frags)):
        for j in range(i + 1, len(frags)):
            scores.append(layer_score(frags[i], frags[j]))
    sc = int(round(sum(scores) / max(1, len(scores))))
    label = "Excellent layer" if sc >= 75 else "Strong layer" if sc >= 60 else "Good layer" if sc >= 45 else "Okay layer"
    return {
        "ok": True, "label": label, "score": sc, "why": explain_layer(frags),
        "frags": frags, "selected_names": list(names),
        "spray_order": [f.get("name") for f in ordered],
        "application": {"order_names": [f.get("name") for f in ordered],
                        "tips": ["Heaviest first, lightest last.", "Wait 30-60 sec between sprays.", "Start light."]},
    }


def suggest_partners(base, num=8, gender="Any", season="Any") -> list:
    if not base:
        return []
    base_name = base.get("name")
    out = []
    for f in st.session_state.get("fragrances_db") or []:
        if f.get("name") == base_name:
            continue
        if st.session_state.get("user_reactions", {}).get(f.get("name")) == "dislike":
            continue
        if gender != "Any" and not matches_gender(f, gender):
            continue
        if season != "Any" and not matches_weather(f, season):
            continue
        sc = layer_score(base, f)
        reason = "Shared families" if set(base.get("category") or []) & set(f.get("category") or []) else "Complement"
        out.append((sc, f, reason))
    out.sort(key=lambda x: (-x[0], (x[1].get("name") or "").lower()))
    final, brands = [], set()
    for sc, f, reason in out:
        b = (f.get("brand") or "").lower()
        if b and b in brands and len(final) < num:
            continue
        if b:
            brands.add(b)
        final.append((f, reason, sc))
        if len(final) >= num:
            break
    return final


def suggest_seasons_from_notes(notes: str, categories=None) -> list:
    text = (notes or "").lower()
    cats = set(categories or [])
    scores = {"Spring": 0, "Summer": 0, "Fall": 0, "Winter": 0}
    for c in cats:
        cl = c.lower()
        if cl in ("fresh", "citrus", "aquatic", "green", "fruity"):
            scores["Spring"] += 2; scores["Summer"] += 3
        if cl in ("floral", "powdery"):
            scores["Spring"] += 2
        if cl in ("gourmand", "sweet", "vanilla", "creamy", "spicy"):
            scores["Fall"] += 2; scores["Winter"] += 2
        if cl in ("oriental", "oud", "woody", "amber", "smoky"):
            scores["Fall"] += 2; scores["Winter"] += 3
    for k in ("citrus", "bergamot", "coconut", "pineapple", "mint"):
        if k in text: scores["Summer"] += 2
    for k in ("rose", "jasmine", "peach", "pear"):
        if k in text: scores["Spring"] += 2
    for k in ("cinnamon", "cedar", "spice"):
        if k in text: scores["Fall"] += 2
    for k in ("vanilla", "amber", "oud", "caramel", "chocolate", "coffee", "tonka"):
        if k in text: scores["Winter"] += 2; scores["Fall"] += 1
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    if not ranked or ranked[0][1] <= 0:
        return ["Versatile"]
    top = ranked[0][1]
    chosen = [s for s, v in ranked if v >= max(1, top - 1) and v > 0]
    if set(chosen) == {"Spring", "Summer"}: return ["Spring, Summer"]
    if set(chosen) == {"Fall", "Winter"}: return ["Fall, Winter"]
    if len(chosen) == 1: return chosen
    return [", ".join(chosen[:2])]


def recipe_gender_from_frags(frags) -> str:
    counts = {"Female": 0, "Male": 0, "Unisex": 0}
    for f in frags:
        g = normalize_gender(f.get("gender") or "")
        if g in ("Female", "Female-leaning"): counts["Female"] += 2 if g == "Female" else 1
        elif g in ("Male", "Male-leaning"): counts["Male"] += 2 if g == "Male" else 1
        else: counts["Unisex"] += 1
    if counts["Female"] == 0 and counts["Male"] == 0:
        return "Unisex" if counts["Unisex"] else "Any"
    if counts["Female"] > counts["Male"]: return "Female"
    if counts["Male"] > counts["Female"]: return "Male"
    return "Unisex"


def suggest_recipe_name(names) -> str:
    words = ["Velvet", "Gilded", "Soft", "Night", "Bloom", "Ember", "Silk", "Amber"]
    notes = []
    for n in names:
        f = resolve_by_name(n)
        if f:
            notes.extend((f.get("category") or [])[:1])
    random.shuffle(words)
    return words[0] + " " + (notes[0] if notes else "Layer")


def log_sotd(names, notes=""):
    entry = {"date": pacific_today().isoformat(), "bottles": list(names), "notes": notes or "", "when": pacific_now_iso()}
    hist = list(st.session_state.get("sotd_history") or [])
    hist.insert(0, entry)
    st.session_state["sotd_history"] = hist[:200]
    mark_dirty(); save_persisted()


def log_vault(action, name, detail=""):
    log = list(st.session_state.get("vault_log") or [])
    log.insert(0, {"when": pacific_today().isoformat(), "action": action, "name": name, "detail": detail})
    st.session_state["vault_log"] = log[:50]
    mark_dirty()


st.set_page_config(page_title="ScentedDeadGirl Fragrance Sanctuary", page_icon="SDG", layout="centered", initial_sidebar_state="expanded")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;600;700&family=Inter:wght@300;400;500;600;700&display=swap');
html, body, .stApp { font-family: 'Inter', system-ui, sans-serif !important; }
.stApp { background: radial-gradient(ellipse at top, #0a1224 0%, #04070f 45%, #010205 100%); color: #c5d0e4; }
.block-container { padding-top: 1.2rem !important; max-width: 820px !important; }
h1, h2, h3 { color: #6ea4ff !important; font-family: 'Cinzel', Georgia, serif !important; }
section[data-testid="stSidebar"] { background: linear-gradient(180deg, #040810 0%, #070c16 100%) !important; border-right: 1px solid #1a2740; }
.stButton > button { background: linear-gradient(180deg, #121c30 0%, #0a1220 100%) !important; color: #6ea4ff !important; border: 1px solid #1a2740 !important; border-radius: 6px !important; font-weight: 600 !important; }
.stButton > button[kind="primary"] { background: linear-gradient(180deg, #1a3060 0%, #122448 100%) !important; color: #e0ecff !important; }
.stTabs [aria-selected="true"] { color: #6ea4ff !important; border-bottom: 2px solid #3d6cb0 !important; }
[data-testid="stExpander"] summary { color: #6ea4ff !important; background: #0c1422 !important; border: 1px solid #1a2740 !important; border-radius: 6px !important; }
</style>
""", unsafe_allow_html=True)

_persisted = load_persisted()
if "_fp_start" not in st.session_state:
    st.session_state["_fp_start"] = ""

if "fragrances_db" not in st.session_state:
    disk = list(_persisted.get("fragrances_db") or [])
    if len(disk) >= 50:
        st.session_state["fragrances_db"] = disk
    else:
        st.session_state["fragrances_db"] = list(SANCTUARY_SEED_DB)
        try: save_persisted(force=True)
        except Exception: pass
elif len(st.session_state.get("fragrances_db") or []) < 20:
    disk = list(_persisted.get("fragrances_db") or [])
    st.session_state["fragrances_db"] = disk if len(disk) >= 20 else list(SANCTUARY_SEED_DB)

for key, default in (
    ("user_reactions", dict(_persisted.get("user_reactions") or SEED.get("user_reactions") or {})),
    ("sotd_history", list(_persisted.get("sotd_history") or SEED.get("sotd_history") or [])),
    ("layer_recipes", list(_persisted.get("layer_recipes") or SEED.get("layer_recipes") or [])),
    ("wishlist", list(_persisted.get("wishlist") or SEED.get("wishlist") or [])),
    ("vault_log", list(_persisted.get("vault_log") or [])),
):
    if key not in st.session_state:
        st.session_state[key] = default
    elif key in ("layer_recipes", "wishlist", "sotd_history"):
        disk_v = list(_persisted.get(key) or [])
        if len(disk_v) > len(st.session_state.get(key) or []):
            st.session_state[key] = disk_v

st.title("ScentedDeadGirl")
st.caption("Fragrance Sanctuary — recommend, layer, log, curate.")

n_bot = len(st.session_state.get("fragrances_db") or [])
db = st.session_state.get("fragrances_db") or []
name_list = sorted((f.get("name") or "") for f in db if f.get("name"))
_saved = st.session_state.get("last_saved_at") or _persisted.get("last_saved_at") or "-"
st.sidebar.caption(f"Vault last saved: {_saved} | **{n_bot}** bottles")
st.sidebar.caption("Cloud redeploys wipe server data. Export JSON from Vault after big changes.")

ca_default = int(default_ca_temp_f())
if "temp_f" not in st.session_state:
    st.session_state["temp_f"] = ca_default

if st.session_state.pop("_clear_filters", False):
    st.session_state["filter_gender"] = "Any"
    st.session_state["filter_categories"] = []
    st.session_state["filter_occasion"] = "Any"
    st.session_state["filter_num_recs"] = 3
    st.session_state["filter_favorites_only"] = False
    st.session_state.pop("last_recs", None)

generate_clicked = False
regenerate_clicked = False

with st.sidebar.expander("Recommend", expanded=True):
    st.caption("Season from outdoor temp (Victorville). Use live temp, then Generate.")
    if st.session_state.pop("_apply_live_temp", False):
        live = st.session_state.get("live_temp_meta") or {}
        if live.get("ok") and live.get("temp_f") is not None:
            st.session_state["temp_f"] = int(round(float(live["temp_f"])))
    gender = st.selectbox("Gender", ["Any", "Female", "Male", "Unisex"], key="filter_gender")
    num_recs = st.radio("How many", [1, 3, 5], index=1, horizontal=True, key="filter_num_recs")
    st.markdown("**Temperature (drives season)**")
    c1, c2 = st.columns([2, 1])
    with c1:
        temp_f = st.slider("Outdoor temp (F)", 30, 115, key="temp_f")
    with c2:
        st.write(""); st.write("")
        if st.button("Use live temp", use_container_width=True, key="live_temp_btn"):
            result = fetch_live_temp_f()
            st.session_state["live_temp_meta"] = result
            if result.get("ok"):
                st.session_state["_apply_live_temp"] = True
                st.rerun()
            else:
                st.warning("Live temp unavailable — using slider.")
    live_meta = st.session_state.get("live_temp_meta") or {}
    live_bit = f" | Live: {live_meta.get('temp_f')} F" if live_meta.get("ok") else ""
    st.caption(f"{int(temp_f)} F > **{temp_band_label(float(temp_f))}** | Norm ~{ca_default} F{live_bit}")
    categories = st.multiselect("Categories", CAT_OPTIONS, key="filter_categories", placeholder="Any if empty")
    occasion = st.selectbox("Occasion", ["Any", "Daily / Casual", "Work / Office", "Date / Evening", "Formal / Event", "Outdoor / Sporty"], key="filter_occasion")
    favorites_only = st.checkbox("YAY only", key="filter_favorites_only")
    generate_clicked = st.button("Generate", type="primary", use_container_width=True, key="gen_btn")
    regenerate_clicked = st.button("Refresh picks", use_container_width=True, key="regen_btn")
    if st.button("Clear", use_container_width=True, key="clear_btn"):
        st.session_state["_clear_filters"] = True
        st.rerun()

with st.sidebar.expander("Add fragrance", expanded=False):
    with st.form("add_frag_form"):
        an = st.text_input("Name")
        ab = st.text_input("Brand")
        ag = st.selectbox("Gender", ["Female", "Male", "Unisex", "Female-leaning", "Male-leaning"])
        aseason = st.selectbox("Season", SEASON_CHOICES)
        acats = st.multiselect("Categories", CAT_OPTIONS)
        anotes = st.text_area("Notes")
        aconc = st.selectbox("Format", CONCENTRATION_OPTIONS)
        if st.form_submit_button("Add to vault") and an.strip():
            st.session_state["fragrances_db"].append({
                "name": an.strip(), "brand": ab.strip(), "gender": ag, "season": aseason,
                "notes": anotes.strip(), "category": acats, "dupe_of": "", "shelf_status": "Own",
                "size_ml": None, "concentration": aconc,
            })
            log_vault("added", an.strip(), ab.strip())
            mark_dirty(); save_persisted(); st.success("Added **" + an.strip() + "**"); st.rerun()

tab_discover, tab_layer, tab_sotd, tab_collection, tab_vault = st.tabs(["Discover", "Layer", "SOTD", "Collection", "Vault"])

with tab_discover:
    st.caption("Recommendations from the sidebar, plus seasonal top picks.")
    with st.expander("Top 5 by season", expanded=True):
        seasons = [("Spring", "spring"), ("Summer", "summer"), ("Fall / Autumn", "fall"), ("Winter", "winter")]
        labels = [s[0] for s in seasons]
        keymap = {s[0]: s[1] for s in seasons}
        if st.session_state.pop("_clear_top_season", False):
            st.session_state.pop("_top_season_results", None)
            st.session_state["top_season_search"] = ""
        gcol, scol = st.columns(2)
        with gcol:
            ts_gender = st.selectbox("Gender", ["Any", "Female", "Male", "Unisex"], key="top_season_gender")
        with scol:
            ts_season = st.selectbox("Season", ["All seasons"] + labels, key="top_season_pick")
        ts_search = st.text_input("Search in results", key="top_season_search", placeholder="Name or brand...")
        b1, b2, b3 = st.columns(3)
        with b1:
            show_top = st.button("Show top 5", type="primary", use_container_width=True, key="top_go")
        with b2:
            refresh_top = st.button("Refresh", use_container_width=True, key="top_refresh")
        with b3:
            if st.button("Clear", use_container_width=True, key="top_clear"):
                st.session_state["_clear_top_season"] = True
                st.rerun()
        if show_top or refresh_top:
            targets = seasons if ts_season == "All seasons" else [(ts_season, keymap[ts_season])]
            results = {}
            for label, key in targets:
                picks = top_picks_for_season(key, gender=ts_gender, top_n=12 if refresh_top else 5)
                if refresh_top and picks:
                    random.shuffle(picks)
                results[label] = picks[:5]
            st.session_state["_top_season_results"] = results
            st.session_state["_top_season_meta"] = {"gender": ts_gender, "season": ts_season}
        results = st.session_state.get("_top_season_results")
        if results:
            meta = st.session_state.get("_top_season_meta") or {}
            st.caption(f"Gender: **{meta.get('gender')}** | Season: **{meta.get('season')}**")
            q = (ts_search or "").strip().lower()
            for label in labels:
                if label not in results:
                    continue
                picks = results[label]
                if q:
                    picks = [f for f in picks if q in (f.get("name") or "").lower() or q in (f.get("brand") or "").lower()]
                st.markdown("### " + label)
                if not picks:
                    st.caption("No matches.")
                for i, f in enumerate(picks, 1):
                    cats = ", ".join((f.get("category") or [])[:4])
                    st.markdown(f"**{i}. {clean_text(f.get('name'))}** - *{clean_text(f.get('brand'))}*  \n{f.get('gender','?')} | {f.get('season','?')} | {cats}")
                    if f.get("notes"):
                        st.caption(clean_text(f.get("notes"))[:140])
                    x1, x2 = st.columns(2)
                    with x1:
                        if st.button("Log SOTD", key=f"ts_sotd_{label}_{i}"):
                            log_sotd([f.get("name")], notes="Top 5 " + label); st.rerun()
                    with x2:
                        if st.button("To Layer", key=f"ts_layer_{label}_{i}"):
                            st.session_state["layer_base"] = f.get("name")
                            st.session_state["_layer_flash"] = "Base set to **" + str(f.get("name")) + "**"
                            st.rerun()
                st.markdown("---")

    if generate_clicked or regenerate_clicked:
        gender = st.session_state.get("filter_gender", "Any")
        cats = st.session_state.get("filter_categories") or []
        category = cats if cats else "Any"
        occasion = st.session_state.get("filter_occasion", "Any")
        num_recs = int(st.session_state.get("filter_num_recs", 3))
        favorites_only = bool(st.session_state.get("filter_favorites_only", False))
        rec_temp = None
        try:
            rec_temp = float(st.session_state.get("temp_f"))
        except Exception:
            pass
        weather = temp_f_to_band(rec_temp) if rec_temp is not None else "Any"
        prev = st.session_state.get("last_recs") or {}
        prev_names = [f.get("name") for f in (prev.get("selected") or []) if isinstance(f, dict)]
        selected = get_top_fragrances(
            gender=gender, weather=weather, category=category, occasion=occasion,
            top_n=num_recs, favorites_only=favorites_only, temp_f=rec_temp, shuffle=True,
            exclude_names=prev_names if regenerate_clicked else None,
        )
        st.session_state["last_recs"] = {
            "selected": selected, "num": num_recs,
            "meta": {"gender": gender, "weather": weather, "temp_f": rec_temp, "occasion": occasion},
        }

    last_recs = st.session_state.get("last_recs")
    if last_recs and (last_recs.get("selected") or []):
        selected = last_recs["selected"]
        meta = last_recs.get("meta") or {}
        st.subheader(f"Top {last_recs.get('num', len(selected))}")
        if meta.get("temp_f") is not None:
            st.caption(f"Based on **{float(meta['temp_f']):.0f} F** > **{meta.get('weather')}** | {meta.get('gender')}")
        for i, f in enumerate(selected, 1):
            cats = ", ".join((f.get("category") or [])[:4])
            st.markdown(f"**{i}. {clean_text(f.get('name'))}** - *{clean_text(f.get('brand'))}*  \n{f.get('gender','?')} | {f.get('season','?')} | {cats}")
            if f.get("notes"):
                st.caption(clean_text(f.get("notes"))[:160])
            r1, r2, r3, r4 = st.columns(4)
            with r1:
                if st.button("YAY", key=f"yay_{i}"):
                    st.session_state.setdefault("user_reactions", {})[f.get("name")] = "fav"
                    mark_dirty(); save_persisted(); st.rerun()
            with r2:
                if st.button("DEL", key=f"del_{i}"):
                    st.session_state.setdefault("user_reactions", {})[f.get("name")] = "dislike"
                    mark_dirty(); save_persisted(); st.rerun()
            with r3:
                if st.button("SOTD", key=f"sotd_{i}"):
                    log_sotd([f.get("name")]); st.rerun()
            with r4:
                if st.button("Layer", key=f"ly_{i}"):
                    st.session_state["layer_base"] = f.get("name")
                    st.session_state["_layer_flash"] = "Base set to **" + str(f.get("name")) + "**"
                    st.rerun()

with tab_layer:
    st.subheader("Layering Studio")
    flash = st.session_state.pop("_layer_flash", None)
    if flash:
        st.success(flash)
    with st.expander("Base + partners", expanded=True):
        lg, ls = st.columns(2)
        with lg:
            layer_gender = st.selectbox("Partner gender", ["Any", "Female", "Male", "Unisex"], key="layer_gender")
        with ls:
            layer_season = st.selectbox("Partner season", ["Any", "Hot / Summer", "Warm / Mild", "Cool / Autumn", "Cold / Winter"], key="layer_season")
        base_default = st.session_state.get("layer_base") or ""
        opts = ["- select -"] + name_list
        try:
            bidx = opts.index(base_default) if base_default in opts else 0
        except Exception:
            bidx = 0
        base_name = st.selectbox("Base bottle", opts, index=min(bidx, len(opts) - 1), key="layer_base_select")
        if base_name and base_name != "- select -":
            st.session_state["layer_base"] = base_name
            base_f = resolve_by_name(base_name)
            if base_f:
                st.caption(f"{base_f.get('brand')} | {base_f.get('gender')} | {base_f.get('season')}")
                partners = suggest_partners(base_f, num=6, gender=layer_gender, season=layer_season)
                if not partners:
                    st.info("No partners matched these filters.")
                for pi, (pf, reason, sc) in enumerate(partners, 1):
                    st.markdown(
                        f"**{pi}. {pf.get('name')}** ({pf.get('brand')})  \n"
                        f"{int(sc)}/100 | {reason}  \n"
                        f"{pf.get('gender')} | {pf.get('season')} | {', '.join((pf.get('category') or [])[:3])}"
                    )
                    if st.button("Layer check", key=f"pc_{pi}"):
                        pair = [base_name, pf.get("name")]
                        st.session_state["_pending_layer"] = pair
                        st.session_state["last_layer_check"] = evaluate_layer(pair)
                        st.rerun()

    st.markdown("### Layer check")
    if st.session_state.get("_pending_layer"):
        st.session_state["layer_pick"] = list(st.session_state.pop("_pending_layer"))
    current = list(st.session_state.get("layer_pick") or [])
    options = sorted(set(name_list) | set(current))
    layer_pick = st.multiselect("Bottles to layer", options, key="layer_pick")
    c1, c2 = st.columns(2)
    with c1:
        run = st.button("Check layer", type="primary", use_container_width=True, key="check_layer")
    with c2:
        if st.button("Clear picks", use_container_width=True, key="clear_layer"):
            st.session_state["layer_pick"] = []
            st.session_state.pop("last_layer_check", None)
            st.rerun()
    if run:
        if len(layer_pick) < 2:
            st.warning("Pick at least two bottles.")
        else:
            st.session_state["last_layer_check"] = evaluate_layer(list(layer_pick))
    ev = st.session_state.get("last_layer_check")
    if ev:
        st.success(f"**{ev.get('label')}** - {ev.get('score')}/100")
        checked = ev.get("selected_names") or []
        spray = ev.get("spray_order") or []
        st.markdown("**You checked:** " + clean_text(" + ".join(checked)))
        st.markdown("**Spray order:** " + clean_text(" > ".join(spray)))
        st.caption(clean_text(ev.get("why") or ""))
        save_name = st.text_input("Save as recipe name", value=suggest_recipe_name(checked), key="recipe_name")
        rg = recipe_gender_from_frags(ev.get("frags") or [])
        st.caption(f"Auto gender: **{rg}**")
        if st.button("Save recipe", type="primary", key="save_recipe"):
            rec = {"name": (save_name or "Untitled").strip(), "bottles": list(checked), "gender": rg,
                   "score": ev.get("score"), "label": ev.get("label"), "why": ev.get("why"),
                   "application": ev.get("application") or {}}
            st.session_state.setdefault("layer_recipes", []).insert(0, rec)
            mark_dirty(); save_persisted(); st.success("Saved **" + rec["name"] + "**"); st.rerun()
        if st.button("Log this layer as SOTD", key="layer_sotd"):
            log_sotd(list(checked), notes="Layer"); st.rerun()

    with st.expander("Saved recipes", expanded=False):
        recipes = st.session_state.get("layer_recipes") or []
        st.caption(str(len(recipes)) + " recipe(s)")
        for i, r in enumerate(recipes[:30]):
            st.markdown(f"**{r.get('name')}** — {' + '.join(r.get('bottles') or [])}")
            st.caption(f"{r.get('gender','?')} | {r.get('label','')} | score {r.get('score','-')}")
            if st.button("Delete", key=f"del_rec_{i}"):
                st.session_state["layer_recipes"].pop(i)
                mark_dirty(); save_persisted(); st.rerun()

with tab_sotd:
    st.subheader("Scent of the Day")
    hist = st.session_state.get("sotd_history") or []
    with st.form("sotd_form"):
        picks = st.multiselect("Bottles worn", name_list if name_list else ["(empty vault)"])
        note = st.text_input("Notes")
        if st.form_submit_button("Log SOTD") and picks:
            log_sotd(picks, notes=note); st.success("Logged."); st.rerun()
    st.markdown("### History")
    if not hist:
        st.caption("No entries yet.")
    for i, e in enumerate(hist[:40]):
        st.markdown(f"**{e.get('date','?')}** — {' + '.join(e.get('bottles') or [])}")
        if e.get("notes"):
            st.caption(e.get("notes"))
        if st.button("Delete entry", key=f"sotd_del_{i}"):
            st.session_state["sotd_history"].pop(i)
            mark_dirty(); save_persisted(); st.rerun()

with tab_collection:
    st.subheader("Collection")
    st.caption(f"{n_bot} bottles in vault")
    q = st.text_input("Search collection", placeholder="Name, brand, notes...")
    season_filter = st.selectbox("Browse by season tag", ["All", "Spring", "Summer", "Fall", "Winter", "Versatile"], key="coll_season")
    shown = 0
    for f in sorted(db, key=lambda x: (x.get("name") or "").lower()):
        blob = f"{f.get('name')} {f.get('brand')} {f.get('notes')} {f.get('season')}".lower()
        if q and q.lower() not in blob:
            continue
        if season_filter != "All" and season_filter.lower() not in (f.get("season") or "").lower():
            continue
        shown += 1
        if shown > 80:
            st.caption("Showing first 80 — refine search.")
            break
        cats = ", ".join((f.get("category") or [])[:5])
        st.markdown(
            f"**{clean_text(f.get('name'))}** - *{clean_text(f.get('brand'))}*  \n"
            f"{f.get('gender')} | {f.get('season')} | {f.get('concentration') or 'EDP'} | {cats}"
        )
    st.markdown("### Wishlist")
    with st.form("wish_form"):
        wn = st.text_input("Name")
        wb = st.text_input("Brand")
        if st.form_submit_button("Add to wishlist") and wn.strip():
            st.session_state.setdefault("wishlist", []).insert(0, {
                "name": wn.strip(), "brand": wb.strip(), "notes": "", "checked": False,
                "gender": "Unisex", "season": "Versatile",
            })
            mark_dirty(); save_persisted(); st.rerun()
    for i, w in enumerate(st.session_state.get("wishlist") or []):
        st.write(f"- {w.get('name')} ({w.get('brand')})")
        if st.button("Remove", key=f"wish_rm_{i}"):
            st.session_state["wishlist"].pop(i)
            mark_dirty(); save_persisted(); st.rerun()

with tab_vault:
    st.subheader("Vault")
    st.caption(f"{n_bot} bottles | export often")
    with st.expander("Edit bottle", expanded=False):
        en = st.selectbox("Select", ["-"] + name_list, key="edit_sel")
        if en and en != "-":
            frag = resolve_by_name(en)
            if frag:
                idx = next(i for i, f in enumerate(st.session_state["fragrances_db"]) if f.get("name") == en)
                gopts = ["Female", "Male", "Unisex", "Female-leaning", "Male-leaning"]
                with st.form("edit_form"):
                    nn = st.text_input("Name", value=frag.get("name") or "")
                    nb = st.text_input("Brand", value=frag.get("brand") or "")
                    gi = gopts.index(frag.get("gender")) if frag.get("gender") in gopts else 2
                    ng = st.selectbox("Gender", gopts, index=gi)
                    ns = st.text_input("Season", value=frag.get("season") or "")
                    nc = st.multiselect("Categories", CAT_OPTIONS, default=[c for c in (frag.get("category") or []) if c in CAT_OPTIONS])
                    nnotes = st.text_area("Notes", value=frag.get("notes") or "")
                    ci = CONCENTRATION_OPTIONS.index(frag.get("concentration")) if frag.get("concentration") in CONCENTRATION_OPTIONS else 0
                    nconc = st.selectbox("Format", CONCENTRATION_OPTIONS, index=ci)
                    if st.form_submit_button("Save changes"):
                        st.session_state["fragrances_db"][idx] = {
                            **frag, "name": nn.strip(), "brand": nb.strip(), "gender": ng,
                            "season": ns.strip(), "category": nc, "notes": nnotes, "concentration": nconc,
                        }
                        log_vault("edited", nn.strip(), nb.strip())
                        mark_dirty(); save_persisted(); st.success("Saved"); st.rerun()

    with st.expander("Season helper", expanded=True):
        st.caption("Fix empty / Versatile / vague season tags.")
        def _weak(s):
            s = (s or "").strip().lower()
            return (not s) or s in ("versatile", "any", "n/a", "na", "none", "?") or len(s) < 3
        weak = []
        for i, f in enumerate(st.session_state.get("fragrances_db") or []):
            if _weak(f.get("season")):
                sug = suggest_seasons_from_notes(f.get("notes") or "", f.get("category") or [])
                weak.append({"idx": i, "name": f.get("name"), "brand": f.get("brand"),
                             "current": f.get("season") or "none", "suggested": sug[0] if sug else "Versatile"})
        st.write(f"**{len(weak)}** bottle(s) need a clearer season.")
        mode = st.radio("Mode", ["Pick one bottle", "Fix all weak"], horizontal=True, key="sh_mode")
        if mode == "Pick one bottle":
            bottle = st.selectbox("Bottle", ["-"] + name_list, key="sh_bottle")
            if bottle != "-":
                frag = resolve_by_name(bottle)
                sug = suggest_seasons_from_notes(frag.get("notes") or "", frag.get("category") or [])
                pick = sug[0] if sug else "Versatile"
                st.info(f"Current: **{frag.get('season')}** | Suggested: **{pick}**")
                new_s = st.selectbox("Save as", [pick] + [x for x in SEASON_CHOICES if x != pick], key="sh_set")
                if st.button("Save season", type="primary", key="sh_save"):
                    for i, f in enumerate(st.session_state["fragrances_db"]):
                        if f.get("name") == bottle:
                            st.session_state["fragrances_db"][i]["season"] = new_s
                            break
                    log_vault("edited", bottle, "season-helper")
                    mark_dirty(); save_persisted(); st.success("Saved"); st.rerun()
        else:
            for item in weak[:25]:
                st.markdown(f"**{item['name']}** (*{item['brand']}*) — {item['current']} > **{item['suggested']}**")
            if weak and st.button(f"Apply all suggested ({len(weak)})", type="primary", key="sh_all"):
                for item in weak:
                    st.session_state["fragrances_db"][item["idx"]]["season"] = item["suggested"]
                log_vault("edited", f"{len(weak)} bottles", "season-helper-bulk")
                mark_dirty(); save_persisted(); st.success(f"Updated {len(weak)}"); st.rerun()

    with st.expander("Backup & restore", expanded=True):
        if st.button("Restore full sanctuary seed (183 bottles)", key="restore_seed"):
            st.session_state["fragrances_db"] = list(SANCTUARY_SEED_DB)
            mark_dirty(); save_persisted(force=True)
            st.success("Restored 183 bottles."); st.rerun()
        export = {
            "fragrances_db": st.session_state["fragrances_db"],
            "user_reactions": st.session_state.get("user_reactions"),
            "sotd_history": st.session_state.get("sotd_history"),
            "layer_recipes": st.session_state.get("layer_recipes"),
            "wishlist": st.session_state.get("wishlist"),
            "vault_log": st.session_state.get("vault_log"),
            "last_saved_at": st.session_state.get("last_saved_at"),
        }
        st.download_button("Export vault as JSON", data=json.dumps(export, indent=2, ensure_ascii=False),
                           file_name="scented_dead_girl_backup.json", mime="application/json")
        up = st.file_uploader("Restore from backup JSON", type=["json"], key="restore_up")
        if up and st.button("Apply restore", type="primary", key="apply_restore"):
            try:
                up.seek(0)
                incoming = json.load(up)
                for k in ("fragrances_db", "user_reactions", "sotd_history", "layer_recipes", "wishlist", "vault_log"):
                    if k in incoming:
                        st.session_state[k] = incoming[k]
                save_persisted(force=True)
                st.success(f"Restored **{len(st.session_state.get('fragrances_db') or [])}** bottles.")
                st.rerun()
            except Exception as e:
                st.error(f"Restore failed: {e}")

try:
    autosave()
except Exception:
    pass
