#!/data/data/com.termux/files/usr/bin/bash
# Inicia o bot com wake lock para evitar que o Android o mate

BOT_DIR="$(cd "$(dirname "$0")" && pwd)"
LOG="$BOT_DIR/affiliate_bot.log"

echo "A iniciar o Affiliate Bot..."
echo "  Directório: $BOT_DIR"
echo "  Log: $LOG"
echo ""

# Activar wake lock — impede Android de dormir a CPU
if command -v termux-wake-lock &>/dev/null; then
    termux-wake-lock
    echo "  ✅ Wake lock activado"
else
    echo "  ⚠️  termux-wake-lock não disponível — instala Termux:API"
fi

# Notificação persistente
if command -v termux-notification &>/dev/null; then
    termux-notification \
        --id 42 \
        --title "Affiliate Bot 🤖" \
        --content "A correr 24/7 — não feches o Termux" \
        --ongoing \
        --priority high \
        2>/dev/null &
fi

echo "  ✅ Bot a iniciar..."
echo "  (Ctrl+C para parar)"
echo ""

cd "$BOT_DIR"

# Loop de restart automático se o bot crashar
while true; do
    python bot.py 2>&1 | tee -a "$LOG"
    EXIT_CODE=$?
    if [ $EXIT_CODE -eq 0 ]; then
        echo "Bot terminou normalmente. A reiniciar em 30s..."
    else
        echo "Bot crashou (exit $EXIT_CODE). A reiniciar em 60s..."
        sleep 60
    fi
    sleep 30
done
