import streamlit as st
import PyPDF2
import pandas as pd
import re
from datetime import datetime
from dateutil import parser as date_parser
from sentence_transformers import SentenceTransformer, util

# --- SETUP ---
st.set_page_config(page_title="Sun Interview Qualifier", page_icon="☀️", layout="wide")

# --- CUSTOM CSS ---
st.markdown("""
<style>
.title-style { text-align:center; font-size:2.5rem; color:#EF476F; font-weight:bold; margin-bottom:1rem; }
.sub-header { font-size:1.2rem; color:#118AB2; margin-bottom:0.5rem; }
div.stButton > button { display:block; margin:0 auto; padding:8px 20px; font-size:1rem; }
div[data-testid="stDataFrameContainer"] { margin-left:auto; margin-right:auto; max-width:900px; }
</style>
""", unsafe_allow_html=True)

# --- HEADER ---
st.markdown("<div class='title-style'>☀️ Sun Interview Qualifier</div>", unsafe_allow_html=True)

# --- INPUT ---
col1, col2 = st.columns(2)
with col1:
    st.markdown("<div class='sub-header'>📄 Upload up to 10 Resume PDFs</div>", unsafe_allow_html=True)
    uploaded_files = st.file_uploader("Upload PDF resumes", type=["pdf"], accept_multiple_files=True)
with col2:
    st.markdown("<div class='sub-header'>📋 Enter Job Criteria</div>", unsafe_allow_html=True)
    criteria = st.text_area("Job Description or Selection Criteria", height=200)

# --- HELPER: Extract text ---
def extract_text_from_pdf(pdf_file):
    try:
        reader = PyPDF2.PdfReader(pdf_file)
        text = "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
        return text
    except:
        return ""

# --- HELPER: Calculate Age ---
def extract_age(text):
    dob_matches = re.findall(r'(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})', text)
    for dob in dob_matches:
        try:
            birth_date = date_parser.parse(dob, dayfirst=True)
            age = (datetime.today() - birth_date).days // 365
            return age
        except:
            continue
    return None

# --- HELPER: Calculate Experience in Years ---
def extract_experience_years(text):
    # Patterns like Jan 2018 - Mar 2020 or 2019 to 2023
    ranges = re.findall(r'(?P<start>\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)?\.?\s?\d{4})\s?(?:to|[-–])\s?(?P<end>\b(?:Present|\d{4}))', text, flags=re.IGNORECASE)
    total_months = 0
    for start, end in ranges:
        try:
            start_date = date_parser.parse(start)
            end_date = datetime.today() if 'present' in end.lower() else date_parser.parse(end)
            total_months += max(0, (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month))
        except:
            continue
    return round(total_months / 12, 2)

# --- HELPER: Check criteria ---
def check_criteria(text, criteria):
    analysis_notes = []
    qualifies = True

    age = extract_age(text)
    experience = extract_experience_years(text)

    for line in criteria.split("\n"):
        line = line.strip().lower()
        if not line:
            continue
        if "age" in line:
            try:
                if "<" in line:
                    threshold = int(re.findall(r'\d+', line)[0])
                    if age is None or age >= threshold:
                        qualifies = False
                        analysis_notes.append(f"Does not qualify: Age is {age} (Expected < {threshold})")
                elif ">" in line:
                    threshold = int(re.findall(r'\d+', line)[0])
                    if age is None or age <= threshold:
                        qualifies = False
                        analysis_notes.append(f"Does not qualify: Age is {age} (Expected > {threshold})")
            except:
                analysis_notes.append("Unable to parse age requirement.")
        elif "experience" in line:
            try:
                if "<" in line:
                    threshold = float(re.findall(r'\d+(?:\.\d+)?', line)[0])
                    if experience is None or experience >= threshold:
                        qualifies = False
                        analysis_notes.append(f"Does not qualify: Experience is {experience} years (Expected < {threshold})")
                elif ">" in line:
                    threshold = float(re.findall(r'\d+(?:\.\d+)?', line)[0])
                    if experience is None or experience <= threshold:
                        qualifies = False
                        analysis_notes.append(f"Does not qualify: Experience is {experience} years (Expected > {threshold})")
            except:
                analysis_notes.append("Unable to parse experience requirement.")
        else:
            # Use semantic match for skills/qualifications
            model = SentenceTransformer('all-MiniLM-L6-v2')
            emb_criteria = model.encode(line, convert_to_tensor=True)
            emb_text = model.encode(text, convert_to_tensor=True)
            score = util.cos_sim(emb_criteria, emb_text).item()
            if score < 0.4:
                qualifies = False
                analysis_notes.append(f"Does not match semantic criteria: '{line}'")

    if qualifies:
        return "✅ This resume qualifies for the next round of recruitment", True
    else:
        return "❌ " + " | ".join(analysis_notes), False

# --- MAIN ACTION ---
if st.button("🚀 Analyze Resumes"):
    if not uploaded_files or not criteria:
        st.warning("Please upload resumes and enter selection criteria.")
    elif len(uploaded_files) > 10:
        st.error("⚠️ Limit is 10 resumes.")
    else:
        with st.spinner("Analyzing resumes... ⏳"):
            results = []
            for idx, pdf in enumerate(uploaded_files, 1):
                text = extract_text_from_pdf(pdf)
                analysis, qualifies = check_criteria(text, criteria)
                rank = 0 if qualifies else "-"
                results.append({
                    "S.No": idx,
                    "Resume Name": pdf.name,
                    "Analysis": analysis,
                    "Rank": rank
                })

            # Ranking and formatting
            qualified = [r for r in results if r["Rank"] == 0]
            qualified.sort(key=lambda x: x["Resume Name"])
            for i, r in enumerate(qualified, 1):
                r["Rank"] = i
            final_results = qualified + [r for r in results if r["Rank"] == "-"]
            for i, r in enumerate(final_results, 1):
                r["S.No"] = i

            df_results = pd.DataFrame(final_results)

            st.markdown("<h3 style='text-align: center; color: #118AB2;'>📊 Analysis Results</h3>", unsafe_allow_html=True)
            st.dataframe(df_results.style.set_properties(**{'text-align': 'center'}))
