#!/usr/bin/env bash
# Linux/macOS: process every .xlsx in the input folder, then show run status and open tickets.
# Schedule with cron, e.g. every day at 9:00:   0 9 * * * /path/to/invoice-bot/deploy/run.sh
set -euo pipefail
cd "$(dirname "$0")/.."
INPUT_DIR="${BOT_INPUT_DIR:-input}"
shopt -s nullglob
files=("$INPUT_DIR"/*.xlsx)
if [ ${#files[@]} -eq 0 ]; then
  echo "No input files found in $INPUT_DIR"; exit 0
fi
for f in "${files[@]}"; do
  python3 main.py run "$f" || echo "Run failed for $f (see logs/bot.log)"
done
python3 main.py status --limit 5
python3 main.py tickets --status OPEN
