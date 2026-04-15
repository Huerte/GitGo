from pygitgo.utils.colors import success, warning, error
from pygitgo.utils.executor import run_command
from pick import pick
import subprocess
import sys


STATUS_LABELS = {
    "M": "modified",
    "A": "added",
    "D": "deleted",
    "R": "renamed",
    "??": "new file",
}


def get_changed_files():
    status = run_command(["git", "status", "--porcelain"], allow_fail=True)
    if isinstance(status, subprocess.CalledProcessError) or not status.strip():
        return []

    files = []
    for line in status.strip().splitlines():
        if len(line) < 3:
            continue
        status_code = line[:2].strip()
        filepath = line[3:].strip()
        label = STATUS_LABELS.get(status_code, "changed")
        files.append({"status": status_code, "label": label, "path": filepath})

    return files


def display_file_picker(files):
    options = [f"({f['label']}) {f['path']}" for f in files]

    selected = pick(
        options,
        "Select files to stage (SPACE to toggle, ENTER to confirm):",
        multiselect=True,
        min_selection_count=0
    )

    return [files[idx]["path"] for _, idx in selected]


def selective_stage(selected_files):
    for filepath in selected_files:
        run_command(["git", "add", "--", filepath])
    success(f"\n{len(selected_files)} file(s) staged for commit.")
