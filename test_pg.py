import psycopg
from config import DATABASE_URL

print(DATABASE_URL)

conn = psycopg.connect(
    DATABASE_URL,
    connect_timeout=10
)

print("Connected!")

conn.close()
