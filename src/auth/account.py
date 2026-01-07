from utils.executor import run_command
from utils.colors import *
import subprocess


def get_user():
    try:
        name = run_command(["git", "config", "--global", "user.name"], allow_fail=True)
        email = run_command(["git", "config", "--global", "user.email"], allow_fail=True)

        if not name or isinstance(name, subprocess.SubprocessError):
            name = None
        if not email or isinstance(email, subprocess.SubprocessError):
            email = None
        return name, email
    except:
        return None, None
    
def set_user(name, email):
    run_command(["git", "config", "--global", "user.name", name])
    run_command(["git", "config", "--global", "user.email", email])
    success(f"Git user configured: {name} <{email}>")

def ensure_user_configure(default_email=None):

    name, email = get_user()

    if name and email:
        return True
    
    warning("\nGit user identity is not configured!")
    info("This is required for your commits to be attributed correctly.")
    
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

