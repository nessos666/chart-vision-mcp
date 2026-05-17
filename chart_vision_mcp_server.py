#!/usr/bin/env python3
"""
Chart Vision MCP Server — Hermes Integration (v2.0)
====================================================
Hybrid: OpenCV (lokal) + Tesseract OCR
Kein API-Key nötig, keine GPU, keine Modelle.

Tools:
  chart_vision_analyze     -> Screenshot + OpenCV + OCR (lokal, sofort)
  chart_vision_screenshot  -> Nur Screenshot speichern

Protocol: stdio JSON-RPC (MCP Standard)
"""

import sys
import json
import os
import io
import subprocess
import tempfile
from datetime import datetime

# ---------------------------------------------------------------------------
# Screenshot
# ---------------------------------------------------------------------------

def take_screenshot():
    """Macht Screenshot (Pillow > ffmpeg Fallback)."""
    try:
        from PIL import ImageGrab
        img = ImageGrab.grab()
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()
    except ImportError:
        pass
    
    try:
        tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        tmp.close()
        subprocess.run(
            ["ffmpeg", "-y", "-f", "x11grab", "-video_size", "1920x1080",
             "-i", os.environ.get("DISPLAY", ":0.0"), "-vframes", "1", tmp.name],
            capture_output=True, timeout=10
        )
        with open(tmp.name, "rb") as f:
            data = f.read()
        os.unlink(tmp.name)
        return data
    except:
        return None

