import sys
from transcript_fetcher import YouTubeTranscriptFetcher
from chapters import ChapterMaker
from exporter import ExcelChapterExporter
from utils import get_video_title


def process_video(video_url: str, out_path: str):
    transcript_text = YouTubeTranscriptFetcher(video_url).fetch_transcript_text()
    print("Transcript generated; now generating and summarizing chapters.")
    # 1) Chapters (summary + per-chapter concepts)
    maker = ChapterMaker()
    chapters = maker.build_chapters_with_summaries(
        video_url=video_url,
        transcript_text=transcript_text,
        prefer_official=True,
        approx_target_chapters=8,
    )

    model_label = maker.model
    src = "YouTube (yt-dlp)" if chapters["source"] == "official" else "LLM ({model_label})"
    print(f"\n=== Chapters source: {src} — {chapters['chapter_count']} chapters ===\n")

    """# Global concepts (with timestamps)
    analyzer = TranscriptAnalyzer(model_name="gpt-4o")
    global_concepts = analyzer.analyze_with_timestamps(transcript_text)

    print("\n=== Global Concepts (with timestamps) ===\n")
    print(global_concepts)
    """

    # export to Excel
    saved = ExcelChapterExporter(video_url, out_path=out_path).export(chapters)
    print(f"Saved: {saved}")
    return out_path


def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py <YouTube URL>")
        raise SystemExit(1)

    video_url = sys.argv[1]
    
    # Auto-generate filename based on video title
    if len(sys.argv) >= 3:
        # If user provides a custom path, use it
        out_path = sys.argv[2]
    else:
        # Auto-generate filename using video title
        video_title = get_video_title(video_url)
        out_path = f"podcast_summary_{video_title}.xlsx"

    process_video(video_url, out_path)


if __name__ == "__main__":
    main()
