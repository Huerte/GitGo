import subprocess
import sys
from utils.colors import error


def run_command(command, allow_fail=False):
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        if allow_fail:
            return e
        
        error("\nCommand Failed: {' '.join(command)}")

        stderr = e.stderr.strip() if e.stderr else "No error details available"
        
        error(f"Error output:\n{stderr}\n")
        sys.exit(1)
