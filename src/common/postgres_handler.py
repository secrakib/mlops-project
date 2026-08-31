import logging
import json
import psycopg2

class PostgresHandler(logging.Handler):
    """
    A custom logging handler that synchronously writes log records 
    into the Supabase `prediction_logs` table.
    Designed to fail-open: if the database is down, it catches the exception 
    so the scoring API request does not crash (500 Error).
    """
    def __init__(self, db_url: str):
        super().__init__()
        self.db_url = db_url

    def emit(self, record):
        try:
            # We expect the message to be a JSON string from python-json-logger
            # or a dict passed directly into logger.info(dict).
            msg = self.format(record)
            
            try:
                data = json.loads(msg)
            except json.JSONDecodeError:
                # If not JSON, we cannot easily unpack it into our strict schema.
                return

            request_id = data.get("request_id", "unknown")
            request_json = data.get("request_json", "{}")
            probability = data.get("probability", -1.0)
            decision = data.get("decision", "UNKNOWN")
            model_version = data.get("model_version", "unknown")
            latency_ms = data.get("latency_ms", 0.0)

            # Ensure request_json is stringified for JSONB insertion if it's a dict
            if isinstance(request_json, dict):
                request_json = json.dumps(request_json)

            conn = psycopg2.connect(self.db_url)
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO prediction_logs 
                    (request_id, request_json, probability, decision, model_version, latency_ms) 
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (request_id, request_json, probability, decision, model_version, latency_ms)
                )
            conn.commit()
            conn.close()

        except Exception as e:
            # Fail-open design: print error to stdout but do not crash thread
            print(f"[PostgresHandler ERROR] Failed to log to Supabase: {e}")
