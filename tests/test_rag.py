from pathlib import Path
from types import SimpleNamespace

import pytest

import ai_helper
from pawpal_system import Pet
from rag import Retriever, load_chunks

KNOWLEDGE = Path(__file__).parent.parent / "knowledge"


@pytest.fixture(scope="module")
def retriever():
    return Retriever(load_chunks(KNOWLEDGE))


class FakeClient:
    def __init__(self, text="Walk twice a day [dog-exercise.md]"):
        self.calls = []
        self.models = self
        self._text = text

    def generate_content(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(text=self._text)


class BrokenClient:
    def __init__(self):
        self.models = self

    def generate_content(self, **kwargs):
        raise RuntimeError("boom")


def test_load_chunks_splits_by_heading(tmp_path):
    (tmp_path / "x.md").write_text("# Title\n\nintro\n\n## A\nalpha\n\n## B\nbeta\n")
    chunks = load_chunks(tmp_path)
    assert [c.heading for c in chunks] == ["A", "B"]
    assert all(c.source == "x.md" for c in chunks)


def test_knowledge_base_loads():
    chunks = load_chunks(KNOWLEDGE)
    assert len(chunks) >= 10
    assert {"dog-exercise.md", "cat-care.md"} <= {c.source for c in chunks}


def test_retrieval_ranks_relevant_chunk_first(retriever):
    hits = retriever.search("how often should I walk a senior dog")
    assert hits
    assert hits[0][0].source in {"senior-pets.md", "dog-exercise.md"}


def test_retrieval_finds_cat_grooming(retriever):
    sources = [c.source for c, _ in retriever.search("how often brush my cat")]
    assert "cat-care.md" in sources or "grooming.md" in sources


def test_out_of_scope_returns_nothing(retriever):
    assert retriever.search("who won the world cup") == []


def test_answer_uses_only_retrieved_passages(retriever):
    client = FakeClient()
    answer, hits = ai_helper.ask("How much exercise does a dog need?", retriever, client=client)
    assert answer.startswith("Walk twice")
    prompt = client.calls[0]["contents"]
    assert all(c.text in prompt for c, _ in hits)
    assert client.calls[0]["model"] == ai_helper.MODEL


def test_pet_context_added_to_query_and_prompt(retriever):
    pet = Pet(name="Rex", species="dog", age=12)
    client = FakeClient()
    ai_helper.ask("How much exercise?", retriever, pet=pet, client=client)
    assert "Rex" in client.calls[0]["contents"]
    assert "dog" in ai_helper.build_query("How much exercise?", pet)


def test_no_match_skips_model_call(retriever):
    client = FakeClient()
    answer, hits = ai_helper.ask("who won the world cup", retriever, client=client)
    assert answer == ai_helper.NO_GUIDANCE
    assert hits == [] and client.calls == []


def test_missing_api_key_fallback(retriever, monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    answer, _ = ai_helper.ask("How much exercise does a dog need?", retriever)
    assert answer == ai_helper.NOT_CONFIGURED


def test_api_error_returns_friendly_message(retriever):
    answer, _ = ai_helper.ask("How much exercise does a dog need?", retriever, client=BrokenClient())
    assert "couldn't get an answer" in answer


# ---- owner data (live pets/tasks/schedule) as context ----

def make_owner():
    from datetime import time

    from pawpal_system import Owner, Preferences, Task

    owner = Owner(name="Sam", preferences=Preferences(time(8, 0), time(18, 0)))
    rex = Pet(name="Rex", species="dog", age=12)
    rex.add_task(Task("Morning walk", "", 20, "high", "walk"))
    rex.add_task(Task("Brush coat", "", 10, "low", "grooming"))
    owner.add_pet(rex)
    owner.add_pet(Pet(name="Tilly", species="cat", age=2))
    return owner


def test_owner_context_reflects_current_data():
    owner = make_owner()
    text = "\n".join(c.text for c in ai_helper.owner_context(owner))
    assert "Rex is a 12-year-old dog" in text
    assert "2 task(s), 30 minutes in total" in text
    assert "Morning walk" in text and "Tilly" in text
    assert "Plan for" in text  # today's schedule chunk
    assert all(c.source == ai_helper.OWNER_SOURCE for c in ai_helper.owner_context(owner))

    owner.pets[0].tasks.pop()  # data changes -> context changes, nothing cached
    assert "Brush coat" not in "\n".join(c.text for c in ai_helper.owner_context(owner))


def test_owner_context_empty_without_pets():
    from pawpal_system import Owner, Preferences
    from datetime import time

    assert ai_helper.owner_context(Owner("Sam", Preferences(time(8), time(18)))) == []


def test_owner_data_included_in_prompt(retriever):
    client = FakeClient()
    ai_helper.ask("What walks does Rex have today?", retriever, client=client, owner=make_owner())
    prompt = client.calls[0]["contents"]
    assert "Morning walk" in prompt and f"[{ai_helper.OWNER_SOURCE}]" in prompt


def test_owner_data_alone_still_answers_when_no_guide_matches(retriever):
    client = FakeClient("Rex has a 20 minute walk.")
    answer, hits = ai_helper.ask("who won the world cup", retriever, client=client, owner=make_owner())
    assert hits == [] and len(client.calls) == 1
    assert answer.startswith("Rex")


def test_no_owner_keeps_old_behaviour(retriever):
    client = FakeClient()
    ai_helper.ask("How much exercise does a dog need?", retriever, client=client)
    assert ai_helper.OWNER_SOURCE not in client.calls[0]["contents"].split("Question:")[0]


def test_cited_passages_only_returns_what_the_answer_cites(retriever):
    hits = retriever.search("feeding schedule dog", k=3)
    assert hits
    owner_chunks = ai_helper.owner_context(make_owner())

    # Answer cites only the owner's data: unrelated guide hits must not be shown.
    shown = ai_helper.cited_passages(f"Rex walks at 08:00 [{ai_helper.OWNER_SOURCE}].", hits, owner_chunks)
    assert shown and all(c.source == ai_helper.OWNER_SOURCE and s is None for c, s in shown)

    # Answer cites a guide: only that guide comes back.
    src = hits[0][0].source
    shown = ai_helper.cited_passages(f"Feed twice daily [{src}].", hits, owner_chunks)
    assert shown and all(c.source == src for c, _ in shown)

    # Answer cites nothing: nothing shown.
    assert ai_helper.cited_passages("I don't know.", hits, owner_chunks) == []
