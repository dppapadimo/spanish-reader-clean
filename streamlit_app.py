import streamlit as st
import pandas as pd
from deep_translator import GoogleTranslator
import PyPDF2
from datetime import datetime
from io import BytesIO

st.set_page_config(page_title="Spanish Reader", layout="wide")

st.title("📖 Spanish Vocabulary Reader")

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

lang = st.selectbox("Μετάφραση σε:", ["Greek", "English"])
target_lang = "el" if lang == "Greek" else "en"

if "words_data" not in st.session_state:
    st.session_state.words_data = []

def find_sentence(word, text):
    sentences = text.split(".")
    for s in sentences:
        if word in s:
            return s.strip()
    return ""

if text:
    st.subheader("📖 Κείμενο")
    st.text_area("Το κείμενό σου:", text, height=300)

    st.subheader("📌 Διάλεξε λέξη")

    words = sorted(list(set([
        w.strip(".,;:!?¡¿()\"'").lower()
        for w in text.split()
        if w.strip() != ""
    ])))

    selected_word = st.selectbox("Λέξη:", words)

    if st.button("🔍 Μετάφραση"):
        try:
            translation = GoogleTranslator(source='auto', target=target_lang).translate(selected_word)
        except:
            translation = "Error"

        sentence = find_sentence(selected_word, text)

        st.success(f"{selected_word} → {translation}")

        st.session_state.words_data.append({
            "word": selected_word,
            "translation": translation,
            "sentence": sentence,
            "source": source_name,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M")
        })

if st.session_state.words_data:
    df = pd.DataFrame(st.session_state.words_data)

    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Words')

    excel_data = output.getvalue()

    st.download_button(
        label="💾 Κατέβασε τις λέξεις (Excel)",
        data=excel_data,
        file_name="unknown_words.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

if st.button("❌ Καθαρισμός λέξεων"):
    st.session_state.words_data = []
