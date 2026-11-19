# Ask PawPal: RAG Care Q&A

## The problem it solves
PawPal+ schedules pet care tasks, but it can't answer the questions that come up while planning them. Examples are "How much exercise does a senior dog need?" and "How often should I groom a cat?" Owners have to leave the app and search the web, where the advice is inconsistent and may not fit their pet.

## The feature
A simple "Ask PawPal" box in the app.

1. The owner types a pet-care question and optionally picks one of their pets.
2. The app searches a small set of curated care guides (`knowledge/*.md`) for the most relevant passages.
3. Gemini answers using only those passages and cites its sources.
4. If nothing relevant is found, the app says "I don't have guidance on that" instead of guessing.

The answer comes from our own guides, so it is grounded and traceable. It also uses the selected pet's species and age.

## What gets added
- `knowledge/*.md`: short care guides (dog exercise, feeding, cat care, senior pets, grooming, medication)
- `pawpal/rag.py`: loads the guides and finds the best-matching passages (BM25, no network)
- `pawpal/ai_helper.py`: sends the passages and question to Gemini and returns a cited answer
- `app.py`: the new "Ask PawPal" section and a sources expander
- `tests/test_rag.py`: offline tests, with the Gemini client mocked

## Out of scope
- The scheduler is unchanged.
- No vector database or embeddings. The guides are small enough for keyword search.
- Answers are general guidance, not veterinary advice.
