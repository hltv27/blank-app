#!/data/data/com.termux/files/usr/bin/bash
# Para o bot e liberta o wake lock

echo "A parar o Affiliate Bot..."

pkill -f "python bot.py" 2>/dev/null && echo "  ✅ Bot parado" || echo "  Bot não estava a correr"

# Libertar wake lock
if command -v termux-wake-unlock &>/dev/null; then
    termux-wake-unlock
    echo "  ✅ Wake lock desactivado"
fi

# Remover notificação
if command -v termux-notification-remove &>/dev/null; then
    termux-notification-remove 42 2>/dev/null
fi

echo "Feito."
