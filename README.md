# Obsidian Workout Analyzer

AI-powered workout analysis tool for Obsidian markdown files. Analyzes workouts, enriches exercise data using Perplexity API, and generates insights with Gemini API.

## Overview

Obsidian Workout Analyzer is a command-line tool designed to help fitness enthusiasts and athletes who use Obsidian for note-taking. It automatically parses workout logs and exercise descriptions, enriches them with scientific data (MET values, calorie calculations, muscle group targeting), and generates comprehensive AI-powered insights about your training.

### Key Capabilities

- **Smart Parsing**: Automatically extracts workout data from Obsidian markdown files with frontmatter
- **AI Enrichment**: Fetches MET values, calorie data, and muscle group targeting for exercises via Perplexity API
- **Comprehensive Analysis**: Calculates calories, estimates workout duration, and tracks muscle balance
- **Progress Tracking**: Compares workouts over time for progress insights
- **AI Insights**: Generates personalized recommendations using Gemini API

## Requirements

- Python 3.11 or higher
- API keys for Gemini and Perplexity
- Obsidian vault with workout and exercise notes

### Python Dependencies

All dependencies are listed in [`requirements.txt`](requirements.txt):

```
google-generativeai>=0.8.0
pyyaml>=6.0
python-dotenv>=1.0.0
```

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd workout-analyzer
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create a `.env` file from the example:

```bash
cp .env.example .env
```

Edit `.env` and add your API keys:

```bash
GEMINI_API_KEY=your_gemini_api_key_here
PERPLEXITY_API_KEY=your_perplexity_api_key_here
```

#### Obtaining API Keys

