import React, { useState, useEffect } from 'react';
import './AchievementBadges.css';

const AchievementBadges = ({ userId, limit = null }) => {
  const [achievements, setAchievements] = useState({ unlocked: [], total: [] });
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');

  useEffect(() => {
    fetchAchievements();
  }, [userId]);

  const fetchAchievements = async () => {
    try {
      const response = await fetch(`/api/gamification/achievements/user?user_id=${userId}`);
      const data = await response.json();
      if (data.success) {
        setAchievements({
          unlocked: data.unlocked,
          total: data.total
        });
      }
    } catch (error) {
      console.error('Error fetching achievements:', error);
    } finally {
      setLoading(false);
    }
  };

  const getFilteredAchievements = () => {
    let filtered = achievements.total;
    
    if (filter === 'unlocked') {
      filtered = achievements.unlocked;
    } else if (filter === 'locked') {
      const unlockedIds = achievements.unlocked.map(a => a.id);
      filtered = achievements.total.filter(a => !unlockedIds.includes(a.id));
    } else if (filter !== 'all') {
      filtered = achievements.total.filter(a => a.category === filter);
    }

    return limit ? filtered.slice(0, limit) : filtered;
  };

  const isUnlocked = (achievementId) => {
    return achievements.unlocked.some(a => a.id === achievementId);
  };

  const categories = ['all', 'beginner', 'learning', 'quiz', 'streak', 'challenge', 'exploration', 'special'];

  if (loading) {
    return <div className="achievements-loading">Loading achievements...</div>;
  }

  const filteredAchievements = getFilteredAchievements();

  return (
    <div className="achievement-badges">
      {!limit && (
        <div className="achievement-filters">
          {categories.map(cat => (
            <button
              key={cat}
              className={filter === cat ? 'active' : ''}
              onClick={() => setFilter(cat)}
            >
              {cat.charAt(0).toUpperCase() + cat.slice(1)}
            </button>
          ))}
          <button
            className={filter === 'unlocked' ? 'active' : ''}
            onClick={() => setFilter('unlocked')}
          >
            Unlocked
          </button>
          <button
            className={filter === 'locked' ? 'active' : ''}
            onClick={() => setFilter('locked')}
          >
            Locked
          </button>
        </div>
      )}

      <div className="achievements-grid">
        {filteredAchievements.map(achievement => {
          const unlocked = isUnlocked(achievement.id);
          return (
            <div 
              key={achievement.id} 
              className={`achievement-card ${unlocked ? 'unlocked' : 'locked'}`}
            >
              <div className="achievement-icon">{achievement.icon}</div>
              <div className="achievement-info">
                <h4>{achievement.name}</h4>
                <p>{achievement.description}</p>
                <div className="achievement-reward">
                  <span className="xp-badge">+{achievement.xp_reward} XP</span>
                  {unlocked && (
                    <span className="unlocked-badge">✓ Unlocked</span>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {filteredAchievements.length === 0 && (
        <div className="no-achievements">
          No achievements found in this category.
        </div>
      )}
    </div>
  );
};

export default AchievementBadges;
