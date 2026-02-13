# Data Model: Goal Evaluation Enhancement

## Entities

### Workout
**Description**: Represents a completed training session with date, type, exercises, metrics, and goal

**Fields**:
- `date`: string - The date of the workout (e.g., "2026-02-11")
- `type`: string - The type/classification of workout (e.g., "Strength", "Endurance")
- `weight`: number - The user's body weight during workout (default: 70kg)
- `duration`: number - Duration of workout in minutes
- `goal`: string - The intended outcome/objective of the workout (e.g., "Strength gain", "Fat loss", "Endurance improvement")
- `scheme`: object - Workout scheme details (type, pattern, reps, timing)
- `exercises`: array - List of exercises performed
- `raw_content`: string - The full content of the workout file
- `content`: string - The processed content without frontmatter

### Goal
**Description**: The intended outcome of a workout session that guides exercise selection and evaluation

**Fields**:
- `value`: string - The specific goal text (e.g., "Build muscle", "Improve conditioning")
- `category`: string - The category/type of goal (e.g., "strength", "endurance", "hypertrophy", "fat_loss")
- `priority`: number - Priority level for goal achievement (1-5 scale)

### Analysis
**Description**: AI-generated feedback that evaluates workout effectiveness in relation to the stated goal

**Fields**:
- `workout_id`: string - Reference to the workout being analyzed
- `goal_alignment_score`: number - Numerical score representing how well the workout aligns with the goal (0-100)
- `goal_alignment_feedback`: string - Detailed feedback on goal alignment
- `recommendations`: array - Specific suggestions for improving goal alignment
- `recovery_advice`: string - Goal-specific recovery recommendations
- `generated_at`: timestamp - When the analysis was generated

## Relationships
- A `Workout` entity HAS ONE `Goal` (optional - may be "Not specified")
- A `Workout` entity GENERATES ONE `Analysis` (after processing)
- An `Analysis` entity REFERS TO ONE `Workout`

## Validation Rules
- `goal` field in Workout must be a string between 3-100 characters when specified
- `goal` field should not be empty string - use "Not specified" as default
- `goal_alignment_score` in Analysis must be between 0-100
- `workout_id` in Analysis must correspond to an existing Workout