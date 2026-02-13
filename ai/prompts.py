"""
Shared prompt generation with EXERCISE DETAILS support
"""

import re


def build_workout_prompt(
    workout_data: dict,
    calories: int,
    muscle_balance: dict,
    actual_duration_minutes: int = 0,
    exercises_details: list = None  # ← КРИТИЧНО!
) -> str:
    """
    Build prompt with FULL EXERCISE DETAILS for complex movements.
    """
    date = workout_data.get("date", "Unknown")
    workout_type = workout_data.get("type", "Unknown")
    goal = workout_data.get("goal", "Не указано")
    scheme = workout_data.get("scheme", {})
    exercises = workout_data.get("exercises", [])

    scheme_type = scheme.get("type", workout_type)
    pattern = scheme.get("pattern", "")
    total_reps = scheme.get("total_reps", 0)

    if total_reps == 0:
        total_reps = sum([ex.get('reps', 0) or 0 for ex in exercises])

    # Duration
    if actual_duration_minutes > 0:
        estimated_time = actual_duration_minutes
    else:
        reps_per_set = scheme.get("reps_per_set", [])
        time_per_rep = scheme.get("time_per_rep", 0)
        rest_between = scheme.get("rest_between", 0)
        estimated_time = (
            total_reps * time_per_rep / 60 +
            (total_reps / max(len(reps_per_set), 1) - 1) * rest_between / 60
        )
        estimated_time = max(estimated_time, 10)

    # IMPROVED: Include exercise components and muscle groups
    exercises_list = []

    for i, ex in enumerate(exercises, 1):
        name = ex.get('name', 'Unknown')
        reps = ex.get('reps', 0)
        equipment = ex.get('equipment', '')

        # Basic info
        ex_str = f"{i}. **{name}**"
        if equipment:
            ex_str += f" ({equipment})"
        if reps:
            ex_str += f" — {reps} повторений"

        # NEW: Add detailed info if available
        if exercises_details and i-1 < len(exercises_details):
            detail = exercises_details[i-1]

            # Check for complex exercise
            components = detail.get('components', [])
            complexity = detail.get('complexity_multiplier', 1)

            if components and len(components) > 1:
                ex_str += f"\n   **КОМПЛЕКСНОЕ упражнение** ({complexity} компонентов):"
                for j, comp in enumerate(components, 1):
                    ex_str += f"\n   {j}. {comp}"

            # Add muscle groups worked
            muscle_groups = detail.get('muscle_groups', [])
            if muscle_groups:
                muscle_groups_ru = {
                    'shoulders': 'плечи',
                    'chest': 'грудь',
                    'back': 'спина',
                    'core': 'кор',
                    'legs': 'ноги',
                    'arms': 'руки',
                    'fullBody': 'всё тело'
                }
                muscles_str = ', '.join([
                    muscle_groups_ru.get(mg, mg) for mg in muscle_groups
                ])
                ex_str += f"\n   Работающие мышцы: {muscles_str}"

        exercises_list.append(ex_str)

    exercises_str = "\n\n".join(
        exercises_list) if exercises_list else "Упражнения не указаны"

    # Muscle balance
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
        balance_parts = []
        for k, v in sorted(muscle_balance.items(), key=lambda x: -x[1]):
            muscle_ru = muscle_groups_mapping.get(k, k)
            balance_parts.append(f"- {muscle_ru}: {v}%")
        balance_str = "\n".join(balance_parts)
    else:
        balance_str = "Нет данных о балансе мышц"

    intensity = round(calories/max(estimated_time, 1), 1)

    # Template with CRITICAL instruction about components
    template = """Ты эксперт по функциональному тренингу и физиологии. Проанализируй тренировку атлета (мужчина, 81 кг).

**КРИТИЧЕСКИ ВАЖНО:**
Если упражнение КОМПЛЕКСНОЕ (содержит несколько компонентов):
1. **Анализируй КАЖДЫЙ компонент отдельно**
2. Учитывай работу мышц во ВСЕХ компонентах
3. НЕ пиши "упражнение не описано" — компоненты УКАЗАНЫ НИЖЕ!

Например, если "злой поток" включает:
- Турецкий подъем → МАКСИМАЛЬНАЯ работа стабилизаторов плеча
- Мельница → ИНТЕНСИВНАЯ работа кора и стабилизаторов
- Жимы → ОБЯЗАТЕЛЬНАЯ работа грудных

ТО **ЗАПРЕЩЕНО** писать:
❌ "Стабилизаторы плеча не работают"
❌ "Грудь: 0%"
❌ "Добавьте упражнения на кор"
❌ "Недостаточно внимания к стабилизаторам"

---

## Контекст тренировки
- Дата: {date}
- Тип: {type}
- Схема: {scheme_type} ({pattern})
- **ЦЕЛЬ**: "{goal}"

## Упражнения (с детализацией)
{exercises_str}

## Метрики
- Всего повторений: {total_reps}
- Калории: {calories} ккал
- Время: {estimated_time} мин
- Интенсивность: {intensity} ккал/мин

## Баланс мышц
{balance_str}

---

## Формат ответа

### Соответствие цели
**Оценка:** [число]/10
- Способствует ли подборка упражнений (УЧИТЫВАЯ ВСЕ КОМПОНЕНТЫ!) достижению цели "{goal}"?
- Если да — объясни почему конкретно, ссылаясь на компоненты
- Гормональный отклик: [оценка]

### Анализ нагрузки
- Плотность: [X] повторений/минуту — [вердикт]
- Дисбаланс: [есть/нет] — НО учитывай КОМПОНЕНТЫ комплексных упражнений!

### Рекомендации
1. Что добавить/убрать (НЕ предлагай то, что УЖЕ есть в компонентах!)
2. Конкретные упражнения-замены
3. Изменения в режиме

### Восстановление
- Рекомендуемый отдых: [X] часов
- Причина: [обоснование]

---

Твой анализ (будь ВНИМАТЕЛЕН к компонентам упражнений):
"""

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
    """Clean up AI response."""
    if not text:
        return ""

    cleaned = re.sub(r'^```markdown?\s*', '', text, flags=re.MULTILINE)
    cleaned = re.sub(r'\s*```\s*$', '', cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)

    return cleaned.strip()