- **Gemini API Key**: Get your API key from [Google AI Studio](https://aistudio.google.com/)
- **Perplexity API Key**: Get your API key from [Perplexity AI](https://www.perplexity.ai/)

### 4. Configure Paths

Edit [`config.yaml`](config.yaml) to set your Obsidian vault path and other settings:

```yaml
obsidian:
  vault_path: "/path/to/your/obsidian/vault" # Required: Path to your Obsidian vault
  exercises_folder: "Exercises" # Folder containing exercise notes
  workouts_folder: "Workouts" # Folder containing workout logs
  cache_folder: ".cache/exercises" # Folder for exercise data cache

user:
  default_weight: 85 # Your body weight in kg

ai:
  gemini_model: "gemini-2.0-flash-exp" # Gemini model for workout analysis
  perplexity_model: "sonar" # Perplexity model for exercise research

calculation:
  base_weight: 70 # Base weight for calorie calculations
  default_met: 8.0 # Default MET value if not found
```

## Obsidian Vault Structure

Your Obsidian vault should have this structure:

```
vault/
├── Exercises/                    # Exercise library
│   ├── Deadlift.md
│   ├── Squats.md
│   └── ...
├── Workouts/                     # Workout logs
│   ├── 2026-02-11.md
│   ├── 2026-02-08.md
│   └── ...
└── .cache/                       # Auto-created cache folder
    └── exercises/
        └── ...
```

### Exercise Template

Create exercise files using this template:

```markdown
---
name: Exercise Name
category: Category (e.g., Strength, Cardio)
equipment: Kettlebells/Dumbbells/Barbell
components: [] # For combo exercises
met_base: null # Auto-filled by AI
cal_per_rep: null # Auto-filled by AI
muscle_groups: [] # Auto-filled by AI
---

Description of the exercise...
```

### Workout Template

Create workout files using this template:

```markdown
---
date: YYYY-MM-DD
type: Workout Type (e.g., Strength, HIIT)
weight: 85 # Your weight in kg
---

## Scheme: Ladder 1-2-3-4-5-5-4-3-2-1

Description of the workout scheme...

## Exercises

- Exercise 1 (weight)
- Exercise 2 (weight)
- ...

## Notes

Your notes about the workout...
```

## Supported Workout Schemes

- **Ladder**: Repetition pattern like 1-2-3-4-5-5-4-3-2-1
- **EMOM**: Every Minute on the Minute
- **Tabata**: High-intensity intervals (work/rest)
- **AMRAP**: As Many Rounds As Possible
- **RFT**: Rounds For Time
- **Custom**: Any other scheme

## Usage

### Check Setup Status

Verify your installation and configuration:

```bash
python main.py --status
```

### Update All Exercises

Enrich all exercises with missing MET values and muscle groups:

```bash
python main.py --update-exercises
```

### Update Single Exercise

```bash
python main.py --update-exercise "Kettlebell Thruster"
```

### Analyze Specific Workout

```bash
python main.py --analyze-workout 2026-02-11
```

### Analyze Latest Workout

```bash
python main.py --analyze-latest
```

### Re-analyze All Workouts

```bash
python main.py --reanalyze-all
```

### Test with Sample Data

The tool includes test data in [`test_data/`](test_data/). Configure [`config.yaml`](config.yaml) to point to test directories for validation.

## Output Format

After analysis, your workout files will have an AI Analysis section appended:

```markdown
## AI Analysis

**General Information:**

- Total repetitions: 90
- Calories: ~320 kcal
- Time: ~35 minutes
- Average intensity: 8.0 MET

**Muscle Group Balance:**

- Legs: 35%
- Shoulders: 25%
- Core: 20%
- Back: 15%
- Chest: 5%

**Gemini Recommendations:**
... AI-generated insights ...

---

_Analysis from 2026-02-11T18:30:00Z_
```

## Troubleshooting

### "Config file not found"

Make sure [`config.yaml`](config.yaml) exists in the project root.

### "API key not set"

Check that `.env` file exists and contains valid API keys.

### "Exercises folder not found"

Verify `vault_path` in [`config.yaml`](config.yaml) points to your Obsidian vault.

### No exercises extracted

Check your workout markdown format:

- Use `-` or `*` for bullet points
- Include weight in parentheses like `(1x24kg)`
- Don't put exercises after `## AI Analysis` section

### Rate limit errors

The APIs have rate limits. Wait a few minutes and retry.

### Empty analysis

Ensure exercises have MET values populated. Run `--update-exercises` first.

## Architecture

```
workout-analyzer/
├── main.py                      # CLI entry point
├── config.yaml                  # Configuration
├── parsers/
│   ├── exercise_parser.py       # Parse exercise markdown
│   └── workout_parser.py        # Parse workout markdown
├── ai/
│   ├── perplexity_client.py     # Perplexity API for exercise data
│   └── gemini_client.py         # Gemini API for analysis
├── cache/
│   └── exercise_cache.py        # Local cache for exercise data
├── calculators/
│   └── calorie_calculator.py    # Calorie and metric calculations
├── writers/
│   └── markdown_writer.py       # Write analysis to markdown
├── utils/
│   └── helpers.py               # Utility functions
└── test_data/                   # Test fixtures
```

### Core Components

- **[`parsers/`](parsers/)**: Parsers extract structured data from Obsidian markdown files
- **[`ai/`](ai/)**: AI clients for Perplexity (exercise enrichment) and Gemini (analysis)
- **[`cache/`](cache/)**: Local caching to minimize API calls and improve performance
- **[`calculators/`](calculators/)**: Calorie and MET calculations
- **[`writers/`](writers/)**: Markdown output generation

## Development

### Running Tests

```bash
# Test with sample data
python main.py --analyze-latest
```

### Adding New Features

1. Follow existing patterns in [`parsers/`](parsers/) and [`calculators/`](calculators/)
2. Add type hints and docstrings
3. Handle errors gracefully
4. Log actions for debugging

### Template Files

Reference [`Templates/`](Templates/) directory for exercise and workout templates.

## License

MIT

---

# Obsidian Workout Analyzer

AI-поддерживаемый инструмент для анализа тренировок в формате Obsidian markdown. Анализирует тренировки, обогащает данные упражнений с помощью Perplexity API и генерирует аналитику с помощью Gemini API.

## Обзор

Obsidian Workout Analyzer — это инструмент командной строки, предназначенный для любителей фитнеса и спортсменов, использующих Obsidian для ведения заметок. Он автоматически анализирует журналы тренировок и описания упражнений, обогащает их научными данными (значения MET, расчёт калорий, целевые группы мышц) и генерирует комплексную аналитику на основе ИИ.

### Ключевые возможности

- **Умный парсинг**: Автоматически извлекает данные тренировок из markdown файлов Obsidian с frontmatter
- **AI обогащение**: Получает значения MET, данные о калориях и целевые группы мышц через Perplexity API
- **Комплексный анализ**: Вычисляет калории, оценивает продолжительность тренировки, отслеживает баланс мышц
- **Отслеживание прогресса**: Сравнивает тренировки во времени для анализа прогресса
- **AI рекомендации**: Генерирует персонализированные советы с помощью Gemini API

## Требования

- Python 3.11 или выше
- API ключи для Gemini и Perplexity
- Obsidian vault с заметками о тренировках и упражнениях

### Зависимости Python

Все зависимости перечислены в [`requirements.txt`](requirements.txt):

```
google-generativeai>=0.8.0
pyyaml>=6.0
python-dotenv>=1.0.0
```

## Установка

### 1. Клонирование репозитория

```bash
git clone <repository-url>
cd workout-analyzer
```

### 2. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 3. Настройка переменных окружения

Создайте файл `.env` из примера:

```bash
cp .env.example .env
```

Отредактируйте `.env` и добавьте ваши API ключи:

```bash
GEMINI_API_KEY=ваш_gemini_api_ключ_здесь
PERPLEXITY_API_KEY=ваш_perplexity_api_ключ_здесь
```

#### Получение API ключей

- **Gemini API ключ**: Получите ваш ключ в [Google AI Studio](https://aistudio.google.com/)
- **Perplexity API ключ**: Получите ваш ключ в [Perplexity AI](https://www.perplexity.ai/)

### 4. Настройка путей

Отредактируйте [`config.yaml`](config.yaml) для установки пути к вашему Obsidian vault и других настроек:

```yaml
obsidian:
  vault_path: "/путь/к/вашему/obsidian/vault" # Обязательно: Путь к вашему Obsidian vault
  exercises_folder: "Exercises" # Папка с заметками упражнений
  workouts_folder: "Workouts" # Папка с журналами тренировок
  cache_folder: ".cache/exercises" # Папка для кэша данных упражнений

user:
  default_weight: 85 # Ваш вес в кг

ai:
  gemini_model: "gemini-2.0-flash-exp" # Модель Gemini для анализа тренировок
  perplexity_model: "sonar" # Модель Perplexity для исследования упражнений

calculation:
  base_weight: 70 # Базовый вес для расчёта калорий
  default_met: 8.0 # Значение MET по умолчанию, если не найдено
```

## Структура Obsidian Vault

Ваш Obsidian vault должен иметь следующую структуру:

```
vault/
├── Exercises/                    # Библиотека упражнений
│   ├── Становая тяга.md
│   ├── Приседания.md
│   └── ...
├── Workouts/                     # Журналы тренировок
│   ├── 2026-02-11.md
│   ├── 2026-02-08.md
│   └── ...
└── .cache/                       # Автоматически создаваемая папка кэша
    └── exercises/
        └── ...
```

### Шаблон упражнения

Создавайте файлы упражнений по этому шаблону:

```markdown
---
name: Название упражнения
category: Категория (например, Сила, Кардио)
equipment: Гантели/Штанга/Гири
components: [] # Для комплексных упражнений
met_base: null # Автоматически заполняется AI
cal_per_rep: null # Автоматически заполняется AI
muscle_groups: [] # Автоматически заполняется AI
---

Описание упражнения...
```

### Шаблон тренировки

Создавайте файлы тренировок по этому шаблону:

```markdown
---
date: ГГГГ-ММ-ДД
type: Тип тренировки (например, Сила, HIIT)
weight: 85 # Ваш вес в кг
---

## Схема: Лесенка 1-2-3-4-5-5-4-3-2-1

Описание схемы тренировки...

## Упражнения

- Упражнение 1 (вес)
- Упражнение 2 (вес)
- ...

## Заметки

Ваши заметки о тренировке...
```

## Поддерживаемые схемы тренировок

- **Лесенка**: Паттерн повторений типа 1-2-3-4-5-5-4-3-2-1
- **EMOM**: Каждую минуту в минуту
- **Табата**: Высокоинтенсивные интервалы (работа/отдых)
- **AMRAP**: Максимум раундов за время
- **RFT**: Раунды за время
- **Custom**: Любая другая схема

## Использование

### Проверка статуса установки

Проверьте вашу установку и конфигурацию:

```bash
python main.py --status
```

### Обновление всех упражнений

Обогатите все упражнения недостающими значениями MET и группами мышц:

```bash
python main.py --update-exercises
```

### Обновление одного упражнения

```bash
python main.py --update-exercise "Трастер с гирей"
```

### Анализ конкретной тренировки

```bash
python main.py --analyze-workout 2026-02-11
```

### Анализ последней тренировки

```bash
python main.py --analyze-latest
```

### Повторный анализ всех тренировок

```bash
python main.py --reanalyze-all
```

### Тестирование с тестовыми данными

Инструмент включает тестовые данные в [`test_data/`](test_data/). Настройте [`config.yaml`](config.yaml) для указания путей к тестовым директориям для проверки.

## Формат вывода

После анализа ваши файлы тренировок будут содержать раздел AI Analysis:

```markdown
## AI Analysis

**Общая информация:**

- Всего повторений: 90
- Калории: ~320 ккал
- Время: ~35 минут
- Средняя интенсивность: 8.0 MET

**Баланс мышечных групп:**

- Ноги: 35%
- Плечи: 25%
- Кор: 20%
- Спина: 15%
- Грудь: 5%

**Рекомендации от Gemini:**
... AI-сгенерированные инсайты ...

---

_Анализ от 2026-02-11T18:30:00Z_
```

## Устранение неполадок

### "Config file not found"

Убедитесь, что [`config.yaml`](config.yaml) существует в корне проекта.

### "API key not set"

Проверьте, что файл `.env` существует и содержит валидные API ключи.

### "Exercises folder not found"

Проверьте, что `vault_path` в [`config.yaml`](config.yaml) указывает на ваш Obsidian vault.

### Упражнения не извлекаются

Проверьте формат ваших markdown файлов тренировок:

- Используйте `-` или `*` для маркированных списков
- Включайте вес в скобках как `(1x24kg)`
- Не помещайте упражнения после раздела `## AI Analysis`

### Ошибки rate limit

API имеют ограничения по частоте запросов. Подождите несколько минут и повторите попытку.

### Пустой анализ

Убедитесь, что у упражнений заполнены значения MET. Сначала запустите `--update-exercises`.

## Архитектура

```
workout-analyzer/
├── main.py                      # Точка входа CLI
├── config.yaml                  # Конфигурация
├── parsers/
│   ├── exercise_parser.py       # Парсер markdown упражнений
│   └── workout_parser.py        # Парсер markdown тренировок
├── ai/
│   ├── perplexity_client.py     # Perplexity API для данных упражнений
│   └── gemini_client.py         # Gemini API для анализа
├── cache/
│   └── exercise_cache.py        # Локальный кэш для данных упражнений
├── calculators/
│   └── calorie_calculator.py    # Калькулятор калорий и метрик
├── writers/
│   └── markdown_writer.py       # Запись анализа в markdown
├── utils/
│   └── helpers.py               # Вспомогательные функции
└── test_data/                   # Тестовые данные
```

### Основные компоненты

- **[`parsers/`](parsers/)**: Парсеры извлекают структурированные данные из markdown файлов Obsidian
- **[`ai/`](ai/)**: AI клиенты для Perplexity (обогащение упражнений) и Gemini (анализ)
- **[`cache/`](cache/)**: Локальное кэширование для минимизации API вызовов и улучшения производительности
- **[`calculators/`](calculators/)**: Расчёты калорий и MET
- **[`writers/`](writers/)**: Генерация markdown вывода

## Разработка

### Запуск тестов

```bash
# Тестирование с тестовыми данными
python main.py --analyze-latest
```

### Добавление новых функций

1. Следуйте существующим паттернам в [`parsers/`](parsers/) и [`calculators/`](calculators/)
2. Добавляйте type hints и docstrings
3. Обрабатывайте ошибки корректно
4. Логируйте действия для отладки

### Файлы шаблонов

Обратитесь к директории [`Templates/`](Templates/) за шаблонами упражнений и тренировок.

## Лицензия

MIT
