from sqlmodel import Session, select
from app.database import engine, init_db
from app.models import Post, AICostLog
from app.services.embedding_service import generate_text_embedding

SAMPLE_POSTS = [
    {
        "title": "The Secrets of Red Foxes in the Wild",
        "category": "animal",
        "content": "Red foxes (Vulpes vulpes) are adaptable opportunistic predators found across forest landscapes with orange fur and bushy tails."
    },
    {
        "title": "Gray Wolves: Kings of the Forest Pack",
        "category": "animal",
        "content": "Gray wolves are large wild apex predators that hunt in organized packs across timberland territories."
    },
    {
        "title": "Modern Aviation and Jet Engines",
        "category": "vehicle",
        "content": "Commercial airliners soar through high altitude clouds using advanced turbofan engines."
    }
]

def seed_posts():
    init_db()
    with Session(engine) as session:
        for p_data in SAMPLE_POSTS:
            existing = session.exec(select(Post).where(Post.title == p_data["title"])).first()
            if not existing:
                full_text = f"{p_data['title']} {p_data['category']} {p_data['content']}"
                embed_res = generate_text_embedding(full_text)
                
                post = Post(
                    title=p_data["title"],
                    category=p_data["category"],
                    content=p_data["content"],
                    embedding=embed_res["embedding"]
                )
                cost = AICostLog(
                    operation="POST_EMBEDDING",
                    model_name="text-embedding-004",
                    prompt_tokens=embed_res["prompt_tokens"],
                    completion_tokens=0,
                    cost_usd=embed_res["cost_usd"]
                )
                session.add(post)
                session.add(cost)
                print(f"Seeded post: {p_data['title']}")
        session.commit()

if __name__ == "__main__":
    seed_posts()