# =========================================
# Spanish Reader v8.5 (State Based Storage)
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

def load_log():
    if os.path.exists(LOG_FILE):
        return pd.read_excel(LOG_FILE)
    return pd.DataFrame(columns=["date","count"])

def translate(word):
    return GoogleTranslator(source="auto", target="el").translate(word)

# ======================
# INIT SESSION STATE
# ======================
if "words_df" not in st.session_state:
    st.session_state.words_df = load_words()

if "log_df" not in st.session_state:
    st.session_state.log_df = load_log()

# ======================
# ADD WORD (APPEND ONLY)
# ======================
def add_word(word, translation, text):

    df = st.session_state.words_df
    before = len(df)

    new = {
        "word": word.strip(),
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

    df = pd.concat([df, pd.DataFrame([new])], ignore_index=True)
    st.session_state.words_df = df

    # update log
    log = st.session_state.log_df
    today = str(date.today())

    if today in log["date"].astype(str).values:
        log.loc[log["date"] == today, "count"] += 1
    else:
        log = pd.concat([log, pd.DataFrame([{"date": today, "count": 1}])], ignore_index=True)

    st.session_state.log_df = log

    after = len(df)
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
    st.session_state.words_df = df.copy()
    st.success("Words loaded")
    st.info(f"Loaded records: {len(df)}")

uploaded_log = st.file_uploader("Upload Log Excel", type=["xlsx"])

if uploaded_log:
    log = pd.read_excel(uploaded_log)
    st.session_state.log_df = log
    st.success("Log loaded")
    st.info(f"Log rows: {len(log)}")

# ======================
# SAVE SESSION
# ======================
st.markdown("## 💾 Save Session")

df_to_save = st.session_state.words_df
log_to_save = st.session_state.log_df

st.info(f"Words ready: {len(df_to_save)}")
st.info(f"Logs ready: {len(log_to_save)}")

# save to file before download
df_to_save.to_excel(WORDS_FILE, index=False)
log_to_save.to_excel(LOG_FILE, index=False)

with open(WORDS_FILE, "rb") as f:
    st.download_button("⬇️ Download Words", f, file_name=WORDS_FILE)

with open(LOG_FILE, "rb") as f:
    st.download_button("⬇️ Download Logs", f, file_name=LOG_FILE)

# ======================
# READ
# ======================
if mode == "Read":
    st.markdown("## 📖 Read")

    st.info(f"Saved Words Total: {len(st.session_state.words_df)}")

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
# AUDIO (FIXED - SESSION SAFE)
# ======================
if mode == "Audio":
    st.markdown("## 🎧 Audio")

    # 🔥 total words (shared with Read)
    st.info(f"Saved Words Total: {len(st.session_state.words_df)}")

    # transcript input
    text = st.text_area("Paste transcript", height=300)

    # 🔥 unique widget key (important)
    word = st.text_input("Input Unknown Word", key="audio_word")

    if word:
        clean_word = word.strip()

        st.markdown(f"### **{clean_word}**")

        t = translate(clean_word)
        st.success(t)

        # 🔥 unique button key
        if st.button("💾 Save Word", key="audio_save"):

            before, after = add_word(clean_word, t, text)

            st.success(f"Saved: {clean_word}")
            st.info(f"Before: {before} → After: {after}")
# ======================
# FLASHCARDS
# ======================
if mode == "Flashcards":
    st.markdown("## 🧠 Flashcards")

    df = st.session_state.words_df

    st.info(f"Words in flashcards: {len(df)}")

    if len(df) > 0:
        if "i" not in st.session_state:
            st.session_state.i = 0

        row = df.iloc[st.session_state.i]

        st.subheader(row["word"])

        if st.button("Show"):
            st.success(row["translation"])

        if st.button("Next"):
            st.session_state.i = (st.session_state.i + 1) % len(df)

# ======================
# CALENDAR
# ======================
if mode == "Calendar":
    st.markdown("## 📅 Calendar")

    log = st.session_state.log_df

    st.info(f"Log entries: {len(log)}")
    st.dataframe(log)
