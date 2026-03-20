from auth.ssh_utils import ensure_github_known_host
from commands.git_operations import (
    git_new_branch, git_commit, git_init, add_remote_origin,
    confirm_remote_link, create_main_branch, check_and_sync_branch,
    git_push, handle_rebase, get_current_branch, is_branch_exist
)
from commands.path_manager import check_path_validity, update_operation
from commands.state import state_operations
from utils.executor import run_command
from auth.manager import login, logout
from auth.account import get_user
from utils.colors import info, success, warning, error, highlight
import subprocess
import sys


GITGO_OPERATIONS = ["push", "link", "update", "state", "user"]
HELP_COMMANDS = ["help", "--help", "-h"]
DEFAULT_COMMIT_MSG = "New Project Update"
DEFAULT_MAIN_BRANCH = "main"


def link_operation(arguments):
    if len(arguments) < 2:
        error("\nGitHub repository URL required!")
        warning("Usage: gitgo link <github_repo_url> [commit_message]\n")
        sys.exit(1)
    
    if arguments[1] in HELP_COMMANDS:
        warning("\nUsage: gitgo link <github_repo_url> [commit_message]\n")
        warning("github_repo_url: The GitHub repository URL to link")
        warning("commit_message: Custom commit message (default: 'Initial commit')\n")
        sys.exit(0)
    
    repo_url = arguments[1]
    commit_message = arguments[2] if len(arguments) > 2 else "Initial commit"
    
    info("\n🚀 INITIATING LINK OPERATION...")
    info(f"Target: {repo_url}\n")
    
    if not git_init():
        return
    
    info("Adding all files...")
    run_command(["git", "add", "."])
    success("Files staged for commit! 📁")
    
    clean_message = commit_message.strip('"\'')
    info("Creating initial commit...")
    run_command(["git", "commit", "-m", clean_message])
    success("Initial commit created! 💾")
    
    add_remote_origin(repo_url)
    
    if not confirm_remote_link():
        error("Link operation failed! Check your repository URL.")
        return
    
    current_branch = get_current_branch()
    if current_branch.strip() != DEFAULT_MAIN_BRANCH:
        info(f"Renaming branch '{current_branch.strip()}' to '{DEFAULT_MAIN_BRANCH}'...")
        run_command(["git", "branch", "-m", DEFAULT_MAIN_BRANCH])
        current_branch = DEFAULT_MAIN_BRANCH
    
    remote_refs = run_command(["git", "ls-remote", "--heads", "origin", DEFAULT_MAIN_BRANCH], allow_fail=True)
    if not isinstance(remote_refs, subprocess.CalledProcessError) and remote_refs.strip():
        info("Remote branch has existing commits. Pulling and merging...")
        pull_result = run_command(
            ["git", "pull", "origin", DEFAULT_MAIN_BRANCH, "--allow-unrelated-histories", "--no-edit"],
            allow_fail=True
        )
        if isinstance(pull_result, subprocess.CalledProcessError):
            error("Failed to merge remote content. You may need to resolve conflicts manually.")
            warning("Run: git pull origin main --allow-unrelated-histories")
            warning("Then: gitgo push main 'your message'\n")
            return
        success("Remote content merged successfully! 🔄")
    
    print("\n" + ("=" * 90))
    success("🎯 LINK OPERATION COMPLETE! REPOSITORY LOCKED AND LOADED!")
    success(f"Ready to push with: gitgo push {DEFAULT_MAIN_BRANCH} 'your message'")
    info("AWAITING FURTHER ORDERS...\n")

    user_choice = input(f"\nDo you want to push now? (y/n): ").lower()
    if user_choice != 'y':
        return
    
    git_push(current_branch)
    
    print("\n" + ("=" * 90))
    success("MISSION COMPLETE ✅ — REPOSITORY INITIALIZED AND PUSHED!\nAWAITING FOR YOUR NEXT ORDERS.\n\n")
    

