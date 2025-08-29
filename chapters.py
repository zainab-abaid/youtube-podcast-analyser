import json
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
import yt_dlp
from dotenv import load_dotenv
from openai import OpenAI
from config import get_openai_model

# --------------------------- Data Models ---------------------------

@dataclass
class Chapter:
    title: str
    start: float       # seconds
    end: float         # seconds

    def as_display(self) -> str:
        def ts(sec: float) -> str:
            m, s = divmod(int(sec), 60)
            return f"{m:02d}:{s:02d}"
        return f"{self.title} [{ts(self.start)}–{ts(self.end)}]"


# --------------------------- Chapter Maker ---------------------------

class ChapterMaker:
    """
    Builds chapters for a given video.
    1) Try to read official chapters via yt-dlp metadata.
    2) If unavailable, ask the LLM to create sequential chapters from the transcript.
    3) For each chapter, ask the LLM for a short summary and a concept list.
    """
    def __init__(self, model_name: str = "gpt-4o"):
        load_dotenv()           # read OPENAI_API_KEY from .env
        self.client = OpenAI()  # create our own client
        self.model = model_name or get_openai_model()

    # --- (A) Try official YouTube chapters via yt-dlp ---
    def _fetch_youtube_chapters(self, video_url: str) -> List[Chapter]:
        ydl_opts = {"quiet": True, "no_warnings": True, "skip_download": True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
        chapters = info.get("chapters") or []
        results: List[Chapter] = []
        for c in chapters:
            # yt-dlp chapter item usually has 'start_time', 'end_time', 'title'
            title = (c.get("title") or "").strip() or "Chapter"
            start = float(c.get("start_time", 0.0))
            end = float(c.get("end_time", max(start, info.get("duration", start))))
            if end < start:
                end = start
            results.append(Chapter(title=title, start=start, end=end))
        # Ensure they’re in time order
        results.sort(key=lambda ch: ch.start)
        return results

    # --- (B) LLM fallback: create chapters from transcript ---
    def _llm_create_chapters(self, transcript_text: str, approx_target_chapters: int = 8) -> List[Chapter]:
        """
        Ask the model to return JSON with sequential chapters:
          [{"title": "...", "start_sec": 0, "end_sec": 123}, ...]
        Uses timestamps present in the transcript lines like [MM:SS] to ground times.
        """
        prompt = (
            "You will read a long transcript with inline timestamps like [MM:SS]. "
            "Create sequential, non-overlapping CHAPTERS that cover the whole talk.\n"
            f"- Aim for ~{approx_target_chapters} chapters when reasonable.\n"
            "- Use the timestamps you see to infer realistic start/end seconds for each chapter.\n"
            "- Titles must be short and topic-focused (like good YouTube chapters).\n"
            "- Return STRICT JSON only, in this schema:\n"
            "[{\"title\": \"...\", \"start_sec\": <number>, \"end_sec\": <number>}, ...]\n\n"
            "Transcript:\n"
            f"{transcript_text}\n"
        )
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )
        raw = resp.choices[0].message.content.strip()

        # Be resilient to stray prose: locate the first JSON array
        json_start = raw.find("[")
        json_end = raw.rfind("]")
        if json_start == -1 or json_end == -1:
            raise RuntimeError("LLM did not return JSON chapters.")
        data = json.loads(raw[json_start: json_end + 1])

        chapters: List[Chapter] = []
        for item in data:
            title = (item.get("title") or "").strip() or "Chapter"
            start = float(item.get("start_sec", 0))
            end = float(item.get("end_sec", max(start + 1, start)))
            if end < start:
                end = start
            chapters.append(Chapter(title=title, start=start, end=end))
        chapters.sort(key=lambda ch: ch.start)
        return chapters

    # --- (C) Chapter summaries + concepts ---
    def _summarize_chapter_and_concepts(self, chapter: Chapter, transcript_text: str) -> Dict[str, Any]:
        """
        Provide a concise summary + concept list for a chapter.
        We pass only the transcript segment that falls within [start, end].
        """
        # Slice transcript by time; transcript has lines like "[MM:SS] text"
        lines = []
        for line in transcript_text.splitlines():
            if not line.startswith("[") or "]" not in line:
                continue
            stamp = line[1:line.index("]")]
            try:
                mm, ss = stamp.split(":")
                t = int(mm) * 60 + int(ss)
            except Exception:
                continue
            if chapter.start <= t <= chapter.end:
                lines.append(line)
        chapter_text = "\n".join(lines)

        prompt = (
            "You are analyzing a single chapter (segment) from a podcast transcript.\n"
            "Tasks:\n"
            "1) Provide a 2–4 sentence **chapter summary** specific to what was said.\n"
            "2) Provide a **list of important concepts/terms** mentioned in this chapter.\n"
            "3) For each concept, include one or more **timestamps [MM:SS]** from the text where it appears.\n\n"
            "Return STRICT JSON with this schema:\n"
            "{\n"
            '  "summary": "string",\n'
            '  "concepts": [\n'
            '     {"name": "string", "mentions": ["[MM:SS]", "..."]}\n'
            "  ]\n"
            "}\n\n"
            f"Chapter window: {chapter.start:.0f}–{chapter.end:.0f} seconds\n"
            f"Transcript lines:\n{chapter_text}\n"
        )

        resp = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )
        raw = resp.choices[0].message.content.strip()
        json_start = raw.find("{")
        json_end = raw.rfind("}")
        data = {}
        if json_start != -1 and json_end != -1:
            try:
                data = json.loads(raw[json_start: json_end + 1])
            except Exception:
                data = {"summary": "", "concepts": []}
        return {
            "title": chapter.title,
            "start": chapter.start,
            "end": chapter.end,
            "summary": data.get("summary", ""),
            "concepts": data.get("concepts", []),
        }

    # --- Public API ---

    def build_chapters_with_summaries(self, video_url, transcript_text, prefer_official=True, approx_target_chapters=8):
        chapters = []
        used_official = False

        if prefer_official:
            try:
                chapters = self._fetch_youtube_chapters(video_url)
                used_official = len(chapters) > 0         
            except Exception:
                chapters = []

        if not chapters:
            chapters = self._llm_create_chapters(transcript_text, approx_target_chapters=approx_target_chapters)

        enriched = [self._summarize_chapter_and_concepts(ch, transcript_text) for ch in chapters]

        return {
            "source": "official" if used_official else "llm",   
            "chapter_count": len(enriched),
            "chapters": enriched,
        }

