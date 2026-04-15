# ----------------------------------------
# Spanish Vocabulary Reader
# Version: 6.9 (Smart NLP)
# ----------------------------------------

import streamlit as st
import pandas as pd
from deep_translator import GoogleTranslator
import PyPDF2
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
# SESSION STATE
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

    return {
        "lemma": token.lemma_,
        "pos": token.pos_,
        "is_verb": token.pos_ == "VERB"
    }

def format_pos(pos):
    mapping = {
        "VERB": "ρήμα",
        "NOUN": "ουσιαστικό",
        "ADJ": "επίθετο",
        "ADV": "επίρρημα",
        "PRON": "αντωνυμία",
        "DET": "άρθρο",
        "ADP": "πρόθεση",
        "CCONJ": "σύνδεσμος",
        "SCONJ": "υποτακτικός σύνδεσμος",
        "NUM": "αριθμός",
        "PART": "μόριο",
        "INTJ": "επιφώνημα"
    }
    return mapping.get(pos, pos)

# 🔥 NEW: smarter sentence extraction
def extract_sentence(text, target_word):
    doc = nlp(text)
    target_doc = nlp(target_word)
    target_lemma = target_doc[0].lemma_

    for sent in doc.sents:
        for token in sent:
            if token.lemma_ == target_lemma:
                return sent.text.strip()

    return ""

# ======================
# UI
# ======================
st.set_page_config(page_title="Spanish Reader", layout="wide")

st.title("📖 Spanish Vocabulary Reader")
st.caption("Version 6.9 (Smart NLP)")

# ======================
# MODE
# ======================
mode = st.radio("Mode:", ["Read", "Flashcards"])

# ======================
# READ MODE
# ======================
if mode == "Read":

    option = st.radio("Input:", ["Paste Text", "Upload File"])

    text = ""
    source_name = "pasted"

    if option == "Paste Text":
        text = st.text_area("Paste Spanish text:", height=150)

    elif option == "Upload File":
        file = st.file_uploader("Upload file", type=["txt", "pdf"])

        if file:
            source_name = file.name

            if file.type == "text/plain":
                text = file.read().decode("utf-8")

            else:
                reader = PyPDF2.PdfReader(file)
                text = "\n".join([
                    p.extract_text()
                    for p in reader.pages
                    if p.extract_text()
                ])

    lang = st.selectbox("Translate to:", ["Greek", "English"])
    target_lang = "el" if lang == "Greek" else "en"

    if text:
        st.subheader("📖 Text")
        st.text_area("", text, height=300)

        st.subheader("✏️ Input unknown word + Enter → translate + save")

        word = st.text_input("")

        if word and word != st.session_state.last_word:

            st.session_state.last_word = word
            clean = word.lower().strip()

            translation = GoogleTranslator(
                source='auto',
                target=target_lang
            ).translate(clean)

            info = get_word_info(clean)
            sentence = extract_sentence(text, clean)

            # DISPLAY
            st.markdown(f"### {clean}")
            st.success(translation)

            if info["is_verb"]:
                st.info(f"ρήμα — {info['lemma']}")
            else:
                st.info(format_pos(info["pos"]))

            if sentence:
                st.caption(f"📌 {sentence}")

            # SAVE
            exists = any(w["word"] == clean for w in st.session_state.words_data)

            if not exists:
                st.session_state.words_data.append({
                    "word": clean,
                    "translation": translation,
                    "lemma": info["lemma"],
                    "pos": info["pos"],
                    "sentence": sentence,
                    "difficulty": "medium",
                    "source": source_name,
                    "date": datetime.now().strftime("%Y-%m-%d %H:%M")
                })

        # WORD LIST
        if st.session_state.words_data:
            st.subheader("📚 Words")

            txt = "\n".join([
                f"{w['word']} → {w['translation']} ({w['lemma']})"
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
        total = len(words)

        learn_mode = st.radio("Order:", ["Sequential", "Random"])

        if learn_mode == "Sequential":
            index = st.session_state.flash_index % total
            word_obj = words[index]
            st.caption(f"Word {index+1} / {total}")
        else:
            word_obj = random.choice(words)

        st.subheader("📖 Word")
        st.markdown(f"## {word_obj['word']}")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("Show answer"):
                st.session_state.show_answer = True

        with col2:
            if st.button("➡️ Next"):
                st.session_state.show_answer = False
                st.session_state.flash_index += 1
                st.rerun()

        if st.session_state.show_answer:
            st.success(word_obj["translation"])
            st.info(f"lemma: {word_obj.get('lemma','')}")
            st.info(f"pos: {format_pos(word_obj.get('pos',''))}")

            if word_obj.get("sentence"):
                st.caption(f"📌 {word_obj['sentence']}")

            st.write("Difficulty:")

            c1, c2, c3 = st.columns(3)

            if c1.button("🟢 Easy"):
                word_obj["difficulty"] = "easy"

            if c2.button("🟡 Medium"):
                word_obj["difficulty"] = "medium"

            if c3.button("🔴 Hard"):
                word_obj["difficulty"] = "hard"

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
