import json

from database.db import get_connection


def get_state(telegram_id):
    conn = get_connection()

    row = conn.execute(
        """
        SELECT state
        FROM users
        WHERE telegram_id=?
        """,
        (telegram_id,)
    ).fetchone()

    conn.close()

    if row is None:
        return "IDLE"

    return row["state"]


def set_state(telegram_id, state):
    conn = get_connection()

    conn.execute(
        """
        UPDATE users
        SET state=?
        WHERE telegram_id=?
        """,
        (
            state,
            telegram_id
        )
    )

    conn.commit()
    conn.close()


def get_state_data(telegram_id):
    conn = get_connection()

    row = conn.execute(
        """
        SELECT state_data
        FROM users
        WHERE telegram_id=?
        """,
        (telegram_id,)
    ).fetchone()

    conn.close()

    if row is None:
        return {}

    if row["state_data"] is None:
        return {}

    try:
        return json.loads(row["state_data"])
    except Exception:
        return {}


def set_state_data(telegram_id, data):
    conn = get_connection()

    conn.execute(
        """
        UPDATE users
        SET state_data=?
        WHERE telegram_id=?
        """,
        (
            json.dumps(data),
            telegram_id
        )
    )

    conn.commit()
    conn.close()


def clear_state(telegram_id):
    conn = get_connection()

    conn.execute(
        """
        UPDATE users
        SET state='IDLE',
            state_data=NULL
        WHERE telegram_id=?
        """,
        (telegram_id,)
    )

    conn.commit()
    conn.close()
