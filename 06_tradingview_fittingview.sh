#!/bin/bash
# Hermes Connection Test Suite - Test 6: TradingView/FittingView-Öffnungstest
echo "=== Test 6: TradingView/FittingView-Integration ==="
echo ""

echo "6.1 TradingView-MCP Node.js Server (78 Tools):"
if [ -d ~/tradingview-mcp ]; then
    echo "  [OK] tradingview-mcp Verzeichnis existiert"
    NODE_MODULES=$(ls ~/tradingview-mcp/node_modules/.package-lock.json 2>/dev/null && echo "installiert" || echo "nicht installiert")
    echo "  Dependencies: $NODE_MODULES"
    
    # Prüf ob der Server lauffähig ist
    if [ -f ~/tradingview-mcp/src/server.js ]; then
        TOOL_COUNT=$(grep -c "server.tool\|registerTool\|\.tool(" ~/tradingview-mcp/src/tools/*.js 2>/dev/null | tail -1 | grep -oP '\d+' || echo "?")
        echo "  [OK] Server-Source: ~/tradingview-mcp/src/server.js"
    fi
else
    echo "  [WARN] tradingview-mcp Verzeichnis nicht gefunden"
fi

echo ""
echo "6.2 Hermes TradingView-MCP (Python, 5 Tools):"
if [ -f ~/HAUPTLAGER/27_TV_Watch_Agent/tv_mcp_server.py ]; then
    echo "  [OK] tv_mcp_server.py existiert"
    # Prüfe Config-Eintrag
    grep -q "tradingview" ~/.hermes/config.yaml 2>/dev/null && echo "  [OK] In Hermes-Config registriert" || echo "  [FAIL] Nicht in Hermes-Config"
    
    # Prüfe Venv
    if [ -f ~/HAUPTLAGER/27_TV_Watch_Agent/.venv/bin/python3 ]; then
        echo "  [OK] Python-Venv existiert"
    else
        echo "  [WARN] Kein Venv gefunden"
    fi
else
    echo "  [FAIL] tv_mcp_server.py fehlt"
fi

echo ""
echo "6.3 FittingView:"
FV_COUNT=$(find /home/boobi -iname "*fittingview*" -o -iname "*fitting_view*" 2>/dev/null | wc -l)
if [ "$FV_COUNT" -gt 0 ]; then
    echo "  [INFO] $FV_COUNT FittingView-Dateien gefunden"
    find /home/boobi -iname "*fittingview*" -o -iname "*fitting_view*" 2>/dev/null | head -5
else
    echo "  [INFO] Keine FittingView-Dateien gefunden (kein separates Tool installiert)"
    echo "  FittingView ist Teil der TradingView Desktop-Oberfläche"
fi

echo ""
echo "6.4 Chrome Remote Debugging (CDP Connection):"
CDP_WS=$(curl -s --max-time 3 "http://localhost:9222/json/list" 2>/dev/null | python3 -c "
import sys, json
tabs = json.load(sys.stdin)
for t in tabs:
    url = t.get('url', '')
    if 'tradingview.com/chart' in url.lower():
        print(f\"Tab: {t.get('title','?')} — WS: {t.get('webSocketDebuggerUrl','?')[:50]}...\")
        break
else:
    print('KEIN_TRADINGVIEW_TAB')
" 2>/dev/null)
if [ -n "$CDP_WS" ] && [ "$CDP_WS" != "KEIN_TRADINGVIEW_TAB" ]; then
    echo "  [OK] CDP-Verbindung zu TradingView möglich"
    echo "  $CDP_WS"
else
    echo "  [WARN] Kein TradingView Chart im Browser -> Kann über Hermes' browser_navigate geöffnet werden"
fi

echo ""
echo "6.5 Hermes Browser-Vision (Screenshots mit KI-Analyse):"
grep -q "browser_vision" ~/.hermes/hermes-agent/tools/browser_tool.py 2>/dev/null && echo "  [OK] browser_vision-Tool vorhanden" || echo "  [WARN] browser_vision könnte anders implementiert sein"

echo ""
echo "=== Test 6 abgeschlossen ==="
