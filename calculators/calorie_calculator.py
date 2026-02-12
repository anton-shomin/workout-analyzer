"""
Calorie calculator module for workout analyzer.

Provides functions to calculate calories and metrics for workouts
based on exercise data, MET values, and user weight.
"""

import math
import re
from datetime import datetime, timezone
from typing import Optional


def calculate_exercise_calories(
    cal_per_rep: float,
    reps: int,
    user_weight: int,
    base_weight: int = 70
) -> int:
    """
    Calculate calories burned for an exercise based on calories per repetition.

    Formula: calories = cal_per_rep * reps * (user_weight / base_weight)
    """
    if cal_per_rep is None or cal_per_rep <= 0:
        return 0

    weight_factor = user_weight / base_weight
    calories = cal_per_rep * reps * weight_factor

    return round(calories)


def calculate_workout_calories(
    workout_data: dict,
    exercises_data: list[dict],
    user_weight: int,
    base_weight: int = 70
) -> dict:
    """
    Calculate calories and metrics for a complete workout.

    CRITICAL UPDATE: Prioritizes Rep-based calculation (Volume Load) over
    Time-based (MET) for high-density workouts to avoid underestimation.
    """
    scheme = workout_data.get('scheme', {})
    exercises = workout_data.get('exercises', [])

    # Determine workout duration (minutes)
    duration_min = workout_data.get('duration', None)
    if duration_min is None:
        duration_min = scheme.get('estimated_time_minutes', 0)

    total_calories = 0.0
    per_exercise = []
    muscle_groups_worked = {}
    total_reps = 0

    # Calculate calories for each exercise
    for exercise, data in zip(exercises, exercises_data):
        ex_name = exercise.get('name', 'Unknown')
        equipment = exercise.get('equipment', data.get('equipment', ''))

        # Get reps
        reps = exercise.get('reps', 0)
        if isinstance(reps, list):
            ex_reps = sum(reps)
        else:
            ex_reps = reps or 0
        total_reps += ex_reps

        # Get intensity data
        met_base = data.get('met_base', 8.0)
        cal_per_rep = data.get('cal_per_rep', 0.0)

        # --- LOGIC FIX: PRIORITY TO VOLUME ---
        ex_cal = 0

        # 1. Try calculating by REPS first (Most accurate for lifting/kettlebells)
        if cal_per_rep > 0 and ex_reps > 0:
            ex_cal = calculate_exercise_calories(
                cal_per_rep, ex_reps, user_weight, base_weight
            )

        # 2. If no rep data, fall back to TIME based (MET)
        elif duration_min and duration_min > 0:
            num_exercises = len(exercises)
            ex_minutes = duration_min / max(num_exercises, 1)
            ex_hours = ex_minutes / 60.0
            ex_cal = met_base * user_weight * ex_hours

        # 3. Last resort: Estimate time from reps (3 sec rule)
        else:
            est_min = (ex_reps * 3.0) / 60.0
            ex_hours = est_min / 60.0
            ex_cal = met_base * user_weight * ex_hours

        # Track muscle groups
        mgs = data.get('muscle_groups', [])
        for mg in mgs:
            muscle_groups_worked[mg] = muscle_groups_worked.get(mg, 0) + 1

        total_calories += ex_cal

        per_exercise.append({
            'name': ex_name,
            'equipment': equipment,
            'reps': ex_reps,
            'calories': round(ex_cal, 1),
            'met_base': met_base,
            'cal_per_rep': cal_per_rep,
            'method': 'reps' if (cal_per_rep > 0 and ex_reps > 0) else 'time'
        })

    # Duration calculations
    if duration_min and duration_min > 0:
        total_time_seconds = int(duration_min * 60)
    else:
        tpr = scheme.get('time_per_rep', 3)
        total_time_seconds = total_reps * tpr + 60

    # Muscle group distribution
    n_ex = len(per_exercise)
    muscle_distribution = {}
    for mg, count in muscle_groups_worked.items():
        pct = round(count / n_ex * 100, 1) if n_ex > 0 else 0
        muscle_distribution[mg] = {
            'count': count,
            'percentage': pct,
        }

    return {
        'total_calories': round(total_calories, 1),
        'per_exercise': per_exercise,
        'muscle_group_distribution': muscle_distribution,
        'total_reps': total_reps,
        'total_sets': scheme.get('sets', 1),
        'total_time_seconds': total_time_seconds,
        'estimated_time_minutes': round(total_time_seconds / 60, 1),
        'user_weight': user_weight,
        'calculated_at': datetime.now(timezone.utc).isoformat(),
    }


def calculate_muscle_balance(
    exercises_data: list[dict],
    exercises: list[dict] = None,
    scheme: dict = None
) -> dict:
    """
    Calculate muscle group balance from exercise data using volume.
    """
    if scheme is None:
        scheme = {}

    muscle_groups = [
        'shoulders', 'chest', 'back', 'core', 'legs', 'arms', 'fullBody'
    ]
    volume_by_muscle = {mg: 0.0 for mg in muscle_groups}
    total_volume = 0.0

    # Process exercises
    if exercises:
        iterator = zip(exercises, exercises_data)
    else:
        iterator = zip(
            [{'reps': 10}] * len(exercises_data), exercises_data
        )

    for exercise, data in iterator:
        reps = exercise.get('reps', 0)
        if isinstance(reps, list):
            total_reps = sum(reps)
        else:
            total_reps = reps or 0

        # Simplified volume weight logic
        equipment = exercise.get('equipment') or data.get('equipment', '')
        weight = extract_weight_from_equipment(equipment)
        if weight == 0:
            weight = 30  # Bodyweight fallback

        exercise_volume = total_reps * weight

        exercise_mgs = data.get('muscle_groups', [])
        for mg in exercise_mgs:
            if mg in volume_by_muscle:
                volume_by_muscle[mg] += exercise_volume

        total_volume += exercise_volume * len(
            [mg for mg in exercise_mgs if mg in volume_by_muscle]
        )

    # Calculate percentages
    balance = {}
    primary_muscle = None
    max_volume = 0.0

    for mg in muscle_groups:
        volume = volume_by_muscle[mg]
        percentage = (
            round((volume / total_volume * 100), 1)
            if total_volume > 0 else 0
        )
        balance[mg] = {'volume': round(volume), 'percentage': percentage}

        if volume > max_volume:
            max_volume = volume
            primary_muscle = mg

    return {
        'balance': balance,
        'primary_muscle': primary_muscle,
        'total_volume': round(total_volume)
    }


def extract_weight_from_equipment(equipment: str) -> int:
    """Helper to extract weight from string."""
    if not equipment or 'body' in equipment.lower():
        return 0
    patterns = [r'(\d+)\s*[xX]\s*(\d+)', r'(\d+)\s*(?:кг|kg)']
    for p in patterns:
        match = re.search(p, equipment)
        if match:
            g = match.groups()
            if len(g) == 2:
                return int(g[0]) * int(g[1])
            return int(g[0])
    return 0
