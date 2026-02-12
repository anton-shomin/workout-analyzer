# Cron Setup for Workout Analyzer

This guide explains how to set up automatic workout analysis using cron on a Linux VM (Oracle Cloud, AWS, DigitalOcean, etc.).

## Prerequisites

1. **Python 3.11+** installed on the VM
2. **Git** installed
3. **Obsidian vault** accessible (local or synced)
4. **API keys** for Gemini and Perplexity

## Setup Steps

### 1. Clone the Repository

```bash
# Connect to your VM
ssh user@your-vm-ip

# Clone the repository
git clone https://github.com/your-username/workout-analyzer.git
cd workout-analyzer

# If using Obsidian vault as a submodule
git submodule update --init --recursive
```

### 2. Install Dependencies

```bash
# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Deactivate when done
deactivate
```

### 3. Configure Environment Variables

Create a `.env` file in the project root:

```bash
# Copy example to .env
cp .env.example .env

# Edit .env with your API keys
nano .env
```

```env
# API Keys
GEMINI_API_KEY=your_gemini_api_key_here
PERPLEXITY_API_KEY=your_perplexity_api_key_here

# Obsidian Vault Path (optional - for automatic vault updates)
OBSIDIAN_VAULT_PATH=/home/user/Obsidian/Vault

# Python path for cron
PYTHON_PATH=/home/user/workout-analyzer/venv/bin/python3
```

### 4. Test the Setup

```bash
# Activate virtual environment
source venv/bin/activate

# Test with latest workout
python main.py --analyze-latest

# Test with specific date
python main.py --analyze-workout 2026-02-11

# Deactivate
deactivate
```

### 5. Setup Logging

Create a log directory:

```bash
mkdir -p /home/user/workout-analyzer/logs
touch /home/user/workout-analyzer/logs/workout-analyzer.log
```

### 6. Configure Crontab

Edit the crontab:

```bash
crontab -e
```

Add one of the following configurations:

#### Option A: Daily at 23:00 (EET/Riga time)

```bash
# Daily analysis at 23:00 EET
0 23 * * * cd /home/user/workout-analyzer && /home/user/workout-analyzer/venv/bin/python3 main.py --analyze-latest >> /home/user/workout-analyzer/logs/workout-analyzer.log 2>&1
```

#### Option B: Every 4 hours

```bash
# Every 4 hours
0 */4 * * * cd /home/user/workout-analyzer && /home/user/workout-analyzer/venv/bin/python3 main.py --analyze-latest >> /home/user/workout-analyzer/logs/workout-analyzer.log 2>&1
```

#### Option C: After workout file is created (using inotifywait)

```bash
# Install inotify-tools first
sudo apt-get install inotify-tools

# Create a script for file watching
cat > /home/user/workout-analyzer/watch_workouts.sh << 'EOF'
#!/bin/bash
inotifywait -m -e close_write /home/user/Obsidian/Vault/Workouts/ --format '%f' | while read filename
do
    if [[ "$filename" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}\.md$ ]]; then
        echo "New workout detected: $filename"
        cd /home/user/workout-analyzer
        ./venv/bin/python3 main.py --analyze-workout "${filename%.md}" >> logs/workout-analyzer.log 2>&1
    fi
done
EOF

chmod +x /home/user/workout-analyzer/watch_workouts.sh

# Add to systemd service or run in screen/tmux
```

### 7. Verify Crontab Installation

```bash
# List current crontab
crontab -l

# Check cron service status (systemd)
sudo systemctl status cron

# View cron logs
sudo journalctl -u cron
```

## Advanced Configuration

### Using systemd Instead of Cron

Create a systemd service and timer:

**Service file:** `/etc/systemd/system/workout-analyzer.service`

```ini
[Unit]
Description=Workout Analyzer Service
After=network.target

[Service]
Type=oneshot
User=user
WorkingDirectory=/home/user/workout-analyzer
Environment="PATH=/home/user/workout-analyzer/venv/bin"
EnvironmentFile=/home/user/workout-analyzer/.env
ExecStart=/home/user/workout-analyzer/venv/bin/python3 main.py --analyze-latest
StandardOutput=append:/home/user/workout-analyzer/logs/workout-analyzer.log
StandardError=append:/home/user/workout-analyzer/logs/workout-analyzer.log

[Install]
WantedBy=multi-user.target
```

