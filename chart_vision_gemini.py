#!/usr/bin/env python3
"""
Hermes Chart Vision GEMINI — TradingView Screenshot Analyse via Gemini API
==============================================================================

WIE MAN EINEN KOSTENLOSEN GEMINI API-KEY BEKOMMT:
1. Gehe zu https://aistudio.google.com/apikey
2. Mit Google-Konto anmelden
3. "Create API Key" klicken
4. Key kopieren und in ~/.hermes/.env einfügen:
     GEMINI_API_KEY=dein_key_hier
5. Fertig — Gemini 3 Flash ist KOSTENLOS (1.500 Requests/Tag)

Oder via terminal:
  echo 'GEMINI_API_KEY=dein_key_hier' >> ~/.hermes/.env

Nutzung:
  python3 chart_vision_gemini.py                          # Screenshot + Analyse
  python3 chart_vision_gemini.py --prompt "Beschreibe die FVGs"
  python3 chart_vision_gemini.py --file pfad/zum/bild.png
  python3 chart_vision_gemini.py --screenshot-only
"""

import os
import sys
import base64
import json
import subprocess
import tempfile
from datetime import datetime

from _logging import logger

# ---------------------------------------------------------------------------
# Konfiguration
# ---------------------------------------------------------------------------

GEMINI_MODEL = "gemini-3-flash"
SCREENSHOT_DIR = os.path.expanduser("~/hermes-test/vision_screenshots")

ANALYSE_PROMPT = """
Du bist ein professioneller ICT-/SMC-Trader und Chart-Analyst.
Analysiere diesen TradingView NQ Futures Chart GENAU.

Beschreibe:

1. WELCHE INDIKATOREN siehst du? (Linien, Zonen, Labels)
2. WELCHE FARBEN haben die Linien?
3. WELCHE LABELS/TEXTE sind sichtbar? (PDH, PDL, Settlement, EHPDA, Asia H/L, London H/L, NDOG)
4. WELCHE MARKTSTRUKTUR: Trendrichtung, BOS, CHOCH, FVGs, Sweeps, Orderblocks
5. WO STEHT DER PREIS relativ zu den Levels?
6. WELCHES IST DAS WICHTIGSTE LEVEL?
7. GIBT ES DIVERGENZEN?
8. WAS FÄLLT DIR AUF? (Liquidity, Manipulation, Reaktionen)
"""

# ---------------------------------------------------------------------------
# Screenshot
# ---------------------------------------------------------------------------

def take_screenshot():
    """Macht Screenshot via Pillow."""
    try:
        from PIL import ImageGrab
        import PIL.Image
        import io
        img = ImageGrab.grab()
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()
    except Exception as e:
        logger.warning("Pillow fehlgeschlagen: %s", e)
    
    # Fallback ffmpeg
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
    except Exception as e:
        logger.warning("ffmpeg fehlgeschlagen: %s", e)
    return None

def save_screenshot(data):
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(SCREENSHOT_DIR, f"chart_gemini_{ts}.png")
    with open(path, "wb") as f:
        f.write(data)
    logger.info("Screenshot gespeichert: %s", path)
    return path

# ---------------------------------------------------------------------------
# Gemini
# ---------------------------------------------------------------------------

def get_api_key():
    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if key:
        return key
    
    env_path = os.path.expanduser("~/.hermes/.env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line.startswith("GEMINI_API_KEY="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
                if line.startswith("GOOGLE_API_KEY="):
                    v = line.split("=", 1)[1].strip().strip('"').strip("'")
                    if v and v != "your_g...here":
                        return v
    return None

def analyze(image_data, prompt):
    try:
        from google import genai
        from google.genai import types
    except ImportError:
        logger.error("google-genai nicht installiert. pip install google-genai")
        sys.exit(1)
    
    key = get_api_key()
    if not key:
        logger.error("KEIN GEMINI_API_KEY. Key holen: https://aistudio.google.com/apikey")
        sys.exit(1)
    
    logger.info("Analysiere mit %s...", GEMINI_MODEL)
    try:
        client = genai.Client(api_key=key)
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=[prompt, types.Part.from_bytes(data=data, mime_type="image/png")]
        )
        return response.text
    except Exception as e:
        logger.error("Gemini API Fehler: %s", e)
        return f"FEHLER: {e}"

# ---------------------------------------------------------------------------

def main():
    if "--file" in sys.argv:
        idx = sys.argv.index("--file")
        path = sys.argv[idx + 1]
        with open(path, "rb") as f:
            data = f.read()
        logger.info("Bild geladen: %s", path)
    else:
        data = take_screenshot()
        if not data:
            logger.error("Kein Screenshot möglich")
            sys.exit(1)
        save_screenshot(data)
    
    if "--screenshot-only" in sys.argv:
        return
    
    prompt = ANALYSE_PROMPT
    if "--prompt" in sys.argv:
        idx = sys.argv.index("--prompt")
        prompt = sys.argv[idx + 1]
    
    result = analyze(data, prompt)
    
    print("\n" + "=" * 60)
    print("GEMINI CHART VISION ANALYSE")
    print("=" * 60)
    print(result)
    print("=" * 60)

if __name__ == "__main__":
    main()
