from pygitgo.utils.colors import error, info, success, warning
from pygitgo.exceptions import GitCommandError
from yaspin import yaspin
import subprocess
import os
import re


def run_command(command, return_complete=False, loading_msg=None, ok_text=None, err_text=None):

    import sys
    kwargs = {"text": loading_msg}
    if sys.stdout.isatty():
        kwargs["color"] = "cyan"
    spinner = yaspin(**kwargs) if loading_msg else None

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
            if ok_text:
                spinner.text = ok_text
            spinner.ok("✔")

        return result if return_complete else result.stdout.strip()
    except (subprocess.CalledProcessError, OSError) as e:
        if spinner:
            if err_text:
                spinner.text = err_text
            spinner.fail("✖")

        stderr = ""
        returncode = 1

        if isinstance(e, subprocess.CalledProcessError):
            stderr = e.stderr.strip() if e.stderr else ""
            returncode = e.returncode
        else:
            stderr = f"Command not found or execution failed: {str(e)}"

        if "detected dubious ownership" in stderr:
            error(f"SECURITY ALERT: {stderr}")
            warning("This is a known Git security feature in shared environments (like Termux).")
            info("GitGo can fix this by adding this directory to your safe list.")

            path_match = re.search(r"repository at '(.+)'", stderr)
            repo_path = path_match.group(1) if path_match else os.getcwd()

            info(f"Directory to trust: {repo_path}")
            confirm = input("\nDo you want GitGo to add this directory as an exception? (y/n): ").strip().lower()

            if confirm == 'y':
                info("Running security fix...")
                fix_command = ["git", "config", "--global", "--add", "safe.directory", repo_path]
                try:
                    subprocess.run(fix_command, check=True)
                    success("Directory trusted. Retrying command...")
                    return run_command(command, return_complete, loading_msg=loading_msg)
                except OSError as fix_err:
                    error(f"Failed to apply fix: {fix_err}")
            else:
                warning("Fix declined. Operations in this directory will continue to fail.")

        raise GitCommandError(command, stderr=stderr, returncode=returncode)
