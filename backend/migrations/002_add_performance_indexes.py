"""
Add Performance Indexes
Migration to add database indexes for frequently queried columns
Requirements: 12.4 - Add database indexes
"""

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT


def get_connection(database_url):
    """Get database connection"""
    return psycopg2.connect(database_url)


def add_indexes(conn):
    """Add performance indexes"""
    cursor = conn.cursor()
    
    print("Adding performance indexes...")
    
    # User table indexes
    indexes = [
        # Auth tables
        ("idx_users_email", "users", "email"),
        ("idx_users_username", "users", "username"),
        ("idx_users_created_at", "users", "created_at"),
        ("idx_sessions_user_id", "sessions", "user_id"),
        ("idx_sessions_token", "sessions", "token"),
        ("idx_sessions_expires_at", "sessions", "expires_at"),
        ("idx_password_reset_tokens_user_id", "password_reset_tokens", "user_id"),
        ("idx_password_reset_tokens_token", "password_reset_tokens", "token"),
        ("idx_password_reset_tokens_expires_at", "password_reset_tokens", "expires_at"),
        
        # Gamification tables
        ("idx_user_progress_user_id", "user_progress", "user_id"),
        ("idx_user_achievements_user_id", "user_achievements", "user_id"),
        ("idx_user_achievements_achievement_id", "user_achievements", "achievement_id"),
        ("idx_user_achievements_earned_at", "user_achievements", "earned_at"),
        ("idx_skill_progress_user_id", "skill_progress", "user_id"),
        ("idx_skill_progress_skill_id", "skill_progress", "skill_id"),
        ("idx_challenge_attempts_user_id", "challenge_attempts", "user_id"),
        ("idx_challenge_attempts_challenge_id", "challenge_attempts", "challenge_id"),
        ("idx_challenge_attempts_completed_at", "challenge_attempts", "completed_at"),
        ("idx_daily_streaks_user_id", "daily_streaks", "user_id"),
        ("idx_daily_streaks_date", "daily_streaks", "date"),
        
        # Study tools tables
        ("idx_flashcard_sets_user_id", "flashcard_sets", "user_id"),
        ("idx_flashcard_sets_created_at", "flashcard_sets", "created_at"),
        ("idx_flashcards_set_id", "flashcards", "set_id"),
        ("idx_flashcard_reviews_user_id", "flashcard_reviews", "user_id"),
        ("idx_flashcard_reviews_flashcard_id", "flashcard_reviews", "flashcard_id"),
        ("idx_flashcard_reviews_reviewed_at", "flashcard_reviews", "reviewed_at"),
        ("idx_notes_user_id", "notes", "user_id"),
        ("idx_notes_created_at", "notes", "created_at"),
        ("idx_study_sessions_user_id", "study_sessions", "user_id"),
        ("idx_study_sessions_started_at", "study_sessions", "started_at"),
        
        # Learning analytics tables
        ("idx_concept_mastery_user_id", "concept_mastery", "user_id"),
        ("idx_concept_mastery_concept_id", "concept_mastery", "concept_id"),
        ("idx_concept_mastery_updated_at", "concept_mastery", "updated_at"),
        ("idx_learning_events_user_id", "learning_events", "user_id"),
        ("idx_learning_events_event_type", "learning_events", "event_type"),
        ("idx_learning_events_timestamp", "learning_events", "timestamp"),
        ("idx_knowledge_gaps_user_id", "knowledge_gaps", "user_id"),
        ("idx_knowledge_gaps_identified_at", "knowledge_gaps", "identified_at"),
    ]
    
    for index_name, table_name, column_name in indexes:
        try:
            # Check if index already exists
            cursor.execute("""
                SELECT 1 FROM pg_indexes 
                WHERE indexname = %s
            """, (index_name,))
            
            if cursor.fetchone():
                print(f"  ⏭️  Index {index_name} already exists")
                continue
            
            # Check if table exists
            cursor.execute("""
                SELECT 1 FROM information_schema.tables 
                WHERE table_name = %s
            """, (table_name,))
            
            if not cursor.fetchone():
                print(f"  ⚠️  Table {table_name} does not exist, skipping index {index_name}")
                continue
            
            # Create index
            cursor.execute(f"""
                CREATE INDEX {index_name} ON {table_name} ({column_name})
            """)
            print(f"  ✅ Created index {index_name} on {table_name}({column_name})")
            
        except Exception as e:
            print(f"  ❌ Error creating index {index_name}: {e}")
            conn.rollback()
            continue
    
    # Composite indexes for common query patterns
    composite_indexes = [
        ("idx_sessions_user_expires", "sessions", ["user_id", "expires_at"]),
        ("idx_user_achievements_user_earned", "user_achievements", ["user_id", "earned_at"]),
        ("idx_challenge_attempts_user_completed", "challenge_attempts", ["user_id", "completed_at"]),
        ("idx_flashcard_reviews_user_reviewed", "flashcard_reviews", ["user_id", "reviewed_at"]),
        ("idx_learning_events_user_timestamp", "learning_events", ["user_id", "timestamp"]),
        ("idx_concept_mastery_user_updated", "concept_mastery", ["user_id", "updated_at"]),
    ]
    
    for index_name, table_name, columns in composite_indexes:
        try:
            # Check if index already exists
            cursor.execute("""
                SELECT 1 FROM pg_indexes 
                WHERE indexname = %s
            """, (index_name,))
            
            if cursor.fetchone():
                print(f"  ⏭️  Composite index {index_name} already exists")
                continue
            
            # Check if table exists
            cursor.execute("""
                SELECT 1 FROM information_schema.tables 
                WHERE table_name = %s
            """, (table_name,))
            
            if not cursor.fetchone():
                print(f"  ⚠️  Table {table_name} does not exist, skipping index {index_name}")
                continue
            
            # Create composite index
            columns_str = ", ".join(columns)
            cursor.execute(f"""
                CREATE INDEX {index_name} ON {table_name} ({columns_str})
            """)
            print(f"  ✅ Created composite index {index_name} on {table_name}({columns_str})")
            
        except Exception as e:
            print(f"  ❌ Error creating composite index {index_name}: {e}")
            conn.rollback()
            continue
    
    conn.commit()
    print("✅ Performance indexes added successfully")


