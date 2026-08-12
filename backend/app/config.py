from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://anchor_user:anchor_pass@localhost:5432/anchor_db"
    # Primary key name used by docker-compose and deployment.
    groq_api_key: str = ""
    # Legacy alias kept for backwards compatibility with older .env files.
    huggingface_api_key: str = ""
    environment: str = "development"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
