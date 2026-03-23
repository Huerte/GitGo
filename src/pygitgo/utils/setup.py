from pygitgo.auth.ssh_utils import ensure_github_known_host
from pygitgo.utils.config import get_config, set_config
from pygitgo.utils.colors import error, info
import shutil
import sys


def check_git_installed():
    """Verify that Git is installed and available on PATH."""
    if not shutil.which("git"):
        error("\nGit is not installed or not found on your PATH!")
        info("Install Git from: https://git-scm.com/downloads")
        info("After installing, restart your terminal and try again.\n")
        sys.exit(1)


def ensure_first_run_setup():
    check_git_installed()

    is_initialized = get_config("initialized", fallback_value="false")

    if is_initialized == "false":
        info("\nInitializing GitGo network settings for the first time... please wait.")
        ensure_github_known_host()

        set_config("initialized", "true")