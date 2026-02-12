"""
Shared prompt generation and utility logic for AI clients.
"""

import re


def build_workout_prompt(
    workout_data: dict,
    calories: int,
    muscle_balance: dict
) -> str:
    """
    Build a prompt for AI to analyze a workout.

    Args:
        workout_data: Parsed workout data from workout_parser.
        calories: Calculated calories burned.
        muscle_balance: Dictionary of muscle group percentages.

    Returns:
        Formatted prompt string.
    """
    date = workout_data.get("date", "Unknown")
    workout_type = workout_data.get("type", "Unknown")
    scheme = workout_data.get("scheme", {})
    exercises = workout_data.get("exercises", [])

    # Build scheme description
    scheme_type = scheme.get("type", workout_type)
    pattern = scheme.get("pattern", "")
    reps_per_set = scheme.get("reps_per_set", [])
    total_reps = scheme.get("total_reps", 0)
    time_per_rep = scheme.get("time_per_rep", 0)
    rest_between = scheme.get("rest_between", 0)

    # Calculate estimated time
    estimated_time = (
        total_reps * time_per_rep / 60 +
        (total_reps / max(len(reps_per_set), 1) - 1) * rest_between / 60
    )
    estimated_time = max(estimated_time, 10)  # Minimum 10 minutes

    # Build exercises list
    exercises_list = []
    for i, ex in enumerate(exercises, 1):
        ex_str = f"{i}. {ex.get('name', 'Unknown')}"
        if ex.get('equipment'):
            ex_str += f" ({ex.get('equipment')})"
        if ex.get('reps'):
            ex_str += f" - {ex.get('reps')} reps"
        exercises_list.append(ex_str)

    exercises_str = "\n".join(exercises_list) if exercises_list else "No exercises listed"

    # Build muscle balance string
    if muscle_balance:
        balance_parts = [f"- {k}: {v}%" for k, v in sorted(muscle_balance.items())]
        balance_str = "\n".join(balance_parts)
    else:
        balance_str = "No muscle balance data available"

    prompt = f"""Ты эксперт по силовым тренировкам с гирями. Проанализируй тренировку:

**Дата:** {date}
**Тип:** {workout_type}
**Схема:** {scheme_type}
**Паттерн:** {pattern if pattern else 'Standard'}

**Упражнения:**
{exercises_str}

**Метрики:**
- Всего повторений: {total_reps}
- Расчетные калории: {calories} ккал
- Примерное время: {int(estimated_time)} минут

**Баланс мышечных групп:**
{balance_str}

Дай структурированный анализ по пунктам:
1. **Баланс мышечных групп** - какие группы работали, есть ли дисбаланс
2. **Объем и интенсивность** - достаточный ли объем, не перетренировка ли
3. **Рекомендации** - что добавить/убрать в следующий раз
4. **Восстановление** - сколько дней отдыха нужно

Формат ответа: структурированный markdown.
"""
    return prompt


def clean_markdown_response(text: str) -> str:
    """
    Clean up AI response if it has markdown code blocks validation.

    Args:
        text: Raw response text.

    Returns:
        Cleaned text.
    """
    if not text:
        return ""

    cleaned = re.sub(r'^```markdown?\s*', '', text, flags=re.MULTILINE)
    cleaned = re.sub(r'\s*```\s*$', '', cleaned, flags=re.MULTILINE)

    return cleaned.strip()
