import re
import frontmatter


def parse_workout_file(file_path):
    """
    IMPROVED: Parses workout with SCHEME-AWARE repetition calculation
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        post = frontmatter.load(f)

    content = post.content
    date_str = str(post.metadata.get('date', ''))
    workout_type = post.metadata.get('type', 'Unknown')
    weight = post.metadata.get('weight', 0)

    # Parse duration
    duration = post.metadata.get('duration')
    if duration and isinstance(duration, str):
        if 'min' in duration or 'мин' in duration:
            try:
                duration = float(re.search(r'(\d+\.?\d*)', duration).group(1))
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

    # Parse scheme FIRST
    scheme = _parse_scheme(content)
    
    # Remove AI Analysis section BEFORE parsing exercises
    content_without_analysis = re.sub(
        r'## AI Analysis\n.*?(?=\n## |\Z)', 
        '', 
        content, 
        flags=re.DOTALL
    )

    # Parse exercises WITH SCHEME CONTEXT
    exercises = _parse_exercises(content_without_analysis, scheme)

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
    """
    IMPROVED: Extracts scheme and CALCULATES total reps
    """
    scheme = {}
    scheme_match = re.search(r'## Схема\n(.*?)\n##', content, re.DOTALL)
    
    if not scheme_match:
        return scheme
        
    scheme_text = scheme_match.group(1)
    
    for line in scheme_text.strip().split('\n'):
        if ':' not in line:
            continue
            
        key, value = line.split(':', 1)
        key = key.strip().replace('**', '').lower()
        value = value.strip()

        if 'тип' in key or 'type' in key:
            scheme['type'] = value
        elif 'кругов' in key or 'rounds' in key:
            try:
                scheme['rounds'] = int(re.search(r'\d+', value).group())
            except:
                scheme['rounds'] = 1
        elif 'снаряд' in key or 'equipment' in key:
            scheme['equipment'] = value
        elif 'паттерн' in key or 'pattern' in key:
            scheme['pattern'] = value
            # Calculate total reps from pattern
            scheme['reps_per_exercise'] = _calculate_reps_from_pattern(value)

    return scheme


def _calculate_reps_from_pattern(pattern: str) -> int:
    """
    Calculates total reps from patterns like:
    - "1-2-3-3-2-1" → 12
    - "10-9-8-7-6-5-4-3-2-1" → 55
    - "1-2-3-4-5" → 15
    """
    if not pattern:
        return 0
    
    # Extract all numbers from pattern
    numbers = re.findall(r'\d+', pattern)
    if not numbers:
        return 0
    
    # Sum them up
    total = sum(int(n) for n in numbers)
    return total


def _parse_exercises(content, scheme):
    """
    IMPROVED: Parses exercises and APPLIES SCHEME REPS if missing
    """
    exercises = []
    
    # Get reps from scheme
    reps_from_scheme = scheme.get('reps_per_exercise', 0)
    rounds = scheme.get('rounds', 1)
    total_reps_from_scheme = reps_from_scheme * rounds

    # Find exercise section
    ex_section_match = re.search(
        r'## Упражнения\n(.*?)(?:\n##|$)', 
        content, 
        re.DOTALL
    )

    if not ex_section_match:
        return exercises

    block = ex_section_match.group(1)
    lines = block.strip().split('\n')

    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue

        # Clean line
        clean_line = line.lstrip('-*1234567890. ')
        clean_line = clean_line.replace('[[', '').replace(']]', '')
        
        if '|' in clean_line:
            clean_line = clean_line.split('|')[0]

        # Try to extract reps from line
        reps = 0
        
        # Pattern 1: "5x5" or "5х5"
        sets_reps_match = re.search(r'(\d+)\s*[xх]\s*(\d+)', clean_line)
        
        # Pattern 2: "Exercise - 5"
        reps_dash_match = re.search(r'[-–—]\s*(\d+)\s*$', clean_line)
        
        # Pattern 3: Just number at end
        reps_simple_match = re.search(r'\s+(\d+)\s*$', clean_line)

        if sets_reps_match:
            sets = int(sets_reps_match.group(1))
            reps_per_set = int(sets_reps_match.group(2))
            reps = sets * reps_per_set
            clean_line = re.sub(r'\d+\s*[xх]\s*\d+', '', clean_line).strip()
        elif reps_dash_match:
            reps = int(reps_dash_match.group(1))
            clean_line = re.sub(r'[-–—]\s*\d+\s*$', '', clean_line).strip()
        elif reps_simple_match:
            reps = int(reps_simple_match.group(1))
            clean_line = re.sub(r'\s+\d+\s*$', '', clean_line).strip()
        else:
            # NO REPS IN LINE → USE SCHEME
            if total_reps_from_scheme > 0:
                reps = total_reps_from_scheme
                print(f"   ℹ️  {clean_line}: нет повторений в строке, использую схему → {reps}")

        # Extract equipment
        equipment = None
        equip_match = re.search(r'\((.*?)\)', clean_line)
        if equip_match:
            equipment = equip_match.group(1)
            clean_line = clean_line.replace(f'({equipment})', '').strip()

        if len(clean_line) > 2:
            exercises.append({
                'name': clean_line.strip(),
                'equipment': equipment,
                'reps': reps
            })

    return exercises


# Public wrappers
def extract_scheme(content):
    return _parse_scheme(content)


def extract_exercises(content):
    content_clean = re.sub(
        r'## AI Analysis\n.*?(?=\n## |\Z)', 
        '', 
        content, 
        flags=re.DOTALL
    )
    scheme = _parse_scheme(content)
    return _parse_exercises(content_clean, scheme)


def extract_workout_metadata(post):
    return {
        'date': str(post.metadata.get('date', '')),
        'type': post.metadata.get('type', 'Unknown'),
        'weight': post.metadata.get('weight', 0),
        'duration': post.metadata.get('duration', 0),
        'goal': post.metadata.get('goal', 'Не указана'),
    }


def get_workout_summary(workout_data):
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
    pass