import React, { useState, useEffect } from 'react';
import './Leaderboard.css';

const Leaderboard = ({ userId }) => {
  const [leaderboard, setLeaderboard] = useState([]);
  const [userRank, setUserRank] = useState(null);
  const [loading, setLoading] = useState(true);
  const [privacyMode, setPrivacyMode] = useState(false);

  useEffect(() => {
    fetchLeaderboard();
    fetchUserRank();
  }, [userId]);

  const fetchLeaderboard = async () => {
    try {
      const response = await fetch('/api/gamification/leaderboard?limit=100');
      const data = await response.json();
      if (data.success) {
        setLeaderboard(data.leaderboard);
      }
    } catch (error) {
      console.error('Error fetching leaderboard:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchUserRank = async () => {
    try {
      const response = await fetch(`/api/gamification/leaderboard/rank?user_id=${userId}`);
      const data = await response.json();
      if (data.success) {
        setUserRank(data.rank);
      }
    } catch (error) {
      console.error('Error fetching user rank:', error);
    }
  };

  const getRankIcon = (rank) => {
    if (rank === 1) return '🥇';
    if (rank === 2) return '🥈';
    if (rank === 3) return '🥉';
    return `#${rank}`;
  };

  const getRankClass = (rank) => {
    if (rank === 1) return 'gold';
    if (rank === 2) return 'silver';
    if (rank === 3) return 'bronze';
    return '';
  };

  if (loading) {
    return <div className="leaderboard-loading">Loading leaderboard...</div>;
  }

  return (
    <div className="leaderboard">
      <div className="leaderboard-header">
        <h2>Global Leaderboard</h2>
        <div className="privacy-toggle">
          <label>
            <input
              type="checkbox"
              checked={privacyMode}
              onChange={(e) => setPrivacyMode(e.target.checked)}
            />
            <span>Privacy Mode</span>
          </label>
          <p className="privacy-note">
            Hide your position from others (you can still see your rank)
          </p>
        </div>
      </div>

      {userRank && (
        <div className="user-rank-card">
          <div className="rank-badge">{getRankIcon(userRank.rank)}</div>
          <div className="rank-info">
            <h3>Your Rank</h3>
            <p className="rank-details">
              Level {userRank.level} • {userRank.total_xp} XP • {userRank.achievements_count} Achievements
            </p>
          </div>
        </div>
      )}

      <div className="leaderboard-list">
        {leaderboard.slice(0, 50).map((entry) => {
          const isCurrentUser = entry.user_id === userId;
          return (
            <div 
              key={entry.user_id}
              className={`leaderboard-entry ${getRankClass(entry.rank)} ${isCurrentUser ? 'current-user' : ''}`}
            >
              <div className="entry-rank">
                {getRankIcon(entry.rank)}
              </div>
              <div className="entry-info">
                <div className="entry-name">
                  {isCurrentUser ? 'You' : (privacyMode && !isCurrentUser ? 'Anonymous' : entry.username)}
                </div>
                <div className="entry-stats">
                  Level {entry.level} • {entry.total_xp.toLocaleString()} XP
                </div>
              </div>
              <div className="entry-achievements">
                🏆 {entry.achievements_count}
              </div>
            </div>
          );
        })}
      </div>

      {leaderboard.length === 0 && (
        <div className="no-leaderboard">
          No leaderboard data available yet. Start learning to appear here!
        </div>
      )}
    </div>
  );
};

export default Leaderboard;
