#!/data/data/com.termux/files/usr/bin/bash
# Auto-arranca o bot quando o telemóvel liga (requer Termux:Boot)
termux-wake-lock
cd /data/data/com.termux/files/home/blank-app
python bot.py >> affiliate_bot.log 2>&1
