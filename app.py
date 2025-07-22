import streamlit as st
import torch
import whisper
import fitz  # PyMuPDF
from docx import Document
import tempfile
import os
import subprocess
import logging
import shutil

# ------------------ FFmpeg Fallback Path ------------------
# Ensure ffmpeg is accessible in Streamlit Cloud
if not shutil.which("ffmpeg"):
    os.environ["PATH"] += os.pathsep + "/usr/bin"

# ------------------ Logging Setup ------------------
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# ------------------ FFmpeg Diagnostic ------------------
try:
    result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True, check=True)
    logging.info(f"FFmpeg is available. Version:\n{result.stdout.splitlines()[0]}")
except Exception as e:
    logging.error("FFmpeg check failed:", exc_info=True)

# ------------------ Streamlit UI ------------------
st.set_page_config(page_title="DUI Case Analyzer", layout="centered")
st.title("🚔 DUI Case Analyzer (Video + Report Comparator)")
st.markdown("Upload a **bodycam video** and either **upload a police report** or **type it manually.**")

# ------------------ Sidebar Uploads ------------------
st.sidebar.header("Upload Files")
video_file = st.sidebar.file_uploader("Upload Bodycam Video", type=["mp4", "mov", "avi", "mkv"])
report_file = st.sidebar.file_uploader("Upload Police Report (PDF or DOCX)", type=["pdf", "docx"])

# ------------------ Manual Report Entry ------------------
typed_report = None
if not report_file:
    typed_report = st.text_area("Manual Report Entry", placeholder="Type the report here...", height=200)

# ------------------ Whisper Model Loader ------------------
@st.cache_resource
def load_whisper_model():
    try:
        logging.info("Loading Whisper model 'small'...")
        model = whisper.load_model("small")
        logging.info("Whisper model loaded successfully.")
        return model
    except Exception as e:
        logging.error(f"Failed to load Whisper model: {e}")
        st.error(f"Could not load AI model. Please try again later. Error: {e}")
        return None

# ------------------ Transcription ------------------
def transcribe_video(video_path):
    if not os.path.exists(video_path):
        logging.error(f"Video file not found: {video_path}")
        st.error(f"Error: Video file not found.")
        return ""

    model = load_whisper_model()
    if model is None:
        return ""

    try:
        logging.info(f"Transcribing video: {video_path}")
        result = model.transcribe(video_path)
        logging.info("Transcription completed.")
        return result["text"]
    except FileNotFoundError:
        logging.error("FFmpeg not found in system PATH.")
        st.error("Error: FFmpeg is required but not found. Please contact support.")
        return ""
    except subprocess.CalledProcessError as e:
        logging.error(f"FFmpeg failed: {e.stderr}")
        st.error("FFmpeg failed to process the video. Please ensure it's valid.")
        return ""
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}", exc_info=True)
        st.error(f"An unexpected error occurred during transcription: {str(e)}")
        return ""

# ------------------ Report File Reader ------------------
def read_report(report_file):
    if report_file.name.endswith(".pdf"):
        logging.info(f"Reading PDF: {report_file.name}")
        return read_pdf(report_file)
    elif report_file.name.endswith(".docx"):
        logging.info(f"Reading DOCX: {report_file.name}")
        doc = Document(report_file)
        return "\n".join([para.text for para in doc.paragraphs])
    else:
        logging.warning(f"Unsupported file: {report_file.name}")
        st.warning("Unsupported file type. Please upload a PDF or DOCX.")
        return ""

def read_pdf(pdf_file):
    text = ""
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(pdf_file.read())
            tmp_path = tmp.name
        doc = fitz.open(tmp_path)
        for page in doc:
            text += page.get_text()
        logging.info("PDF text extraction complete.")
    except Exception as e:
        logging.error(f"Error reading PDF: {str(e)}", exc_info=True)
        st.error(f"Error reading PDF file: {str(e)}")
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)
            logging.info(f"Temporary PDF deleted: {tmp_path}")
    return text

# ------------------ Text Comparison ------------------
def compare_texts(transcript, report_text):
    shared_phrases = []
    normalized_report = report_text.lower().strip() if report_text else ""
    for line in transcript.splitlines():
        normalized_line = line.strip().lower()
        if normalized_line and normalized_line in normalized_report:
            shared_phrases.append(line.strip())
    return shared_phrases

# ------------------ Word Summary Generator ------------------
def generate_word_summary(transcript, report_text, matching_lines):
    doc = Document()
    doc.add_heading("DUI Case Analysis Summary", 0)

    doc.add_heading("Transcript Summary", level=1)
    doc.add_paragraph(transcript or "No transcript available.")

    doc.add_heading("Police Report", level=1)
    doc.add_paragraph(report_text or "No report text available.")

    doc.add_heading("Matched Phrases", level=1)
    if matching_lines:
        for line in matching_lines:
            doc.add_paragraph(f"- {line}")
    else:
        doc.add_paragraph("No matching phrases found.")

    tmp_docx_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
            doc.save(tmp.name)
            tmp_docx_path = tmp.name
        logging.info(f"Word doc saved at: {tmp_docx_path}")
        return tmp_docx_path
    except Exception as e:
        logging.error(f"Error saving Word doc: {str(e)}", exc_info=True)
        st.error(f"Error generating report: {str(e)}")
        return None

# ------------------ Main Processing Logic ------------------
if video_file and (report_file or typed_report):
    st.success("Ready to process!")
    if st.button("Run Analysis"):
        with st.spinner("Processing... This may take a while."):
            tmp_video_path = None
            summary_path = None
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_vid:
                    tmp_vid.write(video_file.read())
                    tmp_video_path = tmp_vid.name
                logging.info(f"Video saved at: {tmp_video_path}")

                transcript = transcribe_video(tmp_video_path)
                report_text = read_report(report_file) if report_file else typed_report

                if not report_text:
                    st.warning("No report text found. Please upload or type it.")
                    matching_lines = []
                else:
                    matching_lines = compare_texts(transcript, report_text)

                summary_path = generate_word_summary(transcript, report_text, matching_lines)

                st.success("✅ Analysis complete!")

                if summary_path and os.path.exists(summary_path):
                    with open(summary_path, "rb") as f:
                        st.download_button(
                            "📄 Download Word Report",
                            data=f.read(),
                            file_name="dui_case_summary.docx",
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                        )
                else:
                    st.error("Could not generate Word report.")

                st.subheader("🔊 Transcript")
                st.text_area("Transcript", transcript or "No transcript generated.", height=200)

                st.subheader("✅ Matching Lines")
                st.text_area("Matching Lines", "\n".join(matching_lines) or "No matches found.", height=150)

            except Exception as e:
                logging.error(f"Main error: {str(e)}", exc_info=True)
                st.error(f"An error occurred during analysis: {str(e)}")
            finally:
                if tmp_video_path and os.path.exists(tmp_video_path):
                    os.remove(tmp_video_path)
                    logging.info(f"Temp video deleted: {tmp_video_path}")
                if summary_path and os.path.exists(summary_path):
                    os.remove(summary_path)
                    logging.info(f"Temp report deleted: {summary_path}")
else:
    st.info("Please upload both a video and a report (or enter manually) to proceed.")