def save_screenshot(data):
    path = os.path.expanduser(
        f"~/hermes-test/vision_screenshots/chart_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    )
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(data)
    return path

# ---------------------------------------------------------------------------
# OpenCV Analyse
# ---------------------------------------------------------------------------

def analyze_candles(img):
    import cv2
    import numpy as np
    chart_area = img[int(img.shape[0]*0.1):int(img.shape[0]*0.85), :]
    green = np.sum(cv2.inRange(chart_area, np.array([0, 80, 0]), np.array([80, 255, 80])) > 0)
    red = np.sum(cv2.inRange(chart_area, np.array([80, 0, 0]), np.array([255, 80, 80])) > 0)
    total = green + red
    if total == 0:
        return {"bias": "unknown", "gruen_pct": 0, "rot_pct": 0}
    return {
        "bias": "bullish" if green > red * 1.2 else "bearish" if red > green * 1.2 else "neutral",
        "gruen_pct": round(green / total * 100, 1),
        "rot_pct": round(red / total * 100, 1)
    }

def analyze_colors(img):
    import cv2
    import numpy as np
    h, w = img.shape[:2]
    ranges = {
        "gruen": [([0, 100, 0], [80, 255, 80])],
        "rot": [([100, 0, 0], [255, 80, 80])],
        "gelb": [([120, 120, 0], [255, 255, 80])],
        "blau": [([0, 50, 120], [80, 150, 255])],
        "pink": [([120, 0, 120], [255, 80, 255])],
        "orange": [([180, 80, 0], [255, 180, 60])],
        "cyan": [([0, 100, 100], [80, 200, 200])],
        "weiss": [([180, 180, 180], [255, 255, 255])],
    }
    colors = {}
    for name, rngs in ranges.items():
        mask = np.zeros((h, w), dtype=np.uint8)
        for low, high in rngs:
            m = cv2.inRange(img, np.array(low), np.array(high))
            mask = cv2.bitwise_or(mask, m)
        pct = round(np.sum(mask > 0) / (h * w) * 100, 2)
        if pct > 0.3:
            colors[name] = pct
    return colors

def analyze_levels(img):
    import cv2
    import numpy as np
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    edges = cv2.Canny(gray, 50, 150)
    lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=100, minLineLength=100, maxLineGap=20)
    if lines is None:
        return {"level_count": 0}
    y_positions = sorted(set((y1 + y2) // 2 for line in lines for x1, y1, x2, y2 in [line[0]] if abs(y2 - y1) < 5))
    return {"level_count": len(y_positions)}

def analyze_zones(img):
    import cv2
    import numpy as np
    h, w = img.shape[:2]
    zones = {}
    for name, (low, high) in {"gelbe_zone": ([120, 120, 0], [255, 255, 100]), "pink_zone": ([120, 0, 120], [255, 100, 255]), "blau_zone": ([0, 80, 150], [80, 200, 255])}.items():
        mask = cv2.inRange(img, np.array(low), np.array(high))
        pct = round(np.sum(mask > 0) / (h * w) * 100, 2)
        if pct > 0.2:
            zones[name] = pct
    return zones

# ---------------------------------------------------------------------------
# Tesseract OCR
# ---------------------------------------------------------------------------

def ocr_analyze(image_path):
    try:
        import pytesseract
    except ImportError:
        return {"status": "pytesseract nicht installiert"}
    try:
        import cv2
        import re
        img = cv2.imread(image_path)
        if img is None:
            return {"status": "konnte Bild nicht laden"}
        full_text = pytesseract.image_to_string(img, lang='eng')
        h = img.shape[0]
        bottom = img[int(h*0.7):, :]
        bottom_text = pytesseract.image_to_string(bottom, lang='eng')
        prices = re.findall(r'\d+[.,]\d{2}', full_text)
        return {"status": "ok", "full_text": full_text.strip()[:500], "bottom_text": bottom_text.strip()[:300], "prices_found": prices[:20]}
    except Exception as e:
        return {"status": f"OCR Fehler: {e}"}

# ---------------------------------------------------------------------------
# MCP Handler
# ---------------------------------------------------------------------------

def handle_request(request):
    req_id = request.get("id", 0)
    method = request.get("method", "")
    
    if method == "initialize":
        return {
            "jsonrpc": "2.0", "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "chart-vision", "version": "2.0.0"}
            }
        }
    
    if method == "tools/list":
        return {
            "jsonrpc": "2.0", "id": req_id,
            "result": {
                "tools": [
                    {
                        "name": "chart_vision_analyze",
                        "description": "Macht Screenshot vom TradingView Chart und analysiert Farben, Levels, Trend lokal (OpenCV) + OCR (Tesseract). Kein API-Key oder GPU nötig.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "region": {
                                    "type": "string",
                                    "enum": ["full", "chart"],
                                    "description": "Bildbereich (full = ganzer Bildschirm, chart = nur Chart)"
                                }
                            }
                        }
                    },
                    {
                        "name": "chart_vision_screenshot",
                        "description": "Macht nur einen Screenshot und speichert ihn. Keine Analyse.",
                        "inputSchema": {"type": "object", "properties": {}}
                    }
                ]
            }
        }
    
    if method == "tools/call":
        tool = request.get("params", {}).get("name", "")
        
        if tool == "chart_vision_screenshot":
            data = take_screenshot()
            if not data:
                return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": "Kein Screenshot moeglich"}], "isError": True}}
            path = save_screenshot(data)
            return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps({"success": True, "file_path": path, "size_bytes": len(data)})}]}}
        
        if tool == "chart_vision_analyze":
            data = take_screenshot()
            if not data:
                return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": "Kein Screenshot moeglich"}], "isError": True}}
            try:
                import cv2
                import numpy as np
                nparr = np.frombuffer(data, np.uint8)
                img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                result = {"candles": analyze_candles(img_rgb), "colors": analyze_colors(img_rgb), "levels": analyze_levels(img), "zones": analyze_zones(img_rgb)}
                path = save_screenshot(data)
                result["screenshot_path"] = path
                result["ocr"] = ocr_analyze(path)
                return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]}}
            except Exception as e:
                return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": f"Analyse-Fehler: {e}"}], "isError": True}}
        
        return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": f"Unbekanntes Tool: {tool}"}], "isError": True}}
    
    if method == "notifications/initialized":
        return None
    
    return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": f"Unbekannte Methode: {method}"}], "isError": True}}

# ---------------------------------------------------------------------------
# Main Loop
# ---------------------------------------------------------------------------

def main():
    os.makedirs(os.path.expanduser("~/hermes-test/vision_screenshots"), exist_ok=True)
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
            response = handle_request(request)
            if response:
                sys.stdout.write(json.dumps(response) + "\n")
                sys.stdout.flush()
        except json.JSONDecodeError:
            pass
        except Exception as e:
            error_response = {"jsonrpc": "2.0", "id": None, "error": {"code": -32603, "message": str(e)}}
            sys.stdout.write(json.dumps(error_response) + "\n")
            sys.stdout.flush()

if __name__ == "__main__":
    main()
