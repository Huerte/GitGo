import subprocess
import sys

GITGO_OPERATIONS = ["push"]
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
        # Fix the AttributeError - safely handle None stderr
        stderr = e.stderr.strip() if e.stderr else "No error details available"
        print(f"{RED}Error output:\n{stderr}{RESET}\n")
        sys.exit(1)


def git_new_branch(branch):
    print(run_command(["git", "checkout", "-b", branch]))
    print(f"\n{GREEN}Branch '{branch}' created.{RESET}\n")


def git_commit(commit_message):
    # Check if there are any changes to commit first - walang utang na loob kung walang changes! 😤
    status_result = run_command(["git", "status", "--porcelain"], allow_fail=True)
    if isinstance(status_result, subprocess.CalledProcessError) or not status_result.strip():
        return False

    print(run_command(["git", "add", "."]))
    clean_message = commit_message.strip('"\'')
    
    print(run_command(["git", "commit", "-m", clean_message]))
    print(f"\n{GREEN}Changes committed.{RESET}\n")
    return True

def check_and_sync_branch(branch):
    """Check if local branch is behind remote and sync if needed - no more rejected pushes, fam! 💪"""
    try:
        # Fetch latest changes from remote
        print(f"{YELLOW}Checking if branch is up to date...{RESET}")
        run_command(["git", "fetch", "origin"])

        # Check if local branch is behind remote
        try:
            local_commit = run_command(["git", "rev-parse", branch])
            remote_commit = run_command(["git", "rev-parse", f"origin/{branch}"])

            if local_commit != remote_commit:
                # Check if we're behind (not ahead)
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
            # Remote branch might not exist yet, that's okay for first push
            print(
                f"{YELLOW}Remote branch doesn't exist yet. First push will create it.{RESET}"
            )
    except:
        # If fetch fails, continue anyway (might be offline or no remote)
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
    
    # Check if we need to push - baka naman may existing commits na di pa na-push 🤔
    if commit_made:
        git_push(branch)
    else:
        # No new changes to commit, check if there are unpushed commits
        try:
            unpushed = run_command(["git", "log", "--oneline", f"origin/{branch}..HEAD"], allow_fail=True)
            if not isinstance(unpushed, subprocess.CalledProcessError) and unpushed.strip():
                print(f"\n{YELLOW}No changes to commit, but found unpushed commits. Pushing to remote...{RESET}")
                git_push(branch)
            else:
                print(f"\n{BLUE}Working tree is clean and everything is up to date! 😎{RESET}")
                print(f"{YELLOW}Make some changes first before using GitGo to commit and push.{RESET}")
                return  # Exit early, no mission complete message needed
        except:
            # If we can't check, inform user about the situation
            print(f"\n{YELLOW}No changes to commit. Cannot verify remote status.{RESET}")
            print(f"{YELLOW}Make some changes first or check your git remote configuration.{RESET}")
            return  # Exit early, no mission complete message needed

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
    else:
        print(f"\n{RED}Insufficient arguments for push operation!{RESET}\n")
        sys.exit(1)
