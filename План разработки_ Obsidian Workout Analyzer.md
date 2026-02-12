<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# План разработки: Obsidian Workout Analyzer

## Общая архитектура

**Стек:**

- Python 3.11+
- Obsidian (markdown файлы)
- Perplexity API (поиск данных об упражнениях)
- Gemini Flash 2.0 API (анализ тренировок)
- python-frontmatter (парсинг markdown)
- python-dotenv (управление API ключами)

**Структура проекта:**

```
workout-analyzer/
├── .env                          # API ключи
├── .gitignore
├── requirements.txt
├── config.yaml                   # Пути к Obsidian vault
├── main.py                       # Точка входа
├── parsers/
│   ├── __init__.py
│   ├── workout_parser.py         # Парсинг тренировок
│   └── exercise_parser.py        # Парсинг упражнений
├── ai/
│   ├── __init__.py
│   ├── perplexity_client.py      # Работа с Perplexity API
│   └── gemini_client.py          # Работа с Gemini API
├── cache/
│   ├── __init__.py
│   └── exercise_cache.py         # Кеширование данных упражнений
├── calculators/
│   ├── __init__.py
│   └── calorie_calculator.py     # Расчет калорий
├── writers/
│   ├── __init__.py
│   └── markdown_writer.py        # Запись результатов
└── utils/
    ├── __init__.py
    └── helpers.py                # Вспомогательные функции
```

---

## Фаза 1: Базовая инфраструктура

### Задача 1.1: Настройка проекта

**Описание:** Создать структуру проекта, настроить зависимости и конфигурацию

**Файлы для создания:**

- `requirements.txt`
- `.env.example`
- `.gitignore`
- `config.yaml`
- `README.md`

**requirements.txt содержит:**

```
python-frontmatter==1.1.0
pyyaml==6.0.1
python-dotenv==1.0.0
requests==2.31.0
google-generativeai==0.3.0
```

**config.yaml структура:**

```yaml
obsidian:
  vault_path: "/path/to/vault"
  exercises_folder: "Exercises"
  workouts_folder: "Workouts"
  cache_folder: ".cache/exercises"

user:
  default_weight: 85

ai:
  gemini_model: "gemini-2.0-flash-exp"
  perplexity_model: "sonar"

calculation:
  base_weight: 70
  default_met: 8.0
```

**.env.example:**

```
GEMINI_API_KEY=your_key_here
PERPLEXITY_API_KEY=your_key_here
```

**Критерии приемки:**

- Проект инициализирован
- Зависимости установлены через `pip install -r requirements.txt`
- Конфигурация загружается корректно
- .gitignore исключает .env и .cache/

---

### Задача 1.2: Утилиты и хелперы

**Описание:** Создать вспомогательные функции для работы с файлами и конфигурацией

**Файл:** `utils/helpers.py`

**Функции:**

```python
def load_config(config_path='config.yaml') -> dict
def ensure_dir_exists(path: str) -> None
def sanitize_filename(name: str) -> str
def extract_json_from_text(text: str) -> dict
```

**Критерии приемки:**

- Конфигурация загружается из YAML
- Создаются необходимые директории автоматически
- Названия файлов корректно обрабатываются (убираются спецсимволы)
- JSON извлекается из текстовых ответов AI

---

## Фаза 2: Парсинг данных

### Задача 2.1: Парсер упражнений

**Описание:** Реализовать парсинг markdown файлов упражнений с frontmatter

**Файл:** `parsers/exercise_parser.py`

**Функции:**

```python
def parse_exercise_file(filepath: str) -> dict
    """
    Парсит файл упражнения, возвращает словарь с:
    - name: str
    - category: str
    - equipment: str
    - components: list[str]
    - met_base: float | None
    - cal_per_rep: float | None
    - muscle_groups: list[str]
    - description: str (из body)
    """

def update_exercise_file(filepath: str, data: dict) -> None
    """
    Обновляет frontmatter упражнения:
    - met_base
    - cal_per_rep
    - muscle_groups
    - last_updated
    - updated_by
    """

def needs_enrichment(exercise_data: dict) -> bool
    """
    Проверяет, нужно ли обогащать упражнение
    (пустые поля: met_base, cal_per_rep, muscle_groups)
    """
```

