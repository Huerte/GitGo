from pygitgo.utils.config import get_config, set_config
from pygitgo.utils.colors import error, warning, info


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
