import streamlit as st
import PyPDF2
from anthropic import Client
import os
from dotenv import load_dotenv

# Set page configuration
st.set_page_config(
    page_title="Sun Interview Qualifier",
    page_icon="☀️",
    layout="wide"
)

# Load environment variables
load_dotenv()

# Initialize Anthropic client
client = Client(api_key=os.getenv('ANTHROPIC_API_KEY'))

# --- UI DESIGN ---
st.markdown("""
    <style>
    html, body, [class*="css"]  {
        font-family: 'Segoe UI', sans-serif;
        background-color: #f9f9f9;
    }
    .block-container {
        padding-top: 2rem;
    }
    .title-style {
        color: #EF476F;
        text-align: center;
        font-size: 2.8rem;
        font-weight: bold;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.3rem;
        color: #118AB2;
        margin-bottom: 1rem;
    }
    .result-box {
        background-color: #ffffff;
        padding: 1rem;
        margin-bottom: 1rem;
        border-left: 6px solid #06D6A0;
        border-radius: 5px;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("<div class='title-style'>☀️ Sun Interview Qualifier</div>", unsafe_allow_html=True)

# --- File upload and job criteria ---
col1, col2 = st.columns(2)

with col1:
    st.markdown("<div class='sub-header'>📄 Upload up to 10 Resume PDFs</div>", unsafe_allow_html=True)
    uploaded_files = st.file_uploader("Upload PDF resumes", type=["pdf"], accept_multiple_files=True)

with col2:
    st.markdown("<div class='sub-header'>📋 Enter Job Criteria</div>", unsafe_allow_html=True)
    criteria = st.text_area("Job Description or Selection Criteria", height=200)

# --- Resume Analyzer ---
def extract_text_from_pdf(pdf_file):
    reader = PyPDF2.PdfReader(pdf_file)
    return "\n".join([p.extract_text() for p in reader.pages if p.extract_text()])

def analyze_resume(resume_text, criteria):
    prompt = f"""Please analyze this resume against the given criteria and determine if the candidate qualifies.
The candidate must meet ALL criteria without exception - if even a single criterion is not met, the resume should be rejected.

Resume:
{resume_text}

Criteria:
{criteria}

First, list out each criterion and whether it was met (YES/NO).
Then, respond with ONLY ONE of these two exact phrases:
"This resume qualifies for the next round of recruitment" (ONLY if ALL criteria are met)
"This resume doesn't qualify the criteria given" (if ANY criterion is not met)
"""
    response = client.messages.create(
        model="claude-3-opus-20240229",
        max_tokens=100,
        temperature=0,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.content[0].text

# --- Action Button ---
if st.button("🚀 Analyze Resumes"):
    if not uploaded_files or not criteria:
        st.warning("Please upload at least one resume and provide the job criteria.")
    elif len(uploaded_files) > 10:
        st.error("⚠️ Limit is 10 resumes at a time.")
    else:
        with st.spinner("Analyzing resumes... Please wait ⏳"):
            for file in uploaded_files:
                try:
                    resume_text = extract_text_from_pdf(file)
                    result = analyze_resume(resume_text, criteria)
                    st.markdown(f"<div class='result-box'><strong>{file.name}</strong><br>{result}</div>", unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"Error analyzing {file.name}: {e}")