**Критерии приемки:**

- Корректно читает frontmatter из markdown
- Извлекает body контента (описание)
- Обновляет только указанные поля, не трогая остальные
- Сохраняет форматирование markdown

---

### Задача 2.2: Парсер тренировок

**Описание:** Реализовать парсинг markdown файлов тренировок

**Файл:** `parsers/workout_parser.py`

**Функции:**

```python
def parse_workout_file(filepath: str) -> dict
    """
    Парсит файл тренировки, возвращает:
    - date: str (YYYY-MM-DD)
    - type: str
    - weight: int (вес пользователя)
    - scheme: dict (схема тренировки)
    - exercises: list[dict] (упражнения)
    - content: str (полный контент)
    - raw_post: frontmatter.Post
    """

def extract_scheme(content: str) -> dict
    """
    Извлекает схему тренировки:
    - type: str (Лесенка, EMOM, Табата, и т.д.)
    - pattern: str (1-2-3-4-5-5-4-3-2-1)
    - reps_per_set: list[int]
    - total_reps: int
    - time_per_rep: int (секунды)
    - rest_between: int (секунды)
    """

def extract_exercises(content: str) -> list[dict]
    """
    Извлекает список упражнений:
    [
      {
        "name": "Становая тяга 2х гирь",
        "equipment": "2x24кг"
      }
    ]
    """

def update_workout_analysis(filepath: str, analysis: str) -> None
    """
    Обновляет секцию ## AI Analysis в файле тренировки
    """
```

**Критерии приемки:**

- Корректно парсит frontmatter тренировки
- Извлекает схему тренировки (лесенка, EMOM и т.д.)
- Извлекает список упражнений с оборудованием
- Обновляет секцию AI Analysis, не затирая остальной контент

---

## Фаза 3: AI интеграции

### Задача 3.1: Perplexity клиент

**Описание:** Реализовать работу с Perplexity API для поиска данных об упражнениях

**Файл:** `ai/perplexity_client.py`

**Функции:**

```python
def search_exercise_data(name: str, equipment: str,
                        components: list[str] = None,
                        description: str = None) -> dict
    """
    Запрашивает у Perplexity данные об упражнении.

    Промпт:
    - Название упражнения
    - Оборудование
    - Компоненты (если комбо)
    - Описание (если есть)

    Возвращает:
    {
      "met_base": float,
      "cal_per_rep": float,
      "muscle_groups": list[str],
      "reasoning": str
    }
    """

def _build_exercise_prompt(name, equipment, components, description) -> str
    """
    Формирует промпт для Perplexity
    """

def _parse_perplexity_response(response: str) -> dict
    """
    Парсит ответ Perplexity, извлекает JSON или структурированные данные
    """
```

**Промпт для Perplexity:**

```
Analyze kettlebell exercise: "{name}"
Equipment: {equipment}
Components: {components if combo}
Description: {description if exists}

Provide scientific data:
1. MET value (Metabolic Equivalent of Task) - numerical value
2. Estimated calories per repetition for 70kg person
3. Primary muscle groups worked (from: shoulders, chest, back, core, legs, arms, fullBody)

Return in JSON format:
{
  "met_base": <number>,
  "cal_per_rep": <number>,
  "muscle_groups": [<list>],
  "reasoning": "<brief explanation>"
}
```

**Критерии приемки:**

- API запрос отправляется корректно
- Ответ парсится в структурированные данные
- Обрабатываются ошибки API (rate limit, timeout)
- Fallback на дефолтные значения при ошибке

---

### Задача 3.2: Gemini клиент

**Описание:** Реализовать работу с Gemini API для анализа тренировок

**Файл:** `ai/gemini_client.py`

**Функции:**

```python
def analyze_workout(workout_data: dict, calories: int,
                   muscle_balance: dict) -> str
    """
    Анализирует тренировку через Gemini.

    Возвращает markdown текст с анализом:
    - Общая информация
    - Баланс мышечных групп
    - Объем и интенсивность
    - Рекомендации по восстановлению
    - Прогресс (если есть история)
    """

def _build_workout_prompt(workout_data, calories, muscle_balance) -> str
    """
    Формирует промпт для Gemini
    """

def _format_gemini_response(response: str) -> str
    """
    Форматирует ответ Gemini в markdown
    """
```

