import subprocess
import sys
import os
import shutil

GITGO_OPERATIONS = ["push", "link", "update"]
HELP_COMMANDS = ["help", "--help", "-h"]

RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
RESET = "\033[0m"


def get_current_script_path():
    # get the actual path where gitgo.py is located - no cap
    return os.path.abspath(__file__)


def get_system_gitgo_path():
    # check where the system thinks gitgo is located
    gitgo_path = shutil.which("gitgo")
    if gitgo_path:
        # resolve any symlinks or batch files to get the actual script path
        if gitgo_path.endswith('.bat'):
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
        print(f"\n{YELLOW}⚠️  PATH OUTDATED DETECTED! ⚠️{RESET}")
        print(f"{RED}Your system PATH points to an outdated GitGo location.{RESET}")
        print(f"{YELLOW}Current script: {get_current_script_path()}{RESET}")
        print(f"{YELLOW}System PATH: {get_system_gitgo_path() or 'Not found'}{RESET}")
        print(f"\n{BLUE}To fix this issue, run:{RESET}")
        print(f"{GREEN}    gitgo update{RESET}")
        print(f"{YELLOW}This will update your system PATH to the current location.{RESET}\n")
        return False
    return True


def run_command(command, allow_fail=False):
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        if allow_fail:
            return e
        print(f"\n{RED}Command Failed: {' '.join(command)}{RESET}")
        stderr = e.stderr.strip() if e.stderr else "No error details available"
        print(f"{RED}Error output:\n{stderr}{RESET}\n")
        sys.exit(1)


def git_new_branch(branch):
    print(run_command(["git", "checkout", "-b", branch]))
    print(f"\n{GREEN}Branch '{branch}' created.{RESET}\n")


def git_commit(commit_message):
    status_result = run_command(["git", "status", "--porcelain"], allow_fail=True)
    if isinstance(status_result, subprocess.CalledProcessError) or not status_result.strip():
        return False

    print(run_command(["git", "add", "."]))
    clean_message = commit_message.strip('"\'')
    
    print(run_command(["git", "commit", "-m", clean_message]))
    print(f"\n{GREEN}Changes committed.{RESET}\n")
    return True


def git_init():
    # check if already a git repo - no cap fr fr
    git_check = run_command(["git", "status"], allow_fail=True)
    if not isinstance(git_check, subprocess.CalledProcessError):
        print(f"{YELLOW}Already a git repository! Skipping init...{RESET}")
        return True
    
    print(f"{BLUE}Initializing git repository...{RESET}")
    run_command(["git", "init"])
    print(f"{GREEN}Git repository initialized! 🎯{RESET}")
    return True


def add_remote_origin(repo_url):
    # clean the URL - remove quotes if present, dili na kailangan og quotes
    clean_url = repo_url.strip('"\'')
    
    # check if remote already exists
    existing_remote = run_command(["git", "remote", "get-url", "origin"], allow_fail=True)
    if not isinstance(existing_remote, subprocess.CalledProcessError):
        print(f"{YELLOW}Remote origin already exists: {existing_remote}{RESET}")
        print(f"{YELLOW}Updating to new URL...{RESET}")
        run_command(["git", "remote", "set-url", "origin", clean_url])
    else:
        print(f"{BLUE}Adding remote origin...{RESET}")
        run_command(["git", "remote", "add", "origin", clean_url])
    
    print(f"{GREEN}Remote origin set to: {clean_url} ✨{RESET}")


def confirm_remote_link():
    # test connection to remote - make sure it's not cap
    print(f"{BLUE}Testing connection to remote...{RESET}")
    test_result = run_command(["git", "ls-remote", "origin"], allow_fail=True)
    
    if isinstance(test_result, subprocess.CalledProcessError):
        print(f"{RED}Failed to connect to remote repository! 💀{RESET}")
        print(f"{YELLOW}Please check your repository URL and network connection.{RESET}")
        return False
    
    print(f"{GREEN}Successfully connected to remote repository! 🔗{RESET}")
    return True


