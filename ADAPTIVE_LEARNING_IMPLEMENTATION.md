# Adaptive Learning Pathways Implementation

This document details the backend implementation of the Adaptive Learning Pathways feature.

## 1. Database Schema (`backend/analytics_db.py`)

Two new tables have been added to `analytics.db`:

### `user_progress`
Tracks the user's mastery level for each subtopic.
- `user_id` (TEXT): User identifier (or 'anonymous')
- `topic` (TEXT): Main topic name
- `subtopic` (TEXT): Subtopic name
- `mastery_level` (INTEGER): 0 (None), 1 (Beginner), 2 (Intermediate), 3 (Advanced)
- `last_accessed` (TIMESTAMP): Last update time

### `quiz_results`
Stores the history of quiz attempts.
- `user_id` (TEXT): User identifier
- `topic` (TEXT): Main topic name
- `score` (INTEGER): User's score
- `total_questions` (INTEGER): Total questions in the quiz
- `difficulty_level` (TEXT): Difficulty of the quiz
- `created_at` (TIMESTAMP): Time of submission

## 2. API Endpoints (`backend/main.py`)

### Generate Quiz
`POST /api/quiz/generate`
- **Body**: `{"topic": "...", "subtopic": "...", "education": "...", "count": 3}`
- **Response**: JSON array of multiple-choice questions.

### Submit Quiz
`POST /api/quiz/submit`
- **Body**: `{"topic": "...", "subtopic": "...", "score": 2, "total": 3, "difficulty": "medium"}`
- **Response**: `{"status": "success", "mastery_level": 2}`
- **Effect**: Updates `user_progress` and saves to `quiz_results`.

### Get Progress
`GET /api/progress?topic=...`
- **Response**: List of progress entries for the user.

### Get Recommendations
`POST /api/recommendations`
- **Body**: `{"topic": "..."}`
- **Response**: JSON array of recommended subtopics based on mastery.

## 3. Adaptive Logic

The `generate_single_explanation_google_ai` function in `main.py` has been updated to automatically check for user mastery.
- If mastery data exists, it uses the `adaptive_explanation` prompt template.
- The prompt adjusts the complexity and depth of the explanation based on the user's level.

## 4. Frontend Implementation Guide

To complete this feature, the following frontend components are needed:

1.  **Quiz Component**:
    - A modal or side panel to display the generated quiz.
    - Logic to handle user selection and scoring.
    - Call `/api/quiz/submit` upon completion.

2.  **Progress Indicators**:
    - Visual badges (e.g., stars, progress bars) on the graph nodes to show mastery level.
    - Fetch data from `/api/progress` on load.

3.  **Recommendation Engine**:
    - A "What to learn next" section.
    - Call `/api/recommendations` to get suggestions.

4.  **Adaptive Content**:
    - The existing explanation view will automatically benefit from the backend changes. No frontend changes needed for the content itself, but you might want to display a "Personalized for your level" badge.
