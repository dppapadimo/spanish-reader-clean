# ----------------------------------------
# Spanish Vocabulary Reader
# Version: 4.8
# Features:
# - Highlight words
# - Manual input (stable)
# - Auto translate
# - Auto save to Excel
# Date: 2026-04-13
# ----------------------------------------

import streamlit as st
import pandas as pd
from deep_translator import GoogleTranslator
import PyPDF2
from datetime import datetime
from io import BytesIO
import re

st.set_page_config(page_title="Spanish Reader", layout="wide")

st.title("📖 Spanish Vocabulary Reader")
st.caption("Version 4.8")

# -----------------------
# Session
# -----------------------
if "words_data" not in st.session_state:
    st.session_state.words_data = []

if "selected_words" not in st.session_state:
    st.session_state.selected_words = set()

if "last_word" not in st.session_state:
    st.session_state.last_word = ""

# -----------------------
# Highlight text
# -----------------------
def highlight_text(text, words):
    def replace(match):
        word = match.group(0)
        clean = word.lower()
        if clean in words:
            return f"<span style='background-color: yellow'>{word}</span>"
        return word

    return re.sub(r'\b\w+\b', replace, text)

# -----------------------
# Input επιλογή
# -----------------------
option = st.radio("Διάλεξε τρόπο εισαγωγής:", ["Paste Text", "Upload File"])

text = ""
source_name = "pasted_text"

if option == "Paste Text":
    text = st.text_area("Επικόλλησε ισπανικό κείμενο εδώ:")
    source_name = "pasted_text"

elif option == "Upload File":
    uploaded_file = st.file_uploader("Ανέβασε αρχείο (.txt ή .pdf)", type=["txt", "pdf"])

    if uploaded_file:
        source_name = uploaded_file.name

        if uploaded_file.type == "text/plain":
            text = uploaded_file.read().decode("utf-8")

        elif uploaded_file.type == "application/pdf":
            reader = PyPDF2.PdfReader(uploaded_file)
            pages = []
            for page in reader.pages:
                content = page.extract_text()
                if content:
                    pages.append(content)
            text = "\n".join(pages)

# -----------------------
# Μετάφραση
# -----------------------
lang = st.selectbox("Μετάφραση σε:", ["Greek", "English"])
target_lang = "el" if lang == "Greek" else "en"

# -----------------------
# Βρες πρόταση
# -----------------------
def find_sentence(word, text):
    sentences = re.split(r'[.!?]', text)
    for s in sentences:
        if word.lower() in s.lower():
            return s.strip()
    return ""

# -----------------------
# Εμφάνιση κειμένου
# -----------------------
if text:
    st.subheader("📖 Κείμενο")

    highlighted = highlight_text(text, st.session_state.selected_words)
    st.markdown(highlighted, unsafe_allow_html=True)

    # -----------------------
    # INPUT
    # -----------------------
    st.subheader("✏️ Input unknown word + enter+ translation-highlight-save")

    user_word = st.text_input("")

    # -----------------------
    # AUTO PROCESS
    # -----------------------
    if user_word and user_word != st.session_state.last_word:

        st.session_state.last_word = user_word
        clean_word = user_word.lower().strip()

        try:
            translation = GoogleTranslator(source='auto', target=target_lang).translate(clean_word)
        except:
            translation = "Error"

        sentence = find_sentence(clean_word, text)

        st.success(f"{clean_word} → {translation}")

        # highlight
        st.session_state.selected_words.add(clean_word)

        # avoid duplicates
        exists = any(w["word"] == clean_word for w in st.session_state.words_data)

        if not exists:
            st.session_state.words_data.append({
                "word": clean_word,
                "translation": translation,
                "sentence": sentence,
                "source": source_name,
                "date": datetime.now().strftime("%Y-%m-%d %H:%M")
            })

# -----------------------
# Excel export
# -----------------------
if st.session_state.words_data:
    df = pd.DataFrame(st.session_state.words_data)

    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)

    st.download_button(
        "💾 Κατέβασε Excel",
        data=output.getvalue(),
        file_name="words.xlsx"
    )

# -----------------------
# Clear
# -----------------------
if st.button("❌ Καθαρισμός"):
    st.session_state.words_data = []
    st.session_state.selected_words = set()
