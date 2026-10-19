from pygitgo.utils.cli_io import success, warning, info, confirm, danger, banner, write
from pygitgo.commands.git_branch import get_current_branch
from pygitgo.exceptions import GitCommandError, GitGoError
from pygitgo.commands.git_core import ensure_inside_git_repository
from pygitgo.utils.executor import run_command
import sys
import time


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
    try:
        staged = run_command(["git", "diff", "--cached", "--name-only"]).strip()
        if not staged:
            info("There are no staged files to unstage.")
            return False
    except GitCommandError:
        pass

    run_command(["git", "reset", "HEAD"], loading_msg="Clearing staging area...", ok_text="Staging cleared. Files are back to unstaged.")
    return True


def undo_changes(permanent=False):
    from pygitgo.commands.staging import get_changed_files
    try:
        files = get_changed_files()
    except GitCommandError:
        files = []
    if not files:
        info("Nothing to discard. Your working tree is already clean.")
        return False

    warning(f"This will discard {len(files)} changed file(s):")
    for f in files[:10]:
        write(f"  {f['label']:<10} {f['path']}")
    if len(files) > 10:
        write(f"  ... and {len(files) - 10} more")
    write()

    if permanent:
        danger("This will permanently delete all your unsaved edits and new files.")
        warning("There is no way to recover them after this step.")
        if not confirm("Delete all unsaved changes? Type 'y' to confirm: ", destructive=True):
            info("Canceled. Your files are safe.")
            return False
    else:
        info("GitGo saves a backup first, so you can get everything back with 'gitgo state load'.")
        if not confirm("Discard these changes? (y/n): "):
            info("Canceled. Your files are safe.")
            return False

        stamp = time.strftime("%Y-%m-%d %H:%M:%S")
        try:
            run_command(
                ["git", "stash", "push", "--include-untracked", "-m", f"GitGo undo-changes backup ({stamp})"],
                loading_msg="Saving a backup, then clearing changes...",
                ok_text="Changes discarded. A backup was saved.",
            )
        except GitCommandError as e:
            raise GitGoError(
                f"Could not back up your changes, so nothing was discarded.\n"
                f"Use 'gitgo undo changes --permanent' to discard without a backup.\nDetails: {e}"
            )
        info("Find the backup with 'gitgo state list' (named 'GitGo undo-changes backup').")
        return True

    reset_done = False
    try:
        run_command(["git", "reset", "--hard", "HEAD"], loading_msg="Throwing away edits...", ok_text="Edits discarded.")
        reset_done = True
        run_command(["git", "clean", "-fd"], loading_msg="Removing new files...", ok_text="Working tree reset. All changes discarded.")
        return True

    except KeyboardInterrupt:
        write()
        if reset_done:
            warning("Interrupted during file removal. Finishing cleanup...")
            try:
                run_command(["git", "clean", "-fd"])
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

    try:
        unpushed = int(run_command(["git", "rev-list", "--count", f"origin/{branch}..HEAD"]).strip() or 0)
        behind = int(run_command(["git", "rev-list", "--count", f"HEAD..origin/{branch}"]).strip() or 0)
    except (GitCommandError, ValueError):
        raise GitGoError(f"Could not compare with 'origin/{branch}'. Has this branch been pushed yet?")

    if unpushed > 0:
        raise GitGoError(
            f"You have {unpushed} commit(s) on '{branch}' that were never pushed.\n"
            "'undo push' removes only the last pushed commit and cannot skip those.\n"
            "Push them first, or run 'gitgo undo commit' to remove them."
        )
    if behind > 0:
        raise GitGoError(
            f"The remote '{branch}' has {behind} newer commit(s) than your local branch.\n"
            "Run 'gitgo pull' first so you do not remove someone else's work."
        )

    last_commit = run_command(["git", "log", "-1", "--format=%h %s"]).strip()
    danger("This will remove this commit from GitHub using a force-push:")
    write(f"  {last_commit}")
    warning("Only the last commit is removed, even if your last push had several.")
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
            ["git", "push", "--force-with-lease", "origin", branch],
            loading_msg=f"Force-pushing reverted state to '{branch}'...",
            ok_text=f"Last push reverted. Remote '{branch}' is back to the previous commit."
        )
        info("Your files are still staged locally. Edit and push again when ready.")
        return True
    except GitCommandError as e:
        warning("Local and remote have diverged!")
        warning("The local commit was reverted, but force-pushing to the remote failed.")
        warning(f"To recover, run manually: git push --force-with-lease origin {branch}")
        raise GitGoError(f"Force-push failed: {e}")


def undo_operation(args):
    ensure_inside_git_repository()
    action = args.action

    success_flag = False
    if action == "commit":
        success_flag = undo_commit()
    elif action == "add":
        success_flag = undo_add()
    elif action == "changes":
        success_flag = undo_changes(permanent=getattr(args, 'permanent', False) is True)
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