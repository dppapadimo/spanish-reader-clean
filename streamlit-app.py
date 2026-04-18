# ----------------------------------------
# Spanish Reader
# Version: 7.4 (Stable Read + Audio + Flashcards)
# ----------------------------------------

import streamlit as st
import pandas as pd
from deep_translator import GoogleTranslator
import PyPDF2
from docx import Document
from datetime import datetime
from io import BytesIO
import random
import spacy

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

if "last_word" not in st.session_state:
    st.session_state.last_word = ""

if "flash_index" not in st.session_state:
    st.session_state.flash_index = 0

if "show_answer" not in st.session_state:
    st.session_state.show_answer = False

# ======================
# FUNCTIONS
# ======================
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
                return sent.text.strip()
    return ""

def process_word(word, text, target_lang):
    clean = word.lower().strip()

    if not clean or clean == st.session_state.last_word:
        return

    st.session_state.last_word = clean

    translation = GoogleTranslator(
        source='auto',
        target=target_lang
    ).translate(clean)

    lemma, pos = get_word_info(clean)
    sentence = extract_sentence(text, clean)

    st.success(translation)
    st.info(f"{pos} — {lemma}")

    if sentence:
        st.caption(f"📌 {sentence}")

    exists = any(w["word"] == clean for w in st.session_state.words_data)

    if not exists:
        st.session_state.words_data.append({
            "word": clean,
            "translation": translation,
            "lemma": lemma,
            "pos": pos,
            "sentence": sentence,
            "difficulty": "medium",
            "date": datetime.now().strftime("%Y-%m-%d %H:%M")
        })

# ======================
# FILE READERS
# ======================
def read_pdf(file):
    reader = PyPDF2.PdfReader(file)
    return "\n".join([p.extract_text() for p in reader.pages])

def read_docx(file):
    doc = Document(file)
    return "\n".join([p.text for p in doc.paragraphs])

# ======================
# UI
# ======================
st.set_page_config(layout="wide")
st.title("📖 Spanish Reader")
st.caption("Version 7.4")

mode = st.radio("Mode:", ["Read", "Audio", "Flashcards"])

# ======================
# READ MODE
# ======================
if mode == "Read":

    st.subheader("📄 Input Text")

    option = st.radio(
        "Choose input:",
        ["Paste text", "Upload file"]
    )

    text = ""

    if option == "Paste text":
        text = st.text_area("Paste text", height=300)

    elif option == "Upload file":
        file = st.file_uploader("Upload TXT / PDF / DOCX", type=["txt", "pdf", "docx"])

        if file:
            if file.type == "text/plain":
                text = file.read().decode("utf-8")
            elif file.type == "application/pdf":
                text = read_pdf(file)
            else:
                text = read_docx(file)

            text = st.text_area("Text", text, height=300)

    lang = st.selectbox("Translate to:", ["Greek", "English"])
    target_lang = "el" if lang == "Greek" else "en"

    if text:

        st.subheader("✏️ input unknown word + Enter")
        word = st.text_input("")

        if word:
            process_word(word, text, target_lang)

        if st.session_state.words_data:
            st.subheader("📚 Words")

            view = "\n".join([
                f"{w['word']} → {w['translation']} ({w['pos']})"
                for w in st.session_state.words_data
            ])

            st.text_area("", view, height=200)

# ======================
# AUDIO MODE
# ======================
if mode == "Audio":

    st.subheader("🎧 Upload Audio")

    audio = st.file_uploader("Upload audio", type=["mp3", "wav", "m4a"])

    if audio:
        st.audio(audio)

    st.subheader("📝 Paste transcript")

    text = st.text_area("Paste transcript here", height=300)

    lang = st.selectbox("Translate to:", ["Greek", "English"])
    target_lang = "el" if lang == "Greek" else "en"

    if text:

        st.subheader("✏️ input unknown word + Enter")
        word = st.text_input("audio_word")

        if word:
            process_word(word, text, target_lang)

        if st.session_state.words_data:
            st.subheader("📚 Words")

            view = "\n".join([
                f"{w['word']} → {w['translation']} ({w['pos']})"
                for w in st.session_state.words_data
            ])

            st.text_area("", view, height=200)

# ======================
# FLASHCARDS
# ======================
if mode == "Flashcards":

    if not st.session_state.words_data:
        st.warning("No words yet.")
    else:

        mode_fc = st.radio("Mode:", ["Serial", "Random"])

        words = st.session_state.words_data

        if mode_fc == "Random":
            word = random.choice(words)
        else:
            index = st.session_state.flash_index % len(words)
            word = words[index]

        st.markdown(f"## {word['word']}")

        if st.button("Show answer"):
            st.session_state.show_answer = True

        if st.button("Next"):
            st.session_state.flash_index += 1
            st.session_state.show_answer = False
            st.rerun()

        if st.session_state.show_answer:
            st.success(word["translation"])
            st.info(word.get("sentence", ""))

            difficulty = st.radio(
                "Difficulty",
                ["easy", "medium", "hard"],
                key=f"diff_{word['word']}"
            )

            word["difficulty"] = difficulty

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
    st.session_state.flash_index = 0
