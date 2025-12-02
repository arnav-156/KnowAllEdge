"""
Study Tools Database Manager
Handles calendar events, notes, citations, and exports
"""
import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class StudyToolsDB:
    def __init__(self, db_path: str = 'study_tools.db'):
        self.db_path = db_path
        self.init_db()
    
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_db(self):
        """Initialize study tools database tables"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Calendar events table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS calendar_events (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                event_type TEXT,
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL,
                topic_id TEXT,
                reminder_minutes INTEGER DEFAULT 15,
                is_recurring BOOLEAN DEFAULT 0,
                recurrence_pattern TEXT,
                status TEXT DEFAULT 'scheduled',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Notes table (Cornell method support)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notes (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                topic_id TEXT,
                title TEXT NOT NULL,
                note_type TEXT DEFAULT 'cornell',
                cue_column TEXT,
                notes_column TEXT,
                summary TEXT,
                tags TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Citations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS citations (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                topic_id TEXT,
                citation_style TEXT DEFAULT 'APA',
                title TEXT NOT NULL,
                authors TEXT,
                publication_date TEXT,
                url TEXT,
                access_date TEXT,
                additional_info TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Export history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS export_history (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                export_type TEXT NOT NULL,
                format TEXT NOT NULL,
                content_id TEXT,
                file_path TEXT,
                status TEXT DEFAULT 'completed',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Integration settings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS integration_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                platform TEXT NOT NULL,
                api_key TEXT,
                webhook_url TEXT,
                sync_enabled BOOLEAN DEFAULT 0,
                last_sync TEXT,
                settings TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, platform)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    # Calendar Methods
    def create_event(self, user_id: str, event_data: Dict) -> Dict:
        """Create a calendar event"""
        import uuid
        
        event_id = str(uuid.uuid4())
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO calendar_events 
            (id, user_id, title, description, event_type, start_time, end_time, 
             topic_id, reminder_minutes, is_recurring, recurrence_pattern)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            event_id, user_id, event_data['title'], event_data.get('description'),
            event_data.get('event_type', 'study'), event_data['start_time'],
            event_data['end_time'], event_data.get('topic_id'),
            event_data.get('reminder_minutes', 15), event_data.get('is_recurring', False),
            event_data.get('recurrence_pattern')
        ))
        
        conn.commit()
        conn.close()
        
        return self.get_event(event_id)

    def get_event(self, event_id: str) -> Optional[Dict]:
        """Get a calendar event by ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM calendar_events WHERE id = ?', (event_id,))
        row = cursor.fetchone()
        conn.close()
        
        return dict(row) if row else None
    
    def get_user_events(self, user_id: str, start_date: str = None, end_date: str = None) -> List[Dict]:
        """Get user's calendar events, optionally filtered by date range"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if start_date and end_date:
            cursor.execute('''
                SELECT * FROM calendar_events 
                WHERE user_id = ? AND start_time >= ? AND start_time <= ?
                ORDER BY start_time
            ''', (user_id, start_date, end_date))
        else:
            cursor.execute('''
                SELECT * FROM calendar_events 
                WHERE user_id = ?
                ORDER BY start_time
            ''', (user_id,))
        
        events = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return events
    
    def update_event(self, event_id: str, updates: Dict) -> Dict:
        """Update a calendar event"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        set_clause = ', '.join([f"{key} = ?" for key in updates.keys()])
        values = list(updates.values()) + [datetime.now().isoformat(), event_id]
        
        cursor.execute(f'''
            UPDATE calendar_events 
            SET {set_clause}, updated_at = ?
            WHERE id = ?
        ''', values)
        
        conn.commit()
        conn.close()
        
        return self.get_event(event_id)
    
    def delete_event(self, event_id: str) -> bool:
        """Delete a calendar event"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM calendar_events WHERE id = ?', (event_id,))
        deleted = cursor.rowcount > 0
        
        conn.commit()
        conn.close()
        
        return deleted

    # Notes Methods
    def create_note(self, user_id: str, note_data: Dict) -> Dict:
        """Create a note (Cornell or outline format)"""
        import uuid
        
        note_id = str(uuid.uuid4())
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO notes 
            (id, user_id, topic_id, title, note_type, cue_column, notes_column, summary, tags)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            note_id, user_id, note_data.get('topic_id'), note_data['title'],
            note_data.get('note_type', 'cornell'), note_data.get('cue_column'),
            note_data.get('notes_column'), note_data.get('summary'),
            json.dumps(note_data.get('tags', []))
        ))
        
        conn.commit()
        conn.close()
        
        return self.get_note(note_id)
    
    def get_note(self, note_id: str) -> Optional[Dict]:
        """Get a note by ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM notes WHERE id = ?', (note_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            note = dict(row)
            note['tags'] = json.loads(note['tags']) if note['tags'] else []
            return note
        return None
    
    def get_user_notes(self, user_id: str, topic_id: str = None) -> List[Dict]:
        """Get user's notes, optionally filtered by topic"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if topic_id:
            cursor.execute('''
                SELECT * FROM notes 
                WHERE user_id = ? AND topic_id = ?
                ORDER BY updated_at DESC
            ''', (user_id, topic_id))
        else:
            cursor.execute('''
                SELECT * FROM notes 
                WHERE user_id = ?
                ORDER BY updated_at DESC
            ''', (user_id,))
        
        notes = []
        for row in cursor.fetchall():
            note = dict(row)
            note['tags'] = json.loads(note['tags']) if note['tags'] else []
            notes.append(note)
        
        conn.close()
        return notes
    
    def update_note(self, note_id: str, updates: Dict) -> Dict:
        """Update a note"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if 'tags' in updates:
            updates['tags'] = json.dumps(updates['tags'])
        
        set_clause = ', '.join([f"{key} = ?" for key in updates.keys()])
        values = list(updates.values()) + [datetime.now().isoformat(), note_id]
        
        cursor.execute(f'''
            UPDATE notes 
            SET {set_clause}, updated_at = ?
            WHERE id = ?
        ''', values)
        
        conn.commit()
        conn.close()
        
        return self.get_note(note_id)
    
    def delete_note(self, note_id: str) -> bool:
        """Delete a note"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM notes WHERE id = ?', (note_id,))
        deleted = cursor.rowcount > 0
        
        conn.commit()
        conn.close()
        
        return deleted

    # Citation Methods
    def create_citation(self, user_id: str, citation_data: Dict) -> Dict:
        """Create a citation"""
        import uuid
        
        citation_id = str(uuid.uuid4())
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO citations 
            (id, user_id, topic_id, citation_style, title, authors, 
             publication_date, url, access_date, additional_info)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            citation_id, user_id, citation_data.get('topic_id'),
            citation_data.get('citation_style', 'APA'), citation_data['title'],
            citation_data.get('authors'), citation_data.get('publication_date'),
            citation_data.get('url'), citation_data.get('access_date'),
            json.dumps(citation_data.get('additional_info', {}))
        ))
        
        conn.commit()
        conn.close()
        
        return self.get_citation(citation_id)
    
    def get_citation(self, citation_id: str) -> Optional[Dict]:
        """Get a citation by ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM citations WHERE id = ?', (citation_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            citation = dict(row)
            citation['additional_info'] = json.loads(citation['additional_info']) if citation['additional_info'] else {}
            return citation
        return None
    
    def get_user_citations(self, user_id: str, topic_id: str = None) -> List[Dict]:
        """Get user's citations"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if topic_id:
            cursor.execute('''
                SELECT * FROM citations 
                WHERE user_id = ? AND topic_id = ?
                ORDER BY created_at DESC
            ''', (user_id, topic_id))
        else:
            cursor.execute('''
                SELECT * FROM citations 
                WHERE user_id = ?
                ORDER BY created_at DESC
            ''', (user_id,))
        
        citations = []
        for row in cursor.fetchall():
            citation = dict(row)
            citation['additional_info'] = json.loads(citation['additional_info']) if citation['additional_info'] else {}
            citations.append(citation)
        
        conn.close()
        return citations
    
    def format_citation(self, citation: Dict) -> str:
        """Format citation in specified style"""
        style = citation.get('citation_style', 'APA')
        
        if style == 'APA':
            return self._format_apa(citation)
        elif style == 'MLA':
            return self._format_mla(citation)
        elif style == 'Chicago':
            return self._format_chicago(citation)
        else:
            return self._format_apa(citation)
    
    def _format_apa(self, citation: Dict) -> str:
        """Format citation in APA style"""
        parts = []
        
        if citation.get('authors'):
            parts.append(f"{citation['authors']}.")
        
        if citation.get('publication_date'):
            parts.append(f"({citation['publication_date']}).")
        
        parts.append(f"{citation['title']}.")
        
        if citation.get('url'):
            parts.append(f"Retrieved from {citation['url']}")
        
        return ' '.join(parts)
    
    def _format_mla(self, citation: Dict) -> str:
        """Format citation in MLA style"""
        parts = []
        
        if citation.get('authors'):
            parts.append(f"{citation['authors']}.")
        
        parts.append(f'"{citation["title"]}."')
        
        if citation.get('publication_date'):
            parts.append(f"{citation['publication_date']}.")
        
        if citation.get('url'):
            parts.append(f"Web. {citation.get('access_date', 'n.d.')}.")
        
        return ' '.join(parts)
    
    def _format_chicago(self, citation: Dict) -> str:
        """Format citation in Chicago style"""
        parts = []
        
        if citation.get('authors'):
            parts.append(f"{citation['authors']}.")
        
        parts.append(f'"{citation["title"]}."')
        
        if citation.get('publication_date'):
            parts.append(f"({citation['publication_date']}).")
        
        if citation.get('url'):
            parts.append(citation['url'])
        
        return ' '.join(parts)

    # Export Methods
    def record_export(self, user_id: str, export_data: Dict) -> Dict:
        """Record an export operation"""
        import uuid
        
        export_id = str(uuid.uuid4())
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO export_history 
            (id, user_id, export_type, format, content_id, file_path, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            export_id, user_id, export_data['export_type'], export_data['format'],
            export_data.get('content_id'), export_data.get('file_path'),
            export_data.get('status', 'completed')
        ))
        
        conn.commit()
        conn.close()
        
        return {'id': export_id, **export_data}
    
    def get_export_history(self, user_id: str, limit: int = 50) -> List[Dict]:
        """Get user's export history"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM export_history 
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        ''', (user_id, limit))
        
        exports = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return exports
    
    # Integration Methods
    def save_integration_settings(self, user_id: str, platform: str, settings: Dict) -> Dict:
        """Save integration settings for a platform"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO integration_settings 
            (user_id, platform, api_key, webhook_url, sync_enabled, settings)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id, platform) DO UPDATE SET
                api_key = excluded.api_key,
                webhook_url = excluded.webhook_url,
                sync_enabled = excluded.sync_enabled,
                settings = excluded.settings,
                updated_at = ?
        ''', (
            user_id, platform, settings.get('api_key'), settings.get('webhook_url'),
            settings.get('sync_enabled', False), json.dumps(settings.get('settings', {})),
            datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()
        
        return self.get_integration_settings(user_id, platform)
    
    def get_integration_settings(self, user_id: str, platform: str = None) -> Optional[Dict]:
        """Get integration settings"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if platform:
            cursor.execute('''
                SELECT * FROM integration_settings 
                WHERE user_id = ? AND platform = ?
            ''', (user_id, platform))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                settings = dict(row)
                settings['settings'] = json.loads(settings['settings']) if settings['settings'] else {}
                return settings
            return None
        else:
            cursor.execute('''
                SELECT * FROM integration_settings 
                WHERE user_id = ?
            ''', (user_id,))
            
            integrations = []
            for row in cursor.fetchall():
                settings = dict(row)
                settings['settings'] = json.loads(settings['settings']) if settings['settings'] else {}
                integrations.append(settings)
            
            conn.close()
            return integrations
    
    def update_last_sync(self, user_id: str, platform: str) -> bool:
        """Update last sync timestamp"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE integration_settings 
            SET last_sync = ?
            WHERE user_id = ? AND platform = ?
        ''', (datetime.now().isoformat(), user_id, platform))
        
        updated = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return updated
