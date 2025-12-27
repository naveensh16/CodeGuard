"""
Database Migration Script for CodeGuard
Adds 'fixed_code' column to Issue table for AI auto-fix feature
"""

import sqlite3
import os

DB_PATH = 'instance/codeguard.db'

def migrate_database():
    """Add fixed_code column to existing database"""
    
    if not os.path.exists(DB_PATH):
        print("✓ No existing database found. Schema will be created on first run.")
        return
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check if fixed_code column exists
        cursor.execute("PRAGMA table_info(issue)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'fixed_code' in columns:
            print("✓ Database already up to date! 'fixed_code' column exists.")
        else:
            print("⚙ Adding 'fixed_code' column to Issue table...")
            cursor.execute("ALTER TABLE issue ADD COLUMN fixed_code TEXT")
            conn.commit()
            print("✓ Migration completed successfully!")
        
        conn.close()
        
    except Exception as e:
        print(f"✗ Migration failed: {e}")
        print("\nTo fix: Delete codeguard.db and restart the application.")
        print("Your old data will be lost, but schema will be recreated correctly.")

if __name__ == '__main__':
    print("CodeGuard Database Migration")
    print("=" * 50)
    migrate_database()
    print("\nYou can now run 'python app.py' to start the application.")