**Промпт для Gemini:**

```
Ты эксперт по силовым тренировкам с гирями. Проанализируй тренировку:

**Дата:** {date}
**Тип:** {type}
**Схема:** {scheme_description}

**Упражнения:**
{list of exercises with equipment and reps}

**Метрики:**
- Всего повторений: {total_reps}
- Расчетные калории: {calories} ккал
- Примерное время: {estimated_time} минут

**Баланс мышечных групп:**
{muscle_group_percentages}

Дай структурированный анализ по пунктам:
1. **Баланс мышечных групп** - какие группы работали, есть ли дисбаланс
2. **Объем и интенсивность** - достаточный ли объем, не перетренировка ли
3. **Рекомендации** - что добавить/убрать в следующий раз
4. **Восстановление** - сколько дней отдыха нужно

Формат ответа: структурированный markdown.
```

**Критерии приемки:**

- API запрос отправляется корректно
- Ответ форматируется в читаемый markdown
- Обрабатываются ошибки API
- Результат структурирован по разделам

---

## Фаза 4: Кеширование и расчеты

### Задача 4.1: Кеш упражнений

**Описание:** Реализовать систему кеширования данных об упражнениях

**Файл:** `cache/exercise_cache.py`

**Функции:**

```python
def get_exercise_data(name: str, equipment: str,
                     vault_path: str, cache_dir: str) -> dict
    """
    Получает данные об упражнении:
    1. Проверяет локальную папку Exercises/
    2. Проверяет кеш .cache/exercises/
    3. Запрашивает Perplexity API
    4. Сохраняет в кеш

    Возвращает:
    {
      "name": str,
      "equipment": str,
      "met_base": float,
      "cal_per_rep": float,
      "muscle_groups": list[str],
      "source": str  # "local", "cache", "perplexity"
    }
    """

def load_from_cache(cache_file: str) -> dict | None
def save_to_cache(cache_file: str, data: dict) -> None
def get_cache_path(name: str, cache_dir: str) -> str
```

**Формат кеш-файла** (JSON):

```json
{
  "name": "Становая тяга 2х гирь",
  "equipment": "2x24кг",
  "met_base": 8.0,
  "cal_per_rep": 1.2,
  "muscle_groups": ["legs", "back", "core"],
  "source": "perplexity",
  "fetched_at": "2026-02-11T16:30:00Z"
}
```

**Критерии приемки:**

- Приоритет: локальные файлы > кеш > API
- Кеш сохраняется в JSON формате
- Имена файлов санитизируются
- Обрабатываются ошибки чтения/записи

### Задача 4.2: Калькулятор калорий

**Описание:** Реализовать расчет калорий и метрик тренировки

**Файл:** `calculators/calorie_calculator.py`

**Функции:**

```python
def calculate_workout_calories(workout_data: dict,
                              exercises_data: list[dict],
                              user_weight: int) -> dict
    """
    Рассчитывает калории и метрики тренировки.

    Возвращает:
    {
      "total_calories": int,
      "total_reps": int,
      "estimated_time_minutes": int,
      "average_met": float,
      "exercises_breakdown": [
        {
          "name": str,
          "reps": int,
          "calories": int,
          "met": float
        }
      ],
      "muscle_groups_balance": {
        "shoulders": int,  # % вовлеченности
        "legs": int,
        "core": int,
        ...
      }
    }
    """

def calculate_exercise_calories(cal_per_rep: float, reps: int,
                               user_weight: int, base_weight: int = 70) -> int
    """
    Калории для упражнения с учетом веса пользователя
    """

def calculate_muscle_balance(exercises_data: list[dict],
                            scheme: dict) -> dict
    """
    Рассчитывает процентное соотношение мышечных групп
    """

def estimate_workout_time(scheme: dict) -> int
    """
    Оценивает время тренировки в минутах на основе схемы
    """
```

