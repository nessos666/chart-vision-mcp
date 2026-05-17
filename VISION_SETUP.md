# Chart Vision — Setup & Status
==============================

## Status

| Feature | Status | Latenz |
|---------|--------|--------|
| Screenshot | ✅ OK | < 1s |
| OpenCV Analyse (Farben, Kerzen-Bias, Level-Linien, Zonen) | ✅ OK | < 1s |
| Tesseract OCR (Preise, Labels) | ✅ OK | < 2s |
| Gemini KI Vision | ❌ Deaktiviert (Key ungültig) | — |
| Lokales Vision-Modell (Qwen3.5) | ❌ Zu langsam auf CPU ohne GPU | — |

## Tools

### `mcp_chart_vision_chart_vision_analyze`
Screenshot + OpenCV (Kerzen-Bias, Farben, Level-Linien, Zonen) + OCR (Preise)
→ Kein API-Key, keine GPU, sofort einsatzbereit

### `mcp_chart_vision_chart_vision_screenshot`
Nur Screenshot speichern

## Dateien

| Datei | Zweck |
|-------|-------|
| `chart_vision_mcp_server.py` | MCP-Server (v2.0, OpenCV + OCR) |
| `chart_vision.py` | OpenCV Analyse (Standalone) |
| `chart_vision_gemini.py` | Gemini Analyse (deaktiviert, kein Key) |
| `VISION_SETUP.md` | Alte Doku (veraltet) |

## Verwendung in Hermes

```
mcp_chart_vision_chart_vision_analyze    -> Screenshot + OpenCV + OCR
mcp_chart_vision_chart_vision_screenshot -> Nur Screenshot
```

Für echte Chart-Daten (Levels, FVGs, Indikatoren) zusätzlich:
```
mcp_tv_data_get_ohlcv            -> OHLCV Bars
mcp_tv_data_get_pine_lines       -> Exakte Level-Preise
mcp_tv_data_get_pine_labels      -> FVG / Orderblock Labels
mcp_tv_data_get_study_values     -> RSI, MACD, etc.
mcp_tv_capture_screenshot        -> TV Screenshot (besser als Bildschirm-Screenshot)
mcp_tv_chart_get_state           -> Symbol, Timeframe, Indikatoren
```

## Hybrid-Analyse (empfohlen)
Kombiniere TV MCP Daten + Vision Screenshot:
1. `mcp_tv_chart_get_state` — was ist offen
2. `mcp_tv_data_get_ohlcv` — letzte 20 Bars
3. `mcp_tv_data_get_pine_lines` — Level
4. `mcp_tv_data_get_pine_labels` — Markierungen
5. `mcp_tv_data_get_study_values` — Indikatoren
6. `mcp_chart_vision_chart_vision_analyze` — Visueller Eindruck
