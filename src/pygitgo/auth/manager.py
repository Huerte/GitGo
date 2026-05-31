from pygitgo.utils.colors import info, success, warning, error
from pygitgo.utils.executor import run_command
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
        

    key_path = ssh_utils.generate_ssh_key(email=email)
    pub_key_path = str(key_path) + ".pub"

    with open(pub_key_path, 'r') as f:
        pub_key = f.read()

    if pub_key:
        success("SSH Key generated successfully!")

        print("\n" + "=" * len(pub_key))
        print(pub_key, end='')
        print("=" * len(pub_key) + "\n")
        
        info("Copy the key above (between the lines).")
        info("You need to add this key TWICE on GitHub:")
        info("  1. Once as 'Authentication Key'  (so you can push and pull)")
        info("  2. Once as 'Signing Key'          (so your commits show as Verified)")
        info("Both entries use the exact same key text.")

        ssh_utils.open_github_settings()
        
        input(
            "After adding both keys on GitHub,\n"
            "come back here and press Enter to verify the connection..."
        )

    else:
        error("Failed to read the generated public key.")
        return False

    if ssh_utils.check_connection():
        from .account import ensure_user_configure
        
        github_username = ssh_utils.get_github_username()

        ensure_user_configure(default_email=email, default_username=github_username)

        success("\nLogin Successful! You are connected.\n")
        return True
    
    error("Login Failed. The SSH key may not have been added to GitHub correctly.")
    info("Possible causes:")
    info("  1. The key was not pasted on GitHub")
    info("  2. SSH agent is not running (try: eval $(ssh-agent) && ssh-add)")
    info("  3. Network or firewall is blocking SSH connections")
    return False
    
def logout():
    key_path = ssh_utils.get_ssh_key_path()
    if not key_path.exists():
        warning("You are already logged out (no keys found).")
        return False
    
    try:
        
        os.remove(key_path)

        pub_key_path = str(key_path) + ".pub"
        if os.path.exists(pub_key_path):
            os.remove(pub_key_path)

        run_command(["git", "config", "--global", "--unset-all", "user.name"], allow_fail=True)
        run_command(["git", "config", "--global", "--unset-all", "user.email"], allow_fail=True)
        
        success("User successfully logout")
        return True
    
    except Exception as e:
        error(f"Failed to remove SSH keys\nCAUSE OF ERROR: {e}")
        return False
