# API Contract: Goal-Evaluated Workout Analysis

## Overview
This contract defines the interface for workout analysis with goal evaluation. The system accepts workout data with an optional goal and returns analysis that specifically evaluates goal alignment.

## Data Contract

### Input: Workout Data with Goal
```json
{
  "date": "2026-02-11",
  "type": "Strength",
  "weight": 81,
  "duration": 45.5,
  "goal": "Increase deadlift strength",
  "scheme": {
    "type": "EMOM",
    "pattern": "5 reps every minute",
    "total_reps": 100,
    "time_per_rep": 3,
    "rest_between": 60
  },
  "exercises": [
    {
      "name": "Push-ups",
      "equipment": "Bodyweight",
      "reps": 50
    },
    {
      "name": "Squats",
      "equipment": "Bodyweight", 
      "reps": 50
    }
  ],
  "raw_content": "# Workout Content...",
  "content": "Processed content..."
}
```

### Output: Goal-Evaluated Analysis
```json
{
  "analysis_id": "uuid-string",
  "workout_date": "2026-02-11",
  "goal_evaluated": "Increase deadlift strength",
  "goal_alignment_score": 35,
  "detailed_analysis": {
    "goal_alignment": {
      "feedback": "Limited posterior chain work despite strength goal. Heavy emphasis on pressing movements does not support deadlift strength development.",
      "hormonal_assessment": "Low compound movement volume limits testosterone/growth hormone response for strength gains."
    },
    "load_analysis": {
      "density": "120 reps in 45 minutes",
      "balance_assessment": "Significant imbalance - no pulling movements for posterior chain development."
    },
    "recommendations": [
      "Add Romanian deadlifts or hip hinges to support main goal",
      "Reduce pressing volume to allow for deadlift recovery",
      "Include more compound pulling movements"
    ],
    "recovery_advice": "3 days rest recommended due to CNS load from strength-focused session"
  },
  "metrics": {
    "total_reps": 100,
    "calories": 285,
    "estimated_time": 45,
    "intensity_kcal_per_min": 6.3
  },
  "muscle_balance": {
    "push": "70%",
    "pull": "0%",
    "legs": "30%"
  },
  "generated_at": "2026-02-13T10:30:00Z"
}
```

## Processing Contract

### Function Signature
```
analyze_workout_with_goal(
    workout_data: dict,
    calories: int,
    muscle_balance: dict,
    actual_duration_minutes: int = 0
) -> dict
```

### Pre-conditions
- `workout_data` contains all required fields as defined in input contract
- `calories` is a positive number
- `muscle_balance` contains muscle group percentages

### Post-conditions
- Returns analysis that explicitly evaluates goal alignment when goal is specified
- When no goal is specified, returns standard analysis with note about missing goal
- Maintains all existing analysis functionality
- Preserves backward compatibility for workouts without goals

### Error Handling
- If `workout_data` is malformed, raises `InvalidWorkoutDataError`
- If AI service is unavailable, returns fallback analysis with appropriate messaging
- If goal field is present but empty, treats as "Not specified"