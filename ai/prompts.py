"""
Shared prompt generation and utility logic for AI clients.
"""

import re
import os


def build_workout_prompt(
    workout_data: dict,
    calories: int,
    muscle_balance: dict,
    actual_duration_minutes: int = 0,
    exercises_details: list = None
) -> str:
    """
    Build a prompt for AI to analyze a workout with Goal evaluation.
    """
    import os
    date = workout_data.get("date", "Unknown")
    workout_type = workout_data.get("type", "Unknown")
    goal = workout_data.get("goal", "Не указано")  # Get goal
    scheme = workout_data.get("scheme", {})
    exercises = workout_data.get("exercises", [])

    # Build scheme description
    scheme_type = scheme.get("type", workout_type)
    pattern = scheme.get("pattern", "")
    total_reps = scheme.get("total_reps", 0)

    # Use passed duration or fall back to estimation if 0
    if actual_duration_minutes > 0:
        estimated_time = actual_duration_minutes
    else:
        # Fallback estimation logic
        reps_per_set = scheme.get("reps_per_set", [])
        time_per_rep = scheme.get("time_per_rep", 0)
        rest_between = scheme.get("rest_between", 0)

        estimated_time = (
            total_reps * time_per_rep / 60 +
            (total_reps / max(len(reps_per_set), 1) - 1) * rest_between / 60
        )
        estimated_time = max(estimated_time, 10)  # Minimum 10 minutes

    # Build exercises list with descriptions
    exercises_list = []

    # Create a map of exercise descriptions: {name: description}
    descriptions_map = {}
    if exercises_details:
        for ex_data in exercises_details:
            name = ex_data.get('name')
            desc = ex_data.get('description', '')
            if name and desc:
                descriptions_map[name] = desc

    for i, ex in enumerate(exercises, 1):
        name = ex.get('name', 'Unknown')
        ex_str = f"{i}. {name}"

        if ex.get('equipment'):
            ex_str += f" ({ex.get('equipment')})"
        if ex.get('reps'):
            ex_str += f" - {ex.get('reps')} reps"

        # Add exercise description context for AI
        if name in descriptions_map:
            short_desc = descriptions_map[name].replace('\n', ' ')[:200]
            ex_str += f"\n   > Контекст: {short_desc}"

        exercises_list.append(ex_str)

    exercises_str = "\n".join(
        exercises_list) if exercises_list else "No exercises listed"

    # Build muscle balance string
    if muscle_balance:
        balance_parts = [f"- {k}: {v}%" for k,
                         v in sorted(muscle_balance.items())]
        balance_str = "\n".join(balance_parts)
    else:
        balance_str = "No muscle balance data available"

    # Calculate intensity before template formatting
    intensity = round(calories/max(estimated_time, 1), 1)

    # Load prompt template
    template_path = os.path.join(os.path.dirname(
        os.path.dirname(__file__)), 'Templates', 'prompt_workout.txt')
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            template = f.read()
    except FileNotFoundError:
        # Fallback if template file is missing - updated template with goal evaluation
        template = """Ты эксперт по функциональному тренингу, гиревому спорту и физиологии. Проанализируй тренировку атлета (мужчина, 81 кг).

**Контекст:**
- Дата: {date}
- Тип: {workout_type}
- Схема: {scheme_type} ({pattern})
- ЦЕЛЬ ТРЕНИРОВКИ: "{goal}"

**Упражнения:**
{exercises_str}

**Метрики:**
- Всего повторений: {total_reps}
- Калории: {calories} ккал
- Время: {int(estimated_time)} минут
- Интенсивность (Kcal/min): {intensity}

**Баланс мышц:**
{balance_str}

Дай жесткий и честный анализ по пунктам:
1. **Соответствие цели** (САМОЕ ВАЖНОЕ):
   - Способствует ли эта подборка упражнений и режим работы (EMOM/Ladder) достижению цели "{goal}"?
   - Если нет, объясни почему.
   - Оцени гормональный отклик (тестостерон/гормон роста) исходя из объема и базовых движений.

2. **Анализ нагрузки**:
   - Оцени плотность (повторений в минуту).
   - Нет ли дисбаланса (например, мало тяг или жимов).

3. **Рекомендации**:
   - Что изменить, чтобы лучше попадать в цель "{goal}" в следующий раз.

4. **Восстановление**:
   - Сколько отдыхать исходя из ЦНС-нагрузки этой сессии.

Формат: Markdown. Не лей воду, пиши по делу."""

    prompt = template.format(
        date=date,
        type=workout_type,
        goal=goal,
        scheme_type=scheme_type,
        pattern=pattern if pattern else 'Standard',
        exercises_str=exercises_str,
        total_reps=total_reps,
        calories=calories,
        estimated_time=int(estimated_time),
        intensity=intensity,
        balance_str=balance_str
    )

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
