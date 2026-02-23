import streamlit as st
from langdetect import detect
from deep_translator import GoogleTranslator
from textblob import TextBlob
import PyPDF2
from docx import Document
from fpdf import FPDF
import io

# Setup Page Configuration
st.set_page_config(
    page_title="Text Analytics & Translation",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Fetch Supported Languages
@st.cache_data
def get_supported_languages():
    return GoogleTranslator().get_supported_languages(as_dict=True)

languages = get_supported_languages()
language_names = list(languages.keys())
language_names.sort()

# Sidebar
st.sidebar.title("Configuration")
st.sidebar.markdown("Select target language for translation.")

# Display language names capitalized for better UI, but keep internal mapping
display_languages = [lang.title() for lang in language_names]
default_index = display_languages.index("English") if "English" in display_languages else 0
selected_display_lang = st.sidebar.selectbox("Target Language", display_languages, index=default_index)

target_lang_name = selected_display_lang.lower()
target_lang_code = languages[target_lang_name]

st.sidebar.markdown("---")

st.title("🌍 Text Analytics & Translation")
st.markdown("Perform language detection, translation, sentiment analysis, and document processing.")

# Create Tabs
tab1, tab2 = st.tabs(["📝 Text Input", "📄 Document Upload"])

# --- TAB 1: Text Input ---
with tab1:
    st.header("Text Analysis & Translation")
    
    input_text = st.text_area("Enter your text here:", height=200, placeholder="Type or paste text...")
    
    if st.button("Process Text", type="primary"):
        if not input_text.strip():
            st.warning("Please enter some text to process.")
        else:
            with st.spinner("Processing..."):
                try:
                    # 1. Language Detection
                    detected_lang_code = detect(input_text)
                    
                    # 2. Translation
                    translated_text = GoogleTranslator(source='auto', target=target_lang_code).translate(input_text)
                    
                    # 3. Sentiment Analysis
                    blob = TextBlob(input_text)
                    polarity = blob.sentiment.polarity
                    if polarity > 0:
                        sentiment = "Positive 😊"
                    elif polarity < 0:
                        sentiment = "Negative 😔"
                    else:
                        sentiment = "Neutral 😐"
                    
                    # 4. Analytics
                    word_count = len(input_text.split())
                    char_count = len(input_text)
                    
                    # Display Results
                    st.divider()
                    st.subheader("Results")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.info(f"**Detected Language:** {detected_lang_code.upper()}")
                    with col2:
                        st.success(f"**Target Language:** {target_lang_name.title()}")
                        
                    st.text_area("Translated Text", translated_text, height=150)
                    
                    st.markdown("### Analytics")
                    col1, col2, col3, col4 = st.columns(4)
                    col1.metric("Word Count", word_count)
                    col2.metric("Character Count", char_count)
                    col3.metric("Sentiment Polarity", f"{polarity:.2f}")
                    col4.metric("Sentiment", sentiment)
                    
                    # Audio/Voice feature from original request mention: 
                    # Streamlit doesn't natively record voice easily without extra components but we can mention it or assume text was typed via system dictation.
                    # We will focus on the text analytics.
                    
                except Exception as e:
                    st.error(f"An error occurred during processing: {e}")

# --- Helper Functions for Document Extraction ---
def extract_text_from_txt(file):
    return file.getvalue().decode("utf-8")

def extract_text_from_pdf(file):
    reader = PyPDF2.PdfReader(file)
    text = ""
    for page in reader.pages:
        extracted = page.extract_text()
        if extracted:
            text += extracted + "\n"
    return text

def extract_text_from_docx(file):
    doc = Document(file)
    text = "\n".join([para.text for para in doc.paragraphs])
    return text

def create_pdf(text):
    # Use fpdf to generate a pdf. fpdf natively handles basic latin well. 
    # For complex unicode it might need a Unicode font.
    # Using a simple fallback for this implementation.
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    # Add text with multi_cell to handle wrapping, encode/decode to avoid character errors with default font
    # Note: fpdf2 supports unicode better natively if we install a ttf font, but we'll use a safe encoding technique.
    safe_text = text.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 10, txt=safe_text)
    
    # fpdf2's output() returns a bytearray by default, 
    # but Streamlit's download_button expects either str, bytes, or an IO object.
    return bytes(pdf.output())

# --- TAB 2: Document Upload ---
with tab2:
    st.header("Document Translation")
    st.markdown("Upload a Document (`.txt`, `.pdf`, `.docx`) to extract text and translate it.")
    
    uploaded_file = st.file_uploader("Choose a file", type=['txt', 'pdf', 'docx'])
    
    if uploaded_file is not None:
        file_details = {"FileName": uploaded_file.name, "FileType": uploaded_file.type, "FileSize": uploaded_file.size}
        st.write(file_details)
        
        extracted_text = ""
        try:
            if uploaded_file.name.endswith('.txt'):
                extracted_text = extract_text_from_txt(uploaded_file)
            elif uploaded_file.name.endswith('.pdf'):
                extracted_text = extract_text_from_pdf(uploaded_file)
            elif uploaded_file.name.endswith('.docx'):
                extracted_text = extract_text_from_docx(uploaded_file)
            
            with st.expander("Show Extracted Text"):
                st.text_area("Extracted Source Text", extracted_text, height=200, disabled=True)
                
            if st.button("Translate Document", type="primary"):
                if not extracted_text.strip():
                    st.warning("Could not extract text from document.")
                else:
                    with st.spinner(f"Translating to {target_lang_name.title()}..."):
                        try:
                            # Handling large texts: deep_translator max is 5000 chars. 
                            # We might need to chunk it.
                            max_chars = 4900
                            chunks = [extracted_text[i:i+max_chars] for i in range(0, len(extracted_text), max_chars)]
                            translated_chunks = []
                            
                            for chunk in chunks:
                                translated_chunk = GoogleTranslator(source='auto', target=target_lang_code).translate(chunk)
                                translated_chunks.append(translated_chunk)
                                
                            full_translation = "\n".join(translated_chunks)
                            
                            st.success("Translation Complete!")
                            st.text_area("Translated Document Text", full_translation, height=300)
                            
                            st.divider()
                            st.subheader("Download Options")
                            
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                # TXT Download
                                st.download_button(
                                    label="Download as TXT",
                                    data=full_translation,
                                    file_name=f"translated_{uploaded_file.name}.txt",
                                    mime="text/plain"
                                )
                                
                            with col2:
                                # PDF Download
                                try:
                                    pdf_data = create_pdf(full_translation)
                                    st.download_button(
                                        label="Download as PDF",
                                        data=pdf_data,
                                        file_name=f"translated_{uploaded_file.name}.pdf",
                                        mime="application/pdf"
                                    )
                                except Exception as e:
                                    st.error(f"Error generating PDF: {e}")
                                    st.info("Translation contains unsupported characters for the default PDF generator. Please use TXT download.")
                                
                        except Exception as e:
                            st.error(f"Translation failed: {e}")
                            
        except Exception as e:
            st.error(f"Failed to read file: {e}")
