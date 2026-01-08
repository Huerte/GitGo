from auth.ssh_utils import ensure_github_known_host, convert_https_to_ssh, is_ssh_url, check_connection
from commands.state import state_operations
from commands.clean import clean_project
from utils.executor import run_command
from auth.manager import login, logout
from utils.platform_utils import *
from auth.account import get_user
from utils.colors import *
import subprocess
import shutil
import sys
import os


GITGO_OPERATIONS = ["push", "link", "update", "state", "clean", "user"]
HELP_COMMANDS = ["help", "--help", "-h"]


def get_current_script_path():
    # get the actual path where gitgo.py is located - no cap
    return os.path.abspath(__file__)


def get_system_gitgo_path():
    # check where the system thinks gitgo is located
    gitgo_path = shutil.which("gitgo")
    if gitgo_path:
        # resolve any symlinks or batch files to get the actual script path
        if is_windows() and gitgo_path.endswith('.bat'):
            # Windows batch file - extract python script path
            try:
                with open(gitgo_path, 'r') as f:
                    content = f.read()
                    # look for python script path in batch file
                    for line in content.split('\n'):
                        if 'python' in line.lower() and 'gitgo.py' in line:
                            # extract the path - basic parsing, might need adjustment
                            parts = line.split()
                            for part in parts:
                                if 'gitgo.py' in part:
                                    return os.path.abspath(part.strip('"\''))
            except:
                pass
        else:
            # Unix shell script - extract python script path
            try:
                with open(gitgo_path, 'r') as f:
                    content = f.read()
                    # look for exec python line
                    for line in content.split('\n'):
                        if 'exec' in line and 'gitgo.py' in line:
                            # extract the path from exec command
                            parts = line.split()
                            for part in parts:
                                if 'gitgo.py' in part:
                                    return os.path.abspath(part.strip('"\''))
            except:
                pass
    return gitgo_path


def is_path_outdated():
    # check if the current script location matches system PATH - lowkey important
    current_path = get_current_script_path()
    system_path = get_system_gitgo_path()
    
    if not system_path:
        return True  # gitgo not in PATH at all
    
    # normalize paths for comparison
    try:
        current_dir = os.path.dirname(current_path)
        system_dir = os.path.dirname(os.path.abspath(system_path))
        return current_dir != system_dir
    except:
        return True  # if we can't determine, assume outdated


def check_path_validity():
    # validate path and warn user if needed - fr fr this is important
    if is_path_outdated():
        warning("\n⚠️  PATH OUTDATED DETECTED! ⚠️")
        error("Your system PATH points to an outdated GitGo location.")
        warning(f"Current script: {get_current_script_path()}")
        warning(f"System PATH: {get_system_gitgo_path() or 'Not found'}")
        warning(f"Platform: {get_platform_display_name()}")

        info("\nTo fix this issue, run:")
        success("    gitgo update")
        warning("This will update your wrapper script to the current location.\n")
        return False
    return True




def git_new_branch(branch):
    print(run_command(["git", "checkout", "-b", branch]))
    success(f"\nBranch '{branch}' created.\n")


def git_commit(commit_message):
    status_result = run_command(["git", "status", "--porcelain"], allow_fail=True)
    if isinstance(status_result, subprocess.CalledProcessError) or not status_result.strip():
        return False

    print(run_command(["git", "add", "."]))
    clean_message = commit_message.strip('"\'')
    
    print(run_command(["git", "commit", "-m", clean_message]))

    success("\nChanges committed.\n")
    return True


def git_init():
    # check if already a git repo - no cap fr fr
    git_check = run_command(["git", "status"], allow_fail=True)
    if not isinstance(git_check, subprocess.CalledProcessError):
        warning("Already a git repository! Skipping init...")
        return True
    
    info("Initializing git repository...")
    run_command(["git", "init"])

    success("Git repository initialized! 🎯")
    return True


def add_remote_origin(repo_url):
    # clean the URL - remove quotes if present, dili na kailangan og quotes
    clean_url = repo_url.strip('"\'')
    
    # check if remote already exists
    existing_remote = run_command(["git", "remote", "get-url", "origin"], allow_fail=True)
    if not isinstance(existing_remote, subprocess.CalledProcessError):
        warning(f"Remote origin already exists: {existing_remote}")
        warning("Updating to new URL...")
        run_command(["git", "remote", "set-url", "origin", clean_url])
    else:
        info("Adding remote origin...")
        run_command(["git", "remote", "add", "origin", clean_url])
    
    success("Remote origin set to: {clean_url} ✨")