def push_operation(arguments):
    if len(arguments) > 1 and arguments[1] in HELP_COMMANDS:
        warning("\nUsage: gitgo push [branch] [commit_message]\n")
        warning("branch: The branch to push to (default: main)")
        warning("commit_message: The commit message (default: empty string)\n")
        sys.exit(0)
    
    branch = None
    message = None

    if len(arguments) > 1 and arguments[1] in ["-n", "new"]:
        # [push, -n, branch, commit_msg]
        if len(arguments) < 3:
            error("\nBranch name required for new branch creation!\n")
            sys.exit(1)
        elif len(arguments) < 4:
            message = DEFAULT_COMMIT_MSG
        elif len(arguments) > 4:
            error("\nToo many arguments for new branch creation!\n")
            sys.exit(1)

        branch = arguments[2]
        git_new_branch(branch)
    else:
        # [push, branch, commit_msg]
        if len(arguments) < 2:
            branch = get_current_branch()
            message = DEFAULT_COMMIT_MSG
        elif len(arguments) < 3:
            if is_branch_exist(arguments[1]):
                message = DEFAULT_COMMIT_MSG
            else:
                branch = get_current_branch()
                message = arguments[1]
        elif len(arguments) > 3:
            error("\nToo many arguments!\n")
            sys.exit(1)

        branch = branch if branch else arguments[1]

    message = message if message else arguments[-1]

    commit_made = git_commit(message)
    
    if commit_made:
        git_push(branch)
    else:
        try:
            unpushed = run_command(["git", "log", "--oneline", f"origin/{branch}..HEAD"], allow_fail=True)
            if not isinstance(unpushed, subprocess.CalledProcessError) and unpushed.strip():
                warning("\nNo changes to commit, but found unpushed commits. Pushing to remote...")
                git_push(branch)
            else:
                info("\nWorking tree is clean and everything is up to date! 😎")
                warning("Make some changes first before using GitGo to commit and push.")
                return
        except:
            warning("\nNo changes to commit. Cannot verify remote status.")
            warning("Make some changes first or check your git remote configuration.")
            return

    print("\n" + ("=" * 90))
    success("MISSION COMPLETE ✅ — NO CASUALTIES. ALL TARGETS NEUTRALIZED.\nAWAITING FOR YOUR NEXT ORDERS.\n\n")


def validate_operation(operation):
    if operation not in GITGO_OPERATIONS:
        error(f"\nInvalid operation '{operation}'!")
        warning(f"Supported operations are: {', '.join(GITGO_OPERATIONS)}\n")
        sys.exit(1)

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


def user_management(operation):
    if not operation:
        display_current_user()
        exit(0)
    if len(operation) > 1:
        if operation[1] in HELP_COMMANDS:
            if operation[0] == "login":
                info("\nUsage: gitgo user login\n")
                info("Sets up your Git user identity (name and email) for commits.\n")
            elif operation[0] == "logout":
                info("\nUsage: gitgo user logout\n")
                info("Removes your Git user identity configuration.\n")
            else:
                warning("\nUsage: gitgo user <login | logout>\n")
                warning("login: Configure your Git user identity.")
                warning("logout: Remove your Git user identity configuration.\n")
            sys.exit(0)
        else:
            error("\nToo many arguments for user management!\n")
            sys.exit(1)

    if operation[0] == "login":
        login()
    elif operation[0] == "logout":
        logout()
    elif operation[0] in HELP_COMMANDS:
        warning("\nUsage: gitgo user <login | logout>\n")
        warning("login: Configure your Git user identity.")
        warning("logout: Remove your Git user identity configuration.\n")
        sys.exit(0)
    else:
        error(f"\nInvalid user operation '{operation[0]}'!\n")
        sys.exit(1)


def main():
    if len(sys.argv) < 2:
        error("\nInvalid arguments!\n")
        sys.exit(1)

    arguments = sys.argv[1:]

    type_of_operation = arguments[0].lower()

    if type_of_operation in ["-r", "ready"]:
        info("\nALL UNITS ONLINE. GitGo STANDING BY. AWAITING COMMANDS...\n")
        sys.exit(0)

    if type_of_operation in ["-v", "version"]:
        highlight("\nGitGo Version 1.0\n")
        sys.exit(0)

    if type_of_operation in HELP_COMMANDS:
        warning("\nUsage: Help Manual for gitgo\n")
        warning("=" * 50)
        warning("Feature is currently in development.\n")
        sys.exit(0)

    if type_of_operation == "update":
        update_operation(arguments)
        sys.exit(0)

    validate_operation(type_of_operation)

    if not check_path_validity():
        error("Operation aborted due to outdated PATH.")
        warning("Please run 'gitgo update' first to fix the issue.\n")
        sys.exit(1)

    ensure_github_known_host()

    if type_of_operation == "push":
        push_operation(arguments)
    elif type_of_operation == "link":
        link_operation(arguments)
    elif type_of_operation == "state":
        state_operations(arguments[1:])
    elif type_of_operation == "user":
        user_management(arguments[1:])
    else:
        error(f"\nInsufficient arguments for {type_of_operation} operation!\n")
        sys.exit(1)


if __name__ == "__main__":
    main()