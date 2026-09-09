import os
from sqlmodel import Session, select
from app.database import engine, init_db
from app.models import Image, BatchStatus

CORPUS_DIR = "./corpus"

def seed_images():
    init_db()
    if not os.path.exists(CORPUS_DIR):
        os.makedirs(CORPUS_DIR)
        print(f"Directory '{CORPUS_DIR}' created. Add test images here.")
        return

    files = [f for f in os.listdir(CORPUS_DIR) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))]
    
    with Session(engine) as session:
        added = 0
        for filename in files:
            file_path = os.path.join(CORPUS_DIR, filename)
            existing = session.exec(select(Image).where(Image.file_path == file_path)).first()
            if not existing:
                img = Image(filename=filename, file_path=file_path, status=BatchStatus.PENDING)
                session.add(img)
                added += 1
        session.commit()
        print(f"Seeded {added} images as PENDING.")

if __name__ == "__main__":
    seed_images()