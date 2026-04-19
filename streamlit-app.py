in# =========================================
# Spanish Reader v8.2 (STABLE)
# =========================================

import streamlit as st
import pandas as pd
from deep_translator import GoogleTranslator
import PyPDF2
from docx import Document
from datetime import date, timedelta
import calendar
import os
import spacy

WORDS_FILE = "spanish_words_unknown.xlsx"
LOG_FILE = "study_log.xlsx"

@st.cache_resource
def load_spacy_model():
    return spacy.load("es_core_news_sm")

nlp = load_spacy_model()

# ======================
# LOAD / SAVE
# ======================
def load_words():
    if os.path.exists(WORDS_FILE):
        return pd.read_excel(WORDS_FILE)
    return pd.DataFrame(columns=[
        "word","translation","lemma","pos","sentence",
        "difficulty","date","ease","interval","repetitions","next_review"
    ])

def save_words(df):
    df.to_excel(WORDS_FILE, index=False)

def load_log():
    if os.path.exists(LOG_FILE):
        return pd.read_excel(LOG_FILE)
    return pd.DataFrame(columns=["date","count"])

def save_log(df):
    df.to_excel(LOG_FILE, index=False)

# ======================
# TRANSLATE
# ======================
def translate(word):
    return GoogleTranslator(source="auto", target="el").translate(word)

# ======================
# NLP
# ======================
def analyze_word(word):
    doc = nlp(word)
    token = doc[0]
    return token.lemma_, token.pos_

def extract_sentence(text, word):
    if not text:
        return ""
    doc = nlp(text)
    for sent in doc.sents:
        if word.lower() in sent.text.lower():
            return sent.text
    return ""

# ======================
# ADD WORD
# ======================
def add_word(word, translation, text):
    df = load_words()

    if word in df["word"].values:
        return df

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

    log = load_log()
    if today in log["date"].astype(str).values:
        log.loc[log["date"] == today, "count"] += 1
    else:
        log = pd.concat([log, pd.DataFrame([{"date": today, "count": 1}])])
    save_log(log)

    return df

# ======================
# SRS
# ======================
def update_srs(row, correct):
    row = row.copy()

    if correct:
        row["repetitions"] += 1
        if row["repetitions"] == 1:
            row["interval"] = 1
        elif row["repetitions"] == 2:
            row["interval"] = 3
        else:
            row["interval"] = int(row["interval"] * 2)
    else:
        row["repetitions"] = 0
        row["interval"] = 1

    row["next_review"] = str(date.today() + timedelta(days=int(row["interval"])))
    return row

# ======================
# FILE READERS
# ======================
def read_pdf(file):
    reader = PyPDF2.PdfReader(file)
    return " ".join([p.extract_text() or "" for p in reader.pages])

def read_docx(file):
    doc = Document(file)
    return "\n".join([p.text for p in doc.paragraphs])

def read_txt(file):
    return file.read().decode("utf-8")

# ======================
# UI
# ======================
st.set_page_config(layout="wide")
st.title("📖 Spanish Reader v8.2")

mode = st.radio("Mode", ["Read","Audio","Flashcards","Calendar"])

# ======================
# SIDEBAR DATA CONTROL
# ======================
st.sidebar.subheader("📁 Data Files")

# Download
if os.path.exists(WORDS_FILE):
    with open(WORDS_FILE, "rb") as f:
        st.sidebar.download_button("Download Words Excel", f, file_name=WORDS_FILE)

if os.path.exists(LOG_FILE):
    with open(LOG_FILE, "rb") as f:
        st.sidebar.download_button("Download Calendar Excel", f, file_name=LOG_FILE)

# Upload
st.sidebar.subheader("📂 Load Existing Data")

uploaded_excel = st.sidebar.file_uploader("Upload words Excel", type=["xlsx"])
if uploaded_excel:
    pd.read_excel(uploaded_excel).to_excel(WORDS_FILE, index=False)
    st.success("Words loaded!")
    st.rerun

