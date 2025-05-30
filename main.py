import streamlit as st
import PyPDF2
import pandas as pd
import re
from datetime import datetime
import anthropic

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

# --- Anthropic API Setup ---
API_KEY = "your_anthropic_api_key_here"  # Replace with your actual key
client = anthropic.Client(API_KEY)

# --- Extract text from PDF ---
def extract_text_from_pdf(pdf_file):
    try:
        reader = PyPDF2.PdfReader(pdf_file)
        text = "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
        return text
    except Exception:
        return ""

# --- Parse Date of Birth and calculate age ---
def extract_dob_and_age(text):
    # Look for date patterns (dd/mm/yyyy, dd-mm-yyyy, yyyy-mm-dd etc.)
    dob_patterns = [
        r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b",
        r"\b(\d{4}[/-]\d{1,2}[/-]\d{1,2})\b"
    ]
    for pattern in dob_patterns:
        matches = re.findall(pattern, text)
        for date_str in matches:
            for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%Y/%m/%d", "%d/%m/%y", "%d-%m-%y"):
                try:
                    dob = datetime.strptime(date_str, fmt)
                    today = datetime.today()
                    age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
                    if 0 < age < 100:  # reasonable age
                        return dob, age
                except Exception:
                    continue
    return None, None

# --- Extract total experience in years from resume text ---
def extract_experience_years(text):
    # Look for common patterns like "X years", "X yrs", "X+ years"
    experience_patterns = [
        r"(\d+)\s*\+?\s*years?",
        r"(\d+)\s*\+?\s*yrs?"
    ]
    years_list = []
    for pattern in experience_patterns:
        matches = re.findall(pattern, text, flags=re.IGNORECASE)
        for match in matches:
            try:
                years = int(match)
                if 0 < years < 60:  # sanity check
                    years_list.append(years)
            except:
                continue
    if years_list:
        return max(years_list)
    return 0

# --- Use Anthropic API for semantic matching ---
def semantic_check(resume_text, criteria):
    prompt = f"""You are a helpful assistant to check if the resume meets the job criteria.
Resume Text:
\"\"\"{resume_text}\"\"\"

Job Criteria:
\"\"\"{criteria}\"\"\"

Answer with 'YES' if resume meets criteria, otherwise 'NO'. Then briefly explain which criteria is missing if any."""
    try:
        response = client.completions.create(
            model="claude-2",
            prompt=anthropic.HUMAN_PROMPT + prompt + anthropic.AI_PROMPT,
            max_tokens_to_sample=200,
            temperature=0
        )
        answer = response.completion.strip()
        return answer
    except Exception as e:
        return f"Error in API call: {str(e)}"

# --- Parse criteria like 'age < 26', 'experience > 2 years' ---
def check_numeric_criteria(criteria, dob, age, experience):
    # For example criteria: "age < 26", "experience > 2 years", "experience less than 3 years"
    # Normalize criteria text
    c = criteria.lower().replace("years", "").replace("year", "").strip()

    # Check age
    age_match = re.search(r"age\s*([<>]=?)\s*(\d+)", c)
    if age_match and age is not None:
        op, val = age_match.group(1), int(age_match.group(2))
        if not eval(f"{age} {op} {val}"):
            return f"Does not qualify - Age criteria not met (Age: {age}, Required: {op} {val})", False

    # Check experience
    exp_match = re.search(r"experience\s*([<>]=?)\s*(\d+)", c)
    if exp_match:
        op, val = exp_match.group(1), int(exp_match.group(2))
        if not eval(f"{experience} {op} {val}"):
            return f"Does not qualify - Experience criteria not met (Experience: {experience} yrs, Required: {op} {val} yrs)", False

    # Handle "less than" or "greater than" wording
    if "age less than" in c and age is not None:
        val = int(re.findall(r"\d+", c)[0])
        if not (age < val):
            return f"Does not qualify - Age criteria not met (Age: {age}, Required: less than {val})", False
    if "age greater than" in c and age is not None:
        val = int(re.findall(r"\d+", c)[0])
        if not (age > val):
            return f"Does not qualify - Age criteria not met (Age: {age}, Required: greater than {val})", False
    if "experience less than" in c:
        val = int(re.findall(r"\d+", c)[0])
        if not (experience < val):
            return f"Does not qualify - Experience criteria not met (Experience: {experience} yrs, Required: less than {val})", False
    if "experience greater than" in c:
        val = int(re.findall(r"\d+", c)[0])
        if not (experience > val):
            return f"Does not qualify - Experience criteria not met (Experience: {experience} yrs, Required: greater than {val})", False

    return None, True

# --- Main analyze function ---
def analyze_resume(resume_text, criteria):
    if not resume_text:
        return "Could not extract text from resume", False

    dob, age = extract_dob_and_age(resume_text)
    experience = extract_experience_years(resume_text)

    numeric_check_msg, numeric_check_result = check_numeric_criteria(criteria, dob, age, experience)
    if not numeric_check_result:
        return numeric_check_msg, False

    # Semantic check using Anthropic API
    semantic_result = semantic_check(resume_text, criteria)

    if semantic_result.startswith("YES"):
        return "This resume qualifies for the next round of recruitment", True
    elif semantic_result.startswith("NO"):
        # Try to extract missing info from semantic_result explanation
        explanation = semantic_result[2:].strip()
        return f"Does not qualify - {explanation}", False
    else:
        # fallback if API fails or unexpected response
        return semantic_result, False

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
