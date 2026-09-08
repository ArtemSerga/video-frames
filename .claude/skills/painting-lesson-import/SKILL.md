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

**Stage bounds are exact YouTube times.** The left link is the first second of the stage, the right link is the second the stage is finished. Adjacent stages share that boundary: the end of N is the start of N+1. Do not round to a "nice" contact-sheet label, and do not start the next stage a minute later.

**The end-of-stage frame is a clean canvas.** No brush, no hand, no palette, no motion blur, no camera cut. The work of that stage is fully on the canvas; the next stage has not started. If the only available second has a brush in it, keep searching the window — do not publish that frame.

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

Timecodes on the frames run **from zero of the window** — add the `-ss` value. **Contact-sheet labels are not exact.** The detector fires on scene change (often the hand entering), then `drawtext` prints that pts. Seeking the same number with `-ss` after `-i` can land on the palette instead of the canvas, or a few seconds earlier while the brush is still down. Lesson 11: the sheet said `00:39:15` (brush on the helix) and `00:40:20` (palette). The clean end of the conch stage was `00:40:08`, found only from a 2-second window.

Pick the **first clean second after the stage is done**, before the next action starts:

- Canvas fills the painted half; hand and brush are out
- The named anatomical / tonal change of this stage is already there
- The next stage's first stroke has not landed yet

Reject and keep looking if any of these are true: brush or finger in frame, palette filling the shot, work still in progress, or the next stage already visible (hair strands over an ear that was meant to stop at the conch, and so on).

### 5. Extraction and repository

Frames live in a public git repository with stable addresses. Notion pulls them by link — no dragging files, and the page is written in a single operation.

```bash
./lesson.sh frame 3 00:31:02 00:40:48 00:51:41
./lesson.sh push 3
```

**Extraction uses `-ss` after `-i` only.** Slow, about 15 seconds a frame, but exact. Any seek before `-i` lands on the nearest keyframe and drifts by seconds: on a lesson where the camera alternates between palette and canvas, three frames out of nine came out as the palette. A double seek does not help either — the coarse jump overshoots and the second `-ss` then counts from the wrong place.

**The filename is the actual timecode of the frame**, not the one planned from the contact sheet. If the frame was taken at 31:01, the file is `00-31-01.jpg`, and the captions and links in Notion are adjusted to match. Never the other way round: a name that lies about its contents surfaces at the first re-check.

**Read the extracted JPEG from disk before committing.** Notion images are not pixels; the contact sheet is not the file you just wrote. If the JPEG shows a brush, a palette, or an unfinished stage — delete it, extract a neighbouring second, read again. Only then `git add` that named file.

**YouTube `t=` is that same second**, as an integer: `00:40:08` → `t=2408s`. Both ends of `from → to` get links. The right-hand `t=` equals the frame filename. The left-hand `t=` equals the previous stage's filename (or `t=0s` for the first stage).

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

### 5.1. Series progression strip

When the user asks for a visual progression of a completed series, build **one horizontal image** in this order:

`reference → final state of lesson 1 → … → final state of the penultimate lesson → finished painting`

The finished painting is the final lesson's state and appears once, at the far right. Do not repeat the reference inside lesson frames.

- Use one clean frame taken after each lesson's work is complete. Prefer a clean frame immediately before the video's end; do not assume the last frame already used on the lesson card shows the whole result.
- For split-screen footage, crop every lesson frame to the canvas half only: `crop=iw/2:ih:iw/2:0`.
- Keep all panels at the maximum common native height. Do not downscale 720 px sources merely because the supplied standalone reference is smaller; align that reference to the strip height.
- Put every panel on the same baseline and use only a **2 px white separator** between neighbours. No wide padding, wrapping, grid, or second row.
- Preserve chronological order numerically; shell glob order puts `10` before `2`.
- Save the stable public artifact at the series root: `painting/SERIES/progression.jpg`.
- Read the final JPEG from disk at full width before publishing. Verify every lesson appears once, the reference is first, the completed painting is last, and there are no hands, brushes, palettes, motion blur, duplicated reference halves, or black gaps.
- Commit and push the image before adding it to Notion.
- Insert it as the first block of the **series page**, followed by a divider:

