from pygitgo.commands.git_branch import is_branch_exist, get_current_branch
from pygitgo.utils.colors import YELLOW, CYAN, GREEN, RESET
from pygitgo.exceptions import GitCommandError, GitGoError
from pygitgo.utils.cli_io import info, write, banner
from pygitgo.utils.executor import run_command

def log_operation(args):
    number = args.number
    branch = args.branch
    
    try:
        run_command(["git", "rev-parse", "--is-inside-work-tree"])
    except GitCommandError:
        raise GitGoError("Not inside a git repository. Run 'gitgo init' or 'gitgo link' first.")
    
    try:
        run_command(["git", "rev-parse", "HEAD"])
    except GitCommandError:
        info("No commits found in this repository.")
        return

    if branch:
        if not is_branch_exist(branch):
            raise GitGoError(f"Branch '{branch}' does not exist.")
        target_branch = branch
    else:
        try:
            target_branch = get_current_branch()
        except Exception:
            target_branch = ""

    command = [
        "git", "log", 
        f"-n{number}",
        "--pretty=format:%h||%an||%cr||%s"
    ]
    
    if branch:
        command.append(branch)
        
    try:
        output = run_command(command)
        if not output:
            info("No commits found.")
            return
            
        banner_subtitle = f"Showing last {number} commits"
        if target_branch:
            banner_subtitle += f" on {target_branch}"
            
        banner("Commit History", banner_subtitle)
        
        for line in output.splitlines():
            try:
                commit_hash, author, date, message = line.split("||", 3)
                write(f"[{YELLOW}{commit_hash}{RESET}] {message} ({CYAN}{date}{RESET}) [{GREEN}{author}{RESET}]")
            except ValueError:
                write(line)
        write()
    except GitCommandError as e:
        raise GitGoError(f"Failed to retrieve log: {getattr(e, 'stderr', str(e))}")
