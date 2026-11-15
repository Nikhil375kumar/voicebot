"""
Groq API service — all LLM logic in one place.
Reads API key from environment; never hardcoded.
"""

import os
from groq import Groq


def get_client() -> Groq:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY is not set. Add it to your .env file.")
    return Groq(api_key=api_key)


def transcribe_audio(audio_bytes: bytes, filename: str = "audio.wav") -> str:
    """
    Convert speech audio bytes → text using Groq Whisper.
    Forces English to avoid mis-detection of accent as another language.
    Returns the transcribed string.
    """
    client = get_client()
    transcription = client.audio.transcriptions.create(
        model="whisper-large-v3-turbo",
        file=(filename, audio_bytes),
        response_format="text",
        language="en",
        prompt="Interview questions about life story, superpower, growth areas, failure, boundaries, limits, motivation, misconceptions, coworkers.",
    )
    return transcription.strip()


def get_llm_response(user_message: str, system_prompt: str) -> str:
    """
    Send a user message to Groq LLM and return the assistant's reply.
    Uses openai/gpt-oss-20b — available on Groq free/paid tier.
    """
    client = get_client()
    completion = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        max_tokens=300,
        temperature=0.75,
    )
    return completion.choices[0].message.content.strip()
