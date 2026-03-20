from auth.ssh_utils import convert_https_to_ssh, is_ssh_url, check_connection
from utils.executor import run_command
from utils.colors import info, success, warning, error
import subprocess
import sys
import os

DEFAULT_MAIN_BRANCH = "main"


def get_current_branch():
    branch = run_command(["git", "branch", "--show-current"])
    if branch.strip() == "":
        branch = git_new_branch(DEFAULT_MAIN_BRANCH)

    return branch

def is_branch_exist(branch):
    # This one check if the branch existed from both remote and local branches
    return bool(run_command(["git", "branch", "-r", "--list", f"*/{branch}"])) or bool(run_command(["git", "branch", "--list", branch]))


def git_new_branch(branch):
    run_command(["git", "checkout", "-b", branch], loading_msg=f"Creating branch '{branch}'...")
    success(f"\nBranch '{branch}' created.\n")

    return branch


def git_commit(commit_message):
    status_result = run_command(["git", "status", "--porcelain"], allow_fail=True)
    if isinstance(status_result, subprocess.CalledProcessError) or not status_result.strip():
        return False

    run_command(["git", "add", "."], loading_msg="Staging files...")
    clean_message = commit_message.strip('"\'')
    
    run_command(["git", "commit", "-m", clean_message], loading_msg="Committing changes...")

    return True


def git_init():
    if os.path.isdir(".git"):
        warning("Already a git repository! Skipping init...")
        return True
    
    # Use -b main to set default branch to 'main' (Git >= 2.28)
    result = run_command(["git", "init", "-b", DEFAULT_MAIN_BRANCH], allow_fail=True, loading_msg="Initializing git repository...")
    if isinstance(result, subprocess.CalledProcessError):
        # Fallback for older Git versions that don't support -b
        run_command(["git", "init"], loading_msg="Initializing git repository...")
        run_command(["git", "checkout", "-b", DEFAULT_MAIN_BRANCH], allow_fail=True)

    success("Git repository initialized.")
    return True


def add_remote_origin(repo_url):
    # clean the URL - remove quotes if present, dili na kailangan og quotes
    clean_url = repo_url.strip('"\'')
    
    existing_remote = run_command(["git", "remote", "get-url", "origin"], allow_fail=True)
    if not isinstance(existing_remote, subprocess.CalledProcessError):
        warning(f"Remote origin already exists: {existing_remote}")
        run_command(["git", "remote", "set-url", "origin", clean_url], loading_msg="Updating remote URL...")
    else:
        run_command(["git", "remote", "add", "origin", clean_url], loading_msg="Adding remote origin...")
    
    success(f"Remote origin set to: {clean_url}")


def confirm_remote_link():
    # test connection to remote - make sure it's not cap
    test_result = run_command(["git", "ls-remote", "origin"], allow_fail=True, loading_msg="Testing connection to remote...")
    
    if isinstance(test_result, subprocess.CalledProcessError):
        error("Failed to connect to remote repository!")
        warning("Please check your repository URL and network connection.")
        return False
    
    success("Successfully connected to remote repository.")
    return True


def create_main_branch():
    # check current branch - switch to main if needed
    current_branch = run_command(["git", "branch", "--show-current"], allow_fail=True)
    
    if isinstance(current_branch, subprocess.CalledProcessError) or not current_branch.strip():
        # no commits yet, set default branch to main
        run_command(["git", "checkout", "-b", "main"], loading_msg="Setting default branch to 'main'...")
    elif current_branch.strip() != "main":
        # rename current branch to main
        run_command(["git", "branch", "-m", "main"], loading_msg=f"Renaming branch '{current_branch.strip()}' to 'main'...")
    else:
        success("Already on 'main' branch.")


def check_and_sync_branch(branch):
    try:
        run_command(["git", "fetch", "origin"], loading_msg="Checking if branch is up to date...")

        try:
            local_commit = run_command(["git", "rev-parse", branch])
            remote_commit = run_command(["git", "rev-parse", f"origin/{branch}"])

            if local_commit != remote_commit:
                behind_check = run_command(
                    ["git", "rev-list", "--count", f"{branch}..origin/{branch}"]
                )
                if behind_check and int(behind_check) > 0:
                    warning(f"Local branch is behind remote by {behind_check} commit(s). Pulling changes...")
                    output = run_command(["git", "pull", "--rebase", "origin", branch], loading_msg="Pulling changes from remote...")
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
                run_command(["git", "remote", "set-url", "origin", ssh_url], loading_msg="Converting remote from HTTPS to SSH for secure push...")
                success(f"Remote updated to: {ssh_url}")
    
    run_command(["git", "push", "-u", "origin", branch], loading_msg=f"Pushing to remote branch '{branch}'...")


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
