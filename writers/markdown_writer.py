"""
Markdown Writer - FIXED version with proper duplicate handling
"""

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional


def write_analysis_to_workout(
    workout_file: str,
    analysis: Dict,
    gemini_response: str,
    user_weight: int = 70
) -> None:
    """
    Writes AI analysis to ## AI Analysis section.
    FIXED: Removes ALL existing AI Analysis sections before adding new one
    """
    file_path = Path(workout_file)

    if not file_path.exists():
        raise FileNotFoundError(f"Workout file not found: {workout_file}")

    content = file_path.read_text(encoding='utf-8')

    # FIX 1: Remove ALL existing AI Analysis sections (not just first)
    content = re.sub(
        r'## AI Analysis\n.*?(?=\n## |\Z)',
        '',
        content,
        flags=re.DOTALL
    )

    # Clean up extra newlines
    content = re.sub(r'\n{3,}', '\n\n', content)

    # Format new analysis section
    analysis_section = format_analysis_section(
        analysis, gemini_response, user_weight)

    # FIX 2: Insert analysis AT THE END (after all sections)
    # This ensures AI Analysis is always the last section
    content = content.rstrip() + '\n\n' + analysis_section

    # Write updated content
    file_path.write_text(content, encoding='utf-8')


def format_analysis_section(
    analysis: Dict,
    gemini_response: str,
    user_weight: int = 70
) -> str:
    """
    Formats analysis section with improved structure
    IMPROVED: Better error handling and data validation
    """
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    # Extract data with safe defaults
    total_reps = analysis.get('total_reps', 0)
    total_calories = analysis.get('total_calories', 0)
    estimated_time = analysis.get('estimated_time_minutes', 0)
    average_met = analysis.get('average_met', 0.0)
    muscle_balance = analysis.get('muscle_groups_balance', {})

    # Format section
    section = f"""## AI Analysis

**Общая информация:**
- Всего повторений: {total_reps}
- Калории: ~{total_calories:.1f} ккал
- Время: ~{estimated_time} минут
- Средняя интенсивность: {average_met:.1f} MET
- Вес пользователя: {user_weight} кг

**Баланс мышечных групп:**
"""

    # Muscle groups mapping
    muscle_groups_mapping = {
        'shoulders': 'Плечи',
        'legs': 'Ноги',
        'core': 'Пресс',
        'back': 'Спина',
        'chest': 'Грудь',
        'arms': 'Руки',
        'fullBody': 'Всё тело'
    }

    if muscle_balance:
        # Sort by percentage descending
        for muscle, percentage in sorted(muscle_balance.items(), key=lambda x: -x[1]):
            muscle_name = muscle_groups_mapping.get(muscle, muscle)
            section += f"- {muscle_name}: {percentage}%\n"
    else:
        section += "- Нет данных о мышечных группах\n"

    section += f"""
**Рекомендации от Gemini:**
{gemini_response.strip()}

---
*Анализ от {timestamp}*
"""

    return section


def update_exercise_data(
    exercise_file: str,
    exercise_data: Dict
) -> None:
    """Unchanged - updates exercise frontmatter"""
    import frontmatter

    file_path = Path(exercise_file)

    if not file_path.exists():
        raise FileNotFoundError(f"Exercise file not found: {exercise_file}")

    post = frontmatter.load(file_path, encoding='utf-8')
    original_content = post.content or ''

    if 'met_base' in exercise_data:
        post['met_base'] = exercise_data['met_base']

    if 'cal_per_rep' in exercise_data:
        post['cal_per_rep'] = exercise_data['cal_per_rep']

    if 'muscle_groups' in exercise_data:
        post['muscle_groups'] = exercise_data['muscle_groups']

    if 'source' in exercise_data:
        post['source'] = exercise_data['source']

    post['last_updated'] = datetime.now(timezone.utc).isoformat()
    post.content = original_content

    with open(file_path, 'w', encoding='utf-8') as f:
        content = frontmatter.dumps(post)
        f.write(content)


def write_calorie_summary(
    workout_file: str,
    exercises_breakdown: List[Dict],
    total_calories: int,
    total_reps: int
) -> None:
    """Unchanged - writes calorie summary table"""
    file_path = Path(workout_file)

    if not file_path.exists():
        raise FileNotFoundError(f"Workout file not found: {workout_file}")

    content = file_path.read_text(encoding='utf-8')

    summary = f"""
---

## Сводка по калориям

| Упражнение | Повторения | Калории | MET |
|------------|------------|---------|-----|
"""

    for exercise in exercises_breakdown:
        name = exercise.get('name', 'Unknown')
        reps = exercise.get('reps', 0)
        calories = exercise.get('calories', 0)
        met = exercise.get('met', 0.0)
        summary += f"| {name} | {reps} | {calories} | {met:.1f} |\n"

    summary += f"""
**Итого:** {total_reps} повторений, ~{total_calories} ккал
"""

    content += summary
    file_path.write_text(content, encoding='utf-8')


def create_empty_analysis_section() -> str:
    """Unchanged"""
    return """## AI Analysis

*Анализ еще не проводился*

"""


def remove_analysis_section(workout_file: str) -> None:
    """
    Removes AI Analysis section from workout file
    FIXED: Removes ALL analysis sections, not just first
    """
    file_path = Path(workout_file)

    if not file_path.exists():
        raise FileNotFoundError(f"Workout file not found: {workout_file}")

    content = file_path.read_text(encoding='utf-8')

    # Remove ALL AI Analysis sections
    content = re.sub(
        r'## AI Analysis\n.*?(?=\n## |\Z)',
        '',
        content,
        flags=re.DOTALL
    )

    # Clean up extra newlines
    content = re.sub(r'\n{3,}', '\n\n', content)

    file_path.write_text(content, encoding='utf-8')
