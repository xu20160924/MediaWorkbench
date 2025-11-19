import sqlite3

try:
    # Connect to the SQLite database
    conn = sqlite3.connect('app.db')
    cursor = conn.cursor()

    # Query to get the list of tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()

    print("Tables in the database:")
    if tables:
        for table in tables:
            print(f"- {table[0]}")
    else:
        print("No tables found.")

except sqlite3.Error as e:
    print(f"Database error: {e}")
finally:
    # Close the connection
    if conn:
        conn.close()







