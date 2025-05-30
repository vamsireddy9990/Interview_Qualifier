import streamlit as st
import PyPDF2
import pandas as pd
import re
from datetime import datetime

# --- SETUP ---
st.set_page_config(page_title="Sun Interview Qualifier", page_icon="☀️", layout="wide")

# --- CUSTOM CSS ---
st.markdown("""
<style>
    body, html {
        font-family: 'Segoe UI', sans-serif;
        background-color: #f9f9f9;
    }
    .title-style {
        color: #EF476F;
        text-align: center;
        font-size: 2.5rem;
        font-weight: bold;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #118AB2;
        margin-bottom: 0.5rem;
    }
    div.stButton > button {
        display: block;
        margin: 0 auto;
        padding: 8px 20px;
        font-size: 1rem;
    }
    div[data-testid="stDataFrameContainer"] {
        margin-left: auto !important;
        margin-right: auto !important;
        max-width: 900px;
    }
    table {
        margin-left: auto !important;
        margin-right: auto !important;
        border-collapse: collapse;
        width: 100%;
        max-width: 900px;
    }
    th, td {
        border: 1px solid #ddd !important;
        padding: 8px !important;
        text-align: center !important;
    }
    th {
        background-color: #f9f9f9 !important;
    }
</style>
""", unsafe_allow_html=True)

# --- HEADER ---
st.markdown("<div class='title-style'>☀️ Sun Interview Qualifier</div>", unsafe_allow_html=True)

# --- INPUTS ---
col1, col2 = st.columns(2)

with col1:
    st.markdown("<div class='sub-header'>📄 Upload up to 10 Resume PDFs</div>", unsafe_allow_html=True)
    uploaded_files = st.file_uploader("Upload PDF resumes", type=["pdf"], accept_multiple_files=True)

with col2:
    st.markdown("<div class='sub-header'>📋 Enter Job Criteria</div>", unsafe_allow_html=True)
    criteria = st.text_area("Job Description or Selection Criteria", height=200)

# --- FUNCTIONS ---
def extract_text_from_pdf(pdf_file):
    try:
        reader = PyPDF2.PdfReader(pdf_file)
        return "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
    except:
        return ""

def extract_dob_and_calculate_age(resume_text):
    dob_patterns = [
        r"(?:DOB|Date of Birth)[:\- ]*\s*(\d{2}[\/\-]\d{2}[\/\-]\d{4})",
        r"(?:DOB|Date of Birth)[:\- ]*\s*(\d{4}[\/\-]\d{2}[\/\-]\d{2})",
    ]
    for pattern in dob_patterns:
        match = re.search(pattern, resume_text, re.IGNORECASE)
        if match:
            dob_str = match.group(1)
            for fmt in ["%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d", "%Y-%m-%d"]:
                try:
                    dob = datetime.strptime(dob_str, fmt)
                    age = (datetime.today() - dob).days // 365
                    return age
                except:
                    continue
    return None

def analyze_resume(resume_text, criteria):
    if not resume_text:
        return "Could not extract text from resume", False

    c = criteria.lower().strip()
    
    # --- Age Criteria ---
    if "age" in c:
        age = extract_dob_and_calculate_age(resume_text)
        if age is None:
            return "Date of Birth not found", False
        try:
            expr = c.replace("age", str(age))
            if eval(expr):
                return "This resume qualifies for the next round of recruitment", True
            else:
                return f"This resume does not qualify: {criteria}", False
        except:
            return "Error evaluating age criteria", False

    # --- Experience Criteria ---
    if "experience" in c:
        matches = re.findall(r'(\d+)\+?\s*(?:years|yrs)', resume_text, re.IGNORECASE)
        exp_years = sum(int(m) for m in matches)
        try:
            expr = c.replace("experience", str(exp_years))
            if eval(expr):
                return "This resume qualifies for the next round of recruitment", True
            else:
                return f"This resume does not qualify: {criteria}", False
        except:
            return "Error evaluating experience criteria", False

    # --- Keyword Matching ---
    if criteria.lower() in resume_text.lower():
        return "This resume qualifies for the next round of recruitment", True
    else:
        return f"Does not qualify - missing in criteria: {criteria}", False

# --- ANALYZE ACTION ---
if st.button("🚀 Analyze Resumes"):
    if not uploaded_files or not criteria:
        st.warning("Please upload resumes and provide job criteria.")
    elif len(uploaded_files) > 10:
        st.error("⚠️ Limit is 10 resumes at a time.")
    else:
        with st.spinner("Analyzing resumes... ⏳"):
            results = []
            for idx, pdf_file in enumerate(uploaded_files, start=1):
                text = extract_text_from_pdf(pdf_file)
                analysis, qualifies = analyze_resume(text, criteria)
                rank = 0 if qualifies else "-"
                results.append({
                    "S.No": idx,
                    "Resume Name": pdf_file.name,
                    "Analysis": analysis,
                    "Rank": rank
                })

            qualified = [r for r in results if r["Rank"] == 0]
            qualified.sort(key=lambda x: x["Resume Name"])
            for i, r in enumerate(qualified, start=1):
                r["Rank"] = i

            unqualified = [r for r in results if r["Rank"] == "-"]
            final_results = qualified + unqualified
            for i, r in enumerate(final_results, start=1):
                r["S.No"] = i

            df_results = pd.DataFrame(final_results)
            st.markdown("<h3 style='text-align: center; color: #118AB2;'>📊 Analysis Results</h3>", unsafe_allow_html=True)
            st.dataframe(df_results.style.set_properties(**{'text-align': 'center'}))