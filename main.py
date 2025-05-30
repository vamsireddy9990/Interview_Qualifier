import streamlit as st
import PyPDF2
from anthropic import Client
import os
from dotenv import load_dotenv

# Page config
st.set_page_config(page_title="Sun Interview Qualifier", page_icon="☀️", layout="wide")

# Try loading from .env (for local)
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path)

# First try .env, then fallback to st.secrets
api_key = os.getenv("ANTHROPIC_API_KEY") or st.secrets.get("ANTHROPIC_API_KEY")

# Fail safely if key is missing
if not api_key:
    st.error("❌ Anthropic API key not found in .env or Streamlit secrets.")
    st.stop()

# Initialize client
client = Client(api_key=api_key)

# CSS
st.markdown("""
    <style>
    html, body, [class*="css"]  {
        font-family: 'Segoe UI', sans-serif;
        background-color: #f9f9f9;
        font-size: 22.4px !important;
    }
    .block-container {
        padding-top: 2rem;
    }
    .title-style {
        color: #EF476F;
        text-align: center;
        font-size: 3.92rem;
        font-weight: bold;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.82rem;
        color: #118AB2;
        margin-bottom: 1rem;
    }
    div.stButton > button {
        display: block;
        margin: 0 auto;
    }
    .results-table {
        margin: 0 auto;
        text-align: center;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("<div class='title-style'>☀️ Sun Interview Qualifier</div>", unsafe_allow_html=True)

# Input columns
col1, col2 = st.columns(2)
with col1:
    st.markdown("<div class='sub-header'>📄 Upload up to 10 Resume PDFs</div>", unsafe_allow_html=True)
    uploaded_files = st.file_uploader("Upload PDF resumes", type=["pdf"], accept_multiple_files=True)

with col2:
    st.markdown("<div class='sub-header'>📋 Enter Job Criteria</div>", unsafe_allow_html=True)
    criteria = st.text_area("Job Description or Selection Criteria", height=200)

# PDF text extractor
def extract_text_from_pdf(pdf_file):
    reader = PyPDF2.PdfReader(pdf_file)
    return "\n".join([p.extract_text() for p in reader.pages if p.extract_text()])

# Claude analysis
def analyze_resume(resume_text, criteria):
    prompt = f"""
Analyze if this resume matches the job criteria.

Resume:
{resume_text}

Job Criteria:
{criteria}

Reply with ONLY one of the following:
- "This resume qualifies for the next round of recruitment"
- "Does not qualify - missing experience in {criteria}"
"""
    response = client.messages.create(
        model="claude-3-opus-20240229",
        max_tokens=100,
        temperature=0,
        messages=[{"role": "user", "content": prompt}]
    )

    raw = response.content[0].text.strip()
    if "Does not qualify" in raw:
        return raw, False
    elif "qualifies for the next round" in raw:
        return raw, True
    else:
        return f"⚠️ Unexpected response: {raw}", False

# Button logic
if st.button("🚀 Analyze Resumes"):
    if not uploaded_files or not criteria:
        st.warning("Please upload resumes and provide job criteria.")
    elif len(uploaded_files) > 10:
        st.error("⚠️ Limit is 10 resumes at a time.")
    else:
        with st.spinner("Analyzing resumes... ⏳"):
            qualified_results = []
            unqualified_results = []

            for idx, pdf in enumerate(uploaded_files, 1):
                text = extract_text_from_pdf(pdf)
                analysis, qualifies = analyze_resume(text, criteria)

                result = {
                    "S.No": idx,
                    "Resume Name": pdf.name,
                    "Analysis": analysis,
                    "Rank": None if not qualifies else 0  # Temporary
                }

                if qualifies:
                    qualified_results.append(result)
                else:
                    result["Rank"] = "-"
                    unqualified_results.append(result)

            # Rank qualified
            qualified_results.sort(key=lambda x: x["Resume Name"])
            for i, r in enumerate(qualified_results, start=1):
                r["Rank"] = i

            # Combine
            results = qualified_results + unqualified_results

            # Show table
            st.markdown("<div class='results-table'>", unsafe_allow_html=True)
            st.markdown("### 📊 Results:")
            table_md = "| S.No | Resume Name | Analysis | Rank |\n|------|--------------|----------|------|\n"
            for r in results:
                table_md += f"| {r['S.No']} | {r['Resume Name']} | {r['Analysis']} | {r['Rank']} |\n"
            st.markdown(table_md)
            st.markdown("</div>", unsafe_allow_html=True)
