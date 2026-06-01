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

            