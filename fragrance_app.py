import json
import random
import re
import streamlit as st

# ==========================================
# PAGE CONFIGURATION & CUSTOM GOTHIC THEME
# ==========================================
st.set_page_config(
    page_title="ScentedDeadGirl Fragrance Vault",
    page_icon="🦇",
    layout="centered",
)

st.markdown(
    """
    <style>
        /* Import edgy fonts from Google Fonts */
        @import url('https://fonts.googleapis.com/css2?family=Creepster&family=Cinzel:wght@600&family=Inter:wght@400;600&display=swap');

        /* Main background and text colors */
        .stApp {
            background-color: #0b0b0c;
            color: #e0e0e0;
            font-family: 'Inter', sans-serif;
        }

        /* Gothic Header styling */
        h1, h2, h3 {
            font-family: 'Creepster', cursive !important;
            color: #b30000 !important;
            letter-spacing: 2px;
        }

        /* Custom Sidebar Styling */
        [data-testid="stSidebar"] {
            background-color: #121212;
            border-right: 1px solid #2b2b2b;
        }

        /* Buttons styling */
        .stButton>button {
            background-color: #1a0000;
            color: #ff4d4d;
            border: 1px solid #b30000;
            border-radius: 4px;
            font-weight: 600;
        }
        .stButton>button:hover {
            background-color: #b30000;
            color: #ffffff;
            border-color: #ff4d4d;
        }

        /* Inputs and Selectboxes */
        .stTextInput>div>div>input, .stSelectbox>div>div>div {
            background-color: #161618;
            color: #f8f9fa;
            border: 1px solid #2b2b2b;
        }

        /* Note / Badge pills */
        .note-badge {
            display: inline-block;
            background-color: #1f1f1f;
            color: #ffb3b3;
            padding: 4px 10px;
            margin: 2px;
            border-radius: 12px;
            border: 1px solid #4d0000;
            font-size: 0.85rem;
        }
    </style>
""",
    unsafe_allow_html=True,
)

# ==========================================
# SESSION STATE INITIALIZATION
# ==========================================
if "fragrance_database" not in st.session_state:
  st.session_state["fragrance_database"] = [
      {
          "name": "Vanilla Noir",
          "brand": "Dark Alchemy",
          "profile": "Smoky Vanilla & Black Amber",
          "notes": ["Dark Vanilla", "Smoked Caramel", "Black Amber"],
      },
      {
          "name": "Midnight Caramel",
          "brand": "Cryptic Scents",
          "profile": "Dark Caramel & Sea Salt",
          "notes": ["Burnt Sugar", "Sea Salt", "Vanilla Bean"],
      },
      {
          "name": "Velvet Orchid",
          "brand": "Gothic Parfums",
          "profile": "Spiced Plum & Dark Musk",
          "notes": ["Black Plum", "Dark Musk", "Patchouli"],
      },
  ]

if "scent_of_the_day_log" not in st.session_state:
  st.session_state["scent_of_the_day_log"] = []

# ==========================================
# APP HEADER & SIDEBAR NAVIGATION
# ==========================================
st.title("🦇 ScentedDeadGirl Vault 🦇")
st.markdown(
    "*Your personal dark archive for gothic gourmands, vanillas, and custom"
    " layering combos.*"
)

st.sidebar.title("🦇 Crypt Controls")
menu_choice = st.sidebar.radio(
    "Navigation",
    ["Collection & Search", "Add Fragrance", "Scent of the Day", "Data Backup"],
)

# ==========================================
# 1. COLLECTION & SEARCH VIEW
# ==========================================
if menu_choice == "Collection & Search":
  st.subheader("🔮 Fragrance Archive")

  search_query = st.text_input(
      "Search by name, brand, or note:",
      placeholder="Type vanilla, caramel, etc...",
  )

  db = st.session_state["fragrance_database"]

  # Filter logic
  filtered_db = db
  if search_query:
    q = search_query.lower()
    filtered_db = []
    for item in db:
      match_name = q in item.get("name", "").lower()
      match_brand = q in item.get("brand", "").lower()
      match_notes = any(q in note.lower() for note in item.get("notes", []))
      if match_name or match_brand or match_notes:
        filtered_db.append(item)

  st.write(f"Showing {len(filtered_db)} dark treasures:")

  for index, frag in enumerate(filtered_db):
    with st.expander(f"🖤 {frag.get('name')} ({frag.get('brand', 'Unknown')})"):
      st.markdown(f"**Vibe / Profile:** {frag.get('profile', 'N/A')}")
      st.markdown("**Notes:**")
      badges = "".join(
          [f"<span class='note-badge'>{note}</span>" for note in frag.get("notes", [])]
      )
      st.markdown(badges, unsafe_allow_html=True)

