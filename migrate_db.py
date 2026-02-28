import sqlite3
import os

db_path = "iis/sessions.db"
if not os.path.exists(db_path):
    print(f"Database {db_path} does not exist.")
else:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if title column exists
        cursor.execute("PRAGMA table_info(chat_sessions)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if "title" not in columns:
            print("Adding 'title' column to 'chat_sessions' table...")
            cursor.execute("ALTER TABLE chat_sessions ADD COLUMN title TEXT DEFAULT 'New Chat'")
            conn.commit()
            print("Column added successfully.")
        else:
            print("'title' column already exists.")
            
    except Exception as e:
        print(f"Error updating database: {e}")
    finally:
        conn.close()
