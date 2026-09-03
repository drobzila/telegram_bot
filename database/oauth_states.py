from database.db import get_connection


STATE_TTL_MINUTES = 15


def save_state(state, telegram_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                DELETE FROM oauth_states
                WHERE telegram_id = %s
            """, (telegram_id,))
            cur.execute("""
                INSERT INTO oauth_states (state, telegram_id)
                VALUES (%s, %s)
            """, (state, telegram_id))
        conn.commit()


def consume_state(state):
    if not state:
        return None

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                DELETE FROM oauth_states
                WHERE state = %s
                  AND created_at >= CURRENT_TIMESTAMP - (%s * INTERVAL '1 minute')
                RETURNING telegram_id
            """, (state, STATE_TTL_MINUTES))
            row = cur.fetchone()
        conn.commit()
        return row["telegram_id"] if row else None
