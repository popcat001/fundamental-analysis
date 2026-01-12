"""
Database migration script to add valuation_data JSON column to valuation_cache table

This script adds a new JSON column to store the complete valuation report including
all visualization data (historical EPS, P/E ratios, quarterly metrics, etc.)

Usage:
    python migrate_add_valuation_data.py
"""
import sqlite3
from database import engine
from sqlalchemy import inspect

def migrate():
    """Add valuation_data column to valuation_cache table"""

    # Check if we're using SQLite
    if 'sqlite' in str(engine.url):
        # SQLite connection
        db_path = str(engine.url).replace('sqlite:///', '')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check if column already exists
        cursor.execute("PRAGMA table_info(valuation_cache)")
        columns = [column[1] for column in cursor.fetchall()]

        if 'valuation_data' in columns:
            print("✓ Column 'valuation_data' already exists in valuation_cache table")
            conn.close()
            return

        # Add the column
        try:
            cursor.execute("ALTER TABLE valuation_cache ADD COLUMN valuation_data JSON")
            conn.commit()
            print("✓ Successfully added 'valuation_data' column to valuation_cache table")
        except Exception as e:
            print(f"✗ Error adding column: {e}")
            conn.rollback()
        finally:
            conn.close()
    else:
        # PostgreSQL or other database
        print("For PostgreSQL, run this SQL:")
        print("ALTER TABLE valuation_cache ADD COLUMN IF NOT EXISTS valuation_data JSON;")

        # Try to execute for PostgreSQL
        try:
            with engine.connect() as conn:
                conn.execute("ALTER TABLE valuation_cache ADD COLUMN IF NOT EXISTS valuation_data JSON")
                conn.commit()
                print("✓ Successfully added 'valuation_data' column")
        except Exception as e:
            print(f"Note: {e}")

if __name__ == "__main__":
    print("Running database migration: Add valuation_data JSON column")
    print("=" * 60)
    migrate()
    print("=" * 60)
    print("Migration complete!")
