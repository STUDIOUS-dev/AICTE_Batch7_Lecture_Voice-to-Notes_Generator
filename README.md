# IntelliLecture -- AI-Powered Lecture Intelligence System

A web application that converts lecture audio files into comprehensive,
structured study materials using state-of-the-art pretrained AI models.
Built with a **FastAPI** backend and **React.js / Vite** frontend.

---

## Recent Updates

- **Enhanced AI Outputs**: Improved the coherence and accuracy of AI-generated summaries (overview, key points, concepts) and assessments (quizzes and flashcards) to ensure high-quality educational materials.
- **Project Structure Optimization**: Transitioned from the original Django monolith architecture to a more scalable separated backend (FastAPI) and frontend (React.js/Vite) stack.
- **Pipeline Refinements**: Adjusted NLP cleaning and evaluation metrics processing for better general reliability.

---

## Project Structure

```
IntelliLecture/
├── backend/
│   ├── main.py              # FastAPI application and route handlers
│   └── services/            # Modular AI services
│       ├── asr.py           # Whisper Speech-to-Text
│       ├── summarizer.py    # BART Summarization
│       ├── nlp_utils.py     # KeyBERT + Topic Segmentation
│       ├── quiz_gen.py      # Flan-T5 Quiz & Flashcards
│       ├── evaluator.py     # WER & ROUGE Metrics
│       └── pdf_export.py    # ReportLab PDF generation
├── frontend/
│   ├── src/
│   │   ├── App.jsx          # Main React application component
│   │   ├── App.css          # Component styles (EventPop theme)
│   │   ├── index.css        # Global CSS variables and resets
│   │   └── main.jsx         # React entry point
│   ├── index.html           # HTML shell
│   ├── vite.config.js       # Vite config with API proxy
│   └── package.json
├── data/                    # Auto-created: jobs JSON + uploaded audio
├── ffmpeg.exe               # Bundled FFmpeg binary (Windows)
└── requirements.txt         # Python dependencies
```

---

## Setup Instructions

### 1. Prerequisites

- Python 3.10+
- Node.js 18+ and npm
- **FFmpeg**: A `ffmpeg.exe` is bundled in the project root for Windows. On other platforms:
  - **macOS**: `brew install ffmpeg`
  - **Ubuntu/Debian**: `sudo apt install ffmpeg`

### 2. Create & Activate Virtual Environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install Python Dependencies

```bash
pip install -r requirements.txt
```

> This will download several GB of model weights on first run (Whisper, BART, Flan-T5, sentence-transformers).
> Subsequent runs load from local cache and are much faster.

### 4. Start the Application

Start both the FastAPI backend and the React frontend concurrently with a single command:

```bash
cd frontend
npm install
npm run dev
```

- The React application will be available at **http://127.0.0.1:5173**
- The FastAPI backend will be running at **http://127.0.0.1:8000**
- The Vite dev server automatically proxies `/api` requests to the backend.

---

## AI Models Used

| Feature            | Model                          | Library              |
|--------------------|--------------------------------|----------------------|
| Speech-to-Text     | `openai/whisper-base`          | `openai-whisper`     |
| Summarization      | `facebook/bart-large-cnn`      | `transformers`       |
| Keyword Extraction | `all-MiniLM-L6-v2` (KeyBERT)  | `keybert`            |
| Topic Segmentation | `all-MiniLM-L6-v2`             | `sentence-transformers` |
| Quiz & Flashcards  | `google/flan-t5-base`          | `transformers`       |
| WER Metric         | --                             | `jiwer`              |
| ROUGE Metric       | --                             | `rouge-score`        |
| PDF Export         | --                             | `reportlab`          |

---

## Application Flow

```
Upload MP3/WAV
     |
     v
1. ASR (Whisper)       -> Full Transcript + Timestamps
     |
     v
2. NLP Cleaning        -> Remove filler words
     |
     v
3. Keyword Extraction  -> Top 10 keyphrases (KeyBERT)
     |
     v
4. Topic Segmentation  -> Semantic sections (SentenceTransformers)
     |
     v
5. Summarization       -> Overview + Key Points + Concepts (BART CNN)
     |
     v
6. Quiz Generation     -> 5 MCQs + 3 Short Answers + 5 Flashcards (Flan-T5)
     |
     v
7. Metrics             -> WER + ROUGE-1 + ROUGE-L (jiwer + rouge-score)
     |
     v
Dashboard (6 tabs) + PDF Download
```

---

## Performance Notes

Processing a 1-hour lecture on CPU takes approximately:

| Step         | Estimated Time |
|--------------|----------------|
| Whisper base | 5-15 min       |
| BART         | 2-5 min        |
| Flan-T5      | 1-3 min        |
| KeyBERT      | < 30 sec       |

**For production**: Processing is already handled as a FastAPI BackgroundTask. For heavier load consider adding a Celery worker queue.

---

## API Endpoints

| Endpoint                  | Method | Description              |
|---------------------------|--------|--------------------------|
| `/api/upload`             | POST   | Upload audio file        |
| `/api/status/{job_id}`    | GET    | Poll processing status   |
| `/api/results/{job_id}`   | GET    | Get full results         |
| `/api/export/{job_id}`    | GET    | Download PDF notes       |
