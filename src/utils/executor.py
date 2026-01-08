import subprocess
import sys
import os
from utils.colors import error, info, success, warning


def run_command(command, allow_fail=False, return_complete=False):
    """
    Runs a shell command safely.
    
    :param command: list of command + args
    :param allow_fail: if True, do not exit on error
    :param return_complete: if True, return subprocess.CompletedProcess instead of stdout
    """
    try:
        result = subprocess.run(
            command,
            check=not allow_fail,  # only raise if not allow_fail
            capture_output=True,
            text=True
        )
        return result if return_complete else result.stdout.strip()
    except subprocess.CalledProcessError as e:
        stderr = e.stderr.strip() if e.stderr else ""
        
        # Check for dubious ownership error (common in Termux/shared storage)
        if "detected dubious ownership" in stderr:
            error(f"\nSECURITY ALERT: {stderr}")
            warning("\nThis is a known Git security feature in shared environments (like Termux).")
            info("GitGo can fix this for you by adding this directory to your safe list.")
            
            # Extract the path from the error message if possible
            # Error looks like: fatal: detected dubious ownership in repository at '/path/to/repo'
            import re
            path_match = re.search(r"repository at '(.+)'", stderr)
            repo_path = path_match.group(1) if path_match else os.getcwd()

            info(f"Directory to trust: {repo_path}")
            confirm = input("\nDo you want GitGo to add this directory as an exception? (y/n): ").strip().lower()
            
            if confirm == 'y':
                info("Running security fix...")
                fix_command = ["git", "config", "--global", "--add", "safe.directory", repo_path]
                try:
                    subprocess.run(fix_command, check=True)
                    success("Success! Directory added to safe list.")
                    info("Retrying your original command...\n")
                    # Recursive call to retry the original command
                    return run_command(command, allow_fail, return_complete)
                except Exception as fix_err:
                    error(f"Failed to apply fix: {fix_err}")
            else:
                warning("\nFix declined. Operations in this directory will continue to fail.")

        if allow_fail:
            return e  # let caller decide
        
        error(f"\nCommand Failed: {' '.join(command)}")
        error(f"Error output:\n{stderr or 'No error details available'}\n")
        sys.exit(1)
