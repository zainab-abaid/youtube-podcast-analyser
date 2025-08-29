import sys
from analyser import TranscriptAnalyzer
from transcript_fetcher import YouTubeTranscriptFetcher
from chapters import ChapterMaker
from exporter import ExcelChapterExporter

def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py <YouTube URL>")
        raise SystemExit(1)

    video_url = sys.argv[1]
    out_path = sys.argv[2] if len(sys.argv) >= 3 else "chapters.xlsx"

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

if __name__ == "__main__":
    main()
