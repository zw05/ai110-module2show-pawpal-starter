"""Save and load the Owner (with pets, tasks and preferences) as JSON on disk.

Streamlit's session_state is per browser session, so it is lost on reload.
This keeps the data in a file so it survives reloads and restarts.
"""

import json
from datetime import date, time
from pathlib import Path

from .pawpal_system import Owner, Pet, Preferences, Task

DEFAULT_PATH = Path(__file__).parent.parent / "data" / "owner.json"


def owner_to_dict(owner: Owner) -> dict:
    prefs = owner.preferences
    return {
        "name": owner.name,
        "preferences": {
            "day_start": prefs.day_start.isoformat(),
            "day_end": prefs.day_end.isoformat(),
            "preferred_categories": list(prefs.preferred_categories),
            "max_task_minutes": prefs.max_task_minutes,
        },
        "pets": [
            {
                "name": p.name,
                "species": p.species,
                "age": p.age,
                "notes": p.notes,
                "vet_visits": [d.isoformat() for d in p.vet_visits],
                "tasks": [
                    {
                        "name": t.name,
                        "description": t.description,
                        "duration_minutes": t.duration_minutes,
                        "priority": t.priority,
                        "category": t.category,
                        "completed": t.completed,
                        "completed_on": t.completed_on.isoformat() if t.completed_on else None,
                    }
                    for t in p.tasks
                ],
            }
            for p in owner.pets
        ],
    }


def owner_from_dict(data: dict) -> Owner:
    prefs = data["preferences"]
    owner = Owner(
        name=data["name"],
        preferences=Preferences(
            day_start=time.fromisoformat(prefs["day_start"]),
            day_end=time.fromisoformat(prefs["day_end"]),
            preferred_categories=list(prefs.get("preferred_categories", [])),
            max_task_minutes=prefs.get("max_task_minutes"),
        ),
    )
    for p in data.get("pets", []):
        pet = Pet(name=p["name"], species=p["species"], age=p["age"], notes=p.get("notes", ""))
        pet.vet_visits = [date.fromisoformat(d) for d in p.get("vet_visits", [])]
        for t in p.get("tasks", []):
            t = dict(t)
            if t.get("completed_on"):
                t["completed_on"] = date.fromisoformat(t["completed_on"])
            pet.add_task(Task(**t))
        owner.add_pet(pet)
    return owner


def save_owner(owner: Owner, path: Path = DEFAULT_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(owner_to_dict(owner), indent=2), encoding="utf-8")
    tmp.replace(path)  # atomic, so a crash mid-write can't corrupt the saved file


def load_owner(path: Path = DEFAULT_PATH) -> Owner | None:
    """Return the saved Owner, or None if there is no usable save file."""
    try:
        return owner_from_dict(json.loads(path.read_text(encoding="utf-8")))
    except (OSError, ValueError, KeyError, TypeError):
        return None
