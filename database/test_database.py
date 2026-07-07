from database.db import initialize_database, get_connection

initialize_database()

conn = get_connection()

tables = conn.execute("""
SELECT table_name
FROM information_schema.tables
WHERE table_schema='public'
ORDER BY table_name
""").fetchall()

print("Tables:")
for table in tables:
    print(table["table_name"])

conn.close()
