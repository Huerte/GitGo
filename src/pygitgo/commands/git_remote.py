from pygitgo.exceptions import GitCommandError, GitGoError
from pygitgo.utils.cli_io import info, warning, error, write
from pygitgo.utils.executor import run_command


def add_remote_origin(repo_url):
    clean_url = repo_url.strip('"\'')

    try:
        existing_remote = run_command(["git", "remote", "get-url", "origin"])
        warning(f"Remote origin already exists: {existing_remote}")
        run_command(["git", "remote", "set-url", "origin", clean_url], loading_msg="Updating remote URL...", ok_text=f"Remote origin set to: {clean_url}")
    except GitCommandError:
        run_command(["git", "remote", "add", "origin", clean_url], loading_msg="Adding remote origin...", ok_text=f"Remote origin set to: {clean_url}")


def confirm_remote_link(ok_text=None):
    if not ok_text:
        ok_text = "Remote is reachable."
    try:
        run_command(["git", "ls-remote", "origin"], loading_msg="Testing connection to remote...", ok_text=ok_text)
        return True
    except GitCommandError as e:
        stderr = getattr(e, "stderr", str(e))
        info("Run:  git remote -v   to inspect your current remote.")
        if "could not resolve" in stderr.lower():
            raise GitGoError("Connection failed: DNS lookup failed for the remote host. Check your internet.")
        elif "permission denied" in stderr.lower():
            raise GitGoError("Connection failed: SSH key not accepted. Run 'gitgo user login' to re-authenticate.")
        elif stderr:
            raise GitGoError(f"Connection failed: {stderr}")
        else:
            raise GitGoError("Connection failed — verify the URL and your SSH key.")


def check_and_sync_branch(branch):
    try:
        run_command(["git", "fetch", "origin"], loading_msg="Checking if branch is up to date...", ok_text="Remote fetched.")

        try:
            local_commit = run_command(["git", "rev-parse", branch])
            remote_commit = run_command(["git", "rev-parse", f"origin/{branch}"])

            if local_commit != remote_commit:
                behind_check = run_command(
                    ["git", "rev-list", "--count", f"{branch}..origin/{branch}"]
                )
                if behind_check and int(behind_check) > 0:
                    warning(f"Local branch is behind remote by {behind_check} commit(s). Pulling changes...")
                    output = run_command(["git", "pull", "--rebase", "origin", branch], loading_msg="Pulling changes from remote...", ok_text="Synced with remote.")
                    if output:
                        write(output)
                else:
                    info("Branch is up to date.")
            else:
                info("Branch is already up to date.")
        except (GitCommandError, ValueError):
            warning("Remote branch doesn't exist yet. First push will create it.")
    except (GitCommandError, OSError):
        warning("Could not fetch from remote. Proceeding with push...")


def handle_rebase():
    warning("Conflict detected during rebase.")
    info("Resolve conflicts manually, then run:")
    info("    git add <files>")
    info("    gitgo resolve")
    info("When finished, run 'gitgo push <branch> <message>' again.")
    raise GitGoError("Push aborted — rebase conflict in progress.")
