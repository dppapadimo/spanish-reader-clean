# =========================================
# Spanish Reader v9.0
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
import streamlit.components.v1 as components

WORDS_FILE = "spanish_words_unknown.xlsx"
LOG_FILE = "study_log.xlsx"

st.set_page_config(layout="wide", initial_sidebar_state="expanded")

# ======================
# LOAD SPACY
# ======================
@st.cache_resource
def load_spacy_model():
    return spacy.load("es_core_news_sm")

nlp = load_spacy_model()

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

    df = df[EXPECTED_COLS]

    df["next_review"] = df["next_review"].astype(str).str[:10]
    df["next_review"] = df["next_review"].replace("nan", str(date.today()))
    df["next_review"] = df["next_review"].fillna(str(date.today()))

    return df

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

def analyze_word(word):
    t = nlp(word)[0]
    return t.lemma_, t.pos_

def extract_sentence(text, word):
    for s in nlp(text).sents:
        if word.lower() in s.text.lower():
            return s.text
    return ""

def add_word(word, translation, text):
    df = load_words()

    if word in df["word"].values:
        return df

    lemma, pos = analyze_word(word)
    sentence = extract_sentence(text, word)
    today = str(date.today())

    new = {
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

    df = pd.concat([df, pd.DataFrame([new])], ignore_index=True)
    save_words(df)

    log = load_log()
    if today in log["date"].astype(str).values:
        log.loc[log["date"] == today, "count"] += 1
    else:
        log = pd.concat([log, pd.DataFrame([{"date": today, "count": 1}])], ignore_index=True)

    save_log(log)

    return df

# ======================
# UI
# ======================
st.title("📖 Spanish Reader")

st.markdown("**Mode**")
mode = st.radio("", ["Dashboard","Read","Audio","Flashcards","Calendar"])

# ======================
# DATA MANAGEMENT
# ======================
st.markdown("## 📁 Data Management")

col1, col2 = st.columns(2)

with col1:
    uploaded_excel = st.file_uploader("Upload Words Excel", type=["xlsx"])
    if uploaded_excel:
        df = fix_columns(pd.read_excel(uploaded_excel))
        save_words(df)
        st.success("Words loaded!")
        # 🔥 ADD THIS
        st.info(f"Words in system: {len(load_words())}")
    

with col2:
    uploaded_log = st.file_uploader("Upload Log Excel", type=["xlsx"])
    if uploaded_log:
        pd.read_excel(uploaded_log).to_excel(LOG_FILE, index=False)
        st.success("Log loaded!")
        # 🔥 ADD THIS
        st.info(f"Logs in system: {len(load_log())}")

# ======================
# SAVE SESSION
# ======================
st.markdown("## 💾 Save Session")

col3, col4 = st.columns(2)
df = load_words()
# st.info(f"Words ready to download: {len(df)} 

with col3:
    df = load_words()
    st.info(f"Words ready to download: {len(df)} recirds")
    
    if os.path.exists(WORDS_FILE):
        with open(WORDS_FILE, "rb") as f:
            st.download_button("⬇️ Download Words", f, file_name=WORDS_FILE)

with col4:
    log = load_log()
    st.info(f"Logs ready to download: {len(log)} rows")

    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "rb") as f:
            st.download_button("⬇️ Download Logs", f, file_name=LOG_FILE)

# ======================
# DASHBOARD
# ======================
if mode == "Dashboard":
    st.markdown("## 📊 Dashboard")

    df = load_words()
    log = load_log()
    today_str = str(date.today())

    total_words = len(df)
    due_today = len(df[df["next_review"].astype(str) <= today_str])
    hard_words = len(df[df["difficulty"].astype(str).str.lower() == "hard"])

    streak = 0
    d = date.today()
    while True:
        if str(d) in log["date"].astype(str).values:
            streak += 1
            d -= timedelta(days=1)
        else:
            break

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("📖 Total Words", total_words)
    c2.metric("⏰ Due Today", due_today)
    c3.metric("🔥 Hard Words", hard_words)
    c4.metric("🏆 Streak", streak)

    st.markdown("---")
    st.info("Use Read / Audio to add words, Flashcards to review.")

