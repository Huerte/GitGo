from pygitgo.utils.executor import run_command
from pygitgo.utils.colors import *
import subprocess


def get_config(key, fallback_value):

    config_key = f"gitgo.{key}"

    result = run_command(['git', 'config', '--global', config_key], allow_fail=True)                                                                                                                     

    if not result or isinstance(result, subprocess.CalledProcessError):
        return fallback_value

    return result.strip()


def set_config(key, value):

    config_key = f"gitgo.{key}"

    result = run_command(['git', 'config', '--global', config_key, value], allow_fail=True)
    
    if isinstance(result, subprocess.CalledProcessError):
        error(f"\nFailed to save configuration for '{key}'.")
        return False 

    success(f"\nConfiguration saved: {key} = '{value}'")
    return True


def config_operation(args):

    key = args.key
    action = args.action
    value = getattr(args, 'value', None)

    VALID_KEYS = ["default-branch", "default-message"]
    if key not in VALID_KEYS:
        error(f"\nInvalid configuration key: '{key}'")
        warning(f"Valid keys are: {', '.join(VALID_KEYS)}\n")
        return

    if action == 'set':
        if not value:
            error("\nYou must provide a value to set!\n")
            return
        set_config(key, value)
    elif action == 'get':
        current_value = get_config(key, None)
        if current_value:
            info(f"\n{key} is currently set to: '{current_value}'\n")
        else:
            warning(f"\n{key} is not currently set.\n")