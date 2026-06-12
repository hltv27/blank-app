#!/bin/bash
# Auto-deploy: verifica commits novos e reinicia o bot se necessário
# Também detecta crash do bot e envia alerta Telegram

REPO="/root/blank-app"
BRANCH="main"
LOG="/root/deploy.log"

# Carrega credenciais
grep -E 'export.*(TELEGRAM|BINANCE)' /root/.bashrc > /tmp/ce 2>/dev/null
source /tmp/ce 2>/dev/null

_tg() {
    curl -s "https://api.telegram.org/bot${TELEGRAM_TOKEN}/sendMessage" \
        -d "chat_id=${TELEGRAM_CHAT_ID}" \
        -d "text=$1" > /dev/null 2>&1
}

cd "$REPO" || exit 1

git fetch origin "$BRANCH" --quiet

LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse "origin/$BRANCH")

if [ "$LOCAL" != "$REMOTE" ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Novo commit detectado — a actualizar..." >> "$LOG"
    git reset --hard "origin/$BRANCH" >> "$LOG" 2>&1

    pkill -f "python.*main.py" 2>/dev/null
    sleep 2

    cd "$REPO/claw_v8"
    nohup python3 main.py > /root/claw.log 2>&1 &
    echo $! > /root/claw.pid

    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Bot reiniciado (PID $(cat /root/claw.pid))" >> "$LOG"
    exit 0
fi

# Sem novo commit — verifica se o bot ainda está vivo
if ! pgrep -f "python3.*main.py" > /dev/null 2>&1; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Bot morto — a reiniciar..." >> "$LOG"

    cd "$REPO/claw_v8"
    nohup python3 main.py > /root/claw.log 2>&1 &
    echo $! > /root/claw.pid

    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Bot reiniciado após crash (PID $(cat /root/claw.pid))" >> "$LOG"
    _tg "🚨 CLAW BOT reiniciado após crash — verifica o log no VPS"
fi
