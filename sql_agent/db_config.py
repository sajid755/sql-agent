import os
import psycopg2
from psycopg2 import OperationalError
from dotenv import load_dotenv
import time

load_dotenv()


required = ["DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD"]
missing = [var for var in required if not os.getenv(var)]
if missing:
    raise RuntimeError(f"Missing required DB env vars: {', '.join(missing)}")


DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT"),
    "database": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD")
}


def get_connection():
    """
    Return a new psycopg2 connection using the credentials from .env.
    Raises OperationalError with a clear message if the connection fails.
    """
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        conn.autocommit = True   # useful for quick SELECTs; adjust as needed
        return conn
    except OperationalError as exc:
        raise OperationalError(
            f"Failed to connect to PostgreSQL at {DB_CONFIG['host']}:{DB_CONFIG['port']}"
            f"/{DB_CONFIG['database']}. Check credentials and network access."
        ) from exc