def create_main_branch():
    # check current branch - switch to main if needed
    current_branch = run_command(["git", "branch", "--show-current"], allow_fail=True)
    
    if isinstance(current_branch, subprocess.CalledProcessError) or not current_branch.strip():
        # no commits yet, set default branch to main
        print(f"{BLUE}Setting default branch to 'main'...{RESET}")
        run_command(["git", "checkout", "-b", "main"])
    elif current_branch.strip() != "main":
        # rename current branch to main
        print(f"{BLUE}Renaming branch '{current_branch.strip()}' to 'main'...{RESET}")
        run_command(["git", "branch", "-m", "main"])
    else:
        print(f"{GREEN}Already on 'main' branch! 👌{RESET}")
    
    print(f"{GREEN}Main branch ready! 🚀{RESET}")

def check_and_sync_branch(branch):
    try:
        print(f"{YELLOW}Checking if branch is up to date...{RESET}")
        run_command(["git", "fetch", "origin"])

        try:
            local_commit = run_command(["git", "rev-parse", branch])
            remote_commit = run_command(["git", "rev-parse", f"origin/{branch}"])

            if local_commit != remote_commit:
                behind_check = run_command(
                    ["git", "rev-list", "--count", f"{branch}..origin/{branch}"]
                )
                if behind_check and int(behind_check) > 0:
                    print(
                        f"{YELLOW}Local branch is behind remote by {behind_check} commit(s). Pulling changes...{RESET}"
                    )
                    output = run_command(["git", "pull", "--rebase", "origin", branch])
                    if output:
                        print(output)
                    print(f"{GREEN}Successfully synced with remote!{RESET}")
                else:
                    print(f"{GREEN}Branch is up to date or ahead of remote.{RESET}")
            else:
                print(f"{GREEN}Branch is already up to date.{RESET}")
        except:
            print(
                f"{YELLOW}Remote branch doesn't exist yet. First push will create it.{RESET}"
            )
    except:
        print(f"{YELLOW}Could not fetch from remote. Proceeding with push...{RESET}")


def git_push(branch):
    print(run_command(["git", "push", "-u", "origin", branch]))
    print(f"\n{GREEN}Pushed to remote branch '{branch}'.{RESET}\n")


def handle_rebase():
    status = run_command(["git", "status"], allow_fail=True)
    if isinstance(status, subprocess.CalledProcessError):
        return False

    if "rebase in progress" in status or "rebase" in status.lower():
        print(f"\n{YELLOW}Conflict detected!{RESET}")
        print(f"{YELLOW}Please resolve conflicts manually, then run:{RESET}")
        print(f"{BLUE}    git add <files>{RESET}")
        print(f"{BLUE}    git rebase --continue{RESET}")
        print(
            f"{YELLOW}When finished, run 'gitgo push <branch> <message>' again.{RESET}\n"
        )
        sys.exit(1)
    return True


def link_operation(arguments):
    if len(arguments) < 2:
        print(f"\n{RED}GitHub repository URL required!{RESET}")
        print(f"{YELLOW}Usage: gitgo link <github_repo_url> [commit_message]{RESET}\n")
        sys.exit(1)
    
    if arguments[1] in HELP_COMMANDS:
        print(f"\n{YELLOW}Usage: gitgo link <github_repo_url> [commit_message]{RESET}\n")
        print(f"{YELLOW}github_repo_url: The GitHub repository URL to link{RESET}")
        print(f"{YELLOW}commit_message: Custom commit message (default: 'Initial commit'){RESET}\n")
        sys.exit(0)
    
    repo_url = arguments[1]
    commit_message = arguments[2] if len(arguments) > 2 else "Initial commit"
    
    print(f"\n{BLUE}🚀 INITIATING LINK OPERATION...{RESET}")
    print(f"{BLUE}Target: {repo_url}{RESET}\n")
    
    # Step 1: Initialize git repository
    if not git_init():
        return
    
    # Step 2: Add all files - stage everything
    print(f"{BLUE}Adding all files...{RESET}")
    run_command(["git", "add", "."])
    print(f"{GREEN}Files staged for commit! 📁{RESET}")
    
    # Step 3: Create initial commit with custom or default message
    clean_message = commit_message.strip('"\'')
    print(f"{BLUE}Creating initial commit...{RESET}")
    run_command(["git", "commit", "-m", clean_message])
    print(f"{GREEN}Initial commit created! 💾{RESET}")
    
    # Step 4: Add remote origin
    add_remote_origin(repo_url)
    
    # Step 5: Confirm remote link - make sure connection works
    if not confirm_remote_link():
        print(f"{RED}Link operation failed! Check your repository URL.{RESET}")
        return
    
    # Step 6: Create/switch to main branch
    create_main_branch()
    
    print("\n" + ("=" * 90))
    print(f"{GREEN}🎯 LINK OPERATION COMPLETE! REPOSITORY LOCKED AND LOADED!{RESET}")
    print(f"{GREEN}Ready to push with: gitgo push main 'your message'{RESET}")
    print(f"{BLUE}AWAITING FURTHER ORDERS...{RESET}\n")


