from pygitgo.commands.git_branch import get_current_branch
from pygitgo.utils.colors import success, warning, info, error
from pygitgo.exceptions import GitCommandError, GitGoError
from pygitgo.utils.executor import run_command
import sys


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

    reset_done = False
    try:
        run_command(["git", "reset", "--hard", "HEAD"], loading_msg="Throwing away edits...")
        reset_done = True
        run_command(["git", "clean", "-fd"], loading_msg="Removing new files...")
        success("Working tree reset. All changes discarded.")

    except KeyboardInterrupt:
        print()
        if reset_done:
            warning("Interrupted during file removal. Finishing cleanup...")
            try:
                run_command(["git", "clean", "-fd"])
                success("Working tree reset. All changes discarded.")
            except GitCommandError:
                warning("Could not finish cleanup. Run 'git clean -fd' manually.")
        else:
            success("Reset canceled before any changes were made. Your files are safe.")
        sys.exit(130)


def undo_link():
    try:
        run_command(["git", "remote", "remove", "origin"])
        success("Remote 'origin' removed.")
    except GitCommandError as e:
        raise GitGoError(
            f"Could not remove remote 'origin'. Is one set? Details: {e}"
        )

    try:
        run_command(["git", "reset", "--soft", "HEAD~"])
        success("Initial commit undone. Files are back to staged, ready to re-link.")
    except GitCommandError:
        info("Remote removed. Could not undo the commit (none or multiple found).")
        info("Run 'gitgo undo commit' separately if needed.")


def undo_push():
    try:
        branch = get_current_branch()
    except GitCommandError as e:
        raise GitGoError(f"Could not determine the current branch: {e}")

    error("DANGER: This force-pushes to the remote. Other collaborators will be affected.")
    warning("Only use this if no one else has pulled the commit you are reverting.")
    confirm = input("Are you sure you want to undo the last push? (y/n): ")
    if confirm.lower() != "y":
        info("Canceled. Remote is unchanged.")
        return

    try:
        run_command(["git", "reset", "--soft", "HEAD~"], loading_msg="Reverting last commit locally...")
    except GitCommandError as e:
        raise GitGoError(f"Undo failed — no previous commit to revert. Details: {e}")

    try:
        run_command(
            ["git", "push", "--force", "origin", branch],
            loading_msg=f"Force-pushing reverted state to '{branch}'..."
        )
        success(f"Last push reverted. Remote '{branch}' is back to the previous commit.")
        info("Your files are still staged locally. Edit and push again when ready.")
    except GitCommandError as e:
        warning("Local commit was undone, but the force-push failed.")
        warning(f"Run manually: git push --force origin {branch}")
        raise GitGoError(f"Force-push failed: {e}")


def undo_operation(args):
    action = args.action

    if action == "commit":
        undo_commit()
    elif action == "add":
        undo_add()
    elif action == "changes":
        undo_changes()
    elif action == "link":
        undo_link()
    elif action == "push":
        undo_push()
    else:
        raise GitGoError(f"Unknown undo operation: {action}")