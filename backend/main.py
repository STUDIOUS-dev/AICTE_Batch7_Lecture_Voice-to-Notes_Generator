import os
import io
import json
import uuid
import logging
from typing import Dict, Any

from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse, Response, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Point to the local ffmpeg.exe bundled in the project root
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_FFMPEG_PATH = os.path.join(_PROJECT_ROOT, "ffmpeg.exe")
if os.path.isfile(_FFMPEG_PATH):
    os.environ["PATH"] = _PROJECT_ROOT + os.pathsep + os.environ["PATH"]

from backend.services.asr import ASRService
from backend.services.nlp_utils import NLPUtils
from backend.services.summarizer import SummarizerService
from backend.services.quiz_gen import QuizService
from backend.services.evaluator import EvaluatorService
from backend.services.pdf_export import PDFExportService

app = FastAPI(title="IntelliLecture API")

# Allow CORS for React frontend (Vite default is 5173)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
JOBS_DIR = os.path.join(DATA_DIR, "jobs")
UPLOADS_DIR = os.path.join(DATA_DIR, "uploads")

for d in [JOBS_DIR, UPLOADS_DIR]:
    os.makedirs(d, exist_ok=True)

# ── Lazy-loaded service singletons ──────────────────────────────────────────
_asr_service = None
_summarizer_service = None
_nlp_utils = None
_quiz_service = None
_evaluator_service = None
_pdf_service = None

def get_asr():
    global _asr_service
    if _asr_service is None:
        _asr_service = ASRService(model_size="base")
    return _asr_service

def get_summarizer():
    global _summarizer_service
    if _summarizer_service is None:
        _summarizer_service = SummarizerService()
    return _summarizer_service

def get_nlp():
    global _nlp_utils
    if _nlp_utils is None:
        _nlp_utils = NLPUtils()
    return _nlp_utils

def get_quiz():
    global _quiz_service
    if _quiz_service is None:
        _quiz_service = QuizService()
    return _quiz_service

def get_evaluator():
    global _evaluator_service
    if _evaluator_service is None:
        _evaluator_service = EvaluatorService()
    return _evaluator_service

def get_pdf():
    global _pdf_service
    if _pdf_service is None:
        _pdf_service = PDFExportService()
    return _pdf_service

def load_job(job_id: str) -> Dict[str, Any]:
    path = os.path.join(JOBS_DIR, f"{job_id}.json")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Job not found")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_job(job_id: str, data: Dict[str, Any]):
    path = os.path.join(JOBS_DIR, f"{job_id}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def process_lecture(job_id: str, file_path: str, filename: str):
    job = load_job(job_id)
    job["status"] = "processing"
    job["step"] = "Transcribing audio"
    save_job(job_id, job)

    try:
        # Step 1: Transcription
        logger.info(f"[{job_id}] Step 1: ASR")
        asr_result = get_asr().transcribe(file_path)
        job["transcript"] = asr_result
        raw_text = asr_result["text"]
        save_job(job_id, job)

        # Step 2: Text Cleaning
        logger.info(f"[{job_id}] Step 2: NLP cleaning")
        job["step"] = "Cleaning text"
        save_job(job_id, job)
        nlp = get_nlp()
        cleaned = nlp.clean_text(raw_text)
        job["cleaned_text"] = cleaned

        # --- TEMPORARILY DISABLED ---
        # # Step 3: Keywords
        # logger.info(f"[{job_id}] Step 3: Keywords")
        # job["step"] = "Extracting keywords"
        # save_job(job_id, job)
        # job["keywords"] = nlp.extract_keywords(cleaned, top_n=10)

        # # Step 4: Segmentation
        # logger.info(f"[{job_id}] Step 4: Segmentation")
        # job["step"] = "Segmenting topics"
        # save_job(job_id, job)
        # job["segments"] = nlp.segment_by_topic(cleaned)
        # ----------------------------

        # Step 5: Summarization
        logger.info(f"[{job_id}] Step 5: Summarization")
        job["step"] = "Generating summary"
        save_job(job_id, job)
        summary = get_summarizer().summarize(cleaned)
        job["summary"] = summary

        # --- TEMPORARILY DISABLED ---
        # # Step 6: Quiz and Flashcards
        # logger.info(f"[{job_id}] Step 6: Quiz + Flashcards")
        # job["step"] = "Generating quiz and flashcards"
        # save_job(job_id, job)
        # quiz_svc = get_quiz()
        # job["quiz"] = quiz_svc.generate_quiz(cleaned)
        # job["flashcards"] = quiz_svc.generate_flashcards(cleaned)

        # # Step 7: Metrics
        # logger.info(f"[{job_id}] Step 7: Metrics")
        # job["step"] = "Calculating metrics"
        # save_job(job_id, job)
        # summary_text = " ".join(summary.get("key_points", []))
        # job["metrics"] = get_evaluator().calculate_metrics(
        #     transcript=cleaned,
        #     summary=summary_text,
        # )
        # ----------------------------

        job["status"] = "done"
        job["step"] = "Complete"
        save_job(job_id, job)
        logger.info(f"[{job_id}] Processing complete")

    except Exception as e:
        import traceback
        full_trace = traceback.format_exc()
        logger.error(f"[{job_id}] Pipeline error: {e}\n{full_trace}")
        job["status"] = "error"
        job["error"] = str(e) + "\n\n" + full_trace
        save_job(job_id, job)

@app.post("/api/upload")
async def upload_audio(background_tasks: BackgroundTasks, audio_file: UploadFile = File(...)):
    if not audio_file.filename:
        raise HTTPException(status_code=400, detail="Filename not provided")
    
    # Save file
    job_id = str(uuid.uuid4())
    ext = os.path.splitext(audio_file.filename)[1]
    file_path = os.path.join(UPLOADS_DIR, f"{job_id}{ext}")
    
    content = await audio_file.read()
    with open(file_path, "wb") as f:
        f.write(content)
        
    job_data = {
        "id": job_id,
        "filename": audio_file.filename,
        "status": "pending",
        "step": "Queued",
        "error": None
    }
    save_job(job_id, job_data)
    
    # Trigger background processing
    background_tasks.add_task(process_lecture, job_id, file_path, audio_file.filename)
    
    return {"job_id": job_id, "status": "pending"}

@app.get("/api/status/{job_id}")
async def get_status(job_id: str):
    job = load_job(job_id)
    return {"status": job.get("status"), "step": job.get("step"), "error": job.get("error")}

@app.get("/api/results/{job_id}")
async def get_results(job_id: str):
    job = load_job(job_id)
    if job.get("status") != "done":
        raise HTTPException(status_code=400, detail="Job not yet complete")
    return job

# --- TEMPORARILY DISABLED ---
# @app.get("/api/export/{job_id}")
# async def export_pdf(job_id: str):
#     job = load_job(job_id)
#     if job.get("status") != "done":
#         raise HTTPException(status_code=400, detail="Job not yet complete")
#         
#     pdf_bytes = get_pdf().generate(job)
#     filename = job.get("filename", "lecture").rsplit(".", 1)[0] + "_notes.pdf"
#     
#     return Response(
#         content=pdf_bytes,
#         media_type="application/pdf",
#         headers={"Content-Disposition": f'attachment; filename="{filename}"'}
#     )
# ----------------------------
