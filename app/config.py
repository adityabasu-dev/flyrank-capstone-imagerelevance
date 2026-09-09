from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "FlyRank Image Matching Engine"
    DATABASE_URL: str = "sqlite:///./app.db"
    GEMINI_API_KEY: str = "your_gemini_api_key_here"
    
    class Config:
        env_file = ".env"

settings = Settings()