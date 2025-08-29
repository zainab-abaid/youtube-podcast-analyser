from openai import OpenAI
from utils import chunk_text
from typing import List
from dotenv import load_dotenv

class TranscriptAnalyzer:
    """Delegates concept extraction/summarization to GPT-4o."""
    def __init__(self, model_name: str = "gpt-4o"):
        load_dotenv()
        self.client = OpenAI()         # key read from env
        self.model_name = model_name

    def analyze_with_timestamps(self, transcript_text: str) -> str:
        """
        Extract important concepts/terms and summarize what was said about each,
        including one or more timestamps [MM:SS] for where it appears.
        """
        chunks = chunk_text(transcript_text, max_chars=9000)

        partials: List[str] = []
        for idx, chunk in enumerate(chunks, 1):
            prompt = (
                "You are an expert on Generative AI. Read the transcript CHUNK and:\n"
                "1) Identify important concepts/terms/technologies mentioned.\n"
                "2) For each, summarize what the speakers said (avoid generic definitions).\n"
                "3) Include one or more timestamps [MM:SS] for each concept, copied from the text.\n\n"
                f"CHUNK {idx}/{len(chunks)}:\n{chunk}\n\n"
                "Return bullets in the form:\n"
                "- <concept>: <what was said>. Timestamps: [MM:SS], [MM:SS]"
            )
            resp = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
            )
            partials.append(resp.choices[0].message.content.strip())

        merge_prompt = (
            "You will receive multiple bullet lists of concepts (each with timestamps) extracted from a long transcript.\n"
            "Deduplicate overlapping concepts, merge points, and output a single tidy list.\n"
            "Be specific to what the speakers said and preserve representative timestamps for each concept.\n\n"
            "INPUT LISTS:\n" + "\n\n---\n\n".join(partials) +
            "\n\nOUTPUT FORMAT:\n- <concept>: <what the transcript said (1–3 concise sentences)>. "
            "Timestamps: [MM:SS], [MM:SS]"
        )
        final = self.client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": merge_prompt}],
            temperature=0.2,
        )
        return final.choices[0].message.content.strip()
    
    def analyze(self, transcript_text: str) -> str:
        """
        - Splits long transcripts into manageable chunks
        - Runs per-chunk extraction
        - Merges/deduplicates concepts across chunks
        """
        chunks = chunk_text(transcript_text, max_chars=9000)
        print("first chunk:", chunks[0])
        partials: List[str] = []
        for idx, chunk in enumerate(chunks, 1):
            prompt = (
                "You are an expert on Generative AI. Read the transcript CHUNK and:\n"
                "1) Identify important concepts/terms/technologies mentioned.\n"
                "2) For each, summarize what the speakers said about it (avoid generic definitions).\n"
                "3) Keep bullets concise. Include the given timestamps when helpful.\n\n"
                f"CHUNK {idx}/{len(chunks)}:\n{chunk}\n\n"
                "Return bullets in the form: '- <concept>: <what was said>'."
            )
            resp = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
            )
            partials.append(resp.choices[0].message.content.strip())

        merge_prompt = (
            "You will receive multiple bullet lists of concepts extracted from a long transcript.\n"
            "Deduplicate overlapping concepts, merge points, and output a single tidy list.\n"
            "Be specific to what the speakers said.\n\n"
            "INPUT LISTS:\n" + "\n\n---\n\n".join(partials) +
            "\n\nOUTPUT FORMAT:\n- <concept>: <what the transcript said (1–3 concise sentences)>"
        )
        final = self.client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": merge_prompt}],
            temperature=0.2,
        )
        return final.choices[0].message.content.strip()