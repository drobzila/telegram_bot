import json
from database.db import get_connection

def get_state(telegram_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT state
                FROM users
                WHERE telegram_id = %s
            """, (telegram_id,))
            row = cur.fetchone()

            if row is None:
                return "IDLE"
            
            return row["state"] or "IDLE"


def set_state(telegram_id, state):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE users
                SET state = %s
                WHERE telegram_id = %s
            """, (state, telegram_id))


def get_state_data(telegram_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT state_data
                FROM users
                WHERE telegram_id = %s
            """, (telegram_id,))
            row = cur.fetchone()

            if row is None or row["state_data"] is None:
                return {}

            try:
                return json.loads(row["state_data"])
            except Exception:
                return {}


def set_state_data(telegram_id, data):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE users
                SET state_data = %s
                WHERE telegram_id = %s
            """, (json.dumps(data), telegram_id))


def clear_state(telegram_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE users
                SET state = 'IDLE',
                    state_data = NULL
                WHERE telegram_id = %s
            """, (telegram_id,))
