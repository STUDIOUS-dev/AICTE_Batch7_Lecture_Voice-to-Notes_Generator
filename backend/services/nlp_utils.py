"""
NLP Utilities — Text cleaning, keyword extraction, and topic segmentation.

Uses:
  - Regex for filler word removal
  - KeyBERT for keyword extraction
  - SentenceTransformers + cosine similarity for topic segmentation
"""

import re
import logging

logger = logging.getLogger(__name__)

# Filler words common in spoken lectures
FILLER_PATTERN = re.compile(
    r'\b(uh+|um+|basically|you know|actually|like|right|okay|so|well|i mean|kind of|sort of)\b',
    flags=re.IGNORECASE
)

# Threshold below which a new topic segment is declared
TOPIC_SIMILARITY_THRESHOLD = 0.40


class NLPUtils:
    """
    NLP helper class for cleaning, keyword extraction, and topic segmentation.
    """

    def __init__(self):
        from keybert import KeyBERT  # deferred import
        from sentence_transformers import SentenceTransformer  # deferred import
        logger.info("Loading KeyBERT and SentenceTransformer models...")
        self.kw_model = KeyBERT()  # Internally uses 'paraphrase-MiniLM-L6-v2'
        self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
        logger.info("NLP models loaded.")

    def clean_text(self, text: str) -> str:
        """
        Remove filler words and normalize whitespace.

        Args:
            text: Raw transcript text.

        Returns:
            Cleaned text string.
        """
        cleaned = FILLER_PATTERN.sub('', text)
        # Collapse multiple spaces
        cleaned = re.sub(r' {2,}', ' ', cleaned)
        return cleaned.strip()

    def extract_keywords(self, text: str, top_n: int = 10) -> list[str]:
        """
        Extract the top N important keywords/keyphrases using KeyBERT.

        Args:
            text: Cleaned transcript text.
            top_n: Number of keywords to extract.

        Returns:
            List of keyword strings.
        """
        if not text or len(text.strip()) < 20:
            return []

        logger.info(f"Extracting top {top_n} keywords...")
        keywords = self.kw_model.extract_keywords(
            text,
            keyphrase_ngram_range=(1, 2),
            stop_words='english',
            top_n=top_n,
            use_maxsum=True,
            nr_candidates=20,
        )
        return [kw[0] for kw in keywords]

    def segment_by_topic(self, text: str) -> list[dict]:
        """
        Segment the lecture transcript into topically coherent sections
        using embedding cosine-similarity between consecutive sentences.

        Args:
            text: Cleaned transcript text.

        Returns:
            List of dicts: [{"title": "Topic N", "content": "..."}]
        """
        sentences = [s.strip() for s in text.split('. ') if s.strip()]
        if not sentences:
            return [{"title": "Topic 1", "content": text}]

        logger.info(f"Segmenting {len(sentences)} sentences by topic...")

        segments = []
        current_segment = [sentences[0]]

        for i in range(1, len(sentences)):
            emb_prev = self.embedder.encode(sentences[i - 1], convert_to_tensor=True)
            emb_curr = self.embedder.encode(sentences[i], convert_to_tensor=True)
            from sentence_transformers import util as st_util
            similarity = float(st_util.cos_sim(emb_prev, emb_curr))

            if similarity < TOPIC_SIMILARITY_THRESHOLD:
                # Topic shift detected — close current segment
                segments.append(" ".join(current_segment))
                current_segment = [sentences[i]]
            else:
                current_segment.append(sentences[i])

        # Append the last segment
        segments.append(" ".join(current_segment))

        logger.info(f"Found {len(segments)} topic segments.")
        return [
            {"title": f"Topic {i + 1}", "content": seg}
            for i, seg in enumerate(segments)
        ]
