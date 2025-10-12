import subprocess
import sys

GITGO_OPERATIONS = ["push", "link"]
HELP_COMMANDS = ["help", "--help", "-h"]

RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
RESET = "\033[0m"


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

    validate_operation(type_of_operation)

    if type_of_operation == "push" and len(arguments) > 2:
        push_operation(arguments)
    elif type_of_operation == "link":
        link_operation(arguments)
    else:
        print(f"\n{RED}Insufficient arguments for {type_of_operation} operation!{RESET}\n")
        sys.exit(1)
