<p align="center">
  <h1 align="center">Chart Vision MCP</h1>
  <p align="center">
    <strong>Local TradingView chart analysis via OpenCV + Tesseract OCR — no API keys, no GPU, runs fully offline.</strong>
  </p>
  <p align="center">
    <a href="#why">Why</a> · <a href="#how-it-works">How It Works</a> · <a href="#comparison">vs Vision LLMs</a> · <a href="#mcp-integration">MCP Integration</a> · <a href="#hybrid-approach">Hybrid Approach</a> · <a href="#limitations">Limitations</a>
  </p>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.11+-blue?logo=python&logoColor=white" alt="Python 3.11+">
  <img src="https://img.shields.io/badge/license-MIT-green" alt="MIT License">
  <img src="https://img.shields.io/badge/OpenCV-4.x-brightgreen?logo=opencv" alt="OpenCV">
  <img src="https://img.shields.io/badge/status-production_active-success" alt="Production active">
  <img src="https://img.shields.io/github/stars/nessos666/chart-vision-mcp?style=social" alt="Stars">
</p>

---

## Why?

AI agents that analyze TradingView charts typically rely on one of three approaches — each with serious tradeoffs:

| Approach | Cost | Speed | Privacy | Quality |
|----------|------|-------|---------|---------|
| **GPT-4 Vision / Gemini** | $$$ per API call | ~3-10s | Your chart data leaves your machine | High — understands context |
| **Local VLM (LLaVA, Qwen-VL)** | Free (GPU required) | ~5-30s | Fully local | Medium — small models hallucinate |
| **OpenCV + OCR (this project)** | **Free** | **< 1s** | **Fully local** | **Medium — structural, not semantic** |

**Chart Vision MCP occupies a unique niche:** it's the only option that is simultaneously free, instant, and fully offline. It doesn't "understand" charts the way an LLM does — but for structural analysis (candle colors, level lines, zone boundaries, volume) it's often *more reliable* than a vision LLM that might hallucinate price levels.

---

## How It Works

```
┌─────────────────┐     screenshot     ┌──────────────────────┐
│   Screen / TV   │  ───────────────►  │  OpenCV Analysis     │
│                 │                    │                      │
└─────────────────┘                    │  Step 1: Grab screen │
                                       │  Step 2: Color mask  │
┌─────────────────┐                    │  Step 3: Hough lines │
│   Tesseract OCR │  ◄───────────────  │  Step 4: Contours    │
│                 │    image regions   │  Step 5: OCR crop    │
└─────────────────┘                    │                      │
                                       └──────────┬───────────┘
                                                  │ JSON result
                                                  ▼
                                       ┌──────────────────────┐
                                       │  MCP Response        │
                                       │  {                   │
                                       │    candle_bias,      │
                                       │    levels: [...]     │
                                       │    zones: [...],     │
                                       │    labels: [...],    │
                                       │    volume_rel,       │
                                       │    trend             │
                                       │  }                   │
                                       └──────────────────────┘
```

### What it detects — step by step

| Step | Method | What it finds | Why it matters |
|------|--------|---------------|----------------|
| **1. Candle colors** | HSV color masking | Green/red pixel ratio per region | Bullish vs bearish bias for the visible period |
| **2. Level lines** | Probabilistic Hough Transform | Horizontal lines matching known colors | Support/resistance levels drawn on the chart |
| **3. Zones** | Contour analysis on color masks | Filled rectangles (FVG zones, order blocks) | Key areas where price might react |
| **4. Volume** | Bar height measurement | Relative volume comparison across visible bars | Confirms whether moves have conviction |
| **5. OCR** | Tesseract + preprocessing | Price labels, indicator values, annotations | Extracts actual numbers from the image |
| **6. Trend** | Price position algorithm | Up / Down / Sideways classification | Overall market direction from the visible range |

### Example output

```json
{
  "candle_bias": "bullish",
  "green_pct": 58.3,
  "red_pct": 41.7,
  "levels": [
    {"price": 19250, "color": "red", "type": "horizontal"},
    {"price": 19300, "color": "blue", "type": "horizontal"}
  ],
  "zones": [
    {"color": "yellow", "bounds": {"x1": 100, "y1": 200, "x2": 300, "y2": 250}}
  ],
  "labels": ["19250.00", "19300.00", "RSI: 62.4"],
  "volume_rel": "increasing",
  "trend": "up"
}
```

---

## Comparison: OpenCV vs Vision LLMs