# ======================
# READ
# ======================
if mode == "Read":
    st.markdown("## 📖 Read")

    uploaded = st.file_uploader("Upload file", type=["pdf","docx","txt"])

    text = ""
    if uploaded:
        if uploaded.name.endswith(".pdf"):
            reader = PyPDF2.PdfReader(uploaded)
            text = " ".join([p.extract_text() or "" for p in reader.pages])

        elif uploaded.name.endswith(".docx"):
            doc = Document(uploaded)
            text = "\n".join([p.text for p in doc.paragraphs])

        elif uploaded.name.endswith(".txt"):
            text = uploaded.read().decode("utf-8")

    text = st.text_area("Text", value=text, height=300)

    word = st.text_input("Input Unknown Word")

    st.info(f"Saved Words Total: {len(load_words())}")

    if word.strip():
        clean_word = word.strip()
        st.markdown(f"### **{clean_word}**")
        
        t = translate(clean_word)
        st.success(t)

        c1, c2 = st.columns(2)

        with c1:
            if st.button("💾 Save Word", key= "save.read"):
                
                add_word(clean_word, t, text)
                total = len(load_words())
                st.success(f"Word saved! Total words: {total}")
                

        with c2:
            if st.button("💡 Explain"):
                lemma, pos = analyze_word(word)
                st.info(f"Lemma: {lemma} | POS: {pos}")

# ======================
# AUDIO
# ======================
if mode == "Audio":
    st.markdown("## 🎧 Audio")

    audio = st.file_uploader("Upload audio", type=["mp3","wav","m4a"])

    if audio:
        st.audio(audio)

    text = st.text_area("Paste transcript", height=300)

    word = st.text_input("Input Unknown Word ")

    st.info(f"Saved Words Total: {len(load_words())}")

    if word:
        st.markdown(f"### **{word}**")

        t = translate(word)
        st.success(t)
        c1, c2 = st.columns(2)

        with c1:
            if st.button("💾 Save Word ", key="save_audio")
                add_word(word, t, text)
                total = len(load_words())
                st.success(f"Word saved! Total words: {total}")
                
                st.success("Word saved!")
                st.rerun()

        with c2:
            if st.button("💡 Explain "):
                lemma, pos = analyze_word(word)
                st.info(f"Lemma: {lemma} | POS: {pos}")

# ======================
# FLASHCARDS PRO v8.8
# ======================
if mode == "Flashcards":
    st.markdown("## 🧠 Flashcards PRO")

    df = load_words()

    if len(df) == 0:
        st.warning("No words loaded")

    else:
        today_str = str(date.today())

        study_mode = st.radio(
            "Study Mode",
            ["Serial", "Random", "Due Today", "Hard", "Smart Mix"],
            horizontal=True
        )

        df_filtered = df.copy()

        if study_mode == "Due Today":
            df_filtered = df[df["next_review"].astype(str) <= today_str]

        elif study_mode == "Hard":
            df_filtered = df[df["difficulty"].astype(str).str.lower() == "hard"]

        elif study_mode == "Random":
            df_filtered = df.sample(frac=1).reset_index(drop=True)

        elif study_mode == "Smart Mix":
            due = df[df["next_review"].astype(str) <= today_str]
            hard = df[df["difficulty"].astype(str).str.lower() == "hard"]
            rand = df.sample(min(5, len(df)))
            df_filtered = pd.concat([due, hard, rand]).drop_duplicates()
            df_filtered = df_filtered.sample(frac=1).reset_index(drop=True)

        else:
            df_filtered = df.reset_index(drop=True)

        if len(df_filtered) == 0:
            st.warning("No cards available in this mode")

        else:
            if "i" not in st.session_state or st.session_state.i >= len(df_filtered):
                st.session_state.i = 0

            i = st.session_state.i
            row = df_filtered.iloc[i]

            st.caption(f"Card {i+1} / {len(df_filtered)}")
            progress = (i + 1) / len(df_filtered)
            st.progress(progress)

            st.markdown(f"""
            <div style="
            padding:20px;
            border-radius:15px;
            background: linear-gradient(135deg,#4facfe,#00f2fe);
            text-align:center;
            color:white;
            font-size:34px;
            font-weight:bold;
            margin-bottom:10px;">
            {row['word']}
            </div>
            """, unsafe_allow_html=True)

            difficulty = str(row["difficulty"]).lower()
            if difficulty == "hard":
                badge = "🔴 Hard"
            elif difficulty == "easy":
                badge = "🟢 Easy"
            else:
                badge = "🟡 Medium"

            st.markdown(f"**Difficulty:** {badge}")

            if st.button("👀 Show Answer"):
                st.success(row["translation"])
                st.write(f"**Lemma:** {row['lemma']}")
                st.write(f"**POS:** {row['pos']}")
                st.info(row["sentence"])

            col1, col2, col3, col4, col5 = st.columns(5)

            def save_updated(updated):
                full = load_words()
                idx = full.index[full["word"] == row["word"]][0]
                for k in updated.index:
                    full.at[idx, k] = updated[k]
                save_words(full)

            if col1.button("❌ Again"):
                updated = row.copy()
                updated["interval"] = 1
                updated["ease"] = max(1.3, float(row["ease"]) - 0.2)
                updated["repetitions"] = 0
                updated["next_review"] = str(date.today() + timedelta(days=1))
                updated["difficulty"] = "hard"
                save_updated(updated)
                st.session_state.i += 1
                st.rerun()

            if col2.button("😬 Hard"):
                updated = row.copy()
                updated["interval"] = max(1, int(float(row["interval"])) + 1)
                updated["ease"] = max(1.3, float(row["ease"]) - 0.05)
                updated["repetitions"] = int(row["repetitions"]) + 1
                updated["next_review"] = str(date.today() + timedelta(days=int(updated["interval"])))
                updated["difficulty"] = "hard"
                save_updated(updated)
                st.session_state.i += 1
                st.rerun()

            if col3.button("🙂 Good"):
                updated = row.copy()
                updated["interval"] = max(1, int(float(row["interval"]) * float(row["ease"])))
                updated["repetitions"] = int(row["repetitions"]) + 1
                updated["next_review"] = str(date.today() + timedelta(days=int(updated["interval"])))
                updated["difficulty"] = "medium"
                save_updated(updated)
                st.session_state.i += 1
                st.rerun()

            if col4.button("😎 Easy"):
                updated = row.copy()
                updated["ease"] = float(row["ease"]) + 0.15
                updated["interval"] = max(1, int(float(row["interval"]) * float(updated["ease"])))
                updated["repetitions"] = int(row["repetitions"]) + 1
                updated["next_review"] = str(date.today() + timedelta(days=int(updated["interval"])))
                updated["difficulty"] = "easy"
                save_updated(updated)
                st.session_state.i += 1
                st.rerun()

            if col5.button("🔥 Toggle"):
                full = load_words()
                idx = full.index[full["word"] == row["word"]][0]
                current = str(full.at[idx, "difficulty"]).lower()
                if current == "hard":
                    full.at[idx, "difficulty"] = "medium"
                    st.toast("Removed Hard")
                else:
                    full.at[idx, "difficulty"] = "hard"
                    st.toast("Marked Hard")
                save_words(full)
                st.rerun()

