from pygitgo.commands.git_operations import (
    git_init, git_commit, git_push, add_remote_origin,
    confirm_remote_link, get_current_branch
)
from pygitgo.utils.config import get_config
from pygitgo.utils.executor import run_command
from pygitgo.utils.colors import success, warning, error, highlight, print_banner
from pygitgo.exceptions import GitCommandError, GitGoError
import re


def validate_repo_url(url):
    """Validate that the URL looks like a valid Git repository URL."""
    patterns = [
        r'^https?://[\w.-]+/[\w.-]+/[\w.-]+(?:\.git)?/?$',  # HTTPS
        r'^git@[\w.-]+:[\w.-]+/[\w.-]+(?:\.git)?$',          # SSH
    ]
    return any(re.match(p, url.strip()) for p in patterns)


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
    
    is_new_repo = git_init()
    
    if not is_new_repo:
        add_remote_origin(repo_url)

        if confirm_remote_link():
            success("\nRemote linked to existing repository.")
            success(f"Ready to push with: gitgo push <branch> 'your message'\n")
        return

    commit_made = git_commit(commit_message, loading_msg="Creating initial commit...")
    if commit_made:
        success("Initial commit created.")
    
    add_remote_origin(repo_url)
    
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
