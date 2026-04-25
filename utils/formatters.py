from models.task import Task
from models.reminder import Reminder
from models.whoop_log import WhoopLog

PRIORITY_EMOJI = {1: "🔴", 2: "🟡", 3: "🟢"}
PRIORITY_LABEL = {1: "High", 2: "Medium", 3: "Low"}


def format_task(task: Task, index: int | None = None) -> str:
    prefix = f"{index}. " if index is not None else ""
    priority = PRIORITY_EMOJI.get(task.priority, "⚪")
    due = f" | Due: {task.due_date}" if task.due_date else ""
    desc = f"\n   ↳ {task.description}" if task.description else ""
    return f"{prefix}{priority} <b>{task.title}</b> [ID:{task.id}]{due}{desc}"


def format_task_list(tasks: list[Task]) -> str:
    if not tasks:
        return "No pending tasks."
    lines = ["<b>Your Tasks:</b>"]
    for i, task in enumerate(tasks, 1):
        lines.append(format_task(task, index=i))
    return "\n".join(lines)


def format_reminder(reminder: Reminder, index: int | None = None) -> str:
    prefix = f"{index}. " if index is not None else ""
    return f"{prefix}⏰ <b>{reminder.message}</b>\n   When: {reminder.remind_at} UTC [ID:{reminder.id}]"


def format_reminder_list(reminders: list[Reminder]) -> str:
    if not reminders:
        return "No pending reminders."
    lines = ["<b>Your Reminders:</b>"]
    for i, r in enumerate(reminders, 1):
        lines.append(format_reminder(r, index=i))
    return "\n".join(lines)


def format_whoop_log(log: WhoopLog) -> str:
    parts = [f"<b>Whoop Log — {log.log_date}</b>"]
    if log.recovery_score is not None:
        emoji = "🟢" if log.recovery_score >= 67 else ("🟡" if log.recovery_score >= 34 else "🔴")
        parts.append(f"Recovery: {emoji} {log.recovery_score}/100")
    if log.hrv is not None:
        parts.append(f"HRV: {log.hrv} ms")
    if log.rhr is not None:
        parts.append(f"Resting HR: {log.rhr} bpm")
    if log.sleep_hours is not None:
        parts.append(f"Sleep: {log.sleep_hours}h")
    if log.sleep_quality is not None:
        parts.append(f"Sleep Quality: {log.sleep_quality}/100")
    if log.strain_score is not None:
        parts.append(f"Strain: {log.strain_score}/21")
    if log.notes:
        parts.append(f"Notes: {log.notes}")
    return "\n".join(parts)


def format_whoop_stats(logs: list[WhoopLog]) -> str:
    if not logs:
        return "No Whoop data logged yet."
    lines = ["<b>Whoop Stats (Last 7 Days):</b>"]
    for log in logs:
        lines.append(format_whoop_log(log))
        lines.append("")
    return "\n".join(lines).strip()
