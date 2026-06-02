from pygitgo.utils.colors import success, warning, error, highlight, info, print_banner
from pygitgo.commands.git_remote import add_remote_origin, confirm_remote_link
from pygitgo.commands.git_core import git_init, git_commit, git_push
from pygitgo.commands.git_branch import get_current_branch
from pygitgo.exceptions import GitCommandError, GitGoError
from pygitgo.utils.executor import run_command
from pygitgo.utils.config import get_config
from pygitgo.utils.validators import validate_repo_url
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
    elif initialized:
        info("Git repository was initialized. Your files are safe.")
        info("Run 'gitgo link <url>' again to complete the setup.")
    else:
        success("No git state was changed.")


def link_operation(args):
    repo_url = args.url

    if not validate_repo_url(repo_url):
        raise GitGoError(
            "\nInvalid repository URL!\n"
            "Expected format: https://github.com/username/repo.git"
            "             or: git@github.com:username/repo.git\n"
        )

    commit_message = args.message

    highlight("INITIATING LINK OPERATION...")
    highlight(f"Target: {repo_url}")
    print()

    initialized = False
    committed = False
    remote_added = False

    try:
        is_new_repo = git_init()
        if is_new_repo:
            initialized = True

        if not is_new_repo:
            add_remote_origin(repo_url)
            remote_added = True

            if confirm_remote_link():
                success("\nRemote linked to existing repository.")
                success(f"Ready to push with: gitgo push <branch> 'your message'\n")
            return

        commit_made = git_commit(commit_message, loading_msg="Creating initial commit...")
        if commit_made:
            committed = True
            success("Initial commit created.")

        add_remote_origin(repo_url)
        remote_added = True

        if not confirm_remote_link():
            return

        current_branch = get_current_branch()
        main_branch = get_config("default-branch", "main")

        if current_branch != main_branch:
            run_command(["git", "branch", "-m", main_branch], loading_msg=f"Renaming branch '{current_branch}' to '{main_branch}'...")
            current_branch = main_branch

        try:
            remote_refs = run_command(["git", "ls-remote", "--heads", "origin", main_branch], loading_msg="Checking remote branches...")
        except GitCommandError:
            remote_refs = None

        if remote_refs and remote_refs.strip():
            try:
                run_command(
                    ["git", "pull", "origin", main_branch, "--allow-unrelated-histories", "--no-edit"],
                    loading_msg="Pulling and merging remote content..."
                )
                success("Remote content merged.")
            except GitCommandError:
                error("Failed to merge remote content. You may need to resolve conflicts manually.")
                warning(f"Run: git pull origin {main_branch} --allow-unrelated-histories")
                warning(f"Then: gitgo push {main_branch} 'your message'\n")
                return

        print_banner("REPOSITORY INITIALIZED AND LINKED.")

        user_choice = input(f"Do you want to push now? (y/n): ").lower()
        if user_choice != 'y':
            return

        git_push(current_branch)

        print_banner("REPOSITORY INITIALIZED AND DEPLOYED.")

    except KeyboardInterrupt:
        print()
        warning("Link interrupted (Ctrl+C).")
        _link_interrupt_cleanup(repo_url, initialized, committed, remote_added)
        sys.exit(130)
