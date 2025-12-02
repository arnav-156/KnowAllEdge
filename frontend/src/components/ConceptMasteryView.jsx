import React, { useState, useEffect } from 'react';
import './ConceptMasteryView.css';

const ConceptMasteryView = ({ userId }) => {
  const [concepts, setConcepts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filterLevel, setFilterLevel] = useState('all');

  useEffect(() => {
    fetchConceptMastery();
  }, [userId]);

  const fetchConceptMastery = async () => {
    try {
      const response = await fetch(`/api/analytics/concepts/mastery?user_id=${userId}`);
      const data = await response.json();
      
      if (data.success) {
        setConcepts(data.concepts);
      }
    } catch (error) {
      console.error('Error fetching concept mastery:', error);
    } finally {
      setLoading(false);
    }
  };

  const getMasteryIcon = (level) => {
    switch (level) {
      case 'mastered': return '🏆';
      case 'reviewing': return '📚';
      case 'learning': return '📖';
      case 'introduced': return '🌱';
      default: return '❓';
    }
  };

  const getMasteryColor = (level) => {
    switch (level) {
      case 'mastered': return '#4caf50';
      case 'reviewing': return '#2196f3';
      case 'learning': return '#ff9800';
      case 'introduced': return '#9e9e9e';
      default: return '#666';
    }
  };

  const filteredConcepts = filterLevel === 'all' 
    ? concepts 
    : concepts.filter(c => c.mastery_level === filterLevel);

  const stats = {
    mastered: concepts.filter(c => c.mastery_level === 'mastered').length,
    reviewing: concepts.filter(c => c.mastery_level === 'reviewing').length,
    learning: concepts.filter(c => c.mastery_level === 'learning').length,
    introduced: concepts.filter(c => c.mastery_level === 'introduced').length
  };

  if (loading) {
    return <div className="concept-mastery loading">Loading concept mastery...</div>;
  }

  return (
    <div className="concept-mastery">
      <div className="mastery-header">
        <h2>Concept Mastery Levels</h2>
        <p>Track your understanding of different concepts</p>
      </div>

      <div className="mastery-stats">
        <div className="stat-card mastered">
          <div className="stat-icon">🏆</div>
          <div className="stat-content">
            <div className="stat-value">{stats.mastered}</div>
            <div className="stat-label">Mastered</div>
          </div>
        </div>

        <div className="stat-card reviewing">
          <div className="stat-icon">📚</div>
          <div className="stat-content">
            <div className="stat-value">{stats.reviewing}</div>
            <div className="stat-label">Reviewing</div>
          </div>
        </div>

        <div className="stat-card learning">
          <div className="stat-icon">📖</div>
          <div className="stat-content">
            <div className="stat-value">{stats.learning}</div>
            <div className="stat-label">Learning</div>
          </div>
        </div>

        <div className="stat-card introduced">
          <div className="stat-icon">🌱</div>
          <div className="stat-content">
            <div className="stat-value">{stats.introduced}</div>
            <div className="stat-label">Introduced</div>
          </div>
        </div>
      </div>

      <div className="mastery-filters">
        <button 
          className={filterLevel === 'all' ? 'active' : ''}
          onClick={() => setFilterLevel('all')}
        >
          All Concepts
        </button>
        <button 
          className={filterLevel === 'mastered' ? 'active' : ''}
          onClick={() => setFilterLevel('mastered')}
        >
          Mastered
        </button>
        <button 
          className={filterLevel === 'reviewing' ? 'active' : ''}
          onClick={() => setFilterLevel('reviewing')}
        >
          Reviewing
        </button>
        <button 
          className={filterLevel === 'learning' ? 'active' : ''}
          onClick={() => setFilterLevel('learning')}
        >
          Learning
        </button>
        <button 
          className={filterLevel === 'introduced' ? 'active' : ''}
          onClick={() => setFilterLevel('introduced')}
        >
          Introduced
        </button>
      </div>

      {filteredConcepts.length === 0 ? (
        <div className="no-concepts">No concepts found</div>
      ) : (
        <div className="concepts-grid">
          {filteredConcepts.map((concept, index) => (
            <div key={index} className={`concept-card ${concept.mastery_level}`}>
              <div className="concept-header">
                <span className="concept-icon">{getMasteryIcon(concept.mastery_level)}</span>
                <div className="concept-info">
                  <h4>{concept.concept_name}</h4>
                  <span className="concept-topic">{concept.topic_name || 'General'}</span>
                </div>
              </div>

              <div className="concept-progress">
                <div className="progress-bar">
                  <div 
                    className="progress-fill"
                    style={{ 
                      width: `${concept.confidence_score}%`,
                      backgroundColor: getMasteryColor(concept.mastery_level)
                    }}
                  ></div>
                </div>
                <span className="progress-label">{concept.confidence_score}% confidence</span>
              </div>

              <div className="concept-meta">
                <div className="meta-item">
                  <span className="meta-icon">📅</span>
                  <span>Last reviewed: {new Date(concept.last_reviewed).toLocaleDateString()}</span>
                </div>
                <div className="meta-item">
                  <span className="meta-icon">🔄</span>
                  <span>{concept.review_count} reviews</span>
                </div>
              </div>

              <div className="concept-level">
                <span 
                  className="level-badge"
                  style={{ backgroundColor: getMasteryColor(concept.mastery_level) }}
                >
                  {concept.mastery_level}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default ConceptMasteryView;