def analyze_tables(conn):
    """Run ANALYZE on tables to update statistics"""
    cursor = conn.cursor()
    
    print("\nAnalyzing tables...")
    
    tables = [
        "users", "sessions", "password_reset_tokens",
        "user_progress", "user_achievements", "skill_progress",
        "challenge_attempts", "daily_streaks",
        "flashcard_sets", "flashcards", "flashcard_reviews",
        "notes", "study_sessions",
        "concept_mastery", "learning_events", "knowledge_gaps"
    ]
    
    for table in tables:
        try:
            # Check if table exists
            cursor.execute("""
                SELECT 1 FROM information_schema.tables 
                WHERE table_name = %s
            """, (table,))
            
            if not cursor.fetchone():
                continue
            
            cursor.execute(f"ANALYZE {table}")
            print(f"  ✅ Analyzed {table}")
        except Exception as e:
            print(f"  ⚠️  Could not analyze {table}: {e}")
            conn.rollback()
            continue
    
    conn.commit()
    print("✅ Table analysis complete")


def run_migration(database_url):
    """Run the migration"""
    print("=" * 60)
    print("Running migration: Add Performance Indexes")
    print("=" * 60)
    
    conn = get_connection(database_url)
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    
    try:
        add_indexes(conn)
        analyze_tables(conn)
        print("\n" + "=" * 60)
        print("Migration completed successfully!")
        print("=" * 60)
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    database_url = os.getenv("DATABASE_URL")
    
    if not database_url:
        print("❌ DATABASE_URL not found in environment")
        exit(1)
    
    run_migration(database_url)
