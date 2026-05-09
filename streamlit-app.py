# =========================================

# Spanish Reader v8.5.2

# Phase 1 Upgrade

# =========================================

# FEATURES

# =========================================

# ✔ Fixed session persistence

# ✔ Auto save

# ✔ Duplicate protection

# ✔ Real spaced repetition

# ✔ Due reviews system

# ✔ Search / filter

# ✔ Statistics dashboard

# ✔ Flashcard grading

# ✔ Review queue

# ✔ Live sync

# ✔ Study calendar

# =========================================

import streamlit as st
import pandas as pd
from deep_translator import GoogleTranslator
from datetime import date, timedelta
import os
import random
import matplotlib.pyplot as plt

# =========================================

# CONFIG

# =========================================

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

# =========================================

# HELPERS

# =========================================

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
    return GoogleTranslator(
        source="auto",
        target="el").translate(word)

    except Exception as e:
    return f"Translation Error: {e}"

def save_all():
    st.session_state.words_df.to_excel(
    WORDS_FILE,
    index=False)

    st.session_state.log_df.to_excel(
    LOG_FILE,
    index=False)

def get_due_words(df):
    if len(df) == 0:
    return df

today = date.today()

df2 = df.copy()

df2["next_review"] = pd.to_datetime(
    df2["next_review"],
    errors="coerce")

due = df2[
    df2["next_review"].dt.date <= today]

return due

# =========================================

# SPACED REPETITION

# =========================================

def update_review(index, grade):
df = st.session_state.words_df

row = df.iloc[index]

ease = float(row["ease"])
interval = int(row["interval"])
repetitions = int(row["repetitions"])

# =====================
# AGAIN
# =====================

if grade == "Again":

    interval = 1
    repetitions = 0
    ease = max(1.3, ease - 0.2)

# =====================
# HARD
# =====================

elif grade == "Hard":

    interval = max(1, int(interval * 1.2))
    repetitions += 1
    ease = max(1.3, ease - 0.05)

# =====================
# GOOD
# =====================

elif grade == "Good":

    interval = max(1, int(interval * ease))
    repetitions += 1

# =====================
# EASY
# =====================

elif grade == "Easy":

    interval = max(2, int(interval * ease * 1.5))
    repetitions += 1
    ease += 0.1

next_review = date.today() + timedelta(days=interval)

df.at[index, "ease"] = round(ease, 2)
df.at[index, "interval"] = interval
df.at[index, "repetitions"] = repetitions
df.at[index, "next_review"] = str(next_review)

# mastered
if repetitions >= 10:
    df.at[index, "status"] = "mastered"
else:
    df.at[index, "status"] = "learning"

st.session_state.words_df = df

save_all()

# =========================================

# SESSION STATE

# =========================================

if "words_df" not in st.session_state:
st.session_state.words_df = load_words()

if "log_df" not in st.session_state:
st.session_state.log_df = load_log()

if "words_loaded" not in st.session_state:
st.session_state.words_loaded = False

if "log_loaded" not in st.session_state:
st.session_state.log_loaded = False

# =========================================

# ADD WORD

# =========================================

def add_word(word, translation, text):
clean_word = word.strip().lower()

df = st.session_state.words_df

existing_words = (
    df["word"]
    .astype(str)
    .str.lower()
    .str.strip()
    .values)

if clean_word in existing_words:
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
    "status": "learning"}

df = pd.concat(
    [df, pd.DataFrame([new])],
    ignore_index=True)

st.session_state.words_df = df

# =====================
# UPDATE LOG
# =====================

log = st.session_state.log_df

today = str(date.today())

if today in log["date"].astype(str).values:

    log.loc[
        log["date"].astype(str) == today,
        "count"
    ] += 1

else:

    log = pd.concat(
        [
            log,
            pd.DataFrame([
                {
                    "date": today,
                    "count": 1
                }
            ])
        ],
        ignore_index=True
    )

st.session_state.log_df = log

save_all()

after = len(df)

return before, after

# =========================================

# UI

