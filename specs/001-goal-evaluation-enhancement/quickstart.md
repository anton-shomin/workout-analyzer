# Quickstart Guide: Goal Evaluation Enhancement

## Overview
This feature enables goal-oriented workout analysis by allowing users to specify workout goals in their workout files and having the AI evaluate how well the workout aligns with those goals.

## Setup

### Prerequisites
- Python 3.11+
- Existing workout analyzer installation
- Obsidian vault with workout markdown files

### Configuration
No additional configuration required. The feature integrates seamlessly with existing setup.

## Usage

### 1. Add Goals to Workout Files
Add a `goal` field to the YAML frontmatter of your workout files:

```yaml
---
date: 2026-02-11
type: Strength
weight: 81
goal: Increase deadlift strength
---
```

### 2. Run Workout Analysis
Execute your normal workout analysis command:

```bash
# Analyze specific workout
python main.py --analyze-workout 2026-02-11

# Analyze latest workout
python main.py --analyze-latest

# Reanalyze all workouts
python main.py --reanalyze-all
```

### 3. View Goal-Oriented Analysis
The AI analysis will now include specific evaluation of how well the workout aligns with the stated goal.

## Example

### Before (without goal):
```markdown
## AI Analysis

1. **Muscle Group Balance**: Good upper body focus, minimal lower body work
2. **Volume and Intensity**: Moderate volume, appropriate for conditioning
3. **Recommendations**: Add more pulling movements next time
4. **Recovery**: Take 2 days rest
```

### After (with goal):
```markdown
## AI Analysis

1. **Goal Alignment** (MOST IMPORTANT): 
   - Does this exercise selection and work mode contribute to achieving the goal "Increase deadlift strength"?
   - Limited posterior chain work despite strength goal
   - Heavy emphasis on pressing reduces recovery for deadlift adaptation

2. **Load Analysis**: 
   - Good rep density for conditioning
   - Insufficient heavy pulling for deadlift strength

3. **Recommendations**: 
   - Add Romanian deadlifts or hip hinges to support main goal
   - Reduce pressing volume to allow for deadlift recovery

4. **Recovery**: 
   - 3 days rest recommended due to CNS load from strength-focused session
```

## Backward Compatibility
- Workouts without a `goal` field will continue to work as before
- Default value "Not specified" will be used for missing goals
- All existing functionality is preserved