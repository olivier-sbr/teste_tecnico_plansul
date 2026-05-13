#!/bin/bash
# Cron — toda segunda-feira às 06h30:
# 30 6 * * 1 cd /caminho/do/projeto && bash run.sh

LOG_FILE="output/logs/pipeline_$(date +%Y%m%d_%H%M%S).log"
mkdir -p output/logs

source .venv/bin/activate

python3 src/main.py >> "$LOG_FILE" 2>&1 || exit 1