# =========================================

st.set_page_config(
page_title="Spanish Reader v8.5.2",
layout="wide"
)

st.title("📖 Spanish Reader v8.5.2")

mode = st.sidebar.radio(
"Mode",
[
"Read",
"Audio",
"Flashcards",
"Search",
"Statistics",
"Calendar"
]
)

# =========================================

# DATA MANAGEMENT

# =========================================

st.sidebar.markdown("## 📁 Data")

uploaded_excel = st.sidebar.file_uploader(
"Upload Words",
type=["xlsx"]
)

if uploaded_excel and not st.session_state.words_loaded:

df = fix_columns(
    pd.read_excel(uploaded_excel)
)

st.session_state.words_df = df.copy()

st.session_state.words_loaded = True

save_all()

st.sidebar.success("Words loaded")

uploaded_log = st.sidebar.file_uploader(
"Upload Logs",
type=["xlsx"]
)

if uploaded_log and not st.session_state.log_loaded:

log = pd.read_excel(uploaded_log)

st.session_state.log_df = log

st.session_state.log_loaded = True

save_all()

st.sidebar.success("Logs loaded")


# =========================================

# SAVE / DOWNLOAD

# =========================================

st.sidebar.markdown("## 💾 Save")

if st.sidebar.button("Save Session"):

save_all()

st.sidebar.success("Saved")


if os.path.exists(WORDS_FILE):


with open(WORDS_FILE, "rb") as f:

    st.sidebar.download_button(
        "⬇️ Download Words",
        f,
        file_name=WORDS_FILE
    )


if os.path.exists(LOG_FILE):


with open(LOG_FILE, "rb") as f:

    st.sidebar.download_button(
        "⬇️ Download Logs",
        f,
        file_name=LOG_FILE
    )


# =========================================

# DASHBOARD METRICS

# =========================================

df_global = st.session_state.words_df

due_words = get_due_words(df_global)

col1, col2, col3, col4 = st.columns(4)

with col1:
st.metric("Total Words", len(df_global))

with col2:
st.metric("Due Reviews", len(due_words))

with col3:
st.metric(
"Mastered",
len(df_global[df_global["status"] == "mastered"])
)

with col4:
st.metric(
"Learning",
len(df_global[df_global["status"] == "learning"])
)

# =========================================

# READ

# =========================================

if mode == "Read":


st.markdown("## 📖 Read")

text = st.text_area(
    "Paste Text",
    height=300
)

word = st.text_input(
    "Unknown Word"
)

if word:

    clean_word = word.strip()

    st.markdown(f"### {clean_word}")

    t = translate(clean_word)

    st.success(t)

    if st.button("💾 Save Word"):

        result = add_word(
            clean_word,
            t,
            text
        )

        if result[0] == "duplicate":

            st.warning(
                f"'{clean_word}' already exists"
            )

        else:

            before, after = result

            st.success(
                f"Saved | {before} → {after}"
            )

            st.rerun()


# =========================================

# AUDIO

# =========================================

if mode == "Audio":


st.markdown("## 🎧 Audio")

text = st.text_area(
    "Paste Transcript",
    height=300
)

word = st.text_input(
    "Unknown Word",
    key="audio_word"
)

if word:

    clean_word = word.strip()

    st.markdown(f"### {clean_word}")

    t = translate(clean_word)

    st.success(t)

    if st.button(
        "💾 Save Word",
        key="audio_save"
    ):

        result = add_word(
            clean_word,
            t,
            text
        )

        if result[0] == "duplicate":

            st.warning(
                f"'{clean_word}' already exists"
            )

        else:

            before, after = result

            st.success(
                f"Saved | {before} → {after}"
            )

            st.rerun()


# =========================================

# FLASHCARDS

# =========================================

if mode == "Flashcards":


st.markdown("## 🧠 Due Reviews")

due_df = get_due_words(
    st.session_state.words_df
)

total = len(due_df)

st.info(f"Due cards: {total}")

if total == 0:

    st.success("No reviews due today 🎉")

