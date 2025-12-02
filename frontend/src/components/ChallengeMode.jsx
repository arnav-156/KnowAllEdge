import React, { useState, useEffect } from 'react';
import './ChallengeMode.css';

const ChallengeMode = ({ userId }) => {
  const [challenges, setChallenge] = useState([]);
  const [userChallenges, setUserChallenges] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeChallenge, setActiveChallenge] = useState(null);
  const [timer, setTimer] = useState(null);

  useEffect(() => {
    fetchChallenges();
    fetchUserChallenges();
  }, [userId]);

  useEffect(() => {
    let interval;
    if (activeChallenge && timer > 0) {
      interval = setInterval(() => {
        setTimer(prev => prev - 1);
      }, 1000);
    } else if (timer === 0) {
      handleChallengeTimeout();
    }
    return () => clearInterval(interval);
  }, [activeChallenge, timer]);

  const fetchChallenges = async () => {
    try {
      const response = await fetch('/api/gamification/challenges');
      const data = await response.json();
      if (data.success) {
        setChallenge(data.challenges);
      }
    } catch (error) {
      console.error('Error fetching challenges:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchUserChallenges = async () => {
    try {
      const response = await fetch(`/api/gamification/challenges/user?user_id=${userId}`);
      const data = await response.json();
      if (data.success) {
        setUserChallenges(data.challenges);
      }
    } catch (error) {
      console.error('Error fetching user challenges:', error);
    }
  };

  const handleStartChallenge = async (challengeId) => {
    try {
      const response = await fetch('/api/gamification/challenges/start', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-User-ID': userId
        },
        body: JSON.stringify({ challenge_id: challengeId })
      });
      
      const data = await response.json();
      
      if (data.success) {
        const challenge = challenges.find(c => c.id === challengeId);
        setActiveChallenge(challenge);
        setTimer(challenge.time_limit);
        fetchUserChallenges();
      } else {
        alert(data.error || 'Failed to start challenge');
      }
    } catch (error) {
      console.error('Error starting challenge:', error);
    }
  };

  const handleCompleteChallenge = async (score = 100) => {
    if (!activeChallenge) return;

    try {
      const response = await fetch('/api/gamification/challenges/complete', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-User-ID': userId
        },
        body: JSON.stringify({ 
          challenge_id: activeChallenge.id,
          score: score
        })
      });
      
      const data = await response.json();
      
      if (data.success) {
        alert(`Challenge completed! You earned ${data.xp_earned} XP!`);
        setActiveChallenge(null);
        setTimer(null);
        fetchUserChallenges();
      }
    } catch (error) {
      console.error('Error completing challenge:', error);
    }
  };

  const handleChallengeTimeout = () => {
    alert('Time\'s up! Challenge failed.');
    setActiveChallenge(null);
    setTimer(null);
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const getDifficultyColor = (difficulty) => {
    switch (difficulty) {
      case 'easy': return '#4caf50';
      case 'medium': return '#ff9800';
      case 'hard': return '#f44336';
      default: return '#999';
    }
  };

  const isChallengeActive = (challengeId) => {
    return userChallenges.some(uc => uc.challenge_id === challengeId && uc.status === 'active');
  };

  const isChallengeCompleted = (challengeId) => {
    return userChallenges.some(uc => uc.challenge_id === challengeId && uc.status === 'completed');
  };

  if (loading) {
    return <div className="challenge-loading">Loading challenges...</div>;
  }

  return (
    <div className="challenge-mode">
      <div className="challenge-header">
        <h2>Challenge Mode</h2>
        <p>Test your skills with time-based challenges and earn bonus XP!</p>
      </div>

      {activeChallenge && (
        <div className="active-challenge-banner">
          <div className="challenge-timer">
            <span className="timer-icon">⏱️</span>
            <span className="timer-value">{formatTime(timer)}</span>
          </div>
          <div className="challenge-info">
            <h3>{activeChallenge.name}</h3>
            <p>{activeChallenge.description}</p>
          </div>
          <button 
            className="complete-button"
            onClick={() => handleCompleteChallenge(100)}
          >
            Complete Challenge
          </button>
        </div>
      )}

      <div className="challenges-grid">
        {challenges.map(challenge => {
          const isActive = isChallengeActive(challenge.id);
          const isCompleted = isChallengeCompleted(challenge.id);
          
          return (
            <div 
              key={challenge.id}
              className={`challenge-card ${isCompleted ? 'completed' : ''} ${isActive ? 'active' : ''}`}
            >
              <div className="challenge-difficulty" style={{ background: getDifficultyColor(challenge.difficulty) }}>
                {challenge.difficulty}
              </div>
              
              <div className="challenge-type-icon">
                {challenge.type === 'timed_quiz' && '⚡'}
                {challenge.type === 'exploration' && '🗺️'}
                {challenge.type === 'achievement' && '🏆'}
              </div>
              
              <h3>{challenge.name}</h3>
              <p>{challenge.description}</p>
              
              <div className="challenge-details">
                {challenge.time_limit && (
                  <div className="detail-item">
                    <span className="detail-icon">⏱️</span>
                    <span>{Math.floor(challenge.time_limit / 60)} min</span>
                  </div>
                )}
                <div className="detail-item">
                  <span className="detail-icon">💎</span>
                  <span>+{challenge.xp_reward} XP</span>
                </div>
              </div>

              {isCompleted ? (
                <div className="challenge-completed-badge">
                  ✓ Completed
                </div>
              ) : isActive ? (
                <div className="challenge-active-badge">
                  In Progress
                </div>
              ) : (
                <button 
                  className="start-challenge-button"
                  onClick={() => handleStartChallenge(challenge.id)}
                  disabled={activeChallenge !== null}
                >
                  Start Challenge
                </button>
              )}
            </div>
          );
        })}
      </div>

      {challenges.length === 0 && (
        <div className="no-challenges">
          No challenges available at the moment. Check back later!
        </div>
      )}
    </div>
  );
};

export default ChallengeMode;
