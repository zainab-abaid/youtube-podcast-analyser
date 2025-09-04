import os
from typing import List, Optional, Any
from dotenv import load_dotenv
from utils import chunk_text

# --------------------------- Provider Switch ---------------------------

load_dotenv()
USE_GROQ = os.getenv("USE_GROQ", "false").lower() == "true"

def _init_llm_client(model_name: Optional[str]) -> tuple[Any, str]:
    """
    Returns (client, resolved_model).
    - Uses Groq if USE_GROQ=true, otherwise OpenAI.
    - Optional env overrides:
        GROQ_CHAT_MODEL (default: llama-3.1-70b-versatile)
        OPENAI_MODEL    (default: gpt-4o)
    """
    if USE_GROQ:
        from groq import Groq
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        resolved = model_name or os.getenv("GROQ_CHAT_MODEL", "meta-llama/llama-4-scout-17b-16e-instruct")
        # If caller passed an OpenAI-only default, swap to Groq default
        if resolved == "gpt-4o":
            resolved = os.getenv("GROQ_CHAT_MODEL", "meta-llama/llama-4-scout-17b-16e-instruct")
        return client, resolved
    else:
        from openai import OpenAI
        client = OpenAI()  # reads OPENAI_API_KEY
        resolved = model_name or os.getenv("OPENAI_MODEL", "gpt-4o")
        return client, resolved


class TranscriptAnalyzer:
    """Delegates concept extraction/summarization to an LLM (OpenAI or Groq)."""
    def __init__(self, model_name: Optional[str] = None):
        self.client, self.model_name = _init_llm_client(model_name)

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
