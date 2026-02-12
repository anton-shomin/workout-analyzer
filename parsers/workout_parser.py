"""Parser for workout markdown files with frontmatter."""

import frontmatter
import os
import re
from typing import Any


# Workout scheme types
SCHEME_TYPES = ['Лесенка', 'EMOM', 'Табата', 'AMRAP', 'RFT', 'Custom']


def _parse_duration(raw) -> float | None:
    """Parse duration from frontmatter value to minutes.

    Handles: int/float, '45 минут', '12 минут 30 секунд',
    '1мин', '90сек', '1:30' (mm:ss).
    Returns float minutes or None.
    """
    if raw is None:
        return None
    if isinstance(raw, (int, float)):
        return float(raw)
    s = str(raw).strip().lower()
    if not s:
        return None

    # Try "mm:ss" format
    mm_ss = re.match(r'^(\d+):(\d+)$', s)
    if mm_ss:
        return int(mm_ss.group(1)) + int(
            mm_ss.group(2)
        ) / 60.0

    total_min = 0.0
    found = False

    # Hours
    h = re.search(r'(\d+)\s*(?:час|hour|ч|h)', s)
    if h:
        total_min += int(h.group(1)) * 60
        found = True

    # Minutes
    m = re.search(r'(\d+)\s*(?:минут|мин|min|m)', s)
    if m:
        total_min += int(m.group(1))
        found = True

    # Seconds
    sec = re.search(r'(\d+)\s*(?:секунд|сек|sec|s)', s)
    if sec:
        total_min += int(sec.group(1)) / 60.0
        found = True

    if found:
        return round(total_min, 2)

    # Try plain number
    try:
        return float(s)
    except ValueError:
        return None


