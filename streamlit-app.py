        # ----------------------------------------
# Spanish Reader
# Version: 7.3 (Clickable + Highlight + Auto-detect)
# ----------------------------------------

import streamlit as st
import pandas as pd
from deep_translator import GoogleTranslator
import PyPDF2
from datetime import datetime
from io import BytesIO
import spacy
import re

# ======================
# LOAD SPACY
# ======================
@st.cache_resource
def load_spacy_model():
    return spacy.load("es_core_news_sm")

nlp = load_spacy_model()

# ======================
# SESSION
# ======================
if "words_data" not in st.session_state:
    st.session_state.words_data = []

if "selected_words" not in st.session_state:
    st.session_state.selected_words = set()

# ======================
# FUNCTIONS
# ======================
def clean_word(word):
    return re.sub(r"[^\wáéíóúñü]", "", word.lower())

def get_word_info(word):
    doc = nlp(word)
    token = doc[0]
    return token.lemma_, token.pos_

def extract_sentence(text, word):
    doc = nlp(text)
    lemma = nlp(word)[0].lemma_

    for sent in doc.sents:
        for token in sent:
            if token.lemma_ == lemma:
                return sent.text
    return ""

def translate(word, target="el"):
    return GoogleTranslator(source='auto', target=target).translate(word)

def add_word(word, text, target_lang):
    clean = clean_word(word)
    if not clean:
        return

    if clean in st.session_state.selected_words:
        return

    translation = translate(clean, target_lang)
    lemma, pos = get_word_info(clean)
    sentence = extract_sentence(text, clean)

    st.session_state.selected_words.add(clean)

    st.session_state.words_data.append({
        "word": clean,
        "translation": translation,
        "lemma": lemma,
        "pos": pos,
        "sentence": sentence,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M")
    })

# ======================
# UI
# ======================
st.set_page_config(layout="wide")
st.title("📖 Spanish Reader")
st.caption("Version 7.3")

mode = st.radio("Mode:", ["Read", "Flashcards"])

# ======================
# READ MODE
# ======================
if mode == "Read":

    st.subheader("📄 Input Text")

    option = st.radio(
        "Choose input method:",
        ["Paste text", "Upload file"]
    )

    text = ""

    if option == "Paste text":
        text = st.text_area("Paste text", height=300)

    elif option == "Upload file":
        uploaded_file = st.file_uploader("Upload TXT or PDF", type=["txt", "pdf"])

        if uploaded_file:
            if uploaded_file.type == "text/plain":
                text = uploaded_file.read().decode("utf-8")

            elif uploaded_file.type == "application/pdf":
                reader = PyPDF2.PdfReader(uploaded_file)
                pages = [p.extract_text() for p in reader.pages]
                text = "\n".join(pages)

            text = st.text_area("Text", text, height=300)

    lang = st.selectbox("Translate to:", ["Greek", "English"])
    target_lang = "el" if lang == "Greek" else "en"

    if text:

        st.subheader("🧠 Click words")

        words = text.split()

        # AUTO DETECT (long words)
        auto_words = [w for w in words if len(clean_word(w)) > 6]

        st.caption("⚡ Suggested difficult words")

        for w in auto_words[:20]:
            if st.button(f"⭐ {clean_word(w)}"):
                add_word(w, text, target_lang)

        st.divider()

        st.subheader("📖 Text (click words)")

        cols = st.columns(6)

        for i, w in enumerate(words):
            clean = clean_word(w)

            if clean in st.session_state.selected_words:
                label = f"🟡 {clean}"
            else:
                label = clean

            with cols[i % 6]:
                if st.button(label, key=f"{i}_{clean}"):
                    add_word(w, text, target_lang)

        # WORD LIST
        if st.session_state.words_data:
            st.subheader("📚 Learned words")

            text_view = "\n".join([
                f"{w['word']} → {w['translation']} ({w['pos']})"
                for w in st.session_state.words_data
            ])

            st.text_area("", text_view, height=200)

# ======================
# FLASHCARDS
# ======================
if mode == "Flashcards":

    if not st.session_state.words_data:
        st.warning("No words yet.")
    else:

        import random

        word = random.choice(st.session_state.words_data)

        st.markdown(f"## {word['word']}")

        if st.button("Show answer"):
            st.success(word["translation"])
            st.info(word.get("sentence", ""))

# ======================
# EXPORT
# ======================
if st.session_state.words_data:

    df = pd.DataFrame(st.session_state.words_data)

    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False)

    st.download_button(
        "💾 Download Excel",
        buffer.getvalue(),
        file_name="words.xlsx"
    )

# ======================
# RESET
# ======================
if st.button("❌ Reset"):
    st.session_state.words_data = []
    st.session_state.selected_words = set()
