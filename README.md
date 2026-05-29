# DUI Case Analyzer ⚖️📹📄

An AI-powered web application designed for lawyers, defense attorneys, and legal investigators to automate the analysis of Driving Under the Influence (DUI) cases. The application accelerates case review and improves legal accuracy by cross-referencing and identifying inconsistencies between official police reports and corresponding bodycam footage.

## 🚀 Project Overview

Manually reviewing hours of bodycam video alongside multi-page police reports is a time-consuming and error-prone process for legal teams. The **DUI Case Analyzer** solves this problem by using advanced Natural Language Processing (NLP) and Speech-to-Text models to automatically compare video evidence against textual documentation, highlighting structural mismatches, omissions, and factual discrepancies.

### Key Features
* **Dual-Input Integration:** Smooth, unified interface for uploading both video evidence and document files simultaneously.
* **Automated Audio Transcription:** Leverages state-of-the-art speech recognition to extract verbatim spoken dialogue and timestamps from bodycam recordings.
* **NLP Cross-Examination:** Employs advanced text similarity checks and semantic analysis to flags contradictions between what is recorded on camera vs. what is written in the police report.
* **High Capacity Uploads:** Optimized lightweight processing architecture supporting large media file uploads up to **200MB**.
* **User-Centric Legal Dashboard:** Simple drag-and-drop mechanics with structured, actionable insights generated upon completion.

---

## 🛠️ Technology Stack

* **Frontend & Application Framework:** [Streamlit](https://streamlit.io/) (Lightweight, responsive web deployment platform).
* **Speech-to-Text Engine:** [OpenAI Whisper](https://github.com/openai/whisper) (Robust, multilingual audio transcription).
* **Natural Language Processing (NLP):** Python-based text extraction and similarity metrics for identifying report-to-video contradictions.
* **Supported File Formats:** 
    * *Video:* `.mp4`, `.mov`, `.avi`, `.mpeg4`
    * *Documents:* `.pdf`

---

## ⚙️ How It Works

1. **Ingestion:** The user uploads the officer's written police report (PDF) and the corresponding bodycam footage (Video) via the drag-and-drop dashboard.
2. **Transcription Pipeline:** The application extracts the audio channel from the video file and passes it through OpenAI’s Whisper model to generate an exact textual transcript.
3. **Document Extraction:** The text from the PDF police report is parsed and structured.
4. **Discrepancy Analysis:** An NLP engine evaluates both texts to flag critical anomalies (e.g., the police report claims the suspect stumbled during a field sobriety test, but the video transcript/timeline reveals a conflicting sequence or statement).
5. **Reporting:** A clean, synchronized breakdown of insights and highlighted mismatches is rendered directly in the web app for manual legal review.

---

## 💻 Installation & Setup

Follow these steps to get a local instance of the application up and running.

### Prerequisites
Ensure you have Python 3.8+ installed along with `ffmpeg` (required by Whisper for audio processing).

```bash
# Install ffmpeg (macOS example)
brew install ffmpeg

# Install ffmpeg (Ubuntu/Debian example)
sudo apt update && sudo apt install ffmpeg
