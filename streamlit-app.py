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

if "last_word" not in st.session_state:
    st.session_state.last_word = ""

# -----------------------
# Clickable text
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
        <span 
            style="cursor:pointer; {style}" 
            onclick="window.parent.postMessage({{word: '{clean}'}}, '*')">
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
# Display
# -----------------------
if text:
    st.subheader("📖 Κείμενο (tap λέξη)")

    clickable_html = make_clickable(text, st.session_state.selected_words)

    st.components.v1.html(f"""
    <div id="text-area">{clickable_html}</div>

    <script>
    window.addEventListener("message", (event) => {{
        const word = event.data.word;
        const streamlitDoc = window.parent.document;

        let input = streamlitDoc.querySelector('input[data-testid="stTextInput"]');

        if(input){{
            input.value = word;
            input.dispatchEvent(new Event('input', {{ bubbles: true }}));
        }}
    }});
    </script>
    """, height=300, scrolling=True)

    # hidden input
    selected_word = st.text_input("hidden", label_visibility="collapsed")

    # -----------------------
    # AUTO TRANSLATE
    # -----------------------
    if selected_word and selected_word != st.session_state.last_word:

        st.session_state.last_word = selected_word

        try:
            translation = GoogleTranslator(source='auto', target=target_lang).translate(selected_word)
        except:
            translation = "Error"

        sentence = find_sentence(selected_word, text)

        st.success(f"{selected_word} → {translation}")

        # highlight
        st.session_state.selected_words.add(selected_word)

        # avoid duplicates
        exists = any(w["word"] == selected_word for w in st.session_state.words_data)

        if not exists:
            st.session_state.words_data.append({
                "word": selected_word,
                "translation": translation,
                "sentence": sentence,
                "source": source_name,
                "date": datetime.now().strftime("%Y-%m-%d %H:%M")
            })

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
