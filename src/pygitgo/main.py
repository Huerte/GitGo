from pygitgo.commands.git_operations import (
    git_new_branch, git_commit, git_init, add_remote_origin,
    confirm_remote_link, git_push, get_current_branch, is_branch_exist
)
from pygitgo.utils.colors import info, success, warning, error
from pygitgo.utils.config import get_config, config_operation
from pygitgo.utils.setup import ensure_first_run_setup
from pygitgo.commands.state import state_operations
from pygitgo.commands.jump import jump_operation
from pygitgo.utils.executor import run_command
from pygitgo.auth.manager import login, logout
from pygitgo.auth.account import get_user
from pygitgo.exceptions import GitGoError
import subprocess
import argparse
import sys
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
        error("\nInvalid repository URL!")
        warning("Expected format: https://github.com/username/repo.git")
        warning("             or: git@github.com:username/repo.git\n")
        sys.exit(1)

    commit_message = args.message
    
    info("\nINITIATING LINK OPERATION...")
    info(f"Target: {repo_url}\n")
    
    if not git_init():
        return
    
    run_command(["git", "add", "."], loading_msg="Staging files...")
    success("Files staged for commit.")
    
    clean_message = commit_message.strip('"\'')
    run_command(["git", "commit", "-m", clean_message], loading_msg="Creating initial commit...")
    success("Initial commit created.")
    
    add_remote_origin(repo_url)
    
    if not confirm_remote_link():
        error("Link operation failed! Check your repository URL.")
        return
    
    current_branch = get_current_branch()
    main_branch = get_config("default-branch", "main")
    
    if current_branch.strip() != main_branch:
        run_command(["git", "branch", "-m", main_branch], loading_msg=f"Renaming branch '{current_branch.strip()}' to '{main_branch}'...")
        current_branch = main_branch
    
    remote_refs = run_command(["git", "ls-remote", "--heads", "origin", main_branch], allow_fail=True, loading_msg="Checking remote branches...")
    if not isinstance(remote_refs, subprocess.CalledProcessError) and remote_refs.strip():
        pull_result = run_command(
            ["git", "pull", "origin", main_branch, "--allow-unrelated-histories", "--no-edit"],
            allow_fail=True, loading_msg="Pulling and merging remote content..."
        )
        if isinstance(pull_result, subprocess.CalledProcessError):
            error("Failed to merge remote content. You may need to resolve conflicts manually.")
            warning(f"Run: git pull origin {main_branch} --allow-unrelated-histories")
            warning(f"Then: gitgo push {main_branch} 'your message'\n")
            return
        success("Remote content merged successfully.")
    
    print("\n" + ("=" * 90))
    success("LINK OPERATION COMPLETE! REPOSITORY LOCKED AND LOADED!")
    success(f"Ready to push with: gitgo push {main_branch} 'your message'")
    info("AWAITING FURTHER ORDERS...\n")

    user_choice = input(f"\nDo you want to push now? (y/n): ").lower()
    if user_choice != 'y':
        return
    
    git_push(current_branch)
    
    print("\n" + ("=" * 90))
    success("MISSION COMPLETE — REPOSITORY INITIALIZED AND PUSHED!\nAWAITING FOR YOUR NEXT ORDERS.\n\n")
    

def push_operation(args):
    branch = args.branch
    message = args.message

    if args.new:
        if not branch:
            error("\nBranch name required when using --new flag!\n")
            sys.exit(1)
        git_new_branch(branch)
    else:
        if branch and not message and not is_branch_exist(branch):
            message = branch
            branch = get_current_branch()
        elif not branch:
            branch = get_current_branch()

    if not message:
        message = get_config("default-message", "New Project Update")

    commit_made = git_commit(message)
    
    if commit_made:
        git_push(branch)
    else:
        try:
            unpushed = run_command(["git", "log", "--oneline", f"origin/{branch}..HEAD"], allow_fail=True, loading_msg="Checking for unpushed commits...")
            if not isinstance(unpushed, subprocess.CalledProcessError) and unpushed.strip():
                warning("\nNo changes to commit, but found unpushed commits. Pushing to remote...")
                git_push(branch)
            else:
                info("\nWorking tree is clean and everything is up to date.")
                warning("Make some changes first before using GitGo to commit and push.")
                return
        except:
            warning("\nNo changes to commit. Cannot verify remote status.")
            warning("Make some changes first or check your git remote configuration.")
            return

    print("\n" + ("=" * 90))
    success("MISSION COMPLETE — NO CASUALTIES. ALL TARGETS NEUTRALIZED.\nAWAITING FOR YOUR NEXT ORDERS.\n\n")


