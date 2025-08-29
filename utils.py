from typing import List, Tuple
from urllib.parse import urlparse, parse_qs



def extract_video_id(url: str) -> str:
    """Extract a YouTube video ID from watch/share/shorts URLs."""
    p = urlparse(url)
    if p.netloc.endswith("youtu.be"):
        return p.path.lstrip("/")
    if "watch" in p.path:
        return parse_qs(p.query).get("v", [""])[0]
    # Fallback to last path segment
    return p.path.strip("/").split("/")[-1]


def ts(mm_ss: float) -> str:
    """Format seconds as [MM:SS]."""
    m, s = divmod(int(mm_ss), 60)
    return f"[{m:02d}:{s:02d}]"


def chunk_text(text: str, max_chars: int = 9000) -> List[str]:
    """Minimal, sentence/newline-aware text chunker."""
    if len(text) <= max_chars:
        return [text]
    chunks, start = [], 0
    while start < len(text):
        end = min(start + max_chars, len(text))
        split_at = max(text.rfind("\n", start, end), text.rfind(". ", start, end))
        if split_at == -1 or split_at < start + int(max_chars * 0.6):
            split_at = end
        chunks.append(text[start:split_at].strip())
        start = split_at
    return [c for c in chunks if c]

def get_start_text(entry) -> Tuple[float, str]:
    if isinstance(entry, dict):
        return float(entry.get("start", 0)), entry.get("text", "") or ""
    start = float(getattr(entry, "start", 0.0))
    text = getattr(entry, "text", "") or ""
    return start, text