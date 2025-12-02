"""
Learning Analytics Database Manager
Tracks learning patterns, performance, and generates insights
"""
import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
from collections import defaultdict
import statistics

logger = logging.getLogger(__name__)

class LearningAnalyticsDB:
    def __init__(self, db_path: str = 'learning_analytics.db'):
        self.db_path = db_path
        self.init_db()
    
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_db(self):
        """Initialize learning analytics database tables"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Learning sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS learning_sessions (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                topic_id TEXT NOT NULL,
                subtopic_id TEXT,
                session_start TEXT NOT NULL,
                session_end TEXT,
                duration_seconds INTEGER,
                concepts_covered TEXT,
                activities TEXT,
                focus_score REAL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Performance records table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS performance_records (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                topic_id TEXT NOT NULL,
                assessment_type TEXT,
                score REAL NOT NULL,
                max_score REAL NOT NULL,
                time_taken INTEGER,
                questions_correct INTEGER,
                questions_total INTEGER,
                difficulty_level TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Concept mastery table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS concept_mastery (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                concept_id TEXT NOT NULL,
                topic_id TEXT,
                mastery_level REAL DEFAULT 0.0,
                attempts INTEGER DEFAULT 0,
                correct_attempts INTEGER DEFAULT 0,
                last_practiced TEXT,
                confidence_score REAL DEFAULT 0.0,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, concept_id)
            )
        ''')

        # Study patterns table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS study_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                day_of_week INTEGER,
                hour_of_day INTEGER,
                session_count INTEGER DEFAULT 0,
                total_duration INTEGER DEFAULT 0,
                avg_performance REAL DEFAULT 0.0,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, day_of_week, hour_of_day)
            )
        ''')
        
        # Knowledge gaps table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS knowledge_gaps (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                topic_id TEXT NOT NULL,
                concept_id TEXT,
                gap_type TEXT,
                severity TEXT,
                description TEXT,
                recommendations TEXT,
                identified_at TEXT DEFAULT CURRENT_TIMESTAMP,
                resolved BOOLEAN DEFAULT 0
            )
        ''')
        
        # Predictive insights table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS predictive_insights (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                topic_id TEXT,
                insight_type TEXT,
                prediction_score REAL,
                confidence_level REAL,
                factors TEXT,
                recommendations TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                expires_at TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    # Learning Session Methods
    def start_session(self, user_id: str, topic_id: str, subtopic_id: str = None) -> str:
        """Start a learning session"""
        import uuid
        
        session_id = str(uuid.uuid4())
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO learning_sessions 
            (id, user_id, topic_id, subtopic_id, session_start)
            VALUES (?, ?, ?, ?, ?)
        ''', (session_id, user_id, topic_id, subtopic_id, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        
        return session_id
    
    def end_session(self, session_id: str, concepts_covered: List[str] = None, 
                    activities: List[str] = None, focus_score: float = None) -> Dict:
        """End a learning session"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT session_start FROM learning_sessions WHERE id = ?', (session_id,))
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            return {'error': 'Session not found'}
        
        start_time = datetime.fromisoformat(row['session_start'])
        end_time = datetime.now()
        duration = int((end_time - start_time).total_seconds())
        
        cursor.execute('''
            UPDATE learning_sessions 
            SET session_end = ?, duration_seconds = ?, concepts_covered = ?, 
                activities = ?, focus_score = ?
            WHERE id = ?
        ''', (
            end_time.isoformat(), duration, 
            json.dumps(concepts_covered or []),
            json.dumps(activities or []),
            focus_score, session_id
        ))
        
        conn.commit()
        conn.close()
        
        # Update study patterns
        self._update_study_patterns(session_id)
        
        return {'session_id': session_id, 'duration': duration}

    def get_user_sessions(self, user_id: str, days: int = 30) -> List[Dict]:
        """Get user's learning sessions"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        cursor.execute('''
            SELECT * FROM learning_sessions 
            WHERE user_id = ? AND session_start >= ?
            ORDER BY session_start DESC
        ''', (user_id, cutoff_date))
        
        sessions = []
        for row in cursor.fetchall():
            session = dict(row)
            session['concepts_covered'] = json.loads(session['concepts_covered']) if session['concepts_covered'] else []
            session['activities'] = json.loads(session['activities']) if session['activities'] else []
            sessions.append(session)
        
        conn.close()
        return sessions
    
    # Performance Methods
    def record_performance(self, user_id: str, performance_data: Dict) -> Dict:
        """Record a performance assessment"""
        import uuid
        
        record_id = str(uuid.uuid4())
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO performance_records 
            (id, user_id, topic_id, assessment_type, score, max_score, 
             time_taken, questions_correct, questions_total, difficulty_level)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            record_id, user_id, performance_data['topic_id'],
            performance_data.get('assessment_type', 'quiz'),
            performance_data['score'], performance_data['max_score'],
            performance_data.get('time_taken'), 
            performance_data.get('questions_correct'),
            performance_data.get('questions_total'),
            performance_data.get('difficulty_level', 'medium')
        ))
        
        conn.commit()
        conn.close()
        
        # Update concept mastery
        if performance_data.get('concepts'):
            self._update_concept_mastery(user_id, performance_data)
        
        # Check for knowledge gaps
        self._detect_knowledge_gaps(user_id, performance_data)
        
        return {'record_id': record_id}
    
    def get_performance_history(self, user_id: str, topic_id: str = None, days: int = 90) -> List[Dict]:
        """Get performance history"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        if topic_id:
            cursor.execute('''
                SELECT * FROM performance_records 
                WHERE user_id = ? AND topic_id = ? AND created_at >= ?
                ORDER BY created_at DESC
            ''', (user_id, topic_id, cutoff_date))
        else:
            cursor.execute('''
                SELECT * FROM performance_records 
                WHERE user_id = ? AND created_at >= ?
                ORDER BY created_at DESC
            ''', (user_id, cutoff_date))
        
        records = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return records

    # Concept Mastery Methods
    def _update_concept_mastery(self, user_id: str, performance_data: Dict):
        """Update concept mastery based on performance"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        concepts = performance_data.get('concepts', [])
        score_percentage = (performance_data['score'] / performance_data['max_score']) * 100
        
        for concept in concepts:
            cursor.execute('''
                INSERT INTO concept_mastery 
                (user_id, concept_id, topic_id, mastery_level, attempts, 
                 correct_attempts, last_practiced, confidence_score)
                VALUES (?, ?, ?, ?, 1, ?, ?, ?)
                ON CONFLICT(user_id, concept_id) DO UPDATE SET
                    attempts = attempts + 1,
                    correct_attempts = correct_attempts + ?,
                    mastery_level = (mastery_level * 0.7) + (? * 0.3),
                    confidence_score = (confidence_score * 0.8) + (? * 0.2),
                    last_practiced = ?,
                    updated_at = ?
            ''', (
                user_id, concept['id'], performance_data['topic_id'],
                score_percentage, 1 if score_percentage >= 70 else 0,
                datetime.now().isoformat(), score_percentage,
                1 if score_percentage >= 70 else 0,
                score_percentage, score_percentage,
                datetime.now().isoformat(), datetime.now().isoformat()
            ))
        
        conn.commit()
        conn.close()
    
    def get_concept_mastery(self, user_id: str, topic_id: str = None) -> List[Dict]:
        """Get concept mastery levels"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if topic_id:
            cursor.execute('''
                SELECT * FROM concept_mastery 
                WHERE user_id = ? AND topic_id = ?
                ORDER BY mastery_level DESC
            ''', (user_id, topic_id))
        else:
            cursor.execute('''
                SELECT * FROM concept_mastery 
                WHERE user_id = ?
                ORDER BY mastery_level DESC
            ''', (user_id,))
        
        concepts = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return concepts
    
    # Study Pattern Methods
    def _update_study_patterns(self, session_id: str):
        """Update study patterns based on session"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM learning_sessions WHERE id = ?', (session_id,))
        session = cursor.fetchone()
        
        if not session or not session['session_end']:
            conn.close()
            return
        
        start_time = datetime.fromisoformat(session['session_start'])
        day_of_week = start_time.weekday()
        hour_of_day = start_time.hour
        
        cursor.execute('''
            INSERT INTO study_patterns 
            (user_id, day_of_week, hour_of_day, session_count, total_duration)
            VALUES (?, ?, ?, 1, ?)
            ON CONFLICT(user_id, day_of_week, hour_of_day) DO UPDATE SET
                session_count = session_count + 1,
                total_duration = total_duration + ?,
                updated_at = ?
        ''', (
            session['user_id'], day_of_week, hour_of_day,
            session['duration_seconds'], session['duration_seconds'],
            datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()
    
    def get_study_patterns(self, user_id: str) -> Dict:
        """Get user's study patterns"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM study_patterns 
            WHERE user_id = ?
            ORDER BY session_count DESC
        ''', (user_id,))
        
        patterns = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        # Analyze patterns
        analysis = self._analyze_study_patterns(patterns)
        
        return {
            'patterns': patterns,
            'analysis': analysis
        }
    
    def _analyze_study_patterns(self, patterns: List[Dict]) -> Dict:
        """Analyze study patterns to find optimal times"""
        if not patterns:
            return {}
        
        # Find best day of week
        day_totals = defaultdict(lambda: {'count': 0, 'duration': 0})
        for pattern in patterns:
            day = pattern['day_of_week']
            day_totals[day]['count'] += pattern['session_count']
            day_totals[day]['duration'] += pattern['total_duration']
        
        best_day = max(day_totals.items(), key=lambda x: x[1]['count'])[0] if day_totals else None
        
        # Find best hour of day
        hour_totals = defaultdict(lambda: {'count': 0, 'duration': 0})
        for pattern in patterns:
            hour = pattern['hour_of_day']
            hour_totals[hour]['count'] += pattern['session_count']
            hour_totals[hour]['duration'] += pattern['total_duration']
        
        best_hour = max(hour_totals.items(), key=lambda x: x[1]['count'])[0] if hour_totals else None
        
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
        return {
            'best_day': days[best_day] if best_day is not None else None,
            'best_hour': f"{best_hour}:00" if best_hour is not None else None,
            'total_sessions': sum(p['session_count'] for p in patterns),
            'total_study_time': sum(p['total_duration'] for p in patterns)
        }

    # Knowledge Gap Detection
    def _detect_knowledge_gaps(self, user_id: str, performance_data: Dict):
        """Detect knowledge gaps based on performance"""
        import uuid
        
        score_percentage = (performance_data['score'] / performance_data['max_score']) * 100
        
        # Identify gap if score is below 70%
        if score_percentage < 70:
            gap_id = str(uuid.uuid4())
            severity = 'high' if score_percentage < 50 else 'medium' if score_percentage < 60 else 'low'
            
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO knowledge_gaps 
                (id, user_id, topic_id, gap_type, severity, description, recommendations)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                gap_id, user_id, performance_data['topic_id'],
                'performance', severity,
                f"Low performance ({score_percentage:.1f}%) on {performance_data['topic_id']}",
                json.dumps([
                    "Review fundamental concepts",
                    "Practice with easier questions first",
                    "Seek additional resources or tutoring"
                ])
            ))
            
            conn.commit()
            conn.close()
    
    def get_knowledge_gaps(self, user_id: str, resolved: bool = False) -> List[Dict]:
        """Get identified knowledge gaps"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM knowledge_gaps 
            WHERE user_id = ? AND resolved = ?
            ORDER BY severity DESC, identified_at DESC
        ''', (user_id, 1 if resolved else 0))
        
        gaps = []
        for row in cursor.fetchall():
            gap = dict(row)
            gap['recommendations'] = json.loads(gap['recommendations']) if gap['recommendations'] else []
            gaps.append(gap)
        
        conn.close()
        return gaps
    
    def resolve_gap(self, gap_id: str) -> bool:
        """Mark a knowledge gap as resolved"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE knowledge_gaps 
            SET resolved = 1
            WHERE id = ?
        ''', (gap_id,))
        
        updated = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return updated
    
    # Predictive Performance
    def generate_predictive_insights(self, user_id: str, topic_id: str = None) -> Dict:
        """Generate predictive insights for exam readiness"""
        import uuid
        
        # Get recent performance
        performance = self.get_performance_history(user_id, topic_id, days=30)
        
        if not performance:
            return {
                'prediction_score': 0,
                'confidence_level': 0,
                'readiness': 'insufficient_data',
                'message': 'Not enough data to make predictions'
            }
        
        # Calculate metrics
        scores = [p['score'] / p['max_score'] * 100 for p in performance]
        avg_score = statistics.mean(scores)
        score_trend = self._calculate_trend(scores)
        consistency = 100 - statistics.stdev(scores) if len(scores) > 1 else 0
        
        # Get concept mastery
        concepts = self.get_concept_mastery(user_id, topic_id)
        avg_mastery = statistics.mean([c['mastery_level'] for c in concepts]) if concepts else 0
        
        # Calculate prediction score (0-100)
        prediction_score = (
            avg_score * 0.4 +
            avg_mastery * 0.3 +
            consistency * 0.2 +
            max(0, score_trend * 10) * 0.1
        )
        
        # Determine confidence level
        data_points = len(performance)
        confidence_level = min(100, (data_points / 10) * 100)
        
        # Determine readiness
        if prediction_score >= 85:
            readiness = 'excellent'
            message = 'You are well-prepared and ready for assessment'
        elif prediction_score >= 70:
            readiness = 'good'
            message = 'You are on track, continue practicing'
        elif prediction_score >= 60:
            readiness = 'fair'
            message = 'More practice needed in weak areas'
        else:
            readiness = 'needs_improvement'
            message = 'Significant study required before assessment'
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            avg_score, score_trend, consistency, avg_mastery
        )
        
        # Store insight
        insight_id = str(uuid.uuid4())
        conn = self.get_connection()
        cursor = conn.cursor()
        
        expires_at = (datetime.now() + timedelta(days=7)).isoformat()
        
        cursor.execute('''
            INSERT INTO predictive_insights 
            (id, user_id, topic_id, insight_type, prediction_score, 
             confidence_level, factors, recommendations, expires_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            insight_id, user_id, topic_id, 'exam_readiness',
            prediction_score, confidence_level,
            json.dumps({
                'avg_score': avg_score,
                'score_trend': score_trend,
                'consistency': consistency,
                'avg_mastery': avg_mastery
            }),
            json.dumps(recommendations),
            expires_at
        ))
        
        conn.commit()
        conn.close()
        
        return {
            'prediction_score': round(prediction_score, 1),
            'confidence_level': round(confidence_level, 1),
            'readiness': readiness,
            'message': message,
            'factors': {
                'average_score': round(avg_score, 1),
                'score_trend': round(score_trend, 2),
                'consistency': round(consistency, 1),
                'concept_mastery': round(avg_mastery, 1)
            },
            'recommendations': recommendations
        }
    
    def _calculate_trend(self, scores: List[float]) -> float:
        """Calculate trend in scores (positive = improving, negative = declining)"""
        if len(scores) < 2:
            return 0
        
        # Simple linear regression
        n = len(scores)
        x = list(range(n))
        x_mean = statistics.mean(x)
        y_mean = statistics.mean(scores)
        
        numerator = sum((x[i] - x_mean) * (scores[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return 0
        
        slope = numerator / denominator
        return slope
    
    def _generate_recommendations(self, avg_score: float, trend: float, 
                                  consistency: float, mastery: float) -> List[str]:
        """Generate personalized recommendations"""
        recommendations = []
        
        if avg_score < 70:
            recommendations.append("Focus on fundamental concepts - your average score needs improvement")
        
        if trend < 0:
            recommendations.append("Your scores are declining - take a break or change study methods")
        elif trend > 0:
            recommendations.append("Great progress! Your scores are improving - keep up the current approach")
        
        if consistency < 50:
            recommendations.append("Work on consistency - your performance varies significantly")
        
        if mastery < 60:
            recommendations.append("Practice more to improve concept mastery")
        
        if not recommendations:
            recommendations.append("Excellent work! Maintain your current study routine")
        
        return recommendations

    # Dashboard Analytics
    def get_dashboard_analytics(self, user_id: str, days: int = 30) -> Dict:
        """Get comprehensive analytics for dashboard"""
        
        # Time invested
        sessions = self.get_user_sessions(user_id, days)
        total_time = sum(s['duration_seconds'] for s in sessions if s['duration_seconds'])
        total_sessions = len(sessions)
        avg_session_time = total_time / total_sessions if total_sessions > 0 else 0
        
        # Concepts mastered
        concepts = self.get_concept_mastery(user_id)
        mastered_concepts = [c for c in concepts if c['mastery_level'] >= 80]
        in_progress_concepts = [c for c in concepts if 50 <= c['mastery_level'] < 80]
        weak_concepts = [c for c in concepts if c['mastery_level'] < 50]
        
        # Performance trends
        performance = self.get_performance_history(user_id, days=days)
        if performance:
            scores = [p['score'] / p['max_score'] * 100 for p in performance]
            avg_performance = statistics.mean(scores)
            performance_trend = self._calculate_trend(scores)
        else:
            avg_performance = 0
            performance_trend = 0
        
        # Study patterns
        patterns = self.get_study_patterns(user_id)
        
        # Knowledge gaps
        gaps = self.get_knowledge_gaps(user_id, resolved=False)
        
        # Recent activity
        recent_sessions = sessions[:10] if sessions else []
        recent_performance = performance[:10] if performance else []
        
        return {
            'time_invested': {
                'total_seconds': total_time,
                'total_hours': round(total_time / 3600, 1),
                'total_sessions': total_sessions,
                'avg_session_minutes': round(avg_session_time / 60, 1)
            },
            'concepts': {
                'mastered': len(mastered_concepts),
                'in_progress': len(in_progress_concepts),
                'weak': len(weak_concepts),
                'total': len(concepts),
                'mastery_percentage': round(len(mastered_concepts) / len(concepts) * 100, 1) if concepts else 0
            },
            'performance': {
                'average_score': round(avg_performance, 1),
                'trend': round(performance_trend, 2),
                'total_assessments': len(performance),
                'trend_direction': 'improving' if performance_trend > 0 else 'declining' if performance_trend < 0 else 'stable'
            },
            'study_patterns': patterns['analysis'],
            'knowledge_gaps': {
                'total': len(gaps),
                'high_severity': len([g for g in gaps if g['severity'] == 'high']),
                'medium_severity': len([g for g in gaps if g['severity'] == 'medium']),
                'low_severity': len([g for g in gaps if g['severity'] == 'low'])
            },
            'recent_activity': {
                'sessions': recent_sessions,
                'performance': recent_performance
            }
        }