def parse_workout_file(filepath: str) -> dict:
    """Parse a workout markdown file and extract data.

    Args:
        filepath: Path to the workout markdown file.

    Returns:
        Dictionary with date, type, weight, scheme,
        exercises, content, raw_post.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(
            f"Workout file not found: {filepath}"
        )

    with open(filepath, 'r', encoding='utf-8') as f:
        post = frontmatter.load(f)

    content = post.content

    # Extract scheme and exercises
    scheme = extract_scheme(content)
    exercises = extract_exercises(content)

    # Distribute reps to exercises
    sets = scheme.get('sets', 1)
    pattern_reps = scheme.get('total_reps', 0)

    # Check if exercises have per-round reps (e.g. x4, x3)
    has_per_exercise_reps = any(
        ex.get('reps_per_round', 0) > 0 for ex in exercises
    )

    if has_per_exercise_reps:
        # Each exercise has its own reps per round
        # Total reps = reps_per_round × number_of_rounds
        total_reps = 0
        for ex in exercises:
            rpr = ex.get('reps_per_round', 0)
            ex['reps'] = rpr * sets
            total_reps += ex['reps']
        scheme['total_reps'] = total_reps
    elif pattern_reps > 0:
        # Ladder/pattern: every exercise does ALL reps
        for ex in exercises:
            ex['reps'] = pattern_reps
    else:
        for ex in exercises:
            ex['reps'] = 0

    # Read duration from frontmatter (minutes)
    # For EMOM: 'time' = per-round duration → total = time × sets
    # For other types: 'duration' or 'time' = total duration
    scheme_type = scheme.get('type', '')
    sets = scheme.get('sets', 1)

    raw_dur = post.metadata.get('duration', None)
    raw_time = post.metadata.get('time', None)

    if raw_dur is not None:
        # 'duration' is normally total
        val = _parse_duration(raw_dur)
        if val and scheme_type == 'EMOM':
            # Heuristic: if duration is very short relative to sets, 
            # it implies per-round time (e.g. 1 min for 20 sets)
            # Threshold: if val < sets * 0.2 (allowing for very short intervals)
            # Actually, let's use 0.5 (30s per round minimum for "normal" EMOMs)
            # If someone does 10s EMOM, 10s = 0.16m. Sets=10. 0.16 < 5. True.
            # If someone does 10 min EMOM with 10 sets. 10 < 5. False.
            if sets > 1 and val < (sets * 0.5):
                duration = val * sets
            else:
                duration = val
        else:
            duration = val
    elif raw_time is not None:
        per_round = _parse_duration(raw_time)
        if per_round and scheme_type == 'EMOM':
            # EMOM: time is per round
            duration = per_round * sets
        else:
            duration = per_round
    else:
        duration = None

    # Extract frontmatter fields
    workout_data = {
        'date': post.metadata.get('date', ''),
        'type': post.metadata.get('type', ''),
        'weight': post.metadata.get('weight', 70),
        'duration': duration,
        'scheme': scheme,
        'exercises': exercises,
        'content': content,
        'raw_post': post,
    }

    return workout_data


def extract_scheme(content: str) -> dict:
    """
    Extract workout scheme from markdown content.
    
    Args:
        content: The markdown content of the workout.
        
    Returns:
        Dictionary containing:
        - type: str (Лесенка, EMOM, Табата, etc.)
        - pattern: str (e.g., "1-2-3-4-5-5-4-3-2-1")
        - reps_per_set: list[int]
        - total_reps: int
        - time_per_rep: int (seconds)
        - rest_between: int (seconds)
    """
    scheme = {
        'type': '',
        'pattern': '',
        'reps_per_set': [],
        'total_reps': 0,
        'time_per_rep': 3,
        'rest_between': 60,
    }
    
    # Detect scheme type
    for scheme_type in SCHEME_TYPES:
        if scheme_type.lower() in content.lower():
            scheme['type'] = scheme_type
            break
    
    # If no scheme type found, try to infer from content
    if not scheme['type']:
        if 'лесенка' in content.lower() or 'ladder' in content.lower():
            scheme['type'] = 'Лесенка'
        elif 'emom' in content.lower():
            scheme['type'] = 'EMOM'
        elif 'табата' in content.lower():
            scheme['type'] = 'Табата'
        elif 'amrap' in content.lower():
            scheme['type'] = 'AMRAP'
        elif 'rft' in content.lower() or 'rounds for time' in content.lower():
            scheme['type'] = 'RFT'
    
    # Extract pattern (e.g., "1-2-3-4-5-5-4-3-2-1")
    # Only search within the Схема section to avoid matching dates
    scheme_section = ''
    scheme_start = re.search(
        r'##\s*Схема', content, re.IGNORECASE
    )
    if scheme_start:
        # Get text from scheme header to next ## header
        rest = content[scheme_start.start():]
        next_section = re.search(r'\n##\s', rest[3:])
        if next_section:
            scheme_section = rest[:next_section.start() + 3]
        else:
            scheme_section = rest

    pattern_match = re.search(
        r'(\d+(?:[-,]+\d+){2,})', scheme_section
    ) if scheme_section else None
    if pattern_match:
        pattern_str = pattern_match.group(1)
        # Parse pattern into reps per set
        reps = re.findall(r'\d+', pattern_str.replace('-', ' ').replace(',', ' '))
        scheme['pattern'] = pattern_str.replace(' ', '-')
        scheme['reps_per_set'] = [int(r) for r in reps]
        scheme['total_reps'] = sum(scheme['reps_per_set'])

    # Parse number of sets/rounds/ladders
    # e.g., "8 лесенок", "5 кругов", "3 rounds"
    sets_pattern = (
        r'(\d+)\s*'
        r'(?:лесенок|лесенки|лесенка'
        r'|кругов|круга|круг'
        r'|раундов|раунда|раунд'
        r'|rounds?|sets?|ladders?)'
    )
    sets_match = re.search(
        sets_pattern, content, re.IGNORECASE
    )
    if sets_match:
        scheme['sets'] = int(sets_match.group(1))
        
        # Check if "sets" describes the ladder rungs rather than repetitions
        # Heuristic: if sets == pattern_len and pattern is monotonic, don't multiply
        should_multiply = True
        
        if scheme['type'] == 'Лесенка' and scheme['reps_per_set']:
            pattern_len = len(scheme['reps_per_set'])
            if scheme['sets'] == pattern_len:
                reps = scheme['reps_per_set']
                # Check strict monotonicity (strictly increasing or decreasing)
                # allowing equal values for plateaus usually, but for ladders
                # usually strictly monotonic. Let's use <= >= to be safe.
                is_increasing = all(reps[i] <= reps[i+1] for i in range(len(reps)-1))
                is_decreasing = all(reps[i] >= reps[i+1] for i in range(len(reps)-1))
                
                if is_increasing or is_decreasing:
                    should_multiply = False
        
        if should_multiply and scheme['total_reps'] > 0:
            scheme['total_reps'] *= scheme['sets']
    else:
        # Try reversed format: **Кругов:** 10
        rev_pattern = (
            r'(?:лесенок|лесенки|лесенка'
            r'|кругов|круга|круг'
            r'|раундов|раунда|раунд'
            r'|rounds?|sets?|ladders?)'
            r'[:\s*]+(\d+)'
        )
        rev_match = re.search(
            rev_pattern, content, re.IGNORECASE
        )
        if rev_match:
            scheme['sets'] = int(rev_match.group(1))
            
            # Check if "sets" describes the ladder rungs rather than repetitions
            should_multiply = True
            
            if scheme['type'] == 'Лесенка' and scheme['reps_per_set']:
                pattern_len = len(scheme['reps_per_set'])
                if scheme['sets'] == pattern_len:
                    reps = scheme['reps_per_set']
                    is_increasing = all(reps[i] <= reps[i+1] for i in range(len(reps)-1))
                    is_decreasing = all(reps[i] >= reps[i+1] for i in range(len(reps)-1))
                    
                    if is_increasing or is_decreasing:
                        should_multiply = False

            if should_multiply and scheme['total_reps'] > 0:
                scheme['total_reps'] *= scheme['sets']
        else:
            scheme['sets'] = 1

    # Extract timing info
    time_per_rep_match = re.search(r'(\d+)\s*сек.*на\s*повторение|time per rep[:\s]*(\d+)', content.lower())
    if time_per_rep_match:
        scheme['time_per_rep'] = int(time_per_rep_match.group(1) or time_per_rep_match.group(2))
    
    rest_match = re.search(r'(\d+)\s*сек.*отдых|rest[:\s]*(\d+)|отдых.*(\d+)\s*сек', content.lower())
    if rest_match:
        scheme['rest_between'] = int(rest_match.group(1) or rest_match.group(2) or rest_match.group(3))
    
    # Try to extract from EMOM format (e.g., "EMOM 20: 5 повторений")
    emom_match = re.search(r'emom[:\s]*(\d+)[:\s]*(\d+)\s*повторений', content.lower())
    if emom_match:
        scheme['type'] = 'EMOM'
        total_time = int(emom_match.group(1))
        reps = int(emom_match.group(2))
        scheme['reps_per_set'] = [reps] * (total_time // 60)
        scheme['total_reps'] = sum(scheme['reps_per_set'])
    
    # Try to extract from Табата format (e.g., "Табата 4x20/10")
    tabata_match = re.search(r'табата[:\s]*(\d+)\s*[x×]\s*(\d+)\s*[/]\s*(\d+)', content.lower())
    if tabata_match:
        scheme['type'] = 'Табата'
        rounds = int(tabata_match.group(1))
        work_time = int(tabata_match.group(2))
        rest_time = int(tabata_match.group(3))
        scheme['reps_per_set'] = [1] * rounds  # Each round is one set
        scheme['total_reps'] = rounds
        scheme['time_per_rep'] = work_time
        scheme['rest_between'] = rest_time

    # Extract Equipment/Snaryad
    # e.g. **Снаряд:** 1x24кг or Equipment: 2x16kg
    equipment_match = re.search(
        r'(?:снаряд|equipment|вес)[:\s]*([^\n]+)',
        content,
        re.IGNORECASE
    )
    if equipment_match:
        # cleanup markdown bold/italic if caught
        raw_eq = equipment_match.group(1).strip()
        # remove trailing ** if present
        raw_eq = raw_eq.replace('**', '').replace('__', '').strip()
        scheme['equipment'] = raw_eq

    return scheme


def extract_exercises(content: str) -> list[dict]:
    """
    Extract exercises from markdown content.
    
    Args:
        content: The markdown content of the workout.
        
    Returns:
        List of dictionaries, each containing:
        - name: str
        - equipment: str (optional)
    """
    exercises = []
    
    # Pattern to match exercise lines
    # Examples:
    # - Становая тяга 2х гирь (2x24кг)
    # - Махи гирей в сторону (1x16кг)
    # - Турник (подтягивания)
    
    exercise_pattern = re.compile(
        r'^\s*[-*•]\s*(.+?)\s*$',
        re.MULTILINE
    )
    
    # Alternative pattern for numbered lists
    numbered_pattern = re.compile(
        r'^\s*\d+[.)]\s*(.+?)\s*$',
        re.MULTILINE
    )
    
    # Find all exercise-like lines
    lines = content.split('\n')
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Stop at analysis section (must check before
        # generic header skip)
        if line.startswith('#'):
            lower = line.lower()
            if ('analysis' in lower
                    or 'анализ' in lower
                    or 'ai' in lower):
                break
            continue
        
        # Try to match exercise pattern
        match = (
            exercise_pattern.match(line)
            or numbered_pattern.match(line)
        )
        if match:
            exercise_text = match.group(1).strip()

            # Skip non-exercise lines
            skip_kw = [
                'разминка', 'заминка', 'растяжка',
                'кошка', 'воробей', 'отдых',
                'повторить', 'схема', 'время',
                'раунд', 'комплекс',
            ]
            lower_text = exercise_text.lower()
            if any(kw in lower_text for kw in skip_kw):
                continue

            # Skip metadata lines like **Тип:** ...
            # Note: exercise_pattern treats * as bullet,
            # so **Тип:** becomes *Тип:** after strip
            if ':**' in exercise_text:
                continue

            # Extract per-exercise reps
            reps_per_round = 0

            # Format 1: number-first ("4 тяги Горилла")
            num_first = re.match(
                r'^(\d+)\s+(.+)$', exercise_text
            )
            if num_first:
                reps_per_round = int(
                    num_first.group(1)
                )
                exercise_text = num_first.group(
                    2
                ).strip()

            # Format 2: suffix reps (e.g. x4, x3)
            if reps_per_round == 0:
                reps_match = re.search(
                    r'[xXхХ×](\d+)', exercise_text
                )
                if reps_match:
                    reps_per_round = int(
                        reps_match.group(1)
                    )
                    exercise_text = re.sub(
                        r'\s*[xXхХ×]\d+', '',
                        exercise_text
                    ).strip()

            # Extract equipment from parens
            equipment = ''
            eq_match = re.search(
                r'[\(\[]'
                r'([^\)\]]*(?:кг|kg)[^\)\]]*)'
                r'[\)\]]',
                exercise_text
            )
            if eq_match:
                equipment = eq_match.group(1).strip()
                exercise_name = re.sub(
                    r'\s*[\(\[]'
                    r'[^\)\]]*(?:кг|kg)[^\)\]]*'
                    r'[\)\]]',
                    '', exercise_text
                ).strip()
            else:
                exercise_name = exercise_text

            if exercise_name and len(exercise_name) > 2:
                ex_data = {
                    'name': exercise_name,
                    'equipment': equipment,
                }
                if reps_per_round > 0:
                    ex_data['reps_per_round'] = (
                        reps_per_round
                    )
                exercises.append(ex_data)
    
    return exercises


def needs_analysis(workout_data: dict) -> bool:
    """
    Check if a workout needs AI analysis.

    Returns True if the AI Analysis section is empty or contains
    only the placeholder comment.

    Args:
        workout_data: Parsed workout data dictionary.

    Returns:
        True if workout needs analysis.
    """
    content = workout_data.get('content', '')

    # Find AI Analysis section
    analysis_match = re.search(
        r'##\s*AI\s*Analysis\s*\n(.*?)(?=\n##\s|\n#\s|$)',
        content,
        re.IGNORECASE | re.DOTALL
    )

    if not analysis_match:
        # No AI Analysis section at all — needs analysis
        return True

    section_body = analysis_match.group(1).strip()

    # Remove HTML comments
    clean = re.sub(r'<!--.*?-->', '', section_body, flags=re.DOTALL)
    clean = clean.strip()

    # If nothing left after removing comments, needs analysis
    return len(clean) == 0


def update_workout_analysis(filepath: str, analysis: str) -> None:
    """
    Update the AI Analysis section in a workout file.
    
    Args:
        filepath: Path to the workout markdown file.
        analysis: The AI analysis markdown content to insert/update.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Workout file not found: {filepath}")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        post = frontmatter.load(f)
    
    # Check if AI Analysis section already exists
    content = post.content

    # Pattern to find ALL AI Analysis sections
    analysis_pattern = re.compile(
        r'##\s*AI\s*Analysis\s*\n'
        r'.*?(?=\n##\s|\n#\s|\Z)',
        re.IGNORECASE | re.DOTALL
    )

    new_section = (
        f"## AI Analysis\n\n{analysis}\n"
    )

    if analysis_pattern.search(content):
        # Remove ALL existing AI Analysis sections
        new_content = analysis_pattern.sub(
            '', content
        ).rstrip()
        # Append the single new section
        new_content += '\n\n' + new_section
    else:
        new_content = (
            content.rstrip() + '\n\n' + new_section
        )

    post.content = new_content

    with open(filepath, 'w', encoding='utf-8') as f:
        out = frontmatter.dumps(post)
        f.write(out)


