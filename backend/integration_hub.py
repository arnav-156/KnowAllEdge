"""
Integration Hub
Manages connections with LMS, Google Classroom, Calendar Apps, and third-party tools
"""
import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Optional
import logging
import hashlib
import secrets

logger = logging.getLogger(__name__)

class IntegrationHub:
    def __init__(self, db_path: str = 'integrations.db'):
        self.db_path = db_path
        self.init_db()
    
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_db(self):
        """Initialize integration database tables"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # LMS connections table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS lms_connections (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                lms_type TEXT NOT NULL,
                lms_url TEXT,
                access_token TEXT,
                refresh_token TEXT,
                token_expires_at TEXT,
                user_lms_id TEXT,
                sync_enabled BOOLEAN DEFAULT 1,
                last_sync TEXT,
                sync_settings TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, lms_type)
            )
        ''')
        
        # Google Classroom connections
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS google_classroom_connections (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                google_user_id TEXT,
                access_token TEXT,
                refresh_token TEXT,
                token_expires_at TEXT,
                sync_enabled BOOLEAN DEFAULT 1,
                sync_courses BOOLEAN DEFAULT 1,
                sync_assignments BOOLEAN DEFAULT 1,
                last_sync TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id)
            )
        ''')
        
        # Calendar connections
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS calendar_connections (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                calendar_type TEXT NOT NULL,
                calendar_id TEXT,
                access_token TEXT,
                refresh_token TEXT,
                token_expires_at TEXT,
                sync_enabled BOOLEAN DEFAULT 1,
                sync_direction TEXT DEFAULT 'bidirectional',
                last_sync TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, calendar_type)
            )
        ''')
        
        # API keys for developers
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS api_keys (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                api_key TEXT UNIQUE NOT NULL,
                api_secret TEXT NOT NULL,
                name TEXT,
                description TEXT,
                permissions TEXT,
                rate_limit INTEGER DEFAULT 1000,
                is_active BOOLEAN DEFAULT 1,
                last_used TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                expires_at TEXT
            )
        ''')
        
        # Webhook subscriptions
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS webhooks (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                api_key_id TEXT NOT NULL,
                webhook_url TEXT NOT NULL,
                events TEXT NOT NULL,
                secret TEXT NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                last_triggered TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (api_key_id) REFERENCES api_keys(id)
            )
        ''')
        
        # Integration logs
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS integration_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                integration_type TEXT NOT NULL,
                action TEXT NOT NULL,
                status TEXT NOT NULL,
                details TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()

    # LMS Integration Methods
    def connect_lms(self, user_id: str, lms_data: Dict) -> Dict:
        """Connect to an LMS (Canvas, Blackboard, Moodle)"""
        import uuid
        
        connection_id = str(uuid.uuid4())
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO lms_connections 
                (id, user_id, lms_type, lms_url, access_token, refresh_token, 
                 token_expires_at, user_lms_id, sync_settings)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(user_id, lms_type) DO UPDATE SET
                    lms_url = excluded.lms_url,
                    access_token = excluded.access_token,
                    refresh_token = excluded.refresh_token,
                    token_expires_at = excluded.token_expires_at,
                    user_lms_id = excluded.user_lms_id,
                    sync_settings = excluded.sync_settings,
                    updated_at = ?
            ''', (
                connection_id, user_id, lms_data['lms_type'], lms_data.get('lms_url'),
                lms_data.get('access_token'), lms_data.get('refresh_token'),
                lms_data.get('token_expires_at'), lms_data.get('user_lms_id'),
                json.dumps(lms_data.get('sync_settings', {})),
                datetime.now().isoformat()
            ))
            
            conn.commit()
            
            # Log the connection
            self._log_integration(user_id, lms_data['lms_type'], 'connect', 'success')
            
            return {'success': True, 'connection_id': connection_id}
        except Exception as e:
            logger.error(f"Error connecting LMS: {e}")
            self._log_integration(user_id, lms_data['lms_type'], 'connect', 'failed', str(e))
            return {'success': False, 'error': str(e)}
        finally:
            conn.close()
    
    def get_lms_connection(self, user_id: str, lms_type: str = None) -> Optional[Dict]:
        """Get LMS connection details"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if lms_type:
            cursor.execute('''
                SELECT * FROM lms_connections 
                WHERE user_id = ? AND lms_type = ?
            ''', (user_id, lms_type))
        else:
            cursor.execute('''
                SELECT * FROM lms_connections 
                WHERE user_id = ?
            ''', (user_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            connection = dict(row)
            connection['sync_settings'] = json.loads(connection['sync_settings']) if connection['sync_settings'] else {}
            return connection
        return None
    
    def sync_lms_courses(self, user_id: str, lms_type: str) -> Dict:
        """Sync courses from LMS"""
        connection = self.get_lms_connection(user_id, lms_type)
        
        if not connection:
            return {'success': False, 'error': 'LMS not connected'}
        
        # In a real implementation, this would call the LMS API
        # For now, return a mock response
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE lms_connections 
            SET last_sync = ?
            WHERE user_id = ? AND lms_type = ?
        ''', (datetime.now().isoformat(), user_id, lms_type))
        
        conn.commit()
        conn.close()
        
        self._log_integration(user_id, lms_type, 'sync_courses', 'success')
        
        return {
            'success': True,
            'message': f'Courses synced from {lms_type}',
            'courses_synced': 0  # Would be actual count in real implementation
        }
    
    # Google Classroom Methods
    def connect_google_classroom(self, user_id: str, google_data: Dict) -> Dict:
        """Connect to Google Classroom"""
        import uuid
        
        connection_id = str(uuid.uuid4())
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO google_classroom_connections 
                (id, user_id, google_user_id, access_token, refresh_token, 
                 token_expires_at, sync_courses, sync_assignments)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    google_user_id = excluded.google_user_id,
                    access_token = excluded.access_token,
                    refresh_token = excluded.refresh_token,
                    token_expires_at = excluded.token_expires_at,
                    sync_courses = excluded.sync_courses,
                    sync_assignments = excluded.sync_assignments,
                    updated_at = ?
            ''', (
                connection_id, user_id, google_data.get('google_user_id'),
                google_data.get('access_token'), google_data.get('refresh_token'),
                google_data.get('token_expires_at'),
                google_data.get('sync_courses', True),
                google_data.get('sync_assignments', True),
                datetime.now().isoformat()
            ))
            
            conn.commit()
            self._log_integration(user_id, 'google_classroom', 'connect', 'success')
            
            return {'success': True, 'connection_id': connection_id}
        except Exception as e:
            logger.error(f"Error connecting Google Classroom: {e}")
            self._log_integration(user_id, 'google_classroom', 'connect', 'failed', str(e))
            return {'success': False, 'error': str(e)}
        finally:
            conn.close()
    
    def get_google_classroom_connection(self, user_id: str) -> Optional[Dict]:
        """Get Google Classroom connection"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM google_classroom_connections 
            WHERE user_id = ?
        ''', (user_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        return dict(row) if row else None
    
    def sync_google_classroom(self, user_id: str) -> Dict:
        """Sync assignments from Google Classroom"""
        connection = self.get_google_classroom_connection(user_id)
        
        if not connection:
            return {'success': False, 'error': 'Google Classroom not connected'}
        
        # In real implementation, would call Google Classroom API
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE google_classroom_connections 
            SET last_sync = ?
            WHERE user_id = ?
        ''', (datetime.now().isoformat(), user_id))
        
        conn.commit()
        conn.close()
        
        self._log_integration(user_id, 'google_classroom', 'sync', 'success')
        
        return {
            'success': True,
            'message': 'Google Classroom synced',
            'assignments_synced': 0  # Would be actual count
        }

    # Calendar Integration Methods
    def connect_calendar(self, user_id: str, calendar_data: Dict) -> Dict:
        """Connect to calendar app (Google Calendar, Outlook, Apple Calendar)"""
        import uuid
        
        connection_id = str(uuid.uuid4())
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO calendar_connections 
                (id, user_id, calendar_type, calendar_id, access_token, 
                 refresh_token, token_expires_at, sync_direction)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(user_id, calendar_type) DO UPDATE SET
                    calendar_id = excluded.calendar_id,
                    access_token = excluded.access_token,
                    refresh_token = excluded.refresh_token,
                    token_expires_at = excluded.token_expires_at,
                    sync_direction = excluded.sync_direction,
                    updated_at = ?
            ''', (
                connection_id, user_id, calendar_data['calendar_type'],
                calendar_data.get('calendar_id'), calendar_data.get('access_token'),
                calendar_data.get('refresh_token'), calendar_data.get('token_expires_at'),
                calendar_data.get('sync_direction', 'bidirectional'),
                datetime.now().isoformat()
            ))
            
            conn.commit()
            self._log_integration(user_id, calendar_data['calendar_type'], 'connect', 'success')
            
            return {'success': True, 'connection_id': connection_id}
        except Exception as e:
            logger.error(f"Error connecting calendar: {e}")
            self._log_integration(user_id, calendar_data['calendar_type'], 'connect', 'failed', str(e))
            return {'success': False, 'error': str(e)}
        finally:
            conn.close()
    
    def get_calendar_connection(self, user_id: str, calendar_type: str = None) -> Optional[Dict]:
        """Get calendar connection"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if calendar_type:
            cursor.execute('''
                SELECT * FROM calendar_connections 
                WHERE user_id = ? AND calendar_type = ?
            ''', (user_id, calendar_type))
        else:
            cursor.execute('''
                SELECT * FROM calendar_connections 
                WHERE user_id = ?
            ''', (user_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        return dict(row) if row else None
    
    def sync_calendar(self, user_id: str, calendar_type: str) -> Dict:
        """Sync study sessions with calendar"""
        connection = self.get_calendar_connection(user_id, calendar_type)
        
        if not connection:
            return {'success': False, 'error': 'Calendar not connected'}
        
        # In real implementation, would sync with calendar API
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE calendar_connections 
            SET last_sync = ?
            WHERE user_id = ? AND calendar_type = ?
        ''', (datetime.now().isoformat(), user_id, calendar_type))
        
        conn.commit()
        conn.close()
        
        self._log_integration(user_id, calendar_type, 'sync', 'success')
        
        return {
            'success': True,
            'message': f'Calendar synced with {calendar_type}',
            'events_synced': 0  # Would be actual count
        }
    
    # Developer API Methods
    def generate_api_key(self, user_id: str, key_data: Dict) -> Dict:
        """Generate API key for developers"""
        import uuid
        
        api_key_id = str(uuid.uuid4())
        api_key = f"ik_{secrets.token_urlsafe(32)}"
        api_secret = secrets.token_urlsafe(48)
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO api_keys 
                (id, user_id, api_key, api_secret, name, description, 
                 permissions, rate_limit, expires_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                api_key_id, user_id, api_key, api_secret,
                key_data.get('name', 'API Key'),
                key_data.get('description'),
                json.dumps(key_data.get('permissions', ['read'])),
                key_data.get('rate_limit', 1000),
                key_data.get('expires_at')
            ))
            
            conn.commit()
            
            return {
                'success': True,
                'api_key': api_key,
                'api_secret': api_secret,
                'key_id': api_key_id,
                'message': 'Store the API secret securely - it will not be shown again'
            }
        except Exception as e:
            logger.error(f"Error generating API key: {e}")
            return {'success': False, 'error': str(e)}
        finally:
            conn.close()
    
    def validate_api_key(self, api_key: str) -> Optional[Dict]:
        """Validate an API key"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM api_keys 
            WHERE api_key = ? AND is_active = 1
        ''', (api_key,))
        
        row = cursor.fetchone()
        
        if row:
            key_data = dict(row)
            
            # Check expiration
            if key_data['expires_at']:
                expires_at = datetime.fromisoformat(key_data['expires_at'])
                if datetime.now() > expires_at:
                    conn.close()
                    return None
            
            # Update last used
            cursor.execute('''
                UPDATE api_keys 
                SET last_used = ?
                WHERE id = ?
            ''', (datetime.now().isoformat(), key_data['id']))
            
            conn.commit()
            conn.close()
            
            key_data['permissions'] = json.loads(key_data['permissions']) if key_data['permissions'] else []
            return key_data
        
        conn.close()
        return None
    
    def get_user_api_keys(self, user_id: str) -> List[Dict]:
        """Get user's API keys"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, name, description, permissions, rate_limit, 
                   is_active, last_used, created_at, expires_at
            FROM api_keys 
            WHERE user_id = ?
            ORDER BY created_at DESC
        ''', (user_id,))
        
        keys = []
        for row in cursor.fetchall():
            key = dict(row)
            key['permissions'] = json.loads(key['permissions']) if key['permissions'] else []
            keys.append(key)
        
        conn.close()
        return keys
    
    def revoke_api_key(self, key_id: str) -> bool:
        """Revoke an API key"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE api_keys 
            SET is_active = 0
            WHERE id = ?
        ''', (key_id,))
        
        revoked = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return revoked
    
    # Webhook Methods
    def create_webhook(self, user_id: str, api_key_id: str, webhook_data: Dict) -> Dict:
        """Create a webhook subscription"""
        import uuid
        
        webhook_id = str(uuid.uuid4())
        webhook_secret = secrets.token_urlsafe(32)
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO webhooks 
                (id, user_id, api_key_id, webhook_url, events, secret)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                webhook_id, user_id, api_key_id,
                webhook_data['webhook_url'],
                json.dumps(webhook_data['events']),
                webhook_secret
            ))
            
            conn.commit()
            
            return {
                'success': True,
                'webhook_id': webhook_id,
                'webhook_secret': webhook_secret,
                'message': 'Webhook created successfully'
            }
        except Exception as e:
            logger.error(f"Error creating webhook: {e}")
            return {'success': False, 'error': str(e)}
        finally:
            conn.close()
    
    def get_user_webhooks(self, user_id: str) -> List[Dict]:
        """Get user's webhooks"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM webhooks 
            WHERE user_id = ?
            ORDER BY created_at DESC
        ''', (user_id,))
        
        webhooks = []
        for row in cursor.fetchall():
            webhook = dict(row)
            webhook['events'] = json.loads(webhook['events']) if webhook['events'] else []
            webhooks.append(webhook)
        
        conn.close()
        return webhooks
    
    # Logging
    def _log_integration(self, user_id: str, integration_type: str, 
                        action: str, status: str, details: str = None):
        """Log integration activity"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO integration_logs 
            (user_id, integration_type, action, status, details)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, integration_type, action, status, details))
        
        conn.commit()
        conn.close()
    
    def get_integration_logs(self, user_id: str, limit: int = 50) -> List[Dict]:
        """Get integration logs"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM integration_logs 
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        ''', (user_id, limit))
        
        logs = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return logs
