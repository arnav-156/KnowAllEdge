"""
Gamification Database Manager
Handles achievements, streaks, leaderboards, challenges, and skill trees
"""
import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class GamificationDB:
    def __init__(self, db_path: str = 'gamification.db'):
        self.db_path = db_path
        self.init_db()
    
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_db(self):
        """Initialize gamification database tables"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # User progress table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_progress (
                user_id TEXT PRIMARY KEY,
                total_xp INTEGER DEFAULT 0,
                level INTEGER DEFAULT 1,
                streak_days INTEGER DEFAULT 0,
                last_activity_date TEXT,
                total_topics_completed INTEGER DEFAULT 0,
                total_quizzes_completed INTEGER DEFAULT 0,
                total_time_spent INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Achievements table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS achievements (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                category TEXT,
                icon TEXT,
                xp_reward INTEGER DEFAULT 0,
                requirement_type TEXT,
                requirement_value INTEGER,
                is_secret BOOLEAN DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # User achievements table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_achievements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                achievement_id TEXT NOT NULL,
                unlocked_at TEXT DEFAULT CURRENT_TIMESTAMP,
                progress INTEGER DEFAULT 0,
                FOREIGN KEY (achievement_id) REFERENCES achievements(id),
                UNIQUE(user_id, achievement_id)
            )
        ''')
        
        # Skill tree table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS skill_tree (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                category TEXT,
                parent_skill_id TEXT,
                xp_cost INTEGER DEFAULT 0,
                level_required INTEGER DEFAULT 1,
                icon TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # User skills table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_skills (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                skill_id TEXT NOT NULL,
                unlocked_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (skill_id) REFERENCES skill_tree(id),
                UNIQUE(user_id, skill_id)
            )
        ''')
        
        # Challenges table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS challenges (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                type TEXT,
                difficulty TEXT,
                time_limit INTEGER,
                xp_reward INTEGER DEFAULT 0,
                requirements TEXT,
                is_active BOOLEAN DEFAULT 1,
                start_date TEXT,
                end_date TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # User challenges table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_challenges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                challenge_id TEXT NOT NULL,
                status TEXT DEFAULT 'active',
                progress INTEGER DEFAULT 0,
                started_at TEXT DEFAULT CURRENT_TIMESTAMP,
                completed_at TEXT,
                score INTEGER DEFAULT 0,
                FOREIGN KEY (challenge_id) REFERENCES challenges(id),
                UNIQUE(user_id, challenge_id)
            )
        ''')

        # Leaderboard table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS leaderboard (
                user_id TEXT PRIMARY KEY,
                username TEXT,
                total_xp INTEGER DEFAULT 0,
                level INTEGER DEFAULT 1,
                rank INTEGER,
                achievements_count INTEGER DEFAULT 0,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        
        # Initialize default achievements
        self._init_default_achievements()
        self._init_default_skill_tree()
        self._init_default_challenges()
    
    def _init_default_achievements(self):
        """Initialize default achievement badges"""
        default_achievements = [
            {
                'id': 'first_steps',
                'name': 'First Steps',
                'description': 'Complete your first topic',
                'category': 'beginner',
                'icon': '🎯',
                'xp_reward': 50,
                'requirement_type': 'topics_completed',
                'requirement_value': 1
            },
            {
                'id': 'knowledge_seeker',
                'name': 'Knowledge Seeker',
                'description': 'Complete 10 topics',
                'category': 'learning',
                'icon': '📚',
                'xp_reward': 200,
                'requirement_type': 'topics_completed',
                'requirement_value': 10
            },
            {
                'id': 'master_learner',
                'name': 'Master Learner',
                'description': 'Complete 50 topics',
                'category': 'learning',
                'icon': '🏆',
                'xp_reward': 1000,
                'requirement_type': 'topics_completed',
                'requirement_value': 50
            },
            {
                'id': 'quiz_master',
                'name': 'Quiz Master',
                'description': 'Complete 25 quizzes',
                'category': 'quiz',
                'icon': '🎓',
                'xp_reward': 500,
                'requirement_type': 'quizzes_completed',
                'requirement_value': 25
            },
            {
                'id': 'streak_warrior',
                'name': 'Streak Warrior',
                'description': 'Maintain a 7-day learning streak',
                'category': 'streak',
                'icon': '🔥',
                'xp_reward': 300,
                'requirement_type': 'streak_days',
                'requirement_value': 7
            },
            {
                'id': 'streak_legend',
                'name': 'Streak Legend',
                'description': 'Maintain a 30-day learning streak',
                'category': 'streak',
                'icon': '⚡',
                'xp_reward': 1500,
                'requirement_type': 'streak_days',
                'requirement_value': 30
            },
            {
                'id': 'speed_demon',
                'name': 'Speed Demon',
                'description': 'Complete a challenge in under 5 minutes',
                'category': 'challenge',
                'icon': '⚡',
                'xp_reward': 250,
                'requirement_type': 'challenge_time',
                'requirement_value': 300
            },
            {
                'id': 'explorer',
                'name': 'Explorer',
                'description': 'Explore 5 different topic categories',
                'category': 'exploration',
                'icon': '🗺️',
                'xp_reward': 400,
                'requirement_type': 'categories_explored',
                'requirement_value': 5
            },
            {
                'id': 'night_owl',
                'name': 'Night Owl',
                'description': 'Complete a topic after midnight',
                'category': 'special',
                'icon': '🦉',
                'xp_reward': 100,
                'requirement_type': 'special',
                'requirement_value': 1,
                'is_secret': True
            }
        ]
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        for achievement in default_achievements:
            cursor.execute('''
                INSERT OR IGNORE INTO achievements 
                (id, name, description, category, icon, xp_reward, requirement_type, requirement_value, is_secret)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                achievement['id'], achievement['name'], achievement['description'],
                achievement['category'], achievement['icon'], achievement['xp_reward'],
                achievement['requirement_type'], achievement['requirement_value'],
                achievement.get('is_secret', False)
            ))
        
        conn.commit()
        conn.close()

    def _init_default_skill_tree(self):
        """Initialize default skill tree"""
        default_skills = [
            {'id': 'beginner_learner', 'name': 'Beginner Learner', 'description': 'Start your learning journey', 
             'category': 'foundation', 'parent_skill_id': None, 'xp_cost': 0, 'level_required': 1, 'icon': '🌱'},
            {'id': 'active_reader', 'name': 'Active Reader', 'description': 'Unlock advanced reading features', 
             'category': 'foundation', 'parent_skill_id': 'beginner_learner', 'xp_cost': 100, 'level_required': 2, 'icon': '📖'},
            {'id': 'quiz_taker', 'name': 'Quiz Taker', 'description': 'Unlock quiz features', 
             'category': 'assessment', 'parent_skill_id': 'beginner_learner', 'xp_cost': 150, 'level_required': 2, 'icon': '✍️'},
            {'id': 'speed_learner', 'name': 'Speed Learner', 'description': 'Unlock timed challenges', 
             'category': 'advanced', 'parent_skill_id': 'active_reader', 'xp_cost': 300, 'level_required': 5, 'icon': '⚡'},
            {'id': 'master_quizzer', 'name': 'Master Quizzer', 'description': 'Unlock advanced quiz modes', 
             'category': 'assessment', 'parent_skill_id': 'quiz_taker', 'xp_cost': 400, 'level_required': 5, 'icon': '🎯'},
            {'id': 'knowledge_architect', 'name': 'Knowledge Architect', 'description': 'Create custom learning paths', 
             'category': 'mastery', 'parent_skill_id': 'speed_learner', 'xp_cost': 800, 'level_required': 10, 'icon': '🏗️'},
        ]
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        for skill in default_skills:
            cursor.execute('''
                INSERT OR IGNORE INTO skill_tree 
                (id, name, description, category, parent_skill_id, xp_cost, level_required, icon)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (skill['id'], skill['name'], skill['description'], skill['category'],
                  skill['parent_skill_id'], skill['xp_cost'], skill['level_required'], skill['icon']))
        
        conn.commit()
        conn.close()

    def _init_default_challenges(self):
        """Initialize default challenges"""
        default_challenges = [
            {
                'id': 'speed_quiz_5min',
                'name': '5-Minute Speed Quiz',
                'description': 'Complete 10 questions in 5 minutes',
                'type': 'timed_quiz',
                'difficulty': 'medium',
                'time_limit': 300,
                'xp_reward': 200,
                'requirements': json.dumps({'questions': 10, 'time_limit': 300})
            },
            {
                'id': 'daily_explorer',
                'name': 'Daily Explorer',
                'description': 'Explore 3 new topics today',
                'type': 'exploration',
                'difficulty': 'easy',
                'time_limit': 86400,
                'xp_reward': 150,
                'requirements': json.dumps({'topics': 3, 'timeframe': 'daily'})
            },
            {
                'id': 'perfect_score',
                'name': 'Perfect Score',
                'description': 'Get 100% on any quiz',
                'type': 'achievement',
                'difficulty': 'hard',
                'time_limit': None,
                'xp_reward': 500,
                'requirements': json.dumps({'score': 100})
            }
        ]
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        for challenge in default_challenges:
            cursor.execute('''
                INSERT OR IGNORE INTO challenges 
                (id, name, description, type, difficulty, time_limit, xp_reward, requirements, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
            ''', (challenge['id'], challenge['name'], challenge['description'], challenge['type'],
                  challenge['difficulty'], challenge['time_limit'], challenge['xp_reward'], 
                  challenge['requirements']))
        
        conn.commit()
        conn.close()

    # User Progress Methods
    def get_user_progress(self, user_id: str) -> Optional[Dict]:
        """Get user's gamification progress"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM user_progress WHERE user_id = ?', (user_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return dict(row)
        return None
    
    def create_user_progress(self, user_id: str) -> Dict:
        """Create initial progress for a new user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR IGNORE INTO user_progress (user_id, last_activity_date)
            VALUES (?, ?)
        ''', (user_id, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        
        return self.get_user_progress(user_id)
    
    def update_user_activity(self, user_id: str) -> Dict:
        """Update user activity and check streak"""
        progress = self.get_user_progress(user_id)
        if not progress:
            progress = self.create_user_progress(user_id)
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        today = datetime.now().date()
        last_activity = datetime.fromisoformat(progress['last_activity_date']).date() if progress['last_activity_date'] else None
        
        # Update streak
        if last_activity:
            days_diff = (today - last_activity).days
            if days_diff == 1:
                # Continue streak
                new_streak = progress['streak_days'] + 1
            elif days_diff == 0:
                # Same day
                new_streak = progress['streak_days']
            else:
                # Streak broken
                new_streak = 1
        else:
            new_streak = 1

        cursor.execute('''
            UPDATE user_progress 
            SET streak_days = ?, last_activity_date = ?, updated_at = ?
            WHERE user_id = ?
        ''', (new_streak, datetime.now().isoformat(), datetime.now().isoformat(), user_id))
        
        conn.commit()
        conn.close()
        
        # Check for streak achievements
        self._check_achievements(user_id, 'streak_days', new_streak)
        
        return self.get_user_progress(user_id)
    
    def add_xp(self, user_id: str, xp_amount: int) -> Dict:
        """Add XP to user and level up if needed"""
        progress = self.get_user_progress(user_id) or self.create_user_progress(user_id)
        
        new_xp = progress['total_xp'] + xp_amount
        new_level = self._calculate_level(new_xp)
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE user_progress 
            SET total_xp = ?, level = ?, updated_at = ?
            WHERE user_id = ?
        ''', (new_xp, new_level, datetime.now().isoformat(), user_id))
        
        conn.commit()
        conn.close()
        
        # Update leaderboard
        self._update_leaderboard(user_id)
        
        return self.get_user_progress(user_id)
    
    def _calculate_level(self, xp: int) -> int:
        """Calculate level based on XP (100 XP per level, exponential growth)"""
        return int((xp / 100) ** 0.5) + 1
    
    def record_topic_completion(self, user_id: str, topic_id: str, time_spent: int = 0) -> Dict:
        """Record topic completion and award XP"""
        progress = self.get_user_progress(user_id) or self.create_user_progress(user_id)
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        new_topics = progress['total_topics_completed'] + 1
        new_time = progress['total_time_spent'] + time_spent

        cursor.execute('''
            UPDATE user_progress 
            SET total_topics_completed = ?, total_time_spent = ?, updated_at = ?
            WHERE user_id = ?
        ''', (new_topics, new_time, datetime.now().isoformat(), user_id))
        
        conn.commit()
        conn.close()
        
        # Award XP
        self.add_xp(user_id, 50)
        
        # Update activity and streak
        self.update_user_activity(user_id)
        
        # Check achievements
        self._check_achievements(user_id, 'topics_completed', new_topics)
        
        return self.get_user_progress(user_id)
    
    def record_quiz_completion(self, user_id: str, quiz_id: str, score: int, time_taken: int = 0) -> Dict:
        """Record quiz completion and award XP based on score"""
        progress = self.get_user_progress(user_id) or self.create_user_progress(user_id)
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        new_quizzes = progress['total_quizzes_completed'] + 1
        
        cursor.execute('''
            UPDATE user_progress 
            SET total_quizzes_completed = ?, updated_at = ?
            WHERE user_id = ?
        ''', (new_quizzes, datetime.now().isoformat(), user_id))
        
        conn.commit()
        conn.close()
        
        # Award XP based on score
        xp_reward = int(score * 2)  # 2 XP per percentage point
        self.add_xp(user_id, xp_reward)
        
        # Check for perfect score achievement
        if score == 100:
            self._check_achievements(user_id, 'perfect_score', 1)
        
        # Check quiz achievements
        self._check_achievements(user_id, 'quizzes_completed', new_quizzes)
        
        return self.get_user_progress(user_id)

    # Achievement Methods
    def get_all_achievements(self, include_secret: bool = False) -> List[Dict]:
        """Get all achievements"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if include_secret:
            cursor.execute('SELECT * FROM achievements ORDER BY category, xp_reward')
        else:
            cursor.execute('SELECT * FROM achievements WHERE is_secret = 0 ORDER BY category, xp_reward')
        
        achievements = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return achievements
    
    def get_user_achievements(self, user_id: str) -> List[Dict]:
        """Get user's unlocked achievements"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT a.*, ua.unlocked_at, ua.progress
            FROM achievements a
            JOIN user_achievements ua ON a.id = ua.achievement_id
            WHERE ua.user_id = ?
            ORDER BY ua.unlocked_at DESC
        ''', (user_id,))
        
        achievements = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return achievements
    
    def unlock_achievement(self, user_id: str, achievement_id: str) -> bool:
        """Unlock an achievement for a user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO user_achievements (user_id, achievement_id, progress)
                VALUES (?, ?, 100)
            ''', (user_id, achievement_id))
            
            # Get achievement XP reward
            cursor.execute('SELECT xp_reward FROM achievements WHERE id = ?', (achievement_id,))
            row = cursor.fetchone()
            
            conn.commit()
            conn.close()
            
            if row:
                self.add_xp(user_id, row['xp_reward'])
            
            return True
        except sqlite3.IntegrityError:
            conn.close()
            return False

    def _check_achievements(self, user_id: str, requirement_type: str, current_value: int):
        """Check and unlock achievements based on progress"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id FROM achievements 
            WHERE requirement_type = ? AND requirement_value <= ?
            AND id NOT IN (SELECT achievement_id FROM user_achievements WHERE user_id = ?)
        ''', (requirement_type, current_value, user_id))
        
        achievements_to_unlock = [row['id'] for row in cursor.fetchall()]
        conn.close()
        
        for achievement_id in achievements_to_unlock:
            self.unlock_achievement(user_id, achievement_id)
    
    # Skill Tree Methods
    def get_skill_tree(self) -> List[Dict]:
        """Get complete skill tree"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM skill_tree ORDER BY level_required, xp_cost')
        skills = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return skills
    
    def get_user_skills(self, user_id: str) -> List[Dict]:
        """Get user's unlocked skills"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT s.*, us.unlocked_at
            FROM skill_tree s
            JOIN user_skills us ON s.id = us.skill_id
            WHERE us.user_id = ?
            ORDER BY us.unlocked_at
        ''', (user_id,))
        
        skills = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return skills
    
    def unlock_skill(self, user_id: str, skill_id: str) -> Dict:
        """Unlock a skill if requirements are met"""
        progress = self.get_user_progress(user_id)
        if not progress:
            return {'success': False, 'error': 'User not found'}

        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Get skill requirements
        cursor.execute('SELECT * FROM skill_tree WHERE id = ?', (skill_id,))
        skill = cursor.fetchone()
        
        if not skill:
            conn.close()
            return {'success': False, 'error': 'Skill not found'}
        
        # Check level requirement
        if progress['level'] < skill['level_required']:
            conn.close()
            return {'success': False, 'error': f"Level {skill['level_required']} required"}
        
        # Check XP cost
        if progress['total_xp'] < skill['xp_cost']:
            conn.close()
            return {'success': False, 'error': f"{skill['xp_cost']} XP required"}
        
        # Check parent skill
        if skill['parent_skill_id']:
            cursor.execute('''
                SELECT COUNT(*) as count FROM user_skills 
                WHERE user_id = ? AND skill_id = ?
            ''', (user_id, skill['parent_skill_id']))
            
            if cursor.fetchone()['count'] == 0:
                conn.close()
                return {'success': False, 'error': 'Parent skill required'}
        
        # Unlock skill
        try:
            cursor.execute('''
                INSERT INTO user_skills (user_id, skill_id)
                VALUES (?, ?)
            ''', (user_id, skill_id))
            
            conn.commit()
            conn.close()
            
            return {'success': True, 'skill': dict(skill)}
        except sqlite3.IntegrityError:
            conn.close()
            return {'success': False, 'error': 'Skill already unlocked'}

    # Challenge Methods
    def get_active_challenges(self) -> List[Dict]:
        """Get all active challenges"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM challenges 
            WHERE is_active = 1
            ORDER BY difficulty, xp_reward DESC
        ''')
        
        challenges = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return challenges
    
    def get_user_challenges(self, user_id: str) -> List[Dict]:
        """Get user's active and completed challenges"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT c.*, uc.status, uc.progress, uc.started_at, uc.completed_at, uc.score
            FROM challenges c
            JOIN user_challenges uc ON c.id = uc.challenge_id
            WHERE uc.user_id = ?
            ORDER BY uc.started_at DESC
        ''', (user_id,))
        
        challenges = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return challenges
    
    def start_challenge(self, user_id: str, challenge_id: str) -> Dict:
        """Start a challenge for a user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO user_challenges (user_id, challenge_id, status)
                VALUES (?, ?, 'active')
            ''', (user_id, challenge_id))
            
            conn.commit()
            conn.close()
            
            return {'success': True, 'message': 'Challenge started'}
        except sqlite3.IntegrityError:
            conn.close()
            return {'success': False, 'error': 'Challenge already started'}

    def complete_challenge(self, user_id: str, challenge_id: str, score: int = 100) -> Dict:
        """Complete a challenge and award XP"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Get challenge
        cursor.execute('SELECT * FROM challenges WHERE id = ?', (challenge_id,))
        challenge = cursor.fetchone()
        
        if not challenge:
            conn.close()
            return {'success': False, 'error': 'Challenge not found'}
        
        # Update challenge status
        cursor.execute('''
            UPDATE user_challenges 
            SET status = 'completed', completed_at = ?, score = ?, progress = 100
            WHERE user_id = ? AND challenge_id = ?
        ''', (datetime.now().isoformat(), score, user_id, challenge_id))
        
        conn.commit()
        conn.close()
        
        # Award XP
        xp_reward = int(challenge['xp_reward'] * (score / 100))
        self.add_xp(user_id, xp_reward)
        
        return {'success': True, 'xp_earned': xp_reward}
    
    # Leaderboard Methods
    def get_leaderboard(self, limit: int = 100) -> List[Dict]:
        """Get top users on leaderboard"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT user_id, username, total_xp, level, achievements_count, updated_at,
                   ROW_NUMBER() OVER (ORDER BY total_xp DESC) as rank
            FROM leaderboard
            ORDER BY total_xp DESC
            LIMIT ?
        ''', (limit,))
        
        leaderboard = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return leaderboard
    
    def get_user_rank(self, user_id: str) -> Optional[Dict]:
        """Get user's rank on leaderboard"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            WITH ranked_users AS (
                SELECT user_id, username, total_xp, level, achievements_count,
                       ROW_NUMBER() OVER (ORDER BY total_xp DESC) as rank
                FROM leaderboard
            )
            SELECT * FROM ranked_users WHERE user_id = ?
        ''', (user_id,))
        
        rank = cursor.fetchone()
        conn.close()
        
        return dict(rank) if rank else None
    
    def _update_leaderboard(self, user_id: str):
        """Update user's leaderboard entry"""
        progress = self.get_user_progress(user_id)
        if not progress:
            return
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Get achievements count
        cursor.execute('SELECT COUNT(*) as count FROM user_achievements WHERE user_id = ?', (user_id,))
        achievements_count = cursor.fetchone()['count']
        
        # Update or insert leaderboard entry
        cursor.execute('''
            INSERT INTO leaderboard (user_id, username, total_xp, level, achievements_count, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                total_xp = excluded.total_xp,
                level = excluded.level,
                achievements_count = excluded.achievements_count,
                updated_at = excluded.updated_at
        ''', (user_id, user_id, progress['total_xp'], progress['level'], 
              achievements_count, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
