from pygitgo.utils.cli_io import info, success, warning, error
from pygitgo.utils.executor import run_command
from pygitgo.exceptions import GitCommandError
from pygitgo.utils.colors import BLUE, RESET


def get_user():
    try:
        name = run_command(["git", "config", "--global", "user.name"])
    except GitCommandError:
        name = None
    
    try:
        email = run_command(["git", "config", "--global", "user.email"])
    except GitCommandError:
        email = None
    
    if not name:
        name = None
    if not email:
        email = None

    return name, email

def set_user(name, email):
    run_command(["git", "config", "--global", "user.name", name])
    run_command(["git", "config", "--global", "user.email", email])
    success("\nGit user configured successfully.")
    print(f"{BLUE}Username{RESET} : {name}")
    print(f"{BLUE}Email    {RESET}: {email}")

def ensure_user_configure(default_email=None, default_username=None):

    name, email = get_user()

    if name and email:
        return True
    
    if default_username and default_email:
        info(f"\nConfiguring Git identity from GitHub...")
        set_user(default_username, default_email)
        return True
    
    print()
    print("  Git Identity Setup")
    print("  " + "-" * 36)
    warning("Git user identity is not configured.")
    info("Needed so your commits are attributed to the right account.")
    print()

    if default_username:
        new_username = default_username
        info(f"Using GitHub username: {new_username}")
    else:
        new_username = input("Enter your Username (for commits): ").strip()
    
    prompt_email = "Enter your Email (for commits)"
    if default_email:
        prompt_email += f" [{default_email}]"
    
    new_email = input(f"{prompt_email}: ").strip()
    
    if not new_email and default_email:
        new_email = default_email
        
    if new_username and new_email:
        set_user(new_username, new_email)
        return True
    
    error("Invalid configuration. Name and Email are required.")
    return False

def sanitize_signing_config():
    try:
        gpgsign = run_command(["git", "config", "--global", "commit.gpgsign"]).strip().lower()
    except GitCommandError:
        return
    
    if gpgsign != "true":
        return
    
    try:
        fmt = run_command(["git", "config", "--global", "gpg.format"]).strip().lower()
    except GitCommandError:
        fmt = ""

    if fmt == "ssh":
        return
    
    warning("Detected 'commit.gpgsign=true' with no GPG key configured.")
    warning("Disabling global GPG signing to prevent commit failures.")

    try:
        run_command(["git", "config", "--global", "--unset", "gpg.program"])
    except GitCommandError:
        pass
    
    try:
        run_command(["git", "config", "--global", "--unset", "commit.gpgsign"])
    except GitCommandError:
        pass
    

