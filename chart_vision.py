#!/usr/bin/env python3
"""
Hermes Chart Vision — OpenCV Lokale Chart-Analyse
==============================================
Analysiert TradingView Screenshots lokal mit OpenCV.
KEIN API-Key nötig. Läuft komplett offline.

Erkennt:
- Farbige Linien und Zonen (Rot, Grün, Blau, Gelb, etc.)
- Preis-Balken und Kerzen (grün/rot)
- Volumen-Balken
- Text/Labels (via einfacher OCR)
- Chart-Struktur (Trend-Richtung, Range)
- Markierte Levels und Bereiche

Nutzung:
  python3 chart_vision.py                          # Screenshot + Analyse
  python3 chart_vision.py --file pfad/zum/bild.png   # Bestimmtes Bild
  python3 chart_vision.py --debug                     # Zeigt Zwischenschritte

Abhängigkeiten:
  pip install opencv-python pillow numpy
"""

import os
import sys
import subprocess
import tempfile
import json
from datetime import datetime
from collections import Counter

import numpy as np

# ---------------------------------------------------------------------------
# Screenshot
# ---------------------------------------------------------------------------

def take_screenshot():
    """Macht Screenshot via Pillow."""
    try:
        from PIL import ImageGrab
        import PIL.Image
        img = ImageGrab.grab()
        return np.array(img.convert("RGB"))
    except Exception as e:
        print(f"Pillow Fehler: {e}")
    
    # Fallback: ffmpeg
    try:
        tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        tmp.close()
        subprocess.run(
            ["ffmpeg", "-y", "-f", "x11grab", "-video_size", "1920x1080",
             "-i", os.environ.get("DISPLAY", ":0.0"), "-vframes", "1", tmp.name],
            capture_output=True, timeout=10
        )
        import cv2
        img = cv2.imread(tmp.name)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        os.unlink(tmp.name)
        return img
    except Exception as e:
        print(f"ffmpeg Fehler: {e}")
    
    return None

# ---------------------------------------------------------------------------
# Farb-Definitionen (für TradingView Dark Theme)
# ---------------------------------------------------------------------------

# RGB Farbbereiche für TradingView typische Farben
COLORS = {
    "grün (bullish)": {
        "ranges": [
            ((0, 120, 0), (80, 255, 80)),      # Hellgrün
            ((0, 80, 0), (60, 180, 60)),         # Mittelgrün
            ((0, 150, 0), (50, 255, 100)),       # Leuchtgrün
            ((0, 100, 0), (40, 200, 80)),        # Kerzen-grün
        ],
        "typical_for": ["bullische Kerzen", "bullische Labels", "long Signale"]
    },
    "rot (bearish)": {
        "ranges": [
            ((120, 0, 0), (255, 80, 80)),        # Hellrot
            ((80, 0, 0), (200, 60, 60)),          # Mittelrot
            ((150, 0, 0), (255, 60, 60)),         # Leuchtrot
            ((100, 0, 0), (220, 50, 50)),         # Kerzen-rot
        ],
        "typical_for": ["bearische Kerzen", "rote Labels", "short Signale"]
    },
    "gelb (neutral)": {
        "ranges": [
            ((150, 150, 0), (255, 255, 80)),      # Gelb
            ((180, 180, 0), (255, 255, 60)),      # Dunkelgelb
        ],
        "typical_for": ["neutrale Levels", "Settlement", "Midline"]
    },
    "blau": {
        "ranges": [
            ((0, 0, 120), (80, 80, 255)),         # Blau
            ((0, 50, 150), (60, 130, 255)),       # Mittelblau
            ((0, 100, 200), (50, 180, 255)),      # Hellblau
            ((0, 80, 180), (40, 150, 255)),       # Indikator-blau
        ],
        "typical_for": ["SMA/EMA Linien", "Indikator-Linien", "blaue Labels"]
    },
    "pink/magenta": {
        "ranges": [
            ((150, 0, 150), (255, 80, 255)),      # Pink
            ((180, 0, 180), (255, 60, 255)),      # Magenta
        ],
        "typical_for": ["FVG Zonen", "Orderblock Markierungen", "pink Labels"]
    },
    "cyan/türkis": {
        "ranges": [
            ((0, 150, 150), (80, 255, 255)),      # Türkis
            ((0, 120, 120), (60, 200, 200)),      # Dunkeltürkis
        ],
        "typical_for": ["Fibonacci Levels", "Inefficiencies"]
    },
    "orange": {
        "ranges": [
            ((200, 100, 0), (255, 180, 60)),      # Orange
            ((180, 80, 0), (255, 150, 50)),       # Dunkelorange
        ],
        "typical_for": ["PDH/PDL", "Session Hoch/Tief"]
    },
    "weiß/hellgrau": {
        "ranges": [
            ((180, 180, 180), (255, 255, 255)),   # Weiß
            ((130, 130, 130), (200, 200, 200)),   # Hellgrau
        ],
        "typical_for": ["Preis-Labels", "Gitterlinien", "Werte"]
    },
}

