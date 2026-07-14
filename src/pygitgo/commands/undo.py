from pygitgo.utils.cli_io import success, warning, info, confirm, danger, banner
from pygitgo.commands.git_branch import get_current_branch
from pygitgo.exceptions import GitCommandError, GitGoError
from pygitgo.utils.executor import run_command
import sys


def undo_commit():
    try:
        run_command(["git", "reset", "--soft", "HEAD~"], loading_msg="Undoing last commit...", ok_text="Last commit undone. Files are untouched.")
    except GitCommandError:
        try:
            run_command(["git", "update-ref", "-d", "HEAD"], loading_msg="Undoing initial commit...", ok_text="Initial commit undone. Files are back to staged.")
        except GitCommandError as e:
            raise GitGoError(f"Undo failed. Details: {e}")
    return True


def undo_add():
    run_command(["git", "reset", "HEAD"], loading_msg="Clearing staging area...", ok_text="Staging cleared. Files are back to unstaged.")
    return True


def undo_changes():
    danger("This will permanently delete all your unsaved edits and new files.")
    warning("There is no way to recover them after this step.")
    if not confirm("Delete all unsaved changes? Type 'y' to confirm: ", destructive=True):
        info("Canceled. Your files are safe.")
        return False

    reset_done = False
    try:
        run_command(["git", "reset", "--hard", "HEAD"], loading_msg="Throwing away edits...", ok_text="Edits discarded.")
        reset_done = True
        run_command(["git", "clean", "-fd"], loading_msg="Removing new files...", ok_text="Working tree reset. All changes discarded.")
        return True

    except KeyboardInterrupt:
        print()
        if reset_done:
            warning("Interrupted during file removal. Finishing cleanup...")
            try:
                run_command(["git", "clean", "-fd"], loading_msg="Removing new files...", ok_text="Working tree reset. All changes discarded.")
            except GitCommandError:
                warning("Could not finish cleanup. Run 'git clean -fd' manually.")
        else:
            success("Reset canceled before any changes were made. Your files are safe.")
        sys.exit(130)


def undo_link():
    try:
        run_command(["git", "remote", "remove", "origin"], loading_msg="Removing remote 'origin'...", ok_text="Remote 'origin' removed.")
    except GitCommandError as e:
        raise GitGoError(
            f"Could not remove remote 'origin'. Is one set? Details: {e}"
        )

    try:
        run_command(["git", "reset", "--soft", "HEAD~"], loading_msg="Undoing initial commit...", ok_text="Initial commit undone. Files are back to staged, ready to re-link.")
    except GitCommandError:
        info("Remote removed. Could not undo the commit (none or multiple found).")
        info("Run 'gitgo undo commit' separately if needed.")
    return True


def undo_pull():
    from pygitgo.commands.git_core import abort_pull_conflict
    return abort_pull_conflict()


def undo_push():
    try:
        branch = get_current_branch(safe=True)
    except GitCommandError as e:
        raise GitGoError(f"Could not determine the current branch: {e}")

    danger("This will remove your last upload from GitHub using a force-push.")
    warning("If anyone else already downloaded that commit, this will cause problems for them.")
    warning("Only continue if you are the only person working on this branch.")
    if not confirm("Remove the last push from GitHub? Type 'y' to confirm: ", destructive=True):
        info("Canceled. Remote is unchanged.")
        return False

    try:
        run_command(["git", "reset", "--soft", "HEAD~"], loading_msg="Reverting last commit locally...", ok_text="Last commit reverted locally.")
    except GitCommandError as e:
        raise GitGoError(f"Undo failed — no previous commit to revert. Details: {e}")

    try:
        run_command(
            ["git", "push", "--force", "origin", branch],
            loading_msg=f"Force-pushing reverted state to '{branch}'...",
            ok_text=f"Last push reverted. Remote '{branch}' is back to the previous commit."
        )
        info("Your files are still staged locally. Edit and push again when ready.")
        return True
    except GitCommandError as e:
        warning("Local and remote have diverged!")
        warning("The local commit was reverted, but force-pushing to the remote failed.")
        warning(f"To recover, run manually: git push --force origin {branch}")
        raise GitGoError(f"Force-push failed: {e}")


def undo_operation(args):
    action = args.action

    success_flag = False
    if action == "commit":
        success_flag = undo_commit()
    elif action == "add":
        success_flag = undo_add()
    elif action == "changes":
        success_flag = undo_changes()
    elif action == "link":
        success_flag = undo_link()
    elif action == "push":
        success_flag = undo_push()
    elif action == "pull":
        success_flag = undo_pull()
    else:
        raise GitGoError(f"Unknown undo operation: {action}")

    if success_flag:
        banner("ACTION ROLLBACK. WORKSPACE RESTORED.", "PREVIOUS STATE RE-ESTABLISHED SUCCESSFULLY.")