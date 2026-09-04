import psycopg2
import logging

logger = logging.getLogger(__name__)

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS prediction_logs (
    id SERIAL PRIMARY KEY,
    ts TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    request_id VARCHAR(50) NOT NULL,
    request_json JSONB NOT NULL,
    probability FLOAT NOT NULL,
    decision VARCHAR(20) NOT NULL,
    model_version VARCHAR(50) NOT NULL
);
"""

def init_db(db_url: str):
    """Initializes the database schema if it does not exist."""
    try:
        logger.info("Initializing Supabase Postgres schema...")
        conn = psycopg2.connect(db_url)
        with conn.cursor() as cursor:
            cursor.execute(CREATE_TABLE_SQL)
        conn.commit()
        conn.close()
        logger.info("Schema initialization successful.")
    except Exception as e:
        logger.error(f"Failed to initialize database schema: {e}")
        # We don't raise the error to allow fail-open.
