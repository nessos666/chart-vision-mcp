<p align="center">
  <h1 align="center">Chart Vision MCP</h1>
  <p align="center">
    <strong>Local TradingView chart analysis via OpenCV + Tesseract OCR — no API keys, no GPU, runs fully offline.</strong>
  </p>
  <p align="center">
    <a href="#quick-start">Quick Start</a> · <a href="#tools">MCP Tools</a> · <a href="#how-it-works">How It Works</a> · <a href="#limitations">Limitations</a>
  </p>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.11+-blue?logo=python&logoColor=white" alt="Python 3.11+">
  <img src="https://img.shields.io/badge/license-MIT-green" alt="MIT License">
  <img src="https://img.shields.io/badge/OpenCV-4.x-brightgreen?logo=opencv" alt="OpenCV">
  <img src="https://img.shields.io/badge/status-production_active-success" alt="Production active">
</p>

---

## Why?

AI agents that analyze TradingView charts usually need one of:
- **API keys** (GPT-4 Vision, Gemini) — costs money, privacy concerns
- **GPU models** (LLaVA, Qwen-VL) — expensive hardware
- **Cloud services** — latency, rate limits, data leaves your machine

**Chart Vision MCP solves this differently.** It uses classical computer vision (OpenCV) and OCR (Tesseract) to extract:
- Price bar structure (green/red candle bias)
- Colored level lines and zones
- Volume bars
- Labels and text via OCR
- Trend direction and range

All locally, all offline, all free.

---

## Quick Start

```bash
git clone https://github.com/nessos666/chart-vision-mcp.git
cd chart-vision-mcp
pip install opencv-python pillow numpy pytesseract
sudo apt install tesseract-ocr   # Linux

# Run standalone analysis
python chart_vision.py --debug

# Or use the MCP server
python chart_vision_mcp_server.py
```

---

## MCP Tools

| Tool | Description |
|------|-------------|
| `chart_vision_analyze` | Screenshot → OpenCV analysis (colors, candle bias, levels) + OCR (prices, labels) |
| `chart_vision_screenshot` | Capture screenshot only (no analysis) |

Both tools work without any API key or internet connection.

---

## How It Works

```
┌─────────────────┐     screenshot     ┌──────────────────────┐
│   Screen / TV   │  ───────────────►  │  OpenCV Analysis     │
│                 │                    │                      │
└─────────────────┘                    │  • Color detection   │
                                       │  • Candle bias       │
┌─────────────────┐                    │  • Level lines       │
│   Tesseract OCR │  ◄───────────────  │  • Zone boundaries   │
│                 │    image regions   │  • Volume bars       │
└─────────────────┘                    │                      │
                                       └──────────┬───────────┘
                                                  │ JSON result
                                                  ▼
                                       ┌──────────────────────┐
                                       │  MCP Response        │
                                       │  { bias, levels,     │
                                       │    colors, trend }   │
                                       └──────────────────────┘
```

### What it detects

| Feature | Method | Detail |
|---------|--------|--------|
| **Candle colors** | OpenCV color masking | Green vs red ratio → bullish/bearish bias |
| **Level lines** | Hough line detection | Horizontal colored lines → support/resistance |
| **Zones** | Contour analysis | Filled rectangles → order blocks / FVG zones |
| **Text labels** | Tesseract OCR | Price labels, indicator values, annotations |
| **Volume** | Bar height analysis | Relative volume comparison |
| **Trend** | Price position analysis | Up/down/sideways classification |

---

## Files

| File | Purpose |
|------|---------|
| `chart_vision.py` | Standalone OpenCV analysis (458 lines) |
| `chart_vision_mcp_server.py` | MCP server (v2.0, stdio JSON-RPC) |
| `chart_vision_gemini.py` | Gemini Vision integration (requires API key — optional) |

---

## Limitations

**This is not an ML model.** It doesn't "understand" charts the way a human or LLM does. It provides a structural, color-based analysis of what's visible on screen.

Best used **in combination with real TradingView data** (OHLCV bars, indicator values, Pine Script levels) for a complete picture:

```python
# Recommended hybrid approach:
# 1. TV MCP: mcp_tv_data_get_ohlcv → real bar data
# 2. TV MCP: mcp_tv_data_get_pine_lines → exact level prices
# 3. TV MCP: mcp_tv_data_get_study_values → RSI, MACD, etc.
# 4. Chart Vision: chart_vision_analyze → visual structure
```

---

## Requirements

```text
opencv-python>=4.8
pillow>=10.0
numpy>=1.26
pytesseract>=0.3
```

Plus system package: `tesseract-ocr`

---

## Testing

```bash
# Syntax check
python3 -m py_compile chart_vision.py
python3 -m py_compile chart_vision_mcp_server.py

# Run with debug (shows intermediate steps)
python chart_vision.py --debug
```

---

## License

MIT — free to use, modify, and integrate.

<p align="center">
  <small>Built for local, offline, zero-cost TradingView chart analysis.<br>
  <strong>github.com/nessos666</strong></small>
</p>
