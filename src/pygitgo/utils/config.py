from pygitgo.utils.executor import run_command
from pygitgo.utils.colors import error, warning, success, info
from pygitgo.exceptions import GitCommandError


def get_config(key, fallback_value):

    config_key = f"gitgo.{key}"

    try:
        result = run_command(['git', 'config', '--global', config_key])                                                                                                                     
        return result.strip()
    except GitCommandError:
        return fallback_value


def set_config(key, value):

    config_key = f"gitgo.{key}"

    try:
        result = run_command(['git', 'config', '--global', config_key, value])
        success(f"\nConfiguration saved: {key} = '{value}'")
        return True
    except GitCommandError:
        error(f"\nFailed to save configuration for '{key}'.")
        return False 