```markdown
![Reference → steps 1–N−1 → finished painting](https://raw.githubusercontent.com/USER/video-frames/main/painting/SERIES/progression.jpg)
---
```

Fetch the series page afterwards and confirm the image is the first content block. If `progression.jpg` is later overwritten, append or bump `?v=N` in Notion because Notion caches external images.

### 6. Verification against frames

Once images are in hand, re-check the whole text. What usually turns out different:

- Coloured lines may be digital markup over the reference rather than paint
- Whether there is an imprimatura or the canvas is bare
- Stage boundaries shift by minutes — move the YouTube range with them
- What is physically on the canvas at that moment
- A "good enough" frame still has a brush or shows the next stage already underway

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

**A mix number inside a stage block always carries its recipe in brackets** — `Замес: №2 (Burnt Umber 3 : Cadmium Red Hue 1)`. The number alone sends the reader back up to the table, which is exactly what cannot happen with a brush in hand. The table stays as the place where volumes and values live.

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

**`update_content` can take neighbouring blocks with it.** A batch of small, individually correct replacements removed everything that followed the last edited block — a heading, a transcript and three uploaded images. Nothing warns you: the call returns only the page id. So after *every* content edit, fetch the whole page and check the tail, not just the region you touched. Notion-hosted images cannot be restored through the API — `download-attachment` only reads text files this integration uploaded — so recovery means the user opening Page history.

**Never leave the user's own material below your card on the same page.** Pre-existing transcripts, uploads and notes belong on a separate page linked from the card, or the card goes below them. Anything sitting after your last block is in the blast radius of the next edit.

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

Tab indentation. **The frame shows the state at the end of the segment**, not the start — the filename matches the right edge of the range. The left timestamp is the start of this stage (end of the previous block, or `00:00:00`). Ranges on the card must be contiguous; a gap means the bounds were rounded.

Ratio 50/50 for a full frame, 35/65 when the frame is cropped to the canvas.

### Inserting a block between existing ones

The anchor is the opening XML together with the label text — that combination is unique:

```
old_str: <columns>\n\t<column ratio="50">\n\t\t**00:39:12** · ...\n\t</column>
new_str: [new block]\n---\n[same block with a corrected caption]
```

The new block lands before the existing one, and the caption is fixed in the same pass.

### After writing

Fetch the page and confirm: URL intact, timecodes ascending **and contiguous**, each `t=` equal to its `HH:MM:SS` (hours×3600+minutes×60+seconds), captions matching frame filenames, frames linking to a file that was read from disk with a clean canvas, no leftover sections.

---

## Common mistakes

Captioning a frame with the wrong timecode — check the filename against the label **and** against `t=` in seconds.

Publishing a contact-sheet timestamp as the YouTube link without extracting and reading that second. The sheet fires on the hand; the seek may show the palette.

Leaving a brush, hand, or unfinished stroke on an "end of stage" frame. Search the window until the canvas is clear and the stage is done.

Leaving a gap between stages (`… → 00:39:15` then next starts `00:40:08` without updating the previous end). Shared boundary, always.

Typing the video filename from memory. yt-dlp appends its own extension: `lesson.mp4` becomes `lesson.mp4.webm`. Always `ls` first.

Repeating paths in commands. The user is already in the working folder — give commands relative to it, without `cd`.

Extracting a frame with a seek before `-i`. It lands on a keyframe and drifts; on a lesson alternating palette and canvas you get the palette. Only `-ss` after `-i`, however slow.

Trusting a single source. The three differ in accuracy: **the description is most accurate on spelling, the frame on composition, the transcript on order of actions and on what the lists leave out entirely.** On the materials lesson the description listed nine paints while ten sat on the table. No thinner appears in the list or on the table, yet "turps" is named in every mix of step 2. Material lists are incomplete by default.

Downloading Russian subtitles. That is machine translation on top of machine recognition — two errors stacked, and paint and brush names turn to mush. Always `--sub-lang en`.

Quoting the transcript verbatim. Don't.
