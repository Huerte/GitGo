from pygitgo.utils.colors import success, warning, error, info
from pygitgo.exceptions import GitCommandError
from pygitgo.utils.executor import run_command
import sys


def undo_commit():
    try:
        run_command(["git", "reset", "--soft", "HEAD~"])
        success("\nSuccess! Your last commit is undone. Your files are safe.\n")
    except GitCommandError as e:
        error("\nFailed! You might not have any previous commits to undo yet.")
        error(f"Details: {e}\n")
        sys.exit(1)
    

def undo_add():
    try:
        run_command(["git", "reset", "HEAD"])
        success("\nSuccess! Files are no longer ready to commit.\n")
    except GitCommandError as e:
        error(f"\n{e}\n")
        sys.exit(1)


def undo_changes():
    warning("\nDANGER: This will permanently delete all your new edits and new files!")
    confirm = input("Are you sure you want to throw away all changes? (y/n): ")
    if confirm.lower() != "y":
        info("\nCanceled. Your files are safe.\n")
        return
    try:
        run_command(["git", "reset", "--hard", "HEAD"], loading_msg="Throwing away edits...")
        run_command(["git", "clean", "-fd"], loading_msg="Removing new files...")
        
        success("\nSuccess! All changes are completely gone. You have a clean start.\n")
    except GitCommandError as e:
        error(f"\n{e}\n")
        sys.exit(1)


def undo_operations(args):
    action = args.action

    if action == "commit":
        undo_commit()
    elif action == "add":
        undo_add()
    elif action == "changes":
        undo_changes()
    else:
        error(f"\nUnknown undo operation: {action}\n")
        sys.exit(1)
