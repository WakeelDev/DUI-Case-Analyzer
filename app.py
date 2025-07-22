import os
import streamlit as st
import whisper
import fitz  # PyMuPDF
import docx
from PyPDF2 import PdfReader
from docx import Document
from io import BytesIO
import tempfile
from datetime import datetime
from docx.shared import Inches

# Load Whisper model
model = whisper.load_model("base")

# Function to transcribe video using Whisper
def transcribe_video(video_path):
    try:
        result = model.transcribe(video_path)
        return result["text"]
    except Exception as e:
        st.error(f"Unexpected error during transcription: {e}")
        return ""

# Function to extract text from uploaded police report
def extract_text_from_report(uploaded_file):
    try:
        if uploaded_file.name.endswith(".pdf"):
            pdf_reader = PdfReader(uploaded_file)
            return "\n".join([page.extract_text() or "" for page in pdf_reader.pages])
        elif uploaded_file.name.endswith(".docx"):
            doc = Document(uploaded_file)
            return "\n".join([para.text for para in doc.paragraphs])
        else:
            st.error("Unsupported file type.")
            return ""
    except Exception as e:
        st.error(f"Error reading report: {e}")
        return ""

# Function to compare texts and generate summary
def compare_texts(transcript, report_text):
    transcript_lines = set(transcript.lower().splitlines())
    report_lines = set(report_text.lower().splitlines())

    matched_lines = transcript_lines & report_lines
    missing_in_report = transcript_lines - report_lines
    extra_in_report = report_lines - transcript_lines

    return {
        "matched": matched_lines,
        "missing": missing_in_report,
        "extra": extra_in_report
    }

# Function to generate a Word report
def generate_word_report(transcript, report_text, comparison_result):
    doc = Document()
    doc.add_heading("DUI Case Analysis Report", 0)

    doc.add_heading("1. Transcript", level=1)
    doc.add_paragraph(transcript)

    doc.add_heading("2. Police Report Text", level=1)
    doc.add_paragraph(report_text)

    doc.add_heading("3. Comparison Result", level=1)
    doc.add_heading("Matched Statements", level=2)
    for line in comparison_result["matched"]:
        doc.add_paragraph(line)

    doc.add_heading("Missing in Report", level=2)
    for line in comparison_result["missing"]:
        doc.add_paragraph(line)

    doc.add_heading("Extra in Report", level=2)
    for line in comparison_result["extra"]:
        doc.add_paragraph(line)

    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

# Streamlit App
st.set_page_config(page_title="DUI Case Analyzer", layout="centered")
st.title("🚔 DUI Case Analyzer (Video + Report Comparator)")
st.write("Upload a police bodycam video and the official report (PDF/DOCX) to generate a comparison report.")

video_file = st.file_uploader("Upload Bodycam Video", type=["mp4", "mov", "avi"])
report_file = st.file_uploader("Upload Police Report (PDF or DOCX)", type=["pdf", "docx"])

if st.button("Analyze") and video_file and report_file:
    with st.spinner("Transcribing video..."):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_video:
            tmp_video.write(video_file.read())
            tmp_video_path = tmp_video.name

        transcript = transcribe_video(tmp_video_path)
        os.remove(tmp_video_path)

    if transcript:
        with st.spinner("Extracting report text..."):
            report_text = extract_text_from_report(report_file)

        with st.spinner("Comparing contents..."):
            comparison_result = compare_texts(transcript, report_text)

        with st.spinner("Generating report..."):
            word_buffer = generate_word_report(transcript, report_text, comparison_result)
            st.success("Report generated successfully!")

            st.download_button(
                label="📄 Download Report (DOCX)",
                data=word_buffer,
                file_name=f"dui_case_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
    else:
        st.error("Transcription failed. Please try again.")
