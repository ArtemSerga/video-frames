---
name: painting-lesson-import
description: Break a painting video lesson down into a Notion card — transcript, timeline, frames per stage, techniques, prohibitions. Use whenever a Realist Academy lesson, Portrait of Lisa, Portrait of Alex, a YouTube painting or drawing demo, or an uploaded .srt/.vtt file comes up, and for requests like "break down this lesson", "summarise this video", "fill in the lesson card", "process this video", "grab screenshots at these timecodes", "разбери урок", "сделай конспект видео", "заполни карточку урока". Trigger even when Notion is not named explicitly.
---

# Painting lesson to Notion card

Turns an hour-long video into a card you can work from at the easel: order of actions, frames per stage, techniques, prohibitions.

## Two environments

**Claude Code / Cowork — local.** Full network and filesystem access. Run every command directly: download, transcribe, build sheets, extract frames, commit, push. The user only reviews the result.

**Web chat — sandboxed.** No network: downloads return 403. `ffmpeg` is present, `yt-dlp` is not. The user runs every command; give them one at a time, for the folder they are already in. Contact sheets and frames must be uploaded to the chat to be seen.

Everything below applies to both. Only who types the commands changes.

## Hard constraints

**Notion images are not readable.** Pictures inside a page body arrive as signed S3 links with no pixel data. Never analyse from them. Locally, read the frame file from disk; in chat, ask for it to be uploaded.

**Never quote the transcript.** It is copyrighted and useless as-is — half the lines are "right here" and "like that". Paraphrase.

**Never present a guess as an observation.** Mark anything inferred from speech and not confirmed by a frame. Correct it once frames arrive.

**Code and commit messages in English only.** The frames repository is public and sits in the user's profile. Notion cards stay in Russian — those are private notes.

---

## Procedure

### 1. Description and transcript

**Ask for the video description first.** Authors usually list the exact paints, brushes and support there. Speech recognition mangles material names: `Winsor & Newton` becomes "winter and newton", `Belle Arti` becomes "billet arty", `Bravura` becomes "Bravera". These cannot be recovered without the description, and guessing is not allowed.

Then the transcript:

```bash
./lesson.sh get 3 VIDEO_ID
```

The script downloads video, audio and subtitles; if YouTube has none — common for stream recordings, where only `live_chat` is listed — it transcribes the audio with faster-whisper.

> **Check the actual filename.** yt-dlp appends its own extension to whatever `-o` specifies: merging AV1 with Opus yields `lesson.mp4.webm`, not `lesson.mp4`. Always `ls` before the first ffmpeg command.

> **Video ids starting with a hyphen.** The Lisa playlist has one — `-QwEB4eq_qA`. Harmless inside a URL, but taken for a flag on a command line. Put `--` before the URL and verify the file appeared rather than trusting the exit code.

> **Video and audio need different name templates.** If both write to `lesson.%(ext)s`, the audio pass downloads the stream over the already merged video and then deletes the source after extracting mp3 — visible in the log as `Deleting original file`. Video goes to `lesson.%(ext)s`, audio to `audio.%(ext)s`.

### 2. First pass on the transcript

Expand the SRT into readable form:

```bash
python3 -c "
import sys
for b in open(sys.argv[1]).read().strip().split('\n\n'):
    l = b.split('\n')
    if len(l) < 3: continue
    print(f\"[{l[1].split(' --> ')[0][:8]}] {' '.join(l[2:])}\")
" lesson.srt
```

Read it whole. Collect:

- **Timeline** — segments by meaning, not equal slices
- **Key techniques** — mechanics that transfer to other work
- **Anchor alignments** — numbers and anatomical references: size on canvas, unit of measurement, what lines up with what
- **Mixes** — a table of area to composition, whenever mixes are named
- **Tools** — brushes, thinning, medium; translate into the user's own kit
- **What not to do** — prohibitions; in demos these are the most valuable part and are almost always said out loud

### 3. Contact sheets — coarse pass

Contact sheets first, never individual frames. One picture instead of twenty: the whole lesson at a glance, and no need to infer timecodes from speech.

```bash
./lesson.sh sheets 3 0.05 10
```

Threshold 0.03 for line drawing, 0.05 for tonal masses — masses change the image more. Step 10 seconds for a two-hour lesson, 3 for a short one.

Expect 40–80 frames over two hours. Above 120 the detector is catching the hand — raise the threshold. Below 25 — lower it.

> **If `drawtext` is missing** — ffmpeg was built without freetype. On macOS: `brew install ffmpeg-full`. It is keg-only, so also
> `echo 'export PATH="/opt/homebrew/opt/ffmpeg-full/bin:$PATH"' >> ~/.zshrc`
> The plain Homebrew formula has shipped without drawtext since version 9, and reinstalling it does not help.

> **Cropping loses half the information on single-camera lessons.** The script keeps the right half so the static reference does not blur the scene metric. That is right for split-screen lessons. When the camera looks straight down at a table — materials, palette layout — the crop cuts away half the tubes. Check the first sheet.

### 4. Windows — fine pass

Name 8–12 key moments from the sheets. Then **run a window around each one**, because the detector reacts first of all to the hand entering frame, and half the selected frames are blocked by the brush.