# ======================
# CALENDAR PRO
# ======================
if mode == "Calendar":
    st.markdown("## 📅 Pro Calendar")

    log = load_log()
    today = date.today()

    # streak
    streak = 0
    d = today
    while True:
        d_str = str(d)
        if d_str in log["date"].astype(str).values:
            streak += 1
            d -= timedelta(days=1)
        else:
            break

    # monthly stats
    year, month = today.year, today.month
    month_prefix = f"{year}-{month:02d}"

    monthly_log = log[log["date"].astype(str).str.startswith(month_prefix)]

    days_studied = len(monthly_log)
    words_added = monthly_log["count"].sum() if len(monthly_log) > 0 else 0

    # top stats
    c1, c2, c3 = st.columns(3)
    c1.metric("🔥 Streak", f"{streak} days")
    c2.metric("📚 Days studied", days_studied)
    c3.metric("📖 Words added", int(words_added))

    st.markdown("---")

    st.markdown(
        f"<h3 style='text-align:center;'>{calendar.month_name[month]} {year}</h3>",
        unsafe_allow_html=True
    )

    cal = calendar.monthcalendar(year, month)

    html = """
    <style>
    body {
        font-family: Arial, sans-serif;
    }
    .calendar-grid {
        display:grid;
        grid-template-columns: repeat(7, 1fr);
        gap:6px;
        text-align:center;
        font-size:14px;
        padding:10px;
    }
    .day-header {
        font-weight:bold;
        padding:8px 0;
        background:#ddd;
        border-radius:8px;
    }
    .day-cell {
        border-radius:10px;
        padding:10px 0;
        min-height:60px;
        display:flex;
        flex-direction:column;
        justify-content:center;
        align-items:center;
        font-weight:bold;
    }
    </style>
    """

    html += "<div class='calendar-grid'>"

    headers = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
    for h in headers:
        html += f"<div class='day-header'>{h}</div>"

    for week in cal:
        for day in week:
            if day == 0:
                html += "<div></div>"
            else:
                d_str = f"{year}-{month:02d}-{day:02d}"

                count = 0
                if d_str in log["date"].astype(str).values:
                    count = int(log.loc[log["date"].astype(str) == d_str, "count"].values[0])

                if count == 0:
                    color = "#f0f0f0"
                elif count < 3:
                    color = "#8BC34A"
                elif count < 6:
                    color = "#FFC107"
                else:
                    color = "#F44336"

                html += f"""
                <div class='day-cell' style='background:{color};'>
                    <div>{day}</div>
                    <div style='font-size:12px;'>{count}</div>
                </div>
                """

    html += "</div>"

    components.html(html, height=700, scrolling=True)

    st.markdown("---")
    st.caption("Color = activity level | Number = words added that day")

