# ----------------------------------------
# Spanish Vocabulary Reader
# Version: 4.7
# Features:
# - Tap word
# - Auto translate
# - Highlight words
# - Auto save to Excel
# Date: 2026-04-13
# ----------------------------------------
# st.caption("Version 4.7")
# ---------------------------------------
import streamlit as st
import pandas as pd
from deep_translator import GoogleTranslator
import PyPDF2
from datetime import datetime
from io import BytesIO
import re
# --------------------------------------
st.caption("Version 4.7")
# ---------------------------------------

st.set_page_config(page_title="Spanish Reader", layout="wide")

st.title("📖 Spanish Vocabulary Reader")

# -----------------------
# Session
# -----------------------
if "words_data" not in st.session_state:
    st.session_state.words_data = []

if "selected_words" not in st.session_state:
    st.session_state.selected_words = set()

if "current_word" not in st.session_state:
    st.session_state.current_word = ""

# -----------------------
# Highlight clickable text
# -----------------------
def render_text(text, selected_words):
    html = ""
    for w in text.split():
        clean = w.strip(".,;:!?¡¿()\"'").lower()

        style = ""
        if clean in selected_words:
            style = "background-color: yellow;"

        html += f"""
        <span 
            style="cursor:pointer; {style}" 
            onclick="window.parent.postMessage('{clean}', '*')">
            {w}
        </span> 
        """
    return html

# -----------------------
# Input
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
# Translation
# -----------------------
lang = st.selectbox("Μετάφραση σε:", ["Greek", "English"])
target_lang = "el" if lang == "Greek" else "en"

# -----------------------
# Sentence
# -----------------------
def find_sentence(word, text):
    sentences = re.split(r'[.!?]', text)
    for s in sentences:
        if word in s:
            return s.strip()
    return ""

# -----------------------
# CLICK HANDLER
# -----------------------
clicked = st.text_input("hidden", key="hidden_input", label_visibility="collapsed")

# -----------------------
# PROCESS CLICK
# -----------------------
if clicked and clicked != st.session_state.current_word:
    st.session_state.current_word = clicked

    try:
        translation = GoogleTranslator(source='auto', target=target_lang).translate(clicked)
    except:
        translation = "Error"

    sentence = find_sentence(clicked, text)

    st.success(f"{clicked} → {translation}")

    # highlight
    st.session_state.selected_words.add(clicked)

    # avoid duplicates
    exists = any(w["word"] == clicked for w in st.session_state.words_data)

    if not exists:
        st.session_state.words_data.append({
            "word": clicked,
            "translation": translation,
            "sentence": sentence,
            "source": source_name,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M")
        })

# -----------------------
# DISPLAY TEXT
# -----------------------
if text:
    st.subheader("📖 Κείμενο (tap λέξη)")

    html = render_text(text, st.session_state.selected_words)

    st.components.v1.html(f"""
    <div>{html}</div>

    <script>
    window.addEventListener("message", function(event) {{
        const word = event.data;
        const input = window.parent.document.querySelector('input[data-testid="stTextInput"]');
        if (input) {{
            input.value = word;
            input.dispatchEvent(new Event('input', {{ bubbles: true }}));
        }}
    }});
    </script>
    """, height=300, scrolling=True)

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
