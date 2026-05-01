# =========================================
# Spanish Reader v8.4.2 (SAFE APPEND DEBUG)
# =========================================

import streamlit as st
import pandas as pd
from deep_translator import GoogleTranslator
from datetime import date
import os

WORDS_FILE = "spanish_words_unknown.xlsx"
LOG_FILE = "study_log.xlsx"

EXPECTED_COLS = [
    "word","translation","lemma","pos","sentence",
    "difficulty","date","ease","interval","repetitions","next_review"
]

# ======================
# HELPERS
# ======================
def fix_columns(df):
    df.columns = [c.lower().strip() for c in df.columns]
    for col in EXPECTED_COLS:
        if col not in df.columns:
            df[col] = ""
    return df[EXPECTED_COLS]

def load_words():
    if os.path.exists(WORDS_FILE):
        return fix_columns(pd.read_excel(WORDS_FILE))
    return pd.DataFrame(columns=EXPECTED_COLS)

def save_words(df):
    df.to_excel(WORDS_FILE, index=False)

def load_log():
    if os.path.exists(LOG_FILE):
        return pd.read_excel(LOG_FILE)
    return pd.DataFrame(columns=["date","count"])

def save_log(df):
    df.to_excel(LOG_FILE, index=False)

def translate(word):
    return GoogleTranslator(source="auto", target="el").translate(word)

# ======================
# SAFE ADD WORD
# ======================
def add_word(word, translation, text):

    df = load_words()
    before = len(df)

    clean_word = word.strip()

    new = {
        "word": clean_word,
        "translation": translation,
        "lemma": "",
        "pos": "",
        "sentence": text[:120],
        "difficulty": "medium",
        "date": str(date.today()),
        "ease": 2.5,
        "interval": 1,
        "repetitions": 0,
        "next_review": str(date.today())
    }

    # 🔥 ALWAYS APPEND (no blocking)
    df = pd.concat([df, pd.DataFrame([new])], ignore_index=True)

    save_words(df)

    after = len(df)

    # LOG UPDATE
    log = load_log()
    today = str(date.today())

    if today in log["date"].astype(str).values:
        log.loc[log["date"] == today, "count"] += 1
    else:
        log = pd.concat([log, pd.DataFrame([{"date": today, "count": 1}])], ignore_index=True)

    save_log(log)

    return before, after

# ======================
# UI
# ======================
st.title("📖 Spanish Reader")

mode = st.radio("Mode", ["Read","Audio","Flashcards","Calendar"])

# ======================
# DATA MANAGEMENT
# ======================
st.markdown("## 📁 Data Management")

uploaded_excel = st.file_uploader("Upload Words Excel", type=["xlsx"])

if uploaded_excel:
    df = fix_columns(pd.read_excel(uploaded_excel))
    save_words(df)

    st.success("Words loaded")
    st.info(f"Loaded records: {len(df)}")
    st.info(f"System records after load: {len(load_words())}")

uploaded_log = st.file_uploader("Upload Log Excel", type=["xlsx"])

if uploaded_log:
    pd.read_excel(uploaded_log).to_excel(LOG_FILE, index=False)

    st.success("Log loaded")
    st.info(f"Log rows: {len(load_log())}")

# ======================
# SAVE / DOWNLOAD
# ======================
st.markdown("## 💾 Save Session")

current_df = load_words()
current_log = load_log()

st.info(f"Words ready to download: {len(current_df)}")
st.info(f"Logs ready: {len(current_log)}")

if os.path.exists(WORDS_FILE):
    with open(WORDS_FILE, "rb") as f:
        st.download_button("⬇️ Download Words", f, file_name=WORDS_FILE)

if os.path.exists(LOG_FILE):
    with open(LOG_FILE, "rb") as f:
        st.download_button("⬇️ Download Logs", f, file_name=LOG_FILE)

# ======================
# READ
# ======================
if mode == "Read":
    st.markdown("## 📖 Read")

    st.info(f"Saved Words Total: {len(load_words())}")

    text = st.text_area("Text", height=300)
    word = st.text_input("Input Unknown Word")

    if word:
        st.markdown(f"### **{word}**")

        t = translate(word)
        st.success(t)

        if st.button("💾 Save Word"):
            before, after = add_word(word, t, text)

            st.success(f"Saved: {word}")
            st.info(f"Before: {before} → After: {after}")

# ======================
# AUDIO
# ======================
if mode == "Audio":
    st.markdown("## 🎧 Audio")

    st.info(f"Saved Words Total: {len(load_words())}")

    text = st.text_area("Paste transcript", height=300)
    word = st.text_input("Input Unknown Word ")

    if word:
        st.markdown(f"### **{word}**")

        t = translate(word)
        st.success(t)

        if st.button("💾 Save Word "):
            before, after = add_word(word, t, text)

            st.success(f"Saved: {word}")
            st.info(f"Before: {before} → After: {after}")

# ======================
# FLASHCARDS DEBUG
# ======================
if mode == "Flashcards":
    st.markdown("## 🧠 Flashcards")

    df = load_words()

    st.info(f"Words loaded in flashcards: {len(df)}")

    if len(df) > 0:
        st.dataframe(df.head(10))

# ======================
# CALENDAR DEBUG
# ======================
if mode == "Calendar":
    st.markdown("## 📅 Calendar")

    log = load_log()

    st.info(f"Log entries: {len(log)}")
    st.dataframe(log)
