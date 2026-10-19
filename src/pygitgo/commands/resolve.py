from pygitgo.utils.cli_io import info, warning, error, banner, write
from pygitgo.exceptions import GitCommandError, GitGoError
from pygitgo.utils.executor import run_command
from pygitgo.commands.git_core import abort_pull_conflict, ensure_inside_git_repository, read_pull_record, finish_pull_record
from pathlib import Path
import re
import sys

# A line that starts with a conflict marker. '=======' alone is too common in
# docs (setext headings), so only the opening/closing markers are checked.
_CONFLICT_MARKER = re.compile(r"^(<{7}|>{7})(?: |$)", re.MULTILINE)


def get_unmerged_files():
    out = run_command(["git", "diff", "--name-only", "--diff-filter=U", "-z"], return_complete=True)
    raw = out.stdout if hasattr(out, "stdout") else str(out)
    return [p for p in raw.split("\0") if p]


def files_with_conflict_markers(paths):
    bad = []
    for path in paths:
        try:
            text = Path(path).read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue  # deleted-by-one-side conflicts have no file to scan
        if _CONFLICT_MARKER.search(text):
            bad.append(path)
    return bad


def resolve_operation(args):
    ensure_inside_git_repository()

    if getattr(args, 'abort', False):
        abort_pull_conflict()
        return

    rebase_in_progress = Path(".git/rebase-merge").exists() or Path(".git/rebase-apply").exists()
    if not rebase_in_progress:
        raise GitGoError("No conflict resolution is currently in progress. You are good to go!")

    unmerged = get_unmerged_files()
    still_conflicted = files_with_conflict_markers(unmerged)
    if still_conflicted:
        error("These files still contain conflict markers (<<<<<<< / >>>>>>>):")
        for path in still_conflicted:
            write(f"  - {path}")
        write()
        raise GitGoError(
            "Fix those files, save them, then run 'gitgo resolve' again.\n"
            "Nothing was staged or committed."
        )

    if unmerged:
        # Stage only the files that were actually in conflict, not the whole tree.
        run_command(["git", "add", "--"] + unmerged, loading_msg="Staging resolved files...", ok_text="Conflict fixes staged.")

    try:
        run_command(
            ["git", "rebase", "--continue"],
            loading_msg="Finishing sync...",
            extra_env={"GIT_EDITOR": "true"}
        )
    except KeyboardInterrupt:
        write()
        warning("Resolve interrupted (Ctrl+C).")
        info("The rebase is still paused. Run 'gitgo resolve' again when ready.")
        sys.exit(130)
    except GitCommandError as e:
        stderr = getattr(e, "stderr", str(e))
        if "must edit all merge conflicts" in stderr.lower() or "still have unmerged paths" in stderr.lower():
            raise GitGoError(
                "You still have unresolved conflicts.\n"
                "Open your editor, fix all the conflict markers, save, and then run 'gitgo resolve' again."
            )
        if (Path(".git/rebase-merge").exists() or Path(".git/rebase-apply").exists()) and get_unmerged_files():
            warning("The next commit being replayed has conflicts too.")
            info("Fix the conflicted files, then run 'gitgo resolve' again.")
            raise GitGoError("Resolve paused — more conflicts to fix.")
        raise GitGoError(f"Resolve failed: {stderr}")

    record = read_pull_record()
    if record and record.get("post") is None:
        finish_pull_record()

    banner("CONFLICT RESOLVED. SYNC COMPLETE.", "YOUR CHANGES AND REMOTE CHANGES ARE MERGED.")
