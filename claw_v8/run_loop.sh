#!/usr/bin/env bash
# Mantém o Claw Agent vivo no Termux — reinicia automaticamente sempre
# que main.py terminar (crash ou watchdog), já que não há systemd/cron.
cd "$(dirname "$0")" || exit 1

while true; do
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] (re)iniciando main.py" >> ~/claw.log
    python3 -u main.py >> ~/claw.log 2>&1
    code=$?
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] main.py terminou (exit $code) — reiniciando em 5s" >> ~/claw.log
    sleep 5
done
