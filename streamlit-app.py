import streamlit as st
import pandas as pd
from deep_translator import GoogleTranslator
from datetime import date, timedelta
import os
import matplotlib.pyplot as plt

# =========================
# CONFIG
# =========================

WORDS_FILE = "spanish_words_unknown.xlsx"
LOG_FILE = "study_log.xlsx"

EXPECTED_COLS = [
    "word",
    "translation",
    "lemma",
    "pos",
    "sentence",
    "difficulty",
    "date",
    "ease",
    "interval",
    "repetitions",
    "next_review",
    "status"
]

# =========================
# HELPERS
# =========================

def fix_columns(df):
    df.columns = [c.lower().strip() for c in df.columns]

    for col in EXPECTED_COLS:
        if col not in df.columns:
            df[col] = ""

    return df[EXPECTED_COLS]


def load_words():
    if os.path.exists(WORDS_FILE):
        try:
            return fix_columns(pd.read_excel(WORDS_FILE))
        except:
            pass
    return pd.DataFrame(columns=EXPECTED_COLS)


def load_log():
    if os.path.exists(LOG_FILE):
        try:
            return pd.read_excel(LOG_FILE)
        except:
            pass
    return pd.DataFrame(columns=["date", "count"])


@st.cache_data(show_spinner=False)
def translate(word):
    try:
        return GoogleTranslator(source="auto", target="el").translate(word)
    except Exception as e:
        return f"Translation Error: {e}"


def save_all():
    st.session_state.words_df.to_excel(WORDS_FILE, index=False)
    st.session_state.log_df.to_excel(LOG_FILE, index=False)


def get_due_words(df):
    if len(df) == 0:
        return df

    df2 = df.copy()
    df2["next_review"] = pd.to_datetime(df2["next_review"], errors="coerce")

    today = date.today()
    return df2[df2["next_review"].dt.date <= today]


# =========================
# SPACED REPETITION
# =========================

def update_review(index, grade):
    df = st.session_state.words_df
    row = df.iloc[index]

    ease = float(row["ease"])
    interval = int(row["interval"])
    repetitions = int(row["repetitions"])

    if grade == "Again":
        interval = 1
        repetitions = 0
        ease = max(1.3, ease - 0.2)

    elif grade == "Hard":
        interval = max(1, int(interval * 1.2))
        repetitions += 1
        ease = max(1.3, ease - 0.05)

    elif grade == "Good":
        interval = max(1, int(interval * ease))
        repetitions += 1

    elif grade == "Easy":
        interval = max(2, int(interval * ease * 1.5))
        repetitions += 1
        ease += 0.1

    next_review = date.today() + timedelta(days=interval)

    df.at[index, "ease"] = round(ease, 2)
    df.at[index, "interval"] = interval
    df.at[index, "repetitions"] = repetitions
    df.at[index, "next_review"] = str(next_review)

    df.at[index, "status"] = "mastered" if repetitions >= 10 else "learning"

    st.session_state.words_df = df
    save_all()


# =========================
# SESSION STATE
# =========================

if "words_df" not in st.session_state:
    st.session_state.words_df = load_words()

if "log_df" not in st.session_state:
    st.session_state.log_df = load_log()

if "words_loaded" not in st.session_state:
    st.session_state.words_loaded = False

if "log_loaded" not in st.session_state:
    st.session_state.log_loaded = False


# =========================
# ADD WORD
# =========================

def add_word(word, translation, text):
    clean_word = word.strip().lower()
    df = st.session_state.words_df

    existing = df["word"].astype(str).str.lower().str.strip().values

    if clean_word in existing:
        return "duplicate", len(df)

    before = len(df)

    new = {
        "word": word.strip(),
        "translation": translation,
        "lemma": "",
        "pos": "",
        "sentence": text[:180],
        "difficulty": "medium",
        "date": str(date.today()),
        "ease": 2.5,
        "interval": 1,
        "repetitions": 0,
        "next_review": str(date.today()),
        "status": "learning"
    }

    df = pd.concat([df, pd.DataFrame([new])], ignore_index=True)
    st.session_state.words_df = df

    log = st.session_state.log_df
    today = str(date.today())

    if today in log["date"].astype(str).values:
        log.loc[log["date"].astype(str) == today, "count"] += 1
    else:
        log = pd.concat([log, pd.DataFrame([{"date": today, "count": 1}])], ignore_index=True)

    st.session_state.log_df = log

    save_all()

    return before, len(df)


