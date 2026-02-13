import re
import frontmatter


def parse_workout_file(file_path):
    """
    Parses a workout markdown file.
    Returns a dictionary with metadata and exercises.
    Supports messy formats and implicit exercise lists.
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        post = frontmatter.load(f)

    content = post.content
    date_str = str(post.metadata.get('date', ''))
    workout_type = post.metadata.get('type', 'Unknown')
    weight = post.metadata.get('weight', 0)

    # Парсинг времени (Duration)
    duration = post.metadata.get('duration')
    if duration and isinstance(duration, str):
        if 'min' in duration or 'мин' in duration:
            try:
                duration = float(re.search(r'(\d+)', duration).group(1))
            except:
                duration = 0
        elif ':' in duration:
            try:
                parts = duration.split(':')
                duration = int(parts[0]) + int(parts[1])/60
            except:
                duration = 0
    elif not duration:
        duration = 0

    scheme = _parse_scheme(content)
    # Передаем весь контент, чтобы найти упражнения даже без заголовка
    exercises = _parse_exercises(content)

    return {
        'date': date_str,
        'type': workout_type,
        'weight': weight,
        'duration': duration,
        'goal': post.metadata.get('goal', 'Не указана'),
        'scheme': scheme,
        'exercises': exercises,
        'raw_content': content
    }


def _parse_scheme(content):
    scheme = {}
    scheme_match = re.search(r'## Схема\n(.*?)\n##', content, re.DOTALL)
    if scheme_match:
        scheme_text = scheme_match.group(1)
        for line in scheme_text.strip().split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip().replace('**', '').lower()
                value = value.strip()

                if 'тип' in key:
                    scheme['type'] = value
                elif 'кругов' in key:
                    try:
                        scheme['rounds'] = int(
                            re.search(r'\d+', value).group())
                    except:
                        scheme['rounds'] = 0
                elif 'снаряд' in key:
                    scheme['weight'] = value
                elif 'паттерн' in key:
                    scheme['pattern'] = value

    return scheme


def _parse_exercises(content):
    exercises = []

    # Шаг 1. Пытаемся найти явную секцию "Упражнения"
    ex_section_match = re.search(
        r'## Упражнения\n(.*?)(?:\n##|$)', content, re.DOTALL)

    lines_to_process = []

    if ex_section_match:
        # Если секция есть - берем строки из нее
        block = ex_section_match.group(1)
        lines_to_process = block.strip().split('\n')
    else:
        # Если секции НЕТ - берем весь текст, но выкидываем "Схему" и "Заметки"
        # чтобы не парсить лишнего
        clean_content = re.sub(r'## Схема.*?(?:\n##|$)',
                               '', content, flags=re.DOTALL)
        clean_content = re.sub(r'## Заметки.*?(?:\n##|$)',
                               '', clean_content, flags=re.DOTALL)
        # Убираем заголовок H1
        clean_content = re.sub(r'# .*?\n', '', clean_content)

        lines_to_process = clean_content.strip().split('\n')

    # Шаг 2. Анализируем строки
    for line in lines_to_process:
        line = line.strip()
        if not line:
            continue

        # Пропускаем заголовки Markdown внутри текста
        if line.startswith('#'):
            continue

        # Чистим от буллитов и ссылок
        # Убираем маркеры списка "1.", "- ", "* "
        clean_line = line.lstrip('-*1234567890. ')
        clean_line = clean_line.replace('[[', '').replace(']]', '')

        if '|' in clean_line:
            clean_line = clean_line.split('|')[0]

        # Логика поиска повторений
        reps = 0

        # Вариант 1: "5x5" или "5х5" (рус х)
        sets_reps_match = re.search(r'(\d+)\s*[xх]\s*(\d+)', clean_line)

        # Вариант 2: "Упражнение - 5" или "Упражнение 5" в конце
        reps_end_match = re.search(
            r'[-–—]\s*(\d+)$', line)  # Тире и число в конце
        reps_simple_match = re.search(
            r'\s+(\d+)$', line)   # Просто число в конце

        if sets_reps_match:
            sets = int(sets_reps_match.group(1))
            reps_per_set = int(sets_reps_match.group(2))
            reps = sets * reps_per_set
            clean_line = re.sub(r'\d+\s*[xх]\s*\d+', '', clean_line).strip()

        elif reps_end_match:
            reps = int(reps_end_match.group(1))
            clean_line = re.sub(r'[-–—]\s*\d+$', '', clean_line).strip()

        elif reps_simple_match:
            # Опасно, может быть год или вес, но пробуем
            reps = int(reps_simple_match.group(1))
            clean_line = re.sub(r'\s+\d+$', '', clean_line).strip()

        # Если это не пустая строка и (мы нашли репсы ИЛИ это было в явной секции упражнений)
        # Если секции не было, мы берем строку только если нашли в ней цифры (чтобы не брать мусор)
        is_valid_exercise = False
        if ex_section_match:
            is_valid_exercise = True  # В секции верим всему
        elif reps > 0:
            is_valid_exercise = True  # Вне секции верим только если есть цифры

        if is_valid_exercise and len(clean_line) > 2:
            # Извлекаем оборудование (если есть в скобках)
            equipment = None
            equip_match = re.search(r'\((.*?)\)', clean_line)
            if equip_match:
                equipment = equip_match.group(1)
                clean_line = clean_line.replace(f'({equipment})', '').strip()

            exercises.append({
                'name': clean_line,
                'equipment': equipment,
                'reps': reps
            })

    return exercises


# Публичные функции для обратной совместимости

def extract_scheme(content):
    """Публичная обёртка для извлечения схемы тренировки."""
    return _parse_scheme(content)


def extract_exercises(content):
    """Публичная обёртка для извлечения упражнений."""
    return _parse_exercises(content)


def extract_workout_metadata(post):
    """Извлекает метаданные из frontmatter поста."""
    return {
        'date': str(post.metadata.get('date', '')),
        'type': post.metadata.get('type', 'Unknown'),
        'weight': post.metadata.get('weight', 0),
        'duration': post.metadata.get('duration', 0),
        'goal': post.metadata.get('goal', 'Не указана'),
    }


def get_workout_summary(workout_data):
    """
    Формирует краткое описание тренировки.
    Принимает словарь, возвращённый parse_workout_file().
    """
    if not workout_data:
        return "Нет данных о тренировке"

    summary_parts = []

    if workout_data.get('type'):
        summary_parts.append(f"Тип: {workout_data['type']}")

    if workout_data.get('duration'):
        summary_parts.append(f"Длительность: {workout_data['duration']} мин")

    if workout_data.get('goal') and workout_data['goal'] != 'Не указана':
        summary_parts.append(f"Цель: {workout_data['goal']}")

    exercises = workout_data.get('exercises', [])
    if exercises:
        summary_parts.append(f"Упражнений: {len(exercises)}")

    return " | ".join(summary_parts) if summary_parts else "Тренировка без описания"


def update_workout_analysis(file_path, analysis_data):
    """
    Обновляет анализ тренировки в файле.
    Пока заглушка - при необходимости реализовать запись обратно в файл.
    """
    # TODO: Реализовать запись анализа обратно в markdown файл
    pass
