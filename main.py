import streamlit as st
import PyPDF2
from anthropic import Client
import os
from dotenv import load_dotenv

# Configure Streamlit page FIRST
st.set_page_config(
    page_title="Sun Interview Qualifier",
    page_icon="☀️",
    layout="wide"
)

# Load environment variables
load_dotenv()

# DEBUG: Check if API key is loaded properly
st.write("API key loaded:", os.getenv("ANTHROPIC_API_KEY"))

# Custom CSS for colorful styling
st.markdown("""
    <style>
    .main {
        background: linear-gradient(135deg, #ff6b6b, #4ecdc4);
        padding: 20px;
        border-radius: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# Title with custom styling
st.markdown("<h1 style='text-align: center; color: #ff6b6b;'>✨ Sun Interview Qualifier ✨</h1>", unsafe_allow_html=True)

# Initialize Anthropic client
client = Client(api_key=os.getenv('ANTHROPIC_API_KEY'))

def extract_text_from_pdf(pdf_file):
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    text = ""
    for page in pdf_reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text
    return text

def analyze_resume(resume_text, criteria):
    prompt = f"""Please analyze this resume against the given criteria and determine if the candidate qualifies. 

Resume:
{resume_text}

Criteria:
{criteria}

Respond with ONLY ONE of these two exact phrases:
"This resume qualifies for the next round of recruitment"
"This resume doesn't qualify the criteria given"
"""
    response = client.messages.create(
        model="claude-3-opus-20240229",
        max_tokens=100,
        temperature=0,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    return response.content[0].text

# File uploader with custom styling
st.markdown("<h3 style='color: #4ecdc4;'>📄 Upload Resumes</h3>", unsafe_allow_html=True)
uploaded_files = st.file_uploader("Upload Resumes (PDF)", 
    type=['pdf'],
    accept_multiple_files=True,
    help="Please upload up to 10 PDF files")

# Job criteria input
st.markdown("<h3 style='color: #ff6b6b;'>📋 Job Criteria</h3>", unsafe_allow_html=True)
criteria = st.text_area("Enter Job Criteria", height=200, help="Enter the job requirements and qualifications")

# Submit button
if st.button("Analyze Resumes", type="primary", help="Click to analyze all resumes"):
    if uploaded_files and criteria:
        if len(uploaded_files) > 10:
            st.warning("⚠️ Please upload a maximum of 10 resumes.", icon="⚡")
        else:
            try:
                with st.spinner('🔄 Analyzing resumes...'):
                    st.markdown("<h3 style='color: #4ecdc4;'>🎯 Analysis Results:</h3>", unsafe_allow_html=True)
                    for i, file in enumerate(uploaded_files):
                        resume_text = extract_text_from_pdf(file)
                        result = analyze_resume(resume_text, criteria)
                        st.markdown(f"**{file.name}**: {result}")
            except Exception as e:
                st.error(f"❌ An error occurred: {e}")
