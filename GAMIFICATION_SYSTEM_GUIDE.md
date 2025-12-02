# 🎮 Gamification System - Complete Implementation Guide

## Overview

A comprehensive gamification system that enhances user engagement through achievement badges, streak tracking, leaderboards, challenges, and RPG-style skill trees.

## Features

### 1. 🏆 Achievement Badges
- **Unlock Rewards**: Earn badges for completing learning milestones
- **Categories**: Beginner, Learning, Quiz, Streak, Challenge, Exploration, Special
- **XP Rewards**: Each achievement grants bonus experience points
- **Secret Achievements**: Hidden achievements for special accomplishments

**Default Achievements:**
- 🎯 First Steps (50 XP) - Complete your first topic
- 📚 Knowledge Seeker (200 XP) - Complete 10 topics
- 🏆 Master Learner (1000 XP) - Complete 50 topics
- 🎓 Quiz Master (500 XP) - Complete 25 quizzes
- 🔥 Streak Warrior (300 XP) - Maintain 7-day streak
- ⚡ Streak Legend (1500 XP) - Maintain 30-day streak
- ⚡ Speed Demon (250 XP) - Complete challenge in under 5 minutes
- 🗺️ Explorer (400 XP) - Explore 5 different categories
- 🦉 Night Owl (100 XP) - Complete topic after midnight (Secret)

### 2. 🔥 Streak Tracking
- **Daily Learning Streaks**: Track consecutive days of learning
- **Streak Milestones**: 3, 7, 14, 30, 60, 90, 180, 365 days
- **Visual Calendar**: See your last 7 days of activity
- **Motivational Messages**: Encouraging feedback based on streak length
- **Streak Protection**: Grace period for maintaining streaks

### 3. 📊 Leaderboards
- **Global Rankings**: Compare with other learners
- **Privacy Mode**: Hide your position from others (optional)
- **Ranking Metrics**: Based on total XP, level, and achievements
- **Top 3 Highlights**: Special badges for gold, silver, bronze positions
- **Real-time Updates**: Leaderboard updates as users progress

### 4. ⚡ Challenge Mode
- **Timed Challenges**: Complete tasks within time limits
- **Difficulty Levels**: Easy, Medium, Hard
- **Challenge Types**:
  - ⚡ Timed Quiz - Answer questions quickly
  - 🗺️ Exploration - Discover new topics
  - 🏆 Achievement - Reach specific goals
- **Bonus XP**: Extra rewards for challenge completion
- **Live Timer**: Real-time countdown during active challenges

**Default Challenges:**
- 5-Minute Speed Quiz (200 XP) - Complete 10 questions in 5 minutes
- Daily Explorer (150 XP) - Explore 3 new topics today
- Perfect Score (500 XP) - Get 100% on any quiz

### 5. 🌳 Skill Tree (RPG-Style)
- **Progressive Unlocking**: Unlock skills as you level up
- **Skill Dependencies**: Some skills require parent skills
- **XP Cost**: Spend XP to unlock new abilities
- **Skill Categories**: Foundation, Assessment, Advanced, Mastery
- **Visual Tree**: Interactive skill tree visualization

**Default Skills:**
- 🌱 Beginner Learner (0 XP, Level 1) - Start your journey
- 📖 Active Reader (100 XP, Level 2) - Advanced reading features
- ✍️ Quiz Taker (150 XP, Level 2) - Unlock quiz features
- ⚡ Speed Learner (300 XP, Level 5) - Timed challenges
- 🎯 Master Quizzer (400 XP, Level 5) - Advanced quiz modes
- 🏗️ Knowledge Architect (800 XP, Level 10) - Custom learning paths

## Backend API

### Database Schema

**Tables:**
- `user_progress` - User XP, level, streak, and stats
- `achievements` - Achievement definitions
- `user_achievements` - Unlocked achievements per user
- `skill_tree` - Skill definitions and requirements
- `user_skills` - Unlocked skills per user
- `challenges` - Challenge definitions
- `user_challenges` - Active/completed challenges per user
- `leaderboard` - Global ranking data

### API Endpoints

#### User Progress
```
GET  /api/gamification/progress?user_id={id}
POST /api/gamification/progress/activity
POST /api/gamification/progress/topic
POST /api/gamification/progress/quiz
```

#### Achievements
```
GET /api/gamification/achievements
GET /api/gamification/achievements/user?user_id={id}
```

#### Skill Tree
```
GET  /api/gamification/skills
GET  /api/gamification/skills/user?user_id={id}
POST /api/gamification/skills/unlock
```

#### Challenges
```
GET  /api/gamification/challenges
GET  /api/gamification/challenges/user?user_id={id}
POST /api/gamification/challenges/start
POST /api/gamification/challenges/complete
```

#### Leaderboard
```
GET /api/gamification/leaderboard?limit={n}
GET /api/gamification/leaderboard/rank?user_id={id}
```

#### Stats
```
GET /api/gamification/stats?user_id={id}
```

## Frontend Components

### Main Components

1. **GamificationDashboard** - Main container with tabs
2. **AchievementBadges** - Display and filter achievements
3. **StreakTracker** - Visual streak calendar and progress
4. **Leaderboard** - Global rankings with privacy options
5. **SkillTree** - Interactive skill tree with unlock functionality
6. **ChallengeMode** - Active challenges with timer

### Integration Example

```jsx
import GamificationDashboard from './components/GamificationDashboard';

function App() {
  const userId = 'user123'; // Get from auth context
  
  return (
    <GamificationDashboard userId={userId} />
  );
}
```

## Installation & Setup

### Backend Setup

