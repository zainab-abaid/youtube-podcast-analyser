from typing import List, Tuple
from urllib.parse import urlparse, parse_qs
import yt_dlp
import re



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


def get_video_title(video_url: str) -> str:
    """Get the title of a YouTube video using yt-dlp."""
    # Try metadata-only extraction first to avoid format-related issues
    metadata_opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "extract_flat": True,  # Only extract metadata, no format info
        "writeinfojson": False,
        "ignoreerrors": True,
        "no_check_certificate": True,
        "format": "worst",  # Don't try to get best formats
    }
    
    try:
        print(f"Attempting to extract title for URL: {video_url}")
        with yt_dlp.YoutubeDL(metadata_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            
            if info and info.get("title"):
                title = info["title"]
                print(f"Successfully extracted title: {title}")
                
                # Sanitize filename by removing invalid characters
                sanitized_title = re.sub(r'[<>:"/\\|?*]', '_', title)
                # Limit length to avoid filesystem issues
                if len(sanitized_title) > 100:
                    sanitized_title = sanitized_title[:100]
                return sanitized_title
            
    except Exception as e:
        print(f"Metadata extraction failed: {str(e)}")
    
    # Try with full extraction but ignore format errors
    try:
        print("Trying full extraction with error tolerance...")
        full_opts = {
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
            "extract_flat": False,
            "ignoreerrors": True,  # Ignore format errors
            "no_check_certificate": True,
            "format": "worst/bestaudio/best",  # Try different format preferences
        }
        
        with yt_dlp.YoutubeDL(full_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            
            if info:
                title = info.get("title")
                if not title:
                    # Try alternative title fields
                    title = (info.get("fulltitle") or 
                            info.get("alt_title") or 
                            info.get("display_id"))
                
                if title:
                    print(f"Full extraction succeeded: {title}")
                    # Sanitize filename by removing invalid characters
                    sanitized_title = re.sub(r'[<>:"/\\|?*]', '_', title)
                    if len(sanitized_title) > 100:
                        sanitized_title = sanitized_title[:100]
                    return sanitized_title
                    
    except Exception as e:
        print(f"Full extraction also failed: {str(e)}")
    
    # Try using YouTube's webpage directly as a last resort
    try:
        print("Trying webpage extraction as final fallback...")
        import urllib.request
        import html
        
        # Get the webpage content
        req = urllib.request.Request(video_url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        with urllib.request.urlopen(req) as response:
            html_content = response.read().decode('utf-8')
            
        # Look for title in various places
        title_patterns = [
            r'"title":"([^"]+)"',
            r'<title>([^<]+)</title>',
            r'"videoDetails":{"videoId":"[^"]+","title":"([^"]+)"',
            r'<meta property="og:title" content="([^"]+)"'
        ]
        
        for pattern in title_patterns:
            match = re.search(pattern, html_content)
            if match:
                title = html.unescape(match.group(1))
                # Clean up common YouTube title suffixes
                title = re.sub(r' - YouTube$', '', title)
                title = re.sub(r' \| YouTube$', '', title)
                
                if title and title != "YouTube":
                    print(f"Webpage extraction succeeded: {title}")
                    # Sanitize filename
                    sanitized_title = re.sub(r'[<>:"/\\|?*]', '_', title)
                    if len(sanitized_title) > 100:
                        sanitized_title = sanitized_title[:100]
                    return sanitized_title
                    
    except Exception as e:
        print(f"Webpage extraction failed: {str(e)}")
    
    # Final fallback to video ID
    video_id = extract_video_id(video_url)
    fallback_title = f"video_{video_id}"
    print(f"Using final fallback title: {fallback_title}")
    return fallback_title