uploaded_log = st.sidebar.file_uploader("Upload calendar Excel", type=["xlsx"])
if uploaded_log:
    pd.read_excel(uploaded_log).to_excel(LOG_FILE, index=False)
    st.success("Log loaded!")
    st.rerun

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
        t = translate(word)
        st.success(t)

        df = add_word(word, t, text)

        pretty = ""
        for _, r in df.iterrows():
            pretty += f"{r['word']} → {r['translation']}\n"
            pretty += f"({r['lemma']} | {r['pos']})\n"
            pretty += f"{r['sentence']}\n"
            pretty += "-"*40 + "\n"

        st.text_area("Saved words", pretty, height=250)

# ======================
# AUDIO
# ======================
if mode == "Audio":

    audio = st.file_uploader("Upload audio", type=["mp3","wav","m4a"])

    if audio:
        st.audio(audio)

    text = st.text_area("Paste transcript", height=300)

    word = st.text_input("Unknown word")

    if word:
        t = translate(word)
        st.success(t)

        df = add_word(word, t, text)

        pretty = ""
        for _, r in df.iterrows():
            pretty += f"{r['word']} → {r['translation']}\n"
            pretty += f"({r['lemma']} | {r['pos']})\n"
            pretty += f"{r['sentence']}\n"
            pretty += "-"*40 + "\n"

        st.text_area("Saved words", pretty, height=250)

# ======================
# FLASHCARDS
# ======================
if mode == "Flashcards":

    if "fc_index" not in st.session_state:
        st.session_state.fc_index = 0

    df = load_words()
    today = str(date.today())
    df = df[df["next_review"] <= today].reset_index(drop=True)

    if len(df) == 0:
        st.success("No cards today 🎉")
    else:
        i = st.session_state.fc_index % len(df)
        row = df.iloc[i]

        st.markdown(f"## {row['word']}")

        if st.button("Show"):
            st.success(row["translation"])
            st.write(row["lemma"], "|", row["pos"])
            st.write(row["sentence"])

        col1, col2, col3 = st.columns(3)

        if col1.button("Correct"):
            updated = update_srs(row, True)
            full = load_words()
            idx = full.index[full["word"] == row["word"]][0]
            for k in updated.index:
                full.at[idx, k] = updated[k]
            save_words(full)
            st.session_state.fc_index += 1
            st.rerun()

        if col2.button("Wrong"):
            updated = update_srs(row, False)
            full = load_words()
            idx = full.index[full["word"] == row["word"]][0]
            for k in updated.index:
                full.at[idx, k] = updated[k]
            save_words(full)
            st.session_state.fc_index += 1
            st.rerun()

        if col3.button("Next"):
            st.session_state.fc_index += 1
            st.rerun()

# ======================
# CALENDAR
# ======================
if mode == "Calendar":

    log = load_log()

    today = date.today()
    year, month = today.year, today.month

    cal = calendar.monthcalendar(year, month)

    st.markdown(f"## {calendar.month_name[month]} {year}")

    # headers
    cols = st.columns(7)
    for i, d in enumerate(["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]):
        cols[i].markdown(f"**{d}**")

    # grid
    for week in cal:
        cols = st.columns(7)

        for i, day in enumerate(week):

            if day == 0:
                cols[i].write("")
            else:
                d_str = f"{year}-{month:02d}-{day:02d}"

                count = 0
                if d_str in log["date"].astype(str).values:
                    count = int(log.loc[log["date"] == d_str, "count"].values[0])

                check = "✅" if count > 0 else "⬜"

                if count == 0:
                    heat = "⬜"
                elif count < 3:
                    heat = "🟩"
                elif count < 6:
                    heat = "🟨"
                else:
                    heat = "🟥"

                cols[i].markdown(f"{day}<br>{check} {heat}", unsafe_allow_html=True)
