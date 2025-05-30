import streamlit as st
import PyPDF2
import pandas as pd
import re

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
    /* Center the dataframe container */
    div[data-testid="stDataFrameContainer"] {
        margin-left: auto !important;
        margin-right: auto !important;
        max-width: 900px;
    }
    /* Center markdown tables */
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
    st.markdown("<div class='sub-header'>📋 Enter Job Criteria (separate by commas)</div>", unsafe_allow_html=True)
    criteria_input = st.text_area("Example: MBA, age < 26, experience >= 3 years", height=200)

# --- FUNCTION: Extract text from PDF ---
def extract_text_from_pdf(pdf_file):
    try:
        reader = PyPDF2.PdfReader(pdf_file)
        text = "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
        return text.lower()  # lowercase for easier matching
    except Exception:
        return ""

# --- FUNCTION: Parse criteria into conditions and keywords ---
def parse_criteria(criteria_text):
    criteria_list = [c.strip() for c in criteria_text.split(",") if c.strip()]
    conditions = []
    keywords = []
    for c in criteria_list:
        if re.match(r'(age|experience)\s*[<>=]+\s*\d+', c.lower()):
            conditions.append(c.lower())
        else:
            keywords.append(c.lower())
    return conditions, keywords

# --- FUNCTION: Check numeric conditions ---
def check_condition(resume_text, condition):
    # age <number>
    m_age = re.match(r'age\s*([<>=]+)\s*(\d+)', condition)
    if m_age:
        operator, val = m_age.group(1), int(m_age.group(2))
        # Try extract age from resume: look for 'age: 25' or '25 years old' etc.
        age_match = re.search(r'age[:\s]*([0-9]{1,2})', resume_text)
        if not age_match:
            age_match = re.search(r'([0-9]{1,2})\s*years\s*old', resume_text)
        if age_match:
            age = int(age_match.group(1))
            if operator == '<':
                return age < val
            elif operator == '>':
                return age > val
            elif operator == '<=':
                return age <= val
            elif operator == '>=':
                return age >= val
            elif operator == '==':
                return age == val
        return False  # Age not found means condition not met

    # experience <number>
    m_exp = re.match(r'experience\s*([<>=]+)\s*(\d+)', condition)
    if m_exp:
        operator, val = m_exp.group(1), int(m_exp.group(2))
        # Try extract experience years from resume, e.g. "3 years experience", "experience: 5"
        exp_match = re.search(r'experience[:\s]*([0-9]+)', resume_text)
        if not exp_match:
            exp_match = re.search(r'([0-9]+)\s*years\s*experience', resume_text)
        if exp_match:
            exp = int(exp_match.group(1))
            if operator == '<':
                return exp < val
            elif operator == '>':
                return exp > val
            elif operator == '<=':
                return exp <= val
            elif operator == '>=':
                return exp >= val
            elif operator == '==':
                return exp == val
        return False  # Experience not found means condition not met

    # If unknown condition, return False
    return False

# --- FUNCTION: Analyze Resume ---
def analyze_resume(resume_text, conditions, keywords):
    if not resume_text:
        return "Could not extract text from resume", False

    missing_criteria = []

    # Check numeric conditions
    for cond in conditions:
        if not check_condition(resume_text, cond):
            missing_criteria.append(cond)

    # Check keywords presence (simple substring match)
    for kw in keywords:
        if kw not in resume_text:
            missing_criteria.append(kw)

    if not missing_criteria:
        return "This resume qualifies for the next round of recruitment", True
    else:
        missing_str = ", ".join(missing_criteria)
        return f"Does not qualify - missing criteria: {missing_str}", False

# --- ANALYZE ACTION ---
if st.button("🚀 Analyze Resumes"):
    if not uploaded_files or not criteria_input:
        st.warning("Please upload resumes and provide job criteria.")
    elif len(uploaded_files) > 10:
        st.error("⚠️ Limit is 10 resumes at a time.")
    else:
        with st.spinner("Analyzing resumes... ⏳"):
            conditions, keywords = parse_criteria(criteria_input)
            results = []
            for idx, pdf_file in enumerate(uploaded_files, start=1):
                text = extract_text_from_pdf(pdf_file)
                analysis, qualifies = analyze_resume(text, conditions, keywords)
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
