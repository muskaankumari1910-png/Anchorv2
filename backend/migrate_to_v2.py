"""
Sprint 8: Database migration to add workspace_id to all tables.

This script:
1. Adds workspace_id column to all relevant tables
2. Sets default workspace_id for existing data ('default')
3. Creates indexes for workspace filtering

Run this before starting V2 with multi-tenancy.
"""
from sqlalchemy import text
from app.database import engine

DEFAULT_WORKSPACE_ID = "default"

def migrate_to_v2():
    """Add workspace_id to all tables for multi-tenancy"""
    
    print("🔄 Starting Sprint 8 migration: Adding workspace_id...")
    
    with engine.begin() as conn:
        # Add workspace_id to sources
        print("  → Adding workspace_id to sources...")
        conn.execute(text("""
            ALTER TABLE sources 
            ADD COLUMN IF NOT EXISTS workspace_id VARCHAR NOT NULL DEFAULT 'default';
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_sources_workspace 
            ON sources(workspace_id);
        """))
        
        # Add workspace_id to segments
        print("  → Adding workspace_id to segments...")
        conn.execute(text("""
            ALTER TABLE segments 
            ADD COLUMN IF NOT EXISTS workspace_id VARCHAR NOT NULL DEFAULT 'default';
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_segment_workspace 
            ON segments(workspace_id);
        """))
        
        # Add workspace_id to requirements
        print("  → Adding workspace_id to requirements...")
        conn.execute(text("""
            ALTER TABLE requirements 
            ADD COLUMN IF NOT EXISTS workspace_id VARCHAR NOT NULL DEFAULT 'default';
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_requirement_workspace 
            ON requirements(workspace_id);
        """))
        
        # Add workspace_id to evidence
        print("  → Adding workspace_id to evidence...")
        conn.execute(text("""
            ALTER TABLE evidence 
            ADD COLUMN IF NOT EXISTS workspace_id VARCHAR NOT NULL DEFAULT 'default';
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_evidence_workspace 
            ON evidence(workspace_id);
        """))
        
        # Add workspace_id to audit_events
        print("  → Adding workspace_id to audit_events...")
        conn.execute(text("""
            ALTER TABLE audit_events 
            ADD COLUMN IF NOT EXISTS workspace_id VARCHAR NOT NULL DEFAULT 'default';
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_audit_workspace 
            ON audit_events(workspace_id);
        """))
        
        # Add workspace_id to merge_suggestions
        print("  → Adding workspace_id to merge_suggestions...")
        conn.execute(text("""
            ALTER TABLE merge_suggestions 
            ADD COLUMN IF NOT EXISTS workspace_id VARCHAR NOT NULL DEFAULT 'default';
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_merge_workspace 
            ON merge_suggestions(workspace_id);
        """))
        
        # Add workspace_id to segment_consumption
        print("  → Adding workspace_id to segment_consumption...")
        conn.execute(text("""
            ALTER TABLE segment_consumption 
            ADD COLUMN IF NOT EXISTS workspace_id VARCHAR NOT NULL DEFAULT 'default';
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_consumption_workspace 
            ON segment_consumption(workspace_id);
        """))
        
        # Add workspace_id to gaps
        print("  → Adding workspace_id to gaps...")
        conn.execute(text("""
            ALTER TABLE gaps 
            ADD COLUMN IF NOT EXISTS workspace_id VARCHAR NOT NULL DEFAULT 'default';
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_gap_workspace 
            ON gaps(workspace_id);
        """))
        
        # Add workspace_id to contradictions
        print("  → Adding workspace_id to contradictions...")
        conn.execute(text("""
            ALTER TABLE contradictions 
            ADD COLUMN IF NOT EXISTS workspace_id VARCHAR NOT NULL DEFAULT 'default';
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_contradiction_workspace 
            ON contradictions(workspace_id);
        """))
    
    print("✅ Migration complete! All tables now have workspace_id.")
    print(f"   Existing data assigned to workspace: '{DEFAULT_WORKSPACE_ID}'")
    print("\nNext steps:")
    print("  1. Restart backend server")
    print("  2. All new data will use workspace_id from API context")
    print("  3. Existing data remains in 'default' workspace")

if __name__ == "__main__":
    try:
        migrate_to_v2()
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        print("\nIf tables already have workspace_id, this is safe to ignore.")
        print("Run this only once after upgrading to V2.")
