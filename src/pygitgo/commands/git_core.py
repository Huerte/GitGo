from pygitgo.auth.ssh_utils import convert_https_to_ssh, get_ssh_key_path, is_ssh_url, check_connection, get_remote_host
from pygitgo.exceptions import GitGoError, GitCommandError
from pygitgo.auth.account import sanitize_signing_config
from pygitgo.commands.git_remote import handle_rebase
from pygitgo.utils.config import get_default_branch
from pygitgo.utils.executor import run_command
from pygitgo.utils.cli_io import info, warning, error, write
from pygitgo.utils.safety import find_sensitive
import sys
from pathlib import Path
import json
import os


def ensure_inside_git_repository():
    if not is_git_repository():
        raise GitGoError("Not inside a git repository. Run 'gitgo init' or 'gitgo link' first.")


def is_git_repository():
    try:
        run_command(["git", "rev-parse", "--is-inside-work-tree"], loading_msg="Checking repository...")
        return True
    except GitCommandError:
        return False


def has_local_changes():
    try:
        status_result = run_command(["git", "status", "--porcelain"])
        return bool(status_result.strip())
    except GitCommandError:
        return False


def is_rebase_in_progress():
    try:
        git_dir = run_command(["git", "rev-parse", "--git-dir"]).strip()
        return Path(git_dir).joinpath("rebase-merge").exists() or Path(git_dir).joinpath("rebase-apply").exists()
    except GitCommandError:
        return False


def has_any_commits():
    try:
        run_command(["git", "rev-parse", "HEAD"])
        return True
    except GitCommandError:
        return False


def get_recent_commits(number=5, branch=None):
    command = [
        "git", "log", 
        f"-n{number}",
        "--pretty=format:%h||%an||%cr||%s"
    ]
    if branch:
        command.append(branch)
        
    try:
        output = run_command(command)
        if not output:
            return []
            
        commits = []
        for line in output.splitlines():
            try:
                commit_hash, author, date, message = line.split("||", 3)
                commits.append({
                    "hash": commit_hash,
                    "author": author,
                    "date": date,
                    "message": message
                })
            except ValueError:
                continue
        return commits
    except GitCommandError as e:
        raise GitGoError(f"Failed to retrieve log: {getattr(e, 'stderr', str(e))}")



def _get_signing_flags():
    key_path = get_ssh_key_path()
    if not key_path.exists():
        return []
    return [
        "-c", "gpg.format=ssh",
        "-c", f"user.signingkey={key_path}",
    ]


def _read_pending_files(skip_staging):
    """Return (pending_paths, untracked_paths) from one raw `git status -z` call."""
    from pygitgo.commands.staging import parse_porcelain_z
    result = run_command(["git", "status", "--porcelain", "-z", "-uall"], return_complete=True)
    raw = result.stdout if hasattr(result, "stdout") else str(result)
    if not raw.strip():
        return None, [], []
    entries = parse_porcelain_z(raw)
    if skip_staging:
        entries = [e for e in entries if e["index"] not in (" ", "?")]
    pending = [e["path"] for e in entries]
    untracked = [e["path"] for e in entries if e["status"] == "??"]
    return raw, pending, untracked


def _preview_commit(pending):
    if not pending:
        return
    shown = ", ".join(pending[:5])
    extra = f" and {len(pending) - 5} more" if len(pending) > 5 else ""
    info(f"Committing {len(pending)} file(s): {shown}{extra}")


def _guard_sensitive_files(pending, untracked, allow_sensitive):
    """Stop before secrets get committed. Returns the list of paths to leave out of this commit."""
    flagged = find_sensitive(pending)
    if not flagged or allow_sensitive:
        return []

    write()
    error("These files look like secrets or private keys:")
    for path in flagged[:10]:
        write(f"  - {path}")
    if len(flagged) > 10:
        write(f"  ... and {len(flagged) - 10} more")
    write()

    if not sys.stdin.isatty():
        raise GitGoError(
            "Refusing to commit files that look like secrets.\n"
            "Add them to .gitignore, or re-run with --allow-sensitive if you are sure."
        )

    info("[i] ignore them (add to .gitignore) and continue")
    info("[c] commit them anyway")
    info("[a] abort (nothing is staged or committed)")
    while True:
        choice = input("Choose i / c / a: ").strip().lower()
        if choice in ("i", "c", "a"):
            break
    if choice == "a":
        raise GitGoError("Aborted. Nothing was staged or committed.")
    if choice == "c":
        return []

    to_ignore = [p for p in flagged if p in untracked]
    if to_ignore:
        with open(".gitignore", "a", encoding="utf-8") as f:
            f.write("\n# Added by GitGo: looks like a secret\n")
            for path in to_ignore:
                f.write(f"/{path}\n")
        info(f"Added {len(to_ignore)} file(s) to .gitignore.")
    already_tracked = [p for p in flagged if p not in untracked]
    if already_tracked:
        warning("Some of these files are already tracked by Git, so .gitignore will not hide them.")
        warning("They were left out of this commit. Remove them from history if they were ever pushed.")
    return flagged


