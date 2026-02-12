"""
Writers package - запись результатов анализа в файлы Obsidian.
"""

from .markdown_writer import (
    write_analysis_to_workout,
    format_analysis_section,
    update_exercise_data,
    write_calorie_summary,
    create_empty_analysis_section,
    remove_analysis_section
)

__all__ = [
    'write_analysis_to_workout',
    'format_analysis_section',
    'update_exercise_data',
    'write_calorie_summary',
    'create_empty_analysis_section',
    'remove_analysis_section'
]
