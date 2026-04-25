from models.task import Task
from db.repositories import task_repo
from utils.validators import validate_task_title, validate_task_description, validate_priority, validate_task_id


def add_task(user_id: int, title: str, description: str | None = None, priority: int = 2, due_date: str | None = None) -> int:
    title = validate_task_title(title)
    if description:
        description = validate_task_description(description)
    task = Task(user_id=user_id, title=title, description=description, priority=priority, due_date=due_date)
    return task_repo.create_task(task)


def list_tasks(user_id: int, priority_filter: int | None = None) -> list[Task]:
    tasks = task_repo.get_tasks(user_id, status="pending")
    if priority_filter is not None:
        tasks = [t for t in tasks if t.priority == priority_filter]
    return tasks


def mark_done(user_id: int, task_id_str: str) -> bool:
    task_id = validate_task_id(task_id_str)
    return task_repo.update_task_status(task_id, user_id, "done")


def delete_task(user_id: int, task_id_str: str) -> bool:
    task_id = validate_task_id(task_id_str)
    return task_repo.update_task_status(task_id, user_id, "deleted")


def change_priority(user_id: int, task_id_str: str, priority_str: str) -> bool:
    task_id = validate_task_id(task_id_str)
    priority = validate_priority(priority_str)
    return task_repo.update_task_priority(task_id, user_id, priority)
