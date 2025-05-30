import streamlit as st
import PyPDF2
import pandas as pd
import re
from datetime import datetime

# --- SETUP ---
st.set_page_config(page_title="Sun Interview Qualifier", page_icon="☀️", layout="wide")

# --- CUSTOM CSS for centering ---
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
        text = "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
        return text
    except Exception:
        return ""

def extract_dob(text):
    # Regex to capture common date formats - extend as needed
    date_patterns = [
        r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',      # e.g. 12/05/1996 or 12-05-1996
        r'(\d{4}[/-]\d{1,2}[/-]\d{1,2})',        # e.g. 1996-05-12
        r'(\d{1,2} \w+ \d{4})',                   # e.g. 12 May 1996
    ]
    for pattern in date_patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            try:
                # Try parsing with multiple date formats
                for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%d %B %Y", "%d %b %Y"):
                    try:
                        dob = datetime.strptime(match, fmt)
                        # Skip future dates, they are invalid
                        if dob <= datetime.now():
                            return dob
                    except:
                        pass
            except:
                continue
    return None

def calculate_age(dob):
    today = datetime.today()
    age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
    return age

def parse_criteria(criteria_text):
    """
    Parse criteria text for special checks:
    - Look for 'age<26', 'age>30', etc. 
    - Return a dict with keys like {'age': ('<', 26)}
    """
    criteria_dict = {}
    # Extract age condition with regex
    age_match = re.search(r'age\s*([<>]=?)\s*(\d+)', criteria_text.lower())
    if age_match:
        op = age_match.group(1)
        val = int(age_match.group(2))
        criteria_dict['age'] = (op, val)
    return criteria_dict

def check_age_criteria(age, op, val):
    if op == '<':
        return age < val
    elif op == '<=':
        return age <= val
    elif op == '>':
        return age > val
    elif op == '>=':
        return age >= val
    return False

def analyze_resume(resume_text, criteria_text):
    if not resume_text:
        return "Could not extract text from resume", False

    crit_dict = parse_criteria(criteria_text)

    missing_criteria = []

    # Check age criteria
    if 'age' in crit_dict:
        dob = extract_dob(resume_text)
        if dob is None:
            missing_criteria.append("Date of Birth (DOB) not found to verify age")
        else:
            age = calculate_age(dob)
            op, val = crit_dict['age']
            if not check_age_criteria(age, op, val):
                missing_criteria.append(f"Age criteria not met (candidate age: {age} years)")

    # For other criteria, simple semantic presence check (case-insensitive)
    # Remove age condition from criteria to avoid false check
    criteria_no_age = re.sub(r'age\s*[<>]=?\s*\d+', '', criteria_text, flags=re.I).strip()
    if criteria_no_age:
        # Split criteria words and check if all present in resume text
        # (You can improve this logic with NLP libraries)
        missing_keywords = [word for word in criteria_no_age.lower().split() if word and word not in resume_text.lower()]
        if missing_keywords:
            missing_criteria.append(f"Missing keywords: {', '.join(missing_keywords)}")

    if missing_criteria:
        return "Does not qualify - " + "; ".join(missing_criteria), False
    else:
        return "This resume qualifies for the next round of recruitment", True

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
                rank = "-" if not qualifies else 0  # will assign ranks later
                results.append({
                    "S.No": idx,
                    "Resume Name": pdf_file.name,
                    "Analysis": analysis,
                    "Rank": rank
                })

            # Assign rank for qualified resumes only (sorted by Resume Name)
            qualified = [r for r in results if r["Rank"] == 0]
            qualified.sort(key=lambda x: x["Resume Name"])
            for i, r in enumerate(qualified, start=1):
                r["Rank"] = i

            # Put unqualified resumes at the end
            unqualified = [r for r in results if r["Rank"] == "-"]

            final_results = qualified + unqualified

            # Reassign S.No after sorting
            for i, r in enumerate(final_results, start=1):
                r["S.No"] = i

            # Convert to DataFrame
            df_results = pd.DataFrame(final_results)

            # Display heading centered
            st.markdown("<h3 style='text-align: center; color: #118AB2;'>📊 Analysis Results</h3>", unsafe_allow_html=True)

            # Display centered table with styled cells
            st.dataframe(
                df_results.style.set_properties(**{
                    'text-align': 'center'
                })
            )
