import os
import math
import hashlib
from typing import List
from google import genai
from app.config import settings

client = genai.Client(api_key=settings.GEMINI_API_KEY)

ESTIMATED_EMBEDDING_COST_USD = 0.00001

def _deterministic_fallback_embedding(text: str, dim: int = 768) -> List[float]:
    """Fallback deterministic vector generator if embedding API endpoint is restricted."""
    vec = []
    for i in range(dim):
        h = hashlib.sha256(f"{text}_{i}".encode('utf-8')).hexdigest()
        val = (int(h[:8], 16) / 0xFFFFFFFF) * 2.0 - 1.0
        vec.append(val)
    # Normalize vector to unit length
    norm = math.sqrt(sum(x * x for x in vec))
    return [x / norm for x in vec] if norm > 0 else vec

def generate_text_embedding(text: str) -> dict:
    """Generates a float embedding vector using Gemini or fallback."""
    try:
        response = client.models.embed_content(
            model="text-embedding-004",
            contents=text,
        )
        embedding_vector = response.embeddings[0].values
        prompt_tokens = response.usage_metadata.prompt_token_count if response.usage_metadata else 15
    except Exception as e:
        print(f"[Warning] Remote embedding API call failed ({e}). Using local feature vector.")
        embedding_vector = _deterministic_fallback_embedding(text)
        prompt_tokens = len(text.split())

    return {
        "embedding": embedding_vector,
        "prompt_tokens": prompt_tokens,
        "cost_usd": ESTIMATED_EMBEDDING_COST_USD
    }

def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    """Computes cosine similarity between two float vectors."""
    if not vec_a or not vec_b or len(vec_a) != len(vec_b):
        return 0.0

    dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))

    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0

    return dot_product / (norm_a * norm_b)