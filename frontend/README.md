# YouTube Podcast Analyzer - Frontend

A Streamlit-based web interface for the YouTube Podcast Analyzer API.

## Features

- Simple and intuitive UI for submitting YouTube videos for analysis
- Real-time status tracking of processing tasks
- Download processed results directly from the interface
- Auto-refresh functionality for monitoring progress

## Requirements

- Python 3.13 (as specified in parent project)
- [uv](https://github.com/astral-sh/uv) - Python package and environment manager

## Installation

1. Install uv (if not already installed):
```bash
curl -sSf https://astral.sh/uv/install.sh | sh
# or on Linux: sudo snap install astral-uv --classic
```

## Running the Frontend

1. Make sure the backend API is running on port 12345:
```bash
# From the root directory
uv run uvicorn app:app --reload --host 0.0.0.0 --port 12345
```

2. Start the Streamlit frontend:
```bash
# From the frontend directory
uv run streamlit run app.py
```

The frontend will be available at `http://localhost:8501`

## Usage

1. Enter a YouTube video URL in the text box
2. Optionally provide a custom filename for the output
3. Click "Generate Summary" to start processing
4. Monitor the processing status
5. Download the results when processing is complete

## Configuration

The frontend connects to the backend API at `http://localhost:12345` by default. You can change this by setting the `API_BASE_URL` environment variable:

```bash
export API_BASE_URL=http://your-api-server:port
uv run streamlit run app.py
```
