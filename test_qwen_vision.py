#!/usr/bin/env python3
"""Test Qwen3.5:0.8b Vision mit gezieltem Prompt"""
import requests, json, base64, sys, time
from _logging import logger

screenshot = sys.argv[1] if len(sys.argv) > 1 else "vision_screenshots/chart_20260515_235128.png"

with open(screenshot, "rb") as f:
    b64 = base64.b64encode(f.read()).decode("utf-8")

prompt = """Describe this NQ futures chart in 3-5 sentences.
What is the trend direction? What key support/resistance levels do you see?
Is the market bullish or bearish right now?"""

payload = {
    "model": "qwen3.5:0.8b",
    "messages": [
        {
            "role": "user",
            "content": prompt,
            "images": [b64]
        }
    ],
    "stream": False,
    "options": {"temperature": 0.1, "num_predict": 256}
}

t0 = time.time()
resp = requests.post("http://localhost:11434/api/chat", json=payload, timeout=300)
t1 = time.time()

data = resp.json()
elapsed = round(t1 - t0)

print(f"⚡ {elapsed}s | Modell: qwen3.5:0.8b")
print()
if "message" in data:
    content = data["message"].get("content", "")
    print(content if content else "(LEER)")
elif "error" in data:
    print(f"FEHLER: {data['error']}")
else:
    print(json.dumps(data, indent=2)[:300])

# Token stats
if "eval_count" in data:
    print(f"\n--- Tokens: {data.get('eval_count')} generated, {data.get('eval_duration',0)//1e9}s inference")
