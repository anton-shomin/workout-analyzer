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
    IMPROVED: Includes few-shot examples and strict structure.
    """
    date = workout_data.get("date", "Unknown")
    workout_type = workout_data.get("type", "Unknown")
    goal = workout_data.get("goal", "Не указано")
    scheme = workout_data.get("scheme", {})
    exercises = workout_data.get("exercises", [])

    # Build scheme description
    scheme_type = scheme.get("type", workout_type)
    pattern = scheme.get("pattern", "")
    total_reps = scheme.get("total_reps", 0)

    # Calculate actual reps if not in scheme
    if total_reps == 0:
        total_reps = sum([ex.get('reps', 0) or 0 for ex in exercises])

    # Duration logic
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

    # IMPROVEMENT: Prioritize exercises by volume, remove verbose descriptions
    exercises_list = []
    
    for i, ex in enumerate(exercises, 1):
        name = ex.get('name', 'Unknown')
        reps = ex.get('reps', 0)
        equipment = ex.get('equipment', '')
        
        # Format: "1. Name (equipment) - X reps"
        ex_str = f"{i}. {name}"
        if equipment:
            ex_str += f" ({equipment})"
        if reps:
            ex_str += f" - {reps} повторений"
        
        exercises_list.append(ex_str)

    exercises_str = "\n".join(exercises_list) if exercises_list else "Упражнения не указаны"

    # Build muscle balance
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

    # Calculate intensity
    intensity = round(calories/max(estimated_time, 1), 1)

    # Improved template with few-shot examples
    template = """Ты эксперт по функциональному тренингу и физиологии. Проанализируй тренировку атлета (мужчина, 81 кг).

**ВАЖНО: Твоя главная задача — оценить соответствие тренировки ЦЕЛИ.**

## Контекст тренировки
- Дата: {date}
- Тип: {type}
- Схема: {scheme_type} ({pattern})
- **ЦЕЛЬ**: "{goal}"

## Упражнения
{exercises_str}

## Метрики
- Всего повторений: {total_reps}
- Калории: {calories} ккал
- Время: {estimated_time} мин
- Интенсивность: {intensity} ккал/мин

## Баланс мышц
{balance_str}

---

## Формат ответа (обязательно следуй структуре)

### Соответствие цели
**Оценка:** [число]/10
- Способствует ли подборка упражнений достижению цели "{goal}"?
- Если нет — почему конкретно?
- Гормональный отклик (тестостерон/гормон роста): [оценка]

### Анализ нагрузки
- Плотность: [X] повторений/минуту — [вердикт]
- Дисбаланс: [есть/нет] — [объяснение]

### Рекомендации
1. Что добавить/убрать для лучшего попадания в цель
2. Конкретные упражнения-замены
3. Изменения в режиме (вес/объем/отдых)

### Восстановление
- Рекомендуемый отдых: [X] часов
- Причина: [ЦНС-нагрузка/микротравмы/etc]

---

## Пример хорошего анализа

**Цель:** "Увеличить силу в становой тяге"

### Соответствие цели
**Оценка:** 4/10
Тренировка включает много жимов (60% объема), но мало тяговых движений (20%). Для силы в становой нужна мощная задняя цепь, а здесь основная работа — плечи и грудь.

**Гормональный отклик:** Умеренный. Базовые движения есть, но без тяжелых приседов/тяг эффект ограничен.

### Анализ нагрузки
- Плотность: 12 повторений/минуту — высокая для силовой работы (лучше 4-6)
- Дисбаланс: Критический. 0% работы задней цепи (ягодицы, бицепс бедра)

### Рекомендации
1. Добавить румынскую тягу 5x5 вместо жимов
2. Заменить отжимания на тягу в наклоне
3. Увеличить вес, снизить повторения до 3-5

### Восстановление
- 72 часа отдыха
- Причина: высокая ЦНС-нагрузка от тяжелых базовых движений

---

Теперь твой анализ (будь конкретен, без воды):
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
    """
    Clean up AI response if it has markdown code blocks validation.
    """
    if not text:
        return ""

    # Remove markdown code blocks
    cleaned = re.sub(r'^```markdown?\s*', '', text, flags=re.MULTILINE)
    cleaned = re.sub(r'\s*```\s*$', '', cleaned, flags=re.MULTILINE)
    
    # Remove excessive newlines
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
    
    # Remove leading/trailing whitespace
    return cleaned.strip()