Vision LLMs are getting better at reading charts, but they have fundamental weaknesses that OpenCV doesn't:

### Where OpenCV wins

| Scenario | OpenCV | Vision LLM |
|----------|--------|------------|
| **Color accuracy** | Exact HSV matching | May confuse similar colors |
| **Line position** | Pixel-exact coordinates | Approximate spatial reasoning |
| **Consistency** | Deterministic — same input, same output | Stochastic — different analysis each time |
| **Speed** | < 1 second | 3-30 seconds |
| **Cost** | $0 | $0.01-$0.10 per call |
| **Offline** | Yes | No (cloud models) |

### Where Vision LLMs win

| Scenario | OpenCV | Vision LLM |
|----------|--------|------------|
| **Chart patterns** | Can't detect head-and-shoulders | Can reason about patterns |
| **Context understanding** | "Many green candles = bullish" | "This looks like a breakout from consolidation" |
| **Complex indicators** | Can only see colored lines | Can read indicator values and interpret |
| **Ambiguity** | Fails on unclear visuals | Makes educated guesses |

### The best of both worlds

Use Chart Vision MCP for the **structural analysis** (what colors, lines, and zones are on screen), and feed those results into an LLM for **semantic interpretation**. This gives you both speed (structural data is instant) and understanding (LLM reasons about the structured data).

---

## MCP Integration

This project is a **Model Context Protocol (MCP)** server, which means it integrates natively with AI agents like Hermes, Claude Code, or any MCP-compatible host.

### Register in your MCP config

```json
{
  "mcpServers": {
    "chart-vision": {
      "command": "python3",
      "args": ["/path/to/chart_vision_mcp_server.py"],
      "env": {}
    }
  }
}
```

### Available tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `chart_vision_analyze` | Screenshot + full analysis (OpenCV + OCR) | `region`: "full" or "chart" |
| `chart_vision_screenshot` | Screenshot only, no analysis | (none) |

Both tools work without any API key or internet connection.

---

## Hybrid Approach (Recommended)

Chart Vision MCP is **most powerful when combined with real TradingView data**. The vision layer gives you visual structure; the TV data layer gives you exact numeric values:

```
1. mcp_tv_chart_get_state          → what symbol, timeframe, indicators
2. mcp_tv_data_get_ohlcv           → last 20 bars (exact prices)
3. mcp_tv_data_get_pine_lines      → exact horizontal level prices
4. mcp_tv_data_get_pine_labels     → FVG / Order Block zones (exact boundaries)
5. mcp_tv_data_get_study_values    → RSI, MACD, Bollinger Bands (exact values)
6. mcp_chart_vision_analyze        → visual structure (colors, candle bias)
```

The TV MCP tools give you **ground truth** (exact prices, indicator values). Chart Vision gives you the **visual gestalt** (is it bullish or bearish-looking?). Together they're stronger than either alone.

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

## Files

| File | Purpose | Lines |
|------|---------|-------|
| `chart_vision.py` | Standalone OpenCV analysis | 458 |
| `chart_vision_mcp_server.py` | MCP server (v2.0, stdio JSON-RPC) | 258 |
| `chart_vision_gemini.py` | Gemini Vision integration (optional, requires API key) | ~150 |

---

## Limitations

**This is not an ML model.** It doesn't "understand" charts the way a human or LLM does. It provides a deterministic, color-based structural analysis of what's visible on screen. It will not:

- Detect complex patterns (head-and-shoulders, wedges, triangles)
- Interpret candlestick patterns (doji, engulfing, harami)
- Read every indicator value reliably (OCR accuracy depends on font size and contrast)
- Understand market context or news

Use it for what it's good at: **fast, reliable, zero-cost structural chart analysis** that never hallucinates a price level.

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

## Related

- [nq-strategy-builder](https://github.com/nessos666/nq-strategy-builder) — Full NQ futures backtesting framework
- [tv-watch-agent](https://github.com/nessos666/tv-watch-agent) — CDP-based TradingView automation
- [tv-mcp-server](https://github.com/nessos666/tv-watch-agent) — TradingView MCP server (68 tools) — use alongside Chart Vision for the hybrid approach

---

## License

MIT — free to use, modify, and integrate.

<p align="center">
  <small>Built for local, offline, zero-cost TradingView chart analysis.<br>
  The only chart vision MCP server that works without internet.<br>
  <strong>github.com/nessos666</strong></small>
</p>
