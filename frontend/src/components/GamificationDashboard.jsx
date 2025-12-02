import React, { useState, useEffect } from 'react';
import './GamificationDashboard.css';
import AchievementBadges from './AchievementBadges';
import StreakTracker from './StreakTracker';
import Leaderboard from './Leaderboard';
import SkillTree from './SkillTree';
import ChallengeMode from './ChallengeMode';

const GamificationDashboard = ({ userId }) => {
  const [activeTab, setActiveTab] = useState('overview');
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchStats();
  }, [userId]);

  const fetchStats = async () => {
    try {
      const response = await fetch(`/api/gamification/stats?user_id=${userId}`);
      const data = await response.json();
      if (data.success) {
        setStats(data.stats);
      }
    } catch (error) {
      console.error('Error fetching stats:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="gamification-loading">Loading your progress...</div>;
  }

  const { progress, achievements, skills, rank, challenges } = stats || {};

  return (
    <div className="gamification-dashboard">
      <div className="gamification-header">
        <h1>Your Learning Journey</h1>
        <div className="user-level-badge">
          <span className="level-icon">⭐</span>
          <span className="level-text">Level {progress?.level || 1}</span>
        </div>
      </div>

      <div className="gamification-tabs">
        <button 
          className={activeTab === 'overview' ? 'active' : ''}
          onClick={() => setActiveTab('overview')}
        >
          Overview
        </button>
        <button 
          className={activeTab === 'achievements' ? 'active' : ''}
          onClick={() => setActiveTab('achievements')}
        >
          Achievements
        </button>
        <button 
          className={activeTab === 'skills' ? 'active' : ''}
          onClick={() => setActiveTab('skills')}
        >
          Skill Tree
        </button>
        <button 
          className={activeTab === 'challenges' ? 'active' : ''}
          onClick={() => setActiveTab('challenges')}
        >
          Challenges
        </button>
        <button 
          className={activeTab === 'leaderboard' ? 'active' : ''}
          onClick={() => setActiveTab('leaderboard')}
        >
          Leaderboard
        </button>
      </div>

      <div className="gamification-content">
        {activeTab === 'overview' && (
          <div className="overview-tab">
            <div className="stats-grid">
              <div className="stat-card">
                <div className="stat-icon">💎</div>
                <div className="stat-value">{progress?.total_xp || 0}</div>
                <div className="stat-label">Total XP</div>
              </div>
              <div className="stat-card">
                <div className="stat-icon">🔥</div>
                <div className="stat-value">{progress?.streak_days || 0}</div>
                <div className="stat-label">Day Streak</div>
              </div>
              <div className="stat-card">
                <div className="stat-icon">🏆</div>
                <div className="stat-value">{achievements?.unlocked || 0}</div>
                <div className="stat-label">Achievements</div>
              </div>
              <div className="stat-card">
                <div className="stat-icon">📊</div>
                <div className="stat-value">#{rank?.rank || 'N/A'}</div>
                <div className="stat-label">Global Rank</div>
              </div>
            </div>

            <StreakTracker userId={userId} streakDays={progress?.streak_days || 0} />
            
            <div className="recent-achievements">
              <h3>Recent Achievements</h3>
              <AchievementBadges userId={userId} limit={3} />
            </div>
          </div>
        )}

        {activeTab === 'achievements' && (
          <AchievementBadges userId={userId} />
        )}

        {activeTab === 'skills' && (
          <SkillTree userId={userId} />
        )}

        {activeTab === 'challenges' && (
          <ChallengeMode userId={userId} />
        )}

        {activeTab === 'leaderboard' && (
          <Leaderboard userId={userId} />
        )}
      </div>
    </div>
  );
};

export default GamificationDashboard;
