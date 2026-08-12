"""
Sprint 9 Database Migration: Feedback Loop

Adds feedback_examples table for storing few-shot training examples.
"""
import psycopg2
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database connection parameters
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "anchor_db")
DB_USER = os.getenv("DB_USER", "anchor_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "anchor_pass")

def run_sprint9_migration():
    """Add feedback_examples table"""
    print("=" * 70)
    print("SPRINT 9 MIGRATION: FEEDBACK LOOP")
    print("=" * 70)
    
    try:
        # Connect to database
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        
        cursor = conn.cursor()
        
        # Check if feedback_examples table exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'feedback_examples'
            );
        """)
        
        table_exists = cursor.fetchone()[0]
        
        if table_exists:
            print("✅ feedback_examples table already exists")
            return
        
        print("\n1. Creating feedback_examples table...")
        
        cursor.execute("""
            CREATE TABLE feedback_examples (
                id VARCHAR NOT NULL,
                workspace_id VARCHAR NOT NULL,
                requirement_id VARCHAR NOT NULL,
                example_type VARCHAR NOT NULL,
                segments_json TEXT NOT NULL,
                expected_output_json TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (id),
                FOREIGN KEY (requirement_id) REFERENCES requirements(id)
            );
        """)
        
        print("✅ Created feedback_examples table")
        
        print("\n2. Creating indexes...")
        
        cursor.execute("""
            CREATE INDEX ix_feedback_workspace ON feedback_examples(workspace_id);
        """)
        
        cursor.execute("""
            CREATE INDEX ix_feedback_requirement ON feedback_examples(requirement_id);
        """)
        
        cursor.execute("""
            CREATE INDEX ix_feedback_type ON feedback_examples(example_type);
        """)
        
        cursor.execute("""
            CREATE INDEX ix_feedback_created ON feedback_examples(created_at);
        """)
        
        print("✅ Created indexes on feedback_examples")
        
        # Commit changes
        conn.commit()
        
        print("\n" + "=" * 70)
        print("✅ SPRINT 9 MIGRATION COMPLETE")
        print("=" * 70)
        print("\nNew table:")
        print("  • feedback_examples - Stores few-shot training examples")
        print("\nNext steps:")
        print("  1. Restart backend server")
        print("  2. Test feedback endpoints:")
        print("     POST /api/feedback/update/{workspace_id}")
        print("     GET /api/feedback/metrics/{workspace_id}")
        print("     GET /api/feedback/improvements/{workspace_id}")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        if conn:
            conn.rollback()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    run_sprint9_migration()