from pygitgo.commands.git_operations import (
    git_new_branch, git_commit, git_init, add_remote_origin,
    confirm_remote_link, git_push, get_current_branch, is_branch_exist
)
from pygitgo.commands.staging import get_changed_files, display_file_picker, selective_stage
from pygitgo.utils.update_checker import check_for_updates_background
from pygitgo.utils.executor import run_command, command_failed
from pygitgo.utils.colors import info, success, warning, error
from pygitgo.utils.config import get_config, config_operation
from pygitgo.exceptions import GitCommandError, GitGoError
from pygitgo.utils.setup import ensure_first_run_setup
from pygitgo.commands.state import state_operations
from pygitgo.commands.undo import undo_operations
from pygitgo.commands.pull import pull_operation
from pygitgo.commands.jump import jump_operation
from pygitgo.auth.manager import login, logout
from pygitgo.auth.account import get_user
from argparse import Namespace
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
        raise GitGoError(
            "\nInvalid repository URL!\n"
            "Expected format: https://github.com/username/repo.git"
            "             or: git@github.com:username/repo.git\n"
        )

    commit_message = args.message
    
    info("\nINITIATING LINK OPERATION...")
    info(f"Target: {repo_url}\n")
    
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
    
    remote_refs = run_command(["git", "ls-remote", "--heads", "origin", main_branch], allow_fail=True, loading_msg="Checking remote branches...")
    if not command_failed(remote_refs) and remote_refs.strip():
        pull_result = run_command(
            ["git", "pull", "origin", main_branch, "--allow-unrelated-histories", "--no-edit"],
            allow_fail=True, loading_msg="Pulling and merging remote content..."
        )
        if command_failed(pull_result):
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
    success("MISSION COMPLETE: REPOSITORY INITIALIZED AND PUSHED!\nAWAITING FOR YOUR NEXT ORDERS.\n\n")
    

def push_operation(args):
    branch = args.branch
    message = args.message
    select = args.select if hasattr(args, 'select') else False

    if args.new:
        if not branch:
            raise GitGoError("\nBranch name required when using --new flag!\n")
        git_new_branch(branch)
    else:
        if branch and not message and not is_branch_exist(branch):
            message = branch
            branch = get_current_branch()
            info(f"No branch name provided. Using current branch: '{branch}'\n")
            
        elif branch and is_branch_exist(branch):
            current_branch = get_current_branch()
            if current_branch != branch:
                warning(f"You are currently on branch '{current_branch}', not '{branch}'.")
                user_choice = input(f"Do you want to switch to branch '{branch}'? (y/n): ").lower()
                if user_choice != 'y':
                    raise GitGoError("\nPush aborted to prevent committing to the wrong branch.\n")
                jump_operation(Namespace(branch=branch))
    
        elif not branch:
            branch = get_current_branch()

    if not message:
        message = get_config("default-message", "New Project Update")
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
        commit_made = git_commit(message, loading_msg="Commiting selected files...", skip_staging=True)
        
        if commit_made:
            git_push(branch)
        
    else:
        commit_made = git_commit(message)
        
        if commit_made:
            git_push(branch)
        else:
            try:
                unpushed = run_command(["git", "log", "--oneline", f"origin/{branch}..HEAD"], allow_fail=True, loading_msg="Checking for unpushed commits...")
                if not command_failed(unpushed) and unpushed.strip():
                    warning("\nNo changes to commit, but found unpushed commits. Pushing to remote...")
                    git_push(branch)
                else:
                    info("\nWorking tree is clean and everything is up to date.")
                    warning("Make some changes first before using GitGo to commit and push.")
                    return
            except (GitCommandError, Exception):
                warning("\nNo changes to commit. Cannot verify remote status.")
                warning("Make some changes first or check your git remote configuration.")
                return

    print("\n" + ("=" * 90))
    success("MISSION COMPLETE: NO CASUALTIES. ALL TARGETS NEUTRALIZED.\nAWAITING FOR YOUR NEXT ORDERS.\n\n")


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
        return
    
    if action == 'login':
        login()
    elif action == 'logout':
        logout()
    else:
        raise GitGoError(f"\nInvalid user operation '{action}'!\n")


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
    
    parser.add_argument("-v", "-V", "--version", action="store_true", help="show program's version number and exit")
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
            "  gitgo push -n feature/login 'add login'   Create new branch and push\n"
            "  gitgo push -s main 'fix bug'      Pick which files to include before pushing"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    push_parser.add_argument("-n", "--new", action="store_true", help="Create a new branch before pushing")
    push_parser.add_argument("-s", "--select", action="store_true", help="Interactively select which files to stage")
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
        nargs="?",
        choices=["list", "save", "load", "delete"],
        metavar="action",
        default=None,
        help="list, save, load, delete"
    )
    state_parser.add_argument(
        "identifier",
        nargs="?",
        default=None,
        help="Optional name or ID"
    )
    _alias_group = state_parser.add_mutually_exclusive_group()
    _alias_group.add_argument("-l", dest="action_alias", action="store_const", const="list",   help="Alias for 'list'")
    _alias_group.add_argument("-s", dest="action_alias", action="store_const", const="save",   help="Alias for 'save'")
    _alias_group.add_argument("-o", dest="action_alias", action="store_const", const="load",   help="Alias for 'load'")
    _alias_group.add_argument("-d", dest="action_alias", action="store_const", const="delete", help="Alias for 'delete'")

    state_parser.add_argument(
        "-a", "--all",
        action="store_true",
        help="Apply action to all states (e.g., delete all)"
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

    undo_parser = subparsers.add_parser("undo", 
        help="Safely undo mistakes", 
        epilog=(
            "Examples:\n"
            "  gitgo undo commit       Undo your last commit (your files are safe)\n"
            "  gitgo undo add          Undo 'git add' (files are no longer ready to commit)\n"
            "  gitgo undo changes      DANGER: Throw away all new changes and start fresh"
        ), 
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    undo_parser.add_argument(
        "action", 
        choices=["commit", "add", "changes"], 
        help="What to undo: 'commit', 'add', or 'changes'"
    )

    pull_parser = subparsers.add_parser("pull", 
        help="Safely pull the latest code without losing your changes",
        epilog=(
            "Examples:\n"
            "  gitgo pull                Safely pull updates for your current branch\n"
            "  gitgo pull main           Safely pull updates from the 'main' branch\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    pull_parser.add_argument("branch", nargs="?", default=None, help="The branch to pull from (default is your current branch)")

    args = parser.parse_args()

    if getattr(args, 'version', False):
        print(f"GitGo {get_version()}")
        print(f"Support GitGo: https://ko-fi.com/huerte")
        return

    if args.ready:
        info("\nALL UNITS ONLINE. GitGo STANDING BY. AWAITING COMMANDS...\n")
        return

    if not args.command:
        parser.print_help()
        return

    ensure_first_run_setup()
    check_for_updates_background(get_version())

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
        elif args.command == "undo":
            undo_operations(args)
        elif args.command == "pull":
            pull_operation(args)
    except GitGoError as e:
        error(f"{e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
