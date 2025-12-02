import React, { useState, useEffect } from 'react';
import './SkillTree.css';

const SkillTree = ({ userId }) => {
  const [skills, setSkills] = useState({ unlocked: [], all_skills: [] });
  const [userProgress, setUserProgress] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedSkill, setSelectedSkill] = useState(null);

  useEffect(() => {
    fetchSkills();
    fetchProgress();
  }, [userId]);

  const fetchSkills = async () => {
    try {
      const response = await fetch(`/api/gamification/skills/user?user_id=${userId}`);
      const data = await response.json();
      if (data.success) {
        setSkills(data);
      }
    } catch (error) {
      console.error('Error fetching skills:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchProgress = async () => {
    try {
      const response = await fetch(`/api/gamification/progress?user_id=${userId}`);
      const data = await response.json();
      if (data.success) {
        setUserProgress(data.progress);
      }
    } catch (error) {
      console.error('Error fetching progress:', error);
    }
  };

  const isUnlocked = (skillId) => {
    return skills.unlocked.some(s => s.skill_id === skillId);
  };

  const canUnlock = (skill) => {
    if (!userProgress) return false;
    
    // Check level requirement
    if (userProgress.level < skill.level_required) return false;
    
    // Check XP cost
    if (userProgress.total_xp < skill.xp_cost) return false;
    
    // Check parent skill
    if (skill.parent_skill_id && !isUnlocked(skill.parent_skill_id)) return false;
    
    return true;
  };

  const handleUnlockSkill = async (skillId) => {
    try {
      const response = await fetch('/api/gamification/skills/unlock', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-User-ID': userId
        },
        body: JSON.stringify({ skill_id: skillId })
      });
      
      const data = await response.json();
      
      if (data.success) {
        fetchSkills();
        fetchProgress();
        alert('Skill unlocked successfully!');
      } else {
        alert(data.error || 'Failed to unlock skill');
      }
    } catch (error) {
      console.error('Error unlocking skill:', error);
      alert('Failed to unlock skill');
    }
  };

  const getSkillsByCategory = () => {
    const categories = {};
    skills.all_skills.forEach(skill => {
      if (!categories[skill.category]) {
        categories[skill.category] = [];
      }
      categories[skill.category].push(skill);
    });
    return categories;
  };

  if (loading) {
    return <div className="skill-tree-loading">Loading skill tree...</div>;
  }

  const skillsByCategory = getSkillsByCategory();

  return (
    <div className="skill-tree">
      <div className="skill-tree-header">
        <h2>Skill Tree</h2>
        {userProgress && (
          <div className="user-resources">
            <span className="resource-item">
              <span className="resource-icon">⭐</span>
              Level {userProgress.level}
            </span>
            <span className="resource-item">
              <span className="resource-icon">💎</span>
              {userProgress.total_xp} XP
            </span>
          </div>
        )}
      </div>

      <div className="skill-categories">
        {Object.entries(skillsByCategory).map(([category, categorySkills]) => (
          <div key={category} className="skill-category">
            <h3 className="category-title">{category.charAt(0).toUpperCase() + category.slice(1)}</h3>
            <div className="skills-grid">
              {categorySkills.map(skill => {
                const unlocked = isUnlocked(skill.id);
                const canUnlockSkill = !unlocked && canUnlock(skill);
                
                return (
                  <div 
                    key={skill.id}
                    className={`skill-node ${unlocked ? 'unlocked' : ''} ${canUnlockSkill ? 'available' : ''}`}
                    onClick={() => setSelectedSkill(skill)}
                  >
                    <div className="skill-icon">{skill.icon}</div>
                    <div className="skill-name">{skill.name}</div>
                    {unlocked && <div className="skill-check">✓</div>}
                    {!unlocked && (
                      <div className="skill-cost">{skill.xp_cost} XP</div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        ))}
      </div>

      {selectedSkill && (
        <div className="skill-modal" onClick={() => setSelectedSkill(null)}>
          <div className="skill-modal-content" onClick={(e) => e.stopPropagation()}>
            <button className="modal-close" onClick={() => setSelectedSkill(null)}>×</button>
            
            <div className="skill-detail-icon">{selectedSkill.icon}</div>
            <h2>{selectedSkill.name}</h2>
            <p className="skill-description">{selectedSkill.description}</p>
            
            <div className="skill-requirements">
              <h4>Requirements:</h4>
              <ul>
                <li>Level {selectedSkill.level_required} required</li>
                <li>{selectedSkill.xp_cost} XP cost</li>
                {selectedSkill.parent_skill_id && (
                  <li>Requires parent skill to be unlocked</li>
                )}
              </ul>
            </div>

            {isUnlocked(selectedSkill.id) ? (
              <div className="skill-unlocked-badge">
                ✓ Unlocked
              </div>
            ) : canUnlock(selectedSkill) ? (
              <button 
                className="unlock-button"
                onClick={() => handleUnlockSkill(selectedSkill.id)}
              >
                Unlock Skill
              </button>
            ) : (
              <div className="skill-locked-message">
                Requirements not met
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default SkillTree;