def push_operation(arguments):
    if arguments[1] in HELP_COMMANDS:
        print(f"\n{YELLOW}Usage: gitgo push [branch] [commit_message]{RESET}\n")
        print(f"{YELLOW}branch: The branch to push to (default: main){RESET}")
        print(
            f"{YELLOW}commit_message: The commit message (default: empty string){RESET}\n"
        )
        sys.exit(0)

    if arguments[1] in ["-n", "new"]:
        if len(arguments) < 3:
            print(f"\n{RED}Branch name required for new branch creation!{RESET}\n")
            sys.exit(1)

        branch = arguments[2]
        git_new_branch(branch)
    else:
        branch = arguments[1]

    commit_made = git_commit(arguments[-1])
    
    if commit_made:
        git_push(branch)
    else:
        try:
            unpushed = run_command(["git", "log", "--oneline", f"origin/{branch}..HEAD"], allow_fail=True)
            if not isinstance(unpushed, subprocess.CalledProcessError) and unpushed.strip():
                print(f"\n{YELLOW}No changes to commit, but found unpushed commits. Pushing to remote...{RESET}")
                git_push(branch)
            else:
                print(f"\n{BLUE}Working tree is clean and everything is up to date! 😎{RESET}")
                print(f"{YELLOW}Make some changes first before using GitGo to commit and push.{RESET}")
                return
        except:
            print(f"\n{YELLOW}No changes to commit. Cannot verify remote status.{RESET}")
            print(f"{YELLOW}Make some changes first or check your git remote configuration.{RESET}")
            return

    print("\n" + ("=" * 90))
    print(
        f"{GREEN}MISSION COMPLETE ✅ — NO CASUALTIES. ALL TARGETS NEUTRALIZED.\nAWAITING FOR YOUR NEXT ORDERS.{RESET}\n\n"
    )


