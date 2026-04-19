# ----------------------------------------
# Spanish Reader
# Version 7.7 (PRO Calendar + Anki SRS)
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
# LOAD WORDS
# ======================
def load_words():
    if os.path.exists(WORDS_FILE):
        return pd.read_excel(WORDS_FILE)
    return pd.DataFrame(columns=[
        "word","translation","lemma","pos","sentence",
        "difficulty","date",
        "ease","interval","repetitions","next_review"
    ])

def save_words(df):
    df.to_excel(WORDS_FILE, index=False)

# ======================
# LOAD LOG
# ======================
def load_log():
    if os.path.exists(LOG_FILE):
        return pd.read_excel(LOG_FILE)
    return pd.DataFrame(columns=["date","count"])

def save_log(df):
    df.to_excel(LOG_FILE, index=False)

# ======================
# INIT STATE
# ======================
if "df" not in st.session_state:
    st.session_state.df = load_words()

if "log_df" not in st.session_state:
    st.session_state.log_df = load_log()

if "flash_index" not in st.session_state:
    st.session_state.flash_index = 0

if "show" not in st.session_state:
    st.session_state.show = False

# ======================
# TRANSLATE
# ======================
def translate(word):
    return GoogleTranslator(source="auto", target="el").translate(word)

# ======================
# ADD WORD + LOG COUNT
# ======================
def add_word(word, translation):

    df = st.session_state.df

    if word in df["word"].values:
        return

    today = str(date.today())

    new_row = {
        "word": word,
        "translation": translation,
        "lemma": word.lower(),
        "pos": "unknown",
        "sentence": "",
        "difficulty": "medium",
        "date": today,
        "ease": 2.5,
        "interval": 1,
        "repetitions": 0,
        "next_review": today
    }

    st.session_state.df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    save_words(st.session_state.df)

    # update log count
    log = st.session_state.log_df

    if today in log["date"].values:
        log.loc[log["date"] == today, "count"] += 1
    else:
        log = pd.concat([log, pd.DataFrame([{"date": today, "count": 1}])])

    st.session_state.log_df = log
    save_log(log)

# ======================
# SRS UPDATE
# ======================
def update_srs(row, correct):

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
        row["interval"] = 1
        row["ease"] = max(1.3, row["ease"] - 0.2)

    row["next_review"] = str(date.today() + timedelta(days=row["interval"]))
    return row

# ======================
# DUE WORDS
# ======================
def get_due(df):
    today = str(date.today())
    return df[df["next_review"] <= today]

# ======================
# UI
# ======================
st.set_page_config(layout="wide")
st.title("📖 Spanish Reader v7.7 PRO")

mode = st.radio("Mode", ["Read","Audio","Flashcards","Calendar"])

# ======================
# READ
# ======================
if mode == "Read":

    text = st.text_area("Paste text", height=300)
    word = st.text_input("Unknown word")

    if word:
        t = translate(word)
        st.success(t)
        add_word(word, t)

# ======================
# AUDIO
# ======================
if mode == "Audio":

    audio = st.file_uploader("Upload audio", type=["mp3","wav","m4a"])

    if audio:
        st.audio(audio)

    text = st.text_area("Paste transcript", height=300)
    word = st.text_input("Unknown word audio")

    if word:
        t = translate(word)
        st.success(t)
        add_word(word, t)

# ======================
# FLASHCARDS
# ======================
if mode == "Flashcards":

    df = get_due(st.session_state.df)

    if df.empty:
        st.success("🎉 No cards due!")
    else:
        row = df.iloc[st.session_state.flash_index % len(df)]

        st.markdown(f"## {row['word']}")

        if st.button("Show"):
            st.session_state.show = True

        if st.session_state.show:
            st.success(row["translation"])

            col1, col2 = st.columns(2)

            if col1.button("✔"):
                updated = update_srs(row, True)
                st.session_state.df.loc[st.session_state.df["word"] == row["word"]] = updated
                save_words(st.session_state.df)
                st.session_state.show = False
                st.session_state.flash_index += 1
                st.rerun()

            if col2.button("❌"):
                updated = update_srs(row, False)
                st.session_state.df.loc[st.session_state.df["word"] == row["word"]] = updated
                save_words(st.session_state.df)
                st.session_state.show = False
                st.session_state.flash_index += 1
                st.rerun()

# ======================
# PRO CALENDAR
# ======================
if mode == "Calendar":

    st.subheader("🔥 Study Heatmap")

    log = st.session_state.log_df

    if log.empty:
        st.info("No data yet")
    else:

        today = date.today()
        year, month = today.year, today.month

        cal = calendar.monthcalendar(year, month)

        st.markdown(f"## {calendar.month_name[month]} {year}")

        # streak
        log_sorted = log.sort_values("date", ascending=False)
        streak = 0

        for d in log_sorted["date"]:
            if d == str(today - timedelta(days=streak)):
                streak += 1
            else:
                break

        st.success(f"🔥 Streak: {streak} days")

        for week in cal:

            cols = st.columns(7)

            for i, day in enumerate(week):

                if day == 0:
                    cols[i].write("")
                else:
                    d_str = f"{year}-{month:02d}-{day:02d}"

                    count = 0
                    if d_str in log["date"].values:
                        count = int(log.loc[log["date"] == d_str, "count"])

                    if count == 0:
                        cols[i].markdown(f"⬜ {day}")
                    elif count < 3:
                        cols[i].markdown(f"🟩 {day}")
                    elif count < 6:
                        cols[i].markdown(f"🟨 {day}")
                    else:
                        cols[i].markdown(f"🟥 {day}")
