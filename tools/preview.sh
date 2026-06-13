#!/usr/bin/env bash
# Render a Manim scene and (re)load it into a single persistent mpv window.
#
# The whole point: keep ONE mpv window open and reload it on every render, so the
# edit -> render -> see loop has no window-spawn churn. Works for both .mp4
# animations and -s still frames (mpv shows images too).
#
# Usage:
#   tools/preview.sh <file> <Scene> [mode]
#   mode = video (default) | frame | final
#
#   video  -ql  full draft animation        (default working mode)
#   frame  -ql -s  last frame only           (fast layout tuning)
#   final  -qh  high-quality animation       (renders for real)
#
# Driven by nvim/helios.lua, but usable standalone.
set -euo pipefail

FILE="${1:?usage: preview.sh <file> <Scene> [video|frame|final]}"
SCENE="${2:?missing Scene name}"
MODE="${3:-video}"

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
SOCK="${TMPDIR:-/tmp}/helios-mpv.sock"

case "$MODE" in
  video) FLAGS=(-ql) ;;
  frame) FLAGS=(-ql -s) ;;
  final) FLAGS=(-qh) ;;
  *) echo "unknown mode: $MODE (want video|frame|final)" >&2; exit 2 ;;
esac

echo ">> rendering $SCENE ($MODE)…"
uv run manim render "${FLAGS[@]}" --media_dir "$ROOT/media" "$FILE" "$SCENE"

# Locate the newest matching artifact manim just produced.
if [[ "$MODE" == "frame" ]]; then
  OUT="$(ls -t media/images/*/"$SCENE"*.png 2>/dev/null | head -1 || true)"
else
  OUT="$(ls -t media/videos/*/*/"$SCENE".mp4 2>/dev/null | head -1 || true)"
fi

if [[ -z "${OUT:-}" ]]; then
  echo "!! could not find render output for $SCENE" >&2
  exit 1
fi
OUT="$ROOT/$OUT"
echo ">> output: $OUT"

# Try to reload an already-running mpv via its IPC socket; else launch one.
reload_mpv() {
  python3 - "$SOCK" "$1" <<'PY'
import json, socket, sys
sock_path, media = sys.argv[1], sys.argv[2]
try:
    s = socket.socket(socket.AF_UNIX)
    s.connect(sock_path)
    s.sendall((json.dumps({"command": ["loadfile", media]}) + "\n").encode())
    s.close()
except OSError:
    sys.exit(1)
PY
}

if reload_mpv "$OUT" 2>/dev/null; then
  echo ">> reloaded existing mpv window"
else
  echo ">> launching mpv"
  # Window placement/behaviour — override via env if you like:
  #   HELIOS_MPV_GEOMETRY  mpv --geometry (default: 40% wide, pinned top-right)
  #   HELIOS_MPV_ONTOP     yes|no  (default yes — floats over Neovim)
  GEOMETRY="${HELIOS_MPV_GEOMETRY:-40%-20+40}"
  ONTOP="${HELIOS_MPV_ONTOP:-yes}"
  # nohup + & + disown fully detaches mpv so it survives the render job exiting.
  nohup mpv \
      --no-terminal --really-quiet \
      --loop-file=inf \
      --image-display-duration=inf \
      --keep-open=yes \
      --geometry="$GEOMETRY" \
      --ontop="$ONTOP" \
      --no-border \
      --osd-level=1 \
      --title="helios ▸ preview" \
      --input-ipc-server="$SOCK" \
      "$OUT" >/dev/null 2>&1 &
  disown
fi
