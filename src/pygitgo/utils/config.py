from pygitgo.utils.cli_io import error, success
from pygitgo.utils.executor import run_command
from pygitgo.exceptions import GitCommandError
import subprocess


def get_config(key, fallback_value):

    config_key = f"gitgo.{key}"

    try:
        result = run_command(['git', 'config', '--global', config_key])                                                                                                                     
        return result.strip()
    except GitCommandError:
        return fallback_value


def set_config(key, value, silent=False):

    config_key = f"gitgo.{key}"

    try:
        run_command(['git', 'config', '--global', config_key, value])
        if not silent:
            success(f"\nConfiguration saved: {key} = '{value}'")
        return True
    except GitCommandError:
        if not silent:
            error(f"\nFailed to save configuration for '{key}'.")
        return False


def get_default_branch() -> str:
    try:
        branch = subprocess.check_output(
            ["git", "config", "--get", "init.defaultBranch"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
        if branch:
            return branch
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass

    return get_config("default-branch", "main")