# ==========================================
# 2. ADD FRAGRANCE VIEW
# ==========================================
elif menu_choice == "Add Fragrance":
  st.subheader("⚰️ Add New Scents to the Crypt")

  with st.form("add_fragrance_form"):
    new_name = st.text_input("Fragrance Name")
    new_brand = st.text_input("Brand / House")
    new_profile = st.text_input("Profile / Vibe (e.g., Sweet Vanilla)")
    new_notes_raw = st.text_input(
        "Notes (comma separated, e.g., Vanilla, Caramel, Musk)"
    )

    submitted = st.form_submit_button("Store in Crypt")
    if submitted:
      if new_name:
        parsed_notes = [
            n.strip() for n in new_notes_raw.split(",") if n.strip()
        ]
        new_entry = {
            "name": new_name,
            "brand": new_brand,
            "profile": new_profile,
            "notes": parsed_notes,
        }
        st.session_state["fragrance_database"].append(new_entry)
        st.success(f"Successfully banished '{new_name}' into your vault!")
      else:
        st.error("Please provide at least a fragrance name.")

# ==========================================
# 3. SCENT OF THE DAY VIEW
# ==========================================
elif menu_choice == "Scent of the Day":
  st.subheader("🦇 Scent of the Day & Layering Logger")

  db_names = [f.get("name") for f in st.session_state["fragrance_database"]]

  if db_names:
    selected_sotd = st.selectbox(
        "Choose today's potion from your collection:", db_names
    )
    sotd_notes = st.text_area(
        "Layering Notes / Thoughts (How does it wear today?):"
    )

    if st.button("Log Scent of the Day"):
      log_entry = {"fragrance": selected_sotd, "notes": sotd_notes}
      st.session_state["scent_of_the_day_log"].append(log_entry)
      st.success(f"Logged '{selected_sotd}' for today's chronicle!")

    if st.session_state["scent_of_the_day_log"]:
      st.markdown("---")
      st.markdown("### 📜 Recent History")
      for log in reversed(st.session_state["scent_of_the_day_log"]):
        st.markdown(
            f"• **{log['fragrance']}** — *{log['notes'] if log['notes'] else 'No special notes'}*"
        )
  else:
    st.info("Add some fragrances to your collection first to log your Scent of the Day!")

# ==========================================
# 4. DATA BACKUP VIEW
# ==========================================
elif menu_choice == "Data Backup":
  st.subheader("💾 Crypt Backup & Restore")

  # Export JSON
  json_data = json.dumps(st.session_state["fragrance_database"], indent=4)
  st.download_button(
      label="Download Database Backup (JSON)",
      data=json_data,
      file_name="scented_dead_girl_vault.json",
      mime="application/json",
  )

  # Import JSON
  uploaded_file = st.file_uploader(
      "Restore Database from JSON Backup", type=["json"]
  )
  if uploaded_file is not None:
    try:
      restored_data = json.load(uploaded_file)
      if isinstance(restored_data, list):
        st.session_state["fragrance_database"] = restored_data
        st.success("Crypt successfully restored from backup file!")
      else:
        st.error("Invalid backup file format.")
    except Exception as e:
      st.error(f"Error reading file: {e}")

# ==========================================
# MIDNIGHT SCENT ROULETTE FEATURE (MAIN PAGE FOOTER)
# ==========================================
st.markdown("---")
st.subheader("🦇 Midnight Scent Roulette")

if st.button("Spin the Roulette"):
  if st.session_state["fragrance_database"]:
    chosen_one = random.choice(st.session_state["fragrance_database"])
    st.markdown(
        f"🔮 **Tonight's Dark Omen Picks:** You are destined to wear"
        f" **{chosen_one.get('name', 'Unknown Fragrance')}**!"
    )
    st.markdown(
        f"<span class='note-badge'>Vibe:"
        f" {chosen_one.get('profile', 'Gourmand/Vanilla')}</span>",
        unsafe_allow_html=True,
    )
  else:
    st.info("The crypt is empty! Add some fragrances to spin the roulette.")