**Формула калорий:**

```python
weight_factor = user_weight / base_weight  # 85 / 70 = 1.21
calories = cal_per_rep * reps * weight_factor
```

**Критерии приемки:**

- Корректный расчет калорий с учетом веса пользователя
- Баланс мышечных групп рассчитывается правильно
- Время тренировки оценивается на основе схемы

---

## Фаза 5: Запись результатов

### Задача 5.1: Markdown Writer

**Описание:** Реализовать запись результатов анализа обратно в файлы

**Файл:** `writers/markdown_writer.py`

**Функции:**

```python
def write_analysis_to_workout(workout_file: str,
                             analysis: dict) -> None
    """
    Записывает AI анализ в секцию ## AI Analysis

    Формат:
    ## AI Analysis

    **Общая информация:**
    - Всего повторений: {total_reps}
    - Калории: ~{calories} ккал
    - Время: ~{time} минут
    - Средняя интенсивность: {avg_met} MET

    **Баланс мышечных групп:**
    - Ноги: {legs}%
    - Плечи: {shoulders}%
    - Кор: {core}%
    - Спина: {back}%

    **Рекомендации от Gemini:**
    {gemini_analysis}

    ---
    *Анализ от {timestamp}*
    """

def format_analysis_section(analysis: dict,
                           gemini_response: str) -> str
    """
    Форматирует секцию анализа в markdown
    """
```

**Критерии приемки:**

- Секция AI Analysis обновляется или создается
- Сохраняется остальной контент файла
- Добавляется timestamp анализа
- Markdown форматирование корректное

---

## Фаза 6: Основной оркестратор

### Задача 6.1: Main CLI

**Описание:** Реализовать точку входа с CLI интерфейсом

**Файл:** `main.py`

**Команды:**

```bash
# Обновить все упражнения с пустыми полями
python main.py --update-exercises

# Обновить конкретное упражнение
python main.py --update-exercise "Трастер с взятием на грудь"

# Проанализировать тренировку по дате
python main.py --analyze-workout 2026-02-11

# Проанализировать последнюю тренировку
python main.py --analyze-latest

# Пересчитать все тренировки
python main.py --reanalyze-all
```

**Функции:**

```python
def update_all_exercises(config: dict) -> None
    """
    Проходит по папке Exercises/, обновляет упражнения с пустыми полями
    """

def update_single_exercise(name: str, config: dict) -> None
    """
    Обновляет конкретное упражнение
    """

def analyze_workout(date: str, config: dict) -> None
    """
    Полный workflow анализа тренировки:
    1. Парсит workout файл
    2. Для каждого упражнения получает данные (cache/local/API)
    3. Обновляет кастомные упражнения если нужно
    4. Рассчитывает калории и метрики
    5. Анализирует через Gemini
    6. Записывает результат в файл
    """

def analyze_latest_workout(config: dict) -> None
    """
    Находит последний файл в Workouts/ и анализирует
    """

def reanalyze_all_workouts(config: dict) -> None
    """
    Пересчитывает все тренировки
    """
```

**Критерии приемки:**

- CLI аргументы работают корректно
- Прогресс выводится в консоль
- Обрабатываются ошибки с понятными сообщениями
- Логирование действий

---

## Фаза 7: Тестирование и документация

### Задача 7.1: Тестовые данные

**Описание:** Создать тестовые файлы для проверки

**Создать:**

1. `test_data/Exercises/Трастер с взятием на грудь.md` (с пустыми полями)
2. `test_data/Workouts/2026-02-11.md` (с лесенкой)
3. `test_data/Workouts/2026-02-08.md` (для проверки прогресса)

**Критерии приемки:**

- Тестовые данные покрывают основные сценарии
- Форматирование соответствует шаблонам

---

### Задача 7.2: README документация

**Описание:** Написать полную документацию проекта

**Файл:** `README.md`

**Разделы:**

1. Описание проекта
2. Установка и настройка
3. Структура Obsidian vault
4. Шаблоны файлов
5. Использование (команды)
6. Конфигурация
7. API ключи
8. Troubleshooting

**Критерии приемки:**

