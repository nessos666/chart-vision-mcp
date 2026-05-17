#!/bin/bash
# Hermes Connection Test Suite - Test 2: Browser-Starttest
echo "=== Test 2: Browser-Fähigkeiten ==="
echo ""

echo "2.1 Google Chrome:"
if command -v google-chrome &>/dev/null; then
    VER=$(google-chrome --version 2>/dev/null)
    echo "  [OK] Chrome installiert: $VER"
else
    echo "  [FAIL] Chrome nicht gefunden"
fi

echo ""
echo "2.2 Playwright:"
if command -v playwright &>/dev/null; then
    VER=$(playwright --version 2>/dev/null)
    echo "  [OK] Playwright $VER"
    PW_BROWSERS=$(playwright ls 2>/dev/null | head -5)
    echo "  Browser: $PW_BROWSERS"
else
    echo "  [FAIL] Playwright nicht installiert"
fi

echo ""
echo "2.3 Xvfb (Virtual Display):"
if command -v Xvfb &>/dev/null; then
    echo "  [OK] Xvfb installiert"
else
    echo "  [FAIL] Xvfb fehlt"
fi

echo ""
echo "2.4 X11 Display:"
echo "  DISPLAY=$DISPLAY"
if [ -n "$DISPLAY" ]; then
    echo "  [OK] X11 Display vorhanden"
else
    echo "  [FAIL] Kein X11 Display"
fi

echo ""
echo "2.5 Chrome Remote Debugging (Port 9222):"
CDP_INFO=$(curl -s --max-time 3 "http://localhost:9222/json/version" 2>/dev/null)
if [ -n "$CDP_INFO" ]; then
    BROWSER=$(echo "$CDP_INFO" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('Browser','?'))" 2>/dev/null)
    echo "  [OK] CDP aktiv — Browser: $BROWSER"
else
    echo "  [FAIL] CDP inaktiv (Port 9222 antwortet nicht?)"
fi

echo ""
echo "2.6 Hermes Browser-Tools Verfügbarkeit:"
grep -q "browser_tool" ~/.hermes/hermes-agent/tools/ 2>/dev/null && echo "  [OK] Hermes hat Browser-Tools" || echo "  [FAIL] Browser-Tools fehlen"

echo ""
echo "=== Test 2 abgeschlossen ==="