else:

    if "fc_index" not in st.session_state:
        st.session_state.fc_index = 0

    if "show_answer" not in st.session_state:
        st.session_state.show_answer = False

    if st.session_state.fc_index >= total:
        st.session_state.fc_index = 0

    review_indexes = due_df.index.tolist()

    current_real_index = review_indexes[
        st.session_state.fc_index
    ]

    row = st.session_state.words_df.iloc[
        current_real_index
    ]

    st.markdown(f"# 🟦 {row['word']}")

    st.caption(row["sentence"])

    if st.button("👁 Show Answer"):
        st.session_state.show_answer = True

    if st.session_state.show_answer:

        st.success(row["translation"])

        st.write(f"Ease: {row['ease']}")
        st.write(f"Interval: {row['interval']} days")
        st.write(f"Repetitions: {row['repetitions']}")

        col1, col2, col3, col4 = st.columns(4)

        with col1:

            if st.button("🔴 Again"):

                update_review(
                    current_real_index,
                    "Again"
                )

                st.session_state.show_answer = False

                st.rerun()

        with col2:

            if st.button("🟠 Hard"):

                update_review(
                    current_real_index,
                    "Hard"
                )

                st.session_state.show_answer = False

                st.rerun()

        with col3:

            if st.button("🟢 Good"):

                update_review(
                    current_real_index,
                    "Good"
                )

                st.session_state.show_answer = False

                st.rerun()

        with col4:

            if st.button("🔵 Easy"):

                update_review(
                    current_real_index,
                    "Easy"
                )

                st.session_state.show_answer = False

                st.rerun()

    if st.button("➡️ Next"):

        st.session_state.fc_index = (
            st.session_state.fc_index + 1
        ) % total

        st.session_state.show_answer = False

        st.rerun()


# =========================================

# SEARCH

# =========================================

if mode == "Search":


st.markdown("## 🔍 Search Words")

df = st.session_state.words_df

search = st.text_input("Search")

status_filter = st.selectbox(
    "Status",
    ["All", "learning", "mastered"]
)

filtered = df.copy()

if search:

    filtered = filtered[
        filtered["word"]
        .astype(str)
        .str.contains(search, case=False)
    ]

if status_filter != "All":

    filtered = filtered[
        filtered["status"] == status_filter
    ]

st.dataframe(filtered)


# =========================================

# STATISTICS

# =========================================

if mode == "Statistics":


st.markdown("## 📊 Statistics")

log = st.session_state.log_df

if len(log) == 0:

    st.warning("No statistics yet")

else:

    log2 = log.copy()

    log2["date"] = pd.to_datetime(log2["date"])

    fig, ax = plt.subplots(figsize=(10, 4))

    ax.plot(
        log2["date"],
        log2["count"]
    )

    ax.set_title("Words Learned Per Day")

    ax.set_xlabel("Date")

    ax.set_ylabel("Words")

    st.pyplot(fig)

    st.dataframe(log2)


# =========================================

# CALENDAR

# =========================================

if mode == "Calendar":


st.markdown("## 📅 Study Calendar")

log = st.session_state.log_df

st.dataframe(log)


# =========================================

# DEBUG

# =========================================

with st.expander("⚙️ Debug"):


st.write(
    st.session_state.words_df.head()
)

st.write(
    f"Words: {len(st.session_state.words_df)}"
)

st.write(
    f"Due: {len(get_due_words(st.session_state.words_df))}"
)


# INSTALL

pip install streamlit pandas openpyxl deep-translator matplotlib

# RUN

bash
streamlit run app.py

# WHAT IS NEW IN 8.5.2

## ✔ Real spaced repetition

* Again
* Hard
* Good
* Easy

## ✔ Due review system

Only review words due today.

## ✔ Statistics dashboard

Daily learning graph.

## ✔ Search system

Search and filter words.

## ✔ Mastered tracking

Words become mastered after enough repetitions.

## ✔ Cached translation

Faster translation requests.

## ✔ Stable persistence

No more rerun overwrite issue.
