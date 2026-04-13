# ----------------------------------------
# Spanish Vocabulary Reader
# Version: 6.5
# Features:
# - Reading mode (text + PDF)
# - Translation + save
# - spaCy lemma + verb detection
# - Flashcards mode
# - Sequential / Random learning
# - Next button
# Date: 2026-04-14
# ----------------------------------------

import streamlit as st
import pandas as pd
from deep_translator import GoogleTranslator
import PyPDF2
from datetime import datetime
from io import BytesIO
import spacy
import random
# ====≠================

import os
os.system("python -m spacy download es_core_news_sm")
# ======================
# LOAD NLP MODEL
# ======================
nlp = spacy.load("es_core_news_sm")

st.set_page_config(page_title="Spanish Reader", layout="wide")

st.title("📖 Spanish Vocabulary Reader")
st.caption("Version 6.5 (spaCy + Flashcards)")

# ======================
# SESSION STATE
# ======================
if "words_data" not in st.session_state:
    st.session_state.words_data = []

if "selected_words" not in st.session_state:
    st.session_state.selected_words = set()

if "last_word" not in st.session_state:
    st.session_state.last_word = ""

if "mode" not in st.session_state:
    st.session_state.mode = "Read"

if "flash_index" not in st.session_state:
    st.session_state.flash_index = 0

if "show_answer" not in st.session_state:
    st.session_state.show_answer = False

# ======================
# NLP FUNCTIONS (spaCy)
# ======================
def get_verb_info(word):
    doc = nlp(word)
    token = doc[0]

    return {
        "lemma": token.lemma_,
        "pos": token.pos_,
        "is_verb": token.pos_ == "VERB"
    }

# ======================
# MODE SELECT
# ======================
mode = st.radio("Mode:", ["Read", "Flashcards"])

# ======================
# READ MODE
# ======================
if mode == "Read":

    option = st.radio("Input:", ["Paste Text", "Upload File"])

    text = ""
    source_name = "pasted"

    if option == "Paste Text":
        text = st.text_area("Paste Spanish text:", height=150)

    elif option == "Upload File":
        file = st.file_uploader("Upload file", type=["txt", "pdf"])

        if file:
            source_name = file.name

            if file.type == "text/plain":
                text = file.read().decode("utf-8")

            else:
                reader = PyPDF2.PdfReader(file)
                text = "\n".join([p.extract_text() for p in reader.pages if p.extract_text()])

    lang = st.selectbox("Translate to:", ["Greek", "English"])
    target_lang = "el" if lang == "Greek" else "en"

    if text:
        st.subheader("📖 Text")
        st.text_area("", text, height=300)

        st.subheader("✏️ Input word + Enter")

        word = st.text_input("")

        if word and word != st.session_state.last_word:

            st.session_state.last_word = word
            clean = word.lower().strip()

            # translation
            translation = GoogleTranslator(
                source='auto',
                target=target_lang
            ).translate(clean)

            # NLP info
            info = get_verb_info(clean)

            if info["is_verb"]:
                display = f"{clean} → {translation} (VERB, lemma: {info['lemma']})"
            else:
                display = f"{clean} → {translation}"

            st.success(display)

            # save highlight list
            st.session_state.selected_words.add(clean)

            # save data
            exists = any(w["word"] == clean for w in st.session_state.words_data)

            if not exists:
                st.session_state.words_data.append({
                    "word": clean,
                    "translation": translation,
                    "lemma": info["lemma"],
                    "pos": info["pos"],
                    "difficulty": "medium",
                    "source": source_name,
                    "date": datetime.now().strftime("%Y-%m-%d %H:%M")
                })

        # translations view
        if st.session_state.words_data:
            st.subheader("📚 Words")

            txt = "\n".join([
                f"{w['word']} → {w['translation']} ({w['lemma']})"
                for w in st.session_state.words_data
            ])

            st.text_area("", txt, height=200)

# ======================
# FLASHCARDS MODE
# ======================
if mode == "Flashcards":

    if not st.session_state.words_data:
        st.warning("No words yet.")
    else:

        words = st.session_state.words_data

        learn_mode = st.radio("Order:", ["Sequential", "Random"])

        # SELECT WORD
        if learn_mode == "Sequential":
            word_obj = words[st.session_state.flash_index % len(words)]
        else:
            word_obj = random.choice(words)

        st.subheader("📖 Word")
        st.markdown(f"## {word_obj['word']}")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("Show answer"):
                st.session_state.show_answer = True

        with col2:
            if st.button("➡️ Next"):
                st.session_state.show_answer = False
                st.session_state.flash_index += 1
                st.rerun()

        if st.session_state.show_answer:
            st.success(word_obj["translation"])
            st.info(f"lemma: {word_obj.get('lemma','')}")
            st.info(f"pos: {word_obj.get('pos','')}")

# ======================
# EXPORT EXCEL
# ======================
if st.session_state.words_data:

    df = pd.DataFrame(st.session_state.words_data)

    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False)

    st.download_button(
        "💾 Download Excel",
        buffer.getvalue(),
        file_name="words.xlsx"
    )

# ======================
# RESET
# ======================
if st.button("❌ Reset"):
    st.session_state.words_data = []
    st.session_state.selected_words = set()
    st.session_state.flash_index = 0
