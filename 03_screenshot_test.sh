#!/bin/bash
# Hermes Connection Test Suite - Test 3: Screenshot-Test
echo "=== Test 3: Screenshot-Fähigkeiten ==="
echo ""

echo "3.1 ImageMagick (import):"
if command -v import &>/dev/null; then
    echo "  [OK] ImageMagick verfügbar"
    # Test-Screenshot
    import -window root /tmp/hermes-test-screenshot-im.png 2>/dev/null
    if [ -f /tmp/hermes-test-screenshot-im.png ]; then
        FILESIZE=$(stat -c%s /tmp/hermes-test-screenshot-im.png 2>/dev/null || echo 0)
        echo "  [OK] Screenshot via import: ${FILESIZE}B"
        rm -f /tmp/hermes-test-screenshot-im.png
    else
        echo "  [FAIL] Screenshot via import fehlgeschlagen (kein X11?)"
    fi
else
    echo "  [FAIL] ImageMagick fehlt"
fi

echo ""
echo "3.2 gnome-screenshot:"
if command -v gnome-screenshot &>/dev/null; then
    echo "  [OK] gnome-screenshot installiert"
else
    echo "  [WARN] gnome-screenshot nicht installiert (kann dennoch gehen)"
fi

echo ""
echo "3.3 flameshot:"
if command -v flameshot &>/dev/null; then
    echo "  [OK] flameshot installiert"
else
    echo "  [WARN] flameshot nicht installiert"
fi

echo ""
echo "3.4 ffmpeg Screenshot:"
if command -v ffmpeg &>/dev/null; then
    ffmpeg -y -f x11grab -video_size 800x600 -i :0.0 -vframes 1 /tmp/hermes-test-screenshot-ff.png 2>/dev/null
    if [ -f /tmp/hermes-test-screenshot-ff.png ]; then
        FILESIZE=$(stat -c%s /tmp/hermes-test-screenshot-ff.png 2>/dev/null || echo 0)
        echo "  [OK] Screenshot via ffmpeg: ${FILESIZE}B"
        rm -f /tmp/hermes-test-screenshot-ff.png
    else
        echo "  [FAIL] ffmpeg Screenshot fehlgeschlagen"
    fi
else
    echo "  [FAIL] ffmpeg nicht installiert"
fi

echo ""
echo "3.5 Python Pillow Screenshot:"
python3 -c "
from PIL import ImageGrab
import os
img = ImageGrab.grab()
img.save('/tmp/hermes-test-screenshot-pil.png')
size = os.path.getsize('/tmp/hermes-test-screenshot-pil.png')
print(f'  [OK] Pillow Screenshot: {size}B')
os.remove('/tmp/hermes-test-screenshot-pil.png')
" 2>/dev/null || echo "  [FAIL] Pillow Screenshot fehlgeschlagen"

echo ""
echo "3.6 CDP Screenshot (via TradingView-MCP Tab):"
TV_TAB=$(curl -s --max-time 3 "http://localhost:9222/json/list" 2>/dev/null | python3 -c "
import sys, json
tabs = json.load(sys.stdin)
tv_tabs = [t for t in tabs if 'tradingview.com/chart' in t.get('url', '').lower()]
if tv_tabs:
    print(tv_tabs[0]['id'])
    print(tv_tabs[0].get('url','')[:80])
else:
    print('NO_TV_TAB')
" 2>/dev/null)
if [ -n "$TV_TAB" ] && [ "$TV_TAB" != "NO_TV_TAB" ]; then
    TAB_ID=$(echo "$TV_TAB" | head -1)
    TV_URL=$(echo "$TV_TAB" | tail -1)
    echo "  [OK] TradingView Tab gefunden (ID: ${TAB_ID:0:20}...)"
    echo "  URL: $TV_URL"
    echo "  [HINWEIS] CDP-Screenshot über tradingview-mcp möglich (capture_screenshot tool)"
else
    echo "  [WARN] Kein TradingView Tab im Browser gefunden"
    echo "  (Browser läuft, aber TV ist nicht geöffnet)"
fi

echo ""
echo "=== Test 3 abgeschlossen ==="