def git_commit(commit_message, loading_msg="Committing changes...", skip_staging=False, ok_text=None, allow_sensitive=False):
    if not ok_text:
        ok_text = "Changes committed."
    try:
        raw, pending, untracked = _read_pending_files(skip_staging)
        if raw is None:
            return False
    except GitCommandError as e:
        stderr = getattr(e, "stderr", str(e))
        if "not a git repository" in stderr.lower():
            raise GitGoError("Not inside a git repository. Run 'gitgo init' or 'gitgo link' first.")
        raise GitGoError(f"Could not check repository status: {stderr}")

    sanitize_signing_config()

    exclude = _guard_sensitive_files(pending, untracked, allow_sensitive)
    _preview_commit([p for p in pending if p not in exclude])

    if not skip_staging:
        run_command(["git", "add", "."], loading_msg="Staging files...", ok_text="Files staged.")
        if exclude:
            run_command(["git", "reset", "-q", "--"] + exclude)
    elif exclude:
        run_command(["git", "reset", "-q", "--"] + exclude)

    if exclude:
        try:
            run_command(["git", "diff", "--cached", "--quiet"])
            info("Nothing left to commit after leaving out those files.")
            return False
        except GitCommandError:
            pass  # exit code 1 means something is still staged

    clean_message = commit_message.strip('"\'')

    signing_flags = _get_signing_flags()

    commit_command = ["git"]
    if signing_flags:
        commit_command.extend(signing_flags + ["commit", "-S", "-m", clean_message])
    else:
        commit_command.extend(["commit", "-m", clean_message])

    run_command(commit_command, loading_msg=loading_msg, ok_text=ok_text)

    return True


def git_init(ok_text=None):
    if os.path.isdir(".git"):
        warning("Already a git repository! Skipping init...")
        return False

    default_main_branch = get_default_branch()

    if not ok_text:
        ok_text = "Git repository initialized."

    try:
        run_command(["git", "init", "-b", default_main_branch], loading_msg="Initializing git repository...", ok_text=ok_text)
    except GitCommandError:
        run_command(["git", "init"], loading_msg="Initializing git repository...")
        run_command(["git", "checkout", "-b", default_main_branch], ok_text=ok_text)

    return True


def git_push(branch, ok_text=None):
    if not ok_text:
        ok_text = f"Pushed to remote branch '{branch}'."
    try:
        remote_url = run_command(["git", "remote", "get-url", "origin"]).strip()
    except GitCommandError:
        remote_url = None

    if remote_url and not is_ssh_url(remote_url):
        # Only attempt SSH conversion if the remote host is github.com and
        # GitHub SSH is working. For other hosts (Gitea, GitLab, etc.) we
        # leave the URL as-is so HTTPS credentials are used instead.
        remote_host = get_remote_host(remote_url)
        if remote_host == "github.com" and check_connection():
            ssh_url = convert_https_to_ssh(remote_url)
            if ssh_url:
                run_command(
                    ["git", "remote", "set-url", "origin", ssh_url],
                    loading_msg="Converting remote from HTTPS to SSH...",
                    ok_text=f"Remote updated to: {ssh_url}"
                )
        elif remote_host and remote_host != "github.com":
            from pygitgo.utils.cli_io import info as _info
            _info(f"Remote host is '{remote_host}'. Keeping HTTPS URL (SSH conversion is for GitHub only).")

    try:
        run_command(["git", "push", "-u", "origin", branch], loading_msg=f"Pushing to remote branch '{branch}'...", ok_text=ok_text, err_text="Push failed: verify your remote URL and SSH key, then try again.")
    except (GitCommandError, OSError) as e:
        stderr = getattr(e, "stderr", str(e))
        if "rebase in progress" in stderr.lower():
            handle_rebase()
        elif "non-fast-forward" in stderr.lower() or "rejected" in stderr.lower():
            info("The remote has commits you don't have locally.")
            info("Run 'gitgo pull' first, then push again.")
            raise GitGoError("Push rejected: pull the latest changes first.")
        elif "repository not found" in stderr.lower() or "does not exist" in stderr.lower():
            info("Run:  git remote -v   to verify the remote URL.")
            raise GitGoError("Push failed: remote repository not found.")
        elif "permission denied" in stderr.lower():
            info("Check that your SSH key is added to GitHub.")
            info("Run:  gitgo user login   to re-authenticate.")
            raise GitGoError("Push failed: permission denied.")
        else:
            info("Run:  git remote -v   to inspect your current remote.")
            raise GitGoError(f"Push failed: {stderr}" if stderr else "Push failed — check the output above.")


