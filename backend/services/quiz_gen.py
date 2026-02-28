"""
Quiz & Flashcard Generation Service using google/flan-t5-base.

Generates:
  - 5 Multiple Choice Questions (MCQs) with difficulty tags
  - 3 Short Answer Questions
  - 5 Flashcard Q/A pairs

As flan-t5 is a generative model, we use prompt engineering to
structure the output; parsing is done with simple heuristics.
"""

import re
import logging

logger = logging.getLogger(__name__)

DIFFICULTY_LABELS = ["Easy", "Medium", "Hard"]


class QuizService:
    """
    Quiz and flashcard generation using google/flan-t5-base.
    """

    def __init__(self, model_name: str = "google/flan-t5-base"):
        from transformers import pipeline  # deferred import
        logger.info(f"Loading quiz generation model: {model_name}")
        self.generator = pipeline("text2text-generation", model=model_name)
        logger.info("Quiz model loaded.")

    def _generate(self, prompt: str, max_length: int = 256) -> str:
        """Run a single generation call and return the text output."""
        result = self.generator(
            prompt,
            max_length=max_length,
            num_beams=4,
            early_stopping=True,
        )
        return result[0]["generated_text"].strip()

    def _assign_difficulty(self, index: int) -> str:
        """Cycle through Easy/Medium/Hard for variety."""
        return DIFFICULTY_LABELS[index % len(DIFFICULTY_LABELS)]

    def generate_quiz(self, text: str) -> dict:
        """
        Generate MCQs and Short Answer Questions from the lecture text.

        Args:
            text: Cleaned lecture transcript (first 1200 chars used for prompting).

        Returns:
            dict with:
                - mcqs (list[dict]): Each has 'question', 'raw_answer', 'difficulty'.
                - short_answers (list[dict]): Each has 'question', 'difficulty'.
        """
        snippet = text[:1200]

        # --- MCQ Generation ---
        mcq_prompt = (
            f"Generate 5 multiple choice questions with 4 options (A, B, C, D) "
            f"and the correct answer labeled. Use this text:\n{snippet}"
        )
        mcq_raw = self._generate(mcq_prompt, max_length=512)
        mcq_lines = [l.strip() for l in mcq_raw.split('\n') if l.strip()]

        mcqs = []
        for i, line in enumerate(mcq_lines[:5]):
            mcqs.append({
                "question": line,
                "difficulty": self._assign_difficulty(i),
            })

        # --- Short Answer Generation ---
        sa_prompt = (
            f"Generate 3 short answer questions (one sentence each) from this text:\n{snippet}"
        )
        sa_raw = self._generate(sa_prompt, max_length=256)
        sa_lines = [l.strip() for l in sa_raw.split('\n') if l.strip()]

        short_answers = []
        for i, line in enumerate(sa_lines[:3]):
            short_answers.append({
                "question": line,
                "difficulty": self._assign_difficulty(i + 1),
            })

        logger.info(f"Generated {len(mcqs)} MCQs and {len(short_answers)} short answers.")
        return {
            "mcqs": mcqs,
            "short_answers": short_answers,
        }

    def generate_flashcards(self, text: str) -> list[dict]:
        """
        Generate 5 flashcard Q/A pairs.

        Args:
            text: Cleaned lecture transcript.

        Returns:
            List of dicts: [{"question": "...", "answer": "..."}]
        """
        snippet = text[:1200]
        prompt = (
            f"Create 5 flashcards in the format 'Q: ... A: ...' "
            f"from this text:\n{snippet}"
        )
        raw = self._generate(prompt, max_length=512)

        # Parse "Q: ... A: ..." pairs
        flashcards = []
        # Try to match Q: ... A: ... pattern
        pattern = re.findall(r'Q[:\.]?\s*(.+?)\s*A[:\.]?\s*(.+?)(?=Q[:\.]?|$)', raw, re.DOTALL | re.IGNORECASE)

        if pattern:
            for q, a in pattern[:5]:
                flashcards.append({"question": q.strip(), "answer": a.strip()})
        else:
            # Fallback: split by newlines and pair them
            lines = [l.strip() for l in raw.split('\n') if l.strip()]
            for i in range(0, min(len(lines) - 1, 10), 2):
                flashcards.append({
                    "question": lines[i],
                    "answer": lines[i + 1] if i + 1 < len(lines) else "—",
                })
                if len(flashcards) >= 5:
                    break

        logger.info(f"Generated {len(flashcards)} flashcards.")
        return flashcards
