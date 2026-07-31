import sqlite3
import os

db_path = "instance/family_database.db"

if os.path.exists(db_path):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if the column exists
        cursor.execute("PRAGMA table_info(guest)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'invitation_code' not in columns:
            print("Adding missing 'invitation_code' column to guest table...")
            cursor.execute("ALTER TABLE guest ADD COLUMN invitation_code VARCHAR(20)")
            conn.commit()
            print("Column added successfully!")
        else:
            print("Column 'invitation_code' already exists!")
        
        conn.close()
        print("Database schema fixed!")
    except Exception as e:
        print(f"Error: {e}")
else:
    print(f"Database file not found at {db_path}")