def get_workout_summary(workout_data: dict) -> str:
    """
    Generate a summary string from parsed workout data.
    
    Args:
        workout_data: Parsed workout data dictionary.
        
    Returns:
        Human-readable summary string.
    """
    parts = []
    
    if workout_data.get('date'):
        parts.append(f"Дата: {workout_data['date']}")
    
    if workout_data.get('type'):
        parts.append(f"Тип: {workout_data['type']}")
    
    scheme = workout_data.get('scheme', {})
    if scheme.get('type'):
        parts.append(f"Схема: {scheme['type']}")
    
    exercises = workout_data.get('exercises', [])
    if exercises:
        parts.append(f"Упражнений: {len(exercises)}")
    
    if scheme.get('total_reps'):
        parts.append(f"Всего повторений: {scheme['total_reps']}")
    
    return ' | '.join(parts)


def extract_workout_metadata(content: str) -> dict:
    """
    Extract additional metadata from workout content.
    
    Args:
        content: The markdown content of the workout.
        
    Returns:
        Dictionary with additional metadata.
    """
    metadata = {}
    
    # Extract date from content if not in frontmatter
    date_match = re.search(r'(\d{4}[-]\d{2}[-]\d{2})', content)
    if date_match:
        metadata['date'] = date_match.group(1)
    
    # Extract user weight mentioned in content
    weight_match = re.search(r'вес[:\s]*(\d+)', content.lower())
    if weight_match:
        metadata['weight'] = int(weight_match.group(1))
    
    # Extract workout notes
    notes_match = re.search(r' notes?[:\s]*(.+?)(?=\n##|\n#\s|$)', content, re.IGNORECASE | re.DOTALL)
    if notes_match:
        metadata['notes'] = notes_match.group(1).strip()
    
    return metadata
