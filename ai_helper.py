"""Gemini-backed answers for Ask PawPal, grounded in retrieved passages."""

import os

from dotenv import load_dotenv

from pawpal_system import Owner, Scheduler
from rag import Chunk, Retriever

load_dotenv()

MODEL = "gemini-3.5-flash-lite"
NO_GUIDANCE = "I don't have guidance on that yet. Try rephrasing, or ask your vet."
NOT_CONFIGURED = "AI is not configured. Set the GEMINI_API_KEY environment variable to enable Ask PawPal."

OWNER_SOURCE = "your-pawpal-data"

SYSTEM_PROMPT = (
    "You are PawPal, a pet-care assistant. Answer ONLY using the provided passages. "
    "Cite sources inline like [dog-exercise.md]. If the passages do not answer the question, "
    "say you don't know. For anything medical or urgent, recommend contacting a vet. "
    "Keep answers short and friendly. "
    f"Passages from [{OWNER_SOURCE}] describe the owner's own pets, tasks and today's schedule: "
    "use them for questions about what the owner has planned, and quote their numbers exactly "
    "instead of recalculating. Care advice (how much, how often, what is safe) must still come "
    "from the care guide passages, never from the owner's data alone."
)


def build_query(question: str, pet=None) -> str:
    """Append the pet's species and age so retrieval can favour relevant guides."""
    if pet is None:
        return question
    return f"{question} {pet.species} age {pet.age}"


def owner_context(owner: Owner) -> list[Chunk]:
    """Describe the owner's current pets, tasks and today's plan as passages.

    Built fresh from the live Owner on every question, so it can never go stale.
    Totals are computed here so the model quotes them instead of doing arithmetic.
    """
    if not owner.pets:
        return []
    chunks = []
    for pet in owner.pets:
        lines = [f"{pet.name} is a {pet.age}-year-old {pet.species}."]
        if pet.notes:
            lines.append(f"Notes: {pet.notes}")
        if pet.tasks:
            total = sum(t.duration_minutes for t in pet.tasks)
            lines.append(f"{len(pet.tasks)} task(s), {total} minutes in total:")
            for t in pet.tasks:
                done = "done" if t.completed else "not done"
                lines.append(
                    f"- {t.name} ({t.category}): {t.duration_minutes} min, "
                    f"{t.priority} priority, {done}"
                )
        else:
            lines.append("No tasks yet.")
        chunks.append(Chunk(OWNER_SOURCE, f"Pet: {pet.name}", "\n".join(lines)))

    if owner.get_all_tasks():
        plan = Scheduler(owner).generate_plan()
        chunks.append(Chunk(OWNER_SOURCE, "Today's schedule", plan.summary()))
    return chunks


def build_prompt(question: str, chunks: list[Chunk], pet=None) -> str:
    passages = "\n\n".join(f"[{c.source}]\n{c.text}" for c in chunks)
    pet_line = f"Pet: {pet.name}, a {pet.age}-year-old {pet.species}.\n" if pet else ""
    return f"Passages:\n{passages}\n\n{pet_line}Question: {question}"


def answer_question(
    question: str, chunks: list[Chunk], pet=None, client=None, owner_chunks=None
) -> str:
    """Answer from `chunks` plus `owner_chunks` only. Never raises; returns a friendly message on failure."""
    owner_chunks = owner_chunks or []
    if not chunks and not owner_chunks:
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
            contents=build_prompt(question, owner_chunks + chunks, pet),
            config={"system_instruction": SYSTEM_PROMPT, "max_output_tokens": 500},
        )
        return (response.text or NO_GUIDANCE).strip()
    except Exception as exc:
        return f"Sorry, I couldn't get an answer right now ({type(exc).__name__})."


def cited_passages(answer: str, hits, owner_chunks):
    """Return (chunk, score) pairs for only the sources the answer actually cites.

    Retrieval is keyword-based and can surface loosely related guides, so showing
    every hit as a "source" is misleading. Owner chunks come back with score None.
    """
    cited = [(c, s) for c, s in hits if c.source in answer]
    if OWNER_SOURCE in answer:
        cited += [(c, None) for c in owner_chunks]
    return cited


def ask(question: str, retriever: Retriever, pet=None, client=None, k: int = 3, owner=None):
    """Retrieve care guides, add the owner's live data, then answer.

    Returns (answer, retrieved guide (chunk, score) pairs). Owner data is always
    included in the prompt rather than retrieved, since it is small.
    """
    hits = retriever.search(build_query(question, pet), k=k)
    owner_chunks = owner_context(owner) if owner is not None else []
    return answer_question(question, [c for c, _ in hits], pet, client, owner_chunks), hits
