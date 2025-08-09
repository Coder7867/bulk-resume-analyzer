import streamlit as st
import spacy
import pandas as pd
import matplotlib.pyplot as plt
import re
import fitz  # PyMuPDF

nlp = spacy.load("en_core_web_sm")

st.title("Resume Analyzer")
st.write("Upload resumes and match them to a job description.")

uploaded_files = st.file_uploader("Upload PDF resumes", type="pdf", accept_multiple_files=True)
job_description = st.text_area("Paste the job description here")

def extract_text_from_pdf(file):
    doc = fitz.open(stream=file.read(), filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    return text

def extract_skills(text):
    doc = nlp(text)
    phrases = set()
    for chunk in doc.noun_chunks:
        phrases.add(chunk.text.strip())
    for ent in doc.ents:
        if ent.label_ in ["ORG", "PERSON", "GPE", "NORP", "PRODUCT", "EVENT", "WORK_OF_ART"]:
            phrases.add(ent.text.strip())
    return list(phrases)

def clean_skills(skills):
    pattern = re.compile(r"^[A-Za-z0-9\-+& ]{2,}$")
    return [s for s in skills if pattern.match(s) and len(s.split()) <= 4]

def extract_jd_phrases(jd_text):
    doc = nlp(jd_text)
    phrases = set()
    for chunk in doc.noun_chunks:
        phrases.add(chunk.text.strip())
    for ent in doc.ents:
        if ent.label_ in ["ORG", "PRODUCT", "EVENT", "WORK_OF_ART"]:
            phrases.add(ent.text.strip())
    return phrases

if st.button("Analyze") and uploaded_files and job_description:
    extracted_texts = [extract_text_from_pdf(file) for file in uploaded_files]
    filtered_skills = [clean_skills(extract_skills(text)) for text in extracted_texts]
    jd_phrases = extract_jd_phrases(job_description)

    jd_scores = []
    for skills in filtered_skills:
        match_count = sum(1 for phrase in jd_phrases if phrase.lower() in [s.lower() for s in skills])
        jd_scores.append(match_count)

    df = pd.DataFrame({
        "Resume": [file.name for file in uploaded_files],
        "JD Match Score": jd_scores
})

    st.subheader("Resume Match Scores")
    st.dataframe(df)

    df["Final Score"] = df["JD Match Score"]
    df_sorted = df.sort_values(by="Final Score", ascending=False).reset_index(drop=True)

    st.subheader("Top Resume Matches")
    st.bar_chart(df_sorted.set_index("Resume")["Final Score"])
