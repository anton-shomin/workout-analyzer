"""Parser for exercise markdown files with frontmatter."""

import frontmatter
import os
from datetime import datetime, timezone
from typing import Any


def parse_exercise_file(filepath: str) -> dict:
    """
    Parse an exercise markdown file and extract data from frontmatter and body.
    
    Args:
        filepath: Path to the exercise markdown file.
        
    Returns:
        Dictionary containing:
        - name: str
        - category: str
        - equipment: str
        - components: list[str]
        - met_base: float | None
        - cal_per_rep: float | None
        - muscle_groups: list[str]
        - description: str (from body)
        - raw_post: frontmatter.Post
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Exercise file not found: {filepath}")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        post = frontmatter.load(f)
    
    # Extract frontmatter fields with defaults
    exercise_data = {
        'name': post.metadata.get('name', ''),
        'category': post.metadata.get('category', ''),
        'equipment': post.metadata.get('equipment', ''),
        'components': post.metadata.get('components', []),
        'met_base': post.metadata.get('met_base'),
        'cal_per_rep': post.metadata.get('cal_per_rep'),
        'muscle_groups': post.metadata.get('muscle_groups', []),
        'description': post.content.strip() if post.content else '',
        'raw_post': post,
    }
    
    return exercise_data


def update_exercise_file(filepath: str, data: dict, updated_by: str = 'workout-analyzer') -> None:
    """
    Update an exercise file's frontmatter with enriched data.
    
    Args:
        filepath: Path to the exercise markdown file.
        data: Dictionary containing fields to update:
            - met_base: float
            - cal_per_rep: float
            - muscle_groups: list[str]
        updated_by: Identifier for what updated the file.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Exercise file not found: {filepath}")
    
    # Load existing content
    with open(filepath, 'r', encoding='utf-8') as f:
        post = frontmatter.load(f)
    
    # ВАЖНО: сохраняем оригинальный контент (тело файла)
    original_content = post.content or ''
    
    # Update frontmatter fields
    if 'met_base' in data:
        post.metadata['met_base'] = data['met_base']
    
    if 'cal_per_rep' in data:
        post.metadata['cal_per_rep'] = data['cal_per_rep']
    
    if 'muscle_groups' in data:
        post.metadata['muscle_groups'] = data['muscle_groups']
    
    # Add/update metadata
    post.metadata['last_updated'] = datetime.now(timezone.utc).isoformat()
    post.metadata['updated_by'] = updated_by
    
    # Гарантируем сохранение оригинального контента
    post.content = original_content
    
    # Write back to file
    with open(filepath, 'w', encoding='utf-8') as f:
        content = frontmatter.dumps(post)
        f.write(content)


def needs_enrichment(exercise_data: dict) -> bool:
    """
    Check if an exercise needs enrichment based on missing fields.
    
    Args:
        exercise_data: Parsed exercise data dictionary.
        
    Returns:
        True if exercise needs enrichment (missing met_base, cal_per_rep, or muscle_groups).
    """
    has_met_base = exercise_data.get('met_base') is not None
    has_cal_per_rep = exercise_data.get('cal_per_rep') is not None
    has_muscle_groups = exercise_data.get('muscle_groups') and len(exercise_data.get('muscle_groups', [])) > 0
    
    return not (has_met_base and has_cal_per_rep and has_muscle_groups)


def get_enrichment_fields() -> list[str]:
    """
    Get the list of fields that need to be enriched.
    
    Returns:
        List of field names that should be populated during enrichment.
    """
    return ['met_base', 'cal_per_rep', 'muscle_groups']


def parse_exercise_frontmatter(post: frontmatter.Post) -> dict:
    """
    Extract exercise data from a frontmatter Post object.
    
    Args:
        post: Loaded frontmatter Post object.
        
    Returns:
        Dictionary with exercise metadata.
    """
    return {
        'name': post.metadata.get('name', ''),
        'category': post.metadata.get('category', ''),
        'equipment': post.metadata.get('equipment', ''),
        'components': post.metadata.get('components', []),
        'met_base': post.metadata.get('met_base'),
        'cal_per_rep': post.metadata.get('cal_per_rep'),
        'muscle_groups': post.metadata.get('muscle_groups', []),
    }
