from database.db import get_connection


def add_pending_deletion(drive_file_id, file_name):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO pending_drive_deletions (drive_file_id, file_name)
                VALUES (%s, %s)
            """, (drive_file_id, file_name))


def list_pending_deletions():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT *
                FROM pending_drive_deletions
                ORDER BY created_at ASC
            """)
            return cur.fetchall()


def remove_pending_deletion(entry_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                DELETE FROM pending_drive_deletions
                WHERE id = %s
            """, (entry_id,))
