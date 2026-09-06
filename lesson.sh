#!/usr/bin/env bash
# Painting lesson breakdown helper. Run from the repository root.
#
#   ./lesson.sh get    3 91Lj6bPCqzQ      download video, audio, transcript
#   ./lesson.sh sheets 3 [thresh] [step]  build contact sheets
#   ./lesson.sh frame  3 00:31:02 ...     extract frames at given timecodes
#   ./lesson.sh push   3                  commit frames only
#   ./lesson.sh ls     3                  list lesson folder
#
# Threshold: 0.03 for line drawing, 0.05 for tonal masses. Default 0.03.
# Step:      10 seconds for a two-hour lesson, 3 for a short one. Default 10.

set -e

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERIES="painting/oil-portrait-lisa"
FONT="/System/Library/Fonts/Helvetica.ttc"

CMD="${1:?usage: get | sheets | frame | push | ls}"
NUM="${2:?lesson number required}"
DIR="$ROOT/$SERIES/$NUM"

# locate the video file whatever its extension
find_video() {
  find "$DIR" -maxdepth 1 -type f \( -name '*.webm' -o -name '*.mp4' -o -name '*.mkv' \) \
    | head -1
}

case "$CMD" in

get)
  ID="${3:?youtube video id required}"
  URL="https://www.youtube.com/watch?v=$ID"
  mkdir -p "$DIR"

  echo "Video..."
  yt-dlp -f "bv*[height<=720]+ba" --no-playlist -o "$DIR/lesson.%(ext)s" "$URL"

  echo "Audio..."
  yt-dlp -f bestaudio -x --audio-format mp3 --no-playlist -o "$DIR/lesson.%(ext)s" "$URL"

  echo "Subtitles, if any..."
  yt-dlp --write-auto-subs --sub-lang en --convert-subs srt \
         --skip-download --no-playlist -o "$DIR/lesson" "$URL" || true

  if [ ! -f "$DIR/lesson.en.srt" ]; then
    echo "No subtitles, transcribing audio"
    python "$ROOT/whisper_srt.py" "$DIR/lesson.mp3"
  fi

  ls -la "$DIR"
  ;;

sheets)
  VIDEO="$(find_video)"
  [ -z "$VIDEO" ] && { echo "No video in $DIR"; exit 1; }

  THRESHOLD="${3:-0.03}"
  STEP="${4:-10}"
  rm -f "$DIR"/contact_*.jpg

  echo "Detecting canvas changes: threshold $THRESHOLD, step ${STEP}s"

  # crop   right half only: the static reference would blur the scene metric
  # fps    thin out first, so frames compared are STEP seconds apart, not adjacent
  # select keep visibly changed frames
  # tile   straight into a grid, no intermediate files
  ffmpeg -hide_banner -loglevel error -i "$VIDEO" -vf \
"crop=iw/2:ih:iw/2:0,\
fps=1/${STEP},\
select='gt(scene,${THRESHOLD})',\
drawtext=fontfile=${FONT}:text='%{pts\\:hms}':x=10:y=10:fontsize=30:fontcolor=yellow:box=1:boxcolor=black@0.8,\
scale=480:-1,\
tile=4x6" \
    -fps_mode vfr -q:v 3 "$DIR/contact_%02d.jpg" -y

  N=$(ls "$DIR"/contact_*.jpg 2>/dev/null | wc -l | tr -d ' ')
  [ "$N" -eq 0 ] && { echo "No sheets. Lower the threshold"; exit 1; }
  echo "Sheets: $N  ->  $DIR"
  ;;

frame)
  VIDEO="$(find_video)"
  [ -z "$VIDEO" ] && { echo "No video in $DIR"; exit 1; }
  shift 2
  [ $# -eq 0 ] && { echo "Give timecodes: 00:31:02 00:40:48"; exit 1; }

  for T in "$@"; do
    OUT="$DIR/${T//:/-}.jpg"
    echo "$T ..."
    # -ss after -i: slow but exact. Seeking before -i lands on a keyframe and drifts
    ffmpeg -hide_banner -loglevel error \
      -i "$VIDEO" -ss "$T" -frames:v 1 -update 1 -q:v 2 "$OUT" -y
  done

  ls -la "$DIR"/[0-9][0-9]-[0-9][0-9]-[0-9][0-9].jpg
  ;;

push)
  cd "$ROOT"
  FRAMES=$(ls "$SERIES/$NUM"/[0-9][0-9]-[0-9][0-9]-[0-9][0-9].jpg 2>/dev/null || true)
  SUBS=$(ls "$SERIES/$NUM"/*.srt 2>/dev/null || true)
  [ -z "$FRAMES$SUBS" ] && { echo "Nothing to commit in $DIR"; exit 1; }

  git add $FRAMES $SUBS
  git status --short
  echo
  read -p "Commit? [y/N] " OK
  [ "$OK" = "y" ] || { echo "Cancelled"; exit 0; }

  git commit -m "lesson $NUM frames and transcript"
  git push
  ;;

ls)
  ls -la "$DIR"
  ;;

*)
  echo "Unknown command: $CMD"
  echo "usage: get | sheets | frame | push | ls"
  exit 1
  ;;

esac