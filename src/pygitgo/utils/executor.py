import subprocess
import sys
import os
from pygitgo.utils.colors import error, info, success, warning
from pygitgo.exceptions import GitCommandError


def run_command(command, allow_fail=False, return_complete=False, loading_msg=None):
    """
    Runs a shell command safely.
    
    :param command: list of command + args
    :param allow_fail: if True, do not raise on error
    :param return_complete: if True, return subprocess.CompletedProcess instead of stdout
    :param loading_msg: if provided, show a yaspin spinner with this message
    :raises GitCommandError: when the command fails and allow_fail is False
    """
    from yaspin import yaspin

    spinner = yaspin(text=loading_msg, color="cyan") if loading_msg else None

    if spinner:
        spinner.start()

    try:
        result = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True
        )

        if spinner:
            spinner.ok("✔")

        return result if return_complete else result.stdout.strip()
    except subprocess.CalledProcessError as e:
        if spinner:
            spinner.fail("✖")

        stderr = e.stderr.strip() if e.stderr else ""
        
        if "detected dubious ownership" in stderr:
            error(f"\nSECURITY ALERT: {stderr}")
            warning("\nThis is a known Git security feature in shared environments (like Termux).")
            info("GitGo can fix this for you by adding this directory to your safe list.")
            
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
                    return run_command(command, allow_fail, return_complete, loading_msg=loading_msg)
                except OSError as fix_err:
                    error(f"Failed to apply fix: {fix_err}")
            else:
                warning("\nFix declined. Operations in this directory will continue to fail.")

        if allow_fail:
            return e
        
        raise GitCommandError(command, stderr=stderr, returncode=e.returncode)
