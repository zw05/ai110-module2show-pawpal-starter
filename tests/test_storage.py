from datetime import time

from pawpal.pawpal_system import Owner, Pet, Preferences, Task
from pawpal.storage import load_owner, save_owner


def make_owner():
    owner = Owner(
        name="Sam",
        preferences=Preferences(time(7, 30), time(19, 0), ["walk"], 45),
    )
    pet = Pet(name="Mochi", species="cat", age=3, notes="shy")
    pet.add_task(Task("Feed", "wet food", 10, "high", "feeding", completed=True))
    owner.add_pet(pet)
    return owner


def test_round_trip(tmp_path):
    path = tmp_path / "owner.json"
    save_owner(make_owner(), path)
    loaded = load_owner(path)
    assert loaded.name == "Sam"
    assert loaded.preferences == Preferences(time(7, 30), time(19, 0), ["walk"], 45)
    pet = loaded.pets[0]
    assert (pet.name, pet.species, pet.age, pet.notes) == ("Mochi", "cat", 3, "shy")
    task = pet.tasks[0]
    assert (task.name, task.duration_minutes, task.priority, task.completed) == ("Feed", 10, "high", True)


def test_missing_or_corrupt_file_returns_none(tmp_path):
    assert load_owner(tmp_path / "nope.json") is None
    bad = tmp_path / "bad.json"
    bad.write_text("{not json", encoding="utf-8")
    assert load_owner(bad) is None
