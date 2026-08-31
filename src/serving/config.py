import yaml
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    DAGSHUB_USER: str
    DAGSHUB_REPO: str
    DAGSHUB_TOKEN: str
    ALLOWED_ORIGINS: str = "*"
    MODEL_ALIAS: str = "Staging"

    @property
    def mlflow_tracking_uri(self) -> str:
        # Construct MLflow Tracking URI for DagsHub dynamically
        return f"https://dagshub.com/{self.DAGSHUB_USER}/{self.DAGSHUB_REPO}.mlflow"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        # We allow extra env vars (like POSTGRES_USER) without throwing an error
        extra = "ignore"

settings = Settings()

def load_serving_config(path: str = "config/serving_config.yaml") -> dict:
    """Loads static serving metadata (e.g. model name)"""
    with open(path, "r") as f:
        return yaml.safe_load(f)

def load_training_config(path: str = "config/training_config.yaml") -> dict:
    """Loads training parameters including required features and cost matrix"""
    with open(path, "r") as f:
        return yaml.safe_load(f)
