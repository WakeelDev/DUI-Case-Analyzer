import streamlit as st
import torch
import whisper
import fitz  # PyMuPDF
from moviepy.editor import VideoFileClip
from PyPDF2 import PdfReader
from docx import Document
import tempfile
import os
import subprocess

# ------------------ Streamlit Setup ------------------
st.set_page_config(page_title="DUI Case Analyzer", layout="centered")
st.title("🚔 DUI Case Analyzer (Video + Report Comparator)")
st.markdown("Upload a **bodycam video** and either **upload a police report** or **type it manually.**")

# ------------------ Sidebar Uploads ------------------
st.sidebar.header("Upload Files")
video_file = st.sidebar.file_uploader("Upload Bodycam Video", type=["mp4", "mov", "avi", "mkv"])
report_file = st.sidebar.file_uploader("Upload Police Report (PDF or DOCX)", type=["pdf", "docx"])

# ------------------ Manual Report Option ------------------
typed_report = None
if not report_file:
    typed_report = st.text_area("Manual Report Entry", placeholder="Type the report here...", height=200)

# ------------------ Helper Functions ------------------

def transcribe_video(video_path):
    if not os.path.exists(video_path):
        st.error(f"Error: Video file not found at path: {video_path}")
        return ""

    try:
        model = whisper.load_model("small")
        result = model.transcribe(video_path)
        return result["text"]
    except subprocess.CalledProcessError as e:
        st.error("FFmpeg failed to process the video. Make sure ffmpeg is installed and the video is valid.")
        return ""
    except Exception as e:
        st.error(f"Unexpected error during transcription: {str(e)}")
        return ""

def read_report(report_file):
    if report_file.name.endswith(".pdf"):
        return read_pdf(report_file)
    else:
        doc = Document(report_file)
        return "\n".join([para.text for para in doc.paragraphs])

def read_pdf(pdf_file):
    text = ""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(pdf_file.read())
        tmp_path = tmp.name
    doc = fitz.open(tmp_path)
    for page in doc:
        text += page.get_text()
    return text

def compare_texts(transcript, report_text):
    shared_phrases = []
    for line in transcript.splitlines():
        if line.strip() and line.strip() in report_text:
            shared_phrases.append(line.strip())
    return shared_phrases

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

# ------------------ Main Logic ------------------
if video_file and (report_file or typed_report):
    st.success("Ready to process!")
    if st.button("Run Analysis"):
        with st.spinner("Processing... Please wait."):

            # Save video to temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_vid:
                tmp_vid.write(video_file.read())
                tmp_video_path = tmp_vid.name

            if os.path.exists(tmp_video_path):
                # Transcribe video
                transcript = transcribe_video(tmp_video_path)

                # Extract report text
                report_text = read_report(report_file) if report_file else typed_report

                # Compare
                matching_lines = compare_texts(transcript, report_text)

                # Generate Word summary
                summary_path = generate_word_summary(transcript, report_text, matching_lines)

                st.success("Analysis complete!")
                st.download_button("📄 Download Word Report", data=open(summary_path, "rb").read(), file_name="dui_case_summary.docx")

                # Display result previews
                st.subheader("🔊 Transcript")
                st.text_area("Transcript", transcript, height=200)

                st.subheader("✅ Matching Lines")
                st.text_area("Matching Lines", "\n".join(matching_lines) if matching_lines else "No matching phrases.", height=150)

            else:
                st.error("Temporary video file could not be saved.")

else:
    st.info("Please upload both a bodycam video and a police report (or enter manually) to proceed.")
