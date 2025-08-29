from youtube_transcript_api import (
    YouTubeTranscriptApi,
    TranscriptsDisabled,
    NoTranscriptFound,
)
from typing import List, Tuple
import os

from config import use_whisper
from transcribe import WhisperTranscriber

from utils import extract_video_id, get_start_text, ts

class YouTubeTranscriptFetcher:
    """
    Fetches YouTube transcripts using the instance-based API:
        ytt_api = YouTubeTranscriptApi()
        ytt_api.fetch(video_id, languages=[...])
    """
    def __init__(self, video_url: str, preferred_langs: List[str] = None):
        self.video_url = video_url
        self.video_id = extract_video_id(video_url)
        self.preferred_langs = preferred_langs or ["en", "en-US", "en-GB"]
        self.ytt_api = YouTubeTranscriptApi()

    def fetch_transcript_text(self) -> str:
        """
        Returns a single text blob with [MM:SS] timestamps.
        Uses .fetch() which will choose an available transcript for preferred languages.
        """
        """try:
            entries = self.ytt_api.fetch(self.video_id, languages=self.preferred_langs)
        except TranscriptsDisabled:
            raise RuntimeError("Transcripts are disabled for this video.")
        except NoTranscriptFound:
            raise RuntimeError("No transcript found for preferred languages.")
        except Exception as e:
            # Surface any other library/network errors succinctly
            raise RuntimeError(f"Transcript fetch failed: {e}")

        lines: List[str] = []
        for e in entries:
            start, text = get_start_text(e)
            if text.strip():
                lines.append(f"{ts(start)} {text}")
        return "\n".join(lines)"""
    
        # Try YouTube transcript first (instance API)
        try:
            entries = self.ytt_api.fetch(self.video_id, languages=self.preferred_langs)
            lines = []
            lines: List[str] = []
            for e in entries:
                start, text = get_start_text(e)
                if text.strip():
                    lines.append(f"{ts(start)} {text}")
            return "\n".join(lines)
        except (TranscriptsDisabled, NoTranscriptFound):
            pass
        except Exception:
            # ignore and fall through to whisper if configured
            pass

        # Fallback: Whisper (only if enabled)
        if use_whisper():
            return WhisperTranscriber().transcribe_video(self.video_url)

        # If we reach here, no transcript and Whisper disabled
        raise RuntimeError("No YouTube transcript available and USE_WHISPER is false. Enable USE_WHISPER in .env to auto-transcribe.")
