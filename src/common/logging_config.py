import logging
from pythonjsonlogger import jsonlogger
from src.common.postgres_handler import PostgresHandler
import contextvars

# We use this ContextVar to store the request_id injected by the FastAPI middleware.
request_id_var = contextvars.ContextVar("request_id", default="SYSTEM")

class RequestIdFilter(logging.Filter):
    """Injects the current request_id from ContextVar into the log record."""
    def filter(self, record):
        record.request_id = request_id_var.get()
        return True

def setup_prediction_logger(db_url: str) -> logging.Logger:
    """
    Configures the central 'prediction_logger' with two handlers:
    1. StreamHandler -> stdout (JSON)
    2. PostgresHandler -> Supabase DB
    """
    logger = logging.getLogger("prediction_logger")
    logger.setLevel(logging.INFO)
    
    # Avoid duplicate logs if setup is called multiple times
    if logger.handlers:
        return logger

    # 1. StreamHandler (stdout JSON for operation traces on Render)
    stream_handler = logging.StreamHandler()
    json_formatter = jsonlogger.JsonFormatter(
        '%(asctime)s %(levelname)s %(name)s %(request_id)s %(message)s'
    )
    stream_handler.setFormatter(json_formatter)
    stream_handler.addFilter(RequestIdFilter())

    # 2. PostgresHandler (Database inserts for Drift Monitoring)
    postgres_handler = PostgresHandler(db_url=db_url)
    postgres_handler.setFormatter(json_formatter)
    postgres_handler.addFilter(RequestIdFilter())

    logger.addHandler(stream_handler)
    logger.addHandler(postgres_handler)
    
    return logger
