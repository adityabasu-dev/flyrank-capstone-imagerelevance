from typing import Dict, Any

def evaluate_mismatch_guard(
    post: Dict[str, Any],
    image: Dict[str, Any],
    similarity_score: float,
    threshold: float = 0.72
) -> Dict[str, Any]:
    """
    Evaluates an image against a post to determine if the pairing is safe.
    Returns match status, final score, and detailed rejection explanation.
    """
    
    # Check 1: Low-confidence vision classification
    if image.get("confidence", 0.0) < 0.70:
        return {
            "is_matched": False,
            "score": similarity_score,
            "reason": f"Low confidence classification on image ({image.get('confidence'):.2f})"
        }

    # Check 2: Category Mismatch
    post_cat = (post.get("category") or "").lower().strip()
    img_cat = (image.get("category") or "").lower().strip()
    
    if post_cat and img_cat and post_cat != img_cat:
        return {
            "is_matched": False,
            "score": similarity_score,
            "reason": f"Category mismatch: post expected '{post_cat}', but image detected '{img_cat}'"
        }

    # Check 3: Semantic Cosine Threshold Boundary
    if similarity_score < threshold:
        return {
            "is_matched": False,
            "score": similarity_score,
            "reason": f"Semantic similarity ({similarity_score:.2f}) below safety threshold ({threshold})"
        }

    return {
        "is_matched": True,
        "score": similarity_score,
        "reason": "Match verified by safety guard"
    }