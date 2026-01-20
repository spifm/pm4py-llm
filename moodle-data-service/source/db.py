import os
import psycopg2
import logging
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class MoodleDatabase:
    """
    Manage Moodle (PostgreSQL) database connection and configuration.
    """

    def __init__(self, host: str, port: int, user: str, password: str, dbname: str, table_prefix: str = "mdl_"):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.dbname = dbname
        self.table_prefix = table_prefix

    @classmethod
    def from_env(cls) -> "MoodleDatabase":
        """Create an instance by reading from environment variables."""
        host = os.getenv("MOODLE_DB_HOST")
        port = int(os.getenv("MOODLE_DB_PORT", "5432"))
        user = os.getenv("MOODLE_DB_USER")
        password = os.getenv("MOODLE_DB_PASSWORD")
        dbname = os.getenv("MOODLE_DB_NAME")
        table_prefix = os.getenv("MOODLE_DB_PREFIX", "mdl_")

        if not all([host, user, password, dbname]):
            raise RuntimeError("Moodle DB config is incomplete. Check MOODLE_DB_* env vars.")

        return cls(host=host, port=port, user=user, password=password, dbname=dbname, table_prefix=table_prefix)

    @contextmanager
    def get_connection(self):
        """Context manager to get and close connection. Enables using with 'with' statement."""
        conn = None
        try:
            conn = psycopg2.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                dbname=self.dbname,
            )
            yield conn
        finally:
            if conn is not None:
                conn.close()
