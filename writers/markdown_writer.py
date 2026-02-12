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
    
    Args:
        workout_file: Путь к файлу тренировки
        analysis: Словарь с результатами анализа из калькулятора
        gemini_response: Текст анализа от Gemini
        user_weight: Вес пользователя для отображения
    """
    file_path = Path(workout_file)
    
    if not file_path.exists():
        raise FileNotFoundError(f"Файл тренировки не найден: {workout_file}")
    
    # Читаем текущее содержимое файла
    content = file_path.read_text(encoding='utf-8')
    
    # Формируем новую секцию анализа
    analysis_section = format_analysis_section(analysis, gemini_response, user_weight)
    
    # Проверяем, есть ли уже секция AI Analysis
    if "## AI Analysis" in content:
        # Обновляем существующую секцию
        pattern = r"## AI Analysis\n.*?(?=\n## |\Z)"
        match = re.search(pattern, content, re.DOTALL)
        if match:
            content = content[:match.start()] + analysis_section + content[match.end():]
        else:
            # Если не нашли границу секции, добавляем в конец
            content += "\n\n" + analysis_section
    else:
        # Добавляем новую секцию перед другими разделами или в конец
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if line.startswith('## ') and line != "## AI Analysis":
                # Вставляем перед первой существующей секцией
                lines.insert(i, analysis_section)
                content = '\n'.join(lines)
                break
        else:
            # Если нет других секций, добавляем в конец
            content += "\n\n" + analysis_section
    
    # Записываем обновленный контент
    file_path.write_text(content, encoding='utf-8')


def format_analysis_section(
    analysis: Dict,
    gemini_response: str,
    user_weight: int = 70
) -> str:
    """
    Форматирует секцию анализа в markdown.
    
    Args:
        analysis: Словарь с результатами анализа
        gemini_response: Текст анализа от Gemini
        user_weight: Вес пользователя
    
    Returns:
        Отформатированная секция анализа в markdown
    """
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    
    # Извлекаем данные из анализа
    total_reps = analysis.get('total_reps', 0)
    total_calories = analysis.get('total_calories', 0)
    estimated_time = analysis.get('estimated_time_minutes', 0)
    average_met = analysis.get('average_met', 0.0)
    muscle_balance = analysis.get('muscle_groups_balance', {})
    
    # Формируем секцию
    section = f"""## AI Analysis

**Общая информация:**
- Всего повторений: {total_reps}
- Калории: ~{total_calories} ккал
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
        for muscle, percentage in sorted(muscle_balance.items(), key=lambda x: -x[1]):
            muscle_name = muscle_groups_mapping.get(muscle, muscle)
            section += f"- {muscle_name}: {percentage}%\n"
    else:
        section += "- Нет данных о мышечных группах\n"
    
    section += f"""
**Рекомендации от Gemini:**
{gemini_response}

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
    
    Args:
        exercise_file: Путь к файлу упражнения
        exercise_data: Словарь с данными для обновления
    """
    import frontmatter
    
    file_path = Path(exercise_file)
    
    if not file_path.exists():
        raise FileNotFoundError(f"Файл упражнения не найден: {exercise_file}")
    
    # Читаем текущий файл
    post = frontmatter.load(file_path, encoding='utf-8')
    
    # ВАЖНО: сохраняем оригинальный контент (тело файла)
    original_content = post.content or ''
    
    # Обновляем frontmatter
    if 'met_base' in exercise_data:
        post['met_base'] = exercise_data['met_base']
    
    if 'cal_per_rep' in exercise_data:
        post['cal_per_rep'] = exercise_data['cal_per_rep']
    
    if 'muscle_groups' in exercise_data:
        post['muscle_groups'] = exercise_data['muscle_groups']
    
    if 'source' in exercise_data:
        post['source'] = exercise_data['source']
    
    # Обновляем timestamp
    post['last_updated'] = datetime.now(timezone.utc).isoformat()
    
    # Гарантируем сохранение оригинального контента
    post.content = original_content
    
    # Записываем обратно
    with open(file_path, 'w', encoding='utf-8') as f:
        content = frontmatter.dumps(post)
        f.write(content)


def write_calorie_summary(
    workout_file: str,
    exercises_breakdown: List[Dict],
    total_calories: int,
    total_reps: int
) -> None:
    """
    Записывает краткую сводку о калориях в конец файла тренировки.
    
    Args:
        workout_file: Путь к файлу тренировки
        exercises_breakdown: Разбивка по упражнениям
        total_calories: Всего калорий
        total_reps: Всего повторений
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
    
    # Добавляем в конец файла
    content += summary
    
    file_path.write_text(content, encoding='utf-8')


def create_empty_analysis_section() -> str:
    """
    Создает пустую секцию AI Analysis для новых файлов.
    
    Returns:
        Пустая секция AI Analysis
    """
    return """## AI Analysis

*Анализ еще не проводился*

"""


def remove_analysis_section(workout_file: str) -> None:
    """
    Удаляет секцию AI Analysis из файла тренировки.
    
    Args:
        workout_file: Путь к файлу тренировки
    """
    file_path = Path(workout_file)
    
    if not file_path.exists():
        raise FileNotFoundError(f"Файл тренировки не найден: {workout_file}")
    
    content = file_path.read_text(encoding='utf-8')
    
    # Удаляем секцию AI Analysis
    pattern = r"\n## AI Analysis\n.*?(?=\n## |\Z)"
    content = re.sub(pattern, '', content, flags=re.DOTALL)
    
    # Убираем лишние переносы
    content = re.sub(r'\n{3,}', '\n\n', content)
    
    file_path.write_text(content, encoding='utf-8')
