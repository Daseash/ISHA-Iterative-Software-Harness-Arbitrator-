#!/usr/bin/env python3
"""
Taskmaster CLI — Lightweight, zero-dependency task manager for ISHA.
Compatible with eyaltoledano/claude-task-master tasks.json schema.
"""

import argparse
import json
import os
import sys
from pathlib import Path

# Ensure utf-8 output on Windows console
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

DEFAULT_TASKS_FILE = Path(__file__).resolve().parent.parent / ".taskmaster" / "tasks.json"
if not DEFAULT_TASKS_FILE.exists():
    ALT = Path(__file__).resolve().parent / ".taskmaster" / "tasks.json"
    if ALT.exists():
        DEFAULT_TASKS_FILE = ALT


def load_tasks(path: Path) -> dict:
    if not path.exists():
        return {"project": {"name": "ISHA"}, "tasks": []}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_tasks(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def cmd_list(args):
    data = load_tasks(DEFAULT_TASKS_FILE)
    tasks = data.get("tasks", [])
    if not tasks:
        print("No tasks found.")
        return

    print(f"\n[TASKMASTER] {data.get('project', {}).get('name', 'Project')} Task Roadmap\n" + "=" * 65)
    for t in tasks:
        status_char = "[X]" if t.get("status") == "done" else ("[~]" if t.get("status") == "in-progress" else "[ ]")
        priority = f"[{t.get('priority', 'medium').upper()}]"
        dep = f" (deps: {t.get('dependencies')})" if t.get("dependencies") else ""
        print(f" {status_char} #{t['id']:<2} {priority:<8} {t['title']}{dep}")
    print("=" * 65 + "\n")


def cmd_next(args):
    data = load_tasks(DEFAULT_TASKS_FILE)
    tasks = data.get("tasks", [])
    completed_ids = {t["id"] for t in tasks if t.get("status") == "done"}

    for t in tasks:
        if t.get("status") == "in-progress":
            print(f"\n>>> CURRENT IN-PROGRESS TASK:")
            print(f"  #{t['id']}: {t['title']}")
            print(f"  Description: {t.get('description')}")
            print(f"  Details: {t.get('details')}\n")
            return

    for t in tasks:
        if t.get("status") == "pending":
            deps = t.get("dependencies", [])
            if all(d in completed_ids for d in deps):
                print(f"\n>>> NEXT ACTIONABLE TASK:")
                print(f"  #{t['id']}: {t['title']} [Priority: {t.get('priority', 'medium')}]")
                print(f"  Description: {t.get('description')}")
                print(f"  Details: {t.get('details')}\n")
                return

    print("\n[ALL TASKS COMPLETE OR WAITING ON DEPENDENCIES]\n")


def cmd_set(args):
    data = load_tasks(DEFAULT_TASKS_FILE)
    tasks = data.get("tasks", [])
    found = False
    for t in tasks:
        if str(t["id"]) == str(args.task_id):
            old = t.get("status")
            t["status"] = args.status
            found = True
            print(f"Updated Task #{args.task_id} status: {old} -> {args.status}")
            break
    if not found:
        print(f"Task #{args.task_id} not found.")
        sys.exit(1)
    save_tasks(DEFAULT_TASKS_FILE, data)


def cmd_show(args):
    data = load_tasks(DEFAULT_TASKS_FILE)
    for t in data.get("tasks", []):
        if str(t["id"]) == str(args.task_id):
            print(json.dumps(t, indent=2))
            return
    print(f"Task #{args.task_id} not found.")


def main():
    parser = argparse.ArgumentParser(description="ISHA Taskmaster CLI")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("list", help="List all tasks")
    sub.add_parser("next", help="Show next actionable task")

    p_set = sub.add_parser("set", help="Set task status")
    p_set.add_argument("task_id", help="Task ID")
    p_set.add_argument("status", choices=["pending", "in-progress", "done"], help="New status")

    p_show = sub.add_parser("show", help="Show task details")
    p_show.add_argument("task_id", help="Task ID")

    args = parser.parse_args()
    if args.command == "list" or not args.command:
        cmd_list(args)
    elif args.command == "next":
        cmd_next(args)
    elif args.command == "set":
        cmd_set(args)
    elif args.command == "show":
        cmd_show(args)


if __name__ == "__main__":
    main()
