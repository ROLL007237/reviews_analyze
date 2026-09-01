import json
import logging
import re

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

PROMPT_TEMPLATE = """You are a review analysis engine. Analyze the following customer review
and respond ONLY with a valid JSON object (no markdown, no extra text) with exactly these keys:

- "sentiment": one of "positive", "negative", "neutral"
- "score": a float between -1.0 (very negative) and 1.0 (very positive)
- "summary": a one-sentence summary of the review
- "topics": a list of up to 3 short topic keywords mentioned in the review

Review:
\"\"\"{review_text}\"\"\"

JSON:"""


def _extract_json(raw_text: str) -> dict:
    """Ollama models sometimes wrap JSON in markdown fences or add stray text."""
    match = re.search(r"\{.*\}", raw_text, re.DOTALL)
    if not match:
        raise ValueError(f"No JSON object found in model output: {raw_text!r}")
    return json.loads(match.group(0))


async def analyze_review(text: str, max_retries: int = 3) -> dict:
    prompt = PROMPT_TEMPLATE.format(review_text=text)

    last_error: Exception | None = None
    async with httpx.AsyncClient(timeout=60.0) as client:
        for attempt in range(1, max_retries + 1):
            try:
                response = await client.post(
                    f"{settings.OLLAMA_URL}/api/generate",
                    json={
                        "model": settings.OLLAMA_MODEL,
                        "prompt": prompt,
                        "stream": False,
                        "options": {"temperature": 0.2},
                    },
                )
                response.raise_for_status()
                raw_output = response.json()["response"]
                parsed = _extract_json(raw_output)

                sentiment = str(parsed.get("sentiment", "neutral")).lower()
                if sentiment not in ("positive", "negative", "neutral"):
                    sentiment = "neutral"

                score = float(parsed.get("score", 0.0))
                score = max(-1.0, min(1.0, score))

                topics = parsed.get("topics", [])
                if isinstance(topics, list):
                    topics_str = ", ".join(str(t) for t in topics[:3])
                else:
                    topics_str = str(topics)

                return {
                    "sentiment": sentiment,
                    "score": score,
                    "summary": str(parsed.get("summary", ""))[:500],
                    "topics": topics_str,
                }
            except Exception as exc:  # noqa: BLE001 - broad on purpose, we retry/fallback
                last_error = exc
                logger.warning("Ollama analyze attempt %s/%s failed: %s", attempt, max_retries, exc)

    logger.error("Ollama analysis failed after %s attempts: %s", max_retries, last_error)
    # Fallback so the pipeline never gets stuck on a bad/unavailable model response
    return {
        "sentiment": "neutral",
        "score": 0.0,
        "summary": "Analysis unavailable.",
        "topics": "",
    }
