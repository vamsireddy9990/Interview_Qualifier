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
    criteria_input = st.text_area("Job Description or Selection Criteria (e.g. 'MBA', 'experience < 3', 'age < 26')", height=200)

# --- UTILITY FUNCTIONS ---
def extract_text_from_pdf(pdf_file):
    try:
        reader = PyPDF2.PdfReader(pdf_file)
        text = "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
        return text
    except:
        return ""

def calculate_experience(text):
    # Extract years like '2018 - 2022', 'Jan 2020 to Dec 2023'
    date_patterns = re.findall(r'(\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)?\s?\d{4})\s?(?:-|to)\s?(\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)?\s?\d{4}|Present)', text, flags=re.IGNORECASE)
    total_months = 0
    for start, end in date_patterns:
        try:
            start_date = datetime.strptime(start.strip(), "%b %Y") if len(start.strip().split()) == 2 else datetime.strptime(start.strip(), "%Y")
            end_date = datetime.today() if "present" in end.lower() else (datetime.strptime(end.strip(), "%b %Y") if len(end.strip().split()) == 2 else datetime.strptime(end.strip(), "%Y"))
            total_months += (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month)
        except:
            continue
    return round(total_months / 12, 1)

def extract_age(text):
    dob_patterns = re.findall(r'(\d{2}[/-]\d{2}[/-]\d{4}|\d{4}-\d{2}-\d{2})', text)
    for dob in dob_patterns:
        try:
            dob_clean = dob.replace('/', '-').replace("\\", "-")
            dob_date = datetime.strptime(dob_clean, "%d-%m-%Y") if '-' in dob_clean else datetime.strptime(dob_clean, "%Y-%m-%d")
            age = (datetime.today() - dob_date).days // 365
            return age
        except:
            continue
    return None

def analyze_resume(text, criteria):
    if not text:
        return "Could not extract text from resume", False

    experience = calculate_experience(text)
    age = extract_age(text)

    lines = [c.strip() for c in criteria.splitlines() if c.strip()]
    for line in lines:
        if "experience" in line.lower():
            try:
                years = float(re.findall(r"\d+", line)[0])
                if ">" in line and not (experience > years):
                    return f"Does not qualify - experience is {experience} years, required > {years}", False
                elif "<" in line and not (experience < years):
                    return f"Does not qualify - experience is {experience} years, required < {years}", False
            except:
                continue
        elif "age" in line.lower():
            try:
                limit = int(re.findall(r"\d+", line)[0])
                if age is None:
                    return f"Could not determine age", False
                if ">" in line and not (age > limit):
                    return f"Does not qualify - age is {age}, required > {limit}", False
                elif "<" in line and not (age < limit):
                    return f"Does not qualify - age is {age}, required < {limit}", False
            except:
                continue
        else:
            if line.lower() not in text.lower():
                return f"Does not qualify - missing keyword: {line}", False

    return "This resume qualifies for the next round of recruitment", True

# --- ANALYZE ACTION ---
if st.button("🚀 Analyze Resumes"):
    if not uploaded_files or not criteria_input:
        st.warning("Please upload resumes and provide job criteria.")
    elif len(uploaded_files) > 10:
        st.error("⚠️ Limit is 10 resumes at a time.")
    else:
        with st.spinner("Analyzing resumes... ⌛"):
            results = []
            for idx, file in enumerate(uploaded_files, start=1):
                text = extract_text_from_pdf(file)
                analysis, qualifies = analyze_resume(text, criteria_input)
                rank = 0 if qualifies else "-"
                results.append({
                    "S.No": idx,
                    "Resume Name": file.name,
                    "Analysis": analysis,
                    "Rank": rank
                })

            qualified = [r for r in results if r["Rank"] == 0]
            qualified.sort(key=lambda x: x["Resume Name"])
            for i, r in enumerate(qualified, start=1):
                r["Rank"] = i

            unqualified = [r for r in results if r["Rank"] == "-"]
            final = qualified + unqualified

            for i, r in enumerate(final, start=1):
                r["S.No"] = i

            df_results = pd.DataFrame(final)

            st.markdown("<h3 style='text-align: center; color: #118AB2;'>📊 Analysis Results</h3>", unsafe_allow_html=True)
            st.dataframe(df_results.style.set_properties(**{'text-align': 'center'}))
