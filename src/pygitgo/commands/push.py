from pygitgo.commands.staging import get_changed_files, display_file_picker, selective_stage
from pygitgo.commands.git_branch import git_new_branch, get_current_branch, is_branch_exist
from pygitgo.utils.cli_io import info, warning, success, confirm, banner
from pygitgo.commands.git_core import git_commit, git_push
from pygitgo.exceptions import GitCommandError, GitGoError
from pygitgo.commands.jump import jump_operation
from pygitgo.utils.executor import run_command
from pygitgo.utils.config import get_config
from argparse import Namespace
import sys


def _push_interrupt_cleanup(original_branch, original_head, created_branch):
    try:
        current_branch = get_current_branch()
    except Exception:
        current_branch = original_branch

    try:
        current_head = run_command(["git", "rev-parse", "HEAD"]).strip()
    except GitCommandError:
        current_head = original_head

    commit_was_made = bool(original_head and current_head and current_head != original_head)

    if commit_was_made:
        info(f"Commit was saved locally on '{current_branch}' but was not pushed.")
        info("Run 'gitgo push' to retry the push.")
        info("Run 'gitgo undo commit' to undo the local commit instead.")
        return

    try:
        status = run_command(["git", "status", "--porcelain"])
        has_staged = any(
            ln and ln[0] not in (' ', '?', '!')
            for ln in status.splitlines()
        )
    except GitCommandError:
        has_staged = False

    if has_staged:
        try:
            run_command(["git", "reset", "HEAD"])
            success("Staged files have been unstaged. Your edits are safe.")
        except GitCommandError:
            warning("Could not unstage automatically. Run 'git reset HEAD' manually.")
    else:
        success("No git state was changed. Your files are safe.")

    if created_branch and not commit_was_made:
        try:
            if current_branch == created_branch:
                run_command(["git", "checkout", original_branch])
            run_command(["git", "branch", "-D", created_branch])
            success(f"Empty branch '{created_branch}' removed. Back on '{original_branch}'.")
        except GitCommandError:
            warning(f"Could not auto-remove '{created_branch}'.")
            warning(f"Run: git checkout {original_branch} && git branch -D {created_branch}")


def push_operation(args):
    branch = args.branch
    message = args.message
    select = args.select if hasattr(args, 'select') else False

    original_branch = get_current_branch(safe=True)
    try:
        original_head = run_command(["git", "rev-parse", "HEAD"]).strip()
    except GitCommandError:
        original_head = None

    created_branch = None
    auto_switched_from = None

    try:
        if args.new:
            if not branch:
                raise GitGoError("\nBranch name required when using --new flag!\n")
            git_new_branch(branch)
            created_branch = branch
        else:
            if branch and not message and not is_branch_exist(branch):
                message = branch
                branch = get_current_branch()
                info(f"No branch name provided. Using current branch: '{branch}'\n")

            elif branch and is_branch_exist(branch):
                current_branch = get_current_branch()
                if current_branch != branch:
                    if confirm(f"Branch '{branch}' already exists. Switch to it before pushing? (y/n): "):
                        info(f"Switching to target branch '{branch}'...")
                        jump_operation(Namespace(branch=branch, nested=True))
                        auto_switched_from = current_branch
                    else:
                        raise GitGoError("Push aborted.")

            elif not branch:
                branch = get_current_branch()

        if not message:
            message = get_config("default-message", "chore: new changes applied")
            info(f"No commit message provided. Using default: '{message}'\n")

        if select:
            files = get_changed_files()
            if not files:
                info("\nWorking tree is clean. Nothing to select.")
                warning("Make some changes first before using GitGo to commit and push.")
                return

            selected = display_file_picker(files)
            if not selected:
                info("\nNo files selected. Push aborted.\n")
                return

            selective_stage(selected)
            commit_made = git_commit(message, loading_msg="Committing selected files...", skip_staging=True)

            if commit_made:
                git_push(branch)

        else:
            commit_made = git_commit(message)

            if commit_made:
                git_push(branch)
            else:
                try:
                    unpushed = run_command(
                        ["git", "log", "--oneline", f"origin/{branch}..HEAD"],
                        loading_msg="Checking for unpushed commits..."
                    )
                    if unpushed.strip():
                        warning("\nNo changes to commit, but found unpushed commits. Pushing to remote...")
                        git_push(branch)
                    else:
                        info("\nWorking tree is clean and everything is up to date.")
                        warning("Make some changes first before using GitGo to commit and push.")
                        return
                except GitCommandError as e:
                    stderr = getattr(e, "stderr", str(e))
                    if "unknown revision" in stderr or "bad revision" in stderr:
                        warning("\nBranch has no upstream yet. Push first to set it: 'gitgo push'.")
                    else:
                        warning(f"\nCould not verify remote status: {stderr or 'unknown error'}")
                        info("Check your remote with:  git remote -v")
                    return

        banner("MISSION COMPLETE. ALL TARGETS COMMITTED AND PUSHED.", "REMOTE TARGETS ALIGNED WITH LOCAL EDITS.")

        print()
        if auto_switched_from:
            info(f"Switched from '{auto_switched_from}' to '{branch}' automatically.")
            info(f"Run 'gitgo undo push' to revert the push, then 'gitgo jump {auto_switched_from}' to return.")
        else:
            info("Run 'gitgo undo push' to revert this push if it was unintended.")

    except KeyboardInterrupt:
        print()
        warning("Push interrupted (Ctrl+C).")
        _push_interrupt_cleanup(original_branch, original_head, created_branch)
        sys.exit(130)
