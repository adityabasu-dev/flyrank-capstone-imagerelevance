from fastapi import FastAPI, BackgroundTasks, Depends, status
from sqlmodel import Session, select
from typing import List
from app.database import init_db, get_session
from app.models import Image, BatchStatus, AICostLog
from app.schemas import BatchIngestResponse, ImageProcessResult
from app.services.batch_processor import process_pending_images_batch

app = FastAPI(title="FlyRank Image Matching Engine")

@app.on_event("startup")
def on_startup():
    init_db()

@app.post("/api/v1/images/batch", response_model=BatchIngestResponse, status_code=status.HTTP_202_ACCEPTED)
def trigger_batch_processing(
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session)
):
    pending = session.exec(
        select(Image).where(Image.status == BatchStatus.PENDING)
    ).all()

    if not pending:
        return BatchIngestResponse(message="No pending images to process", total_queued=0)

    background_tasks.add_task(process_pending_images_batch)
    return BatchIngestResponse(
        message="Batch processing started in background",
        total_queued=len(pending)
    )

@app.get("/api/v1/images", response_model=List[ImageProcessResult])
def list_images(session: Session = Depends(get_session)):
    return session.exec(select(Image)).all()

@app.get("/api/v1/costs")
def get_total_costs(session: Session = Depends(get_session)):
    logs = session.exec(select(AICostLog)).all()
    total_cost = sum(log.cost_usd for log in logs)
    return {"total_calls": len(logs), "total_cost_usd": round(total_cost, 6), "logs": logs}