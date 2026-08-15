import datetime
import json
import os
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
    page_icon="ð",
    layout="centered",
)

# Custom Gothic Styling for ScentedDeadGirl Aesthetic
# Deep black, blood-crimson accents, spectral blue, floating bats
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;600;700&family=Cinzel+Decorative:wght@400;700&family=UnifrakturMaguntia&display=swap');

    /* Deep void background */
    .stApp {
        background: radial-gradient(ellipse at top, #0a0e18 0%, #020408 45%, #000000 100%);
        color: #c8d0e0;
    }

    /* Headings - spectral gothic */
    h1, h2, h3, h4 {
        color: #9ec5ff !important;
        font-family: 'Cinzel Decorative', 'Cinzel', serif !important;
        text-shadow: 0 0 12px rgba(80, 140, 255, 0.55), 0 0 4px rgba(180, 40, 60, 0.3), 2px 2px 6px rgba(0, 0, 0, 0.95);
        letter-spacing: 1.5px;
    }

    h1 {
        font-size: 2.5rem !important;
        border-bottom: 1px solid #2a1a30;
        padding-bottom: 0.5rem;
        background: linear-gradient(90deg, transparent, rgba(40, 20, 50, 0.4), transparent);
    }

    /* Body text */
    p, .stMarkdown, .stCaption, label, .stText, .stInfo, .stSuccess, .stWarning {
        font-family: 'Cinzel', serif !important;
        color: #b0c0d8 !important;
    }

    /* Sidebar - deeper crypt */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #05070e 0%, #0a0f1a 50%, #08060c 100%) !important;
        border-right: 1px solid #1a1525;
        box-shadow: 4px 0 20px rgba(0, 0, 0, 0.6);
    }
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {
        color: #8ab4ff !important;
        font-family: 'Cinzel Decorative', 'Cinzel', serif !important;
        text-shadow: 0 0 8px rgba(60, 100, 200, 0.4);
    }

    /* Buttons - dark steel with blue glow */
    .stButton > button {
        background: linear-gradient(180deg, #0c1528 0%, #070e1a 100%) !important;
        color: #a0c8ff !important;
        border: 1px solid #2a4068 !important;
        border-radius: 2px !important;
        font-family: 'Cinzel', serif !important;
        font-weight: 600 !important;
        letter-spacing: 0.8px;
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

    /* Primary buttons - deeper emphasis */
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
        font-family: 'Cinzel', serif !important;
    }
    .stTextInput > div > div > input:focus,
    .stSelectbox > div > div > select:focus {
        border-color: #4a80d0 !important;
        box-shadow: 0 0 10px rgba(60, 120, 220, 0.45) !important;
    }

    /* Radio & checkbox */
    .stRadio label, .stCheckbox label {
        font-family: 'Cinzel', serif !important;
        color: #a8bdd8 !important;
    }

    /* Alerts */
    .stAlert {
        background-color: #0a101c !important;
        border: 1px solid #1e2a48 !important;
        color: #b8cce8 !important;
        font-family: 'Cinzel', serif !important;
    }

    /* Expander */
    .streamlit-expanderHeader {
        background-color: #0a0e18 !important;
        color: #8ab0e8 !important;
        font-family: 'Cinzel', serif !important;
        border: 1px solid #1a2540 !important;
    }

    /* Download button */
    .stDownloadButton > button {
        background: linear-gradient(180deg, #0c1528 0%, #070e1a 100%) !important;
        color: #a0c8ff !important;
        border: 1px solid #2a4068 !important;
        font-family: 'Cinzel', serif !important;
    }

    /* File uploader */
    .stFileUploader {
        border: 1px dashed #2a3050 !important;
        background-color: #060a12 !important;
    }

    /* Horizontal rules */
    hr {
        border-color: #1a2035 !important;
        opacity: 0.7;
    }

    /* Floating Bats Animation */
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

    /* Scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    ::-webkit-scrollbar-track {
        background: #030508;
    }
    ::-webkit-scrollbar-thumb {
        background: #1a2540;
        border-radius: 4px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #2a4068;
    }

    /* Subtle crimson accent for success messages */
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
          "notes": (
              "Fruity-woody-oriental (pineapple/rose/oud-leaning)"
          ),
          "category": ["Oriental", "Woody", "Fruity"],
      },
      {
          "name": "Al Rehab Caramello",
          "brand": "Al Rehab",
          "gender": "Unisex",
          "season": "Fall, Winter",
          "notes": (
              "Top â Pistachio, Almond / Heart â Jasmine, Heliotrope / Base â"
              " Caramel, Vanilla, Sandalwood"
          ),
          "category": ["Gourmand", "Sweet"],
      },
      {
          "name": "Al Rehab Chocomusk",
          "brand": "Al Rehab",
          "gender": "Unisex",
          "season": "Fall, Winter",
          "notes": (
              "Top â Warm Spicy, Amber / Heart â Sweet, Powdery, Vanilla /"
              " Base â Chocolate, Musky, Cocoa"
          ),
          "category": ["Gourmand", "Sweet"],
      },
      {
          "name": "Al Rehab Chocomusk Marshmallow",
          "brand": "Al Rehab",
          "gender": "Unisex",
          "season": "Fall, Winter",
          "notes": (
              "Top â Marshmallow, Strawberry / Heart â Cocoa, Vanilla / Base â"
              " Sweet Musk"
          ),
          "category": ["Gourmand", "Sweet"],
      },
      {
          "name": "Al Rehab Chocomusk Vanilla",
          "brand": "Al Rehab",
          "gender": "Unisex",
          "season": "Fall, Winter",
          "notes": (
              "Top â Chocolate / Heart â Vanilla / Base â Musk"
          ),
          "category": ["Gourmand", "Sweet"],
      },
      {
          "name": "Al Rehab Cup Cake",
          "brand": "Al Rehab",
          "gender": "Unisex",
          "season": "Fall, Winter",
          "notes": (
              "Top â Citrus, Amber / Heart â Vanilla Cake / Base â Vanilla,"
              " Amber"
          ),
          "category": ["Gourmand", "Sweet"],
      },
      {
          "name": "Al Rehab French Vanilla",
          "brand": "Al Rehab",
          "gender": "Unisex",
          "season": "Fall, Winter",
          "notes": (
              "Top â Vanilla / Heart â Creamy Sweet / Base â Vanilla, Musk"
          ),
          "category": ["Gourmand", "Sweet"],
      },
      {
          "name": "Al Rehab Royal Men",
          "brand": "Al Rehab",
          "gender": "Male",
          "season": "Fall, Winter",
          "notes": (
              "Top â Spicy, Citrus, Woody / Heart â Floral, Sweet / Base â"
              " Amber, Musk, Vanilla"
          ),
          "category": ["Woody", "Spicy", "Oriental"],
      },
      {
          "name": "Al Rehab Silver",
          "brand": "Al Rehab",
          "gender": "Unisex/Male",
          "season": "Spring, Summer",
          "notes": (
              "Top â Fresh Citrus, Metallic / Heart â Floral / Base â Musk,"
              " Sweet"
          ),
          "category": ["Fresh", "Citrus"],
      },
      {
          "name": "Al Rehab Soft",
          "brand": "Al Rehab",
          "gender": "Unisex (leans feminine)",
          "season": "Fall, Winter",
          "notes": (
              "Top â Citruses / Heart â Orchid, Jasmine, Vanilla, Caramel /"
              " Base â White Musk, Woody Notes, Vetiver"
          ),
          "category": ["Floral", "Sweet", "Gourmand"],
      },
      {
          "name": "Ameerat Al Arab Prive Rose",
          "brand": "Ameerat Al Arab",
          "gender": "Female",
          "season": "Fall, Spring",
          "notes": (
              "Top â Rose / Heart â Floral, Sweet / Base â Musk, Vanilla"
          ),
          "category": ["Floral", "Sweet"],
      },
      {
          "name": "Arabiyat Prestige Bahiya Garnet",
          "brand": "Arabiyat Prestige",
          "gender": "Female-leaning",
          "season": "Fall, Winter",
          "notes": (
              "Top â Cherry, Mandarin, Mango, Pear, Bergamot / Heart â Amber,"
              " Fig, Jasmine / Base â Amber, Vanilla, Sandalwood, Musk"
          ),
          "category": ["Fruity", "Oriental", "Sweet"],
      },
      {
          "name": "Arabiyat Prestige Nyla",
          "brand": "Arabiyat Prestige",
          "gender": "Female",
          "season": "Spring, Summer",
          "notes": (
              "Top â Coconut, Peach, Bergamot, Mandarin / Heart â Tiare, White"
              " Flowers, Jasmine, Rose / Base â White Musk, Patchouli"
          ),
          "category": ["Floral", "Fruity", "Fresh"],
      },
      {
          "name": "Arabiyat Prestige Nyla Vanielle",
          "brand": "Arabiyat Prestige",
          "gender": "Female",
          "season": "Fall, Winter",
          "notes": (
              "Top â Jasmine, Vanilla Bean / Heart â Caramel, Amber / Base â"
              " Musk, Tonka Bean, Vanilla"
          ),
          "category": ["Gourmand", "Sweet", "Floral"],
      },
      {
          "name": "Ard Al Zaafaran Bint Hooran",
          "brand": "Ard Al Zaafaran",
          "gender": "Female",
          "season": "Fall, Winter",
          "notes": (
              "Top â Almond, Coffee, Ylang Ylang / Heart â Jasmine, Rose,"
              " Tuberose / Base â Vanilla, Musk, Tonka, Woody/Cacao"
          ),
          "category": ["Gourmand", "Floral", "Oriental"],
      },
      {
          "name": "Armaf Island Bliss",
          "brand": "Armaf",
          "gender": "Unisex",
          "season": "Spring, Summer",
          "notes": (
              "Top â Tropical Fruits, Coconut / Heart â Sweet / Base â Musk"
          ),
          "category": ["Fruity", "Fresh", "Sweet"],
      },
      {
          "name": "Armaf Odyssey Aqua",
          "brand": "Armaf",
          "gender": "Male",
          "season": "Spring, Summer",
          "notes": (
              "Top â Orange, Grapefruit, Artemisia / Heart â Mint, Lavender /"
              " Base â Ambroxan, Cypress, Patchouli"
          ),
          "category": ["Fresh", "Citrus", "Aromatic"],
      },
      {
          "name": "Armaf Odyssey Candee",
          "brand": "Armaf",
          "gender": "Female-leaning",
          "season": "Fall, Winter",
          "notes": (
              "Top â Strawberry, Raspberry, Peach, Bergamot / Heart â Caramel,"
              " Jasmine / Base â Patchouli, Musk, Amber"
          ),
          "category": ["Fruity", "Gourmand", "Sweet"],
      },
      {
          "name": "Armaf Odyssey Marshmallow",
          "brand": "Armaf",
          "gender": "Unisex",
          "season": "Spring, Fall, Winter",
          "notes": (
              "Top â Apple, Lemon, Coconut, Peony, Lily of the Valley / Heart â"
              " Strawberry, Peach, Raspberry, Apricot, Marshmallow, Orange"
              " Blossom / Base â Vanilla, Praline, Tonka, Amber, Musk, Mascarpone"
          ),
          "category": ["Gourmand", "Fruity", "Sweet"],
      },
      {
          "name": "Banat Dubai",
          "brand": "Le Chameau",
          "gender": "Female",
          "season": "Versatile to cooler",
          "notes": (
              "Top â Jasmine, Bergamot, Peony / Heart â Pineapple, Peach, Plum /"
              " Base â Musk, Patchouli, Sandalwood"
          ),
          "category": ["Floral", "Fruity"],
      },
      {
          "name": "Baraja Red 500",
          "brand": "Baraja",
          "gender": "Unisex/Male",
          "season": "Fall, Winter",
          "notes": (
              "Top â Red Fruits, Spices / Heart â Sweet Notes / Base â Woody,"
              " Musk"
          ),
          "category": ["Fruity", "Woody", "Spicy"],
      },
      {
          "name": "Bellavita Vanilla",
          "brand": "Bellavita",
          "gender": "Female",
          "season": "Fall, Winter",
          "notes": (
              "Top â Aldehydes, Heliotrope, Coconut, Vanilla / Heart â Vanilla,"
              " Mango / Base â White Musk, Coconut, Vanilla Absolute"
          ),
          "category": ["Gourmand", "Sweet"],
      },
      {
          "name": "Berries Cream Macaron",
          "brand": "Arabiyat Sugar",
          "gender": "Female",
          "season": "SpringâFall",
          "notes": "Berry + cream macaron gourmand",
          "category": ["Gourmand", "Fruity", "Sweet"],
      },
      {
          "name": "Black Opinion",
          "brand": "Black Opinion",
          "gender": "Male/Unisex",
          "season": "FallâWinter",
          "notes": "Dark, bold (woody/spicy/leather)",
          "category": ["Woody", "Spicy", "Leather"],
      },
      {
          "name": "Blue for Men Le Parfum",
          "brand": "Blue for Men",
          "gender": "Male/Unisex",
          "season": "Fall, Winter",
          "notes": (
              "Top â Cardamom / Heart â Lavender, Iris / Base â Vanilla,"
              " Oriental Woods"
          ),
          "category": ["Woody", "Oriental", "Spicy"],
      },
      {
          "name": "Caramel Chocolate Macaron",
          "brand": "Arabiyat Sugar",
          "gender": "Female/Unisex",
          "season": "FallâWinter",
          "notes": "Caramel-chocolate-macaron gourmand",
          "category": ["Gourmand", "Sweet"],
      },
      {
          "name": "Club de Nuit Women",
          "brand": "Armaf",
          "gender": "Female",
          "season": "Spring, Fall",
          "notes": (
              "Top â Apple, Citrus / Heart â Rose, Jasmine / Base â Vanilla,"
              " Musk"
          ),
          "category": ["Floral", "Fruity", "Fresh"],
      },
      {
          "name": "Coconut Chiffon",
          "brand": "Arabiyat Sugar",
          "gender": "Female/Unisex",
          "season": "SpringâSummer",
          "notes": "Coconut + light cake/chiffon",
          "category": ["Gourmand", "Sweet", "Fresh"],
      },
      {
          "name": "Confections",
          "brand": "Paris Corner",
          "gender": "Female/Unisex",
          "season": "FallâWinter",
          "notes": "Gourmand/sweet, confectionery-style",
          "category": ["Gourmand", "Sweet"],
      },
      {
          "name": "Dulzura",
          "brand": "Paris Corner",
          "gender": "Female",
          "season": "FallâWinter",
          "notes": (
              "Top â Black pepper, buttermilk / Heart â Cake, vanilla, cream /"
              " Base â Amber, musk"
          ),
          "category": ["Gourmand", "Sweet"],
      },
      {
          "name": "Eclaire Banoffi",
          "brand": "Lattafa",
          "gender": "Unisex/Female",
          "season": "FallâWinter",
          "notes": "Banana-toffee/Ã©clair gourmand",
          "category": ["Gourmand", "Sweet"],
      },
      {
          "name": "Ãclat Parfumerie Al Gazal",
          "brand": "Ãclat Parfumerie",
          "gender": "Unisex (leans masculine)",
          "season": "Versatile to cooler",
          "notes": (
              "Limited public data; typically woody-oriental or spicy"
          ),
          "category": ["Woody", "Oriental"],
      },
      {
          "name": "Elyssia Aura",
          "brand": "Riiffs",
          "gender": "Unisex",
          "season": "Fall, Winter (versatile to cooler)",
          "notes": (
              "Top â Cinnamon, Orange, Nutmeg / Heart â Vanilla Cream, Cognac,"
              " Cocoa / Base â Bourbon Vanilla, Cedarwood, Patchouli"
          ),
          "category": ["Gourmand", "Spicy", "Woody"],
      },
      {
          "name": "Elyssia Scarlet",
          "brand": "Riiffs",
          "gender": "Female",
          "season": "SpringâSummer / versatile",
          "notes": (
              "Top â Black Cherry, Pink Pepper / Heart â Leather, Cream, Benzoin"
              " / Base â Vanilla Absolute, Cashmeran, Amber, Iso E Super"
          ),
          "category": ["Fruity", "Leather", "Sweet"],
      },
      {
          "name": "Emir Pear Potion",
          "brand": "Paris Corner",
          "gender": "Unisex",
          "season": "Spring",
          "notes": (
              "Top â Pear, Apple / Heart â Caramel, Jasmine / Base â"
              " Raspberry, Musk"
          ),
          "category": ["Fruity", "Gourmand", "Sweet"],
      },
      {
          "name": "Empire Najm by Risala",
          "brand": "Risala",
          "gender": "Unisex (female-leaning)",
          "season": "Fall, Winter",
          "notes": (
              "Top â Mango, Ginger, Lemon, Red Berries / Heart â Coumarin,"
              " Jasmine, Cedar / Base â Cypriol, Amber, Musk, Oud"
          ),
          "category": ["Fruity", "Oriental", "Woody"],
      },
      {
          "name": "Emper Boulevard of New York",
          "brand": "Le Chameau",
          "gender": "Unisex",
          "season": "Fall, Winter",
          "notes": (
              "Top â Roasted Coffee Beans / Heart â Praline, Rose / Base â"
              " Oakmoss, Cedar, Amber"
          ),
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
          "season": "SpringâSummer / versatile",
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
          "season": "SpringâSummer / versatile",
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
          "notes": (
              "Top â Vanilla, Chocolate, Burnt Sugar / Heart â Milk,"
              " Creamy/Coconut Milk, Whipped Cream / Base â Musk"
          ),
          "category": ["Gourmand", "Sweet"],
      },
      {
          "name": "French Avenue 8th Wonder",
          "brand": "French Avenue",
          "gender": "Unisex",
          "season": "Fall, Winter",
          "notes": (
              "Top â Cardamom, Pink Pepper, Candy Apple / Heart â Liquor, Dates,"
              " Boozy notes, Davana, Osmanthus / Base â Myrrh, Benzoin, Styrax,"
              " Amber Xtreme, Labdanum, Patchouli"
          ),
          "category": ["Oriental", "Spicy", "Sweet"],
      },
      {
          "name": "French Avenue Spectre Original",
          "brand": "French Avenue",
          "gender": "Male/Unisex (leans masculine)",
          "season": "Fall, Winter",
          "notes": (
              "Top â Incense, Guaiac Wood, Saffron / Heart â Leather, Amberwood,"
              " Violet, Sugar Cane / Base â Smoke, Patchouli, Sandalwood, Woodsy"
              " Notes, Black Musk"
          ),
          "category": ["Woody", "Leather", "Oriental"],
      },
      {
          "name": "French Avenue Vulcan Baie",
          "brand": "French Avenue",
          "gender": "Unisex",
          "season": "Spring, Summer",
          "notes": (
              "Top â Blackberry, Black Currant, Rosemary, Bergamot / Heart â"
              " Raspberry, Vodka, Basil, Lily of the Valley / Base â Strawberry,"
              " Musk, Peach, Amber, Sandalwood, Patchouli, Incense"
          ),
          "category": ["Fruity", "Fresh", "Aromatic"],
      },
      {
          "name": "French Vanilla Latte",
          "brand": "Arabiyat Sugar",
          "gender": "Unisex",
          "season": "Fall, Winter",
          "notes": (
              "Top â Nutella, Cardamom, Rum / Heart â Cocoa, Coconut, White"
              " Flowers, Lily of the Valley / Base â Sandalwood, Ambergris, Musk"
          ),
          "category": ["Gourmand", "Sweet"],
      },
      {
          "name": "Ghaliya",
          "brand": "Zakat",
          "gender": "Unisex/Female",
          "season": "FallâWinter",
          "notes": "Rich oriental/oud-floral",
          "category": ["Oriental", "Floral", "Oud"],
      },
      {
          "name": "Gulf Orchid Cookie Bite",
          "brand": "Gulf Orchid",
          "gender": "Unisex",
          "season": "Fall, Winter",
          "notes": (
              "Top â Cookie, Butter / Heart â Vanilla, Musk / Base â Caramel,"
              " Amber"
          ),
          "category": ["Gourmand", "Sweet"],
      },
      {
          "name": "Gulf Orchid PiÃ±a Colada Musk Collection Body Spray",
          "brand": "Gulf Orchid",
          "gender": "Unisex",
          "season": "Spring, Summer",
          "notes": (
              "Top â Pineapple, Coconut / Heart â Tropical / Base â Musk"
          ),
          "category": ["Fruity", "Fresh", "Sweet"],
      },
      {
          "name": "Hawas Elixir",
          "brand": "Rasasi",
          "gender": "Unisex",
          "season": "FallâWinter",
          "notes": (
              "Top â Mint, bergamot, artemisia / Heart â Dark chocolate,"
              " lavender, benzoin / Base â Vanilla, tonka bean, white musk"
          ),
          "category": ["Gourmand", "Fresh", "Sweet"],
      },
      {
          "name": "Heroes Energize",
          "brand": "Heroes",
          "gender": "Male",
          "season": "Spring, Summer",
          "notes": (
              "Top â Citrus, Aromatic Herbs / Heart â Light Spices / Base â"
              " Woods, Musk"
          ),
          "category": ["Fresh", "Citrus", "Aromatic"],
      },
      {
          "name": "Kandy Rush",
          "brand": "Kandy Rush",
          "gender": "Female/Unisex",
          "season": "FallâWinter / casual year-round",
          "notes": "Sweet candy/gourmand",
          "category": ["Gourmand", "Sweet"],
      },
      {
          "name": "Khadlaj Cafe Latte",
          "brand": "Khadlaj",
          "gender": "Unisex",
          "season": "Fall, Winter",
          "notes": (
              "Top â Coffee, Sweet Almond, Milk / Heart â Vanilla, Ice Cream"
              " Accord, Amber / Base â Vanilla, Almond Cream, Caramel"
          ),
          "category": ["Gourmand", "Sweet"],
      },
      {
          "name": "Khadlaj Cream Velvet",
          "brand": "Khadlaj",
          "gender": "Unisex (leans feminine)",
          "season": "Fall, Winter",
          "notes": (
              "Top â Caramel, Butter / Heart â Tonka, Honey, Jasmine / Base â"
              " Vanilla, Musk, Amber"
          ),
          "category": ["Gourmand", "Sweet"],
      },
      {
          "name": "Khadlaj Hareem Al Sultan Gold",
          "brand": "Khadlaj",
          "gender": "Female",
          "season": "Spring, Summer",
          "notes": (
              "Top â Bergamot, Jasmine, Peony / Heart â Pineapple, Peach, Plum /"
              " Base â Musk, Sandalwood, Patchouli"
          ),
          "category": ["Floral", "Fruity", "Fresh"],
      },
      {
          "name": "Khadlaj Nuha Vanilla Pearl",
          "brand": "Khadlaj",
          "gender": "Female",
          "season": "Fall, Winter",
          "notes": (
              "Top â Blackcurrant, Strawberry, Freesia / Heart â Raspberry,"
              " Magnolia, Cashmere Wood / Base â Vanilla, Caramel, Moss"
          ),
          "category": ["Fruity", "Gourmand", "Floral"],
      },
      {
          "name": "Khadlaj Peach Velvet",
          "brand": "Khadlaj",
          "gender": "Female",
          "season": "Spring, Summer, Fall",
          "notes": (
              "Top â Guava, Peach, Nectarine / Heart â Vanilla, Ginger,"
              " Cinnamon, Amber / Base â Caramel, Musk, Sandalwood"
          ),
          "category": ["Fruity", "Gourmand", "Sweet"],
      },
      {
          "name": "Khadlaj Zainab Oil",
          "brand": "Khadlaj",
          "gender": "Unisex",
          "season": "Fall, Winter",
          "notes": (
              "Top â Bergamot, Gardenia, Almond / Heart â Coconut, Caramel /"
              " Base â Patchouli, Vanilla, Musk"
          ),
          "category": ["Gourmand", "Floral", "Sweet"],
      },
      {
          "name": "Khamrah Waha",
          "brand": "Lattafa",
          "gender": "Unisex",
          "season": "FallâWinter",
          "notes": "Spicy-sweet (date, cinnamon, vanilla family)",
          "category": ["Oriental", "Spicy", "Sweet"],
      },
      {
          "name": "Khayali Vanilla Ayelet",
          "brand": "Khayali",
          "gender": "Unisex",
          "season": "FallâWinter",
          "notes": (
              "Vanilla orchid, jasmine / Brown sugar, tonka / Amber, musk,"
              " patchouli (Kayali-inspired)"
          ),
          "category": ["Gourmand", "Floral", "Sweet"],
      },
      {
          "name": "Lattafa Angham",
          "brand": "Lattafa",
          "gender": "Unisex (leans feminine)",
          "season": "Fall, Winter",
          "notes": (
              "Top â Ginger, Mandarin, Pink Pepper / Heart â Lavender, Praline,"
              " Cacao, Jasmine / Base â Vanilla, Amber, Musk"
          ),
          "category": ["Gourmand", "Spicy", "Sweet"],
      },
      {
          "name": "Lattafa Ansaam Gold",
          "brand": "Lattafa",
          "gender": "Female/Unisex",
          "season": "Fall, Winter",
          "notes": (
              "Top â Mandarin Orange, Pear / Heart â Sweet Notes, Jasmine, Rose"
              " / Base â Musk, Vanilla, Raspberry"
          ),
          "category": ["Fruity", "Floral", "Sweet"],
      },
      {
          "name": "Lattafa Asad",
          "brand": "Lattafa",
          "gender": "Male",
          "season": "Fall, Winter",
          "notes": (
              "Top â Black Pepper, Tobacco, Pineapple / Heart â Patchouli,"
              " Coffee, Iris / Base â Vanilla, Amber, Dry Woods, Benzoin,"
              " Labdanum"
          ),
          "category": ["Woody", "Spicy", "Oriental"],
      },
      {
          "name": "Lattafa Badee Al Oud Noble Blush",
          "brand": "Lattafa",
          "gender": "Female",
          "season": "Fall, Winter",
          "notes": (
              "Top â Rose Milk / Heart â Meringue, Almond / Base â Vanilla,"
              " Musk, Sandalwood"
          ),
          "category": ["Floral", "Gourmand", "Sweet"],
      },
      {
          "name": "Lattafa Coral (Ana Abiyedh Coral)",
          "brand": "Lattafa",
          "gender": "Unisex (leans feminine)",
          "season": "Spring, Summer",
          "notes": (
              "Top â Watermelon, Peach, Orange / Heart â Coconut, White Flowers"
              " / Base â Musk, Vanilla, Amber"
          ),
          "category": ["Fruity", "Fresh", "Sweet"],
      },
      {
          "name": "Lattafa Dalal",
          "brand": "Lattafa",
          "gender": "Female",
          "season": "Spring",
          "notes": (
              "Top â Apple (Golden Delicious), Mandarin / Heart â Jasmine,"
              " Ylang-Ylang, Orange Flower / Base â Vanilla, Musk, Oakmoss"
          ),
          "category": ["Floral", "Fruity", "Fresh"],
      },
      {
          "name": "Lattafa Eclaire",
          "brand": "Lattafa",
          "gender": "Female",
          "season": "Fall, Winter",
          "notes": (
              "Top â Caramel, Milk, Sugar / Heart â Honey, White Flowers / Base"
              " â Vanilla, Praline, Musk"
          ),
          "category": ["Gourmand", "Sweet"],
      },
      {
          "name": "Lattafa Emaan",
          "brand": "Lattafa",
          "gender": "Female/Unisex",
          "season": "Fall, Winter",
          "notes": (
              "Top â Orange Blossom, Black Currant, Bergamot / Heart â Tuberose,"
              " Jasmine, Marigold / Base â Musk, Vanilla, Cedarwood, Patchouli"
          ),
          "category": ["Floral", "Fruity"],
      },
      {
          "name": "Lattafa Eternal Vanille",
          "brand": "Lattafa",
          "gender": "Unisex",
          "season": "Year-round (best Spring/Fall)",
          "notes": (
              "Top â Blackberry / Heart â Cocoapulse, Vanilla Caviar, Cacao /"
              " Base â Akigalawood, Tonka Bean, Ambrofix, Cedarwood, Benzoin,"
              " Musk"
          ),
          "category": ["Gourmand", "Woody", "Sweet"],
      },
      {
          "name": "Lattafa Fakhar Black",
          "brand": "Lattafa",
          "gender": "Unisex",
          "season": "Fall, Winter",
          "notes": (
              "Top â Dark Fruits, Spices / Heart â Woody / Base â Vanilla, Musk"
          ),
          "category": ["Fruity", "Woody", "Spicy"],
      },
      {
          "name": "Lattafa Fakhar Gold",
          "brand": "Lattafa",
          "gender": "Unisex",
          "season": "Fall, Winter",
          "notes": (
              "Top â Tuberose, Salt / Heart â Amber, Tonka / Base â Cedarwood,"
              " Vetiver, Labdanum"
          ),
          "category": ["Floral", "Woody", "Oriental"],
      },
      {
          "name": "Lattafa Habik (Womenâs version)",
          "brand": "Lattafa",
          "gender": "Female",
          "season": "Spring, Summer",
          "notes": (
              "Top â Pear, Bergamot / Heart â Lily of the Valley, Jasmine,"
              " Freesia / Base â Musk, Amber, Oakmoss"
          ),
          "category": ["Floral", "Fresh", "Fruity"],
      },
      {
          "name": "Lattafa Haya",
          "brand": "Lattafa",
          "gender": "Female",
          "season": "Fall, Winter",
          "notes": (
              "Top â Champagne, Strawberry, Rose, Tangerine, Blood Orange /"
              " Heart â Gardenia, Jasmine, Vanilla Orchid / Base â Amber,"
              " Sandalwood"
          ),
          "category": ["Floral", "Fruity", "Sweet"],
      },
      {
          "name": "Lattafa Her Confessions",
          "brand": "Lattafa",
          "gender": "Female",
          "season": "Fall, Winter",
          "notes": (
              "Top â Cinnamon / Heart â Tuberose, Jasmine, Incense / Base â"
              " Vanilla, Musk, Tonka"
          ),
          "category": ["Floral", "Spicy", "Oriental"],
      },
      {
          "name": "Lattafa His Confessions",
          "brand": "Lattafa",
          "gender": "Male",
          "season": "Fall, Winter",
          "notes": (
              "Top â Lavender, Cinnamon, Mandarin / Heart â Iris, Benzoin,"
              " Cypress, Mahonial / Base â Vanilla, Tonka, Amber, Incense,"
              " Cedarwood, Patchouli"
          ),
          "category": ["Woody", "Spicy", "Oriental"],
      },
      {
          "name": "Lattafa Khamrah Dukhan",
          "brand": "Lattafa",
          "gender": "Unisex",
          "season": "Fall, Winter",
          "notes": (
              "Top â Spices, Pimento, Mandarin / Heart â Incense, Labdanum,"
              " Orange Blossom, Patchouli / Base â Tobacco, Praline, Amber, Tonka"
              " Bean, Benzoin"
          ),
          "category": ["Oriental", "Spicy", "Sweet"],
      },
      {
          "name": "Lattafa Khamrah Original",
          "brand": "Lattafa",
          "gender": "Unisex",
          "season": "Fall, Winter",
          "notes": (
              "Top â Cinnamon, Nutmeg, Bergamot / Heart â Dates, Praline,"
              " Tuberose, Mahonial / Base â Vanilla, Tonka Bean, Amberwood,"
              " Myrrh, Benzoin, Akigalawood"
          ),
          "category": ["Oriental", "Spicy", "Sweet"],
      },
      {
          "name": "Lattafa Khamrah Qahwa",
          "brand": "Lattafa",
          "gender": "Unisex",
          "season": "Fall, Winter",
          "notes": (
              "Top â Cinnamon, Cardamom, Ginger / Heart â Praline, Candied"
              " Fruits, White Flowers / Base â Coffee, Vanilla, Tonka Bean,"
              " Benzoin, Musk"
          ),
          "category": ["Gourmand", "Spicy", "Sweet"],
      },
      {
          "name": "Lattafa Maitha Oil (Attar)",
          "brand": "Lattafa",
          "gender": "Unisex",
          "season": "Fall, Winter",
          "notes": (
              "Top â Anise / Heart â Caramel / Base â Vanilla, Tonka Bean, Musk"
          ),
          "category": ["Gourmand", "Sweet"],
      },
      {
          "name": "Lattafa Mayar Cherry Intense",
          "brand": "Lattafa",
          "gender": "Female",
          "season": "Fall, Winter",
          "notes": (
              "Top â Strawberry, Bergamot / Heart â Cherry Jam, Cacao / Base â"
              " Vanilla, Amber, Patchouli"
          ),
          "category": ["Fruity", "Gourmand", "Sweet"],
      },
      {
          "name": "Lattafa Nasmaat",
          "brand": "Lattafa",
          "gender": "Unisex",
          "season": "Spring, Fall",
          "notes": (
              "Top â Blackcurrant, Apricot, Pineapple / Heart â Magnolia,"
              " Cyclamen, Jasmine, Orange Blossom, Rose / Base â Vanilla,"
              " Cashmeran, Caramel, Sandalwood"
          ),
          "category": ["Floral", "Fruity", "Sweet"],
      },
      {
          "name": "Lattafa Nebras",
          "brand": "Lattafa",
          "gender": "Unisex",
          "season": "Fall, Winter",
          "notes": (
              "Top â Red Berries, Mandarin Orange / Heart â Vanilla, Cacao,"
              " Rose / Base â Sugar, Tonka Bean, Amber, Musk"
          ),
          "category": ["Gourmand", "Fruity", "Sweet"],
      },
      {
          "name": "Lattafa Nebras Elixir",
          "brand": "Lattafa",
          "gender": "Unisex",
          "season": "Fall, Winter, Mild Spring",
          "notes": (
              "Top â Milk Candy, Whipped Cream / Heart â Sugar Cane, Heliotrope"
              " / Base â Vanilla, Ambroxan, Musk"
          ),
          "category": ["Gourmand", "Sweet"],
      },
      {
          "name": "Lattafa Opulent Dubai",
          "brand": "Lattafa",
          "gender": "Unisex",
          "season": (
              "Spring, Summer (versatile year-round in mild climates)"
          ),
          "notes": (
              "Top â Mango, Grapefruit, Lemon, Ginger / Heart â Jasmine,"
              " Cedarwood, Violet / Base â Woodsy notes, Ambergris, Benzoin,"
              " Oakmoss"
          ),
          "category": ["Fruity", "Woody", "Fresh"],
      },
      {
          "name": "Lattafa Oud Mood",
          "brand": "Lattafa",
          "gender": "Unisex",
          "season": "Fall, Winter",
          "notes": (
              "Top â Rose, Saffron, Pimento / Heart â Agarwood (Oud), Caramel,"
              " Floral Notes, Patchouli / Base â Woody Notes, Amber, Resins,"
              " Incense, Musk"
          ),
          "category": ["Oriental", "Oud", "Woody"],
      },
      {
          "name": "Lattafa Qaed Al Fursan (Original)",
          "brand": "Lattafa",
          "gender": "Unisex (leans masculine)",
          "season": "Versatile",
          "notes": (
              "Top â Pineapple, Saffron / Heart â Balsam Fir, Jasmine / Base â"
              " Cedar, Amber, Agarwood (Oud)"
          ),
          "category": ["Fruity", "Woody", "Oud"],
      },
      {
          "name": "Lattafa Qaed Al Fursan Unlimited",
          "brand": "Lattafa",
          "gender": "Male/Unisex",
          "season": "Spring, Fall",
          "notes": (
              "Top â Coconut, Pineapple, Citruses / Heart â Ylang-Ylang,"
              " Frangipani, Jasmine / Base â Vanilla, Musk, Sandalwood, Sweet"
              " Notes"
          ),
          "category": ["Fruity", "Floral", "Sweet"],
      },
      {
          "name": "Lattafa Qaed Al Fursan Untamed",
          "brand": "Lattafa",
          "gender": "Male/Unisex",
          "season": "Spring, Fall",
          "notes": (
              "Top â Apple, Citrus / Heart â Floral / Base â Sweet, Woody"
          ),
          "category": ["Fruity", "Woody", "Fresh"],
      },
      {
          "name": "Lattafa Raneen",
          "brand": "Lattafa",
          "gender": "Female",
          "season": "Fall, Winter",
          "notes": (
              "Top â Fruity, Sweet / Heart â Floral / Base â Vanilla, Musk"
          ),
          "category": ["Floral", "Fruity", "Sweet"],
      },
      {
          "name": "Lattafa Rave Now (for Women)",
          "brand": "Lattafa",
          "gender": "Female",
          "season": "Spring, Fall",
          "notes": (
              "Top â Red Fruits, Orange / Heart â Marshmallow, Jasmine, Lily of"
              " the Valley / Base â Vanilla, Musk, Moss"
          ),
          "category": ["Fruity", "Gourmand", "Floral"],
      },
      {
          "name": "Lattafa Rave Now Intense",
          "brand": "Lattafa",
          "gender": "Male/Unisex",
          "season": "Spring, Fall",
          "notes": (
              "Top â Cucumber, Watermelon, Tangerine / Heart â Basil, Sage /"
              " Base â Sandalwood, Leather, Cedar"
          ),
          "category": ["Fresh", "Woody", "Aromatic"],
      },
      {
          "name": "Lattafa Sakeena",
          "brand": "Lattafa",
          "gender": "Female/Unisex",
          "season": "Fall, Winter",
          "notes": (
              "Top â Passionfruit, Mandarin Orange, Ozonic Notes / Heart â"
              " Raspberry, Rose, Orange Blossom, Sea Salt / Base â Toffee,"
              " Praline, Vanilla, Musk"
          ),
          "category": ["Fruity", "Gourmand", "Floral"],
      },
      {
          "name": "Lattafa Teriaq",
          "brand": "Lattafa",
          "gender": "Unisex (leans feminine)",
          "season": "Fall, Winter",
          "notes": (
              "Top â Caramel, Bitter Almond, Apricot, Pink Pepper / Heart â"
              " Honey, Rhubarb, White Flowers, Rose / Base â Leather, Vanilla,"
              " Musk, Vetiver, Labdanum"
          ),
          "category": ["Gourmand", "Floral", "Oriental"],
      },
      {
          "name": "Lattafa Teriaq Intense",
          "brand": "Lattafa",
          "gender": "Unisex",
          "season": "Fall, Winter",
          "notes": (
              "Top â Saffron, Bergamot / Heart â Plum Liquor, Cinnamon / Base â"
              " Amber, Tonka Bean, Benzoin"
          ),
          "category": ["Oriental", "Spicy", "Sweet"],
      },
      {
          "name": "Lattafa Vanilla Freak (Give Me Gourmand)",
          "brand": "Lattafa",
          "gender": "Unisex / Female-leaning",
          "season": "Fall, Spring",
          "notes": (
              "Top â Cupcake / Heart â Sugar Frosting, Almond, Cinnamon / Base"
              " â Butter, Vanilla, Musk"
          ),
          "category": ["Gourmand", "Sweet"],
      },
      {
          "name": "Lattafa Whipped Pleasure (Give Me Gourmand)",
          "brand": "Lattafa",
          "gender": "Female",
          "season": "Fall, Winter",
          "notes": (
              "Top â Caramel, Popcorn, Salted Caramel / Heart â Milk, Jasmine /"
              " Base â Tonka, Benzoin, Musk, Ambrofix"
          ),
          "category": ["Gourmand", "Sweet"],
      },
      {
          "name": "Lattafa Yara Candy Body Spray",
          "brand": "Lattafa",
          "gender": "Female",
          "season": "Fall, Winter",
          "notes": (
              "Top â Candy, Sweet / Heart â Fruity / Base â Vanilla, Musk"
          ),
          "category": ["Gourmand", "Sweet", "Fruity"],
      },
      {
          "name": "Lattafa Yara Tous",
          "brand": "Lattafa",
          "gender": "Female",
          "season": "Versatile",
          "notes": (
              "Top â Fruity, Sweet / Heart â Floral / Base â Vanilla, Musk"
          ),
          "category": ["Floral", "Fruity", "Sweet"],
      },
      {
          "name": "Love & Peace",
          "brand": "Lattafa",
          "gender": "Unisex/Female",
          "season": "SpringâFall",
          "notes": "Soft floral, musky, or peaceful sweet",
          "category": ["Floral", "Sweet"],
      },
      {
          "name": "Maison Alhambra Luxe Chic",
          "brand": "Maison Alhambra",
          "gender": "Female/Unisex",
          "season": "Spring, Fall",
          "notes": (
              "Top â Tangerine, Freesia / Heart â Lily of the Valley, Jasmine,"
              " Rose / Base â Musk, Sandalwood, Amber"
          ),
          "category": ["Floral", "Fresh"],
      },
      {
          "name": "Maison Asrar Vanilla Aura",
          "brand": "Maison Asrar",
          "gender": "Female/Unisex",
          "season": "Fall, Winter",
          "notes": (
              "Top â Vanilla / Heart â Creamy Sweet / Base â Vanilla, Musk"
          ),
          "category": ["Gourmand", "Sweet"],
      },
      {
          "name": "Maison Asrar Vanilla Seduction",
          "brand": "Maison Asrar",
          "gender": "Female/Unisex",
          "season": "Fall, Winter",
          "notes": (
              "Top â Plum, Jasmine, Lily of the Valley / Heart â Vanilla,"
              " Brown Sugar, Caramel / Base â Tonka, Patchouli, Amber, Musk"
          ),
          "category": ["Gourmand", "Floral", "Sweet"],
      },
      {
          "name": "Majestic Supreme",
          "brand": "Le Falcone",
          "gender": "Women/Unisex",
          "season": "FallâWinter / versatile",
          "notes": (
              "Top â Rose, peony, pink pepper / Heart â Raspberry blossom,"
              " jasmine / Base â Amber, papyrus, tonka, vanilla"
          ),
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
          "season": "SpringâSummer / year-round",
          "notes": (
              "Top â Mango, nutmeg, clove / Heart â Leather, saffron, amber,"
              " moss / Base â Akigalawood, patchouli, vetiver, cypriol"
          ),
          "category": ["Fruity", "Woody", "Spicy"],
      },
      {
          "name": "Mango Ice",
          "brand": "Gulf Orchid",
          "gender": "Unisex",
          "season": "SpringâSummer",
          "notes": "Fruity mango with cool/icy facets",
          "category": ["Fruity", "Fresh"],
      },
      {
          "name": "Mayar",
          "brand": "Lattafa",
          "gender": "Female",
          "season": "Spring, Summer",
          "notes": (
              "Top â Lychee, Raspberry, Violet Leaf / Heart â Peony, White"
              " Rose, Jasmine / Base â Musk, Vanilla"
          ),
          "category": ["Floral", "Fruity", "Fresh"],
      },
      {
          "name": "Mayar Natural Intense Body Spray",
          "brand": "Mayar",
          "gender": "Female",
          "season": "Fall, Winter",
          "notes": (
              "Top â Sweet Gourmand / Heart â Vanilla / Base â Musk"
          ),
          "category": ["Gourmand", "Sweet"],
      },
      {
          "name": "Melt Cafe Bliss",
          "brand": "Mamlakat Al Oud / Fragrance World",
          "gender": "Unisex",
          "season": "Fall, Winter",
          "notes": (
              "Top â Black Coffee, Amaretto Liquor / Heart â Vanilla Ice Cream,"
              " Speculoos / Base â Vanilla Pods, Brown Sugar, Grey Amber"
          ),
          "category": ["Gourmand", "Sweet"],
      },
      {
          "name": "Melt CrÃ¨me Caramel",
          "brand": "Mamlakat Al Oud",
          "gender": "Unisex (leans feminine)",
          "season": "Fall, Winter",
          "notes": (
              "Top â Caramel, Vanilla Flower / Heart â Dulce de Leche, Cotton"
              " Candy, Frangipani, White Flowers / Base â Vanilla Pod, Tonka"
              " Bean, Musk"
          ),
          "category": ["Gourmand", "Sweet"],
      },
      {
          "name": "Melt Marshmallows Kiss",
          "brand": "Mamlakat Al Oud",
          "gender": "Unisex",
          "season": "Fall, Winter, Spring",
          "notes": (
              "Top â Strawberry, Blackberry (or Caramel/Milk) / Heart â"
              " Jasmine, Rose, Marshmallow, Vanilla, Honey / Base â Vanilla,"
              " Musk, Praline, Tonka"
          ),
          "category": ["Gourmand", "Floral", "Sweet"],
      },
      {
          "name": "Melt Vanilla Madness",
          "brand": "Mamlakat Al Oud",
          "gender": "Unisex (leans feminine)",
          "season": "Fall, Winter (versatile year-round)",
          "notes": (
              "Top â Vanilla (woody tones), Lavender, Cacao, Ginger / Heart â"
              " Vanilla Caviar / Base â Vanilla Absolute"
          ),
          "category": ["Gourmand", "Sweet"],
      },
      {
          "name": "Melt Velvet Breeze",
          "brand": "Mamlakat Al Oud",
          "gender": "Unisex",
          "season": "Fall, Winter",
          "notes": (
              "Top â Italian Bergamot, Pistachio Gelato, Hazelnut, Sweet Rum,"
              " Cardamom / Heart â Geranium, White Peony, Muguet, Jasmine /"
              " Base â Amber, Musk, Woody Notes"
          ),
          "category": ["Gourmand", "Floral", "Woody"],
      },
      {
          "name": "Miss Armaf Mystique",
          "brand": "Armaf",
          "gender": "Female",
          "season": "Fall, Winter",
          "notes": (
              "Top â Pear, Tangerine, Bergamot, Orange / Heart â Vanilla,"
              " Strawberry, Mimosa, Rose, Ylang Ylang, Jasmine, Passionfruit /"
              " Base â Vanilla, Coffee, Tonka Bean, Patchouli, Vetiver"
          ),
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
          "notes": (
              "Top â Brown Sugar, Caramel, Biscuit / Heart â Toffee, Vanilla"
              " Bean, Amber / Base â White Musk, Praline"
          ),
          "category": ["Gourmand", "Sweet"],
      },
      {
          "name": "Obsidian",
          "brand": "French Avenue",
          "gender": "Unisex/Male",
          "season": "FallâWinter",
          "notes": "Dark, woody, or smoky-oriental",
          "category": ["Woody", "Oriental", "Smoky"],
      },
      {
          "name": "Panache Angel Dust",
          "brand": "Khadlaj",
          "gender": "Female",
          "season": "SpringâFall / versatile",
          "notes": "Soft, powdery, musk-vanilla / âangelicâ",
          "category": ["Floral", "Sweet", "Powdery"],
      },
      {
          "name": "Paris Corner Eshal Vanilla",
          "brand": "Paris Corner",
          "gender": "Female/Unisex",
          "season": "Fall, Winter",
          "notes": (
              "Top â Sugar, Sweet Notes / Heart â Rose, Jasmine / Base â"
              " Vanilla, Caramel, Musk"
          ),
          "category": ["Gourmand", "Floral", "Sweet"],
      },
      {
          "name": "Paris Corner Khair Men",
          "brand": "Paris Corner",
          "gender": "Male/Unisex",
          "season": "Fall, Winter",
          "notes": (
              "Top â Davana, Bergamot, Pink Pepper / Heart â Agarwood (Oud),"
              " Amber, Rosemary / Base â Leather, Vetiver, Musk"
          ),
          "category": ["Woody", "Oud", "Spicy"],
      },
      {
          "name": "Paris Corner Marshmallow Blush",
          "brand": "Paris Corner",
          "gender": "Female/Unisex",
          "season": "Fall, Winter",
          "notes": (
              "Top â Marshmallow, Sweet / Heart â Fruity / Base â Vanilla, Musk"
          ),
          "category": ["Gourmand", "Sweet", "Fruity"],
      },
      {
          "name": "Paris Corner Qissa Delicious",
          "brand": "Paris Corner",
          "gender": "Female",
          "season": "Fall, Winter",
          "notes": (
              "Top â Whipped Cream, Dark Chocolate, Orange / Heart â"
              " Marshmallow, Coconut, Jasmine / Base â Vanilla, White Musk"
          ),
          "category": ["Gourmand", "Sweet"],
      },
      {
          "name": "Pecan Butter Cookie",
          "brand": "Arabiyat Sugar",
          "gender": "Unisex/Female",
          "season": "FallâWinter",
          "notes": (
              "Top â Pecan, coconut milk, butter / Heart â Hazelnut, almond,"
              " roasted nuts / Base â Hazelnut, vanilla, ambergris"
          ),
          "category": ["Gourmand", "Sweet"],
      },
      {
          "name": "Phlur Heavy Cream",
          "brand": "Phlur",
          "gender": "Unisex",
          "season": "Fall, Winter",
          "notes": (
              "Top â Marshmallow, Sugar, Citrus / Heart â Coconut, Jasmine /"
              " Base â Whipped Cream, Vanilla, Caramel"
          ),
          "category": ["Gourmand", "Sweet"],
      },
      {
          "name": "Phlur Vanilla Skin",
          "brand": "Phlur",
          "gender": "Unisex (female-leaning)",
          "season": "Fall, Winter",
          "notes": (
              "Top â Sugar, Pink Pepper, Apple / Heart â Cashmere Wood, Jasmine,"
              " Lily / Base â Vanilla, Sandalwood, Agarwood, Benzoin"
          ),
          "category": ["Gourmand", "Woody", "Sweet"],
      },
      {
          "name": "Pink Velvet",
          "brand": "Maison Alhambra",
          "gender": "Female",
          "season": "SpringâFall",
          "notes": "Soft, powdery, rosy, or gourmand-pink",
          "category": ["Floral", "Sweet", "Powdery"],
      },
      {
          "name": "Pink Yara / Yara Pink",
          "brand": "Lattafa",
          "gender": "Female",
          "season": "SpringâSummer",
          "notes": (
              "Top â Orchid, heliotrope, tangerine / Heart â Gourmand accord,"
              " tropical fruits / Base â Vanilla, musk, sandalwood"
          ),
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
          "notes": (
              "Top â Apple, mint / Heart â Geranium, cinnamon, lavender / Base"
              " â Vanilla, Peru balsam, cedarwood, guaiac wood"
          ),
          "category": ["Fresh", "Woody", "Spicy"],
      },
      {
          "name": "Rasasi Hawas Diva",
          "brand": "Rasasi",
          "gender": "Female",
          "season": "Fall, Winter",
          "notes": (
              "Top â Red Fruits, Rhubarb, Lychee / Heart â Rose, Frankincense,"
              " Cedar / Base â Vanilla, Musk, Ambergris"
          ),
          "category": ["Fruity", "Floral", "Woody"],
      },
      {
          "name": "Rasasi Hawas Eclat (Eclat Hawas)",
          "brand": "Rasasi",
          "gender": "Female",
          "season": "Spring, Fall",
          "notes": (
              "Top â Litchi/Lychee, Bergamot, Pear, Pistachio / Heart â Rose,"
              " Incense / Base â Vanilla, Amber, Musk, Woody Notes"
          ),
          "category": ["Fruity", "Floral", "Woody"],
      },
      {
          "name": "Rasasi Hawas Ice",
          "brand": "Rasasi",
          "gender": "Male",
          "season": "Versatile",
          "notes": (
              "Top â Apple, Italian Lemon, Sicilian Bergamot, Star Anise /"
              " Heart â Plum, Orange Blossom, Cardamom / Base â Musk, Moss,"
              " Driftwood, Amber"
          ),
          "category": ["Fresh", "Fruity", "Aromatic"],
      },
      {
          "name": "Rasasi Hawas London",
          "brand": "Rasasi",
          "gender": "Unisex",
          "season": "Fall, Spring",
          "notes": (
              "Top â Pink Pepper, Saffron, Pear / Heart â Rose, Frankincense,"
              " White Flowers / Base â Blonde Woods, Vanilla, Amber, Musk"
          ),
          "category": ["Floral", "Woody", "Spicy"],
      },
      {
          "name": "Rasasi Hawas Pink",
          "brand": "Rasasi",
          "gender": "Female",
          "season": "Fall, Winter",
          "notes": (
              "Top â Cinnamon, Nutmeg, Neroli / Heart â Marshmallow, Tuberose,"
              " Orange Blossom / Base â Cotton Candy, Vanilla, Tonka Bean"
          ),
          "category": ["Gourmand", "Floral", "Sweet"],
      },
      {
          "name": "Red Velvet",
          "brand": "Armaf Delights",
          "gender": "Female/Unisex",
          "season": "Fall, Winter",
          "notes": (
              "Top â Strawberry, Lemon / Heart â Whipped Sugar, Sugarberry,"
              " Frangipani / Base â Vanilla Bean, Musk, Amber"
          ),
          "category": ["Gourmand", "Fruity", "Sweet"],
      },
      {
          "name": "Rizz Tiramisu Candy",
          "brand": "Rizz",
          "gender": "Female",
          "season": "Spring, Fall",
          "notes": (
              "Top â Bergamot / Heart â Blackcurrant, Strawberry Milk / Base â"
              " Musk, Vanilla"
          ),
          "category": ["Gourmand", "Fruity", "Sweet"],
      },
      {
          "name": "Safa by Nusuk",
          "brand": "Nusuk",
          "gender": "Unisex/Female",
          "season": "SpringâSummer / versatile",
          "notes": (
              "Top â Marshmallow, Strawberry, Lemon / Heart â Coconut, Sugar,"
              " Nectarine / Base â Vanilla, Musk, Ambroxan"
          ),
          "category": ["Gourmand", "Fruity", "Sweet"],
      },
      {
          "name": "Sahari Ghubar Al Dhahab",
          "brand": "Sahari",
          "gender": "Unisex",
          "season": "Fall, Winter",
          "notes": (
              "Top â Cinnamon, Pear, Mandarin, Floral notes / Heart â Jasmine"
              " Sambac, Orange Blossom / Base â White Musk, Vanilla, Tonka Bean,"
              " Coffee, Patchouli"
          ),
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
          "season": "SpringâSummer",
          "notes": (
              "Top â Heliotrope, orchid, tangerine / Heart â Gourmand accord,"
              " tropical fruits / Base â Vanilla, musk, sandalwood"
          ),
          "category": ["Floral", "Gourmand", "Fruity"],
      },
      {
          "name": "Spectre / Sceptre Malachite",
          "brand": "Maison Alhambra",
          "gender": "Unisex",
          "season": "SpringâSummer",
          "notes": (
              "Top â Green tangerine, bergamot, blackcurrant / Heart â"
              " Aromatic + spicy notes, lavender, pink pepper, jasmine / Base â"
              " Amber, musk, woody notes, vetiver"
          ),
          "category": ["Fresh", "Aromatic", "Woody"],
      },
      {
          "name": "Strawberry Tres Leches",
          "brand": "Arabiyat Sugar",
          "gender": "Female",
          "season": "SpringâSummer / year-round",
          "notes": "Strawberry + milky cake gourmand",
          "category": ["Gourmand", "Fruity", "Sweet"],
      },
      {
          "name": "Sugar Crown",
          "brand": "Lattafa",
          "gender": "Female/Unisex",
          "season": "FallâWinter",
          "notes": "Sweet/sugar gourmand",
          "category": ["Gourmand", "Sweet"],
      },
      {
          "name": "Sugar Me Dulce de Leche",
          "brand": "Maison Alhambra",
          "gender": "Unisex/Female",
          "season": "FallâWinter",
          "notes": "Dulce de leche / caramel-vanilla gourmand",
          "category": ["Gourmand", "Sweet"],
      },
      {
          "name": "Sweet Surrender",
          "brand": "Mahajan",
          "gender": "Female",
          "season": "FallâWinter / versatile",
          "notes": "Soft sweet/gourmand",
          "category": ["Gourmand", "Sweet"],
      },
      {
          "name": "Sweet Surrender Pink Parfait",
          "brand": "Mahajan",
          "gender": "Female",
          "season": "SpringâSummer / year-round",
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
          "season": "Versatile (SpringâSummer preferred)",
          "notes": (
              "Top â Ginger, Calabrian Bergamot, Lemon, Orange Blossom / Heart"
              " â Musk, Rose Petals, Tuberose / Base â Vanilla Bean, Amberwood,"
              " Clearwood"
          ),
          "category": ["Floral", "Fresh", "Woody"],
      },
      {
          "name": "The King",
          "brand": "Ali",
          "gender": "Male",
          "season": "FallâWinter / versatile",
          "notes": "Masculine woody or oriental",
          "category": ["Woody", "Oriental"],
      },
      {
          "name": "Toffee Ganache",
          "brand": "Arabiyat Sugar",
          "gender": "Unisex",
          "season": "FallâWinter",
          "notes": "Toffee/chocolate gourmand",
          "category": ["Gourmand", "Sweet"],
      },
      {
          "name": "Valentine Milano",
          "brand": "Valentine",
          "gender": "Unisex",
          "season": "Fall, Winter",
          "notes": (
              "Top â Raspberry, Peach, Bergamot / Heart â Rose, Jasmine, Orange"
              " Blossom / Base â Vanilla, Amber, Woods"
          ),
          "category": ["Floral", "Fruity", "Sweet"],
      },
      {
          "name": "Valentine Nero Xtravagant",
          "brand": "Valentine (Urban Collection)",
          "gender": "Male / Unisex (leans masculine)",
          "season": "Fall, Winter (versatile)",
          "notes": (
              "Top â Calabrian Bergamot, Espresso Coffee Accord / Heart â"
              " Coffee / Base â Vetiver"
          ),
          "category": ["Woody", "Fresh", "Aromatic"],
      },
      {
          "name": "Vanilla Addiction",
          "brand": "Gulf Orchid",
          "gender": "Unisex/Female",
          "season": "FallâWinter",
          "notes": "Vanilla-forward gourmand",
          "category": ["Gourmand", "Sweet"],
      },
      {
          "name": "Vanilla Dunes",
          "brand": "Khadlaj",
          "gender": "Unisex",
          "season": "Autumn, Winter",
          "notes": (
              "Top â Vanilla, Cinnamon, Cardamom, Bergamot / Heart â Orange"
              " Blossom, Guaiac Wood, Bourbon / Base â Praline, Amber, Musk"
          ),
          "category": ["Gourmand", "Spicy", "Woody"],
      },
      {
          "name": "Yara Elixir",
          "brand": "Lattafa",
          "gender": "Female",
          "season": "Fall, Winter, Cool Spring Days",
          "notes": (
              "Top â Strawberry S'mores, Black Currant / Heart â Jasmine,"
              " Orange Blossom / Base â Vanilla, Caramel, Amber, Musk"
          ),
          "category": ["Gourmand", "Floral", "Sweet"],
      },
      {
          "name": "Zenith",
          "brand": "Riiffs",
          "gender": "Unisex",
          "season": "SpringâSummer / versatile",
          "notes": (
              "Top â Coconut, Vanilla, Cream / Heart â Rum, Saffron / Base â"
              " Cashmeran, Tonka Bean"
          ),
          "category": ["Gourmand", "Sweet", "Fresh"],
      },
      {
          "name": "Zimaya Fatima (Fatima Pink)",
          "brand": "Zimaya",
          "gender": "Female",
          "season": "Spring, Fall",
          "notes": (
              "Top â Rhubarb, Bergamot, Grapefruit, Nutmeg / Heart â Rose,"
              " Jasmine / Base â Musk, Vanilla, Vetiver, Ambergris"
          ),
          "category": ["Floral", "Fruity", "Fresh"],
      },
      {
          "name": "Zimaya Hawwa Red",
          "brand": "Zimaya",
          "gender": "Female",
          "season": "Fall, Winter",
          "notes": (
              "Top â Cassis, Strawberry, Raspberry, Orange / Heart â Black"
              " Currant, Grapefruit, Peach, Lily / Base â Musk, Vanilla,"
              " Patchouli"
          ),
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
  season = fragrance["season"].lower()
  if weather == "Any":
    return True

  is_summer_target = "summer" in weather.lower() or "hot" in weather.lower()
  is_winter_target = "winter" in weather.lower() or "cold" in weather.lower()

  # Strict filtering logic
  if is_summer_target:
    if (
        ("winter" in season or "fall" in season or "autumn" in season)
        and not "summer" in season
        and not "spring" in season
        and not "versatile" in season
        and not "year-round" in season
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
        and not "winter" in season
        and not "fall" in season
        and not "autumn" in season
        and not "cooler" in season
        and not "versatile" in season
        and not "year-round" in season
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

  if weather == "Warm / Mild":
    return any(
        x in season
        for x in [
            "spring",
            "fall",
            "autumn",
            "mild",
            "versatile",
            "year-round",
            "summer",
        ]
    )

  if weather == "Cool / Autumn":
    return any(
        x in season
        for x in [
            "fall",
            "autumn",
            "winter",
            "cooler",
            "versatile",
            "year-round",
        ]
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

  score += random.randint(0, 3)
  return score


def get_top_fragrances(
    gender: str, weather: str, category: str, occasion: str, top_n: int
) -> list:
  scored = []
  for f in st.session_state["fragrances_db"]:
    if st.session_state["user_reactions"].get(f["name"]) == "dislike":
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

  score += random.randint(1, 5)
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


# ==========================================
# STREAMLIT USER INTERFACE
# ==========================================
st.title("ð ScentedDeadGirl ð¤")
st.markdown(
    """
    *Enter the crypt of scentâ¦*  
    Filter the vault, cherish or banish bottles, log your Scent of the Day,  
    and weave forbidden layering combinations under the watch of the bats.
    """
)

st.sidebar.header("ð Search Your Collection")
search_col1, search_col2 = st.sidebar.columns([3, 1])
with search_col1:
  search_query = st.text_input(
      "Type name or brand...",
      value=st.session_state["search_input"],
      placeholder="e.g. Lattafa, Eclaire",
      label_visibility="collapsed",
  )
  st.session_state["search_input"] = search_query
with search_col2:
  if st.button("Clear", key="clear_search_btn"):
    st.session_state["search_input"] = ""
    st.rerun()

# Quick Notes & Season Lookup Section
st.sidebar.markdown("---")
st.sidebar.header("ð¦ Quick Notes & Season Lookup")
quick_query = st.sidebar.text_input(
    "Fragrance name...",
    value=st.session_state["quick_lookup_input"],
    placeholder="e.g. Ajwad",
    key="quick_lookup_box",
)
st.session_state["quick_lookup_input"] = quick_query

if quick_query:
  matched_quick = [
      f
      for f in st.session_state["fragrances_db"]
      if quick_query.lower() in f["name"].lower()
  ]
  if matched_quick:
    for f in matched_quick:
      st.sidebar.info(
          f"**{f['name']}** ({f['brand']})\n\nð¿ **Notes:**"
          f" {f['notes']}\n\nð¤ï¸ **Season:** {f['season']}"
      )
  else:
    st.sidebar.warning("No matching fragrance found.")

# Note Specific Search Option
st.sidebar.markdown("---")
st.sidebar.header("ð Search by Specific Note")
note_col1, note_col2 = st.sidebar.columns([3, 1])
with note_col1:
  note_query = st.text_input(
      "Note keyword...",
      value=st.session_state["note_search_input"],
      placeholder="e.g. Vanilla, Coffee",
      label_visibility="collapsed",
  )
  st.session_state["note_search_input"] = note_query
with note_col2:
  if st.button("Clear", key="clear_note_btn"):
    st.session_state["note_search_input"] = ""
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.header("ð¯ Filter Options")

gender = st.sidebar.selectbox(
    "Gender Preference", ["Any", "Male", "Female", "Unisex"]
)
weather = st.sidebar.selectbox(
    "Weather / Season",
    [
        "Any",
        "Hot / Summer",
        "Warm / Mild",
        "Cool / Autumn",
        "Cold / Winter",
    ],
)
category = st.sidebar.selectbox(
    "Preferred Category",
    ["Any", "Gourmand", "Floral", "Woody", "Oriental", "Fresh", "Fruity"],
)
occasion = st.sidebar.selectbox(
    "Occasion",
    [
        "Any",
        "Daily / Casual",
        "Work / Office",
        "Date / Evening",
        "Formal / Event",
        "Outdoor / Sporty",
    ],
)
num_recs = st.sidebar.radio("Number of Recommendations", [1, 3, 5], index=1)

st.sidebar.markdown("---")
st.sidebar.header("â Add New Fragrance")

with st.sidebar.form("add_fragrance_form"):
  new_name = st.text_input("Fragrance Name", value=st.session_state["add_name"])
  new_brand = st.text_input(
      "Brand Name", value=st.session_state["add_brand"]
  )
  new_gender = st.selectbox(
      "Gender", ["Unisex", "Female", "Male", "Female-leaning", "Male-leaning"]
  )
  new_season = st.text_input(
      "Season/Weather", value=st.session_state["add_season"]
  )
  new_notes = st.text_input(
      "Notes (e.g. Top â Vanilla / Base â Musk)",
      value=st.session_state["add_notes"],
  )
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
      ],
  )

  form_col1, form_col2 = st.columns(2)
  with form_col1:
    submit_added = st.form_submit_button("Add to Collection")
  with form_col2:
    clear_form = st.form_submit_button("Clear Input")

  if clear_form:
    st.session_state["add_name"] = ""
    st.session_state["add_brand"] = ""
    st.session_state["add_season"] = "Fall, Winter"
    st.session_state["add_notes"] = ""
    st.rerun()

  if submit_added:
    if new_name and new_brand:
      new_item = {
          "name": new_name,
          "brand": new_brand,
          "gender": new_gender,
          "season": new_season,
          "notes": new_notes if new_notes else "Not specified",
          "category": new_cats if new_cats else ["Gourmand"],
      }
      st.session_state["fragrances_db"].append(new_item)
      save_persisted_data()
      st.sidebar.success(f"Added {new_name} successfully!")
    else:
      st.sidebar.error("Please provide at least a Name and Brand.")

# Handle Note Specific Search Query Results
if note_query:
  st.markdown("---")
  st.subheader(f"ð Note Search Results for: '{note_query}'")
  note_query_lower = note_query.lower()
  matching_notes = [
      f
      for f in st.session_state["fragrances_db"]
      if note_query_lower in f["notes"].lower()
  ]

  if not matching_notes:
    st.warning("No fragrances found containing that specific note.")
  else:
    for f in matching_notes:
      current_reaction = st.session_state["user_reactions"].get(f["name"])
      status_badge = (
          " â­ [Favorite]"
          if current_reaction == "fav"
          else (" ð [Disliked]" if current_reaction == "dislike" else "")
      )

      st.info(f"**{f['name']}** by *{f['brand']}*{status_badge}")
      st.write(f"**Gender:** {f['gender']} | **Season:** {f['season']}")
      st.write(f"**Category:** {', '.join(f['category'])}")
      st.caption(f"Notes: {f['notes']}")
      st.markdown("---")

# Handle Name/Brand Search Query
if search_query:
  st.markdown("---")
  st.subheader(f"ð Search Results for: '{search_query}'")
  query_lower = search_query.lower()
  matching_fragrances = [
      f
      for f in st.session_state["fragrances_db"]
      if query_lower in f["name"].lower()
      or query_lower in f["brand"].lower()
  ]

  if not matching_fragrances:
    st.warning("No fragrances found matching your search term.")
  else:
    for f in matching_fragrances:
      current_reaction = st.session_state["user_reactions"].get(f["name"])
      status_badge = (
          " â­ [Favorite]"
          if current_reaction == "fav"
          else (" ð [Disliked]" if current_reaction == "dislike" else "")
      )

      st.info(f"**{f['name']}** by *{f['brand']}*{status_badge}")
      st.write(f"**Gender:** {f['gender']} | **Season:** {f['season']}")
      st.write(f"**Category:** {', '.join(f['category'])}")
      st.caption(f"Notes: {f['notes']}")

      col1, col2, col3 = st.columns([1, 1, 4])
      with col1:
        if st.button("ð Love", key=f"search_fav_{f['name']}"):
          st.session_state["user_reactions"][f["name"]] = "fav"
          save_persisted_data()
          st.rerun()
      with col2:
        if st.button("ð Trash", key=f"search_dislike_{f['name']}"):
          st.session_state["user_reactions"][f["name"]] = "dislike"
          save_persisted_data()
          st.rerun()
      st.markdown("---")

if st.sidebar.button("â¨ Generate Recommendations", type="primary"):
  selected = get_top_fragrances(gender, weather, category, occasion, num_recs)

  st.markdown("---")
  st.subheader(f"ð Top {num_recs} Recommendation(s)")

  if not selected:
    st.warning(
        "No fragrances matched your exact filters (or they were marked as"
        " disliked). Try selecting 'Any' for some options."
    )
  else:
    for i, f in enumerate(selected, 1):
      current_reaction = st.session_state["user_reactions"].get(f["name"])
      status_badge = " â­ [Favorite]" if current_reaction == "fav" else ""

      st.success(
          f"**#{i} â {f['name']}** by *{f['brand']}*{status_badge}"
      )
      st.write(f"**Gender:** {f['gender']} | **Season:** {f['season']}")
      st.write(f"**Category:** {', '.join(f['category'])}")
      st.caption(f"Notes: {f['notes']}")

      col1, col2, col3 = st.columns([1, 1, 4])
      with col1:
        if st.button("ð Love", key=f"fav_{f['name']}_{i}"):
          st.session_state["user_reactions"][f["name"]] = "fav"
          save_persisted_data()
          st.rerun()
      with col2:
        if st.button("ð Trash", key=f"dislike_{f['name']}_{i}"):
          st.session_state["user_reactions"][f["name"]] = "dislike"
          save_persisted_data()
          st.rerun()
      st.markdown("---")

  pool = get_top_fragrances(
      gender,
      weather,
      category,
      occasion,
      min(30, len(st.session_state["fragrances_db"])),
  )
  combos = suggest_layering_combos(pool, num_combos=3)

  if combos:
    st.markdown("---")
    st.subheader("ð§ª Recommended Layering Combos")
    for i, (f1, f2, reason) in enumerate(combos, 1):
      st.info(
          f"**Combo #{i}**\n\nð¤ **Base / First:** {f1['name']}"
          f" ({f1['brand']})\n\nð¤ **Layer / Top:** {f2['name']}"
          f" ({f2['brand']})\n\nð¡ **Why it works:** {reason}"
      )
    st.caption(
        "Tip: Spray the richer/heavier fragrance first, then layer the lighter"
        " one on top."
    )
elif not search_query and not note_query:
  st.info(
      "Type a fragrance name or specific note in the sidebar search, adjust"
      " your filters, or click **Generate Recommendations** to explore!"
  )

# ==========================================
# FRAGRANCE ROULETTE
# ==========================================
st.markdown("---")
st.subheader("ð° Fragrance Roulette")
st.write(
    "The night is restlessâ¦ let the darkness choose your next offering."
)

r_col1, r_col2 = st.columns(2)
with r_col1:
  roulette_gender = st.selectbox(
      "Roulette Gender", ["Any", "Male", "Female", "Unisex"], key="roulette_gender"
  )
with r_col2:
  roulette_season = st.selectbox(
      "Roulette Season / Weather",
      [
          "Any",
          "Hot / Summer",
          "Warm / Mild",
          "Cool / Autumn",
          "Cold / Winter",
      ],
      key="roulette_season",
  )

if st.button("ð² Spin the Roulette", type="primary", key="spin_roulette_btn"):
  # Exclude scents worn in the last few SOTD entries
  recent_worn = set()
  for entry in st.session_state.get("sotd_history", [])[:5]:
    if entry.get("scents"):
      recent_worn.update(entry["scents"])
    elif entry.get("scent"):
      # handle old single-scent format and "A + B" strings
      for part in entry["scent"].split(" + "):
        recent_worn.add(part.strip())

  pool = []
  for f in st.session_state["fragrances_db"]:
    if st.session_state["user_reactions"].get(f["name"]) == "dislike":
      continue
    if f["name"] in recent_worn:
      continue
    if matches_gender(f, roulette_gender) and matches_weather(
        f, roulette_season
    ):
      pool.append(f)

  if not pool:
    st.warning(
        "No fragrances available matching those roulette criteria. Try"
        " loosening the gender or season."
    )
  else:
    chosen = random.choice(pool)
    current_reaction = st.session_state["user_reactions"].get(chosen["name"])
    status_badge = (
        " â­ [Favorite]"
        if current_reaction == "fav"
        else (" ð [Disliked]" if current_reaction == "dislike" else "")
    )

    # Floating Bats animation instead of balloons
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

    st.success("### ð©¸ The roulette has spoken...")
    st.markdown(f"## **{chosen['name']}**{status_badge}")
    st.markdown(f"### by *{chosen['brand']}*")
    st.write(f"**Gender:** {chosen['gender']}  |  **Season:** {chosen['season']}")
    st.write(f"**Category:** {', '.join(chosen['category'])}")
    st.caption(f"Notes: {chosen['notes']}")

    # Quick action buttons for the chosen scent
    rcol1, rcol2, rcol3 = st.columns([1, 1, 2])
    with rcol1:
      if st.button("ð Love it", key=f"roulette_fav_{chosen['name']}"):
        st.session_state["user_reactions"][chosen["name"]] = "fav"
        save_persisted_data()
        st.rerun()
    with rcol2:
      if st.button("ð Trash it", key=f"roulette_dislike_{chosen['name']}"):
        st.session_state["user_reactions"][chosen["name"]] = "dislike"
        save_persisted_data()
        st.rerun()

# Scent of the Day (SOTD) Section
st.markdown("---")
st.subheader("ð©¸ Scent of the Day (SOTD) Logger")
all_frag_names = [f["name"] for f in st.session_state["fragrances_db"]]

# Keep a place to pre-fill the multiselect when user picks a suggested combo
if "sotd_prefill" not in st.session_state:
  st.session_state["sotd_prefill"] = []

st.caption(
    "Select one fragrance for a single wear, or multiple for a layering combo."
)
sotd_choices = st.multiselect(
    "What are you wearing today? (select one or more)",
    options=all_frag_names,
    default=st.session_state["sotd_prefill"],
    placeholder="Choose fragrance(s)...",
    key="sotd_multiselect",
)

# Clear the prefill after it has been applied once
if st.session_state["sotd_prefill"]:
  st.session_state["sotd_prefill"] = []

# Auto-suggest a note when layering
default_note = ""
if len(sotd_choices) > 1:
  default_note = "Layered combo"

sotd_notes = st.text_input(
    "Optional comments/vibe for today:",
    value=default_note if default_note else "",
    placeholder="e.g. Perfect for a rainy gothic afternoon. / Layered for depth.",
    key="sotd_notes_input",
)

# Quick Layering Combo suggestions (based on favorites + good pairs)
with st.expander("ð§ª Quick Layering Combos (click to use)"):
  # Prefer favorites if any, otherwise sample from whole DB
  fav_names = [
      n for n, s in st.session_state["user_reactions"].items() if s == "fav"
  ]
  pool = [
      f
      for f in st.session_state["fragrances_db"]
      if f["name"] in fav_names
  ] if fav_names else st.session_state["fragrances_db"]

  if len(pool) < 2:
    pool = st.session_state["fragrances_db"]

  quick_combos = suggest_layering_combos(pool, num_combos=4)

  if not quick_combos:
    st.write("Not enough fragrances to suggest layering combos yet.")
  else:
    for i, (f1, f2, reason) in enumerate(quick_combos, 1):
      col_a, col_b = st.columns([4, 1])
      with col_a:
        st.markdown(
            f"**Combo {i}:** `{f1['name']}` + `{f2['name']}`  \n"
            f"*{reason}*"
        )
      with col_b:
        if st.button("Use", key=f"use_combo_{i}_{f1['name']}_{f2['name']}"):
          st.session_state["sotd_prefill"] = [f1["name"], f2["name"]]
          st.rerun()

if st.button("Log Today's Scent", type="primary"):
  if sotd_choices:
    today_date = datetime.date.today().strftime("%Y-%m-%d")
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
    if is_layering:
      st.success(
          f"Successfully logged layering combo: **{scent_display}** for today!"
      )
    else:
      st.success(f"Successfully logged **{scent_display}** for today!")
  else:
    st.warning("Please select at least one fragrance to log.")

if st.session_state["sotd_history"]:
  with st.expander("ð¦ View SOTD Journal History"):
    for i, entry in enumerate(st.session_state["sotd_history"]):
      layer_badge = " ð§ª [Layering]" if entry.get("is_layering") else ""
      notes_text = f" â {entry['notes']}" if entry.get("notes") else ""
      col_h, col_x = st.columns([6, 1])
      with col_h:
        st.write(
            f"**{entry['date']}**: ð¤ *{entry['scent']}*{layer_badge}{notes_text}"
        )
      with col_x:
        if st.button("â", key=f"del_sotd_{i}_{entry['date']}"):
          st.session_state["sotd_history"].pop(i)
          save_persisted_data()
          st.rerun()
    if st.button("Clear entire SOTD journal", key="clear_sotd_all"):
      st.session_state["sotd_history"] = []
      save_persisted_data()
      st.rerun()

# Collection & Data Management Expander (Export/Import + Reactions + Edit/Delete)
with st.expander("ð¤ Sanctuary Vault â Collection & Data Management"):
  st.write(
      f"ð Bottles in the vault: **{len(st.session_state['fragrances_db'])}**"
  )

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
    st.write(f"â­ **Cherished:** {', '.join(favs)}")
  if dislikes:
    st.write(f"ð **Banished:** {', '.join(dislikes)}")

  if st.button("Clear All Reactions", key="clear_all_rx"):
    st.session_state["user_reactions"] = {}
    save_persisted_data()
    st.rerun()

  st.markdown("---")
  st.subheader("âï¸ Edit or Banish a Fragrance")

  manage_names = [f["name"] for f in st.session_state["fragrances_db"]]
  selected_manage = st.selectbox(
      "Choose a bottle to edit or removeâ¦",
      ["â select â"] + manage_names,
      key="manage_select",
  )

  if selected_manage != "â select â":
    idx = next(
        (i for i, f in enumerate(st.session_state["fragrances_db"]) if f["name"] == selected_manage),
        None,
    )
    if idx is not None:
      frag = st.session_state["fragrances_db"][idx]
      gender_opts = ["Unisex", "Female", "Male", "Female-leaning", "Male-leaning"]
      g_idx = gender_opts.index(frag["gender"]) if frag["gender"] in gender_opts else 0

      with st.form(key=f"edit_form_{selected_manage}"):
        e_name = st.text_input("Name", value=frag["name"])
        e_brand = st.text_input("Brand", value=frag["brand"])
        e_gender = st.selectbox("Gender", gender_opts, index=g_idx)
        e_season = st.text_input("Season", value=frag["season"])
        e_notes = st.text_area("Notes", value=frag["notes"])
        cat_opts = ["Gourmand", "Sweet", "Floral", "Woody", "Oriental", "Fresh", "Fruity", "Spicy", "Citrus", "Aromatic", "Leather", "Oud", "Smoky", "Powdery"]
        e_cats = st.multiselect(
            "Categories",
            cat_opts,
            default=[c for c in frag.get("category", []) if c in cat_opts],
        )

        col_save, col_del = st.columns(2)
        with col_save:
          save_edit = st.form_submit_button("ð¾ Save Changes")
        with col_del:
          delete_it = st.form_submit_button("ð Banish Forever")

        if save_edit:
          st.session_state["fragrances_db"][idx] = {
              "name": e_name,
              "brand": e_brand,
              "gender": e_gender,
              "season": e_season,
              "notes": e_notes,
              "category": e_cats if e_cats else ["Gourmand"],
          }
          if e_name != selected_manage and selected_manage in st.session_state["user_reactions"]:
            st.session_state["user_reactions"][e_name] = st.session_state["user_reactions"].pop(selected_manage)
          save_persisted_data()
          st.success(f"Updated **{e_name}**")
          st.rerun()

        if delete_it:
          st.session_state["fragrances_db"].pop(idx)
          st.session_state["user_reactions"].pop(selected_manage, None)
          save_persisted_data()
          st.success(f"Banished **{selected_manage}** from the sanctuary.")
          st.rerun()

  st.markdown("---")
  st.subheader("ð¾ Backup & Restore the Vault")

  export_data = {
      "fragrances_db": st.session_state["fragrances_db"],
      "user_reactions": st.session_state["user_reactions"],
      "sotd_history": st.session_state["sotd_history"],
  }
  json_string = json.dumps(export_data, indent=4)

  st.download_button(
      label="ð¥ Export Vault as JSON",
      data=json_string,
      file_name="scented_dead_girl_backup.json",
      mime="application/json",
  )

  uploaded_file = st.file_uploader(
      "ð¤ Restore from Backup JSON", type=["json"]
  )
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
      st.success("The vault has been restored from the shadows.")
      st.rerun()
    except Exception as e:
      st.error(f"The ritual failed: {e}")
