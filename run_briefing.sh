#!/bin/bash
# ==============================================================================
# Daily Morning Briefing Runner
# Usage:
#   ./run_briefing.sh              (Generate newspaper + audio file)
#   ./run_briefing.sh --voice      (Generate & listen to audio briefing directly)
#   ./run_briefing.sh --open-html  (Generate & open HTML newspaper in Safari/Chrome)
#   ./run_briefing.sh --print      (Generate & print Markdown paper in terminal)
#   ./run_briefing.sh --play       (Play already generated latest audio file)
# ==============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN="/Library/Frameworks/Python.framework/Versions/3.12/bin/python3"

if [ ! -f "$PYTHON_BIN" ]; then
    PYTHON_BIN="$(command -v python3)"
fi

export PYTHONPATH="$SCRIPT_DIR:$PYTHONPATH"
cd "$SCRIPT_DIR"

if [ "$1" == "--play" ]; then
    AUDIO_FILE="$SCRIPT_DIR/outputs/audio/latest_briefing_ko.mp3"
    if [ ! -f "$AUDIO_FILE" ]; then
        AUDIO_FILE="$SCRIPT_DIR/outputs/audio/latest_briefing_ko.m4a"
    fi
    if [ -f "$AUDIO_FILE" ]; then
        echo "🔊 [Playing latest audio briefing: $AUDIO_FILE]"
        afplay "$AUDIO_FILE"
        exit 0
    else
        echo "No audio briefing found. Generating now..."
    fi
fi

exec "$PYTHON_BIN" "$SCRIPT_DIR/main.py" "$@"
