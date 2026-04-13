# ----------------------------------------
# Spanish Vocabulary Reader
# Version: 5.5
# Features:
# - Reading + saving words
# - Flashcards mode
# - Difficulty system
# - Random / Sequential learning
# Date: 2026-04-13
# ----------------------------------------

import streamlit as st
import pandas as pd
from deep_translator import GoogleTranslator
import PyPDF2
from datetime import datetime
from io import BytesIO
import re
import random

st.set_page_config(page_title="Spanish Reader", layout="wide")

st.title("📖 Spanish Vocabulary Reader")
st.caption("Version 5.5")

# -----------------------
# Session
# -----------------------
if "words_data" not in st.session_state:
    st.session_state.words_data = []

if "selected_words" not in st.session_state:
    st.session_state.selected_words = set()

if "last_word" not in st.session_state:
    st.session_state.last_word = ""

if "mode" not in st.session_state:
    st.session_state.mode = "read"

if "flash_index" not in st.session_state:
    st.session_state.flash_index = 0

if "show_answer" not in st.session_state:
    st.session_state.show_answer = False

# -----------------------
# MODE SWITCH
# -----------------------
mode = st.radio("Mode:", ["Read", "Flashcards"])

# -----------------------
# -----------------------
# 📖 READING MODE
# -----------------------
# -----------------------
if mode == "Read":

    option = st.radio("Διάλεξε τρόπο εισαγωγής:", ["Paste Text", "Upload File"])

    text = ""
    source_name = "pasted_text"

    if option == "Paste Text":
        text = st.text_area("Επικόλλησε ισπανικό κείμενο εδώ:", height=150)

    elif option == "Upload File":
        uploaded_file = st.file_uploader("Ανέβασε αρχείο (.txt ή .pdf)", type=["txt", "pdf"])

        if uploaded_file:
            source_name = uploaded_file.name

            if uploaded_file.type == "text/plain":
                text = uploaded_file.read().decode("utf-8")

            elif uploaded_file.type == "application/pdf":
                reader = PyPDF2.PdfReader(uploaded_file)
                pages = []
                for page in reader.pages:
                    content = page.extract_text()
                    if content:
                        pages.append(content)
                text = "\n".join(pages)

    lang = st.selectbox("Μετάφραση σε:", ["Greek", "English"])
    target_lang = "el" if lang == "Greek" else "en"

    if text:
        st.subheader("📖 Κείμενο")
        st.text_area("", text, height=300)

        st.subheader("✏️ Input unknown word + Enter → Translation + Save")
        user_word = st.text_input("")

        if user_word and user_word != st.session_state.last_word:

            st.session_state.last_word = user_word
            clean_word = user_word.lower().strip()

            try:
                translation = GoogleTranslator(source='auto', target=target_lang).translate(clean_word)
            except:
                translation = "Error"

            st.success(f"{clean_word} → {translation}")

            st.session_state.selected_words.add(clean_word)

            exists = any(w["word"] == clean_word for w in st.session_state.words_data)

            if not exists:
                st.session_state.words_data.append({
                    "word": clean_word,
                    "translation": translation,
                    "difficulty": "medium",
                    "source": source_name,
                    "date": datetime.now().strftime("%Y-%m-%d %H:%M")
                })

        if st.session_state.words_data:
            st.subheader("📚 Translations")

            translation_text = "\n".join([
                f"{w['word']} → {w['translation']}"
                for w in st.session_state.words_data
            ])

            st.text_area("", translation_text, height=200)

# -----------------------
# -----------------------
# 🧠 FLASHCARDS MODE
# -----------------------
# -----------------------
if mode == "Flashcards":

    if not st.session_state.words_data:
        st.warning("Δεν υπάρχουν λέξεις ακόμα.")
    else:

        st.subheader("⚙️ Επιλογή τρόπου")
        learn_mode = st.radio("Mode:", ["Sequential", "Random"])

        words = st.session_state.words_data

        # επιλογή λέξης
        if learn_mode == "Sequential":
            word_obj = words[st.session_state.flash_index % len(words)]

        else:
            weighted = []
            for w in words:
                if w["difficulty"] == "hard":
                    weighted.extend([w]*3)
                elif w["difficulty"] == "medium":
                    weighted.extend([w]*2)
                else:
                    weighted.append(w)

            word_obj = random.choice(weighted)

        st.subheader("📖 Word")
        st.markdown(f"### {word_obj['word']}")

        if st.button("Show answer"):
            st.session_state.show_answer = True

        if st.session_state.show_answer:
            st.success(f"{word_obj['translation']}")

            st.write("Difficulty:")

            col1, col2, col3 = st.columns(3)

            if col1.button("🟢 Easy"):
                word_obj["difficulty"] = "easy"
                st.session_state.show_answer = False
                st.session_state.flash_index += 1

            if col2.button("🟡 Medium"):
                word_obj["difficulty"] = "medium"
                st.session_state.show_answer = False
                st.session_state.flash_index += 1

            if col3.button("🔴 Hard"):
                word_obj["difficulty"] = "hard"
                st.session_state.show_answer = False
                st.session_state.flash_index += 1

# -----------------------
# Excel
# -----------------------
if st.session_state.words_data:
    df = pd.DataFrame(st.session_state.words_data)

    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)

    st.download_button(
        "💾 Κατέβασε Excel",
        data=output.getvalue(),
        file_name="words.xlsx"
    )

# -----------------------
# Clear
# -----------------------
if st.button("❌ Καθαρισμός"):
    st.session_state.words_data = []
    st.session_state.selected_words = set()
