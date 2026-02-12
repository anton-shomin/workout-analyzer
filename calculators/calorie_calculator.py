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
    
    Args:
        cal_per_rep: Estimated calories per repetition.
        reps: Number of repetitions.
        user_weight: User's weight in kg.
        base_weight: Base weight for MET standardization (default: 70).
        
    Returns:
        Estimated calories burned (rounded to integer).
    """
    if cal_per_rep is None or cal_per_rep <= 0:
        return 0
    
    weight_factor = user_weight / base_weight
    calories = cal_per_rep * reps * weight_factor
    
    return round(calories)


def calculate_cal_per_rep(
    met_base: float,
    user_weight: int,
    base_weight: int = 70,
    avg_rep_seconds: float = 3.0
) -> float:
    """
    Calculate estimated calories per repetition.
    
    Args:
        met_base: MET value for the exercise.
        user_weight: User's weight in kg.
        base_weight: Base weight for MET standardization (default: 70).
        avg_rep_seconds: Average seconds per repetition.
        
    Returns:
        Estimated calories per repetition.
    """
    if met_base is None or met_base <= 0:
        return 0.0
    
    hours_per_rep = avg_rep_seconds / 3600
    calories_per_hour = met_base * user_weight
    calories_per_rep = calories_per_hour * hours_per_rep
    
    return round(calories_per_rep, 2)


def calculate_total_volume(
    scheme: dict,
    exercises: list[dict],
    exercises_data: list[dict]
) -> dict:
    """
    Calculate total volume for a workout.
    
    Args:
        scheme: Workout scheme dictionary with pattern and reps.
        exercises: List of exercises with reps.
        exercises_data: List of exercise data with equipment weights.
        
    Returns:
        Dictionary with volume metrics.
    """
    total_reps = scheme.get('total_reps', 0)
    sets = scheme.get('sets', 1)
    
    # Calculate weight per set (simplified - assumes single weight)
    total_weight = 0
    weight_per_set = 0
    
    for exercise, data in zip(exercises, exercises_data):
        reps = exercise.get('reps', [])
        equipment = data.get('equipment', '')
        
        # Extract weight from equipment (e.g., "2x24кг" -> 48)
        weight = extract_weight_from_equipment(equipment)
        
        if weight > 0:
            if isinstance(reps, list):
                exercise_reps = sum(reps) if reps else 0
            else:
                exercise_reps = reps or 0
            exercise_weight = weight * exercise_reps if exercise_reps else weight
            total_weight += exercise_weight
            weight_per_set += weight
    
    # Calculate estimated time
    time_per_rep = scheme.get('time_per_rep', 3)
    rest_between = scheme.get('rest_between', 60)
    
    estimated_seconds = (total_reps * time_per_rep) + ((sets - 1) * rest_between)
    
    return {
        'total_reps': total_reps,
        'total_sets': sets,
        'total_weight_kg': total_weight,
        'weight_per_set_kg': weight_per_set,
        'estimated_seconds': estimated_seconds,
        'estimated_minutes': round(estimated_seconds / 60, 1)
    }


def extract_weight_from_equipment(equipment: str) -> int:
    """
    Extract total weight in kg from equipment string.
    
    Examples:
        "2x24кг" -> 48
        "24кг" -> 24
        "16kg" -> 16
        "Bodyweight" -> 0
    
    Args:
        equipment: Equipment string.
        
    Returns:
        Total weight in kg.
    """
    if not equipment or 'body' in equipment.lower():
        return 0
    
    # Match patterns like "2x24kg", "2x24кг", "24кг", "24kg"
    patterns = [
        r'(\d+)\s*[xX]\s*(\d+)\s*(?:кг|kg)',  # 2x24kg or 2x24кг
        r'(\d+)\s*(?:кг|kg)',                  # 24kg or 24кг
    ]
    
    for pattern in patterns:
        match = re.search(pattern, equipment)
        if match:
            groups = match.groups()
            if len(groups) == 2:
                return int(groups[0]) * int(groups[1])  # 2x24 = 48
            elif len(groups) == 1:
                return int(groups[0])
    
    return 0


def calculate_workout_calories(
    workout_data: dict,
    exercises_data: list[dict],
    user_weight: int,
    base_weight: int = 70
) -> dict:
    """
    Calculate calories and metrics for a complete workout.

    Primary formula: MET × weight_kg × duration_hours
    Fallback: cal_per_rep × reps × weight_factor

    Args:
        workout_data: Parsed workout data dictionary.
        exercises_data: List of exercise data dicts.
        user_weight: User's weight in kg.
        base_weight: Base weight for MET standardization.

    Returns:
        Dictionary with calorie and exercise metrics.
    """
    scheme = workout_data.get('scheme', {})
    exercises = workout_data.get('exercises', [])

    # Determine workout duration (minutes)
    duration_min = workout_data.get('duration', None)
    if duration_min is None:
        duration_min = scheme.get(
            'estimated_time_minutes', 0
        )

    total_calories = 0.0
    per_exercise = []
    muscle_groups_worked = {}
    total_reps = 0
    num_exercises = max(len(exercises), 1)

    for exercise, data in zip(exercises, exercises_data):
        ex_name = exercise.get('name', 'Unknown')
        equipment = exercise.get(
            'equipment', data.get('equipment', '')
        )
        reps = exercise.get('reps', 0)

        met_base = data.get('met_base', 8.0)
        cal_per_rep = data.get('cal_per_rep', 0.0)

        if isinstance(reps, list):
            ex_reps = sum(reps)
        else:
            ex_reps = reps or 0

        total_reps += ex_reps

        # --- Calorie calculation ---
        if duration_min and duration_min > 0:
            # MET-based: distribute total time across
            # exercises proportionally
            ex_minutes = duration_min / num_exercises
            ex_hours = ex_minutes / 60.0
            ex_cal = met_base * user_weight * ex_hours
        elif cal_per_rep and cal_per_rep > 0:
            # Fallback: per-rep formula
            ex_cal = calculate_exercise_calories(
                cal_per_rep, ex_reps,
                user_weight, base_weight
            )
        else:
            # Last resort: estimate from reps
            est_min = (ex_reps * 3.0) / 60.0
            ex_hours = est_min / 60.0
            ex_cal = met_base * user_weight * ex_hours

        # Track muscle groups
        mgs = data.get('muscle_groups', [])
        for mg in mgs:
            muscle_groups_worked[mg] = (
                muscle_groups_worked.get(mg, 0) + 1
            )

        total_calories += ex_cal

        per_exercise.append({
            'name': ex_name,
            'equipment': equipment,
            'reps': ex_reps,
            'calories': round(ex_cal, 1),
            'met_base': met_base,
            'muscle_groups': mgs,
        })

    # Use actual duration if available, else estimate
    if duration_min and duration_min > 0:
        total_time_seconds = int(duration_min * 60)
    else:
        tpr = scheme.get('time_per_rep', 3)
        total_time_seconds = total_reps * tpr + 60

    # Muscle group distribution
    n_ex = len(per_exercise)
    muscle_distribution = {}
    for mg, count in muscle_groups_worked.items():
        pct = round(
            count / n_ex * 100, 1
        ) if n_ex > 0 else 0
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
        'estimated_time_minutes': round(
            total_time_seconds / 60, 1
        ),
        'user_weight': user_weight,
        'calculated_at': datetime.now(
            timezone.utc
        ).isoformat(),
    }


def calculate_muscle_balance(
    exercises_data: list[dict],
    scheme: dict = None
) -> dict:
    """
    Calculate muscle group balance from exercise data.
    
    Args:
        exercises_data: List of exercise data dictionaries.
        scheme: Optional workout scheme dictionary for additional context.
        
    Returns:
        Dictionary with muscle balance analysis including:
        - balance: dict with muscle groups and their percentages
        - primary_muscle: most worked muscle group
        - total_exercises: count of exercises
        - imbalances: list of potential imbalances
        - is_balanced: boolean indicating if workout is balanced
    """
    if scheme is None:
        scheme = {}
    
    muscle_groups = ['shoulders', 'chest', 'back', 'core', 'legs', 'arms', 'fullBody']
    
    counts = {mg: 0 for mg in muscle_groups}
    total_exercises = 0
    
    for data in exercises_data:
        exercise_muscle_groups = data.get('muscle_groups', [])
        for mg in exercise_muscle_groups:
            if mg in counts:
                counts[mg] += 1
        total_exercises += 1
    
    # Calculate percentages and identify imbalances
    balance = {}
    primary_muscle = None
    max_count = 0
    
    for mg in muscle_groups:
        count = counts[mg]
        percentage = round((count / total_exercises * 100), 1) if total_exercises > 0 else 0
        balance[mg] = {
            'count': count,
            'percentage': percentage
        }
        
        if count > max_count:
            max_count = count
            primary_muscle = mg
    
    # Identify potential imbalances
    imbalances = []
    avg_percentage = 100 / len(muscle_groups)
    
    for mg, data in balance.items():
        deviation = data['percentage'] - avg_percentage
        if deviation > 25:  # More than 25% above average
            imbalances.append({
                'muscle': mg,
                'type': 'overdeveloped',
                'deviation': round(deviation, 1)
            })
        elif deviation < -15:  # More than 15% below average
            imbalances.append({
                'muscle': mg,
                'type': 'underdeveloped',
                'deviation': round(abs(deviation), 1)
            })
    
    return {
        'balance': balance,
        'primary_muscle': primary_muscle,
        'total_exercises': total_exercises,
        'imbalances': imbalances,
        'is_balanced': len(imbalances) == 0
    }


def estimate_workout_time(scheme: dict) -> int:
    """
    Estimate workout time in minutes based on scheme.
    
    Args:
        scheme: Workout scheme dictionary containing:
            - type: str (Лесенка, EMOM, Табата, etc.)
            - pattern: str (repetition pattern)
            - reps_per_set: list[int]
            - total_reps: int
            - time_per_rep: int (seconds per repetition)
            - rest_between: int (seconds between sets)
            - sets: int (number of sets)
            
    Returns:
        Estimated workout time in minutes.
    """
    if not scheme:
        return 0
    
    total_reps = scheme.get('total_reps', 0)
    time_per_rep = scheme.get('time_per_rep', 3)  # Default 3 seconds per rep
    rest_between = scheme.get('rest_between', 60)  # Default 60 seconds rest
    sets = scheme.get('sets', 1)
    
    # Calculate base exercise time
    exercise_time = total_reps * time_per_rep
    
    # Add rest time between sets
    rest_time = (sets - 1) * rest_between if sets > 1 else 0
    
    # Add transition time between exercises (30 seconds)
    transition_time = 30
    
    total_seconds = exercise_time + rest_time + transition_time
    
    return round(total_seconds / 60)  # Return minutes


def estimate_workout_intensity(
    calories: float, 
    total_time_minutes: int, 
    user_weight: int
) -> dict:
    """
    Estimate workout intensity based on calories and time.
    
    Args:
        calories: Total calories burned.
        total_time_minutes: Total workout time in minutes.
        user_weight: User's weight in kg.
        
    Returns:
        Dictionary with intensity metrics.
    """
    if total_time_minutes <= 0:
        return {
            'intensity': 'unknown',
            'calories_per_minute': 0,
            'calories_per_kg': 0,
            'description': 'Unable to calculate - no time data'
        }
    
    calories_per_minute = calories / total_time_minutes
    calories_per_kg = calories / user_weight
    
    # Intensity classification
    if calories_per_minute < 5:
        intensity = 'low'
        description = 'Light activity, suitable for recovery'
    elif calories_per_minute < 10:
        intensity = 'moderate'
        description = 'Moderate intensity, good for maintenance'
    elif calories_per_minute < 15:
        intensity = 'high'
        description = 'High intensity, effective for calorie burn'
    else:
        intensity = 'very_high'
        description = 'Very high intensity, significant calorie burn'
    
    return {
        'intensity': intensity,
        'calories_per_minute': round(calories_per_minute, 2),
        'calories_per_kg': round(calories_per_kg, 2),
        'description': description,
        'cal_per_minute_per_kg': round(calories_per_minute / user_weight, 3)
    }
