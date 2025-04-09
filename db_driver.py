# db_driver.py
import sqlite3
from typing import Optional
from dataclasses import dataclass
from contextlib import contextmanager


@dataclass
class PatientProfile:
    id_number: str
    mobile_number: str
    name: str


class DatabaseDriver:
    def __init__(self, db_path: str = "hospital_db.sqlite"):
        self.db_path = db_path
        self._init_db()

    @contextmanager
    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
        finally:
            conn.close()

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS user_profile (
                    id_number TEXT PRIMARY KEY,
                    mobile_number TEXT NOT NULL,
                    name TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def create_profile(
        self, id_number: str, mobile_number: str, name: str
    ) -> Optional[PatientProfile]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO user_profile (id_number, mobile_number, name) VALUES (?, ?, ?)",
                    (id_number, mobile_number, name),
                )
                conn.commit()
                return PatientProfile(
                    id_number=id_number, mobile_number=mobile_number, name=name
                )
        except sqlite3.IntegrityError:
            return None

    def get_profile_by_id(self, id_number: str) -> Optional[PatientProfile]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM user_profile WHERE id_number = ?", (id_number,)
            )
            row = cursor.fetchone()
            if not row:
                return None
            return PatientProfile(id_number=row[0], mobile_number=row[1], name=row[2])
