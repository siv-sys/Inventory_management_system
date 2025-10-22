# migrate_db.py
import sqlite3
from datetime import datetime

def migrate_database():
    # Connect to the database
    conn = sqlite3.connect('expenses.db')
    cursor = conn.cursor()
    
    try:
        # Check if updated_at column exists
        cursor.execute("PRAGMA table_info(expense)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'updated_at' not in columns:
            print("Adding updated_at column to expense table...")
            
            # Create a backup of the existing data
            cursor.execute("SELECT * FROM expense")
            expenses = cursor.fetchall()
            
            # Rename old table
            cursor.execute("ALTER TABLE expense RENAME TO expense_old")
            
            # Create new table with updated schema
            cursor.execute('''
                CREATE TABLE expense (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    description VARCHAR(200) NOT NULL,
                    amount FLOAT NOT NULL,
                    date DATE NOT NULL,
                    category VARCHAR(50) NOT NULL,
                    created_at DATETIME,
                    updated_at DATETIME
                )
            ''')
            
            # Copy data from old table to new table
            for expense in expenses:
                if len(expense) == 6:  # Old schema without updated_at
                    cursor.execute('''
                        INSERT INTO expense (id, description, amount, date, category, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (*expense, expense[5]))  # Use created_at for updated_at
                else:
                    cursor.execute('''
                        INSERT INTO expense (id, description, amount, date, category, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', expense)
            
            # Drop old table
            cursor.execute("DROP TABLE expense_old")
            
            print("Database migration completed successfully!")
        else:
            print("Database is already up to date.")
            
    except Exception as e:
        print(f"Migration error: {e}")
        conn.rollback()
    finally:
        conn.commit()
        conn.close()

if __name__ == '__main__':
    migrate_database()