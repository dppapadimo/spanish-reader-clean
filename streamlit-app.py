# =========================================
# Spanish Reader v8.5.1
# FIXED SESSION + PERSISTENCE VERSION
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


def translate(word):

    try:
        return GoogleTranslator(
            source="auto",
            target="el"
        ).translate(word)

    except Exception as e:
        return f"Translation Error: {e}"


def save_all():

    st.session_state.words_df.to_excel(
        WORDS_FILE,
        index=False
    )

    st.session_state.log_df.to_excel(
        LOG_FILE,
        index=False
    )


# ======================
# INIT SESSION STATE
# ======================

if "words_df" not in st.session_state:
    st.session_state.words_df = load_words()

if "log_df" not in st.session_state:
    st.session_state.log_df = load_log()

if "words_loaded" not in st.session_state:
    st.session_state.words_loaded = False

if "log_loaded" not in st.session_state:
    st.session_state.log_loaded = False


# ======================
# ADD WORD
# ======================

def add_word(word, translation, text):

    clean_word = word.strip().lower()

    df = st.session_state.words_df

    # ======================
    # DUPLICATE PROTECTION
    # ======================

    existing_words = (
        df["word"]
        .astype(str)
        .str.lower()
        .str.strip()
        .values
    )

    if clean_word in existing_words:
        return "duplicate", len(df)

    before = len(df)

    # ======================
    # NEW RECORD
    # ======================

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

    # ======================
    # APPEND
    # ======================

    df = pd.concat(
        [df, pd.DataFrame([new])],
        ignore_index=True
    )

    st.session_state.words_df = df

    # ======================
    # UPDATE LOG
    # ======================

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

    # ======================
    # AUTO SAVE
    # ======================

    save_all()

    after = len(df)

    return before, after


# ======================
# UI
# ======================

st.title("📖 Spanish Reader v8.5.1")

mode = st.radio(
    "Mode",
    ["Read", "Audio", "Flashcards", "Calendar"]
)

# ======================
# DATA MANAGEMENT
# ======================

st.markdown("## 📁 Data Management")

# ======================
# WORDS UPLOAD
# ======================

uploaded_excel = st.file_uploader(
    "Upload Words Excel",
    type=["xlsx"]
)

if uploaded_excel and not st.session_state.words_loaded:

    try:

        df = fix_columns(
            pd.read_excel(uploaded_excel)
        )

        st.session_state.words_df = df.copy()

        st.session_state.words_loaded = True

        save_all()

        st.success("Words loaded successfully")
        st.info(f"Loaded records: {len(df)}")

    except Exception as e:
        st.error(f"Upload Error: {e}")

# ======================
# LOG UPLOAD
# ======================

uploaded_log = st.file_uploader(
    "Upload Log Excel",
    type=["xlsx"]
)

if uploaded_log and not st.session_state.log_loaded:

    try:

        log = pd.read_excel(uploaded_log)

        st.session_state.log_df = log

        st.session_state.log_loaded = True

        save_all()

        st.success("Log loaded successfully")
        st.info(f"Log rows: {len(log)}")

    except Exception as e:
        st.error(f"Log Upload Error: {e}")

# ======================
# SAVE SESSION
# ======================

st.markdown("## 💾 Save Session")

st.info(
    f"Words ready: {len(st.session_state.words_df)}"
)

st.info(
    f"Logs ready: {len(st.session_state.log_df)}"
)

if st.button("💾 Save Session Now"):

    save_all()

    st.success("Session saved successfully")

# ======================
# DOWNLOAD BUTTONS
# ======================

if os.path.exists(WORDS_FILE):

    with open(WORDS_FILE, "rb") as f:

        st.download_button(
            "⬇️ Download Words",
            f,
            file_name=WORDS_FILE
        )

if os.path.exists(LOG_FILE):

    with open(LOG_FILE, "rb") as f:

        st.download_button(
            "⬇️ Download Logs",
            f,
            file_name=LOG_FILE
        )

# ======================
# READ
# ======================

if mode == "Read":

    st.markdown("## 📖 Read")

    st.info(
        f"Saved Words Total: "
        f"{len(st.session_state.words_df)}"
    )

    text = st.text_area(
        "Text",
        height=300
    )

    word = st.text_input(
        "Input Unknown Word"
    )

    if word:

        clean_word = word.strip()

        st.markdown(f"### **{clean_word}**")

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
                    f"Saved: {clean_word}"
                )

                st.info(
                    f"Before: {before} → After: {after}"
                )

                st.rerun()

# ======================
# AUDIO
# ======================

if mode == "Audio":

    st.markdown("## 🎧 Audio")

    st.info(
        f"Saved Words Total: "
        f"{len(st.session_state.words_df)}"
    )

    text = st.text_area(
        "Paste transcript",
        height=300
    )

    word = st.text_input(
        "Input Unknown Word",
        key="audio_word"
    )

    if word:

        clean_word = word.strip()

        st.markdown(f"### **{clean_word}**")

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
                    f"Saved: {clean_word}"
                )

                st.info(
                    f"Before: {before} → After: {after}"
                )

                st.rerun()

# ======================
# FLASHCARDS
# ======================

if mode == "Flashcards":

    st.markdown("## 🧠 Flashcards")

    df = st.session_state.words_df

    total = len(df)

    # ======================
    # LIVE REFRESH
    # ======================

    if "fc_len" not in st.session_state:
        st.session_state.fc_len = total

    if total != st.session_state.fc_len:

        st.session_state.fc_index = 0

        st.session_state.show_answer = False

        st.session_state.fc_len = total

        st.rerun()

    st.info(
        f"Words in flashcards: {total}"
    )

    if total == 0:

        st.warning("No words available")

    else:

        if "fc_index" not in st.session_state:
            st.session_state.fc_index = 0

        if "show_answer" not in st.session_state:
            st.session_state.show_answer = False

        if st.session_state.fc_index >= total:
            st.session_state.fc_index = 0

        row = df.iloc[
            st.session_state.fc_index
        ]

        st.markdown(
            f"### 🟦 {row['word']}"
        )

        if st.button(
            "👁 Show Answer",
            key="show_btn"
        ):

            st.session_state.show_answer = True

        if st.session_state.show_answer:

            st.success(
                row["translation"]
            )

        col1, col2 = st.columns(2)

        with col1:

            if st.button(
                "➡️ Next",
                key="next_btn"
            ):

                st.session_state.fc_index = (
                    st.session_state.fc_index + 1
                ) % total

                st.session_state.show_answer = False

                st.rerun()

        with col2:

            if st.button(
                "🔄 Reset",
                key="reset_btn"
            ):

                st.session_state.fc_index = 0

                st.session_state.show_answer = False

                st.rerun()

# ======================
# CALENDAR
# ======================

if mode == "Calendar":

    st.markdown("## 📅 Calendar")

    log = st.session_state.log_df

    st.info(
        f"Log entries: {len(log)}"
    )

    st.dataframe(log)

# ======================
# DEBUG INFO
# ======================

with st.expander("⚙️ Debug"):

    st.write(
        "Words Loaded:",
        st.session_state.words_loaded
    )

    st.write(
        "Log Loaded:",
        st.session_state.log_loaded
    )

    st.write(
        "Words Count:",
        len(st.session_state.words_df)
    )

    st.write(
        "Logs Count:",
        len(st.session_state.log_df)
    )
