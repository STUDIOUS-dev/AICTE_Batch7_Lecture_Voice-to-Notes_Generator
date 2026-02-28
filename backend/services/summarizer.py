"""
Summarizer Service — Text summarization using facebook/bart-large-cnn.

Handles long texts by chunking them intelligently before passing
to the transformer pipeline, then stitching the summaries together
into a structured output.
"""

import logging

logger = logging.getLogger(__name__)

# Max characters per chunk for BART (approx 1024 tokens ≈ 800 chars)
MAX_CHUNK_CHARS = 800


class SummarizerService:
    """
    Summarization using facebook/bart-large-cnn (pretrained, no fine-tuning needed).
    """

    def __init__(self, model_name: str = "facebook/bart-large-cnn"):
        from transformers import pipeline  # deferred import
        logger.info(f"Loading summarization model: {model_name}")
        self.summarizer = pipeline(
            "summarization",
            model=model_name,
        )
        logger.info("Summarization model loaded.")

    def _chunk_text(self, text: str) -> list[str]:
        """Split text into chunks that fit within the model's token limit."""
        words = text.split()
        chunks = []
        current_chunk = []
        current_len = 0

        for word in words:
            current_chunk.append(word)
            current_len += len(word) + 1
            if current_len >= MAX_CHUNK_CHARS:
                chunks.append(" ".join(current_chunk))
                current_chunk = []
                current_len = 0

        if current_chunk:
            chunks.append(" ".join(current_chunk))

        return chunks

    def summarize(self, text: str) -> dict:
        """
        Summarize the lecture transcript.

        Returns a structured dict:
            - overview (str): High-level 2-3 sentence summary.
            - key_points (list[str]): Bullet-level important sentences.
            - important_concepts (list[str]): Shorter conceptual phrases.
        """
        if not text or len(text.strip()) < 50:
            return {
                "overview": "Text too short to summarize.",
                "key_points": [],
                "important_concepts": [],
            }

        logger.info("Starting summarization...")
        chunks = self._chunk_text(text)
        logger.info(f"Text split into {len(chunks)} chunks.")

        summaries = self.summarizer(
            chunks,
            max_length=150,
            min_length=40,
            do_sample=False,
            truncation=True,
        )

        # Stitch chunked summaries into one body
        full_summary = " ".join(s["summary_text"] for s in summaries)

        # Parse into structure
        sentences = [s.strip() for s in full_summary.split(".") if s.strip()]

        overview = ". ".join(sentences[:3]) + "." if sentences else full_summary
        key_points = sentences  # All sentences as bullet points
        important_concepts = [
            s for s in sentences if len(s.split()) <= 8
        ]  # Short phrases = concepts

        logger.info("Summarization complete.")
        return {
            "overview": overview,
            "key_points": key_points,
            "important_concepts": important_concepts,
        }
