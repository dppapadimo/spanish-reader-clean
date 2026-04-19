# ----------------------------------------
# Spanish Reader v8.0 FINAL
# Read + Audio + Flashcards + Pro Calendar
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
import random

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
# FILE READERS
# ======================
def read_pdf(file):
    reader = PyPDF2.PdfReader(file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text

def read_docx(file):
    doc = Document(file)
    return "\n".join([p.text for p in doc.paragraphs])

def read_txt(file):
    return file.read().decode("utf-8")

# ======================
# NLP
# ======================
def analyze_word(word):
    doc = nlp(word)
    token = doc[0]
    return token.lemma_, token.pos_

def extract_sentence(text, word):
    doc = nlp(text)
    for sent in doc.sents:
        if word.lower() in sent.text.lower():
            return sent.text
    return ""

# ======================
# TRANSLATE
# ======================
def translate(word):
    return GoogleTranslator(source="auto", target="el").translate(word)

# ======================
# ADD WORD
# ======================
def add_word(word, text):

    df = load_words()

    if word in df["word"].values:
        return df

    translation = translate(word)
    lemma, pos = analyze_word(word)
    sentence = extract_sentence(text, word)

    today = str(date.today())

    new_row = {
        "word": word,
        "translation": translation,
        "lemma": lemma,
        "pos": pos,
        "sentence": sentence,
        "difficulty": "medium",
        "date": today,
        "ease": 2.5,
        "interval": 1,
        "repetitions": 0,
        "next_review": today
    }

    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    save_words(df)

    # update log
    log = load_log()
    if today in log["date"].values:
        log.loc[log["date"] == today, "count"] += 1
    else:
        log = pd.concat([log, pd.DataFrame([{"date": today, "count": 1}])])

    save_log(log)

    return df

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
# UI
# ======================
st.set_page_config(layout="wide")
st.title("📖 Spanish Reader v8.0")

mode = st.radio("Mode", ["Read","Audio","Flashcards","Calendar"])

# ======================
# READ
# ======================
if mode == "Read":

    uploaded = st.file_uploader("Upload file", type=["pdf","docx","txt"])

    text = ""

    if uploaded:
        if uploaded.name.endswith(".pdf"):
            text = read_pdf(uploaded)
        elif uploaded.name.endswith(".docx"):
            text = read_docx(uploaded)
        elif uploaded.name.endswith(".txt"):
            text = read_txt(uploaded)

    text = st.text_area("Text", value=text, height=300)

    word = st.text_input("Unknown word")

    if word:
        df = add_word(word, text)
        st.success("Saved!")

        st.text_area("Saved words", df.to_string(), height=200)

# ======================
# AUDIO
# ======================
if mode == "Audio":

    audio = st.file_uploader("Upload audio", type=["mp3","wav","m4a"])

    if audio:
        st.audio(audio)

    text = st.text_area("Paste transcript", height=300)

    word = st.text_input("Unknown word from audio")

    if word:
        df = add_word(word, text)
        st.success("Saved!")

        st.text_area("Saved words", df.to_string(), height=200)

# ======================
# FLASHCARDS
# ======================
if mode == "Flashcards":

    df = load_words()

    option = st.selectbox("Mode", ["Due","Random","Serial"])

    if option == "Due":
        df = df[df["next_review"] <= str(date.today())]
    elif option == "Random":
        df = df.sample(frac=1)
    elif option == "Serial":
        df = df.sort_values("date")

    if df.empty:
        st.info("No cards available")
    else:
        if "index" not in st.session_state:
            st.session_state.index = 0
        if "show" not in st.session_state:
            st.session_state.show = False

        row = df.iloc[st.session_state.index % len(df)]

        st.markdown(f"## {row['word']}")

        if st.button("Show"):
            st.session_state.show = True

        if st.session_state.show:
            st.write(row["translation"])
            st.write(f"lemma: {row['lemma']}")
            st.write(f"pos: {row['pos']}")
            st.write(f"sentence: {row['sentence']}")

            col1, col2 = st.columns(2)

            if col1.button("Correct"):
                updated = update_srs(row.copy(), True)
                full = load_words()
                full.loc[full["word"] == row["word"]] = updated
                save_words(full)
                st.session_state.index += 1
                st.session_state.show = False
                st.rerun()

            if col2.button("Wrong"):
                updated = update_srs(row.copy(), False)
                full = load_words()
                full.loc[full["word"] == row["word"]] = updated
                save_words(full)
                st.session_state.index += 1
                st.session_state.show = False
                st.rerun()

# ======================
# CALENDAR
# ======================
if mode == "Calendar":

    log = load_log()

    today = date.today()
    year, month = today.year, today.month
    cal = calendar.monthcalendar(year, month)

    st.subheader(f"{calendar.month_name[month]} {year}")

    # STREAK
    log_sorted = log.sort_values("date", ascending=False)
    streak = 0

    for i in range(len(log_sorted)):
        d = datetime.strptime(log_sorted.iloc[i]["date"], "%Y-%m-%d").date()
        if d == today - timedelta(days=streak):
            streak += 1
        else:
            break

    st.success(f"🔥 Streak: {streak} days")

    st.markdown("### ✅ Activity Calendar")

    for week in cal:
        cols = st.columns(7)
        for i, day in enumerate(week):
            if day == 0:
                cols[i].write("")
            else:
                d_str = f"{year}-{month:02d}-{day:02d}"
                if d_str in log["date"].values:
                    cols[i].markdown(f"✅ {day}")
                else:
                    cols[i].markdown(f"⬜ {day}")

    st.markdown("### 🔥 Heatmap")

    for week in cal:
        cols = st.columns(7)
        for i, day in enumerate(week):
            if day == 0:
                cols[i].write("")
            else:
                d_str = f"{year}-{month:02d}-{day:02d}"

                count = 0
                if d_str in log["date"].values:
                    count = int(log.loc[log["date"] == d_str]["count"].values[0])

                if count == 0:
                    cols[i].markdown(f"⬜ {day}")
                elif count < 3:
                    cols[i].markdown(f"🟩 {day}")
                elif count < 6:
                    cols[i].markdown(f"🟨 {day}")
                else:
                    cols[i].markdown(f"🟥 {day}")
