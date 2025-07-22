import streamlit as st
import torch
import whisper
import fitz  # PyMuPDF
from moviepy.editor import VideoFileClip # Although imported, VideoFileClip is not used in the provided code.
from PyPDF2 import PdfReader # Although imported, PdfReader is not used in the provided code.
from docx import Document
import tempfile
import os
import subprocess
import logging # Import logging for more detailed error messages
import shutil # Import shutil for safe deletion of temporary files

# Configure logging for better debugging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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

# Use st.cache_resource for the Whisper model to load it only once
# This significantly speeds up subsequent runs and saves memory
@st.cache_resource
def load_whisper_model():
    """Loads the Whisper model and caches it."""
    try:
        logging.info("Attempting to load Whisper model 'small'...")
        model = whisper.load_model("small")
        logging.info("Whisper model loaded successfully.")
        return model
    except Exception as e:
        logging.error(f"Failed to load Whisper model: {e}")
        st.error(f"Could not load the AI model. Please try again or contact support. Error: {e}")
        return None

def transcribe_video(video_path):
    """
    Transcribes the audio from a video file using the Whisper model.
    Requires FFmpeg to be installed on the system.
    """
    if not os.path.exists(video_path):
        logging.error(f"Video file not found at path: {video_path}")
        st.error(f"Error: Video file not found at path: {video_path}")
        return ""

    model = load_whisper_model()
    if model is None:
        return "" # Model failed to load, return empty transcript

    try:
        logging.info(f"Starting transcription for video: {video_path}")
        # Add a timeout to subprocess call if you suspect it's hanging
        # Note: whisper.transcribe might not directly expose timeout for ffmpeg,
        # but you can wrap it if needed for more control.
        result = model.transcribe(video_path)
        logging.info("Video transcription completed successfully.")
        return result["text"]
    except subprocess.CalledProcessError as e:
        logging.error(f"FFmpeg failed during video processing: {e.stderr.decode()}")
        st.error(f"FFmpeg failed to process the video. Make sure ffmpeg is installed and the video is valid. Error details: {e.stderr.decode()}")
        return ""
    except Exception as e:
        logging.error(f"Unexpected error during transcription: {str(e)}", exc_info=True)
        st.error(f"An unexpected error occurred during transcription: {str(e)}")
        return ""

def read_report(report_file):
    """Reads text from PDF or DOCX report files."""
    if report_file.name.endswith(".pdf"):
        logging.info(f"Reading PDF file: {report_file.name}")
        return read_pdf(report_file)
    elif report_file.name.endswith(".docx"):
        logging.info(f"Reading DOCX file: {report_file.name}")
        doc = Document(report_file)
        return "\n".join([para.text for para in doc.paragraphs])
    else:
        logging.warning(f"Unsupported report file type: {report_file.name}")
        st.warning("Unsupported report file type. Please upload a PDF or DOCX.")
        return ""

def read_pdf(pdf_file):
    """Reads text from a PDF file using PyMuPDF (fitz)."""
    text = ""
    tmp_path = None # Initialize tmp_path
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(pdf_file.read())
            tmp_path = tmp.name
        logging.info(f"PDF saved to temporary path: {tmp_path}")
        doc = fitz.open(tmp_path)
        for page in doc:
            text += page.get_text()
        logging.info("PDF reading completed.")
    except Exception as e:
        logging.error(f"Error reading PDF file: {str(e)}", exc_info=True)
        st.error(f"Error reading PDF file: {str(e)}")
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path) # Ensure temp file is deleted
            logging.info(f"Temporary PDF file deleted: {tmp_path}")
    return text

def compare_texts(transcript, report_text):
    """Compares transcript lines with report text to find matching phrases."""
    shared_phrases = []
    # Normalize texts for better comparison (e.g., lowercasing, removing extra spaces)
    normalized_report_text = report_text.lower().strip()
    
    for line in transcript.splitlines():
        normalized_line = line.strip().lower()
        if normalized_line and normalized_line in normalized_report_text:
            shared_phrases.append(line.strip()) # Append original line for display
    
    # Optional: You might want to use more sophisticated NLP techniques for comparison
    # (e.g., fuzzy matching, sentence embeddings) for better results,
    # but for exact phrase matching, this is fine.
    
    return shared_phrases

def generate_word_summary(transcript, report_text, matching_lines):
    """Generates a Word document summary of the analysis."""
    doc = Document()
    doc.add_heading("DUI Case Analysis Summary", 0)

    doc.add_heading("Transcript Summary", level=1)
    doc.add_paragraph(transcript if transcript else "No transcript available.")

    doc.add_heading("Police Report", level=1)
    doc.add_paragraph(report_text if report_text else "No report text available.")

    doc.add_heading("Matched Phrases", level=1)
    if matching_lines:
        for line in matching_lines:
            doc.add_paragraph(f"- {line}")
    else:
        doc.add_paragraph("No matching phrases found.")

    tmp_docx_path = None # Initialize tmp_docx_path
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
            doc.save(tmp.name)
            tmp_docx_path = tmp.name
        logging.info(f"Word summary saved to temporary path: {tmp_docx_path}")
        return tmp_docx_path
    except Exception as e:
        logging.error(f"Error generating Word summary: {str(e)}", exc_info=True)
        st.error(f"Error generating Word summary: {str(e)}")
        return None

# ------------------ Main Logic ------------------
if video_file and (report_file or typed_report):
    st.success("Ready to process!")
    if st.button("Run Analysis"):
        with st.spinner("Processing... This may take a while for large files."):
            tmp_video_path = None
            summary_path = None
            try:
                # Save video to temp file
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_vid:
                    tmp_vid.write(video_file.read())
                    tmp_video_path = tmp_vid.name
                logging.info(f"Video saved to temporary path: {tmp_video_path}")

                if os.path.exists(tmp_video_path):
                    # Transcribe video
                    transcript = transcribe_video(tmp_video_path)

                    # Extract report text
                    report_text = read_report(report_file) if report_file else typed_report
                    if not report_text: # Handle case where manual entry is empty
                        st.warning("No report text provided. Please upload a file or type manually.")
                        transcript = "" # Clear transcript if no report to compare
                        matching_lines = [] # No matches possible
                    
                    # Compare
                    matching_lines = compare_texts(transcript, report_text)

                    # Generate Word summary
                    summary_path = generate_word_summary(transcript, report_text, matching_lines)

                    st.success("Analysis complete!")
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

                    # Display result previews
                    st.subheader("🔊 Transcript")
                    st.text_area("Transcript", transcript if transcript else "No transcript generated.", height=200)

                    st.subheader("✅ Matching Lines")
                    st.text_area("Matching Lines", "\n".join(matching_lines) if matching_lines else "No matching phrases found.", height=150)

                else:
                    st.error("Temporary video file could not be saved. Please try again.")

            except Exception as e:
                logging.error(f"An error occurred during analysis: {str(e)}", exc_info=True)
                st.error(f"An unexpected error occurred during analysis: {str(e)}")
            finally:
                # Clean up temporary files
                if tmp_video_path and os.path.exists(tmp_video_path):
                    os.remove(tmp_video_path)
                    logging.info(f"Temporary video file deleted: {tmp_video_path}")
                if summary_path and os.path.exists(summary_path):
                    os.remove(summary_path)
                    logging.info(f"Temporary summary file deleted: {summary_path}")

else:
    st.info("Please upload both a bodycam video and a police report (or enter manually) to proceed.")

