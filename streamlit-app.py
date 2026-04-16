# ----------------------------------------
# Spanish Vocabulary Reader
# Version: 7.2 (Audio MVP)
# ----------------------------------------

import streamlit as st
import pandas as pd
from deep_translator import GoogleTranslator
import PyPDF2
from datetime import datetime
from io import BytesIO
import random
import spacy
from openai import OpenAI
import tempfile

# ======================
# OPENAI CLIENT
# ======================
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

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

if "audio_text" not in st.session_state:
    st.session_state.audio_text = ""

# ======================
# FUNCTIONS
# ======================
def get_word_info(word):
    doc = nlp(word)
    token = doc[0]
    return token.lemma_, token.pos_

def extract_sentence(text, word):
    doc = nlp(text)
    target = nlp(word)[0].lemma_

    for sent in doc.sents:
        for token in sent:
            if token.lemma_ == target:
                return sent.text.strip()
    return ""

def transcribe_audio(file):
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(file.read())
        tmp_path = tmp.name

    with open(tmp_path, "rb") as audio_file:
        transcript = client.audio.transcriptions.create(
            model="gpt-4o-transcribe",
            file=audio_file
        )

    return transcript.text

# ======================
# UI
# ======================
st.set_page_config(layout="wide")
st.title("📖 Spanish Reader + Audio")
st.caption("Version 7.2")

mode = st.radio("Mode:", ["Read", "Audio", "Flashcards"])

# ======================
# READ MODE
# ======================
if mode == "Read":

    text = st.text_area("Paste text", height=200)

# ======================
# AUDIO MODE
# ======================
elif mode == "Audio":

    st.subheader("🎧 Upload Audio")

    audio_file = st.file_uploader(
        "Upload podcast / audio",
        type=["mp3", "wav", "m4a"]
    )

    if audio_file:
        st.audio(audio_file)

        if st.button("🧠 Transcribe"):

            with st.spinner("Transcribing..."):
                text = transcribe_audio(audio_file)
                st.session_state.audio_text = text

    text = st.session_state.audio_text

# ======================
# COMMON TEXT PROCESSING
# ======================
if mode in ["Read", "Audio"]:

    lang = st.selectbox("Translate to:", ["Greek", "English"])
    target_lang = "el" if lang == "Greek" else "en"

    if "text" in locals() and text:

        st.subheader("📖 Text")
        st.text_area("", text, height=300)

        st.subheader("✏️ Input unknown word + Enter")

        word = st.text_input("")

        if word and word != st.session_state.last_word:

            st.session_state.last_word = word
            clean = word.lower().strip()

            translation = GoogleTranslator(
                source='auto',
                target=target_lang
            ).translate(clean)

            lemma, pos = get_word_info(clean)
            sentence = extract_sentence(text, clean)

            st.markdown(f"### {clean}")
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
                    "date": datetime.now().strftime("%Y-%m-%d %H:%M")
                })

        # WORD LIST
        if st.session_state.words_data:

            st.subheader("📚 Words")

            txt = "\n".join([
                f"{w['word']} → {w['translation']}"
                for w in st.session_state.words_data
            ])

            st.text_area("", txt, height=200)

# ======================
# FLASHCARDS
# ======================
if mode == "Flashcards":

    if not st.session_state.words_data:
        st.warning("No words yet.")
    else:

        words = st.session_state.words_data
        index = st.session_state.flash_index % len(words)
        word_obj = words[index]

        st.markdown(f"## {word_obj['word']}")

        if st.button("Show answer"):
            st.session_state.show_answer = True

        if st.button("Next"):
            st.session_state.flash_index += 1
            st.session_state.show_answer = False
            st.rerun()

        if st.session_state.show_answer:
            st.success(word_obj["translation"])
            st.info(word_obj.get("sentence", ""))

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
    st.session_state.audio_text = ""