# ---------------------------------------------------------------------------
# Analyse-Funktionen
# ---------------------------------------------------------------------------

def detect_colors(img):
    """Erkenne welche Farben im Chart vorkommen und wo."""
    results = {}
    h, w = img.shape[:2]
    
    for color_name, color_info in COLORS.items():
        mask_total = np.zeros((h, w), dtype=np.uint8)
        for low, high in color_info["ranges"]:
            mask = cv2.inRange(img, np.array(low), np.array(high))
            mask_total = cv2.bitwise_or(mask_total, mask)
        
        pixel_count = np.sum(mask_total > 0)
        percentage = (pixel_count / (h * w)) * 100
        
        if percentage > 0.5:  # Mindestens 0.5% der Bildfläche
            # Cluster finden (zusammenhängende Bereiche)
            contours, _ = cv2.findContours(mask_total, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Größe des größten Clusters
            max_area = 0
            if contours:
                max_area = max(cv2.contourArea(c) for c in contours)
            
            results[color_name] = {
                "pct": round(percentage, 1),
                "clusters": len(contours),
                "biggest_cluster_px": int(max_area),
                "typical_for": color_info["typical_for"]
            }
    
    return results

def detect_horizontal_lines(img):
    """Erkenne horizontale Linien (Levels)."""
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    edges = cv2.Canny(gray, 50, 150, apertureSize=3)
    
    lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=100, 
                           minLineLength=100, maxLineGap=20)
    
    if lines is None:
        return {"count": 0, "y_positions": []}
    
    # Gruppiere nahe Linien (gleiches Level)
    y_positions = []
    for line in lines:
        x1, y1, x2, y2 = line[0]
        if abs(y2 - y1) < 5:  # Horizontal
            y_positions.append((y1 + y2) // 2)
    
    # Cluster ähnlicher Y-Positionen
    if not y_positions:
        return {"count": 0, "y_positions": []}
    
    y_clusters = []
    used = set()
    for i, y in enumerate(sorted(y_positions)):
        if i in used:
            continue
        cluster = [y]
        used.add(i)
        for j in range(i+1, len(y_positions)):
            if j not in used and abs(y_positions[j] - y) < 5:
                cluster.append(y_positions[j])
                used.add(j)
        y_clusters.append(int(np.mean(cluster)))
    
    return {
        "count": len(y_clusters),
        "y_positions": y_clusters[:50]  # Max 50 Levels
    }

def detect_price_bars(img):
    """Erkenne grüne/rote Candlestick-Balken im Chart-Bereich."""
    h, w = img.shape[:2]
    
    # Chart-Bereich = mittlere 70% der Höhe, volle Breite
    chart_top = int(h * 0.1)
    chart_bot = int(h * 0.85)
    chart = img[chart_top:chart_bot, :]
    
    # Grüne Pixel (bullish)
    green_mask = cv2.inRange(chart, np.array([0, 100, 0]), np.array([80, 255, 80]))
    green_pct = np.sum(green_mask > 0) / green_mask.size * 100
    
    # Rote Pixel (bearish)
    red_mask = cv2.inRange(chart, np.array([100, 0, 0]), np.array([255, 80, 80]))
    red_pct = np.sum(red_mask > 0) / red_mask.size * 100
    
    total_candle = green_pct + red_pct
    
    if total_candle == 0:
        return {"bias": "unknown", "green_pct": 0, "red_pct": 0}
    
    return {
        "bias": "bullish" if green_pct > red_pct * 1.2 
                else "bearish" if red_pct > green_pct * 1.2 
                else "neutral",
        "green_pct": round(green_pct, 2),
        "red_pct": round(red_pct, 2),
        "green_ratio": round(green_pct / total_candle * 100, 1) if total_candle > 0 else 0
    }

def detect_volume_bars(img):
    """Erkenne Volumen-Balken (unten im Chart)."""
    h, w = img.shape[:2]
    
    # Volumen-Bereich = untere 15%
    vol_area = img[int(h * 0.85):, :]
    
    # Volumen ist oft grün/rot gefärbt
    green_vol = cv2.inRange(vol_area, np.array([0, 80, 0]), np.array([60, 255, 60]))
    red_vol = cv2.inRange(vol_area, np.array([80, 0, 0]), np.array([255, 60, 60]))
    
    green_pct = np.sum(green_vol > 0) / green_vol.size * 100
    red_pct = np.sum(red_vol > 0) / red_vol.size * 100
    
    return {
        "volume_present": (green_pct + red_pct) > 0.5,
        "volume_green_pct": round(green_pct, 2),
        "volume_red_pct": round(red_pct, 2),
        "volume_bias": "bullish" if green_pct > red_pct * 1.3 
                       else "bearish" if red_pct > green_pct * 1.3 
                       else "mixed"
    }

def detect_text_regions(img):
    """Erkenne Bereiche mit Text/Labels (hell auf dunklem Hintergrund)."""
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    
    # Helle Pixel (Text auf dunklem TradingView-Hintergrund)
    _, bright = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)
    
    # Finde zusammenhängende Textblöcke
    contours, _ = cv2.findContours(bright, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    text_regions = []
    for c in contours:
        area = cv2.contourArea(c)
        if 10 < area < 5000:  # Typische Textgröße
            x, y, w, h = cv2.boundingRect(c)
            text_regions.append({"x": x, "y": y, "w": w, "h": h})
    
    return {
        "text_regions_found": len(text_regions),
        "approximate_labels": min(len(text_regions), 30)  # Max 30 Labels
    }

def detect_rectangles(img):
    """Erkenne farbige Rechtecke/Zonen (FVG, Orderblock, EHPDA-Bereiche)."""
    h, w = img.shape[:2]
    
    # Suche nach semi-transparenten farbigen Blöcken
    # Typisch für EHPDA/FVG: Pink, Blau, Gelb, Türkis
    zone_colors = {
        "pink/fvg_zone": cv2.inRange(img, np.array([120, 0, 120]), np.array([255, 100, 255])),
        "blue/inefficiency": cv2.inRange(img, np.array([0, 80, 150]), np.array([80, 200, 255])),
        "yellow/level_zone": cv2.inRange(img, np.array([120, 120, 0]), np.array([255, 255, 100])),
        "cyan/zone": cv2.inRange(img, np.array([0, 100, 100]), np.array([100, 255, 255])),
    }
    
    zones = {}
    for name, mask in zone_colors.items():
        pct = np.sum(mask > 0) / mask.size * 100
        if pct > 0.3:
            zones[name] = round(pct, 1)
    
    return zones

def classify_trend(candle_data):
    """Bestimme Trend basierend auf Kerzen-Farbverhältnis."""
    if candle_data["bias"] == "bullish":
        return "AUFWÄRTSTREND (mehr grüne als rote Kerzen)"
    elif candle_data["bias"] == "bearish":
        return "ABWÄRTSTREND (mehr rote als grüne Kerzen)"
    else:
        return "SEITWÄRTS/UNENTSCHIEDEN (grün/rot ausgeglichen)"

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

SAVE_DIR = os.path.expanduser("~/hermes-test/vision_screenshots")

def main():
    import cv2  # Import hier, damit ImportError sauber abgefangen wird
    
    debug = "--debug" in sys.argv
    
    # Screenshot machen
    if "--file" in sys.argv:
        idx = sys.argv.index("--file")
        path = sys.argv[idx + 1]
        import cv2
        img = cv2.imread(path)
        if img is None:
            print(f"❌ Kann Bild nicht laden: {path}")
            sys.exit(1)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        print(f"📂 Bild geladen: {path}")
    else:
        print("📸 Nehme Screenshot auf...")
        img = take_screenshot()
        if img is None:
            print("❌ Kein Screenshot möglich")
            sys.exit(1)
        
        # Speichern
        os.makedirs(SAVE_DIR, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        save_path = os.path.join(SAVE_DIR, f"chart_{ts}.png")
        cv2.imwrite(save_path, cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
        print(f"📸 Gespeichert: {save_path}")
    
    h, w = img.shape[:2]
    print(f"📐 Bildgröße: {w}x{h}px")
    
    print("\n" + "=" * 60)
    print("📊 CHART VISION ANALYSE (OpenCV Lokal)")
    print("=" * 60)
    
    # 1. Trend erkennen (Kerzen-Farben)
    print("\n📈 TREND/BIAS:")
    candle_data = detect_price_bars(img)
    print(f"   Bias: {candle_data['bias']}")
    print(f"   Grüne Pixel: {candle_data['green_pct']}% | Rote Pixel: {candle_data['red_pct']}%")
    print(f"   Grün-Ratio: {candle_data['green_ratio']}%")
    print(f"   → {classify_trend(candle_data)}")
    
    # 2. Farben erkennen
    print("\n🎨 FARBEN IM CHART:")
    colors = detect_colors(img)
    for color_name, info in sorted(colors.items(), key=lambda x: -x[1]["pct"]):
        if info["pct"] > 1:
            print(f"   {color_name}: {info['pct']}% ({info['clusters']} Stellen)")
    
    # 3. Horizontale Levels
    print("\n📏 LEVELS:")
    lines = detect_horizontal_lines(img)
    print(f"   {lines['count']} horizontale Linien/Levels erkannt")
    if lines["count"] > 0 and debug:
        print(f"   Y-Positionen: {lines['y_positions'][:10]}...")
    
    # 4. Volumen
    print("\n📊 VOLUMEN:")
    vol = detect_volume_bars(img)
    if vol["volume_present"]:
        print(f"   Volumen erkannt (Bias: {vol['volume_bias']})")
    else:
        print(f"   Kein klares Volumen-Signal")
    
    # 5. Text/Labels
    print("\n🏷️ LABELS/TEXT:")
    text_info = detect_text_regions(img)
    print(f"   ~{text_info['approximate_labels']} Text/Label-Bereiche gefunden")
    
    # 6. Farbige Zonen
    print("\n🔲 FARBIGE ZONEN (FVG/EHPDA/Orderblocks):")
    zones = detect_rectangles(img)
    if zones:
        for name, pct in sorted(zones.items(), key=lambda x: -x[1]):
            print(f"   {name}: ~{pct}% der Chart-Fläche")
    else:
        print(f"   Keine großen farbigen Zonen erkannt")
    
    # 7. Zusammenfassung
    print("\n" + "=" * 60)
    print("📋 ZUSAMMENFASSUNG")
    print("=" * 60)
    
    # Volumen-bestätigter Trend
    if candle_data["bias"] == "bullish" and vol["volume_bias"] == "bullish":
        print("✅ BULLISH: Grüne Kerzen + bullishes Volumen → Aufwärtsdruck bestätigt")
    elif candle_data["bias"] == "bearish" and vol["volume_bias"] == "bearish":
        print("✅ BEARISH: Rote Kerzen + bearishes Volumen → Abwärtsdruck bestätigt")
    elif candle_data["bias"] == "bullish":
        print("⚡ SCHWACH BULLISH: Grüne Kerzen, aber Volumen gemischt")
    elif candle_data["bias"] == "bearish":
        print("⚡ SCHWACH BEARISH: Rote Kerzen, aber Volumen gemischt")
    else:
        print("⚖️ NEUTRAL: Kein klares Signal")
    
    # Wichtige Farben
    key_colors = []
    for c in ["rot (bearish)", "grün (bullish)", "gelb (neutral)", "pink/magenta", "orange"]:
        if c in colors and colors[c]["pct"] > 2:
            key_colors.append(c)
    if key_colors:
        print(f"🎨 Dominante Chart-Farben: {', '.join(key_colors)}")
    
    # Levels
    if lines["count"] > 20:
        print(f"📏 Viele Levels ({lines['count']}) → Dichte Preis-Zonen")
    elif lines["count"] > 10:
        print(f"📏 Moderate Levels ({lines['count']}) → Normale Marktstruktur")
    else:
        print(f"📏 Wenige Levels ({lines['count']}) → Weite Zonen")
    
    if zones:
        zone_names = [f"{n}({p}%)" for n, p in sorted(zones.items(), key=lambda x: -x[1])[:3]]
        print(f"🔲 Aktive Zonen: {', '.join(zone_names)}")
    
    print("\n" + "=" * 60)
    print("HINWEIS: OpenCV erkennt nur Pixel und Farben.")
    print("Für echte Chart-Analyse (FVGs, BOS, CHOCH): Gemini-API-Key besorgen")
    print("  -> GEMINI_API_KEY in ~/.hermes/.env setzen")
    print("  -> Dann: chart_vision_gemini.py (kommt bald)")
    print("=" * 60)

if __name__ == "__main__":
    try:
        import cv2
    except ImportError:
        print("❌ opencv-python nicht installiert.")
        print("   pip install opencv-python pillow numpy")
        sys.exit(1)
    main()
