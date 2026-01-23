from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    cors_origins: list[str] = ["http://localhost:3000"]
    debug: bool = False

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
