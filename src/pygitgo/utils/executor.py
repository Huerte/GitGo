from pygitgo.utils.cli_io import error, info, success, warning, confirm, danger
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
        env = os.environ.copy()
        env["GIT_TERMINAL_PROMPT"] = "0"
        base_ssh_cmd = env.get("GIT_SSH_COMMAND", "ssh")
        env["GIT_SSH_COMMAND"] = f"{base_ssh_cmd} -o BatchMode=yes"

        result = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
            stdin=subprocess.DEVNULL,
            env=env,
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
            danger("Git blocked this folder for security reasons (dubious ownership).")
            warning("This usually happens in shared environments like Termux or network drives.")
            info("GitGo can add this folder to Git's trusted list so commands work here.")

            path_match = re.search(r"repository at '(.+)'", stderr)
            repo_path = path_match.group(1) if path_match else os.getcwd()

            info(f"Folder to trust: {repo_path}")
            if confirm("Trust this folder and allow Git commands to run in it? (y/n): "):
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
