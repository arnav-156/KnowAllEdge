# 🎮 Gamification System - Quick Start Guide

## What You Get

✅ **Achievement Badges** - Earn rewards for learning milestones  
✅ **Streak Tracking** - Daily learning streaks with visual calendar  
✅ **Leaderboards** - Global rankings (privacy-conscious)  
✅ **Challenge Mode** - Time-based quizzes and tasks  
✅ **Skill Trees** - RPG-style progression system  

## Quick Setup (5 Minutes)

### 1. Backend is Ready ✓
The gamification system is already integrated into your backend!

### 2. Add to Your Frontend

Add the gamification dashboard to any page:

```jsx
import GamificationDashboard from './components/GamificationDashboard';

function MyPage() {
  const userId = 'user123'; // Get from your auth system
  
  return (
    <div>
      <h1>My Learning Dashboard</h1>
      <GamificationDashboard userId={userId} />
    </div>
  );
}
```

### 3. Track User Actions

**When user completes a topic:**
```javascript
await fetch('/api/gamification/progress/topic', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-User-ID': userId
  },
  body: JSON.stringify({
    topic_id: topicId,
    time_spent: 300 // seconds
  })
});
```

**When user completes a quiz:**
```javascript
await fetch('/api/gamification/progress/quiz', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-User-ID': userId
  },
  body: JSON.stringify({
    quiz_id: quizId,
    score: 85, // percentage
    time_taken: 180 // seconds
  })
});
```

## That's It! 🎉

Your gamification system is now live with:
- 9 default achievements
- 6 skill tree nodes
- 3 challenges
- Global leaderboard
- Streak tracking

## Test It Out

1. **Start the backend:**
```bash
cd backend
python main.py
```

2. **Start the frontend:**
```bash
cd frontend
npm run dev
```

3. **Visit the gamification dashboard** and start earning XP!

## Quick API Reference

| Endpoint | Purpose |
|----------|---------|
| `GET /api/gamification/stats` | Get all user stats |
| `POST /api/gamification/progress/topic` | Record topic completion |
| `POST /api/gamification/progress/quiz` | Record quiz completion |
| `GET /api/gamification/achievements/user` | Get user achievements |
| `GET /api/gamification/leaderboard` | Get global rankings |
| `POST /api/gamification/challenges/start` | Start a challenge |
| `POST /api/gamification/skills/unlock` | Unlock a skill |

## Customization

Want to add your own achievements, skills, or challenges?  
See `GAMIFICATION_SYSTEM_GUIDE.md` for detailed customization instructions.

## Need Help?

- Check `GAMIFICATION_SYSTEM_GUIDE.md` for full documentation
- Test endpoints with: `curl -X GET "http://localhost:5000/api/gamification/stats?user_id=test"`
- Check browser console for frontend errors
- Check backend logs for API errors

---

**Happy Learning! 🚀**
