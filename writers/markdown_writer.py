"""
Markdown Writer - запись результатов анализа обратно в файлы Obsidian.
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
    Записывает AI анализ в секцию ## AI Analysis файла тренировки.
    FIXED: Удаляет ВСЕ существующие секции перед добавлением новой.
    """
    file_path = Path(workout_file)
    
    if not file_path.exists():
        raise FileNotFoundError(f"Файл тренировки не найден: {workout_file}")
    
    # Читаем текущее содержимое файла
    content = file_path.read_text(encoding='utf-8')
    
    # FIX 1: Удаляем ВСЕ существующие секции AI Analysis
    content = re.sub(
        r'## AI Analysis\n.*?(?=\n## |\Z)', 
        '', 
        content, 
        flags=re.DOTALL
    )
    
    # Чистим лишние переносы строк, которые могли остаться
    content = re.sub(r'\n{3,}', '\n\n', content)
    
    # Формируем новую секцию анализа
    analysis_section = format_analysis_section(analysis, gemini_response, user_weight)
    
    # FIX 2: Вставляем анализ ПЕРЕД первой секцией (Схема или Упражнения), а не после
    # Ищем любую секцию ##, которая НЕ AI Analysis (их мы уже удалили, но для надежности)
    first_section_match = re.search(r'\n(## (?!AI Analysis))', content)
    
    if first_section_match:
        # Вставляем перед первой найденой секцией
        insert_pos = first_section_match.start()
        content = content[:insert_pos] + '\n\n' + analysis_section + '\n' + content[insert_pos:]
    else:
        # Если секций нет - добавляем в конец
        content += '\n\n' + analysis_section
    
    # Записываем обновленный контент
    file_path.write_text(content, encoding='utf-8')


def format_analysis_section(
    analysis: Dict,
    gemini_response: str,
    user_weight: int = 70
) -> str:
    """
    Форматирует секцию анализа в markdown.
    """
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    
    # Извлекаем данные из анализа с безопасными значениями
    total_reps = analysis.get('total_reps', 0)
    total_calories = analysis.get('total_calories', 0)
    estimated_time = analysis.get('estimated_time_minutes', 0)
    average_met = analysis.get('average_met', 0.0)
    muscle_balance = analysis.get('muscle_groups_balance', {})
    
    # Формируем секцию
    section = f"""## AI Analysis

**Общая информация:**
- Всего повторений: {total_reps}
- Калории: ~{total_calories:.1f} ккал
- Время: ~{estimated_time} минут
- Средняя интенсивность: {average_met:.1f} MET
- Вес пользователя: {user_weight} кг

**Баланс мышечных групп:**
"""
    
    # Добавляем мышечные группы
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
        # Сортируем по убыванию процента
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
    """
    Обновляет frontmatter упражнения новыми данными.
    """
    import frontmatter
    
    file_path = Path(exercise_file)
    
    if not file_path.exists():
        raise FileNotFoundError(f"Файл упражнения не найден: {exercise_file}")
    
    start_post = frontmatter.load(file_path, encoding='utf-8')
    original_content = start_post.content or ''
    
    if 'met_base' in exercise_data:
        start_post['met_base'] = exercise_data['met_base']
    
    if 'cal_per_rep' in exercise_data:
        start_post['cal_per_rep'] = exercise_data['cal_per_rep']
    
    if 'source' in exercise_data:
        start_post['source'] = exercise_data['source']

    # Обновляем timestamp
    start_post['last_updated'] = datetime.now(timezone.utc).isoformat()
    start_post.content = original_content
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(frontmatter.dumps(start_post))


def write_calorie_summary(
    workout_file: str,
    exercises_breakdown: List[Dict],
    total_calories: int,
    total_reps: int
) -> None:
    """
    Записывает краткую сводку о калориях в конец файла тренировки.
    """
    file_path = Path(workout_file)
    
    if not file_path.exists():
        raise FileNotFoundError(f"Файл тренировки не найден: {workout_file}")
    
    content = file_path.read_text(encoding='utf-8')
    
    # Формируем сводку
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
    """
    Создает пустую секцию AI Analysis для новых файлов.
    """
    return """## AI Analysis

*Анализ еще не проводился*

"""


def remove_analysis_section(workout_file: str) -> None:
    """
    Удаляет секцию AI Analysis из файла тренировки.
    FIXED: Удаляет ВСЕ секции.
    """
    file_path = Path(workout_file)
    
    if not file_path.exists():
        raise FileNotFoundError(f"Файл тренировки не найден: {workout_file}")
    
    content = file_path.read_text(encoding='utf-8')
    
    # Удаляем ВСЕ секции AI Analysis
    content = re.sub(
        r'## AI Analysis\n.*?(?=\n## |\Z)', 
        '', 
        content, 
        flags=re.DOTALL
    )
    
    # Убираем лишние переносы
    content = re.sub(r'\n{3,}', '\n\n', content)
    
    file_path.write_text(content, encoding='utf-8')
