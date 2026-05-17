#!/bin/bash
# Hermes Connection Test Suite - Test 1: Netzwerk & Verbindung
echo "=== Test 1: Netzwerk & Verbindung ==="
echo ""

echo "1.1 Internet-Konnektivität:"
if ping -c 1 -W 3 8.8.8.8 >/dev/null 2>&1; then
    echo "  [OK] Internet erreichbar (8.8.8.8)"
else
    echo "  [FAIL] Kein Internet"
fi

echo ""
echo "1.2 TradingView Erreichbarkeit:"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "https://www.tradingview.com" 2>/dev/null)
if [ "$HTTP_CODE" = "200" ]; then
    echo "  [OK] TradingView antwortet (HTTP $HTTP_CODE)"
else
    echo "  [WARN] TradingView: HTTP $HTTP_CODE (kann bei Captcha passieren)"
fi

echo ""
echo "1.3 CDP (Chrome DevTools Protocol) - TradingView Desktop:"
CDP_RESP=$(curl -s --max-time 3 "http://localhost:9222/json/list" 2>/dev/null)
if [ -n "$CDP_RESP" ]; then
    TV_TABS=$(echo "$CDP_RESP" | python3 -c "import sys,json; tabs=json.load(sys.stdin); tv=[t for t in tabs if 'tradingview' in t.get('url','').lower()]; print(f'{len(tv)} TradingView-Tabs gefunden')" 2>/dev/null || echo "OK (Port antwortet)")
    echo "  [OK] CDP Port 9222 antwortet — $TV_TABS"
else
    echo "  [FAIL] CDP Port 9222 nicht erreichbar"
fi

echo ""
echo "1.4 Docker/Qdrant:"
if docker ps --format "{{.Names}}" 2>/dev/null | grep -q qdrant; then
    echo "  [OK] Qdrant läuft"
else
    echo "  [WARN] Qdrant läuft nicht"
fi

echo ""
echo "1.5 Lokale IPs:"
ip -4 addr show | grep -oP 'inet \K[\d.]+' | grep -v '127.0.0' | while read ip; do
    echo "  [INFO] $ip"
done

echo ""
echo "=== Test 1 abgeschlossen ==="
