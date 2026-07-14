from pygitgo.utils.cli_io import info, error, warning, confirm, success, banner, write
from pygitgo.commands.init import init_operation
from pygitgo.commands.repo import repo_operation
from pygitgo.utils.platform import get_platform
from pygitgo.commands.link import link_core
from pygitgo.exceptions import GitGoError
import sys
import os


def _assert_not_inside_target(repo_name):
    # This will abort operation if the user is already inside the folder with same name as repo

    cwd_basename = os.path.basename(os.path.abspath("."))

    if get_platform() == "windows":
        match = cwd_basename.lower() == repo_name.lower()
    else:
        match = cwd_basename == repo_name 

    if match:
        raise GitGoError(
            f"\nDirectory mismatch detected.\n\n"
            f"  You are already inside '{repo_name}/', but you ran: gitgo new {repo_name}\n\n"
            f"  'gitgo new' creates a NEW folder from scratch. If you want to:\n\n"
            f"  → Publish this existing folder to GitHub, run:\n"
            f"      gitgo repo             (creates the GitHub repo)\n"
            f"      gitgo link <repo-url>  (links and pushes)\n\n"
            f"  → Start completely fresh in a new folder, cd out first:\n"
            f"      cd ..\n"
            f"      gitgo new {repo_name}\n"
        )


def new_operation(args):
    
    _assert_not_inside_target(args.name)
    
    init_operation(args)

    os.chdir(args.name)

    repo_url = repo_operation(args, silent=True)

    try:
        link_core(repo_url, "Initial commit", silent=True, already_initialized=True)
    except GitGoError as e:
        error(str(e))
        from pygitgo.commands.repo import delete_github_repo, parse_repo_fullname
        warning(f"An orphaned remote repository was created on GitHub: {repo_url}")
        info("It needs manual deletion or a retry of 'gitgo link'.")
        full_name = parse_repo_fullname(repo_url)
        if full_name:
            if confirm("Delete the repo I just created on GitHub? (y/n): ", destructive=True):
                try:
                    delete_github_repo(full_name)
                    success("GitHub repository deleted successfully.")
                except Exception as delete_err:
                    error(f"Failed to delete: {delete_err}")
        sys.exit(1)

    banner("PROJECT LAUNCHED. SCAFFOLDED, CREATED, AND DEPLOYED.", "LOCAL STRUCTURE ESTABLISHED AND REMOTE SYNCED.")

    write()
    info("Run 'gitgo undo link' to remove the remote and undo the initial commit.")

