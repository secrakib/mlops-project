import os
import sys
import psycopg2
from dotenv import load_dotenv


def check_database():
    load_dotenv()

    db_url = os.getenv("DATABASE_URL")

    if not db_url:
        print("[ERROR] DATABASE_URL not found in .env file.")
        sys.exit(1)

    print("[INFO] Attempting to connect to database...")

    try:
        conn = psycopg2.connect(db_url)

        with conn.cursor() as cursor:
            cursor.execute("SELECT 1;")
            result = cursor.fetchone()

        conn.close()

        if result and result[0] == 1:
            print("[SUCCESS] Database connection established successfully!")
            print("[SUCCESS] Database health check passed.")
            sys.exit(0)

        print("[ERROR] Database returned unexpected result.")
        sys.exit(1)

    except Exception as e:
        print("[FAIL] Connection failed!")
        print(f"[FAIL] Error details: {e}")
        sys.exit(1)


if __name__ == "__main__":
    check_database()