def confirm_remote_link():
    # test connection to remote - make sure it's not cap
    info("Testing connection to remote...")
    test_result = run_command(["git", "ls-remote", "origin"], allow_fail=True)
    
    if isinstance(test_result, subprocess.CalledProcessError):
        error("Failed to connect to remote repository! 💀")
        warning("Please check your repository URL and network connection.")
        return False
    
    success("Successfully connected to remote repository! 🔗")
    return True


def create_main_branch():
    # check current branch - switch to main if needed
    current_branch = run_command(["git", "branch", "--show-current"], allow_fail=True)
    
    if isinstance(current_branch, subprocess.CalledProcessError) or not current_branch.strip():
        # no commits yet, set default branch to main
        info("Setting default branch to 'main'...")
        run_command(["git", "checkout", "-b", "main"])
    elif current_branch.strip() != "main":
        # rename current branch to main
        info(f"Renaming branch '{current_branch.strip()}' to 'main'...")
        run_command(["git", "branch", "-m", "main"])
    else:
        success("Already on 'main' branch! 👌")
    
    success("Main branch ready! 🚀")


def check_and_sync_branch(branch):
    try:
        warning("Checking if branch is up to date...")
        run_command(["git", "fetch", "origin"])

        try:
            local_commit = run_command(["git", "rev-parse", branch])
            remote_commit = run_command(["git", "rev-parse", f"origin/{branch}"])

            if local_commit != remote_commit:
                behind_check = run_command(
                    ["git", "rev-list", "--count", f"{branch}..origin/{branch}"]
                )
                if behind_check and int(behind_check) > 0:
                    warning(f"Local branch is behind remote by {behind_check} commit(s). Pulling changes...")
                    output = run_command(["git", "pull", "--rebase", "origin", branch])
                    if output:
                        print(output)
                    success("Successfully synced with remote!")
                else:
                    success("Branch is up to date or ahead of remote.")
            else:
                success("Branch is already up to date.")
        except:
            warning("Remote branch doesn't exist yet. First push will create it.")
    except:
        warning("Could not fetch from remote. Proceeding with push...")


def git_push(branch):
    # Check if remote is using HTTPS and SSH is available
    remote_url = run_command(["git", "remote", "get-url", "origin"], allow_fail=True)
    
    if not isinstance(remote_url, subprocess.CalledProcessError) and remote_url:
        remote_url = remote_url.strip()
        
        # If using HTTPS and SSH is set up, convert to SSH
        if not is_ssh_url(remote_url) and check_connection():
            ssh_url = convert_https_to_ssh(remote_url)
            if ssh_url:
                info(f"Converting remote from HTTPS to SSH for secure push...")
                run_command(["git", "remote", "set-url", "origin", ssh_url])
                success(f"Remote updated to: {ssh_url}")
    
    print(run_command(["git", "push", "-u", "origin", branch]))
    success(f"\nPushed to remote branch '{branch}'.\n")


def handle_rebase():
    status = run_command(["git", "status"], allow_fail=True)
    if isinstance(status, subprocess.CalledProcessError):
        return False

    if "rebase in progress" in status or "rebase" in status.lower():
        warning("\nConflict detected!")
        warning("Please resolve conflicts manually, then run:")
        info("    git add <files>")
        info("    git rebase --continue")
        warning("When finished, run 'gitgo push <branch> <message>' again.\n")
        sys.exit(1)

    return True


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
    
    # Step 1: Initialize git repository
    if not git_init():
        return
    
    # Step 2: Add all files - stage everything
    info("Adding all files...")
    run_command(["git", "add", "."])
    success("Files staged for commit! 📁")
    
    # Step 3: Create initial commit with custom or default message
    clean_message = commit_message.strip('"\'')
    info("Creating initial commit...")
    run_command(["git", "commit", "-m", clean_message])
    success("Initial commit created! 💾")
    
    # Step 4: Add remote origin
    add_remote_origin(repo_url)
    
    # Step 5: Confirm remote link - make sure connection works
    if not confirm_remote_link():
        error("Link operation failed! Check your repository URL.")
        return
    
    # Step 6: Create/switch to main branch
    create_main_branch()
    
    print("\n" + ("=" * 90))
    success("🎯 LINK OPERATION COMPLETE! REPOSITORY LOCKED AND LOADED!")
    success("Ready to push with: gitgo push main 'your message'")
    info("AWAITING FURTHER ORDERS...\n")


