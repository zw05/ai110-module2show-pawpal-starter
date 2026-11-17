"""Gemini-backed answers for Ask PawPal, grounded in retrieved passages."""

import os

from dotenv import load_dotenv

from rag import Chunk, Retriever

load_dotenv()

MODEL = "gemini-2.5-flash"
NO_GUIDANCE = "I don't have guidance on that yet. Try rephrasing, or ask your vet."
NOT_CONFIGURED = "AI is not configured. Set the GEMINI_API_KEY environment variable to enable Ask PawPal."

SYSTEM_PROMPT = (
    "You are PawPal, a pet-care assistant. Answer ONLY using the provided passages. "
    "Cite sources inline like [dog-exercise.md]. If the passages do not answer the question, "
    "say you don't know. For anything medical or urgent, recommend contacting a vet. "
    "Keep answers short and friendly."
)


def build_query(question: str, pet=None) -> str:
    """Append the pet's species and age so retrieval can favour relevant guides."""
    if pet is None:
        return question
    return f"{question} {pet.species} age {pet.age}"


def build_prompt(question: str, chunks: list[Chunk], pet=None) -> str:
    passages = "\n\n".join(f"[{c.source}]\n{c.text}" for c in chunks)
    pet_line = f"Pet: {pet.name}, a {pet.age}-year-old {pet.species}.\n" if pet else ""
    return f"Passages:\n{passages}\n\n{pet_line}Question: {question}"


def answer_question(question: str, chunks: list[Chunk], pet=None, client=None) -> str:
    """Answer from `chunks` only. Never raises; returns a friendly message on failure."""
    if not chunks:
        return NO_GUIDANCE
    if client is None:
        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            return NOT_CONFIGURED
        try:
            from google import genai

            client = genai.Client(api_key=api_key)
        except Exception:
            return NOT_CONFIGURED
    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=build_prompt(question, chunks, pet),
            config={"system_instruction": SYSTEM_PROMPT, "max_output_tokens": 500},
        )
        return (response.text or NO_GUIDANCE).strip()
    except Exception as exc:
        return f"Sorry, I couldn't get an answer right now ({type(exc).__name__})."


def ask(question: str, retriever: Retriever, pet=None, client=None, k: int = 3):
    """Retrieve then answer. Returns (answer, retrieved (chunk, score) pairs)."""
    hits = retriever.search(build_query(question, pet), k=k)
    return answer_question(question, [c for c, _ in hits], pet, client), hits
