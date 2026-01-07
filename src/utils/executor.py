import subprocess
import sys
from utils.colors import error


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
        if allow_fail:
            return e  # let caller decide
        
        error(f"\nCommand Failed: {' '.join(command)}")
        stderr = e.stderr.strip() if e.stderr else "No error details available"
        error(f"Error output:\n{stderr}\n")
        sys.exit(1)
