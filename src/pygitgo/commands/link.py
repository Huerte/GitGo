from pygitgo.commands.git_remote import add_remote_origin, confirm_remote_link
from pygitgo.utils.cli_io import success, warning, error, info, banner
from pygitgo.commands.git_core import git_init, git_commit, git_push
from pygitgo.commands.git_branch import get_current_branch
from pygitgo.auth.ssh_utils import ensure_github_known_host, convert_https_to_ssh, is_ssh_url, check_connection
from pygitgo.exceptions import GitCommandError, GitGoError
from pygitgo.utils.validators import validate_repo_url
from pygitgo.utils.config import get_default_branch
from pygitgo.utils.executor import run_command
import sys


def _link_interrupt_cleanup(repo_url, initialized, committed, remote_added):
    try:
        run_command(["git", "merge", "--abort"])
        info("In-progress merge aborted.")
    except GitCommandError:
        pass

    if remote_added:
        info(f"Remote 'origin' was set to: {repo_url}")
        info("Run 'gitgo undo link' to remove it, or 'gitgo link <url>' to replace it.")

    if committed:
        info("Initial commit was created. Your files are safe.")
        info("Run 'gitgo push' when ready to push to the remote.")
        return

    if initialized:
        try:
            import shutil
            import os
            shutil.rmtree(".git")
            success("Local Git repository config removed. Files are untouched.")
        except Exception:
            warning("Could not auto-remove '.git' folder.")
            warning("Run: rmdir /s /q .git  (Windows) or  rm -rf .git  (Mac/Linux)")
    else:
        success("No Git state was changed. Your files are safe.")


def link_core(repo_url, commit_message, silent=False, already_initialized=False):
    if not validate_repo_url(repo_url):
        raise GitGoError(f"Invalid remote repository URL: '{repo_url}'")
    
    ensure_github_known_host()

    if not is_ssh_url(repo_url):
        if check_connection(ok_text="GitHub connection verified.", fail_text=None):
            ssh_url = convert_https_to_ssh(repo_url)
            if ssh_url:
                repo_url = ssh_url

    initialized = False
    committed = False
    remote_added = False

    try:
        main_branch = get_default_branch()

        if already_initialized:
            is_new_repo = True
        else:
            is_new_repo = git_init()
            if is_new_repo:
                initialized = True

        if not is_new_repo:
            add_remote_origin(repo_url)
            remote_added = True

            confirm_remote_link(ok_text="Remote linked to existing repository.")
            info("Ready to push with: gitgo push <branch> 'your message'")
            return

        commit_made = git_commit(commit_message, loading_msg="Creating initial commit...", ok_text="Initial commit created.")
        if commit_made:
            committed = True

        add_remote_origin(repo_url)
        remote_added = True

        try:
            current_branch = get_current_branch()
        except GitCommandError as e:
            raise GitGoError(f"Could not determine the current branch: {e}")

        if current_branch != main_branch:
            run_command(["git", "branch", "-m", main_branch], loading_msg=f"Renaming branch '{current_branch}' to '{main_branch}'...", ok_text=f"Branch renamed to '{main_branch}'.")
            current_branch = main_branch

        try:
            remote_refs = run_command(["git", "ls-remote", "--heads", "origin", main_branch], loading_msg="Checking remote branches...", ok_text="Remote branches checked.")
        except GitCommandError:
            remote_refs = None

        if remote_refs and remote_refs.strip():
            try:
                run_command(
                    ["git", "pull", "origin", main_branch, "--allow-unrelated-histories", "--no-edit"],
                    loading_msg="Pulling and merging remote content...",
                    ok_text="Remote content merged."
                )
            except GitCommandError as e:
                error("Failed to merge remote content. You may need to resolve conflicts manually.")
                warning(f"Run: git pull origin {main_branch} --allow-unrelated-histories")
                warning(f"Then: gitgo push {main_branch} 'your message'\n")
                raise GitGoError(f"Failed to merge remote content: {e.stderr}" if e.stderr else "Failed to merge remote content.")

        try:
            run_command(["git", "rev-parse", "HEAD"])
            has_commits = True
        except GitCommandError:
            has_commits = False

        if has_commits:
            git_push(current_branch)
        else:
            info("Repository is currently empty. Add files and run 'gitgo push' to upload.")

        if not silent:
            banner("REPOSITORY INITIALIZED AND DEPLOYED.", "LOCAL REPOSITORY CONNECTED TO REMOTE ORIGIN.")
            print()
            info("Run 'gitgo undo link' to remove the remote and undo the initial commit.")

    except KeyboardInterrupt:
        print()
        warning("Link interrupted (Ctrl+C).")
        _link_interrupt_cleanup(repo_url, initialized, committed, remote_added)
        sys.exit(130)


def link_operation(args):
    link_core(args.url, args.message)

