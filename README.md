# YouTube Podcast Chapterizer & Concept Extractor

Turn long GenAI podcasts into **clean chapters with summaries and concept lists**, plus a neatly formatted **Excel** file with **timestamped hyperlinks** back to YouTube.

## Features
- Pulls the **official YouTube transcript** via `youtube-transcript-api`.
- If a transcript is not available for the video, uses OpenAI Whisper to transcribe the video (if permitted using an env variable)
- Builds **chapters**:
  - Uses **YouTube's own chapters** when available (via `yt-dlp`).
  - Otherwise falls back to an **LLM (e.g. GPT-4o or as specified in the env file)** to create sensible, sequential chapters.
- For each chapter:
  - Generates a **short summary**.
  - Extracts a **concept list**, each with **one or more timestamps**.
- Exports everything to **Excel (`.xlsx`)**:
  - Chapter title and **start/end** (clickable links to the exact moment).
  - Chapter summary (wrapped).
  - Concepts under each chapter.
  - Each timestamp cell is a **hyperlink** back to the YouTube URL at that second.
- **REST API** for processing videos programmatically

## Requirements
- Python 3.13 (as specified in `.python-version`)
- [uv](https://github.com/astral-sh/uv) - Python package and environment manager
- An OpenAI API key

## Setup

### Option 1: Docker (Recommended)

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd youtube-podcast-analyser
   ```

2. **Configure environment variables**:
   Copy the example environment file and configure it:
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` with your API keys:
   ```env
   # Required: Your OpenAI API key
   OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxx
   
   # Optional: Specify the OpenAI model (default: gpt-4o)
   OPENAI_MODEL=gpt-4o
   
   # Optional: Set to 'true' to allow Whisper transcription if no transcript is available
   WHISPER_TRANSCRIPTION=false
   
   # Optional: Whisper model to use (if WHISPER_TRANSCRIPTION is true)
   WHISPER_MODEL=whisper-1

   # If you want to use Groq instead of OpenAI then set:
   USE_GROQ=false           # set to true to enable groq instead of OpenAI

   # If you have set USE_GROQ to true, then set your Groq API key:
   GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxx

   # Optional: Specify the Groq model to use: (default: meta-llama/llama-4-scout-17b-16e-instruct)
   GROQ_CHAT_MODEL=meta-llama/llama-4-scout-17b-16e-instruct
   ```

3. **Run with Docker Compose**:
   ```bash
   docker-compose up -d
   ```

4. **Access the application**:
   - Frontend (Streamlit): http://localhost:8501
   - Backend API: http://localhost:12345
   - API Documentation: http://localhost:12345/docs

5. **Stop the application**:
   ```bash
   docker-compose down
   ```

### Option 2: Local Development

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd youtube-podcast-analyser
   ```

2. **Install uv** (if not already installed):
   ```bash
   curl -sSf https://astral.sh/uv/install.sh | sh
   ```
   linux: `sudo snap install astral-uv --classic`

3. **Configure environment variables**:
   Create a `.env` file in the project root with the following content:
   ```env
   # Required: Your OpenAI API key
   OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxx
   
   # Optional: Specify the OpenAI model (default: gpt-4o)
   OPENAI_MODEL=gpt-4o
   
   # Optional: Set to 'true' to allow Whisper transcription if no transcript is available
   WHISPER_TRANSCRIPTION=false
   
   # Optional: Whisper model to use (if WHISPER_TRANSCRIPTION is true)
   WHISPER_MODEL=whisper-1

   # If you want to use Groq instead of OpenAI then set:
   USE_GROQ=true           # set to true to enable groq instead of OpenAI

   # If you have set USE_GROQ to true, then set your Groq API key:
   GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxx

   # Optional: Specify the Groq model to use: (default: meta-llama/llama-4-scout-17b-16e-instruct)
   GROQ_CHAT_MODEL=meta-llama/llama-4-scout-17b-16e-instruct
   ```

4. Run the application using uv:
   ```bash
   uv run uvicorn app:app --reload --port 12345
   ```

## Usage

### Docker Usage (Recommended)

After running `docker-compose up -d`, the application will be available at:
- **Web Interface**: http://localhost:8501 (Streamlit frontend)
- **API Documentation**: http://localhost:12345/docs (FastAPI Swagger UI)

Simply open your browser to http://localhost:8501 and start analyzing YouTube videos!

### Local Development Usage

#### Web Interface (Streamlit Frontend)
The project includes a Streamlit-based web interface for easy interaction:

1. Start the backend API:
```bash
uv run uvicorn app:app --reload --host 0.0.0.0 --port 12345
```

2. In a new terminal, start the frontend:
```bash
cd frontend
uv run streamlit run app.py
```

3. Open your browser to `http://localhost:8501` to access the web interface

### Web API
Start the FastAPI server:
```bash
uv run uvicorn app:app --reload --host 0.0.0.0 --port 12345
```

#### API Endpoints
- `POST /api/process?youtube_url=URL` - Start processing a YouTube video (filename auto-generated from video title)
- `GET /api/tasks` - List all tasks and their statuses
- `GET /api/status/{task_id}` - Check status of a specific task
- `GET /api/download/{task_id}` - Download the processed Excel file

### Command Line
You can also use the command line interface:
```bash
uv run python main.py "YOUTUBE_URL" [optional_output_path]
```

Run the main entry point with a YouTube URL. Optionally specify an output Excel path.

```bash
uv run python main.py "https://www.youtube.com/watch?v=YOUR_VIDEO_ID" ./chapters.xlsx
```

On the console you’ll see:
- Whether chapters came from **YouTube (yt-dlp)** or the **LLM**.
- How many chapters were produced.

The Excel file includes:
- One **chapter row** (title, start/end links, source label, summary).
- Followed by **concept rows** under that chapter, with key concepts and what is said in the podcast about each concept.
- Timestamp cells are **clickable** and jump straight to the moment on YouTube.

## API Usage

You can also use the FastAPI endpoint to generate and download the Excel file:

1. Start the API server:
   ```bash
   uv run uvicorn app:app --reload --port 12345
   ```

2. Send a POST request to `/api/process` with the YouTube URL:
   ```bash
   curl -X POST "http://localhost:12345/api/process?youtube_url=https://www.youtube.com/watch?v=YOUR_VIDEO_ID"
   ```

3. Check the task status and download when complete:
   ```bash
   curl "http://localhost:12345/api/tasks"
   curl "http://localhost:12345/api/download/{task_id}" -o chapters.xlsx
   ```

This will return the generated `.xlsx` file as a download.

## Project Structure
```
youtube-podcast-analyser/
├─ frontend/               # Streamlit web interface
│  ├─ app.py              # Streamlit frontend application
│  ├─ pyproject.toml      # Frontend dependencies
│  └─ README.md           # Frontend documentation
├─ output/                 # Generated Excel files output directory
├─ .env                    # Environment variables (OpenAI/Groq API keys, not committed)
├─ .gitignore             # Git ignore patterns
├─ pyproject.toml         # Main project dependencies
├─ uv.lock                # Dependency lock file
├─ README.md              # This file
├─ main.py                # CLI entry point
├─ app.py                 # FastAPI web server
├─ config.py              # Configuration management
├─ analyser.py            # Transcript analysis with timestamps
├─ transcript_fetcher.py  # Pulls YouTube transcript, adds [MM:SS] stamps
├─ transcribe.py          # Creates transcript with Whisper if YouTube transcript not available
├─ chapters.py            # ChapterMaker: official chapters → else LLM; per-chapter summary+concepts
├─ exporter.py            # Excel exporter with timestamp hyperlinks
└─ utils.py               # Helpers (timestamps, chunking, URL parsing)
```

## How It Works
1. **Transcript**: `transcript_fetcher.py` extracts the video ID, fetches the transcript (or generates a new one with transcribe.py **if the Youtube transcript is not available AND USE_WHISPER in the .env is set to true**), and produces a single text with `[MM:SS]` stamps.
2. **Chapters**: `chapters.py` tries YouTube’s official chapters first (via `yt-dlp`). If none are available, it asks the LLM specified in the env file (or defaults) to create sequential chapters using the transcript timestamps.
3. **Summaries & Concepts**: For each chapter, the selected LLM produces a short summary and a list of concepts/terms with representative timestamps.
4. **Export**: `exporter.py` writes an `.xlsx` with hyperlinks for start/end and each concept mention timestamp.

## Notes & Limits
- If a video has **no transcript** or transcripts are disabled, it will look for the variable USE_WHISPER in the .env file to be true; otherwise generate an error and exit.
- When **official YouTube chapters** exist, they are preferred; otherwise **LLM** chapters are generated.
- Prompts are intentionally simple; tune temperature or instructions if needed.

## Troubleshooting
- **“OPENAI_API_KEY not set”** → Ensure `.env` exists and is loaded (the app uses `python-dotenv`).
- **Transcript errors** → The video may not allow transcripts (try another video).
- **Hyperlinks not clickable** → Open the `.xlsx` in Excel/compatible viewer; links are placed on timestamp cells.

---

**Credits**: Built with `youtube-transcript-api`, `yt-dlp`, `openai`, `python-dotenv`, and `openpyxl`.


