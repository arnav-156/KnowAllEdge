"""
Analytics Database Module
Stores frontend analytics events in SQLite for persistence
"""

import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import threading
from contextlib import contextmanager
import logging
import os

logger = logging.getLogger(__name__)

DB_PATH = os.path.join(os.path.dirname(__file__), 'analytics.db')

class AnalyticsDB:
    """SQLite-based analytics storage"""
    
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.lock = threading.Lock()
        self._init_db()
        logger.info(f"Analytics database initialized at {db_path}")
    
    def _init_db(self):
        """Create analytics tables if they don't exist"""
        with self._get_connection() as conn:
            # Main events table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    event_data TEXT,
                    user_agent TEXT,
                    ip_address TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # ✅ Add user_id column if it doesn't exist (migration)
            try:
                conn.execute('ALTER TABLE events ADD COLUMN user_id TEXT')
                logger.info("✅ Added user_id column to events table")
            except sqlite3.OperationalError as e:
                if 'duplicate column name' in str(e).lower():
                    pass  # Column already exists, that's fine
                else:
                    raise
            
            # Create indexes for fast queries
            conn.execute('CREATE INDEX IF NOT EXISTS idx_user_id ON events(user_id)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_session ON events(session_id)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_event_type ON events(event_type)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_created_at ON events(created_at)')
            
            # Page views table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS page_views (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    page_name TEXT NOT NULL,
                    load_time_ms REAL,
                    fcp REAL,
                    lcp REAL,
                    ttfb REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Errors table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS errors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    error_message TEXT,
                    error_stack TEXT,
                    context TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # API calls table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS api_calls (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    endpoint TEXT NOT NULL,
                    method TEXT,
                    duration_ms REAL,
                    status_code INTEGER,
                    error TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
    
            # User Progress table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS user_progress (
                    user_id TEXT NOT NULL,
                    topic TEXT NOT NULL,
                    subtopic TEXT NOT NULL,
                    mastery_level INTEGER DEFAULT 0,
                    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (user_id, topic, subtopic)
                )
            ''')

            # Quiz Results table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS quiz_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    topic TEXT NOT NULL,
                    score INTEGER NOT NULL,
                    total_questions INTEGER NOT NULL,
                    difficulty_level TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
    
    @contextmanager
    def _get_connection(self):
        """Thread-safe database connection"""
        with self.lock:
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            try:
                yield conn
            finally:
                conn.close()
    
    def insert_event(self, session_id: str, event_type: str, 
                    event_data: Dict, user_agent: str = None, ip_address: str = None):
        """Insert analytics event"""
        try:
            # ✅ NEW: Extract user_id from event_data
            user_id = event_data.get('userId') if event_data else None
            
            with self._get_connection() as conn:
                conn.execute(
                    '''INSERT INTO events 
                       (user_id, session_id, event_type, event_data, user_agent, ip_address) 
                       VALUES (?, ?, ?, ?, ?, ?)''',
                    (user_id, session_id, event_type, json.dumps(event_data), user_agent, ip_address)
                )
                conn.commit()
                
                # Also store specific event types in specialized tables
                if event_type == 'page_load' and event_data:
                    self._insert_page_view(conn, session_id, event_data)
                elif event_type == 'api_call' and event_data:
                    self._insert_api_call(conn, session_id, event_data)
                elif event_type == 'error' and event_data:
                    self._insert_error(conn, session_id, event_data)
                    
        except Exception as e:
            logger.error(f"Failed to insert event: {e}")
    
    def _insert_page_view(self, conn, session_id: str, data: Dict):
        """Insert page view record"""
        try:
            conn.execute(
                '''INSERT INTO page_views 
                   (session_id, page_name, load_time_ms, fcp, lcp, ttfb) 
                   VALUES (?, ?, ?, ?, ?, ?)''',
                (
                    session_id,
                    data.get('pageName'),
                    data.get('loadTime'),
                    data.get('metrics', {}).get('FCP'),
                    data.get('metrics', {}).get('LCP'),
                    data.get('metrics', {}).get('TTFB')
                )
            )
            conn.commit()
        except Exception as e:
            logger.error(f"Failed to insert page view: {e}")
    
    def _insert_api_call(self, conn, session_id: str, data: Dict):
        """Insert API call record"""
        try:
            conn.execute(
                '''INSERT INTO api_calls 
                   (session_id, endpoint, method, duration_ms, status_code, error) 
                   VALUES (?, ?, ?, ?, ?, ?)''',
                (
                    session_id,
                    data.get('endpoint'),
                    data.get('method'),
                    data.get('duration'),
                    data.get('status'),
                    data.get('error')
                )
            )
            conn.commit()
        except Exception as e:
            logger.error(f"Failed to insert API call: {e}")
    
    def _insert_error(self, conn, session_id: str, data: Dict):
        """Insert error record"""
        try:
            conn.execute(
                '''INSERT INTO errors 
                   (session_id, error_message, error_stack, context) 
                   VALUES (?, ?, ?, ?)''',
                (
                    session_id,
                    data.get('message'),
                    data.get('stack'),
                    json.dumps(data.get('context', {}))
                )
            )
            conn.commit()
        except Exception as e:
            logger.error(f"Failed to insert error: {e}")
    
    def get_events(self, limit: int = 100, event_type: Optional[str] = None,
                   since: Optional[datetime] = None) -> List[Dict]:
        """Get recent events"""
        try:
            query = 'SELECT * FROM events WHERE 1=1'
            params = []
            
            if event_type:
                query += ' AND event_type = ?'
                params.append(event_type)
            
            if since:
                query += ' AND created_at >= ?'
                params.append(since.isoformat())
            
            query += ' ORDER BY created_at DESC LIMIT ?'
            params.append(limit)
            
            with self._get_connection() as conn:
                rows = conn.execute(query, params).fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Failed to get events: {e}")
            return []
    
    def get_funnel_stats(self, days: int = 7) -> Dict:
        """Calculate funnel conversion rates"""
        try:
            since = datetime.now() - timedelta(days=days)
            
            with self._get_connection() as conn:
                # Count unique sessions at each stage
                total_sessions = conn.execute(
                    '''SELECT COUNT(DISTINCT session_id) FROM page_views 
                       WHERE created_at >= ? AND page_name = 'Homepage' ''',
                    (since.isoformat(),)
                ).fetchone()[0]
                
                interactions = conn.execute(
                    '''SELECT COUNT(DISTINCT session_id) FROM events 
                       WHERE created_at >= ? AND event_type = 'first_interaction' ''',
                    (since.isoformat(),)
                ).fetchone()[0]
                
                presentations = conn.execute(
                    '''SELECT COUNT(DISTINCT session_id) FROM events 
                       WHERE created_at >= ? AND event_type = 'task_completion' 
                       AND json_extract(event_data, '$.taskName') = 'generate_presentation' ''',
                    (since.isoformat(),)
                ).fetchone()[0]
                
                exports = conn.execute(
                    '''SELECT COUNT(DISTINCT session_id) FROM events 
                       WHERE created_at >= ? AND event_type = 'task_completion' 
                       AND json_extract(event_data, '$.taskName') LIKE 'export_%' ''',
                    (since.isoformat(),)
                ).fetchone()[0]
                
                return {
                    'period_days': days,
                    'homepage_views': total_sessions,
                    'first_interactions': interactions,
                    'interaction_rate': round(interactions / total_sessions * 100, 2) if total_sessions > 0 else 0,
                    'presentations_generated': presentations,
                    'generation_rate': round(presentations / interactions * 100, 2) if interactions > 0 else 0,
                    'exports': exports,
                    'export_rate': round(exports / presentations * 100, 2) if presentations > 0 else 0,
                    'overall_conversion': round(exports / total_sessions * 100, 2) if total_sessions > 0 else 0
                }
        except Exception as e:
            logger.error(f"Failed to get funnel stats: {e}")
            return {}
    
    def get_performance_stats(self, days: int = 7) -> Dict:
        """Get performance metrics statistics"""
        try:
            since = datetime.now() - timedelta(days=days)
            
            with self._get_connection() as conn:
                stats = conn.execute(
                    '''SELECT 
                        AVG(load_time_ms) as avg_load_time,
                        AVG(fcp) as avg_fcp,
                        AVG(lcp) as avg_lcp,
                        AVG(ttfb) as avg_ttfb,
                        COUNT(*) as total_page_views
                       FROM page_views 
                       WHERE created_at >= ? AND load_time_ms IS NOT NULL''',
                    (since.isoformat(),)
                ).fetchone()
                
                api_stats = conn.execute(
                    '''SELECT 
                        AVG(duration_ms) as avg_duration,
                        COUNT(*) as total_calls,
                        SUM(CASE WHEN status_code >= 400 THEN 1 ELSE 0 END) as error_count
                       FROM api_calls 
                       WHERE created_at >= ?''',
                    (since.isoformat(),)
                ).fetchone()
                
                return {
                    'period_days': days,
                    'avg_page_load_ms': round(stats['avg_load_time'], 2) if stats['avg_load_time'] else 0,
                    'avg_fcp_ms': round(stats['avg_fcp'], 2) if stats['avg_fcp'] else 0,
                    'avg_lcp_ms': round(stats['avg_lcp'], 2) if stats['avg_lcp'] else 0,
                    'avg_ttfb_ms': round(stats['avg_ttfb'], 2) if stats['avg_ttfb'] else 0,
                    'total_page_views': stats['total_page_views'],
                    'avg_api_duration_ms': round(api_stats['avg_duration'], 2) if api_stats['avg_duration'] else 0,
                    'total_api_calls': api_stats['total_calls'],
                    'api_error_rate': round(api_stats['error_count'] / api_stats['total_calls'] * 100, 2) if api_stats['total_calls'] > 0 else 0
                }
        except Exception as e:
            logger.error(f"Failed to get performance stats: {e}")
            return {}
    
    def get_error_summary(self, days: int = 7) -> List[Dict]:
        """Get error summary grouped by error message"""
        try:
            since = datetime.now() - timedelta(days=days)
            
            with self._get_connection() as conn:
                rows = conn.execute(
                    '''SELECT 
                        error_message,
                        COUNT(*) as count,
                        MAX(created_at) as last_occurred
                       FROM errors 
                       WHERE created_at >= ?
                       GROUP BY error_message
                       ORDER BY count DESC
                       LIMIT 20''',
                    (since.isoformat(),)
                ).fetchall()
                
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Failed to get error summary: {e}")
            return []
    
    def cleanup_old_data(self, days: int = 30):
        """Delete events older than specified days"""
        try:
            cutoff = datetime.now() - timedelta(days=days)
            
            with self._get_connection() as conn:
                # Delete from all tables
                for table in ['events', 'page_views', 'api_calls', 'errors']:
                    result = conn.execute(
                        f'DELETE FROM {table} WHERE created_at < ?',
                        (cutoff.isoformat(),)
                    )
                    conn.commit()
                    logger.info(f"Deleted {result.rowcount} old records from {table}")
                
                # Vacuum to reclaim space
                conn.execute('VACUUM')
                
        except Exception as e:
            logger.error(f"Failed to cleanup old data: {e}")
    
    def get_database_size(self) -> int:
        """Get database file size in bytes"""
        try:
            return os.path.getsize(self.db_path)
        except Exception as e:
            logger.error(f"Failed to get database size: {e}")
            return 0
    
    def get_cohort_analysis(self, period: str = 'week') -> Dict:
        """
        Cohort analysis - track user retention over time
        Groups users by their first visit period and tracks return rates
        """
        try:
            with self._get_connection() as conn:
                # Determine grouping (week or month)
                if period == 'month':
                    date_format = "%Y-%m"
                    period_name = "month"
                else:
                    date_format = "%Y-W%W"  # Year-Week
                    period_name = "week"
                
                # Get cohorts: first visit period for each session
                query = f"""
                SELECT 
                    strftime('{date_format}', MIN(created_at)) as cohort,
                    session_id
                FROM events
                GROUP BY session_id
                """
                
                cohorts = {}
                for row in conn.execute(query):
                    cohort = row['cohort']
                    if cohort not in cohorts:
                        cohorts[cohort] = set()
                    cohorts[cohort].add(row['session_id'])
                
                # Calculate retention for each cohort
                cohort_stats = []
                for cohort, sessions in sorted(cohorts.items()):
                    # Count how many returned in subsequent periods
                    retention = {
                        'cohort': cohort,
                        'size': len(sessions),
                        'retention': {}
                    }
                    
                    # Check retention for next 4 periods
                    for i in range(1, 5):
                        # Count sessions that returned in period i
                        returned = 0
                        for session in sessions:
                            query = f"""
                            SELECT COUNT(*) as count
                            FROM events
                            WHERE session_id = ? 
                            AND strftime('{date_format}', created_at) > ?
                            LIMIT 1
                            """
                            result = conn.execute(query, (session, cohort)).fetchone()
                            if result['count'] > 0:
                                returned += 1
                        
                        retention['retention'][f'{period}_{i}'] = round(returned / len(sessions) * 100, 1) if sessions else 0
                    
                    cohort_stats.append(retention)
                
                return {
                    'period': period_name,
                    'cohorts': cohort_stats[-10:]  # Last 10 cohorts
                }
        except Exception as e:
            logger.error(f"Failed to get cohort analysis: {e}")
            return {}
    
    def get_user_segments(self, days: int = 7) -> Dict:
        """
        User segmentation by device, browser, location
        Parse user agent to extract device and browser info
        """
        try:
            since = datetime.now() - timedelta(days=days)
            
            with self._get_connection() as conn:
                # Get device distribution (simple parsing from user agent)
                devices = conn.execute(
                    """SELECT 
                        CASE 
                            WHEN user_agent LIKE '%Mobile%' THEN 'Mobile'
                            WHEN user_agent LIKE '%Tablet%' THEN 'Tablet'
                            ELSE 'Desktop'
                        END as device_type,
                        COUNT(DISTINCT session_id) as users
                    FROM events
                    WHERE created_at >= ?
                    GROUP BY device_type""",
                    (since.isoformat(),)
                ).fetchall()
                
                # Get browser distribution
                browsers = conn.execute(
                    """SELECT 
                        CASE 
                            WHEN user_agent LIKE '%Chrome%' AND user_agent NOT LIKE '%Edg%' THEN 'Chrome'
                            WHEN user_agent LIKE '%Safari%' AND user_agent NOT LIKE '%Chrome%' THEN 'Safari'
                            WHEN user_agent LIKE '%Firefox%' THEN 'Firefox'
                            WHEN user_agent LIKE '%Edg%' THEN 'Edge'
                            ELSE 'Other'
                        END as browser,
                        COUNT(DISTINCT session_id) as users
                    FROM events
                    WHERE created_at >= ?
                    GROUP BY browser""",
                    (since.isoformat(),)
                ).fetchall()
                
                # Get most active sessions (power users)
                power_users = conn.execute(
                    """SELECT 
                        session_id,
                        COUNT(*) as event_count,
                        MIN(created_at) as first_seen,
                        MAX(created_at) as last_seen
                    FROM events
                    WHERE created_at >= ?
                    GROUP BY session_id
                    HAVING event_count > 10
                    ORDER BY event_count DESC
                    LIMIT 10""",
                    (since.isoformat(),)
                ).fetchall()
                
                return {
                    'period_days': days,
                    'devices': [dict(row) for row in devices],
                    'browsers': [dict(row) for row in browsers],
                    'power_users': [
                        {
                            'session_id': row['session_id'],
                            'events': row['event_count'],
                            'duration_hours': round((
                                datetime.fromisoformat(row['last_seen']) - 
                                datetime.fromisoformat(row['first_seen'])
                            ).total_seconds() / 3600, 2)
                        } for row in power_users
                    ]
                }
        except Exception as e:
            logger.error(f"Failed to get user segments: {e}")
            return {}
    
    def get_realtime_stats(self) -> Dict:
        """
        Real-time analytics (last 5 minutes)
        Shows active users, current events, recent errors
        """
        try:
            five_min_ago = datetime.now() - timedelta(minutes=5)
            
            with self._get_connection() as conn:
                # Active users (unique sessions in last 5 min)
                active_users = conn.execute(
                    "SELECT COUNT(DISTINCT session_id) FROM events WHERE created_at >= ?",
                    (five_min_ago.isoformat(),)
                ).fetchone()[0]
                
                # Recent events by type
                recent_events = conn.execute(
                    """SELECT event_type, COUNT(*) as count
                    FROM events
                    WHERE created_at >= ?
                    GROUP BY event_type""",
                    (five_min_ago.isoformat(),)
                ).fetchall()
                
                # Recent errors
                recent_errors = conn.execute(
                    """SELECT error_message, COUNT(*) as count
                    FROM errors
                    WHERE created_at >= ?
                    GROUP BY error_message
                    ORDER BY count DESC
                    LIMIT 5""",
                    (five_min_ago.isoformat(),)
                ).fetchall()
                
                # Current page views
                current_pages = conn.execute(
                    """SELECT page_name, COUNT(*) as views
                    FROM page_views
                    WHERE created_at >= ?
                    GROUP BY page_name
                    ORDER BY views DESC""",
                    (five_min_ago.isoformat(),)
                ).fetchall()
                
                return {
                    'timestamp': datetime.now().isoformat(),
                    'active_users_5min': active_users,
                    'events_by_type': {row['event_type']: row['count'] for row in recent_events},
                    'recent_errors': [dict(row) for row in recent_errors],
                    'current_pages': [dict(row) for row in current_pages],
                    'refresh_interval_seconds': 30
                }
        except Exception as e:
            logger.error(f"Failed to get realtime stats: {e}")
            return {}
    
    def export_data(self, days: int = 7, event_type: Optional[str] = None, format_type: str = 'json') -> any:
        """
        Export analytics data for external analysis
        Supports JSON and CSV formats
        """
        try:
            since = datetime.now() - timedelta(days=days)
            
            with self._get_connection() as conn:
                query = "SELECT * FROM events WHERE created_at >= ?"
                params = [since.isoformat()]
                
                if event_type:
                    query += " AND event_type = ?"
                    params.append(event_type)
                
                query += " ORDER BY created_at DESC LIMIT 10000"
                
                rows = conn.execute(query, params).fetchall()
                data = [dict(row) for row in rows]
                
                if format_type == 'csv':
                    # Convert to CSV
                    import csv
                    import io
                    
                    output = io.StringIO()
                    if data:
                        writer = csv.DictWriter(output, fieldnames=data[0].keys())
                        writer.writeheader()
                        writer.writerows(data)
                    
                    return output.getvalue()
                else:
                    return {
                        'period_days': days,
                        'event_type_filter': event_type,
                        'total_events': len(data),
                        'events': data[:1000]  # Limit to 1000 for JSON
                    }
        except Exception as e:
            logger.error(f"Failed to export data: {e}")
            return {} if format_type == 'json' else ""
    
    def get_user_journey(self, user_id: str) -> Dict:
        """
        Get complete user journey across all sessions
        Shows chronological events, session count, engagement metrics
        """
        try:
            with self._get_connection() as conn:
                # Get all events for this user
                events = conn.execute(
                    """SELECT event_type, event_data, session_id, created_at
                    FROM events
                    WHERE user_id = ?
                    ORDER BY created_at ASC""",
                    (user_id,)
                ).fetchall()
                
                if not events:
                    return {'error': 'User not found', 'user_id': user_id}
                
                # Calculate metrics
                sessions = set(e['session_id'] for e in events)
                first_seen = events[0]['created_at']
                last_seen = events[-1]['created_at']
                
                # Parse first and last seen
                first_dt = datetime.fromisoformat(first_seen)
                last_dt = datetime.fromisoformat(last_seen)
                days_active = (last_dt - first_dt).days + 1
                
                # Event counts by type
                event_counts = {}
                for event in events:
                    et = event['event_type']
                    event_counts[et] = event_counts.get(et, 0) + 1
                
                return {
                    'user_id': user_id,
                    'total_events': len(events),
                    'total_sessions': len(sessions),
                    'first_seen': first_seen,
                    'last_seen': last_seen,
                    'days_active': days_active,
                    'events_per_session': round(len(events) / len(sessions), 2),
                    'event_counts': event_counts,
                    'journey': [
                        {
                            'event_type': e['event_type'],
                            'session_id': e['session_id'],
                            'timestamp': e['created_at'],
                            'data': json.loads(e['event_data']) if e['event_data'] else {}
                        } for e in events[-100:]  # Last 100 events
                    ]
                }
        except Exception as e:
            logger.error(f"Failed to get user journey: {e}")
            return {}

    def update_progress(self, user_id: str, topic: str, subtopic: str, mastery_level: int):
        """Update user mastery level for a subtopic"""
        try:
            with self._get_connection() as conn:
                conn.execute(
                    '''INSERT INTO user_progress (user_id, topic, subtopic, mastery_level, last_accessed)
                       VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                       ON CONFLICT(user_id, topic, subtopic) 
                       DO UPDATE SET mastery_level = ?, last_accessed = CURRENT_TIMESTAMP''',
                    (user_id, topic, subtopic, mastery_level, mastery_level)
                )
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to update progress: {e}")

    def get_user_progress(self, user_id: str, topic: str = None) -> List[Dict]:
        """Get user progress, optionally filtered by topic"""
        try:
            with self._get_connection() as conn:
                query = "SELECT * FROM user_progress WHERE user_id = ?"
                params = [user_id]
                
                if topic:
                    query += " AND topic = ?"
                    params.append(topic)
                
                rows = conn.execute(query, params).fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Failed to get user progress: {e}")
            return []

    def save_quiz_result(self, user_id: str, topic: str, score: int, total: int, difficulty: str):
        """Save quiz result"""
        try:
            with self._get_connection() as conn:
                conn.execute(
                    '''INSERT INTO quiz_results (user_id, topic, score, total_questions, difficulty_level)
                       VALUES (?, ?, ?, ?, ?)''',
                    (user_id, topic, score, total, difficulty)
                )
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to save quiz result: {e}")

    def get_quiz_history(self, user_id: str, topic: str = None) -> List[Dict]:
        """Get quiz history"""
        try:
            with self._get_connection() as conn:
                query = "SELECT * FROM quiz_results WHERE user_id = ?"
                params = [user_id]
                
                if topic:
                    query += " AND topic = ?"
                    params.append(topic)
                
                query += " ORDER BY created_at DESC"
                
                rows = conn.execute(query, params).fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Failed to get quiz history: {e}")
            return []

# Global instance
analytics_db = AnalyticsDB()