A window is continuous, one frame per second, no detection: inside 20–30 seconds there is nothing to filter.

```bash
ffmpeg -i lesson.webm -ss 01:13:20 -t 00:00:30 \
  -vf "fps=1,drawtext=fontfile=/System/Library/Fonts/Helvetica.ttc:\
text='%{pts\:hms}':x=10:y=10:fontsize=30:fontcolor=yellow:box=1:boxcolor=black@0.8,\
scale=480:-1,tile=5x6" -frames:v 1 win.jpg -y
```

Timecodes on the frames run **from zero of the window** — add the `-ss` value.

Pick a frame where the hand is off the canvas: usually the first seconds after a finished stroke, or just before the camera moves in.

### 5. Extraction and repository

Frames live in a public git repository with stable addresses. Notion pulls them by link — no dragging files, and the page is written in a single operation.

```bash
./lesson.sh frame 3 00:31:02 00:40:48 00:51:41
./lesson.sh push 3
```

**Extraction uses `-ss` after `-i` only.** Slow, about 15 seconds a frame, but exact. Any seek before `-i` lands on the nearest keyframe and drifts by seconds: on a lesson where the camera alternates between palette and canvas, three frames out of nine came out as the palette. A double seek does not help either — the coarse jump overshoots and the second `-ss` then counts from the wrong place.

**The filename is the actual timecode of the frame**, not the one planned from the contact sheet. If the frame was taken at 31:01, the file is `00-31-01.jpg`, and the captions and links in Notion are adjusted to match. Never the other way round: a name that lies about its contents surfaces at the first re-check.

Address format:

```
https://raw.githubusercontent.com/USER/video-frames/main/painting/SERIES/N/HH-MM-SS.jpg
```

**Crop to the canvas only when the reference carries no markup.** In lesson 1 the red and blue lines over the photo are half the point — a full frame is needed there. Judge from the contact sheet.

**List files by name** in `git add`, never `git add .` or `*.jpg`: contact sheets, windows, video and audio sit in the same folder.

`.gitignore` is mandatory — video runs to gigabytes:

```
*.mp4
*.webm
*.mkv
*.mp3
*.wav
contact_*.jpg
win*.jpg
.DS_Store
```

**Transcripts are committed.** An `.srt` is a hundred kilobytes, while re-transcribing a two-hour lesson costs fifteen minutes. On a re-run the transcript is read straight from the repository.

**Contact sheets and windows are not.** They cannot be read back from the repository anyway — `web_fetch` returns page text, not pixels — so they can only be looked at by uploading to chat, and re-creating them is one command. Windows are additionally built around a specific moment and will be about the wrong place next time.

### 6. Verification against frames

Once images are in hand, re-check the whole text. What usually turns out different:

- Coloured lines may be digital markup over the reference rather than paint
- Whether there is an imprimatura or the canvas is bare
- Stage boundaries shift by minutes
- What is physically on the canvas at that moment

Make the corrections silently. A "what the frames corrected" section has no place on the page.

### 7. Writing to Notion

Schema and pitfalls below.

---

## Card structure

Only what is needed at the easel. Nothing about the process of breaking the lesson down.

```
Session N · [what governs the layer]

### Frames by stage
The frame shows the state at the end of the segment. Timecodes link to the video.

[two-column blocks: range from → to, stage name, what happened inside it]

### Key techniques
[mechanics, first words in bold]

### Anchor alignments
[numbers and anatomical references]

### Mixes
[table of area to composition, when mixes are named]

## Tools
[brushes, thinning, medium]

## What not to do
[prohibitions]
```

**Must not appear:** conclusions, running time, where the transcript came from, analysis of the user's own mistakes, a separate "order within the step" — it duplicates the frames.

Sequences inside a stage go **as arrows**, not prose:
`ear: top → bottom → tragus → antitragus → helix`

That is what the card exists for.

---

## Conventions

**Brushes:** `shape: softness: size` — `flat: springy: 12`. Softness: stiff, springy, medium, soft.

**Value:** Munsell scale, 0 black, 10 white. Give a target number, not "a bit darker".

**Mixes:** numbered `№1`…`№5`. Ratios explicit (`D 1 : Zinc 2.5`), volumes in ml with strip length for a 4 mm nozzle (1 ml ≈ 8 cm).

**Medium:** always its own line or column, even when the answer is "none" everywhere. Thirteen "none" in a row is a rule, not an empty column.

---

## Notion

### The "Урок" database

`collection://a8db010e-e0a2-442a-acab-50431d41012c`

| Field | Type | Fill with |
|---|---|---|
| Название | title | `Шаг N · Name` |
| Номер | number, float | materials 0, palette 0.5, steps 1–14 |
| userDefined:URL | url | direct link to the video |
| Автор | text | `Realist Academy · Louis Smith` |
| Минут | number | actual duration, not an estimate |
| Статус | select | В очереди / Смотрю / Просмотрено / Пропустить |
| Сюжет | multi_select | Фигура и портрет / Натюрморт / Пейзаж / Прочее |
| Ресурс | relation | the series card |
| Основы | relation | related principles |
| Кадры | file | screenshots |

