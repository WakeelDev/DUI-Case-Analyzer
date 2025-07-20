import streamlit as st
import torch
import whisper
import fitz  # PyMuPDF
from moviepy.editor import VideoFileClip
from PyPDF2 import PdfReader
from docx import Document
import tempfile
import os

# -------------------------------
# 🔐 Password Protection Block
# -------------------------------
st.title("DUI Case Analyzer (Video + Report Comparator)")

password = st.text_input("Enter password to continue", type="password")

if password != "yourSecretPassword":
    st.warning("Access denied. Please enter the correct password.")
    st.stop()

# Function to transcribe video using OpenAI Whisper
@st.cache_resource
def transcribe_video(video_path):
    model = whisper.load_model("small")
    result = model.transcribe(video_path)
    return result["text"]

# Function to read the police report text (PDF or DOCX)
def read_report(report_file):
    if report_file.name.endswith(".pdf"):
        return read_pdf(report_file)
    else:
        doc = Document(report_file)
        return "\n".join([para.text for para in doc.paragraphs])

# Read PDF using PyMuPDF
def read_pdf(pdf_file):
    text = ""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(pdf_file.read())
        tmp_path = tmp.name
    doc = fitz.open(tmp_path)
    for page in doc:
        text += page.get_text()
    return text

# Function to compare transcript and report
def compare_texts(transcript, report_text):
    shared_phrases = []
    for line in transcript.splitlines():
        if line.strip() and line.strip() in report_text:
            shared_phrases.append(line.strip())
    return shared_phrases

# Function to create Word summary
def generate_word_summary(transcript, report_text, matching_lines):
    doc = Document()
    doc.add_heading("DUI Case Analysis Summary", 0)

    doc.add_heading("Transcript Summary", level=1)
    doc.add_paragraph(transcript)

    doc.add_heading("Police Report", level=1)
    doc.add_paragraph(report_text)

    doc.add_heading("Matched Phrases", level=1)
    if matching_lines:
        for line in matching_lines:
            doc.add_paragraph(f"- {line}")
    else:
        doc.add_paragraph("No matching phrases found.")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
        doc.save(tmp.name)
        return tmp.name

# ------------------ UI SECTION ------------------
st.set_page_config(page_title="DUI Case Analyzer", layout="centered")
st.title("DUI Case Analyzer (Video + Report Comparator)")
st.markdown("Upload a **bodycam video** and either **upload a police report** or **type it manually**.")

# Sidebar file uploads
st.sidebar.header("Upload Files")
video_file = st.sidebar.file_uploader("Upload Bodycam Video", type=["mp4", "mov", "avi", "mkv"])
report_file = st.sidebar.file_uploader("Upload Police Report (PDF or DOCX)", type=["pdf", "docx"])

# If report is NOT uploaded, show manual input box
typed_report = None
if not report_file:
    typed_report = st.text_area("Manual Report Entry", placeholder="Type the report here...", height=200)

# === PROCESS ===
if video_file and (report_file or typed_report):
    st.success("Ready to process!")
    if st.button("Run Analysis"):
        with st.spinner("Processing... Please wait."):
            # Save video temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_vid:
                tmp_vid.write(video_file.read())
                tmp_video_path = tmp_vid.name

            # Transcribe video
            transcript = transcribe_video(tmp_video_path)

            # Read report
            report_text = read_report(report_file) if report_file else typed_report

            # Compare
            matching_lines = compare_texts(transcript, report_text)

            # Generate summary
            summary_path = generate_word_summary(transcript, report_text, matching_lines)

        st.success("Analysis complete!")
        st.download_button("📄 Download Word Report", data=open(summary_path, "rb").read(), file_name="dui_case_summary.docx")

        # Preview Section
        st.subheader("Preview")
        st.text_area("Transcript", transcript, height=200)
        st.text_area("Matching Lines", "\n".join(matching_lines) if matching_lines else "No matching phrases.", height=150)
else:
    st.info("Please upload both a video and a report (uploaded or typed) to proceed.")
