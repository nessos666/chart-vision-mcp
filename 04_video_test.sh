#!/bin/bash
# Hermes Connection Test Suite - Test 4: Video-Aufnahme-Test
echo "=== Test 4: Video-Aufnahme ==="
echo ""

echo "4.1 ffmpeg Codecs:"
if command -v ffmpeg &>/dev/null; then
    FFVER=$(ffmpeg -version 2>/dev/null | head -1)
    echo "  [OK] ffmpeg: $FFVER"
    
    # Check H.264 encoding
    H264=$(ffmpeg -encoders 2>/dev/null | grep -c "libx264" || echo 0)
    if [ "$H264" -gt 0 ]; then
        echo "  [OK] H.264/libx264 encoder verfügbar"
    else
        echo "  [WARN] libx264 nicht gefunden"
    fi
else
    echo "  [FAIL] ffmpeg nicht installiert"
fi

echo ""
echo "4.2 OBS Studio:"
for cmd in obs obs-studio obs-cli; do
    if command -v "$cmd" &>/dev/null; then
        echo "  [OK] $cmd gefunden"
    fi
done
if ! command -v obs &>/dev/null && ! command -v obs-studio &>/dev/null; then
    echo "  [WARN] OBS nicht installiert (alternativ: ffmpeg + x11grab)"
fi

echo ""
echo "4.3 VNC:"
for cmd in x11vnc vncserver vncviewer; do
    if command -v "$cmd" &>/dev/null; then
        echo "  [OK] $cmd gefunden"
    fi
done
if ! command -v x11vnc &>/dev/null; then
    echo "  [WARN] x11vnc nicht installiert"
fi

echo ""
echo "4.4 Python OpenCV:"
python3 -c "
import cv2
print(f'  [OK] OpenCV {cv2.__version__}')
" 2>/dev/null || echo "  [WARN] OpenCV nicht installiert"

echo ""
echo "4.5 ffmpeg x11grab test (2s):"
ffmpeg -y -f x11grab -video_size 640x480 -i :0.0 -t 2 -c:v libx264 -preset ultrafast /tmp/hermes-test-video.mp4 2>/dev/null
if [ -f /tmp/hermes-test-video.mp4 ]; then
    FILESIZE=$(stat -c%s /tmp/hermes-test-video.mp4 2>/dev/null || echo 0)
    DURATION=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 /tmp/hermes-test-video.mp4 2>/dev/null || echo "?")
    echo "  [OK] 2s Video aufgenommen: ${FILESIZE}B, Dauer: ${DURATION}s"
    rm -f /tmp/hermes-test-video.mp4
else
    echo "  [FAIL] Video-Aufnahme fehlgeschlagen (kein X11 Display?)"
fi

echo ""
echo "=== Test 4 abgeschlossen ==="