Video links carry the playlist and index, so the next lesson opens without going back to Notion:

```
https://www.youtube.com/watch?v=VIDEO_ID&list=PLAYLIST_ID&index=N
```

All ids and durations for a series in one command:

```bash
yt-dlp --flat-playlist --print "%(playlist_index)s %(id)s %(duration)s %(title)s" -- "PLAYLIST_URL"
```

### Dangerous operations

**`replace_content` silently wipes the URL property.** Prefer `insert_content` or `update_content`. If used anyway, restore the URL with `update_properties` immediately and verify.

**Batched ALTERs break the schema:** fields vanish, related databases move to trash. One statement at a time, verify in between.

**Colours in `ALTER COLUMN SET SELECT`** are accepted only for options that already exist. Add new ones without a colour.

**`update_content` needs an exact match.** Re-read a page before editing it again. A `~` comes back escaped as `\~`.

**A markdown table becomes a Notion block on write.** Its rows stop being text and `update_content` will not match them. Edit cells only after re-reading the page, against the actual `<td>` markup.

**SQL returns properties only**, not page content. Use `notion-fetch` by id for the body.

### Images by external link

Notion **caches the image on its side** while keeping the external address in the markup. Overwriting a file under the same name has no effect — Notion never learns it changed.

Workaround: append a version to the link. Notion treats it as a new address; GitHub ignores the extra parameter.

```
.../00-07-30.jpg?v=2
```

Then `?v=3`, `?v=4`. Replaced a frame — bump the version.

It follows that **the repository must live permanently and stay public.** `raw.githubusercontent.com` requires a token for private repositories, and Notion will not send one. Path structure is fixed once: renaming a folder breaks images across every card.

### Links to moments in the video

The timecode in a caption is a YouTube link. **Always with the `s`:**

```
https://www.youtube.com/watch?v=ID&t=4410s
```

Without it the player jumps twice: it lands on a nearby marker, then walks to the second.

A range "from → to" is two links. Plain YouTube links have no end parameter; `&end=` works only in embeds, and Notion parses embed addresses its own way.

**Never place a player inside a block.** Notion turns the link into its own viewer, ignores the start time, and every block shows the same thumbnail instead of different frames.

### Navigation between lessons

Every card in a series carries two level-one headings, so the page's table of contents doubles as navigation.

**At the very top, before all content:**
```
# [← Previous lesson name](https://app.notion.com/p/ID)
```

**At the very bottom:**
```
# [Next lesson name →](https://app.notion.com/p/ID)
```

The first lesson only has "next", the last only "back". The arrow always sits outside the text.

H1 specifically — Notion builds its outline from headings, so a jump to the neighbouring lesson is reachable from the table of contents without scrolling.

Links in the form `https://app.notion.com/p/ID`, no dashes. SQL returns the url without `/p/` — add it, or `update_content` will not match later.

**Set navigation up while creating the series cards**, while all the ids are at hand. A separate pass costs a database query and two operations per page.

### Two-column block

```
<columns>
	<column ratio="50">
		[00:07:30](https://www.youtube.com/watch?v=ID&t=450s) → [00:13:00](https://www.youtube.com/watch?v=ID&t=780s)
		**Stage name**
		What happened inside the segment, in order: action → action → action
	</column>
	<column ratio="50">
		![](https://raw.githubusercontent.com/USER/video-frames/main/painting/SERIES/1/00-13-00.jpg)
	</column>
</columns>
---
```

Tab indentation. **The frame shows the state at the end of the segment**, not the start — the filename matches the right edge of the range.

Ratio 50/50 for a full frame, 35/65 when the frame is cropped to the canvas.

### Inserting a block between existing ones

The anchor is the opening XML together with the label text — that combination is unique:

```
old_str: <columns>\n\t<column ratio="50">\n\t\t**00:39:12** · ...\n\t</column>
new_str: [new block]\n---\n[same block with a corrected caption]
```

The new block lands before the existing one, and the caption is fixed in the same pass.

### After writing

Fetch the page and confirm: URL intact, timecodes ascending, captions matching frame filenames, no leftover sections.

---

## Common mistakes

Captioning a frame with the wrong timecode — check the filename against the label.

Typing the video filename from memory. yt-dlp appends its own extension: `lesson.mp4` becomes `lesson.mp4.webm`. Always `ls` first.

Repeating paths in commands. The user is already in the working folder — give commands relative to it, without `cd`.

Extracting a frame with a seek before `-i`. It lands on a keyframe and drifts; on a lesson alternating palette and canvas you get the palette. Only `-ss` after `-i`, however slow.

Trusting a single source. The three differ in accuracy: **the description is most accurate on spelling, the frame on composition, the transcript on order of actions and on what the lists leave out entirely.** On the materials lesson the description listed nine paints while ten sat on the table. No thinner appears in the list or on the table, yet "turps" is named in every mix of step 2. Material lists are incomplete by default.

Downloading Russian subtitles. That is machine translation on top of machine recognition — two errors stacked, and paint and brush names turn to mush. Always `--sub-lang en`.

Quoting the transcript verbatim. Don't.
