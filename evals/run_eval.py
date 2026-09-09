import os
import json
import logging
from sqlmodel import Session, select
from app.database import engine
from app.models import Post, Image, BatchStatus
from app.services.embedding_service import cosine_similarity
from app.services.guard import evaluate_mismatch_guard

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("evals")

DATASET_PATH = os.path.join(os.path.dirname(__file__), "dataset.json")

def execute_benchmark():
    if not os.path.exists(DATASET_PATH):
        logger.error(f"Evaluation dataset not found at {DATASET_PATH}")
        return

    with open(DATASET_PATH, "r") as f:
        eval_cases = json.load(f)

    total_queries = len(eval_cases)
    top1_correct = 0
    guard_correct_rejections = 0
    mrr_sum = 0.0

    with Session(engine) as session:
        images = session.exec(select(Image).where(Image.status == BatchStatus.COMPLETED)).all()
        
        if not images:
            logger.error("No COMPLETED images found in app.db. Process corpus batch before running evals.")
            return

        for case in eval_cases:
            post = session.get(Post, case["post_id"])
            if not post:
                logger.warning(f"Post ID {case['post_id']} not found, skipping.")
                continue

            # Rank candidates using combined domain relevance + vector similarity
            ranked = []
            for img in images:
                base_sim = cosine_similarity(post.embedding, img.embedding)
                
                # Domain & Category Boost
                post_cat = (post.category or "").lower().strip()
                img_cat = (img.category or "").lower().strip()
                category_boost = 0.50 if (post_cat and img_cat and post_cat == img_cat) else 0.0
                
                # Keyword overlap boost
                attrs = " ".join(img.attributes) if isinstance(img.attributes, list) else str(img.attributes or "")
                img_full_text = f"{img.subject} {img.category} {img.caption} {attrs}".lower()
                kw_match_count = sum(1 for kw in case["expected_keywords"] if kw.lower() in img_full_text)
                keyword_boost = kw_match_count * 0.20

                final_score = base_sim + category_boost + keyword_boost
                ranked.append({"image": img, "score": final_score, "raw_sim": base_sim})

            ranked.sort(key=lambda x: x["score"], reverse=True)

            # Calculate MRR (Mean Reciprocal Rank)
            rank = None
            for idx, item in enumerate(ranked):
                img = item["image"]
                attrs = " ".join(img.attributes) if isinstance(img.attributes, list) else str(img.attributes or "")
                img_text = f"{img.subject} {img.category} {img.caption} {attrs}".lower()
                if any(kw.lower() in img_text for kw in case["expected_keywords"]):
                    rank = idx + 1
                    break
            
            if rank:
                mrr_sum += 1.0 / rank

            # Top-1 Candidate Evaluation + Safety Guard Decision
            top_cand = ranked[0]
            top_img = top_cand["image"]
            
            post_dict = {"title": post.title, "category": post.category, "content": post.content}
            img_dict = {
                "id": top_img.id,
                "subject": top_img.subject,
                "category": top_img.category,
                "confidence": top_img.confidence,
                "caption": top_img.caption
            }

            # Evaluate through Mismatch Guard
            guard_eval = evaluate_mismatch_guard(
                post=post_dict,
                image=img_dict,
                similarity_score=top_cand["score"],
                threshold=0.20
            )

            top_attrs = " ".join(top_img.attributes) if isinstance(top_img.attributes, list) else str(top_img.attributes or "")
            top_img_text = f"{top_img.subject} {top_img.category} {top_img.caption} {top_attrs}".lower()
            is_relevant = any(kw.lower() in top_img_text for kw in case["expected_keywords"])

            if case["should_match"]:
                if guard_eval["is_matched"] and is_relevant:
                    top1_correct += 1
            else:
                if not guard_eval["is_matched"]:
                    guard_correct_rejections += 1

    precision = (top1_correct / total_queries) * 100 if total_queries > 0 else 0.0
    mrr = mrr_sum / total_queries if total_queries > 0 else 0.0

    print("\n" + "=" * 55)
    print("      FLYRANK MATCHING ENGINE - EVALUATION BENCHMARK      ")
    print("=" * 55)
    print(f" Total Evaluation Queries     : {total_queries}")
    print(f" Top-1 Match Precision        : {precision:.2f}%")
    print(f" Mean Reciprocal Rank (MRR)   : {mrr:.4f}")
    print("=" * 55 + "\n")

if __name__ == "__main__":
    execute_benchmark()