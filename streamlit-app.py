# ----------------------------------------
# Spanish Vocabulary Reader
# Version: 5.1
# Features:
# - Tap word → auto fill input
# - Text area reading (scrollable)
# - Auto translate (Enter)
# - Highlight words
# - Vertical translations list
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
st.caption("Version 5.1")

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
# Highlight HTML
# -----------------------
def highlight_html(text, words):
    def replace(match):
        word = match.group(0)
        if word.lower() in words:
            return f"<span style='background-color: yellow'>{word}</span>"
        return word
    return re.sub(r'\b\w+\b', replace, text)

# -----------------------
# Clickable text
# -----------------------
def clickable_text(text, words):
    html = ""
    for w in text.split():
        clean = w.strip(".,;:!?¡¿()\"'").lower()

        style = ""
        if clean in words:
            style = "background-color: yellow;"

        html += f"""
        <span style="cursor:pointer; {style}"
        onclick="window.parent.postMessage('{clean}', '*')">
        {w}
        </span> 
        """
    return html

# -----------------------
# Input επιλογή
# -----------------------
option = st.radio("Διάλεξε τρόπο εισαγωγής:", ["Paste Text", "Upload File"])

text = ""
source_name = "pasted_text"

if option == "Paste Text":
    text = st.text_area("Επικόλλησε ισπανικό κείμενο εδώ:", height=150)
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
# DISPLAY
# -----------------------
if text:
    st.subheader("👆 Tap λέξη")

    html = clickable_text(text, st.session_state.selected_words)

    st.components.v1.html(f"""
    <div style="line-height:1.6">{html}</div>

    <script>
    window.addEventListener("message", function(event) {{
        const word = event.data;
        const input = window.parent.document.querySelector('input[data-testid="stTextInput"]');
        if(input){{
            input.value = word;
            input.dispatchEvent(new Event('input', {{ bubbles: true }}));
        }}
    }});
    </script>
    """, height=150, scrolling=True)

    # -----------------------
    # TEXT AREA (READING)
    # -----------------------
    st.subheader("📖 Reading area")

    clean_text = re.sub('<.*?>', '', text)

    st.text_area("", clean_text, height=300)

    # -----------------------
    # INPUT
    # -----------------------
    st.subheader("✏️ Input unknown word + Enter → Translation + Save")

    user_word = st.text_input("")

    # -----------------------
    # PROCESS
    # -----------------------
    if user_word and user_word != st.session_state.last_word:

        st.session_state.last_word = user_word
        clean_word = user_word.lower().strip()

        try:
            translation = GoogleTranslator(source='auto', target=target_lang).translate(clean_word)
        except:
            translation = "Error"

        st.success(f"{clean_word} → {translation}")

        st.session_state.selected_words.add(clean_word)

        exists = any(w["word"] == clean_word for w in st.session_state.words_data)

        if not exists:
            st.session_state.words_data.append({
                "word": clean_word,
                "translation": translation,
                "source": source_name,
                "date": datetime.now().strftime("%Y-%m-%d %H:%M")
            })

    # -----------------------
    # TRANSLATIONS
    # -----------------------
    if st.session_state.words_data:
        st.subheader("📚 Translations")

        translation_text = "\n".join([
            f"{w['word']} → {w['translation']}"
            for w in st.session_state.words_data
        ])

        st.text_area("", translation_text, height=200)

# -----------------------
# Excel
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
