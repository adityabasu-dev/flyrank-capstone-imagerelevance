import logging
from sqlmodel import Session, select
from app.database import engine
from app.models import Image, BatchStatus, AICostLog
from app.services.vision_service import analyze_image_file
from app.services.embedding_service import generate_text_embedding

logger = logging.getLogger("batch_processor")

def process_pending_images_batch():
    with Session(engine) as session:
        statement = select(Image).where(Image.status == BatchStatus.PENDING)
        pending_images = session.exec(statement).all()

        for image in pending_images:
            image.status = BatchStatus.PROCESSING
            session.add(image)
            session.commit()

            try:
                # 1. Vision Tagging via Gemini 2.5 Flash
                result = analyze_image_file(image.file_path)
                meta = result["metadata"]

                image.subject = meta.subject
                image.category = meta.category
                image.attributes = meta.attributes
                image.caption = meta.caption
                image.confidence = meta.confidence
                image.flagged = result["flagged"]

                # 2. Embedding Generation for Image Caption
                caption_text = f"{meta.subject} - {meta.category}: {meta.caption}"
                embed_res = generate_text_embedding(caption_text)
                image.embedding = embed_res["embedding"]
                image.status = BatchStatus.COMPLETED

                # 3. Log AI Costs
                v_cost = AICostLog(
                    operation="VISION_TAGGING",
                    model_name="gemini-2.5-flash",
                    prompt_tokens=result["prompt_tokens"],
                    completion_tokens=result["completion_tokens"],
                    cost_usd=result["cost_usd"]
                )
                e_cost = AICostLog(
                    operation="TEXT_EMBEDDING",
                    model_name="text-embedding-004",
                    prompt_tokens=embed_res["prompt_tokens"],
                    completion_tokens=0,
                    cost_usd=embed_res["cost_usd"]
                )

                session.add(image)
                session.add(v_cost)
                session.add(e_cost)
                session.commit()
                logger.info(f"Successfully processed image ID {image.id}: {meta.subject}")

            except Exception as e:
                logger.error(f"Failed to process image ID {image.id}: {str(e)}")
                image.status = BatchStatus.FAILED
                session.add(image)
                session.commit()