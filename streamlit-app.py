import streamlit as st
import pandas as pd
from deep_translator import GoogleTranslator
import PyPDF2
from datetime import datetime
from io import BytesIO
import re

st.set_page_config(page_title="Spanish Reader", layout="wide")

st.title("📖 Spanish Vocabulary Reader")

# -----------------------
# Session
# -----------------------
if "words_data" not in st.session_state:
    st.session_state.words_data = []

if "selected_words" not in st.session_state:
    st.session_state.selected_words = set()

# -----------------------
# Clickable + highlight
# -----------------------
def make_clickable(text, selected_words):
    words = text.split()
    html = ""

    for w in words:
        clean = w.strip(".,;:!?¡¿()\"'").lower()

        style = ""
        if clean in selected_words:
            style = "background-color: yellow;"

        html += f"""
        <a href="?word={clean}" style="text-decoration:none; color:black; {style}">
            {w}
        </a> 
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
# Detect clicked word
# -----------------------
query_params = st.query_params
clicked_word = query_params.get("word")

# -----------------------
# AUTO PROCESS
# -----------------------
if clicked_word and text:

    if clicked_word not in st.session_state.selected_words:

        try:
            translation = GoogleTranslator(source='auto', target=target_lang).translate(clicked_word)
        except:
            translation = "Error"

        sentence = find_sentence(clicked_word, text)

        st.session_state.selected_words.add(clicked_word)

        st.session_state.words_data.append({
            "word": clicked_word,
            "translation": translation,
            "sentence": sentence,
            "source": source_name,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M")
        })

        st.success(f"{clicked_word} → {translation}")

# -----------------------
# Display text
# -----------------------
if text:
    st.subheader("📖 Κείμενο (tap λέξη)")

    html = make_clickable(text, st.session_state.selected_words)
    st.markdown(html, unsafe_allow_html=True)

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
