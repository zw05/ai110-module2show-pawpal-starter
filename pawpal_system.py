from dataclasses import dataclass, field
from datetime import date, time

PRIORITY_ORDER = {"high": 3, "medium": 2, "low": 1}


def _to_minutes(t: time) -> int:
    return t.hour * 60 + t.minute


def _to_time(minutes: int) -> time:
    return time(minutes // 60, minutes % 60)


@dataclass(eq=False)
class Task:
    """A single care activity for a pet."""

    name: str
    description: str
    duration_minutes: int
    priority: str
    category: str
    completed: bool = False

    def __post_init__(self) -> None:
        """Normalize priority and reject invalid priority or duration values."""
        self.priority = self.priority.lower()
        if self.priority not in PRIORITY_ORDER:
            raise ValueError(
                f"priority must be one of {list(PRIORITY_ORDER)}, got {self.priority!r}"
            )
        if self.duration_minutes <= 0:
            raise ValueError("duration_minutes must be positive")

    def mark_complete(self) -> None:
        """Mark this task as completed."""
        self.completed = True


@dataclass(eq=False)
class Pet:
    """Pet details and the tasks that belong to this pet."""

    name: str
    species: str
    age: int
    notes: str = ""
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Add a task to this pet's task list."""
        self.tasks.append(task)

    def remove_task(self, task: Task) -> None:
        """Remove a task from this pet's task list."""
        self.tasks.remove(task)


@dataclass
class Preferences:
    day_start: time
    day_end: time
    preferred_categories: list[str] = field(default_factory=list)
    max_task_minutes: int | None = None

    def available_minutes(self) -> int:
        """Return the number of minutes between day start and day end."""
        return max(0, _to_minutes(self.day_end) - _to_minutes(self.day_start))


@dataclass
class Owner:
    """Manages multiple pets and exposes all of their tasks."""

    name: str
    preferences: Preferences
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner's pets."""
        self.pets.append(pet)

    def remove_pet(self, pet: Pet) -> None:
        """Remove a pet from this owner's pets."""
        self.pets.remove(pet)

    def get_all_tasks(self) -> list[tuple[Pet, Task]]:
        """Every task across every pet, paired with the pet it belongs to."""
        return [(pet, task) for pet in self.pets for task in pet.tasks]


@dataclass
class ScheduledTask:
    task: Task
    pet: Pet
    start_time: time
    end_time: time
    reason: str


@dataclass
class SkippedTask:
    task: Task
    pet: Pet
    reason: str


@dataclass
class DailyPlan:
    date: date
    scheduled: list[ScheduledTask] = field(default_factory=list)
    skipped: list[SkippedTask] = field(default_factory=list)

    def total_minutes(self) -> int:
        """Return the total duration of all scheduled tasks."""
        return sum(s.task.duration_minutes for s in self.scheduled)

    def summary(self) -> str:
        """Return a readable text summary of scheduled and skipped tasks."""
        lines = [f"Plan for {self.date.isoformat()} ({self.total_minutes()} min scheduled)"]
        for s in self.scheduled:
            lines.append(
                f"  {s.start_time:%H:%M}-{s.end_time:%H:%M}  {s.pet.name}: "
                f"{s.task.name} [{s.task.priority}] - {s.reason}"
            )
        if self.skipped:
            lines.append("Skipped:")
            for s in self.skipped:
                lines.append(f"  {s.pet.name}: {s.task.name} [{s.task.priority}] - {s.reason}")
        return "\n".join(lines)


@dataclass
class Scheduler:
    """Builds a daily plan from the owner's tasks across all pets.

    Tasks are ranked by priority (high first), then by duration (shorter
    first). They are placed back to back from the start of the day; a task
    that doesn't fit is skipped and later, shorter tasks may still fit.
    """

    owner: Owner

    def generate_plan(self, plan_date: date | None = None) -> DailyPlan:
        """Build a plan for the given date (default today) from all incomplete tasks."""
        plan = DailyPlan(date=plan_date or date.today())
        pairs = [(p, t) for p, t in self.owner.get_all_tasks() if not t.completed]

        remaining = self.owner.preferences.available_minutes()
        cursor = _to_minutes(self.owner.preferences.day_start)

        for pet, task in self._rank_tasks(pairs):
            if self._fits_constraints(task, remaining):
                start, end = cursor, cursor + task.duration_minutes
                plan.scheduled.append(
                    ScheduledTask(
                        task=task,
                        pet=pet,
                        start_time=_to_time(start),
                        end_time=_to_time(end),
                        reason=self._explain(task, True, remaining),
                    )
                )
                cursor = end
                remaining -= task.duration_minutes
            else:
                plan.skipped.append(
                    SkippedTask(
                        task=task,
                        pet=pet,
                        reason=self._explain(task, False, remaining),
                    )
                )
        return plan

    def _rank_tasks(self, pairs: list[tuple[Pet, Task]]) -> list[tuple[Pet, Task]]:
        """Sort (pet, task) pairs by priority, then duration, then name."""
        return sorted(
            pairs,
            key=lambda pt: (
                -PRIORITY_ORDER[pt[1].priority],
                pt[1].duration_minutes,
                pt[1].name,
            ),
        )

    def _fits_constraints(self, task: Task, minutes_remaining: int) -> bool:
        """Return True if the task is within the task-length cap and remaining time."""
        cap = self.owner.preferences.max_task_minutes
        if cap is not None and task.duration_minutes > cap:
            return False
        return task.duration_minutes <= minutes_remaining

    def _explain(self, task: Task, scheduled: bool, minutes_remaining: int) -> str:
        """Return a short reason the task was scheduled or skipped."""
        if scheduled:
            reason = f"{task.priority} priority, {task.duration_minutes} min"
            if task.category in self.owner.preferences.preferred_categories:
                reason += ", preferred category"
            return reason

        cap = self.owner.preferences.max_task_minutes
        if cap is not None and task.duration_minutes > cap:
            return f"{task.duration_minutes} min exceeds the {cap} min task limit"
        return (
            f"needs {task.duration_minutes} min but only {minutes_remaining} min left"
        )
