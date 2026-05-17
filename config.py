# ── Blogging Platform API — config ───────────────────────────────────
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL:   str = "sqlite+aiosqlite:///./data/blog.db"
    SECRET_KEY:     str = "roadmap-blog-api-dev-secret-change-in-production"

settings = Settings()
