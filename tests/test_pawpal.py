from pawpal_system import Pet, Task


def test_mark_complete_changes_task_status():
    task = Task(
        name="Morning walk",
        description="30 min around the block",
        duration_minutes=30,
        priority="high",
        category="walk",
    )
    assert task.completed is False

    task.mark_complete()

    assert task.completed is True


def test_adding_task_to_pet_increases_task_count():
    pet = Pet(name="Toby", species="dog", age=20)
    task = Task(
        name="Feed breakfast",
        description="Dry food",
        duration_minutes=10,
        priority="medium",
        category="feeding",
    )
    assert len(pet.tasks) == 0

    pet.add_task(task)

    assert len(pet.tasks) == 1


from datetime import date, time

from pawpal_system import Owner, Preferences, Scheduler


def _plan(*tasks, day_end=time(18, 0)):
    pet = Pet("Toby", "dog", 3)
    for t in tasks:
        pet.add_task(t)
    owner = Owner("Sam", Preferences(time(8, 0), day_end), pets=[pet])
    return Scheduler(owner).generate_plan(date(2026, 1, 1))


def _task(name, minutes=10, priority="medium"):
    return Task(name, "", minutes, priority, "general")


def test_sorting_orders_by_priority_then_duration_then_name():
    plan = _plan(
        _task("low", 5, "low"),
        _task("med-long", 30),
        _task("high", 60, "high"),
        _task("med-b", 10),
        _task("med-a", 10),
    )
    assert [s.task.name for s in plan.scheduled] == [
        "high", "med-a", "med-b", "med-long", "low"]


def test_scheduled_tasks_are_back_to_back_without_overlap():
    plan = _plan(_task("a", 30, "high"), _task("b", 15))
    first, second = plan.scheduled
    assert (first.start_time, first.end_time) == (time(8, 0), time(8, 30))
    assert second.start_time == first.end_time


def test_task_that_does_not_fit_is_skipped_but_shorter_one_still_fits():
    plan = _plan(_task("big", 50, "high"), _task("huge", 50), _task("tiny", 5, "low"),
                 day_end=time(9, 0))
    assert [s.task.name for s in plan.scheduled] == ["big", "tiny"]
    assert [s.task.name for s in plan.skipped] == ["huge"]


def test_completed_tasks_and_empty_pets_yield_empty_plan():
    done = _task("done")
    done.mark_complete()
    assert _plan(done).scheduled == []
    assert _plan().scheduled == []


def test_duplicate_tasks_are_not_flagged_yet():
    # Characterization: no duplicate detection exists; update once it does.
    plan = _plan(_task("Walk", 30), _task("Walk", 30))
    assert [s.task.name for s in plan.scheduled] == ["Walk", "Walk"]
    assert plan.skipped == []