def update_operation(arguments):
    # handle gitgo update command - update PATH to current location
    if len(arguments) > 1 and arguments[1] in HELP_COMMANDS:
        print(f"\n{YELLOW}Usage: gitgo update{RESET}\n")
        print(f"{YELLOW}Updates your system PATH to point to the current GitGo location.{RESET}")
        print(f"{YELLOW}This fixes issues when GitGo is moved to a different directory.{RESET}\n")
        sys.exit(0)
    
    print(f"\n{BLUE}🔧 INITIATING PATH UPDATE OPERATION...{RESET}")
    
    current_script = get_current_script_path()
    current_dir = os.path.dirname(current_script)
    
    print(f"{BLUE}Current GitGo location: {current_dir}{RESET}")
    
    # create or update batch file in a system-accessible location
    try:
        # try to use a common system path location
        system_paths = [
            os.path.expanduser("~\\AppData\\Local\\Microsoft\\WindowsApps"),
            "C:\\Windows\\System32",
            os.path.expanduser("~\\bin")
        ]
        
        target_dir = None
        for path in system_paths:
            if os.path.exists(path) and os.access(path, os.W_OK):
                target_dir = path
                break
        
        if not target_dir:
            # create user bin directory if none available
            target_dir = os.path.expanduser("~\\bin")
            os.makedirs(target_dir, exist_ok=True)
        
        batch_file = os.path.join(target_dir, "gitgo.bat")
        
        # create batch file that points to current script
        batch_content = f'@echo off\npython "{current_script}" %*\n'
        
        with open(batch_file, 'w') as f:
            f.write(batch_content)
        
        print(f"{GREEN}✅ Batch file created: {batch_file}{RESET}")
        
        # check if target_dir is in PATH
        current_path = os.environ.get('PATH', '')
        if target_dir.lower() not in current_path.lower():
            print(f"\n{YELLOW}⚠️  MANUAL ACTION REQUIRED ⚠️{RESET}")
            print(f"{YELLOW}Add this directory to your system PATH:{RESET}")
            print(f"{GREEN}    {target_dir}{RESET}")
            print(f"\n{BLUE}How to add to PATH:{RESET}")
            print(f"{YELLOW}1. Press Win + R, type 'sysdm.cpl', press Enter{RESET}")
            print(f"{YELLOW}2. Click 'Environment Variables' button{RESET}")
            print(f"{YELLOW}3. Under 'User variables', find and select 'Path', click 'Edit'{RESET}")
            print(f"{YELLOW}4. Click 'New' and add: {target_dir}{RESET}")
            print(f"{YELLOW}5. Click 'OK' on all dialogs{RESET}")
            print(f"{YELLOW}6. Restart your terminal{RESET}")
        else:
            print(f"{GREEN}✅ Directory already in PATH!{RESET}")
        
        print(f"\n{GREEN}🎯 PATH UPDATE COMPLETE!{RESET}")
        print(f"{BLUE}GitGo should now work from any location.{RESET}")
        print(f"{YELLOW}If issues persist, restart your terminal.{RESET}\n")
        
    except Exception as e:
        print(f"\n{RED}❌ Update failed: {str(e)}{RESET}")
        print(f"{YELLOW}You may need to run this command as Administrator.{RESET}\n")
        sys.exit(1)


def validate_operation(operation):
    if operation not in GITGO_OPERATIONS:
        print(f"\n{RED}Invalid operation '{operation}'!{RESET}")
        print(
            f"{YELLOW}Supported operations are: {', '.join(GITGO_OPERATIONS)}{RESET}\n"
        )
        sys.exit(1)


if __name__ == "__main__":

    if len(sys.argv) < 2:
        print(f"\n{RED}Invalid arguments!{RESET}\n")
        sys.exit(1)

    arguments = sys.argv[1:]
    type_of_operation = arguments[0].lower()

    if type_of_operation in ["-r", "ready"]:
        print(
            f"\n{BLUE}ALL UNITS ONLINE. GitGo STANDING BY. AWAITING COMMANDS...{RESET}\n"
        )
        sys.exit(0)

    if type_of_operation in HELP_COMMANDS:
        print(f"\n{YELLOW}Usage: Help Manual for gitgo{RESET}\n")
        print(f"{YELLOW}" + "=" * 50 + f"{RESET}")
        print(f"{YELLOW}Feature is currently in development.{RESET}\n")
        sys.exit(0)

    # handle update operation first - no path validation needed for update
    if type_of_operation == "update":
        update_operation(arguments)
        sys.exit(0)

    validate_operation(type_of_operation)

    # check path validity for all operations except update - lowkey important
    if not check_path_validity():
        print(f"{RED}Operation aborted due to outdated PATH.{RESET}")
        print(f"{YELLOW}Please run 'gitgo update' first to fix the issue.{RESET}\n")
        sys.exit(1)

    if type_of_operation == "push" and len(arguments) > 2:
        push_operation(arguments)
    elif type_of_operation == "link":
        link_operation(arguments)
    else:
        print(f"\n{RED}Insufficient arguments for {type_of_operation} operation!{RESET}\n")
        sys.exit(1)
