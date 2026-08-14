import json
import random
import re
import streamlit as st

# ==========================================
# PAGE CONFIGURATION & CUSTOM GOTHIC THEME
# ==========================================
st.set_page_config(
    page_title="ScentedDeadGirl Fragrance Sanctuary",
    page_icon="💀",
    layout="centered",
)

# Custom Gothic Styling for ScentedDeadGirl Aesthetic (Black & Blue)
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;600;700&family=Cinzel+Decorative:wght@400;700&family=UnifrakturMaguntia&display=swap');

    /* Main app background & text */
    .stApp {
        background: linear-gradient(160deg, #020408 0%, #0a0f1a 40%, #050810 100%);
        color: #c8d8f0;
    }

    /* Headings - strong gothic feel */
    h1, h2, h3, h4 {
        color: #7eb8ff !important;
        font-family: 'Cinzel Decorative', 'Cinzel', serif !important;
        text-shadow: 0 0 8px rgba(60, 140, 255, 0.45), 2px 2px 4px rgba(0, 0, 0, 0.9);
        letter-spacing: 1px;
    }

    h1 {
        font-size: 2.4rem !important;
        border-bottom: 1px solid #1a3a6a;
        padding-bottom: 0.4rem;
    }

    /* Body text */
    p, .stMarkdown, .stCaption, label, .stText, .stInfo, .stSuccess, .stWarning {
        font-family: 'Cinzel', serif !important;
        color: #b8cce8 !important;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #03060c 0%, #0a1220 100%) !important;
        border-right: 1px solid #1a3050;
    }
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {
        color: #6aa8ff !important;
        font-family: 'Cinzel Decorative', 'Cinzel', serif !important;
    }

    /* Buttons */
    .stButton > button {
        background: linear-gradient(180deg, #0d1f3c 0%, #081428 100%) !important;
        color: #a8d0ff !important;
        border: 1px solid #2a5a9a !important;
        border-radius: 3px !important;
        font-family: 'Cinzel', serif !important;
        font-weight: 600 !important;
        letter-spacing: 0.5px;
        transition: all 0.25s ease;
        box-shadow: 0 0 6px rgba(40, 100, 200, 0.25);
    }
    .stButton > button:hover {
        background: linear-gradient(180deg, #143060 0%, #0c1e40 100%) !important;
        border-color: #4a90e0 !important;
        color: #e0f0ff !important;
        box-shadow: 0 0 14px rgba(60, 140, 255, 0.55);
    }
    .stButton > button:active {
        background: #0a1830 !important;
    }

    /* Primary / Generate button emphasis */
    .stButton > button[kind="primary"] {
        background: linear-gradient(180deg, #0e2a55 0%, #0a1c3a 100%) !important;
        border: 1px solid #3a7acc !important;
        color: #d0e8ff !important;
    }

    /* Text inputs & select boxes */
    .stTextInput > div > div > input,
    .stSelectbox > div > div > select,
    .stMultiSelect > div > div,
    .stTextArea > div > div > textarea {
        background-color: #0a1220 !important;
        color: #d0e4ff !important;
        border: 1px solid #1e4068 !important;
        border-radius: 3px !important;
        font-family: 'Cinzel', serif !important;
    }
    .stTextInput > div > div > input:focus,
    .stSelectbox > div > div > select:focus {
        border-color: #3a7acc !important;
        box-shadow: 0 0 8px rgba(60, 140, 255, 0.4) !important;
    }

    /* Radio & other controls */
    .stRadio label, .stCheckbox label {
        font-family: 'Cinzel', serif !important;
        color: #b0c8e8 !important;
    }

    /* Info / Success / Warning boxes */
    .stAlert {
        background-color: #0a1528 !important;
        border: 1px solid #1e4068 !important;
        color: #c0d8f0 !important;
        font-family: 'Cinzel', serif !important;
    }

    /* Expander */
    .streamlit-expanderHeader {
        background-color: #0a1424 !important;
        color: #8ab8ff !important;
        font-family: 'Cinzel', serif !important;
        border: 1px solid #1a3a60 !important;
    }

    /* Download button */
    .stDownloadButton > button {
        background: linear-gradient(180deg, #0d1f3c 0%, #081428 100%) !important;
        color: #a8d0ff !important;
        border: 1px solid #2a5a9a !important;
        font-family: 'Cinzel', serif !important;
    }

    /* File uploader */
    .stFileUploader {
        border: 1px dashed #1e4068 !important;
        background-color: #080e18 !important;
    }

    /* Horizontal rules */
    hr {
        border-color: #1a3050 !important;
    }

    /* Scrollbar (webkit) */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    ::-webkit-scrollbar-track {
        background: #050810;
    }
    ::-webkit-scrollbar-thumb {
        background: #1a3a60;
        border-radius: 4px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #2a5a9a;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# ==========================================
# FRAGRANCE DATABASE (Stored in Session State)
# ==========================================
if "fragrances_db" not in st.session_state:
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
              "Top – Pistachio, Almond / Heart – Jasmine, Heliotrope / Base –"
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
              "Top – Warm Spicy, Amber / Heart – Sweet, Powdery, Vanilla /"
              " Base – Chocolate, Musky, Cocoa"
          ),
          "category": ["Gourmand", "Sweet"],
      },
      {
          "name": "Al Rehab Chocomusk Marshmallow",
          "brand": "Al Rehab",
          "gender": "Unisex",
          "season": "Fall, Winter",
          "notes": (
              "Top – Marshmallow, Strawberry / Heart – Cocoa, Vanilla / Base –"
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
              "Top – Chocolate / Heart – Vanilla / Base – Musk"
          ),
          "category": ["Gourmand", "Sweet"],
      },
      {
          "name": "Al Rehab Cup Cake",
          "brand": "Al Rehab",
          "gender": "Unisex",
          "season": "Fall, Winter",
          "notes": (
              "Top – Citrus, Amber / Heart – Vanilla Cake / Base – Vanilla,"
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
              "Top – Vanilla / Heart – Creamy Sweet / Base – Vanilla, Musk"
          ),
          "category": ["Gourmand", "Sweet"],
      },
      {
          "name": "Al Rehab Royal Men",
          "brand": "Al Rehab",
          "gender": "Male",
          "season": "Fall, Winter",
          "notes": (
              "Top – Spicy, Citrus, Woody / Heart – Floral, Sweet / Base –"
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
              "Top – Fresh Citrus, Metallic / Heart – Floral / Base – Musk,"
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
              "Top – Citruses / Heart – Orchid, Jasmine, Vanilla, Caramel /"
              " Base – White Musk, Woody Notes, Vetiver"
          ),
          "category": ["Floral", "Sweet", "Gourmand"],
      },
      {
          "name": "Ameerat Al Arab Prive Rose",
          "brand": "Ameerat Al Arab",
          "gender": "Female",
          "season": "Fall, Spring",
          "notes": (
              "Top – Rose / Heart – Floral, Sweet / Base – Musk, Vanilla"
          ),
          "category": ["Floral", "Sweet"],
      },
      {
          "name": "Arabiyat Prestige Bahiya Garnet",
          "brand": "Arabiyat Prestige",
          "gender": "Female-leaning",
          "season": "Fall, Winter",
          "notes": (
              "Top – Cherry, Mandarin, Mango, Pear, Bergamot / Heart – Amber,"
              " Fig, Jasmine / Base – Amber, Vanilla, Sandalwood, Musk"
          ),
          "category": ["Fruity", "Oriental", "Sweet"],
      },
      {
          "name": "Arabiyat Prestige Nyla",
          "brand": "Arabiyat Prestige",
          "gender": "Female",
          "season": "Spring, Summer",
          "notes": (
              "Top – Coconut, Peach, Bergamot, Mandarin / Heart – Tiare, White"
              " Flowers, Jasmine, Rose / Base – White Musk, Patchouli"
          ),
          "category": ["Floral", "Fruity", "Fresh"],
      },
      {
          "name": "Arabiyat Prestige Nyla Vanielle",
          "brand": "Arabiyat Prestige",
          "gender": "Female",
          "season": "Fall, Winter",
          "notes": (
              "Top – Jasmine, Vanilla Bean / Heart – Caramel, Amber / Base –"
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
              "Top – Almond, Coffee, Ylang Ylang / Heart – Jasmine, Rose,"
              " Tuberose / Base – Vanilla, Musk, Tonka, Woody/Cacao"
          ),
          "category": ["Gourmand", "Floral", "Oriental"],
      },
      {
          "name": "Armaf Island Bliss",
          "brand": "Armaf",
          "gender": "Unisex",
          "season": "Spring, Summer",
          "notes": (
              "Top – Tropical Fruits, Coconut / Heart – Sweet / Base – Musk"
          ),
          "category": ["Fruity", "Fresh", "Sweet"],
      },
      {
          "name": "Armaf Odyssey Aqua",
          "brand": "Armaf",
          "gender": "Male",
          "season": "Spring, Summer",
          "notes": (
              "Top – Orange, Grapefruit, Artemisia / Heart – Mint, Lavender /"
              " Base – Ambroxan, Cypress, Patchouli"
          ),
          "category": ["Fresh", "Citrus", "Aromatic"],
      },
      {
          "name": "Armaf Odyssey Candee",
          "brand": "Armaf",
          "gender": "Female-leaning",
          "season": "Fall, Winter",
          "notes": (
              "Top – Strawberry, Raspberry, Peach, Bergamot / Heart – Caramel,"
              " Jasmine / Base – Patchouli, Musk, Amber"
          ),
          "category": ["Fruity", "Gourmand", "Sweet"],
      },
      {
          "name": "Armaf Odyssey Marshmallow",
          "brand": "Armaf",
          "gender": "Unisex",
          "season": "Spring, Fall, Winter",
          "notes": (
              "Top – Apple, Lemon, Coconut, Peony, Lily of the Valley / Heart –"
              " Strawberry, Peach, Raspberry, Apricot, Marshmallow, Orange"
              " Blossom / Base – Vanilla, Praline, Tonka, Amber, Musk, Mascarpone"
          ),
          "category": ["Gourmand", "Fruity", "Sweet"],
      },
      {
          "name": "Banat Dubai",
          "brand": "Le Chameau",
          "gender": "Female",
          "season": "Versatile to cooler",
          "notes": (
              "Top – Jasmine, Bergamot, Peony / Heart – Pineapple, Peach, Plum /"
              " Base – Musk, Patchouli, Sandalwood"
          ),
          "category": ["Floral", "Fruity"],
      },
      {
          "name": "Baraja Red 500",
          "brand": "Baraja",
          "gender": "Unisex/Male",
          "season": "Fall, Winter",
          "notes": (
              "Top – Red Fruits, Spices / Heart – Sweet Notes / Base – Woody,"
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
              "Top – Aldehydes, Heliotrope, Coconut, Vanilla / Heart – Vanilla,"
              " Mango / Base – White Musk, Coconut, Vanilla Absolute"
          ),
          "category": ["Gourmand", "Sweet"],
      },
      {
          "name": "Berries Cream Macaron",
          "brand": "Arabiyat Sugar",
          "gender": "Female",
          "season": "Spring–Fall",
          "notes": "Berry + cream macaron gourmand",
          "category": ["Gourmand", "Fruity", "Sweet"],
      },
      {
          "name": "Black Opinion",
          "brand": "Black Opinion",
          "gender": "Male/Unisex",
          "season": "Fall–Winter",
          "notes": "Dark, bold (woody/spicy/leather)",
          "category": ["Woody", "Spicy", "Leather"],
      },
      {
          "name": "Blue for Men Le Parfum",
          "brand": "Blue for Men",
          "gender": "Male/Unisex",
          "season": "Fall, Winter",
          "notes": (
              "Top – Cardamom / Heart – Lavender, Iris / Base – Vanilla,"
              " Oriental Woods"
          ),
          "category": ["Woody", "Oriental", "Spicy"],
      },
      {
          "name": "Caramel Chocolate Macaron",
          "brand": "Arabiyat Sugar",
          "gender": "Female/Unisex",
          "season": "Fall–Winter",
          "notes": "Caramel-chocolate-macaron gourmand",
          "category": ["Gourmand", "Sweet"],
      },
      {
          "name": "Club de Nuit Women",
          "brand": "Armaf",
          "gender": "Female",
          "season": "Spring, Fall",
          "notes": (
              "Top – Apple, Citrus / Heart – Rose, Jasmine / Base – Vanilla,"
              " Musk"
          ),
          "category": ["Floral", "Fruity", "Fresh"],
      },
      {
          "name": "Coconut Chiffon",
          "brand": "Arabiyat Sugar",
          "gender": "Female/Unisex",
          "season": "Spring–Summer",
          "notes": "Coconut + light cake/chiffon",
          "category": ["Gourmand", "Sweet", "Fresh"],
      },
      {
          "name": "Confections",
          "brand": "Paris Corner",
          "gender": "Female/Unisex",
          "season": "Fall–Winter",
          "notes": "Gourmand/sweet, confectionery-style",
          "category": ["Gourmand", "Sweet"],
      },
      {
          "name": "Dulzura",
          "brand": "Paris Corner",
          "gender": "Female",
          "season": "Fall–Winter",
          "notes": (
              "Top – Black pepper, buttermilk / Heart – Cake, vanilla, cream /"
              " Base – Amber, musk"
          ),
          "category": ["Gourmand", "Sweet"],
      },
      {
          "name": "Eclaire Banoffi",
          "brand": "Lattafa",
          "gender": "Unisex/Female",
          "season": "Fall–Winter",
          "notes": "Banana-toffee/éclair gourmand",
          "category": ["Gourmand", "Sweet"],
      },
      {
          "name": "Éclat Parfumerie Al Gazal",
          "brand": "Éclat Parfumerie",
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
              "Top – Cinnamon, Orange, Nutmeg / Heart – Vanilla Cream, Cognac,"
              " Cocoa / Base – Bourbon Vanilla, Cedarwood, Patchouli"
          ),
          "category": ["Gourmand", "Spicy", "Woody"],
      },
      {
          "name": "Elyssia Scarlet",
          "brand": "Riiffs",
          "gender": "Female",
          "season": "Spring–Summer / versatile",
          "notes": (
              "Top – Black Cherry, Pink Pepper / Heart – Leather, Cream, Benzoin"
              " / Base – Vanilla Absolute, Cashmeran, Amber, Iso E Super"
          ),
          "category": ["Fruity", "Leather", "Sweet"],
      },
      {
          "name": "Emir Pear Potion",
          "brand": "Paris Corner",
          "gender": "Unisex",
          "season": "Spring",
          "notes": (
              "Top – Pear, Apple / Heart – Caramel, Jasmine / Base –"
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
              "Top – Mango, Ginger, Lemon, Red Berries / Heart – Coumarin,"
              " Jasmine, Cedar / Base – Cypriol, Amber, Musk, Oud"
          ),
          "category": ["Fruity", "Oriental", "Woody"],
      },
      {
          "name": "Emper Boulevard of New York",
          "brand": "Le Chameau",
          "gender": "Unisex",
          "season": "Fall, Winter",
          "notes": (
              "Top – Roasted Coffee Beans / Heart – Praline, Rose / Base –"
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
          "season": "Spring–Summer / versatile",
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
          "season": "Spring–Summer / versatile",
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
          "name": "Fragrance World Crème of Clouds",
          "brand": "Fragrance World",
          "gender": "Unisex",
          "season": "Fall, Winter",
          "notes": (
              "Top – Vanilla, Chocolate, Burnt Sugar / Heart – Milk,"
              " Creamy/Coconut Milk, Whipped Cream / Base – Musk"
          ),
          "category": ["Gourmand", "Sweet"],
      },
      {
          "name": "French Avenue 8th Wonder",
          "brand": "French Avenue",
          "gender": "Unisex",
          "season": "Fall, Winter",
          "notes": (
              "Top – Cardamom, Pink Pepper, Candy Apple / Heart – Liquor, Dates,"
              " Boozy notes, Davana, Osmanthus / Base – Myrrh, Benzoin, Styrax,"
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
              "Top – Incense, Guaiac Wood, Saffron / Heart – Leather, Amberwood,"
              " Violet, Sugar Cane / Base – Smoke, Patchouli, Sandalwood, Woodsy"
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
              "Top – Blackberry, Black Currant, Rosemary, Bergamot / Heart –"
              " Raspberry, Vodka, Basil, Lily of the Valley / Base – Strawberry,"
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
              "Top – Nutella, Cardamom, Rum / Heart – Cocoa, Coconut, White"
              " Flowers, Lily of the Valley / Base – Sandalwood, Ambergris, Musk"
          ),
          "category": ["Gourmand", "Sweet"],
      },
      {
          "name": "Ghaliya",
          "brand": "Zakat",
          "gender": "Unisex/Female",
          "season": "Fall–Winter",
          "notes": "Rich oriental/oud-floral",
          "category": ["Oriental", "Floral", "Oud"],
      },
      {
          "name": "Gulf Orchid Cookie Bite",
          "brand": "Gulf Orchid",
          "gender": "Unisex",
          "season": "Fall, Winter",
          "notes": (
              "Top – Cookie, Butter / Heart – Vanilla, Musk / Base – Caramel,"
              " Amber"
          ),
          "category": ["Gourmand", "Sweet"],
      },
      {
          "name": "Gulf Orchid Piña Colada Musk Collection Body Spray",
          "brand": "Gulf Orchid",
          "gender": "Unisex",
          "season": "Spring, Summer",
          "notes": (
              "Top – Pineapple, Coconut / Heart – Tropical / Base – Musk"
          ),
          "category": ["Fruity", "Fresh", "Sweet"],
      },
      {
          "name": "Hawas Elixir",
          "brand": "Rasasi",
          "gender": "Unisex",
          "season": "Fall–Winter",
          "notes": (
              "Top – Mint, bergamot, artemisia / Heart – Dark chocolate,"
              " lavender, benzoin / Base – Vanilla, tonka bean, white musk"
          ),
          "category": ["Gourmand", "Fresh", "Sweet"],
      },
      {
          "name": "Heroes Energize",
          "brand": "Heroes",
          "gender": "Male",
          "season": "Spring, Summer",
          "notes": (
              "Top – Citrus, Aromatic Herbs / Heart – Light Spices / Base –"
              " Woods, Musk"
          ),
          "category": ["Fresh", "Citrus", "Aromatic"],
      },
      {
          "name": "Kandy Rush",
          "brand": "Kandy Rush",
          "gender": "Female/Unisex",
          "season": "Fall–Winter / casual year-round",
          "notes": "Sweet candy/gourmand",
          "category": ["Gourmand", "Sweet"],
      },
      {
          "name": "Khadlaj Cafe Latte",
          "brand": "Khadlaj",
          "gender": "Unisex",
          "season": "Fall, Winter",
          "notes": (
              "Top – Coffee, Sweet Almond, Milk / Heart – Vanilla, Ice Cream"
              " Accord, Amber / Base – Vanilla, Almond Cream, Caramel"
          ),
          "category": ["Gourmand", "Sweet"],
      },
      {
          "name": "Khadlaj Cream Velvet",
          "brand": "Khadlaj",
          "gender": "Unisex (leans feminine)",
          "season": "Fall, Winter",
          "notes": (
              "Top – Caramel, Butter / Heart – Tonka, Honey, Jasmine / Base –"
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
              "Top – Bergamot, Jasmine, Peony / Heart – Pineapple, Peach, Plum /"
              " Base – Musk, Sandalwood, Patchouli"
          ),
          "category": ["Floral", "Fruity", "Fresh"],
      },
      {
          "name": "Khadlaj Nuha Vanilla Pearl",
          "brand": "Khadlaj",
          "gender": "Female",
          "season": "Fall, Winter",
          "notes": (
              "Top – Blackcurrant, Strawberry, Freesia / Heart – Raspberry,"
              " Magnolia, Cashmere Wood / Base – Vanilla, Caramel, Moss"
          ),
          "category": ["Fruity", "Gourmand", "Floral"],
      },
      {
          "name": "Khadlaj Peach Velvet",
          "brand": "Khadlaj",
          "gender": "Female",
          "season": "Spring, Summer, Fall",
          "notes": (
              "Top – Guava, Peach, Nectarine / Heart – Vanilla, Ginger,"
              " Cinnamon, Amber / Base – Caramel, Musk, Sandalwood"
          ),
          "category": ["Fruity", "Gourmand", "Sweet"],
      },
      {
          "name": "Khadlaj Zainab Oil",
          "brand": "Khadlaj",
          "gender": "Unisex",
          "season": "Fall, Winter",
          "notes": (
              "Top – Bergamot, Gardenia, Almond / Heart – Coconut, Caramel /"
              " Base – Patchouli, Vanilla, Musk"
          ),
          "category": ["Gourmand", "Floral", "Sweet"],
      },
      {
          "name": "Khamrah Waha",
          "brand": "Lattafa",
          "gender": "Unisex",
          "season": "Fall–Winter",
          "notes": "Spicy-sweet (date, cinnamon, vanilla family)",
          "category": ["Oriental", "Spicy", "Sweet"],
      },
      {
          "name": "Khayali Vanilla Ayelet",
          "brand": "Khayali",
          "gender": "Unisex",
          "season": "Fall–Winter",
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
              "Top – Ginger, Mandarin, Pink Pepper / Heart – Lavender, Praline,"
              " Cacao, Jasmine / Base – Vanilla, Amber, Musk"
          ),
          "category": ["Gourmand", "Spicy", "Sweet"],
      },
      {
          "name": "Lattafa Ansaam Gold",
          "brand": "Lattafa",
          "gender": "Female/Unisex",
          "season": "Fall, Winter",
          "notes": (
              "Top – Mandarin Orange, Pear / Heart – Sweet Notes, Jasmine, Rose"
              " / Base – Musk, Vanilla, Raspberry"
          ),
          "category": ["Fruity", "Floral", "Sweet"],
      },
      {
          "name": "Lattafa Asad",
          "brand": "Lattafa",
          "gender": "Male",
          "season": "Fall, Winter",
          "notes": (
              "Top – Black Pepper, Tobacco, Pineapple / Heart – Patchouli,"
              " Coffee, Iris / Base – Vanilla, Amber, Dry Woods, Benzoin,"
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
              "Top – Rose Milk / Heart – Meringue, Almond / Base – Vanilla,"
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
              "Top – Watermelon, Peach, Orange / Heart – Coconut, White Flowers"
              " / Base – Musk, Vanilla, Amber"
          ),
          "category": ["Fruity", "Fresh", "Sweet"],
      },
      {
          "name": "Lattafa Dalal",
          "brand": "Lattafa",
          "gender": "Female",
          "season": "Spring",
          "notes": (
              "Top – Apple (Golden Delicious), Mandarin / Heart – Jasmine,"
              " Ylang-Ylang, Orange Flower / Base – Vanilla, Musk, Oakmoss"
          ),
          "category": ["Floral", "Fruity", "Fresh"],
      },
      {
          "name": "Lattafa Eclaire",
          "brand": "Lattafa",
          "gender": "Female",
          "season": "Fall, Winter",
          "notes": (
              "Top – Caramel, Milk, Sugar / Heart – Honey, White Flowers / Base"
              " – Vanilla, Praline, Musk"
          ),
          "category": ["Gourmand", "Sweet"],
      },
      {
          "name": "Lattafa Emaan",
          "brand": "Lattafa",
          "gender": "Female/Unisex",
          "season": "Fall, Winter",
          "notes": (
              "Top – Orange Blossom, Black Currant, Bergamot / Heart – Tuberose,"
              " Jasmine, Marigold / Base – Musk, Vanilla, Cedarwood, Patchouli"
          ),
          "category": ["Floral", "Fruity"],
      },
      {
          "name": "Lattafa Eternal Vanille",
          "brand": "Lattafa",
          "gender": "Unisex",
          "season": "Year-round (best Spring/Fall)",
          "notes": (
              "Top – Blackberry / Heart – Cocoapulse, Vanilla Caviar, Cacao /"
              " Base – Akigalawood, Tonka Bean, Ambrofix, Cedarwood, Benzoin,"
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
              "Top – Dark Fruits, Spices / Heart – Woody / Base – Vanilla, Musk"
          ),
          "category": ["Fruity", "Woody", "Spicy"],
      },
      {
          "name": "Lattafa Fakhar Gold",
          "brand": "Lattafa",
          "gender": "Unisex",
          "season": "Fall, Winter",
          "notes": (
              "Top – Tuberose, Salt / Heart – Amber, Tonka / Base – Cedarwood,"
              " Vetiver, Labdanum"
          ),
          "category": ["Floral", "Woody", "Oriental"],
      },
      {
          "name": "Lattafa Habik (Women’s version)",
          "brand": "Lattafa",
          "gender": "Female",
          "season": "Spring, Summer",
          "notes": (
              "Top – Pear, Bergamot / Heart – Lily of the Valley, Jasmine,"
              " Freesia / Base – Musk, Amber, Oakmoss"
          ),
          "category": ["Floral", "Fresh", "Fruity"],
      },
      {
          "name": "Lattafa Haya",
          "brand": "Lattafa",
          "gender": "Female",
          "season": "Fall, Winter",
          "notes": (
              "Top – Champagne, Strawberry, Rose, Tangerine, Blood Orange /"
              " Heart – Gardenia, Jasmine, Vanilla Orchid / Base – Amber,"
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
              "Top – Cinnamon / Heart – Tuberose, Jasmine, Incense / Base –"
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
              "Top – Lavender, Cinnamon, Mandarin / Heart – Iris, Benzoin,"
              " Cypress, Mahonial / Base – Vanilla, Tonka, Amber, Incense,"
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
              "Top – Spices, Pimento, Mandarin / Heart – Incense, Labdanum,"
              " Orange Blossom, Patchouli / Base – Tobacco, Praline, Amber, Tonka"
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
              "Top – Cinnamon, Nutmeg, Bergamot / Heart – Dates, Praline,"
              " Tuberose, Mahonial / Base – Vanilla, Tonka Bean, Amberwood,"
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
              "Top – Cinnamon, Cardamom, Ginger / Heart – Praline, Candied"
              " Fruits, White Flowers / Base – Coffee, Vanilla, Tonka Bean,"
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
              "Top – Anise / Heart – Caramel / Base – Vanilla, Tonka Bean, Musk"
          ),
          "category": ["Gourmand", "Sweet"],
      },
      {
          "name": "Lattafa Mayar Cherry Intense",
          "brand": "Lattafa",
          "gender": "Female",
          "season": "Fall, Winter",
          "notes": (
              "Top – Strawberry, Bergamot / Heart – Cherry Jam, Cacao / Base –"
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
              "Top – Blackcurrant, Apricot, Pineapple / Heart – Magnolia,"
              " Cyclamen, Jasmine, Orange Blossom, Rose / Base – Vanilla,"
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
              "Top – Red Berries, Mandarin Orange / Heart – Vanilla, Cacao,"
              " Rose / Base – Sugar, Tonka Bean, Amber, Musk"
          ),
          "category": ["Gourmand", "Fruity", "Sweet"],
      },
      {
          "name": "Lattafa Nebras Elixir",
          "brand": "Lattafa",
          "gender": "Unisex",
          "season": "Fall, Winter, Mild Spring",
          "notes": (
              "Top – Milk Candy, Whipped Cream / Heart – Sugar Cane, Heliotrope"
              " / Base – Vanilla, Ambroxan, Musk"
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
              "Top – Mango, Grapefruit, Lemon, Ginger / Heart – Jasmine,"
              " Cedarwood, Violet / Base – Woodsy notes, Ambergris, Benzoin,"
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
              "Top – Rose, Saffron, Pimento / Heart – Agarwood (Oud), Caramel,"
              " Floral Notes, Patchouli / Base – Woody Notes, Amber, Resins,"
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
              "Top – Pineapple, Saffron / Heart – Balsam Fir, Jasmine / Base –"
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
              "Top – Coconut, Pineapple, Citruses / Heart – Ylang-Ylang,"
              " Frangipani, Jasmine / Base – Vanilla, Musk, Sandalwood, Sweet"
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
              "Top – Apple, Citrus / Heart – Floral / Base – Sweet, Woody"
          ),
          "category": ["Fruity", "Woody", "Fresh"],
      },
      {
          "name": "Lattafa Raneen",
          "brand": "Lattafa",
          "gender": "Female",
          "season": "Fall, Winter",
          "notes": (
              "Top – Fruity, Sweet / Heart – Floral / Base – Vanilla, Musk"
          ),
          "category": ["Floral", "Fruity", "Sweet"],
      },
      {
          "name": "Lattafa Rave Now (for Women)",
          "brand": "Lattafa",
          "gender": "Female",
          "season": "Spring, Fall",
          "notes": (
              "Top – Red Fruits, Orange / Heart – Marshmallow, Jasmine, Lily of"
              " the Valley / Base – Vanilla, Musk, Moss"
          ),
          "category": ["Fruity", "Gourmand", "Floral"],
      },
      {
          "name": "Lattafa Rave Now Intense",
          "brand": "Lattafa",
          "gender": "Male/Unisex",
          "season": "Spring, Fall",
          "notes": (
              "Top – Cucumber, Watermelon, Tangerine / Heart – Basil, Sage /"
              " Base – Sandalwood, Leather, Cedar"
          ),
          "category": ["Fresh", "Woody", "Aromatic"],
      },
      {
          "name": "Lattafa Sakeena",
          "brand": "Lattafa",
          "gender": "Female/Unisex",
          "season": "Fall, Winter",
          "notes": (
              "Top – Passionfruit, Mandarin Orange, Ozonic Notes / Heart –"
              " Raspberry, Rose, Orange Blossom, Sea Salt / Base – Toffee,"
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
              "Top – Caramel, Bitter Almond, Apricot, Pink Pepper / Heart –"
              " Honey, Rhubarb, White Flowers, Rose / Base – Leather, Vanilla,"
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
              "Top – Saffron, Bergamot / Heart – Plum Liquor, Cinnamon / Base –"
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
              "Top – Cupcake / Heart – Sugar Frosting, Almond, Cinnamon / Base"
              " – Butter, Vanilla, Musk"
          ),
          "category": ["Gourmand", "Sweet"],
      },
      {
          "name": "Lattafa Whipped Pleasure (Give Me Gourmand)",
          "brand": "Lattafa",
          "gender": "Female",
          "season": "Fall, Winter",
          "notes": (
              "Top – Caramel, Popcorn, Salted Caramel / Heart – Milk, Jasmine /"
              " Base – Tonka, Benzoin, Musk, Ambrofix"
          ),
          "category": ["Gourmand", "Sweet"],
      },
      {
          "name": "Lattafa Yara Candy Body Spray",
          "brand": "Lattafa",
          "gender": "Female",
          "season": "Fall, Winter",
          "notes": (
              "Top – Candy, Sweet / Heart – Fruity / Base – Vanilla, Musk"
          ),
          "category": ["Gourmand", "Sweet", "Fruity"],
      },
      {
          "name": "Lattafa Yara Tous",
          "brand": "Lattafa",
          "gender": "Female",
          "season": "Versatile",
          "notes": (
              "Top – Fruity, Sweet / Heart – Floral / Base – Vanilla, Musk"
          ),
          "category": ["Floral", "Fruity", "Sweet"],
      },
      {
          "name": "Love & Peace",
          "brand": "Lattafa",
          "gender": "Unisex/Female",
          "season": "Spring–Fall",
          "notes": "Soft floral, musky, or peaceful sweet",
          "category": ["Floral", "Sweet"],
      },
      {
          "name": "Maison Alhambra Luxe Chic",
          "brand": "Maison Alhambra",
          "gender": "Female/Unisex",
          "season": "Spring, Fall",
          "notes": (
              "Top – Tangerine, Freesia / Heart – Lily of the Valley, Jasmine,"
              " Rose / Base – Musk, Sandalwood, Amber"
          ),
          "category": ["Floral", "Fresh"],
      },
      {
          "name": "Maison Asrar Vanilla Aura",
          "brand": "Maison Asrar",
          "gender": "Female/Unisex",
          "season": "Fall, Winter",
          "notes": (
              "Top – Vanilla / Heart – Creamy Sweet / Base – Vanilla, Musk"
          ),
          "category": ["Gourmand", "Sweet"],
      },
      {
          "name": "Maison Asrar Vanilla Seduction",
          "brand": "Maison Asrar",
          "gender": "Female/Unisex",
          "season": "Fall, Winter",
          "notes": (
              "Top – Plum, Jasmine, Lily of the Valley / Heart – Vanilla,"
              " Brown Sugar, Caramel / Base – Tonka, Patchouli, Amber, Musk"
          ),
          "category": ["Gourmand", "Floral", "Sweet"],
      },
      {
          "name": "Majestic Supreme",
          "brand": "Le Falcone",
          "gender": "Women/Unisex",
          "season": "Fall–Winter / versatile",
          "notes": (
              "Top – Rose, peony, pink pepper / Heart – Raspberry blossom,"
              " jasmine / Base – Amber, papyrus, tonka, vanilla"
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
          "season": "Spring–Summer / year-round",
          "notes": (
              "Top – Mango, nutmeg, clove / Heart – Leather, saffron, amber,"
              " moss / Base – Akigalawood, patchouli, vetiver, cypriol"
          ),
          "category": ["Fruity", "Woody", "Spicy"],
      },
      {
          "name": "Mango Ice",
          "brand": "Gulf Orchid",
          "gender": "Unisex",
          "season": "Spring–Summer",
          "notes": "Fruity mango with cool/icy facets",
          "category": ["Fruity", "Fresh"],
      },
      {
          "name": "Mayar",
          "brand": "Lattafa",
          "gender": "Female",
          "season": "Spring, Summer",
          "notes": (
              "Top – Lychee, Raspberry, Violet Leaf / Heart – Peony, White"
              " Rose, Jasmine / Base – Musk, Vanilla"
          ),
          "category": ["Floral", "Fruity", "Fresh"],
      },
      {
          "name": "Mayar Natural Intense Body Spray",
          "brand": "Mayar",
          "gender": "Female",
          "season": "Fall, Winter",
          "notes": (
              "Top – Sweet Gourmand / Heart – Vanilla / Base – Musk"
          ),
          "category": ["Gourmand", "Sweet"],
      },
      {
          "name": "Melt Cafe Bliss",
          "brand": "Mamlakat Al Oud / Fragrance World",
          "gender": "Unisex",
          "season": "Fall, Winter",
          "notes": (
              "Top – Black Coffee, Amaretto Liquor / Heart – Vanilla Ice Cream,"
              " Speculoos / Base – Vanilla Pods, Brown Sugar, Grey Amber"
          ),
          "category": ["Gourmand", "Sweet"],
      },
      {
          "name": "Melt Crème Caramel",
          "brand": "Mamlakat Al Oud",
          "gender": "Unisex (leans feminine)",
          "season": "Fall, Winter",
          "notes": (
              "Top – Caramel, Vanilla Flower / Heart – Dulce de Leche, Cotton"
              " Candy, Frangipani, White Flowers / Base – Vanilla Pod, Tonka"
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
              "Top – Strawberry, Blackberry (or Caramel/Milk) / Heart –"
              " Jasmine, Rose, Marshmallow, Vanilla, Honey / Base – Vanilla,"
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
              "Top – Vanilla (woody tones), Lavender, Cacao, Ginger / Heart –"
              " Vanilla Caviar / Base – Vanilla Absolute"
          ),
          "category": ["Gourmand", "Sweet"],
      },
      {
          "name": "Melt Velvet Breeze",
          "brand": "Mamlakat Al Oud",
          "gender": "Unisex",
          "season": "Fall, Winter",
          "notes": (
              "Top – Italian Bergamot, Pistachio Gelato, Hazelnut, Sweet Rum,"
              " Cardamom / Heart – Geranium, White Peony, Muguet, Jasmine /"
              " Base – Amber, Musk, Woody Notes"
          ),
          "category": ["Gourmand", "Floral", "Woody"],
      },
      {
          "name": "Miss Armaf Mystique",
          "brand": "Armaf",
          "gender": "Female",
          "season": "Fall, Winter",
          "notes": (
              "Top – Pear, Tangerine, Bergamot, Orange / Heart – Vanilla,"
              " Strawberry, Mimosa, Rose, Ylang Ylang, Jasmine, Passionfruit /"
              " Base – Vanilla, Coffee, Tonka Bean, Patchouli, Vetiver"
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
              "Top – Brown Sugar, Caramel, Biscuit / Heart – Toffee, Vanilla"
              " Bean, Amber / Base – White Musk, Praline"
          ),
          "category": ["Gourmand", "Sweet"],
      },
      {
          "name": "Obsidian",
          "brand": "French Avenue",
          "gender": "Unisex/Male",
          "season": "Fall–Winter",
          "notes": "Dark, woody, or smoky-oriental",
          "category": ["Woody", "Oriental", "Smoky"],
      },
      {
          "name": "Panache Angel Dust",
          "brand": "Khadlaj",
          "gender": "Female",
          "season": "Spring–Fall / versatile",
          "notes": "Soft, powdery, musk-vanilla / “angelic”",
          "category": ["Floral", "Sweet", "Powdery"],
      },
      {
          "name": "Paris Corner Eshal Vanilla",
          "brand": "Paris Corner",
          "gender": "Female/Unisex",
          "season": "Fall, Winter",
          "notes": (
              "Top – Sugar, Sweet Notes / Heart – Rose, Jasmine / Base –"
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
              "Top – Davana, Bergamot, Pink Pepper / Heart – Agarwood (Oud),"
              " Amber, Rosemary / Base – Leather, Vetiver, Musk"
          ),
          "category": ["Woody", "Oud", "Spicy"],
      },
      {
          "name": "Paris Corner Marshmallow Blush",
          "brand": "Paris Corner",
          "gender": "Female/Unisex",
          "season": "Fall, Winter",
          "notes": (
              "Top – Marshmallow, Sweet / Heart – Fruity / Base – Vanilla, Musk"
          ),
          "category": ["Gourmand", "Sweet", "Fruity"],
      },
      {
          "name": "Paris Corner Qissa Delicious",
          "brand": "Paris Corner",
          "gender": "Female",
          "season": "Fall, Winter",
          "notes": (
              "Top – Whipped Cream, Dark Chocolate, Orange / Heart –"
              " Marshmallow, Coconut, Jasmine / Base – Vanilla, White Musk"
          ),
          "category": ["Gourmand", "Sweet"],
      },
      {
          "name": "Pecan Butter Cookie",
          "brand": "Arabiyat Sugar",
          "gender": "Unisex/Female",
          "season": "Fall–Winter",
          "notes": (
              "Top – Pecan, coconut milk, butter / Heart – Hazelnut, almond,"
              " roasted nuts / Base – Hazelnut, vanilla, ambergris"
          ),
          "category": ["Gourmand", "Sweet"],
      },
      {
          "name": "Phlur Heavy Cream",
          "brand": "Phlur",
          "gender": "Unisex",
          "season": "Fall, Winter",
          "notes": (
              "Top – Marshmallow, Sugar, Citrus / Heart – Coconut, Jasmine /"
              " Base – Whipped Cream, Vanilla, Caramel"
          ),
          "category": ["Gourmand", "Sweet"],
      },
      {
          "name": "Phlur Vanilla Skin",
          "brand": "Phlur",
          "gender": "Unisex (female-leaning)",
          "season": "Fall, Winter",
          "notes": (
              "Top – Sugar, Pink Pepper, Apple / Heart – Cashmere Wood, Jasmine,"
              " Lily / Base – Vanilla, Sandalwood, Agarwood, Benzoin"
          ),
          "category": ["Gourmand", "Woody", "Sweet"],
      },
      {
          "name": "Pink Velvet",
          "brand": "Maison Alhambra",
          "gender": "Female",
          "season": "Spring–Fall",
          "notes": "Soft, powdery, rosy, or gourmand-pink",
          "category": ["Floral", "Sweet", "Powdery"],
      },
      {
          "name": "Pink Yara / Yara Pink",
          "brand": "Lattafa",
          "gender": "Female",
          "season": "Spring–Summer",
          "notes": (
              "Top – Orchid, heliotrope, tangerine / Heart – Gourmand accord,"
              " tropical fruits / Base – Vanilla, musk, sandalwood"
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
              "Top – Apple, mint / Heart – Geranium, cinnamon, lavender / Base"
              " – Vanilla, Peru balsam, cedarwood, guaiac wood"
          ),
          "category": ["Fresh", "Woody", "Spicy"],
      },
      {
          "name": "Rasasi Hawas Diva",
          "brand": "Rasasi",
          "gender": "Female",
          "season": "Fall, Winter",
          "notes": (
              "Top – Red Fruits, Rhubarb, Lychee / Heart – Rose, Frankincense,"
              " Cedar / Base – Vanilla, Musk, Ambergris"
          ),
          "category": ["Fruity", "Floral", "Woody"],
      },
      {
          "name": "Rasasi Hawas Eclat (Eclat Hawas)",
          "brand": "Rasasi",
          "gender": "Female",
          "season": "Spring, Fall",
          "notes": (
              "Top – Litchi/Lychee, Bergamot, Pear, Pistachio / Heart – Rose,"
              " Incense / Base – Vanilla, Amber, Musk, Woody Notes"
          ),
          "category": ["Fruity", "Floral", "Woody"],
      },
      {
          "name": "Rasasi Hawas Ice",
          "brand": "Rasasi",
          "gender": "Male",
          "season": "Versatile",
          "notes": (
              "Top – Apple, Italian Lemon, Sicilian Bergamot, Star Anise /"
              " Heart – Plum, Orange Blossom, Cardamom / Base – Musk, Moss,"
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
              "Top – Pink Pepper, Saffron, Pear / Heart – Rose, Frankincense,"
              " White Flowers / Base – Blonde Woods, Vanilla, Amber, Musk"
          ),
          "category": ["Floral", "Woody", "Spicy"],
      },
      {
          "name": "Rasasi Hawas Pink",
          "brand": "Rasasi",
          "gender": "Female",
          "season": "Fall, Winter",
          "notes": (
              "Top – Cinnamon, Nutmeg, Neroli / Heart – Marshmallow, Tuberose,"
              " Orange Blossom / Base – Cotton Candy, Vanilla, Tonka Bean"
          ),
          "category": ["Gourmand", "Floral", "Sweet"],
      },
      {
          "name": "Red Velvet",
          "brand": "Armaf Delights",
          "gender": "Female/Unisex",
          "season": "Fall, Winter",
          "notes": (
              "Top – Strawberry, Lemon / Heart – Whipped Sugar, Sugarberry,"
              " Frangipani / Base – Vanilla Bean, Musk, Amber"
          ),
          "category": ["Gourmand", "Fruity", "Sweet"],
      },
      {
          "name": "Rizz Tiramisu Candy",
          "brand": "Rizz",
          "gender": "Female",
          "season": "Spring, Fall",
          "notes": (
              "Top – Bergamot / Heart – Blackcurrant, Strawberry Milk / Base –"
              " Musk, Vanilla"
          ),
          "category": ["Gourmand", "Fruity", "Sweet"],
      },
      {
          "name": "Safa by Nusuk",
          "brand": "Nusuk",
          "gender": "Unisex/Female",
          "season": "Spring–Summer / versatile",
          "notes": (
              "Top – Marshmallow, Strawberry, Lemon / Heart – Coconut, Sugar,"
              " Nectarine / Base – Vanilla, Musk, Ambroxan"
          ),
          "category": ["Gourmand", "Fruity", "Sweet"],
      },
      {
          "name": "Sahari Ghubar Al Dhahab",
          "brand": "Sahari",
          "gender": "Unisex",
          "season": "Fall, Winter",
          "notes": (
              "Top – Cinnamon, Pear, Mandarin, Floral notes / Heart – Jasmine"
              " Sambac, Orange Blossom / Base – White Musk, Vanilla, Tonka Bean,"
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
          "season": "Spring–Summer",
          "notes": (
              "Top – Heliotrope, orchid, tangerine / Heart – Gourmand accord,"
              " tropical fruits / Base – Vanilla, musk, sandalwood"
          ),
          "category": ["Floral", "Gourmand", "Fruity"],
      },
      {
          "name": "Spectre / Sceptre Malachite",
          "brand": "Maison Alhambra",
          "gender": "Unisex",
          "season": "Spring–Summer",
          "notes": (
              "Top – Green tangerine, bergamot, blackcurrant / Heart –"
              " Aromatic + spicy notes, lavender, pink pepper, jasmine / Base –"
              " Amber, musk, woody notes, vetiver"
          ),
          "category": ["Fresh", "Aromatic", "Woody"],
      },
      {
          "name": "Strawberry Tres Leches",
          "brand": "Arabiyat Sugar",
          "gender": "Female",
          "season": "Spring–Summer / year-round",
          "notes": "Strawberry + milky cake gourmand",
          "category": ["Gourmand", "Fruity", "Sweet"],
      },
      {
          "name": "Sugar Crown",
          "brand": "Lattafa",
          "gender": "Female/Unisex",
          "season": "Fall–Winter",
          "notes": "Sweet/sugar gourmand",
          "category": ["Gourmand", "Sweet"],
      },
      {
          "name": "Sugar Me Dulce de Leche",
          "brand": "Maison Alhambra",
          "gender": "Unisex/Female",
          "season": "Fall–Winter",
          "notes": "Dulce de leche / caramel-vanilla gourmand",
          "category": ["Gourmand", "Sweet"],
      },
      {
          "name": "Sweet Surrender",
          "brand": "Mahajan",
          "gender": "Female",
          "season": "Fall–Winter / versatile",
          "notes": "Soft sweet/gourmand",
          "category": ["Gourmand", "Sweet"],
      },
      {
          "name": "Sweet Surrender Pink Parfait",
          "brand": "Mahajan",
          "gender": "Female",
          "season": "Spring–Summer / year-round",
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
          "season": "Versatile (Spring–Summer preferred)",
          "notes": (
              "Top – Ginger, Calabrian Bergamot, Lemon, Orange Blossom / Heart"
              " – Musk, Rose Petals, Tuberose / Base – Vanilla Bean, Amberwood,"
              " Clearwood"
          ),
          "category": ["Floral", "Fresh", "Woody"],
      },
      {
          "name": "The King",
          "brand": "Ali",
          "gender": "Male",
          "season": "Fall–Winter / versatile",
          "notes": "Masculine woody or oriental",
          "category": ["Woody", "Oriental"],
      },
      {
          "name": "Toffee Ganache",
          "brand": "Arabiyat Sugar",
          "gender": "Unisex",
          "season": "Fall–Winter",
          "notes": "Toffee/chocolate gourmand",
          "category": ["Gourmand", "Sweet"],
      },
      {
          "name": "Valentine Milano",
          "brand": "Valentine",
          "gender": "Unisex",
          "season": "Fall, Winter",
          "notes": (
              "Top – Raspberry, Peach, Bergamot / Heart – Rose, Jasmine, Orange"
              " Blossom / Base – Vanilla, Amber, Woods"
          ),
          "category": ["Floral", "Fruity", "Sweet"],
      },
      {
          "name": "Valentine Nero Xtravagant",
          "brand": "Valentine (Urban Collection)",
          "gender": "Male / Unisex (leans masculine)",
          "season": "Fall, Winter (versatile)",
          "notes": (
              "Top – Calabrian Bergamot, Espresso Coffee Accord / Heart –"
              " Coffee / Base – Vetiver"
          ),
          "category": ["Woody", "Fresh", "Aromatic"],
      },
      {
          "name": "Vanilla Addiction",
          "brand": "Gulf Orchid",
          "gender": "Unisex/Female",
          "season": "Fall–Winter",
          "notes": "Vanilla-forward gourmand",
          "category": ["Gourmand", "Sweet"],
      },
      {
          "name": "Vanilla Dunes",
          "brand": "Khadlaj",
          "gender": "Unisex",
          "season": "Autumn, Winter",
          "notes": (
              "Top – Vanilla, Cinnamon, Cardamom, Bergamot / Heart – Orange"
              " Blossom, Guaiac Wood, Bourbon / Base – Praline, Amber, Musk"
          ),
          "category": ["Gourmand", "Spicy", "Woody"],
      },
      {
          "name": "Yara Elixir",
          "brand": "Lattafa",
          "gender": "Female",
          "season": "Fall, Winter, Cool Spring Days",
          "notes": (
              "Top – Strawberry S'mores, Black Currant / Heart – Jasmine,"
              " Orange Blossom / Base – Vanilla, Caramel, Amber, Musk"
          ),
          "category": ["Gourmand", "Floral", "Sweet"],
      },
      {
          "name": "Zenith",
          "brand": "Riiffs",
          "gender": "Unisex",
          "season": "Spring–Summer / versatile",
          "notes": (
              "Top – Coconut, Vanilla, Cream / Heart – Rum, Saffron / Base –"
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
              "Top – Rhubarb, Bergamot, Grapefruit, Nutmeg / Heart – Rose,"
              " Jasmine / Base – Musk, Vanilla, Vetiver, Ambergris"
          ),
          "category": ["Floral", "Fruity", "Fresh"],
      },
      {
          "name": "Zimaya Hawwa Red",
          "brand": "Zimaya",
          "gender": "Female",
          "season": "Fall, Winter",
          "notes": (
              "Top – Cassis, Strawberry, Raspberry, Orange / Heart – Black"
              " Currant, Grapefruit, Peach, Lily / Base – Musk, Vanilla,"
              " Patchouli"
          ),
          "category": ["Fruity", "Floral", "Sweet"],
      },
  ]

# Initialize Reactions Database & SOTD History
if "user_reactions" not in st.session_state:
  st.session_state["user_reactions"] = {}

if "sotd_history" not in st.session_state:
  st.session_state["sotd_history"] = []

# Session states for clearing inputs explicitly
if "search_input" not in st.session_state:
  st.session_state["search_input"] = ""

if "note_search_input" not in st.session_state:
  st.session_state["note_search_input"] = ""

if "add_name" not in st.session_state:
  st.session_state["add_name"] = ""
if "add_brand" not in st.session_state:
  st.session_state["add_brand"] = ""
if "add_season" not in st.session_state:
  st.session_state["add_season"] = "Fall, Winter"
if "add_notes" not in st.session_state:
  st.session_state["add_notes"] = ""

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
    return fg in ["Male", "Male-leaning", "Unisex"]
  if preferred == "Female":
    return fg in ["Female", "Female-leaning", "Unisex"]
  if preferred == "Unisex":
    return fg in ["Unisex", "Male-leaning", "Female-leaning"]
  return True


def matches_weather(fragrance: dict, weather: str) -> bool:
  season = fragrance["season"].lower()
  if weather == "Any":
    return True
  if weather == "Hot / Summer":
    return any(x in season for x in ["spring", "summer", "versatile", "year-round"])
  if weather == "Warm / Mild":
    return any(
        x in season
        for x in ["spring", "fall", "autumn", "versatile", "year-round", "mild"]
    )
  if weather == "Cool / Autumn":
    return any(
        x in season
        for x in ["fall", "autumn", "winter", "cooler", "versatile", "year-round"]
    )
  if weather == "Cold / Winter":
    return any(
        x in season for x in ["fall", "winter", "cooler", "autumn", "versatile"]
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
  elif weather == "Hot / Summer":
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
  elif weather == "Cold / Winter":
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
st.title("💀 ScentedDeadGirl 🖤")
st.write(
    "Welcome to your dark sanctuary of scent! Filter your collection, rate your"
    " bottles, log your Scent of the Day, and discover custom layering"
    " combinations."
)

st.sidebar.header("🔍 Search Your Collection")
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

# Note Specific Search Option
st.sidebar.markdown("---")
st.sidebar.header("🔎 Search by Specific Note")
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
st.sidebar.header("🎯 Filter Options")

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
st.sidebar.header("➕ Add New Fragrance")

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
      "Notes (e.g. Top – Vanilla / Base – Musk)",
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
      st.sidebar.success(f"Added {new_name} successfully!")
    else:
      st.sidebar.error("Please provide at least a Name and Brand.")

# Handle Note Specific Search Query Results
if note_query:
  st.markdown("---")
  st.subheader(f"🔎 Note Search Results for: '{note_query}'")
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
          " ⭐ [Favorite]"
          if current_reaction == "fav"
          else (" 👎 [Disliked]" if current_reaction == "dislike" else "")
      )

      st.info(f"**{f['name']}** by *{f['brand']}*{status_badge}")
      st.write(f"**Gender:** {f['gender']} | **Season:** {f['season']}")
      st.write(f"**Category:** {', '.join(f['category'])}")
      st.caption(f"Notes: {f['notes']}")
      st.markdown("---")

# Handle Name/Brand Search Query
if search_query:
  st.markdown("---")
  st.subheader(f"🔍 Search Results for: '{search_query}'")
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
          " ⭐ [Favorite]"
          if current_reaction == "fav"
          else (" 👎 [Disliked]" if current_reaction == "dislike" else "")
      )

      st.info(f"**{f['name']}** by *{f['brand']}*{status_badge}")
      st.write(f"**Gender:** {f['gender']} | **Season:** {f['season']}")
      st.write(f"**Category:** {', '.join(f['category'])}")
      st.caption(f"Notes: {f['notes']}")

      col1, col2, col3 = st.columns([1, 1, 4])
      with col1:
        if st.button("👍 Love", key=f"search_fav_{f['name']}"):
          st.session_state["user_reactions"][f["name"]] = "fav"
          st.rerun()
      with col2:
        if st.button("👎 Trash", key=f"search_dislike_{f['name']}"):
          st.session_state["user_reactions"][f["name"]] = "dislike"
          st.rerun()
      st.markdown("---")

if st.sidebar.button("✨ Generate Recommendations", type="primary"):
  selected = get_top_fragrances(gender, weather, category, occasion, num_recs)

  st.markdown("---")
  st.subheader(f"🏆 Top {num_recs} Recommendation(s)")

  if not selected:
    st.warning(
        "No fragrances matched your exact filters (or they were marked as"
        " disliked). Try selecting 'Any' for some options."
    )
  else:
    for i, f in enumerate(selected, 1):
      current_reaction = st.session_state["user_reactions"].get(f["name"])
      status_badge = " ⭐ [Favorite]" if current_reaction == "fav" else ""

      st.success(
          f"**#{i} — {f['name']}** by *{f['brand']}*{status_badge}"
      )
      st.write(f"**Gender:** {f['gender']} | **Season:** {f['season']}")
      st.write(f"**Category:** {', '.join(f['category'])}")
      st.caption(f"Notes: {f['notes']}")

      col1, col2, col3 = st.columns([1, 1, 4])
      with col1:
        if st.button("👍 Love", key=f"fav_{f['name']}_{i}"):
          st.session_state["user_reactions"][f["name"]] = "fav"
          st.rerun()
      with col2:
        if st.button("👎 Trash", key=f"dislike_{f['name']}_{i}"):
          st.session_state["user_reactions"][f["name"]] = "dislike"
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
    st.subheader("🧪 Recommended Layering Combos")
    for i, (f1, f2, reason) in enumerate(combos, 1):
      st.info(
          f"**Combo #{i}**\n\n🖤 **Base / First:** {f1['name']}"
          f" ({f1['brand']})\n\n🖤 **Layer / Top:** {f2['name']}"
          f" ({f2['brand']})\n\n💡 **Why it works:** {reason}"
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

# Scent of the Day (SOTD) Section
st.markdown("---")
st.subheader("🩸 Scent of the Day (SOTD) Logger")
all_frag_names = [f["name"] for f in st.session_state["fragrances_db"]]
sotd_choice = st.selectbox(
    "What are you wearing today?", ["Select a fragrance..."] + all_frag_names
)
sotd_notes = st.text_input(
    "Optional comments/vibe for today:",
    placeholder="e.g. Perfect for a rainy gothic afternoon.",
)

if st.button("Log Today's Scent"):
  if sotd_choice != "Select a fragrance...":
    import datetime

    today_date = datetime.date.today().strftime("%Y-%m-%d")
    st.session_state["sotd_history"].insert(
        0, {"date": today_date, "scent": sotd_choice, "notes": sotd_notes}
    )
    st.success(f"Successfully logged {sotd_choice} for today!")
  else:
    st.warning("Please choose a valid fragrance to log.")

if st.session_state["sotd_history"]:
  with st.expander("🦇 View SOTD Journal History"):
    for entry in st.session_state["sotd_history"]:
      st.write(
          f"**{entry['date']}**: 🖤 *{entry['scent']}* — {entry['notes']}"
      )

# Collection & Data Management Expander (Export/Import + Reactions)
with st.expander("🖤 View All Collection & Saved Data Management"):
  st.write(
      "Total fragrances in database:"
      f" **{len(st.session_state['fragrances_db'])}**"
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
    st.write(f"⭐ **Favorites:** {', '.join(favs)}")
  if dislikes:
    st.write(f"👎 **Disliked:** {', '.join(dislikes)}")

  if st.button("Clear All Reactions"):
    st.session_state["user_reactions"] = {}
    st.rerun()

  st.markdown("---")
  st.subheader("💾 Backup & Restore Collection Data")

  # Export JSON Data
  export_data = {
      "fragrances_db": st.session_state["fragrances_db"],
      "user_reactions": st.session_state["user_reactions"],
      "sotd_history": st.session_state["sotd_history"],
  }
  json_string = json.dumps(export_data, indent=4)

  st.download_button(
      label="📥 Export Collection & Data as JSON",
      data=json_string,
      file_name="scented_dead_girl_backup.json",
      mime="application/json",
  )

  # Import JSON Data
  uploaded_file = st.file_uploader(
      "📤 Restore from Backup JSON File", type=["json"]
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
      st.success("Successfully restored your collection and data backup!")
      st.rerun()
    except Exception as e:
      st.error(f"Error loading file: {e}")
