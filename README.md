# YouTube Podcast Chapterizer & Concept Extractor

Turn long GenAI podcasts into **clean chapters with summaries and concept lists**, plus a neatly formatted **Excel** file with **timestamped hyperlinks** back to YouTube.

## Features
- Pulls the **official YouTube transcript** via `youtube-transcript-api`.
- If a transcript is not available for the video, uses OpenAI Whisper to transcribe the video (if permitted using an env variable)
- Builds **chapters**:
  - Uses **YouTube’s own chapters** when available (via `yt-dlp`).
  - Otherwise falls back to an **LLM (e.g. GPT-4o or as specified in the env file)** to create sensible, sequential chapters.
- For each chapter:
  - Generates a **short summary**.
  - Extracts a **concept list**, each with **one or more timestamps**.
- Exports everything to **Excel (`.xlsx`)**:
  - Chapter title and **start/end** (clickable links to the exact moment).
  - Chapter summary (wrapped).
  - Concepts under each chapter.
  - Each timestamp cell is a **hyperlink** back to the YouTube URL at that second.

## Requirements
- Python 3.9+
- An OpenAI API key
- Packages:
  ```bash
  pip install youtube-transcript-api yt-dlp openai python-dotenv openpyxl
  ```

## Setup
1. **Clone or open this folder** in VS Code (recommended).
2. **Create a virtual environment** (optional but recommended):
   - macOS/Linux:
     ```bash
     python3 -m venv .venv
     source .venv/bin/activate
     ```
   - Windows (PowerShell):
     ```powershell
     python -m venv .venv
     .venv\Scripts\Activate.ps1
     ```
3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   # or
   pip install youtube-transcript-api yt-dlp openai python-dotenv openpyxl
   ```
4. **Add your OpenAI key and preferred model** in a `.env` file at the repo root:
   ```env
   OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxx
   OPENAI_MODEL=gpt-4o
   ```


## Usage
Ensure .env file is created and contains the following:
OPENAI_API_KEY=<your_key>
OPENAI_MODEL=gpt-4o              # gpt-4o-mini
USE_WHISPER=true                 # set to true to enable fallback
WHISPER_MODEL=whisper-1 

Run the main entry point with a YouTube URL. Optionally specify an output Excel path.

```bash
python main.py "https://www.youtube.com/watch?v=YOUR_VIDEO_ID" ./chapters.xlsx
```

On the console you’ll see:
- Whether chapters came from **YouTube (yt-dlp)** or the **LLM**.
- How many chapters were produced.

The Excel file includes:
- One **chapter row** (title, start/end links, source label, summary).
- Followed by **concept rows** under that chapter, with key concepts and what is said in the podcast about each concept.
- Timestamp cells are **clickable** and jump straight to the moment on YouTube.

## Project Structure
```
youtube_analysers/
├─ .env                    # your OpenAI key (not committed)
├─ requirements.txt        # optional: freeze your deps
├─ main.py                 # CLI entry point
├─ transcript_fetcher.py   # pulls YouTube transcript, adds [MM:SS] stamps
├─ transcribe.py           # creates transcript with Whisper if YouTube transcript not available, adds [MM:SS] stamps
├─ chapters.py             # ChapterMaker: official chapters → else LLM; per-chapter summary+concepts
├─ exporter.py             # Excel exporter with timestamp hyperlinks
└─ utils.py                # helpers (ts, chunking, URL parsing)
```

## How It Works
1. **Transcript**: `transcript_fetcher.py` extracts the video ID, fetches the transcript (or generates a new one with transcribe.py **if USE_WHISPER in the .env is set to true**), and produces a single text with `[MM:SS]` stamps.
2. **Chapters**: `chapters.py` tries YouTube’s official chapters first (via `yt-dlp`). If none are available, it asks GPT-4o to create sequential chapters using the transcript timestamps.
3. **Summaries & Concepts**: For each chapter, GPT-4o produces a short summary and a list of concepts/terms with representative timestamps.
4. **Export**: `exporter.py` writes an `.xlsx` with hyperlinks for start/end and each concept mention timestamp.

## Notes & Limits
- If a video has **no transcript** or transcripts are disabled, it will look for the variable USE_WHISPER in the .env file to be true; otherwise generate an error and exit.
- When **official YouTube chapters** exist, they are preferred; otherwise **LLM** chapters are generated.
- Prompts are intentionally simple; tune temperature or instructions if needed.
- Currently only supports OpenAI models; Groq support coming soon.

## Troubleshooting
- **“OPENAI_API_KEY not set”** → Ensure `.env` exists and is loaded (the app uses `python-dotenv`).
- **Transcript errors** → The video may not allow transcripts (try another video).
- **Hyperlinks not clickable** → Open the `.xlsx` in Excel/compatible viewer; links are placed on timestamp cells.

---

**Credits**: Built with `youtube-transcript-api`, `yt-dlp`, `openai`, `python-dotenv`, and `openpyxl`.