def push_operation(arguments):
    if arguments[1] in HELP_COMMANDS:
        warning("\nUsage: gitgo push [branch] [commit_message]\n")
        warning("branch: The branch to push to (default: main)")
        warning("commit_message: The commit message (default: empty string)\n")
        sys.exit(0)

    if arguments[1] in ["-n", "new"]:
        if len(arguments) < 3:
            error("\nBranch name required for new branch creation!\n")
            sys.exit(1)
        elif len(arguments) < 4:
            error("\nCommit message required!\n")
            sys.exit(1)
        elif len(arguments) > 4:
            error("\nToo many arguments for new branch creation!\n")
            sys.exit(1)

        branch = arguments[2]
        git_new_branch(branch)
    else:
        if len(arguments) < 2:
            error("\nBranch name required!\n")
            sys.exit(1)
        elif len(arguments) < 3:
            error("\nCommit message required!\n")
            sys.exit(1)
        elif len(arguments) > 3:
            error("\nToo many arguments!\n")
            sys.exit(1)

        branch = arguments[1]

    commit_made = git_commit(arguments[-1])
    
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


def update_operation(arguments):
    # handle gitgo update command - update wrapper to current location (cross-platform)
    if len(arguments) > 1 and arguments[1] in HELP_COMMANDS:
        warning("\nUsage: gitgo update\n")
        warning("Updates your gitgo wrapper to point to the current GitGo location.")
        warning("This fixes issues when GitGo is moved to a different directory.\n")
        sys.exit(0)
    
    info(f"\n🔧 INITIATING UPDATE OPERATION... [{get_platform_display_name()}]")
    
    current_script = get_current_script_path()
    current_dir = os.path.dirname(current_script)
    
    info(f"Current GitGo location: {current_dir}")
    
    # create or update wrapper script in a system-accessible location
    try:
        # Get platform-specific bin directory
        target_dir = get_bin_directory()
        
        if not os.path.exists(target_dir):
            os.makedirs(target_dir, exist_ok=True)
            success(f"✅ Created directory: {target_dir}")
        
        # Get wrapper filename (gitgo.bat for Windows, gitgo for Unix)
        wrapper_name = get_executable_name()
        wrapper_path = os.path.join(target_dir, wrapper_name)
        
        # Create wrapper content
        wrapper_content = create_wrapper_script(current_script, current_dir)
        
        # Write wrapper file
        with open(wrapper_path, 'w', newline='\n' if not is_windows() else None) as f:
            f.write(wrapper_content)
        
        # Make executable on Unix systems
        if not is_windows():
            import stat
            os.chmod(wrapper_path, os.stat(wrapper_path).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        
        success(f"✅ Wrapper created: {wrapper_path}")
        
        # Check if target_dir is in PATH
        if not is_in_path(target_dir):
            warning("\n⚠️  MANUAL ACTION REQUIRED ⚠️")
            warning("Add this directory to your system PATH:")
            success(f"    {target_dir}")
            
            if is_windows():
                info("\nHow to add to PATH on Windows:")
                warning("1. Press Win + R, type 'sysdm.cpl', press Enter")
                warning("2. Click 'Environment Variables' button")
                warning("3. Under 'User variables', find and select 'Path', click 'Edit'")
                warning(f"4. Click 'New' and add: {target_dir}")
                warning("5. Click 'OK' on all dialogs")
                warning("6. Restart your terminal")
            else:
                info("\nHow to add to PATH on Linux/Termux:")
                warning("Add this line to your shell configuration file (~/.bashrc or ~/.zshrc):")
                success(f"    export PATH=\"$PATH:{target_dir}\"")
                warning("\nThen run: source ~/.bashrc (or ~/.zshrc)")
        else:
            success("✅ Directory already in PATH!")
        
        success("\n🎯 UPDATE COMPLETE!")
        info("GitGo should now work from any location.")
        warning("If issues persist, restart your terminal.")
    
    except Exception as e:
        error(f"❌ Update failed: {str(e)}")
        if is_windows():
            warning("You may need to run this command as Administrator.")
        else:
            warning("Check file permissions and try again.")
        sys.exit(1)


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

    # This list will return all arguments except the script name "gitgo"
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

    # handle update operation first - no path validation needed for update
    if type_of_operation == "update":
        update_operation(arguments)
        sys.exit(0)

    validate_operation(type_of_operation)

    # check path validity for all operations except update - lowkey important
    if not check_path_validity():
        error("Operation aborted due to outdated PATH.")
        warning("Please run 'gitgo update' first to fix the issue.\n")
        sys.exit(1)

    ensure_github_known_host()

    if type_of_operation == "push" and len(arguments) >= 2:
        push_operation(arguments)
    elif type_of_operation == "link":
        link_operation(arguments)
    elif type_of_operation == "clean":
        clean_project(arguments)
    elif type_of_operation == "state":
        state_operations(arguments[1:]) # This only passes the argument like load, save, delete
    elif type_of_operation == "user":
        user_management(arguments[1:])
    else:
        error(f"\nInsufficient arguments for {type_of_operation} operation!\n")
        sys.exit(1)


if __name__ == "__main__":
    main()