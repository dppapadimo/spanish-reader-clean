# ----------------------------------------
# Spanish Reader
# Version 7.6 (Anki-style Flashcards + Excel DB)
# ----------------------------------------

import streamlit as st
import pandas as pd
from deep_translator import GoogleTranslator
import PyPDF2
from docx import Document
from datetime import datetime, date, timedelta
import calendar
import os
import spacy

# ======================
# FILES
# ======================
WORDS_FILE = "spanish_words_unknown.xlsx"
LOG_FILE = "study_log.xlsx"

# ======================
# LOAD NLP
# ======================
@st.cache_resource
def load_spacy_model():
    return spacy.load("es_core_news_sm")

nlp = load_spacy_model()

# ======================
# LOAD WORDS DB (APPEND ONLY BASE)
# ======================
def load_words():
    if os.path.exists(WORDS_FILE):
        df = pd.read_excel(WORDS_FILE)
    else:
        df = pd.DataFrame(columns=[
            "word","translation","lemma","pos","sentence",
            "difficulty","date",
            "ease","interval","repetitions","next_review"
        ])
    return df

def save_words(df):
    df.to_excel(WORDS_FILE, index=False)

# ======================
# INIT STATE
# ======================
if "df" not in st.session_state:
    st.session_state.df = load_words()

if "flash_index" not in st.session_state:
    st.session_state.flash_index = 0

if "show" not in st.session_state:
    st.session_state.show = False

if "study_log" not in st.session_state:
    if os.path.exists(LOG_FILE):
        st.session_state.study_log = pd.read_excel(LOG_FILE)["date"].tolist()
    else:
        st.session_state.study_log = []

# ======================
# TRANSLATION
# ======================
def translate(word):
    return GoogleTranslator(source="auto", target="el").translate(word)

# ======================
# ADD WORD (APPEND ONLY + SRS INIT)
# ======================
def add_word(word, translation, lemma, pos, sentence):

    df = st.session_state.df

    if word in df["word"].values:
        return

    new_row = {
        "word": word,
        "translation": translation,
        "lemma": lemma,
        "pos": pos,
        "sentence": sentence,
        "difficulty": "medium",
        "date": str(date.today()),

        # SRS fields
        "ease": 2.5,
        "interval": 1,
        "repetitions": 0,
        "next_review": str(date.today())
    }

    st.session_state.df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    save_words(st.session_state.df)

# ======================
# SRS UPDATE (ANKI STYLE)
# ======================
def update_srs(row, correct: bool):

    if correct:
        row["repetitions"] += 1
        row["ease"] = min(3.0, row["ease"] + 0.1)

        if row["repetitions"] == 1:
            row["interval"] = 1
        elif row["repetitions"] == 2:
            row["interval"] = 3
        else:
            row["interval"] = int(row["interval"] * row["ease"])

    else:
        row["repetitions"] = 0
        row["ease"] = max(1.3, row["ease"] - 0.2)
        row["interval"] = 1

    row["next_review"] = str(date.today() + timedelta(days=row["interval"]))
    return row

# ======================
# FLASHCARDS FILTER
# ======================
def get_due_words(df):
    today = str(date.today())
    return df[df["next_review"] <= today]

# ======================
# CALENDAR
# ======================
def mark_today():
    today = str(date.today())
    if today not in st.session_state.study_log:
        st.session_state.study_log.append(today)

        pd.DataFrame({"date": st.session_state.study_log}).to_excel(LOG_FILE, index=False)

# ======================
# UI
# ======================
st.set_page_config(layout="wide")
st.title("📖 Spanish Reader v7.6 (Anki Style)")

mode = st.radio("Mode", ["Read", "Flashcards", "Calendar"])

# ======================
# READ MODE
# ======================
if mode == "Read":

    text = st.text_area("Paste text", height=300)

    word = st.text_input("Unknown word")

    if word:
        translation = translate(word)

        st.success(translation)

        add_word(word, translation, word.lower(), "unknown", "")

        st.session_state.df.to_excel(WORDS_FILE, index=False)

# ======================
# FLASHCARDS (ANKI STYLE)
# ======================
if mode == "Flashcards":

    df = get_due_words(st.session_state.df)

    if df.empty:
        st.warning("No cards due today 🎉")
    else:

        idx = st.session_state.flash_index % len(df)
        row = df.iloc[idx]

        st.markdown(f"## {row['word']}")

        if st.button("Show answer"):
            st.session_state.show = True

        if st.session_state.show:
            st.success(row["translation"])
            st.info(row.get("sentence",""))

            col1, col2 = st.columns(2)

            if col1.button("✔ Correct"):
                updated = update_srs(row, True)
                st.session_state.df.loc[st.session_state.df["word"] == row["word"], :] = updated
                save_words(st.session_state.df)
                st.session_state.show = False
                st.session_state.flash_index += 1
                st.rerun()

            if col2.button("❌ Wrong"):
                updated = update_srs(row, False)
                st.session_state.df.loc[st.session_state.df["word"] == row["word"], :] = updated
                save_words(st.session_state.df)
                st.session_state.show = False
                st.session_state.flash_index += 1
                st.rerun()

        if st.button("Next"):
            st.session_state.flash_index += 1
            st.rerun()

# ======================
# CALENDAR
# ======================
if mode == "Calendar":

    st.subheader("📅 Study Calendar")

    mark_today()

    today = date.today()
    year, month = today.year, today.month

    cal = calendar.monthcalendar(year, month)

    days = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
    cols = st.columns(7)

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
