"""
Migration 001: Create authentication tables

Creates User, Session, and AuditLog tables with proper indexes
"""

from datetime import datetime


def upgrade(conn):
    """Apply migration"""
    
    # Create users table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id VARCHAR(36) PRIMARY KEY,
            email VARCHAR(255) NOT NULL UNIQUE,
            password_hash VARCHAR(255) NOT NULL,
            role VARCHAR(20) NOT NULL DEFAULT 'user',
            quota_tier VARCHAR(20) NOT NULL DEFAULT 'free',
            api_key_hash VARCHAR(64) UNIQUE,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP,
            failed_login_attempts INTEGER NOT NULL DEFAULT 0,
            account_locked_until TIMESTAMP,
            email_verified BOOLEAN NOT NULL DEFAULT 0,
            email_verification_token VARCHAR(64),
            password_reset_token VARCHAR(64),
            password_reset_expires TIMESTAMP,
            consent_given_at TIMESTAMP,
            data_export_requested_at TIMESTAMP,
            deletion_requested_at TIMESTAMP
        )
    """)
    
    # Create indexes on users table
    conn.execute("CREATE INDEX IF NOT EXISTS idx_user_email ON users(email)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_user_api_key_hash ON users(api_key_hash)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_user_created_at ON users(created_at)")
    
    # Create sessions table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id VARCHAR(36) PRIMARY KEY,
            user_id VARCHAR(36) NOT NULL,
            token_hash VARCHAR(64) NOT NULL UNIQUE,
            ip_address VARCHAR(45),
            user_agent VARCHAR(500),
            device_type VARCHAR(50),
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP NOT NULL,
            last_activity TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN NOT NULL DEFAULT 1,
            revoked_at TIMESTAMP,
            revoke_reason VARCHAR(255),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)
    
    # Create indexes on sessions table
    conn.execute("CREATE INDEX IF NOT EXISTS idx_session_user_id ON sessions(user_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_session_token_hash ON sessions(token_hash)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_session_expires_at ON sessions(expires_at)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_session_is_active ON sessions(is_active)")
    
    # Create audit_logs table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id VARCHAR(36) PRIMARY KEY,
            user_id VARCHAR(36),
            event_type VARCHAR(50) NOT NULL,
            event_category VARCHAR(50) NOT NULL,
            resource_type VARCHAR(50),
            resource_id VARCHAR(255),
            ip_address VARCHAR(45),
            user_agent VARCHAR(500),
            request_id VARCHAR(36),
            event_data TEXT,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
        )
    """)
    
    # Create indexes on audit_logs table
    conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_user_id ON audit_logs(user_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_event_type ON audit_logs(event_type)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_created_at ON audit_logs(created_at)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_request_id ON audit_logs(request_id)")
    
    # Create migration tracking table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version INTEGER PRIMARY KEY,
            applied_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            description TEXT
        )
    """)
    
    # Record this migration
    conn.execute("""
        INSERT INTO schema_migrations (version, description)
        VALUES (1, 'Create authentication tables')
    """)
    
    conn.commit()
    print("✅ Migration 001 applied: Created authentication tables")


def downgrade(conn):
    """Rollback migration"""
    
    # Drop tables in reverse order (respecting foreign keys)
    conn.execute("DROP TABLE IF EXISTS audit_logs")
    conn.execute("DROP TABLE IF EXISTS sessions")
    conn.execute("DROP TABLE IF EXISTS users")
    
    # Remove migration record
    conn.execute("DELETE FROM schema_migrations WHERE version = 1")
    
    conn.commit()
    print("⚠️ Migration 001 rolled back: Dropped authentication tables")


if __name__ == '__main__':
    import sqlite3
    import os
    
    # Get database path
    db_path = os.getenv('DATABASE_PATH', 'auth.db')
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    
    try:
        print(f"Applying migration to {db_path}...")
        upgrade(conn)
        print("Migration complete!")
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        conn.rollback()
    finally:
        conn.close()
