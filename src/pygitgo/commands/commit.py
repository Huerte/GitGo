from pygitgo.utils.colors import (
    info, success, warning,
    GREEN, YELLOW, CYAN, RED, BLUE, RESET
)
from pygitgo.commands.git_operations import get_status_content, get_current_branch, git_push
from pygitgo.utils.executor import run_command
from yaspin import yaspin
from pathlib import Path
import subprocess
import sys


CONVENTIONAL_COMMIT_MAP = {
    "A": "feat",
    "AM": "feat",
    "??": "feat",
    "M": "fix",
    "MM": "fix",
    "D": "chore",
    "R": "refactor",
    "RM": "refactor",
    "C": "chore",

    "UU": None,
    "UD": None,
    "DU": None,
    "AA": None,
    "DD": None,
    "!!": None, 
    " ": None,  
}

DOCS_EXTENSIONS = [".md", ".rst", ".txt"]

ACTION_DESCRIPTION_MAP = {
    "feat":     "add",
    "fix":      "update",
    "chore":    "remove",
    "refactor": "rename",
}

COMMIT_TYPE_COLOR = {
    "feat":     GREEN,    
    "fix":      YELLOW,
    "docs":     CYAN,
    "chore":    RED,
    "refactor": BLUE,
}

def generate_messages(status_code, file_path):
    commit_type = CONVENTIONAL_COMMIT_MAP.get(status_code, None)
    if not commit_type:
        return None
    
    path = Path(file_path)
    file_name = path.name
    file_ext = path.suffix

    action_description = ACTION_DESCRIPTION_MAP.get(commit_type, "chore")

    if file_ext in DOCS_EXTENSIONS:
        commit_type = "docs"
    
    return f"{commit_type}: {action_description} {file_name}"

def atomic_commit(change_list):
    files = [str(file_path) for _, file_path, msg in change_list if msg]
    messages = [msg for _, _, msg in change_list if msg]

    if not files:
        warning("\nNo files to commit.\n")
        return

    final_msg = "\n".join(messages)

    with yaspin(text=f"Committing {len(files)} files...", color="cyan") as spinner:
        try:
            run_command(['git', 'add', *files])
            run_command(['git', 'commit', '-m', final_msg])
            spinner.ok("✔ Commit created")
        except subprocess.CalledProcessError:
            spinner.fail("✖ Commit failed")
            sys.exit(1)
    

def commit_operation():
    
    status_content = get_status_content()

    if not status_content.strip():
        warning("\nNo changes to commit.\n")
        sys.exit(0)

    changes = [line.strip().split(maxsplit=1) for line in status_content.split('\n') if line.strip()]

    for i, change in enumerate(changes):
        if len(change) == 2:
            placeholder_msg = generate_messages(change[0], change[1])
            changes[i].append(placeholder_msg)

    info("\nThe following changes will be committed:")
    has_valid_commits = False
    for change in changes:
        if len(change) == 3 and change[2]:
            msg = change[2]
            code, description = msg.split(': ', 1)
            print(f"{COMMIT_TYPE_COLOR.get(code, RESET)}{code}{RESET}: {description}")
            has_valid_commits = True

    if not has_valid_commits:
        warning("\nNo valid files to automatically commit.\n")
        sys.exit(0)

    user_prompt = input("\nProceed with these commits? (y/n): ").lower().strip()
    if user_prompt != 'y':
        warning("\nCommit operation cancelled.\n")
        sys.exit(0)
    
    atomic_commit(changes)

    user_prompt = input("\nPush changes to remote? (y/n): ").lower().strip()
    if user_prompt != 'y':
        print("\n" + ("=" * 90))
        success("MISSION COMPLETE — ALL COMMITS CREATED LOCALLY!\nAWAITING FOR YOUR NEXT ORDERS.\n\n")
        sys.exit(0)
    
    current_branch = get_current_branch()
    git_push(current_branch)
    
    print("\n" + ("=" * 90))
    success("MISSION COMPLETE — ALL COMMITS CREATED AND PUSHED!\nAWAITING FOR YOUR NEXT ORDERS.\n\n")

