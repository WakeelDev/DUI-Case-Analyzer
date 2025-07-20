import os
import tempfile
import whisper
from moviepy.editor import VideoFileClip
from docx import Document
import streamlit as st

# Function to transcribe video using OpenAI Whisper
@st.cache_resource
def transcribe_video(video_path):
    model = whisper.load_model("base")
    result = model.transcribe(video_path)
    return result["text"]

# Function to read the police report text
def read_report(docx_file):
    doc = Document(docx_file)
    full_text = "\n".join([para.text for para in doc.paragraphs])
    return full_text

# Function to compare transcript and report (very basic for now)
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

    # Save to a temporary file and return path
    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
        doc.save(tmp.name)
        return tmp.name

# Streamlit UI
st.title("DUI Case Analyzer (Video + Report Comparator)")

video_file = st.file_uploader("Upload Bodycam Video (.mp4 or .mov)", type=["mp4", "mov"])
report_file = st.file_uploader("Upload Police Report (.docx)", type=["docx"])

if video_file and report_file:
    with st.spinner("Processing..."):

        # Save temp video
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_vid:
            tmp_vid.write(video_file.read())
            tmp_video_path = tmp_vid.name

        # Step 1: Transcribe the video
        transcript = transcribe_video(tmp_video_path)

        # Step 2: Read report
        report_text = read_report(report_file)

        # Step 3: Compare transcript and report
        matching_lines = compare_texts(transcript, report_text)

        # Step 4: Generate downloadable Word summary
        summary_path = generate_word_summary(transcript, report_text, matching_lines)

    st.success("Analysis complete!")
    st.download_button("Download Word Report", data=open(summary_path, "rb").read(), file_name="dui_case_summary.docx")

    st.subheader("Preview (Transcript + Matches)")
    st.text_area("Transcript", transcript, height=200)
    st.text_area("Matching Lines", "\n".join(matching_lines), height=150 if matching_lines else 50)

