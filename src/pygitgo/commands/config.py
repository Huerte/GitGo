from pygitgo.utils.config import get_config, set_config
from pygitgo.utils.cli_io import warning, info
from pygitgo.exceptions import GitGoError


def config_operation(args):

    key = args.key
    action = args.action
    value = getattr(args, 'value', None)

    VALID_KEYS = ["default-branch", "default-message"]
    if key not in VALID_KEYS:
        raise GitGoError(f"Invalid configuration key: '{key}'. Valid keys are: {', '.join(VALID_KEYS)}")

    if action == 'set':
        if not value:
            raise GitGoError("You must provide a value to set!")
        set_config(key, value)
    elif action == 'get':
        current_value = get_config(key, None)
        if current_value:
            info(f"\n{key} is currently set to: '{current_value}'\n", required=True)
        else:
            warning(f"\n{key} is not currently set.\n", required=True)

