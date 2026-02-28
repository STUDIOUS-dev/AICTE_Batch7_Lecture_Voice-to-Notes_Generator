"""
Evaluator Service — WER and ROUGE metric computation.

Uses:
  - jiwer for Word Error Rate (ASR quality)
  - rouge_score for ROUGE-1 and ROUGE-L (summarization quality)
"""

import logging

logger = logging.getLogger(__name__)


class EvaluatorService:
    """
    Computes evaluation metrics for transcription and summarization quality.
    """

    def calculate_wer(self, reference: str, hypothesis: str) -> float:
        """
        Calculate Word Error Rate between reference and hypothesis transcripts.

        Lower WER = better transcription quality.
        WER of 0.0 = perfect match.

        Args:
            reference: Ground-truth reference transcript.
            hypothesis: Model-generated transcript.

        Returns:
            WER as a float rounded to 4 decimal places.
        """
        if not reference or not hypothesis:
            return 0.0
        from jiwer import wer  # deferred import
        error_rate = wer(reference.lower().strip(), hypothesis.lower().strip())
        return round(error_rate, 4)

    def calculate_rouge(self, reference: str, hypothesis: str) -> dict:
        """
        Calculate ROUGE-1 and ROUGE-L F1 scores.

        Higher ROUGE = better summarization quality.

        Args:
            reference: Original source text (transcript).
            hypothesis: Generated summary.

        Returns:
            dict with 'rouge1' and 'rougeL' F1 scores.
        """
        if not reference or not hypothesis:
            return {"rouge1": 0.0, "rougeL": 0.0}

        from rouge_score import rouge_scorer  # deferred import
        scorer = rouge_scorer.RougeScorer(['rouge1', 'rougeL'], use_stemmer=True)
        scores = scorer.score(reference, hypothesis)

        return {
            "rouge1": round(scores['rouge1'].fmeasure, 4),
            "rougeL": round(scores['rougeL'].fmeasure, 4),
        }

    def calculate_metrics(self, transcript: str, summary: str, reference_transcript: str = None) -> dict:
        """
        Compute all evaluation metrics in one call.

        Args:
            transcript: The ASR-generated transcript.
            summary: The generated summary text.
            reference_transcript: Optional ground-truth transcript for WER.

        Returns:
            dict with 'wer', 'rouge1', 'rougeL'.
        """
        metrics = {}

        # WER: only meaningful if a reference is provided
        if reference_transcript:
            metrics["wer"] = self.calculate_wer(reference_transcript, transcript)
        else:
            metrics["wer"] = None  # Not computable without ground truth

        # ROUGE: compare original transcript vs summary
        rouge = self.calculate_rouge(transcript, summary)
        metrics.update(rouge)

        logger.info(f"Evaluation metrics: {metrics}")
        return metrics
