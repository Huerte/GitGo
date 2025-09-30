import subprocess
import sys

GITGO_OPERATIONS = ['push']
HELP_COMMANDS = ['help', '--help', '-h']

RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
RESET = "\033[0m"


def run_command(command):
    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        print(f"\n{RED}Command Failed: {' '.join(command)}{RESET}")
        print(f"{RED}Error output:\n{e.stderr.strip()}{RESET}\n")
        sys.exit(1)


def git_new_branch(branch):
    print(run_command(['git', 'checkout', '-b', branch]))
    print(f"\n{GREEN}Branch '{branch}' created.{RESET}\n")


def git_commit(commit_message):
    print(run_command(['git', 'add', '.']))
    print(run_command(['git', 'commit', '-m', f"{commit_message}"]))
    print(f"\n{GREEN}Changes committed.{RESET}\n")


def git_push(branch):
    print(run_command(['git', 'push', '-u', 'origin', branch]))
    print(f"\n{GREEN}Pushed to remote branch '{branch}'.{RESET}\n")


def push_operation(arguments):
    if arguments[1] in HELP_COMMANDS:
        print(f"\n{YELLOW}Usage: gitgo push [branch] [commit_message]{RESET}\n")
        print(f"{YELLOW}branch: The branch to push to (default: main){RESET}")
        print(f"{YELLOW}commit_message: The commit message (default: empty string){RESET}\n")
        sys.exit(0)
        
    if arguments[1] in ['-n', 'new']:
        if len(arguments) < 3:
            print(f"\n{RED}Branch name required for new branch creation!{RESET}\n")
            sys.exit(1)
            
        branch = arguments[2]
        git_new_branch(branch)
    else:
        branch = arguments[1]
        
    git_commit(arguments[-1])
    git_push(branch)
    
    print("\n" + ("=" * 90))
    print(f"{GREEN}MISSION COMPLETE ✅ — NO CASUALTIES. ALL TARGETS NEUTRALIZED.\nAWAITING FOR YOUR NEXT ORDERS.{RESET}\n\n")


def validate_operation(operation):
    if operation not in GITGO_OPERATIONS:
        print(f"\n{RED}Invalid operation '{operation}'!{RESET}")
        print(f"{YELLOW}Supported operations are: {', '.join(GITGO_OPERATIONS)}{RESET}\n")
        sys.exit(1)


if __name__ == "__main__":

    if len(sys.argv) < 2:
        print(f"\n{RED}Invalid arguments!{RESET}\n")
        sys.exit(1)
    
    arguments = sys.argv[1:]
    type_of_operation = arguments[0].lower()

    if type_of_operation in ['-r', 'ready']:
        print(f"\n{BLUE}ALL UNITS ONLINE. GitGo STANDING BY. AWAITING COMMANDS...{RESET}\n")
        sys.exit(0)

    if type_of_operation in HELP_COMMANDS:
        print(f"\n{YELLOW}Usage: Help Manual for gitgo{RESET}\n")
        print(f"{YELLOW}" + '=' * 50 + f"{RESET}")
        print(f"{YELLOW}Feature is currently in development.{RESET}\n")
        sys.exit(0)
    
    validate_operation(type_of_operation)
    
    if type_of_operation == 'push' and len(arguments) > 2:
        push_operation(arguments)
    else:
        print(f"\n{RED}Insufficient arguments for push operation!{RESET}\n")
        sys.exit(1)
