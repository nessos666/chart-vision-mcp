#!/bin/bash
# Hermes Connection Test Suite - Test 5: Prozessbeobachtung
echo "=== Test 5: Prozessbeobachtung ==="
echo ""

echo "5.1 Laufende Hermes-Prozesse:"
ps aux | grep hermes | grep -v grep | head -5
echo ""

echo "5.2 Laufende Browser/TV Prozesse:"
ps aux | grep -E "chrome|tradingview|tv_mcp" | grep -v grep | head -5
echo ""

echo "5.3 inotifywait:"
if command -v inotifywait &>/dev/null; then
    echo "  [OK] inotifywait verfügbar (Datei-Überwachung)"
else
    echo "  [FAIL] inotifywait nicht installiert"
fi

echo ""
echo "5.4 systemd Timer (user):"
TIMER_COUNT=$(systemctl --user list-timers 2>/dev/null | grep -c ".timer" || echo 0)
echo "  [OK] $TIMER_COUNT systemd Timer aktiv"
systemctl --user list-timers 2>/dev/null | head -15

echo ""
echo "5.5 systemd Services (user) - NQ/Handel:"
systemctl --user list-units --type=service 2>/dev/null | grep -E "nq|trade|scanner|sweep" | head -10

echo ""
echo "5.6 watch tool:"
if command -v watch &>/dev/null; then
    echo "  [OK] watch verfügbar"
else
    echo "  [WARN] watch nicht installiert"
fi

echo ""
echo "5.7 systemd Services (user) - Hermes:"
systemctl --user list-units --type=service 2>/dev/null | grep -E "hermes|gateway" | head -5

echo ""
echo "=== Test 5 abgeschlossen ==="
