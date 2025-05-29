import streamlit as st
import PyPDF2
import pandas as pd
import io

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
    /* Center download button */
    div.stDownloadButton > button {
        display: block !important;
        margin: 0 auto !important;
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
    Dummy analysis logic:
    - If the criteria word appears in the resume text, qualifies.
    - Else does not qualify.
    Replace this with your actual AI / NLP logic.
    """
    if not resume_text:
        return "Could not extract text from resume", False
    if criteria.lower() in resume_text.lower():
        return "This resume qualifies for the next round of recruitment", True
    else:
        keyword = criteria.split()[0] if criteria else "required skills"
        return f"Does not qualify - missing experience in {keyword}", False

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
            
            # Prepare Excel file in memory
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df_results.to_excel(writer, index=False)
            excel_data = output.getvalue()

            # Center container for download button
            col1, col2, col3 = st.columns([1,2,1])
            with col2:
                # Download button
                st.download_button(
                    label="📥 Download Results as Excel",
                    data=excel_data,
                    file_name="resume_analysis_results.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
