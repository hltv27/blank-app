#!/bin/bash
# Auto-deploy: verifica commits novos e reinicia o bot se necessário

REPO="/root/blank-app"
BRANCH="claude/setup-project-structure-3xwuR"
LOG="/root/deploy.log"

cd "$REPO" || exit 1

git fetch origin "$BRANCH" --quiet

LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse "origin/$BRANCH")

if [ "$LOCAL" = "$REMOTE" ]; then
    exit 0
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Novo commit detectado — a actualizar..." >> "$LOG"

git reset --hard "origin/$BRANCH" >> "$LOG" 2>&1

# Carrega credenciais
grep -E 'export.*(TELEGRAM|BINANCE)' /root/.bashrc > /tmp/ce 2>/dev/null
source /tmp/ce 2>/dev/null

# Reinicia o bot
pkill -f "python.*main.py" 2>/dev/null
sleep 2

cd "$REPO/claw_v8"
nohup python main.py > /root/claw.log 2>&1 &
echo $! > /root/claw.pid

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Bot reiniciado (PID $(cat /root/claw.pid))" >> "$LOG"
