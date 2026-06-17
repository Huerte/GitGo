from pygitgo.utils.cli_io import error, info
from pygitgo.exceptions import GitGoError
import shutil


def check_git_installed():
    if not shutil.which("git"):
        error("\nGit is not installed or not found on your PATH!")
        info("Install Git from: https://git-scm.com/downloads")
        info("After installing, restart your terminal and try again.\n")
        raise GitGoError()


def ensure_first_run_setup():
    check_git_installed()
