
import os
import tempfile
import whisper
import streamlit as st
from moviepy.editor import VideoFileClip
from PyPDF2 import PdfReader
from docx import Document

# Title
st.title("DUI Case Analyzer (Video + Report Comparator)")

# Sidebar
st.sidebar.title("Upload Files")

# Upload the bodycam video
video_file = st.sidebar.file_uploader("Upload Bodycam Video", type=["mp4", "mov", "avi", "mkv"])

# Upload the police report (PDF or DOCX)
report_file = st.sidebar.file_uploader("Upload Police Report", type=["pdf", "docx"])

# Step 1: Transcribe the bodycam video
@st.cache_resource
def transcribe_video(video_path):
    model = whisper.load_model("base")
    result = model.transcribe(video_path)
    return result["text"]

# Step 2: Read the police report
def extract_text_from_report(uploaded_file):
    if uploaded_file.name.endswith(".pdf"):
        reader = PdfReader(uploaded_file)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
        return text
    elif uploaded_file.name.endswith(".docx"):
        doc = Document(uploaded_file)
        return "
".join([para.text for para in doc.paragraphs])"
    else:
        return "Unsupported file format."

# Step 3: Compare Transcription and Report
def compare_texts(transcript, report):
    transcript_lines = transcript.lower().splitlines()
    report_lines = report.lower().splitlines()
    matched = []
    unmatched = []

    for line in transcript_lines:
        if any(line.strip() in r for r in report_lines):
            matched.append(line)
        else:
            unmatched.append(line)

    return matched, unmatched

# UI Processing
if video_file and report_file:
    st.subheader("Processing...")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_video:
        tmp_video.write(video_file.read())
        tmp_video_path = tmp_video.name

    with st.spinner("Transcribing video..."):
        transcript = transcribe_video(tmp_video_path)
        st.success("Transcription complete!")

    with st.spinner("Extracting police report..."):
        report_text = extract_text_from_report(report_file)
        st.success("Report extraction complete!")

    with st.spinner("Comparing texts..."):
        matched, unmatched = compare_texts(transcript, report_text)

        st.subheader("Matched Statements")
        st.write("\n".join(matched) if matched else "No matches found.")

        st.subheader("Unmatched Statements")
        st.write("\n".join(unmatched) if unmatched else "Everything matched.")

    # Optional: Save full comparison to Word doc
    save_doc = st.button("Download Comparison Report")
    if save_doc:
        doc = Document()
        doc.add_heading("DUI Case Comparison Report", 0)
        doc.add_heading("Matched Statements", level=1)
        for line in matched:
            doc.add_paragraph(line)
        doc.add_heading("Unmatched Statements", level=1)
        for line in unmatched:
            doc.add_paragraph(line)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp_docx:
            doc.save(tmp_docx.name)
            with open(tmp_docx.name, "rb") as file:
                st.download_button("Download Report", file, file_name="comparison_report.docx")
