from pygitgo.utils.cli_io import info, warning, banner, write
from pygitgo.auth.manager import login, logout
from pygitgo.auth.account import get_user
from pygitgo.exceptions import GitGoError
import shutil


def display_current_user():
    username, email = get_user()
    if username and email:
        width = min(shutil.get_terminal_size().columns, 40)
        write()
        write("=" * width)
        info(f"Git User:  {username}")
        info(f"Git Email: {email}")
        write("=" * width)
        write()
    else:
        warning("No Git user identity configured.")
        info("Run 'gitgo user login'")


def user_operation(args):
    action = args.action if hasattr(args, 'action') else None

    if not action:
        display_current_user()
        return
    
    if action == 'login':
        if login():
            banner("IDENTITY VERIFIED. ACCESS GRANTED.", "GITHUB SECURE KEYPAIR REGISTERED AND ENABLED.")
    elif action == 'logout':
        logout()
    else:
        raise GitGoError(f"\nInvalid user operation '{action}'!\n")