1. **Install Dependencies** (already included in requirements.txt):
```bash
cd backend
pip install flask flask-cors python-dotenv
```

2. **Database Initialization**:
The database is automatically initialized on first import of `GamificationDB`.

3. **Start Backend**:
```bash
python main.py
```

### Frontend Setup

1. **Components are ready to use** - No additional dependencies needed
2. **Import in your app**:
```jsx
import GamificationDashboard from './components/GamificationDashboard';
```

## Usage Examples

### Recording Topic Completion

```javascript
// When user completes a topic
const response = await fetch('/api/gamification/progress/topic', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-User-ID': userId
  },
  body: JSON.stringify({
    topic_id: 'topic123',
    time_spent: 300 // seconds
  })
});

const data = await response.json();
console.log(`Earned ${data.xp_earned} XP!`);
```

### Recording Quiz Completion

```javascript
// When user completes a quiz
const response = await fetch('/api/gamification/progress/quiz', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-User-ID': userId
  },
  body: JSON.stringify({
    quiz_id: 'quiz123',
    score: 85, // percentage
    time_taken: 180 // seconds
  })
});

const data = await response.json();
console.log(`Earned ${data.xp_earned} XP!`);
```

### Starting a Challenge

```javascript
const response = await fetch('/api/gamification/challenges/start', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-User-ID': userId
  },
  body: JSON.stringify({
    challenge_id: 'speed_quiz_5min'
  })
});
```

### Unlocking a Skill

```javascript
const response = await fetch('/api/gamification/skills/unlock', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-User-ID': userId
  },
  body: JSON.stringify({
    skill_id: 'speed_learner'
  })
});
```

## XP and Leveling System

### XP Rewards
- **Topic Completion**: 50 XP
- **Quiz Completion**: 2 XP per percentage point (max 200 XP for 100%)
- **Achievement Unlock**: Varies by achievement (50-1500 XP)
- **Challenge Completion**: Varies by difficulty (150-500 XP)

### Level Calculation
```
Level = floor(sqrt(total_xp / 100)) + 1
```

**Examples:**
- 0 XP = Level 1
- 100 XP = Level 2
- 400 XP = Level 3
- 900 XP = Level 4
- 10,000 XP = Level 11

## Privacy & Security

### Privacy Features
- **Optional Leaderboard**: Users can enable privacy mode
- **Anonymous Display**: Usernames hidden in privacy mode
- **User Control**: Users control their visibility

### Security
- **User Authentication**: All endpoints require user_id
- **Data Isolation**: Users can only access their own data
- **Input Validation**: All inputs are validated and sanitized

## Customization

### Adding New Achievements

```python
# In gamification_db.py, add to _init_default_achievements()
{
    'id': 'custom_achievement',
    'name': 'Custom Achievement',
    'description': 'Complete a custom task',
    'category': 'special',
    'icon': '🎉',
    'xp_reward': 300,
    'requirement_type': 'custom_metric',
    'requirement_value': 10
}
```

### Adding New Skills

```python
# In gamification_db.py, add to _init_default_skill_tree()
{
    'id': 'custom_skill',
    'name': 'Custom Skill',
    'description': 'A custom skill',
    'category': 'advanced',
    'parent_skill_id': 'beginner_learner',
    'xp_cost': 500,
    'level_required': 5,
    'icon': '🚀'
}
```

### Adding New Challenges

```python
# In gamification_db.py, add to _init_default_challenges()
{
    'id': 'custom_challenge',
    'name': 'Custom Challenge',
    'description': 'Complete a custom challenge',
    'type': 'custom',
    'difficulty': 'medium',
    'time_limit': 600,
    'xp_reward': 300,
    'requirements': json.dumps({'custom': 'requirements'})
}
```

## Testing

### Test User Progress
```bash
curl -X GET "http://localhost:5000/api/gamification/progress?user_id=test_user"
```

### Test Topic Completion
```bash
curl -X POST "http://localhost:5000/api/gamification/progress/topic" \
  -H "Content-Type: application/json" \
  -H "X-User-ID: test_user" \
  -d '{"topic_id": "test_topic", "time_spent": 300}'
```

### Test Leaderboard
```bash
curl -X GET "http://localhost:5000/api/gamification/leaderboard?limit=10"
```

## Performance Considerations

- **Database Indexing**: User IDs and achievement IDs are indexed
- **Caching**: Consider caching leaderboard data
- **Batch Updates**: Leaderboard updates are batched
- **Efficient Queries**: Optimized SQL queries with proper joins

## Future Enhancements

- [ ] Team/Group challenges
- [ ] Social features (friend comparisons)
- [ ] Seasonal events and limited-time challenges
- [ ] Custom avatars and profile customization
- [ ] Achievement showcase on profile
- [ ] Skill tree branches and specializations
- [ ] Daily/weekly quests
- [ ] Reward shop (spend XP on perks)
- [ ] Push notifications for streak reminders
- [ ] Mobile app integration

## Troubleshooting

### Database Issues
```python
# Reset database
import os
os.remove('gamification.db')
# Restart backend to reinitialize
```

### Missing Achievements
```python
# Manually trigger achievement check
from gamification_db import GamificationDB
db = GamificationDB()
db._check_achievements('user_id', 'topics_completed', 10)
```

### Leaderboard Not Updating
```python
# Manually update leaderboard
db._update_leaderboard('user_id')
```

## Support

For issues or questions:
1. Check the API documentation at `/api/docs`
2. Review backend logs for errors
3. Test endpoints with curl or Postman
4. Check browser console for frontend errors

## License

Part of the KnowAllEdge learning platform.

---

**Built with ❤️ for enhanced learning engagement**
