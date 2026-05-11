#!/bin/bash
set -e

LOG_FILE="output/logs/pipeline_$(date +%Y%m%d_%H%M%S).log"
mkdir -p output/logs

source .venv/bin/activate

python3 src/main.py >> "$LOG_FILE" 2>&1
