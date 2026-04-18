# ----------------------------------------
# Spanish Reader
# Version 7.5 (Excel + Flashcards + Calendar)
# ----------------------------------------

import streamlit as st
import pandas as pd
from deep_translator import GoogleTranslator
import PyPDF2
from docx import Document
from datetime import datetime, date
import os
import calendar
import spacy

# ======================
# FILES
# ======================
WORDS_FILE = "words.xlsx"
LOG_FILE = "study_log.xlsx"

# ======================
# LOAD SPACY
# ======================
@st.cache_resource
def load_spacy_model():
    return spacy.load("es_core_news_sm")

nlp = load_spacy_model()

# ======================
# LOAD / SAVE WORDS
# ======================
def load_words():
    if os.path.exists(WORDS_FILE):
        return pd.read_excel(WORDS_FILE).to_dict("records")
    return []

def save_words(data):
    pd.DataFrame(data).to_excel(WORDS_FILE, index=False)

# ======================
# LOAD / SAVE LOG
# ======================
def load_log():
    if os.path.exists(LOG_FILE):
        return pd.read_excel(LOG_FILE)["date"].tolist()
    return []

def save_log(log):
    pd.DataFrame({"date": log}).to_excel(LOG_FILE, index=False)

# ======================
# INIT STATE
# ======================
if "words_data" not in st.session_state:
    st.session_state.words_data = load_words()

if "study_log" not in st.session_state:
    st.session_state.study_log = load_log()

if "flash_index" not in st.session_state:
    st.session_state.flash_index = 0

if "show_answer" not in st.session_state:
    st.session_state.show_answer = False

# ======================
# FUNCTIONS
# ======================
def translate(word, target="el"):
    return GoogleTranslator(source="auto", target=target).translate(word)

def add_word(word, translation, lemma, pos, sentence):
    exists = any(w["word"] == word for w in st.session_state.words_data)

    if not exists:
        st.session_state.words_data.append({
            "word": word,
            "translation": translation,
            "lemma": lemma,
            "pos": pos,
            "sentence": sentence,
            "difficulty": "medium",
            "date": str(date.today())
        })

        save_words(st.session_state.words_data)

def mark_today():
    today = str(date.today())
    if today not in st.session_state.study_log:
        st.session_state.study_log.append(today)
        save_log(st.session_state.study_log)

# ======================
# UI
# ======================
st.set_page_config(layout="wide")
st.title("📖 Spanish Reader v7.5")

mode = st.radio("Mode:", ["Read", "Audio", "Flashcards", "Calendar"])

# ======================
# READ MODE
# ======================
if mode == "Read":

    st.subheader("📄 Input Text")

    option = st.radio("Input:", ["Paste", "Upload"])

    text = ""

    if option == "Paste":
        text = st.text_area("Paste text", height=300)

    else:
        file = st.file_uploader("Upload txt/pdf/docx", type=["txt", "pdf", "docx"])

        if file:
            if file.type == "text/plain":
                text = file.read().decode("utf-8")

            elif file.type == "application/pdf":
                reader = PyPDF2.PdfReader(file)
                text = "\n".join([p.extract_text() for p in reader.pages])

            else:
                doc = Document(file)
                text = "\n".join([p.text for p in doc.paragraphs])

            text = st.text_area("Text", text, height=300)

    if text:

        word = st.text_input("Unknown word")

        if word:

            lemma = word.lower()
            translation = translate(word)
            pos = "unknown"
            sentence = ""

            st.success(translation)

            add_word(word, translation, lemma, pos, sentence)

# ======================
# AUDIO MODE
# ======================
if mode == "Audio":

    st.subheader("🎧 Upload Audio")

    audio = st.file_uploader("Audio file", type=["mp3", "wav", "m4a"])

    if audio:
        st.audio(audio)

    st.subheader("📝 Paste transcript")
    text = st.text_area("Transcript", height=300)

    if text:

        word = st.text_input("Unknown word (audio)")

        if word:

            translation = translate(word)

            st.success(translation)

            add_word(word, translation, word.lower(), "unknown", "")

# ======================
# FLASHCARDS
# ======================
if mode == "Flashcards":

    words = st.session_state.words_data

    if not words:
        st.warning("No words yet")
    else:

        mode_fc = st.radio("Mode", ["Serial", "Random"])

        import random

        if mode_fc == "Random":
            w = random.choice(words)
        else:
            w = words[st.session_state.flash_index % len(words)]

        st.markdown(f"## {w['word']}")

        if st.button("Show answer"):
            st.success(w["translation"])

        if st.button("Next"):
            st.session_state.flash_index += 1
            st.rerun()

        difficulty = st.radio("Difficulty", ["easy", "medium", "hard"], key=w["word"])
        w["difficulty"] = difficulty

# ======================
# CALENDAR (PRETTY)
# ======================
if mode == "Calendar":

    st.subheader("📅 Study Calendar")

    mark_today()

    today = date.today()
    year = today.year
    month = today.month

    cal = calendar.monthcalendar(year, month)

    cols = st.columns(7)

    days = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]

    for i, d in enumerate(days):
        cols[i].markdown(f"**{d}**")

    for week in cal:
        cols = st.columns(7)
        for i, day in enumerate(week):
            if day == 0:
                cols[i].write("")
            else:
                d_str = f"{year}-{month:02d}-{day:02d}"

                if d_str in st.session_state.study_log:
                    cols[i].success(day)
                else:
                    cols[i].write(day)

# ======================
# EXPORT (optional backup)
# ======================
if st.session_state.words_data:

    df = pd.DataFrame(st.session_state.words_data)

    st.download_button(
        "💾 Export Excel",
        df.to_csv(index=False).encode(),
        file_name="words_backup.csv"
    )

# ======================
# RESET
# ======================
if st.button("❌ Reset"):
    st.session_state.words_data = []
    st.session_state.study_log = []
