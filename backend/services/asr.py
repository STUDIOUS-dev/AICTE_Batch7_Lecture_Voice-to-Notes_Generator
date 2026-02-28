"""
ASR Service — Speech-to-Text using OpenAI Whisper.

Loads the Whisper model once and exposes a `transcribe()` method
that returns both the full text and per-segment timestamps.
"""

import logging
import os

# Point to the local ffmpeg.exe bundled in the project root
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
_FFMPEG_PATH = os.path.join(_PROJECT_ROOT, "ffmpeg.exe")
if os.path.isfile(_FFMPEG_PATH):
    os.environ["PATH"] = _PROJECT_ROOT + os.pathsep + os.environ["PATH"]

logger = logging.getLogger(__name__)


class ASRService:
    """
    Automatic Speech Recognition using OpenAI Whisper.
    
    Supported model sizes: tiny, base, small, medium, large
    Larger models are more accurate but slower.
    For internship demo: 'base' is a good balance.
    """

    def __init__(self, model_size: str = "base"):
        import whisper  # deferred import — only needed when ASRService is first used
        logger.info(f"Loading Whisper model: {model_size}")
        self.model = whisper.load_model(model_size)
        logger.info("Whisper model loaded successfully.")

    def transcribe(self, audio_path: str) -> dict:
        """
        Transcribe an audio file to text.

        Args:
            audio_path: Absolute path to the audio file (mp3/wav).

        Returns:
            dict with:
                - text (str): Full concatenated transcript.
                - segments (list): Each segment has 'start', 'end', 'text'.
        """
        logger.info(f"Transcribing audio: {audio_path}")
        result = self.model.transcribe(audio_path, verbose=False)

        # Format segments for clean display
        segments = [
            {
                "start": round(seg["start"], 2),
                "end": round(seg["end"], 2),
                "text": seg["text"].strip(),
            }
            for seg in result.get("segments", [])
        ]

        logger.info(f"Transcription complete. {len(segments)} segments found.")
        return {
            "text": result["text"].strip(),
            "segments": segments,
        }
