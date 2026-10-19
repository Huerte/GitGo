from pygitgo.commands.git_branch import is_branch_exist, get_current_branch
from pygitgo.utils.colors import YELLOW, CYAN, GREEN, RED, BLUE, RESET
from pygitgo.exceptions import GitCommandError, GitGoError
from pygitgo.utils.cli_io import info, write, banner
from pygitgo.utils.executor import run_command

def _format_refs(refs):
    """Turn git's %D text into a short coloured label, e.g. (main, origin/main, v1.2)."""
    names = []
    for part in refs.split(", "):
        part = part.strip()
        if not part:
            continue
        if part.startswith("HEAD -> "):
            names.append(f"{GREEN}HEAD -> {part[len('HEAD -> '):]}{RESET}{BLUE}")
        elif part == "HEAD":
            names.append(f"{GREEN}HEAD")
        elif part.startswith("tag: "):
            names.append(f"{YELLOW}{part[5:]}{BLUE}")
        else:
            names.append(part)
    return f" {BLUE}({', '.join(names)}){RESET}" if names else ""


def _unpushed_hashes(branch):
    """Short hashes of commits not yet on the upstream, or None when there is no upstream."""
    target = branch or "HEAD"
    upstream = f"{branch}@{{u}}" if branch else "@{u}"
    try:
        out = run_command(["git", "log", "--pretty=format:%h", f"{upstream}..{target}"])
    except Exception:
        return None
    return set(out.split())


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
        "--pretty=format:@@%h||%an||%cr||%D||%s"
    ]
    if getattr(args, "graph", False):
        command.insert(2, "--graph")
    
    filters = []
    for flag, attr in (("--author", "author"), ("--since", "since"), ("--grep", "grep")):
        value = getattr(args, attr, None)
        if value:
            command.append(f"{flag}={value}")
            filters.append(f"{attr}: {value}")

    if branch:
        command.append(branch)
        
    try:
        output = run_command(command)
        if not output:
            info("No commits match those filters." if filters else "No commits found.")
            return
            
        banner_subtitle = f"Showing last {number} commits"
        if target_branch:
            banner_subtitle += f" on {target_branch}"
        if filters:
            banner_subtitle += f" ({', '.join(filters)})"
            
        banner("Commit History", banner_subtitle, required=True)
        
        unpushed = _unpushed_hashes(branch)

        for line in output.splitlines():
            if "@@" in line:
                prefix, rest = line.split("@@", 1)
                try:
                    commit_hash, author, date, refs, message = rest.split("||", 4)
                except ValueError:
                    write(line, required=True)
                    continue
                tag = f" {RED}[unpushed]{RESET}" if unpushed and commit_hash in unpushed else ""
                write(
                    f"{BLUE}{prefix}{RESET}[{YELLOW}{commit_hash}{RESET}] {message}{_format_refs(refs)}{tag} "
                    f"({CYAN}{date}{RESET}) [{GREEN}{author}{RESET}]",
                    required=True,
                )
                continue
            try:
                commit_hash, author, date, message = line.split("||", 3)
                write(f"[{YELLOW}{commit_hash}{RESET}] {message} ({CYAN}{date}{RESET}) [{GREEN}{author}{RESET}]", required=True)
            except ValueError:
                write(f"{BLUE}{line}{RESET}" if getattr(args, "graph", False) else line, required=True)
        if unpushed:
            write(f"{RED}{len(unpushed)} commit(s) not pushed yet.{RESET} Run 'gitgo push' to send them.", required=True)
        write(required=True)

    except GitCommandError as e:
        raise GitGoError(f"Failed to retrieve log: {getattr(e, 'stderr', str(e))}")