# =========================
# UI
# =========================

st.set_page_config(page_title="Spanish Reader v8.5.3", layout="wide")
st.title("📖 Spanish Reader v8.5.3")

mode = st.sidebar.radio("Mode", ["Read", "Audio", "Flashcards", "Search", "Statistics", "Calendar"])


# =========================
# DASHBOARD
# =========================

df_global = st.session_state.words_df
due_words = get_due_words(df_global)

c1, c2, c3, c4 = st.columns(4)

c1.metric("Total", len(df_global))
c2.metric("Due", len(due_words))
c3.metric("Mastered", len(df_global[df_global["status"] == "mastered"]))
c4.metric("Learning", len(df_global[df_global["status"] == "learning"]))


# =========================
# READ
# =========================

if mode == "Read":
    st.subheader("Read")

    text = st.text_area("Text", height=250)
    word = st.text_input("Unknown word")

    if word:
        translation = translate(word)
        st.success(translation)

        if st.button("Save"):
            result = add_word(word, translation, text)

            if result[0] == "duplicate":
                st.warning("Already exists")
            else:
                st.success(f"Saved {result}")


# =========================
# AUDIO
# =========================

if mode == "Audio":
    st.subheader("Audio")

    text = st.text_area("Transcript", height=250)
    word = st.text_input("Word", key="audio")

    if word:
        translation = translate(word)
        st.success(translation)

        if st.button("Save Audio", key="audio_btn"):
            result = add_word(word, translation, text)

            if result[0] == "duplicate":
                st.warning("Already exists")
            else:
                st.success(f"Saved {result}")


# =========================
# FLASHCARDS
# =========================

if mode == "Flashcards":
    st.subheader("Due Reviews")

    due_df = get_due_words(st.session_state.words_df)

    if len(due_df) == 0:
        st.success("No due cards")
    else:
        if "i" not in st.session_state:
            st.session_state.i = 0

        idxs = due_df.index.tolist()
        real_index = idxs[st.session_state.i]

        row = st.session_state.words_df.iloc[real_index]

        st.write("###", row["word"])

        if st.button("Show"):
            st.success(row["translation"])

        col1, col2, col3, col4 = st.columns(4)

        if col1.button("Again"):
            update_review(real_index, "Again")
            st.rerun()

        if col2.button("Hard"):
            update_review(real_index, "Hard")
            st.rerun()

        if col3.button("Good"):
            update_review(real_index, "Good")
            st.rerun()

        if col4.button("Easy"):
            update_review(real_index, "Easy")
            st.rerun()


# =========================
# SEARCH
# =========================

if mode == "Search":
    st.subheader("Search")

    q = st.text_input("Search")
    df = st.session_state.words_df

    if q:
        df = df[df["word"].str.contains(q, case=False)]

    st.dataframe(df)


# =========================
# STATISTICS
# =========================

if mode == "Statistics":
    st.subheader("Stats")

    log = st.session_state.log_df

    if len(log) > 0:
        log["date"] = pd.to_datetime(log["date"])

        fig, ax = plt.subplots()
        ax.plot(log["date"], log["count"])

        st.pyplot(fig)

    st.dataframe(log)


# =========================
# CALENDAR
# =========================

if mode == "Calendar":
    st.subheader("Calendar")
    st.dataframe(st.session_state.log_df)


# =========================
# DEBUG
# =========================

with st.expander("Debug"):
    st.write(st.session_state.words_df.head())
