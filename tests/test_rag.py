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
