from pydantic import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Event Planner"

    class Config:
        env_file = ".env"