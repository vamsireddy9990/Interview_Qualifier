import streamlit as st
import PyPDF2
import pandas as pd
import io
# test commit1
#  --- SETUP ---
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
        font-weight: 900;  /* Increased from bold to 900 */
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #118AB2;
        margin-bottom: 0.5rem;
        font-weight: 700;  /* Added bold for sub-headers */
    }
    div.stButton > button {
        display: block;
        margin: 0 auto;
        padding: 8px 20px;
        font-size: 1rem;
        font-weight: 700;  /* Added bold for buttons */
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
        font-weight: 700 !important;  /* Added bold for table headers */
    }
    /* Center download button */
    div.stDownloadButton > button {
        display: block !important;
        margin: 0 auto !important;
        font-weight: 700 !important;  /* Added bold for download button */
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

# --- FUNCTION: Extract text from PDF ---
def extract_text_from_pdf(pdf_file):
    try:
        reader = PyPDF2.PdfReader(pdf_file)
        text = "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
        return text
    except Exception:
        return ""

# --- FUNCTION: Analyze Resume ---
def analyze_resume(resume_text, criteria):
    """
    Enhanced analysis logic:
    - Splits criteria into key terms
    - Checks for contextual matches in resume
    - Considers partial matches and related terms
    """
    if not resume_text:
        return "Could not extract text from resume", False
        
    # Convert both texts to lowercase for comparison
    resume_text = resume_text.lower()
    criteria = criteria.lower()
    
    # Split criteria into key terms (removing common words)
    common_words = {'and', 'or', 'the', 'in', 'on', 'at', 'to', 'for', 'with', 'a', 'an'}
    key_terms = [term.strip() for term in criteria.split() if term.strip() and term not in common_words]
    
    # Count matching terms
    matches = []
    for term in key_terms:
        # Check for exact matches
        if term in resume_text:
            matches.append(term)
        # Check for plural/singular variations
        elif term + 's' in resume_text or (term.endswith('s') and term[:-1] in resume_text):
            matches.append(term)
            
    # Calculate match percentage
    match_percentage = len(matches) / len(key_terms) if key_terms else 0
    
    if match_percentage >= 0.6:  # 60% or more matches
        matched_skills = ", ".join(matches)
        return f"Qualifies - Matched skills: {matched_skills}", True
    else:
        missing_skills = ", ".join(set(key_terms) - set(matches))
        return f"Does not qualify - Missing key skills: {missing_skills}", False

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
            st.markdown("<h3 style='text-align: center; color: #118AB2; font-weight: 900;'>📊 Analysis Results</h3>", unsafe_allow_html=True)

            # Display centered table with styled cells
            st.dataframe(
                df_results.style.set_properties(**{
                    'text-align': 'center',
                    'font-weight': '700'
                })
            )
