import streamlit as st
import os
import tempfile
import torch
import fitz  # PyMuPDF
from moviepy.editor import VideoFileClip
from docx import Document
import whisper

st.set_page_config(page_title="DUI Case Analyzer", layout="wide")

st.title("🚔 DUI Case Analyzer (Video + Report Comparator)")

# Upload section in sidebar
with st.sidebar:
    st.header("Upload Files")
    video_file = st.file_uploader("Upload Bodycam Video", type=["mp4", "mov", "avi"])
    report_file = st.file_uploader("Upload Police Report (PDF or DOCX)", type=["pdf", "docx"])

# Optional text box if no report is uploaded
typed_report = None
if not report_file:
    typed_report = st.text_area(
        label="",
        placeholder="Type the report manually",
        height=250
    )

# Process the uploaded report
def extract_text_from_report(report_file):
    if report_file.name.endswith(".pdf"):
        pdf_doc = fitz.open(stream=report_file.read(), filetype="pdf")
        return "\n".join(page.get_text() for page in pdf_doc)
    elif report_file.name.endswith(".docx"):
        doc = Document(report_file)
        return "\n".join(para.text for para in doc.paragraphs)
    else:
        return None

# Transcribe the video using Whisper
def transcribe_video(video_path):
    model = whisper.load_model("base")  # or "medium", "small", etc.
    return model.transcribe(video_path)["text"]

# Process when both inputs are available
if (video_file and report_file) or (video_file and typed_report):
    with st.spinner("Processing video and report..."):

        # Save the uploaded video temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_vid:
            tmp_vid.write(video_file.read())
            tmp_video_path = tmp_vid.name

        # Transcribe video
        transcript = transcribe_video(tmp_video_path)

        # Load report
        if report_file:
            report_text = extract_text_from_report(report_file)
        else:
            report_text = typed_report

        # Display results
        st.subheader("🔊 Transcription from Bodycam Video")
        st.text_area("Transcript:", transcript, height=300)

        st.subheader("📝 Police Report Content")
        st.text_area("Report:", report_text, height=300)

        # You could add comparison or analysis here
        st.success("✅ Analysis complete!")

# Just a notice if not all inputs are available
elif video_file and not report_file and not typed_report:
    st.warning("Please upload a police report or type it manually.")

elif not video_file:
    st.info("Please upload a bodycam video to start.")
