from pygitgo.commands.git_operations import get_status_content, get_current_branch, git_push
from pygitgo.utils.colors import (
    info, success, warning, error,
    GREEN, YELLOW, CYAN, RED, BLUE, RESET
)
from pygitgo.utils.executor import run_command
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
    
    file_name, file_ext = file_path.split('/')[-1].split('.')
    action_description = ACTION_DESCRIPTION_MAP.get(commit_type, "chore")

    if file_ext in DOCS_EXTENSIONS:
        commit_type = "docs"
    
    return f"{commit_type}: {action_description} {file_name}.{file_ext}"

def commit_changes(file_path, msg):
    try:
        file_path = Path(file_path)
        run_command(['git', 'add', str(file_path)], loading_msg=f"Staging {file_path}...")
        run_command(['git', 'commit', '-m', msg], loading_msg=f"Committing {file_path}...")
    except subprocess.CalledProcessError as e:
        error("Error occurred while staging file.")
        sys.exit(1)

def atomic_commit(change_list):
    
    print("Committing changes...")
    for _, file_path, msg in change_list:
        if msg:
            commit_changes(file_path, msg)

def commit_operation():
    
    status_content = get_status_content()

    changes = [line.strip().split() for line in status_content.split('\n')]

    for i, change in enumerate(changes):
        placeholder_msg = generate_messages(change[0], change[1])
        changes[i].append(placeholder_msg)

    info("\nThe following changes will be committed:")
    for _, _, msg in changes:
        if msg:
            code, description = msg.split(': ')
            print(f"{COMMIT_TYPE_COLOR.get(code, RESET)}{code}{RESET}: {description}")


    user_prompt = input("\nProceed with these commits? (y/n): ").lower().strip()
    if user_prompt != 'y':
        warning("Commit operation cancelled.")
        exit(0)
    
    atomic_commit(changes)
    success("Successfully committed changes.")

    user_prompt = input("\nPush changes to remote? (y/n): ").lower().strip()
    if user_prompt != 'y':
        exit(0)
    
    current_branch = get_current_branch()
    git_push(current_branch)
    success("Changes pushed successfully.")

