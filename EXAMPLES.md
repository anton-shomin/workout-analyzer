# Obsidian Workout Analyzer - Usage Examples

## Table of Contents

1. [Creating a New Custom Exercise](#1-creating-a-new-custom-exercise)
2. [Recording and Analyzing a Workout](#2-recording-and-analyzing-a-workout)
3. [Updating All Exercises](#3-updating-all-exercises)
4. [Setting Up Automatic Analysis with Cron](#4-setting-up-automatic-analysis-with-cron)

---

## 1. Creating a New Custom Exercise

### Step 1: Create Exercise File

Create a new markdown file in your Obsidian vault's `Exercises/` folder:

**File:** `Exercises/Трастер с гирей.md`

```markdown
---
name: Трастер с гирей
category: Комплексное
equipment: 1x24кг
components: []
met_base:
cal_per_rep:
muscle_groups: []
created_by: manual
created_at: 2026-02-01T10:00:00Z
---

Комплексное упражнение, сочетающее присед с толчком гири над головой.

Техника:

1. Исходное положение - гиря в опущенной руке
2. Присед с одновременным подъемом гири
3. Толчок гири над головой
4. Опускание в исходное положение

Работает: ноги, плечи, трицепс, кор
```

### Step 2: Enrich with AI Data

Run the analyzer to fetch MET values and muscle group data:

```bash
python main.py --update-exercise "Трастер с гирей"
```

**Expected Output:**

```
✅ Config loaded from config.yaml

🔄 Updating exercise: Трастер с гирей

📝 Enriching: Трастер с гирей
   - Searching Perplexity for exercise data...
   - Found MET value: 8.0
   - Found muscle groups: legs, shoulders, core, arms
✅ Updated: Трастер с гирей
```

### Step 3: Verify Enriched Data

The exercise file will be automatically updated:

```markdown
---
name: Трастер с гирей
category: Комплексное
equipment: 1x24кг
components: []
met_base: 8.0
cal_per_rep: 1.15
muscle_groups: ["legs", "shoulders", "core", "arms"]
created_by: manual
created_at: 2026-02-01T10:00:00Z
updated_by: workout-analyzer
last_updated: 2026-02-11T18:30:00Z
---

[exercise description unchanged]
```

---

## 2. Recording and Analyzing a Workout

### Step 1: Create Workout File

Create a new markdown file in your Obsidian vault's `Workouts/` folder:

**File:** `Workouts/2026-02-11.md`

```markdown
---
date: 2026-02-11
type: Тренировка с гирями
weight: 85
---

## Схема: Лесенка 1-2-3-4-5-5-4-3-2-1

Каждое упражнение выполняется по схеме лесенки с отдыхом 60 секунд.

## Упражнения

- Трастер с гирей (1x24кг)
- Становая тяга 2х гирь (2x24кг)
- Махи гирей в сторону (1x16кг)
- Приседания с гирей (1x24кг)
- Жим гири стоя (1x16кг)

## Notes

Хорошая тренировка на всё тело.
```

### Step 2: Run Analysis

```bash
python main.py --analyze-workout 2026-02-11
```

**Expected Output:**

```
✅ Config loaded from config.yaml

📊 Analyzing workout: 2026-02-11

   Found 5 exercises
   - Трастер с гирей: cache
   - Становая тяга 2х гирь: cache
   - Махи гирей в сторону: perplexity
   - Приседания с гирей: cache
   - Жим гири стоя: perplexity

✅ Analysis complete!
   Total reps: 55
   Calories: ~420 kcal
   Time: ~28 minutes
   Primary muscle: legs
```

### Step 3: View Results

The workout file will be updated with AI Analysis:

```markdown
---
date: 2026-02-11
type: Тренировка с гирями
weight: 85
---

## Схема: Лесенка 1-2-3-4-5-5-4-3-2-1

[scheme description...]

## Упражнения

[exercise list...]

## Notes

[notes...]

## AI Analysis

**Общая информация:**

- Всего повторений: 55
- Калории: ~420 ккал
- Время: ~28 минут
- Средняя интенсивность: 8.0 MET

**Баланс мышечных групп:**

- Ноги: 40%
- Плечи: 25%
- Кор: 20%
- Спина: 10%
- Грудь: 5%

**Рекомендации от Gemini:**

1. **Баланс мышечных групп** - Тренировка отлично сбалансирована с акцентом на ноги и плечи.

2. **Объем и интенсивность** - Хороший объем (55 повторений) для лесенки. Достаточное время восстановления между подходами.

3. **Рекомендации** - Рассмотрите добавление упражнений на спину в следующую тренировку для лучшего баланса.

4. **Восстановление** - 48 часов отдыха достаточно перед следующей тренировкой.

---

_Анализ от 2026-02-11T18:30:00Z_
```

---

## 3. Updating All Exercises

### Run Bulk Update

```bash
python main.py --update-exercises
```

**Expected Output:**

```
✅ Config loaded from config.yaml

🔄 Updating all exercises...

🔍 Found 15 exercise files

📝 Enriching: Трастер с гирей
   - Found in cache
✅ Updated: Трастер с гирей

📝 Enriching: Рывок гири
   - Searching Perplexity for exercise data...
✅ Updated: Рывок гири

⏭️  Skipping: Становая тяга (already enriched)

📝 Enriching: Приседания с гирей
   - Found in cache
✅ Updated: Приседания с гирей

📊 Summary:
   Updated: 10
   Skipped (already enriched): 5
   Total: 15
```

### How It Works

1. The tool scans the `Exercises/` folder
2. For each exercise, it checks:
   - Is `met_base` empty?
   - Is `cal_per_rep` empty?
   - Is `muscle_groups` empty?
3. If any field is missing, it:
   - Checks local cache first
   - Queries Perplexity API if not cached
   - Saves result to cache
   - Updates the exercise file

---

## 4. Setting Up Automatic Analysis with Cron

### Option A: Local Machine (macOS/Linux)

#### Step 1: Create Script

Create `run_analysis.sh`:

```bash
#!/bin/bash
cd /path/to/workout-analyzer
python main.py --analyze-latest
```

Make it executable:

```bash
chmod +x run_analysis.sh
```

#### Step 2: Add to Crontab

```bash
crontab -e
```

Add this line to run daily at 9 PM:

```
0 21 * * * /path/to/workout-analyzer/run_analysis.sh >> /var/log/workout-analyzer.log 2>&1
```

#### Step 3: Verify Cron Setup

```bash
# List current crontab
crontab -l

# Check cron service status (macOS)
sudo brew services list | grep cron

# Check logs
tail -f /var/log/workout-analyzer.log
```

### Option B: GitHub Actions

Create `.github/workflows/analyze-workouts.yml`:

```yaml
name: Analyze Workouts
on:
  schedule:
    - cron: "0 21 * * *" # 9 PM daily
  workflow_dispatch:

jobs:
  analyze:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
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

#### Setup GitHub Secrets

1. Go to your repository on GitHub
2. Navigate to Settings → Secrets and variables → Actions
3. Add these secrets:
   - `GEMINI_API_KEY`: Your Gemini API key
   - `PERPLEXITY_API_KEY`: Your Perplexity API key

### Option C: Oracle Cloud VM

#### Step 1: Connect to VM

```bash
ssh user@your-vm-ip
```

#### Step 2: Clone and Setup

```bash
git clone <your-repo-url>
cd workout-analyzer
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your API keys
```

#### Step 3: Setup Cron

```bash
crontab -e
```

Add:

```
0 21 * * * cd /home/user/workout-analyzer && /usr/bin/python3 main.py --analyze-latest >> /var/log/workout-analyzer.log 2>&1
```

#### Step 4: Create Log Rotation

Create `/etc/logrotate.d/workout-analyzer`:

```
/var/log/workout-analyzer {
    weekly
    missingok
    rotate 4
    compress
    delaycompress
    notifempty
}
```

### Verify Automation

Test your setup manually:

```bash
# Test script
./run_analysis.sh

# Test with verbose output
python main.py --analyze-latest -v

# Check last run time
grep "Analysis complete" /var/log/workout-analyzer.log | tail -1
```

---

## Common Issues and Solutions

### Issue: "API key not set"

**Solution:** Ensure `.env` file exists in the project root:

```bash
cat .env
# Should show:
# GEMINI_API_KEY=your_key
# PERPLEXITY_API_KEY=your_key
```

### Issue: "Exercises folder not found"

**Solution:** Check `config.yaml`:

```yaml
obsidian:
  vault_path: "/Users/username/Documents/Obsidian Vault"
  exercises_folder: "Exercises"
```

### Issue: No exercises extracted

**Solution:** Ensure your workout format uses bullet points:

```markdown
## Упражнения

- Упражнение 1 (1x24кг) ✅
- Упражнение 2 (2x16кг) ✅

# Wrong format:

Упражнение 1 (1x24кг) ❌
```

### Issue: Rate limiting from API

**Solution:** Add delays between requests in `config.yaml` or wait a few minutes before retrying.

---

## Next Steps

- Set up automatic sync with Obsidian Shell Commands
- Configure notifications for completed analysis
- Create dashboards in Obsidian with DataviewJS
- Export data to Notion or other platforms