def display_current_user():
    username, email = get_user()
    if username and email:
        print("\n" + "="*40)
        info(f"Git User:  {username}")
        info(f"Git Email: {email}")
        print("="*40 + "\n")
    else:
        warning("\nNo Git user identity configured.")
        info("Run 'gitgo user login'\n")


def user_management(args):
    action = args.action if hasattr(args, 'action') else None

    if not action:
        display_current_user()
        sys.exit(0)
    
    if action == 'login':
        login()
    elif action == 'logout':
        logout()
    else:
        error(f"\nInvalid user operation '{action}'!\n")
        sys.exit(1)


def get_version():
    try:
        from importlib.metadata import version
        return version("pygitgo")
    except Exception:
        return "dev"

def main():
    parser = argparse.ArgumentParser(
        prog='gitgo',
        description="GitGo CLI - Your Fast Git Companion",
        epilog="Use 'gitgo <command> -h' for help on a specific command."
    )
    
    parser.add_argument("-v", "-V", "--version", action="version", version=f"GitGo {get_version()}")
    parser.add_argument("-r", "--ready", action="store_true", help="Check tool readiness")

    subparsers = parser.add_subparsers(title="Commands", dest="command")
    subparsers.required = False

    jump_parser = subparsers.add_parser("jump", help="Safely switch branches with try-and-revert")
    jump_parser.add_argument("branch", help="The name of the branch to jump to")

    link_parser = subparsers.add_parser("link", help="Init, commit, and link to a remote repo")
    link_parser.add_argument("url", help="The GitHub repository URL to link")
    link_parser.add_argument("message", nargs="?", default="Initial commit", help="Custom commit message")

    push_parser = subparsers.add_parser(
        "push",
        help="Commit and push branch to remote",
        epilog=(
            "Examples:\n"
            "  gitgo push                        Push current branch with default message\n"
            "  gitgo push main 'fix auth bug'    Push to main with a custom message\n"
            "  gitgo push 'fix auth bug'         Push current branch with a custom message\n"
            "  gitgo push -n feature/login 'add login'   Create new branch and push"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    push_parser.add_argument("-n", "--new", action="store_true", help="Create a new branch before pushing")
    push_parser.add_argument("branch", nargs="?", default=None, help="Branch to push to (default: current branch)")
    push_parser.add_argument("message", nargs="?", default=None, help="Commit message")

    state_parser = subparsers.add_parser(
        "state",
        help="Manage saved working states (stashes)",
        epilog=(
            "Examples:\n"
            "  gitgo state list                  Show all saved states\n"
            "  gitgo state save 'halfway done'   Save current work with a name\n"
            "  gitgo state load 1                Restore state by ID\n"
            "  gitgo state delete 1              Delete a specific state\n"
            "  gitgo state delete -a             Delete all saved states"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    state_parser.add_argument(
        "action",
        choices=["list", "save", "load", "delete", "-l", "-s", "-o", "-d"],
        metavar="action",
        help="list, save, load, delete  (aliases: -l, -s, -o, -d)"
    )
    state_parser.add_argument(
        "identifier",
        nargs="?",
        default=None,
        help="Optional name or ID"
    )
    
    user_parser = subparsers.add_parser("user", help="Manage Git user identity")
    user_parser.add_argument("action", nargs="?", choices=["login", "logout"], default=None, help="login or logout")

    config_parser = subparsers.add_parser("config",
        help="Manage GitGo default settings",
        epilog=(
            "Examples:\n"
            "  gitgo config set default-branch master\n"
            "  gitgo config set default-message 'WIP'\n"
            "  gitgo config get default-branch"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    config_parser.add_argument("action", choices=["set", "get"], help="Action to perform")
    config_parser.add_argument("key", choices=["default-branch", "default-message"], help="The setting to change")
    config_parser.add_argument("value", nargs="?", help="The new value (required for 'set')")

    args = parser.parse_args()

    if args.ready:
        info("\nALL UNITS ONLINE. GitGo STANDING BY. AWAITING COMMANDS...\n")
        sys.exit(0)

    if not args.command:
        parser.print_help()
        sys.exit(0)

    ensure_first_run_setup()

    try:
        if args.command == "jump":
            jump_operation(args)
        elif args.command == "link":
            link_operation(args)
        elif args.command == "push":
            push_operation(args)
        elif args.command == "state":
            state_operations(args)
        elif args.command == "user":
            user_management(args)
        elif args.command == "config":
            config_operation(args)
    except GitGoError as e:
        error(f"\n{e}\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
