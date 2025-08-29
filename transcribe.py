# transcribe.py
import os
import json
import math
import tempfile
from typing import List, Tuple, Optional

from pydub import AudioSegment
import yt_dlp
from openai import OpenAI
from dotenv import load_dotenv

from utils import ts, extract_video_id
from config import get_whisper_model

class WhisperTranscriber:
    """
    Fallback transcriber using OpenAI Whisper when YouTube transcript is unavailable.
    Flow:
      1) Download bestaudio with yt-dlp
      2) Extract to m4a (ffmpeg) and chunk by duration
      3) Transcribe chunks with Whisper (verbose JSON to get timestamps)
      4) Stitch segments into a single [MM:SS] stamped transcript
    """
    def __init__(self, model_name: Optional[str] = None, chunk_minutes: int = 8, overlap_ms: int = 0):
        load_dotenv()
        self.client = OpenAI()
        self.model = model_name or get_whisper_model()
        self.chunk_ms = int(chunk_minutes * 60 * 1000)
        self.overlap_ms = overlap_ms  # set to ~500–2000 if you want overlapping context

    # ---------- Public API ----------
    def transcribe_video(self, video_url: str) -> str:
        print("Warning: Transcribing using Whisper")
        with tempfile.TemporaryDirectory() as tmpdir:
            audio_path = self._download_audio(video_url, tmpdir)
            chunks = self._chunk_audio(audio_path, tmpdir)
            lines: List[str] = []
            for idx, (chunk_path, start_ms) in enumerate(chunks):
                segments = self._transcribe_file(chunk_path)
                if not segments:
                    # fallback: put whole chunk at its start time
                    text = self._safe_text(self._transcribe_text_only(chunk_path))
                    if text.strip():
                        lines.append(f"{ts(start_ms/1000)} {text}")
                    continue

                # stitch with offset from chunk start
                for seg in segments:
                    seg_start = float(seg.get("start", 0.0)) + (start_ms / 1000.0)
                    seg_text = self._safe_text(seg.get("text", ""))
                    if seg_text.strip():
                        lines.append(f"{ts(seg_start)} {seg_text}")

            return "\n".join(lines)

    # ---------- Steps ----------
    def _download_audio(self, video_url: str, out_dir: str) -> str:
        vid = extract_video_id(video_url)
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "format": "bestaudio/best",
            "outtmpl": os.path.join(out_dir, f"{vid}.%(ext)s"),
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "m4a",
                    "preferredquality": "192",
                }
            ],
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
        # Determine resulting audio path (m4a)
        audio_path = os.path.join(out_dir, f"{vid}.m4a")
        if not os.path.exists(audio_path):
            # sometimes it stays webm/opus; fall back to bestaudio file found
            base = os.path.join(out_dir, f"{vid}")
            for ext in (".m4a", ".webm", ".opus", ".mp3"):
                if os.path.exists(base + ext):
                    audio_path = base + ext
                    break
        return audio_path

    def _chunk_audio(self, audio_path: str, out_dir: str) -> List[Tuple[str, int]]:
        audio = AudioSegment.from_file(audio_path)
        if len(audio) <= self.chunk_ms:
            out_path = os.path.join(out_dir, "chunk_000.m4a")
            audio.export(out_path, format="m4a")
            return [(out_path, 0)]

        chunks: List[Tuple[str, int]] = []
        start = 0
        idx = 0
        while start < len(audio):
            end = min(start + self.chunk_ms, len(audio))
            piece = audio[start:end]
            out_path = os.path.join(out_dir, f"chunk_{idx:03d}.m4a")
            piece.export(out_path, format="m4a")
            chunks.append((out_path, start))
            idx += 1
            if end == len(audio):
                break
            start = end - self.overlap_ms if self.overlap_ms else end
        return chunks

    def _transcribe_file(self, file_path: str) -> List[dict]:
        """
        Use verbose_json to get segments with per-segment start times.
        Returns list of {start, end, text}.
        """
        with open(file_path, "rb") as f:
            res = self.client.audio.transcriptions.create(
                model=self.model,  # e.g., "whisper-1"
                file=f,
                response_format="verbose_json",
                temperature=0.0,
            )
        # Be tolerant to SDK return types
        segments = getattr(res, "segments", None)
        if segments is None:
            try:
                segments = res.get("segments", None)  # type: ignore[attr-defined]
            except Exception:
                segments = None

        # Convert to a normalized list of dicts
        out: List[dict] = []
        if segments:
            for s in segments:
                start = float(getattr(s, "start", None) if hasattr(s, "start") else s.get("start", 0.0))
                text = getattr(s, "text", None) if hasattr(s, "text") else s.get("text", "")
                out.append({"start": start, "text": text})
        return out

    def _transcribe_text_only(self, file_path: str) -> str:
        with open(file_path, "rb") as f:
            res = self.client.audio.transcriptions.create(
                model=self.model,
                file=f,
                temperature=0.0,
            )
        return getattr(res, "text", None) or (res.get("text", "") if isinstance(res, dict) else "")

    @staticmethod
    def _safe_text(text: Optional[str]) -> str: 
        return text or ""