- Документация покрывает все функции
- Примеры команд работают
- Описаны требования и зависимости

---

### Задача 7.3: Примеры использования

**Описание:** Создать step-by-step гайд

**Файл:** `EXAMPLES.md`

**Сценарии:**

1. Создание нового кастомного упражнения
2. Запись тренировки и анализ
3. Обновление всех упражнений
4. Настройка cron для автоматического запуска

**Критерии приемки:**

- Пошаговые инструкции с командами
- Скриншоты/примеры вывода
- Объяснение результатов

---

## Фаза 8: Автоматизация

### Задача 8.1: GitHub Actions workflow (опционально)

**Описание:** Настроить автоматический запуск через GitHub Actions

**Файл:** `.github/workflows/analyze-workouts.yml`

**Workflow:**

```yaml
name: Analyze Workouts
on:
  schedule:
    - cron: "0 21 * * *" # 23:00 EET
  workflow_dispatch:

jobs:
  analyze:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: "3.11"
      - run: pip install -r requirements.txt
      - run: python main.py --analyze-latest
        env:
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
          PERPLEXITY_API_KEY: ${{ secrets.PERPLEXITY_API_KEY }}
      - name: Commit changes
        run: |
          git config --global user.name 'Workout Analyzer Bot'
          git config --global user.email 'bot@workout.local'
          git add .
          git commit -m 'Auto-analyze workout' || echo "No changes"
          git push
```

**Критерии приемки:**

- Workflow запускается по расписанию
- Секреты настроены
- Изменения коммитятся автоматически

---

### Задача 8.2: Cron setup для локальной VM (опционально)

**Описание:** Инструкция по настройке cron на Oracle Cloud VM

**Файл:** `CRON_SETUP.md`

**Шаги:**

1. Клонирование репозитория на VM
2. Установка зависимостей
3. Настройка .env файла
4. Добавление в crontab
5. Настройка логирования

**Пример crontab:**

```bash
0 23 * * * cd /home/user/workout-analyzer && /usr/bin/python3 main.py --analyze-latest >> /var/log/workout-analyzer.log 2>&1
```

**Критерии приемки:**

- Документация полная и понятная
- Команды протестированы
- Логи настроены

---

## Итоговый чеклист

### Must-have (MVP):

- [ ] Задача 1.1: Настройка проекта
- [ ] Задача 1.2: Утилиты и хелперы
- [ ] Задача 2.1: Парсер упражнений
- [ ] Задача 2.2: Парсер тренировок
- [ ] Задача 3.1: Perplexity клиент
- [ ] Задача 3.2: Gemini клиент
- [ ] Задача 4.1: Кеш упражнений
- [ ] Задача 4.2: Калькулятор калорий
- [ ] Задача 5.1: Markdown Writer
- [ ] Задача 6.1: Main CLI
- [ ] Задача 7.2: README документация

### Nice-to-have:

- [ ] Задача 7.1: Тестовые данные
- [ ] Задача 7.3: Примеры использования
- [ ] Задача 8.1: GitHub Actions
- [ ] Задача 8.2: Cron setup инструкция

---

## Порядок разработки (рекомендуемый):

**День 1-2:**

- Задачи 1.1, 1.2 (инфраструктура)
- Задачи 2.1, 2.2 (парсинг)

**День 3-4:**

- Задачи 3.1, 3.2 (AI интеграции)
- Задача 4.1 (кеширование)

**День 5:**

- Задача 4.2 (калькулятор)
- Задача 5.1 (writer)

**День 6:**

- Задача 6.1 (main CLI)
- Тестирование на реальных данных

**День 7:**

- Задача 7.2 (документация)
- Полировка и багфиксы

---

## Примечания для AI-агентов:

1. **Используй type hints** во всех функциях
2. **Обрабатывай ошибки** с понятными сообщениями
3. **Логируй действия** (print statements для отладки)
4. **Сохраняй форматирование** markdown при обновлении файлов
5. **Тестируй на реальных данных** после каждой задачи
6. **Документируй функции** с docstrings
7. **Следуй PEP 8** для стиля кода

---

**Всё! Полный план готов. Можешь скармливать задачи своим агентам по порядку.**
