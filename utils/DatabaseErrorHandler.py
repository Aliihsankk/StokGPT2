import sqlite3
from typing import Optional

class DatabaseErrorHandler:
    @staticmethod
    def check_table_exists(cursor: sqlite3.Cursor, table_name: str) -> bool:
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name=?
        """, (table_name,))
        return cursor.fetchone() is not None

    @staticmethod
    def check_column_exists(cursor: sqlite3.Cursor, table_name: str, column_name: str) -> bool:
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        return any(column[1] == column_name for column in columns)

    @staticmethod
    def validate_query(cursor: sqlite3.Cursor, query: str) -> Optional[str]:
        try:
            cursor.execute("EXPLAIN QUERY PLAN " + query)
            return None
        except sqlite3.Error as e:
            return str(e)
