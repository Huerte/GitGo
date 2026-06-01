from pygitgo.exceptions import GitCommandError, GitGoError
from pygitgo.utils.colors import success, warning, info, error
from pygitgo.utils.executor import run_command


def undo_commit():
    try:
        run_command(["git", "reset", "--soft", "HEAD~"])
        success("Last commit undone. Files are untouched.")
    except GitCommandError as e:
        raise GitGoError(
            f"Undo failed — no previous commit to revert. Details: {e}"
        )


def undo_add():
    run_command(["git", "reset", "HEAD"])
    success("Staging cleared. Files are back to unstaged.")


def undo_changes():
    error("DANGER: This will permanently delete all your new edits and new files!")
    warning("This action cannot be undone.")
    confirm = input("Are you sure you want to throw away all changes? (y/n): ")
    if confirm.lower() != "y":
        info("Canceled. Your files are safe.")
        return

    run_command(["git", "reset", "--hard", "HEAD"], loading_msg="Throwing away edits...")
    run_command(["git", "clean", "-fd"], loading_msg="Removing new files...")

    success("Working tree reset. All changes discarded.")


def undo_operation(args):
    action = args.action

    if action == "commit":
        undo_commit()
    elif action == "add":
        undo_add()
    elif action == "changes":
        undo_changes()
    else:
        raise GitGoError(f"Unknown undo operation: {action}")