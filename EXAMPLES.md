# Examples of Workout Files with Goal Field

This document provides examples of workout files that demonstrate the usage of the `goal` field for goal-oriented analysis.

## Example 1: Strength Training Goal

```markdown
---
date: 2026-02-15
type: Strength
weight: 81
goal: Increase deadlift strength
---

## Warm-up
- Cat-cow stretches (5 reps)
- Band pull-aparts (10 reps)

## Схема
**Тип:** EMOM
**Кругов:** 20
**Снаряд:** 2x24кг

## Main Workout
- Deadlifts (2x24кг) x5
- Pull-ups (bodyweight) x5
- Farmers walk (2x24кг) 20m

## Cool-down
- Hamstring stretches
- Hip flexor stretches
```

## Example 2: Endurance Training Goal

```markdown
---
date: 2026-02-16
type: Endurance
weight: 78
goal: Improve cardiovascular endurance
---

## Warm-up
- Light jogging (5 mins)
- Dynamic stretching (5 mins)

## Схема
**Тип:** AMRAP
**Время:** 20 минут
**Снаряд:** 2x16кг

## Main Workout
- Kettlebell swings (2x16кг) x20
- Goblet squats (2x16кг) x15
- Push-ups (bodyweight) x10
- Burpees (bodyweight) x5

## Cool-down
- Static stretching (10 mins)
```

## Example 3: Muscle Building Goal

```markdown
---
date: 2026-02-17
type: Hypertrophy
weight: 80
goal: Build upper body muscle mass
---

## Warm-up
- Arm circles (10 reps each direction)
- Shoulder rolls (10 reps each direction)

## Схема
**Тип:** RFT
**Кругов:** 3
**Снаряд:** 2x20кг

## Main Workout
- Strict press (2x20кг) x8
- Bent-over row (2x20кг) x8
- Weighted dips (2x20кг) x8
- Barbell curls (2x20кг) x10

## Cool-down
- Upper body stretching (10 mins)
```

## Example 4: Without Goal (Backward Compatibility)

```markdown
---
date: 2026-02-18
type: Conditioning
weight: 81
---

## Warm-up
- Joint mobility (5 mins)
- Light cardio (5 mins)

## Схема
**Тип:** Tabata
**Кругов:** 8
**Снаряд:** 2x16кг

## Main Workout
- Kettlebell swings (2x16кг) x20
- Goblet squats (2x16кг) x15
- Push-ups (bodyweight) x10

## Cool-down
- Static stretching (10 mins)
```

## How Goals Enhance Analysis

When you include a `goal` field in your workout file, the AI analysis will:

1. **Evaluate goal alignment**: Assess whether your exercise selection supports your stated goal
2. **Provide targeted recommendations**: Suggest specific improvements to better achieve your goal
3. **Consider goal-specific recovery**: Recommend recovery strategies based on both workout intensity and your goal
4. **Assess hormonal response**: Evaluate how your workout affects hormone production in relation to your goal

The goal field is optional but highly recommended for more personalized and actionable feedback.