**Timer file:** `/etc/systemd/system/workout-analyzer.timer`

```ini
[Unit]
Description=Run Workout Analyzer daily at 23:00
Requires=workout-analyzer.service

[Timer]
OnCalendar=*-*-* 23:00:00
Persistent=true
Unit=workout-analyzer.service

[Install]
WantedBy=timers.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable workout-analyzer.timer
sudo systemctl start workout-analyzer.timer
sudo systemctl status workout-analyzer.timer
```

### Using Screen/tmux for Long-Running Processes

```bash
# Using screen
screen -S workout-analyzer
cd /home/user/workout-analyzer
./watch_workouts.sh

# Detach: Ctrl+A, D

# Reattach
screen -r workout-analyzer

# Using tmux
tmux new-session -s workout-analyzer
./watch_workouts.sh

# Detach: Ctrl+B, D
# Reattach: tmux attach-session -t workout-analyzer
```

## Troubleshooting

### Check Logs

```bash
# View recent log entries
tail -100 /home/user/workout-analyzer/logs/workout-analyzer.log

# Watch logs in real-time
tail -f /home/user/workout-analyzer/logs/workout-analyzer.log
```

### Common Issues

#### 1. Cron not running

```bash
# Check if cron is installed
which cron

# Install cron if missing
sudo apt-get update
sudo apt-get install cron

# Start cron
sudo systemctl start cron
sudo systemctl enable cron
```

#### 2. Python path issues

Use absolute paths in crontab:

```bash
# Wrong
0 23 * * * python main.py --analyze-latest

# Correct (absolute path to venv python)
0 23 * * * /home/user/workout-analyzer/venv/bin/python3 /home/user/workout-analyzer/main.py --analyze-latest
```

#### 3. Environment variables not loaded

Crons don't load `.env` files automatically. Options:

```bash
# Option 1: Source .env before running
0 23 * * * cd /home/user/workout-analyzer && source .env && ./venv/bin/python3 main.py --analyze-latest >> logs/workout-analyzer.log 2>&1

# Option 2: Use EnvironmentFile in systemd
EnvironmentFile=/home/user/workout-analyzer/.env

# Option 3: Export in script
```

#### 4. Permission denied errors

```bash
# Fix log file permissions
sudo chown -R user:user /home/user/workout-analyzer/logs/
chmod -R 755 /home/user/workout-analyzer/

# Make scripts executable
chmod +x /home/user/workout-analyzer/*.sh
```

### Debug Mode

Run manually with verbose output:

```bash
cd /home/user/workout-analyzer
source venv/bin/activate
python main.py --analyze-latest -v
```

## Security Considerations

1. **Protect API keys**: Never commit `.env` files to git
2. **Use secrets management**: Consider using GitHub Secrets or cloud key management
3. **Limit permissions**: Run cron jobs with minimal required permissions
4. **Network security**: If vault is remote, use VPN or SSH tunneling

## Monitoring

### Health Check Script

Create `/home/user/workout-analyzer/health_check.sh`:

```bash
#!/bin/bash

LOG_FILE="/home/user/workout-analyzer/logs/workout-analyzer.log"
LAST_RUN=$(tail -5 "$LOG_FILE" | grep -oP '\d{4}-\d{2}-\d{2} \d{2}:\d{2}' | tail -1)

if [ -z "$LAST_RUN" ]; then
    echo "WARNING: No recent activity detected"
    exit 1
fi

echo "Last successful run: $LAST_RUN"
exit 0
```

Add to crontab for monitoring:

```bash
# Check every hour
0 * * * * /home/user/workout-analyzer/health_check.sh || echo "Workout analyzer may be failing"
```

## Summary

| Component     | Command/Path                                                                                                                 |
| ------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| Project path  | `/home/user/workout-analyzer`                                                                                                |
| Python venv   | `/home/user/workout-analyzer/venv/bin/python3`                                                                               |
| Main script   | `/home/user/workout-analyzer/main.py`                                                                                        |
| Log file      | `/home/user/workout-analyzer/logs/workout-analyzer.log`                                                                      |
| Config        | `/home/user/workout-analyzer/.env`                                                                                           |
| Crontab entry | `0 23 * * * cd /home/user/workout-analyzer && ./venv/bin/python3 main.py --analyze-latest >> logs/workout-analyzer.log 2>&1` |