def _pull_state_file():
    git_dir = run_command(["git", "rev-parse", "--git-dir"]).strip()
    return Path(git_dir) / "gitgo" / "last-pull.json"


def begin_pull_record(branch):
    """Remember where `branch` was before a pull so `undo pull` can restore exactly that."""
    try:
        pre = run_command(["git", "rev-parse", "HEAD"]).strip()
        path = _pull_state_file()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"branch": branch, "pre": pre, "post": None}))
    except (GitCommandError, OSError):
        pass


def finish_pull_record():
    try:
        path = _pull_state_file()
        data = json.loads(path.read_text())
        data["post"] = run_command(["git", "rev-parse", "HEAD"]).strip()
        path.write_text(json.dumps(data))
    except (GitCommandError, OSError, ValueError):
        pass


def read_pull_record():
    try:
        return json.loads(_pull_state_file().read_text())
    except (GitCommandError, OSError, ValueError):
        return None


def clear_pull_record():
    try:
        _pull_state_file().unlink()
    except (GitCommandError, OSError):
        pass


def abort_pull_conflict():
    from pathlib import Path
    from pygitgo.utils.cli_io import warning, info, confirm
    from pygitgo.exceptions import GitCommandError, GitGoError
    from pygitgo.utils.executor import run_command
    from pygitgo.commands.git_branch import get_current_branch
    
    rebase_in_progress = Path(".git/rebase-merge").exists() or Path(".git/rebase-apply").exists()
    
    if rebase_in_progress:
        warning("A sync or jump hit a merge conflict and is paused.")
        if not confirm("Cancel the sync and discard any conflict fixes? (y/n): ", destructive=True):
            info("Canceled. The conflict is still active.")
            return False
            
        try:
            run_command(["git", "rebase", "--abort"], loading_msg="Aborting sync...", ok_text="Sync aborted. Branch is back to how it was before the conflict.")
            return True
        except GitCommandError as e:
            raise GitGoError(f"Abort failed: {getattr(e, 'stderr', str(e))}")

    record = read_pull_record()
    if not record or not record.get("post"):
        info("Nothing to undo. GitGo has no record of a completed pull in this repository.")
        return False

    try:
        branch = get_current_branch(safe=True)
    except GitCommandError as e:
        raise GitGoError(f"Could not determine the current branch: {e}")

    if record["branch"] != branch:
        raise GitGoError(
            f"The last pull was on '{record['branch']}' but you are on '{branch}'. "
            f"Run 'gitgo jump {record['branch']}' first."
        )

    head = run_command(["git", "rev-parse", "HEAD"]).strip()
    if head != record["post"]:
        raise GitGoError(
            "This branch has moved since the last pull (new commits, a reset, or another pull).\n"
            "Refusing to guess. Undo those first, or reset manually with git."
        )

    if record["pre"] == record["post"]:
        info("The last pull brought nothing new. Nothing to undo.")
        return False

    warning("This will move your branch back to where it was before the last pull.")
    warning("Commits that arrived in the pull will be removed locally.")
    if not confirm("Undo the last pull? Type 'y' to confirm: ", destructive=True):
        info("Canceled. Branch is unchanged.")
        return False

    try:
        # --keep refuses to run if it would overwrite uncommitted changes, so it can't eat your work.
        run_command(
            ["git", "reset", "--keep", record["pre"]],
            loading_msg="Reverting to pre-pull state...",
            ok_text="Branch reset to its state before the last pull."
        )
    except GitCommandError as e:
        raise GitGoError(
            "Could not undo the pull without overwriting your uncommitted changes.\n"
            "Commit them or run 'gitgo state save' first, then try again.\n"
            f"Details: {getattr(e, 'stderr', str(e))}"
        )
    clear_pull_record()

    try:
        behind = run_command(["git", "rev-list", "--count", f"HEAD..origin/{branch}"]).strip()
        if behind and int(behind) > 0:
            warning(f"Your local branch is now {behind} commit(s) behind remote '{branch}'.")
            info("The remote still has the pulled commits. Your local copy has been reset.")
            info(f"To push your undo to the remote: git push --force-with-lease origin {branch}")
            info("Only do this if you are the only person working on this branch.")
    except (GitCommandError, ValueError):
        pass

    return True
