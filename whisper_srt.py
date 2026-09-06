#!/usr/bin/env python3
"""
Transcribe lesson audio to SRT.

Needed for videos without subtitles — YouTube usually generates none
for stream recordings.

Setup:
    pip install -U faster-whisper

Usage:
    python whisper_srt.py lesson.mp3

On Apple Silicon a one-hour lesson takes 5-15 minutes with the small model.
No progress output — the file appears at the end.
vad_filter drops silence, and painting demos have plenty of it.
"""

import sys

from faster_whisper import WhisperModel

MODEL = "small"  # base is faster and rougher, medium is finer and twice as slow


def ts(seconds: float) -> str:
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{int(h):02}:{int(m):02}:{int(s):02},{int((s % 1) * 1000):03}"


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit("usage: python whisper_srt.py audio.mp3")

    path = sys.argv[1]
    model = WhisperModel(MODEL, device="cpu", compute_type="int8")
    segments, _ = model.transcribe(path, language="en", vad_filter=True)

    out = path.rsplit(".", 1)[0] + ".srt"
    with open(out, "w", encoding="utf-8") as f:
        for i, seg in enumerate(segments, 1):
            f.write(f"{i}\n{ts(seg.start)} --> {ts(seg.end)}\n{seg.text.strip()}\n\n")

    print(f"Done: {out}")


if __name__ == "__main__":
    main()
