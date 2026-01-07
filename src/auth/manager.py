from utils.colors import *
from . import ssh_utils
import os

def login():
    if ssh_utils.check_connection():
        success("You are already logged in!")
        return True

    info("initiating login sequence...")

    while True:
        email = input("Enter your email for GitHub: ").strip()
        if "@" in email and "." in email:
            break
        else:
            error("Please enter a valid email address.")
        

    # GENERATE KEY
    key_path = ssh_utils.generate_ssh_key(email=email)
    pub_key_path = str(key_path) + ".pub"

    with open(pub_key_path, 'r') as f:
        pub_key = f.read()

    if pub_key:
        success("SSH Key generated successfully!")

        print("\n" + "="*50)
        print(pub_key)
        print("="*50 + "\n")
        
        info("Copy the key above (between the lines).")
        ssh_utils.open_github_settings()
    else:
        error("Failed to read the generated public key.")
        return False
    
    input("Press Enter after adding the key to GitHub...")

    if ssh_utils.check_connection():
        from .account import ensure_user_configure

        ensure_user_configure(default_email=email)

        success("Login Successful! You are connected.")
        return True
    
    error("Login Failed. Please try again.")
    return False
    
def logout():
    key_path = ssh_utils.get_ssh_key_path()
    if not key_path.exists():
        warning("You are already logged out (no keys found).")
        return False
    
    try:
        os.remove(key_path)
        os.remove(str(key_path) + '.pub')
        success("Logged out. SSH keys removed.")
        return True
    except Exception as e:
        error(f"Failed to remove SSH keys\nCAUSE OF ERROR: {e}")
        return False

