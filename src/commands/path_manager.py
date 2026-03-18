from utils.platform_utils import (
    is_windows, get_platform_display_name, get_bin_directory,
    get_executable_name, create_wrapper_script, is_in_path
)
from utils.colors import info, success, warning, error
import shutil
import sys
import os


def get_current_script_path():
    # get the actual path where gitgo.py is located - no cap
    return os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'gitgo.py'))


def get_system_gitgo_path():
    # check where the system thinks gitgo is located
    gitgo_path = shutil.which("gitgo")
    if gitgo_path:
        # resolve any symlinks or batch files to get the actual script path
        if is_windows() and gitgo_path.endswith('.bat'):
            # Windows batch file - extract python script path
            try:
                with open(gitgo_path, 'r') as f:
                    content = f.read()
                    # look for python script path in batch file
                    for line in content.split('\n'):
                        if 'python' in line.lower() and 'gitgo.py' in line:
                            # extract the path - basic parsing, might need adjustment
                            parts = line.split()
                            for part in parts:
                                if 'gitgo.py' in part:
                                    return os.path.abspath(part.strip('"\''))
            except:
                pass
        else:
            # Unix shell script - extract python script path
            try:
                with open(gitgo_path, 'r') as f:
                    content = f.read()
                    # look for exec python line
                    for line in content.split('\n'):
                        if 'exec' in line and 'gitgo.py' in line:
                            # extract the path from exec command
                            parts = line.split()
                            for part in parts:
                                if 'gitgo.py' in part:
                                    return os.path.abspath(part.strip('"\''))
            except:
                pass
    return gitgo_path


def is_path_outdated():
    # check if the current script location matches system PATH - lowkey important
    current_path = get_current_script_path()
    system_path = get_system_gitgo_path()
    
    if not system_path:
        return True  # gitgo not in PATH at all
    
    # normalize paths for comparison
    try:
        current_dir = os.path.dirname(current_path)
        system_dir = os.path.dirname(os.path.abspath(system_path))
        return current_dir != system_dir
    except:
        return True  # if we can't determine, assume outdated


def check_path_validity():
    # validate path and warn user if needed - fr fr this is important
    if is_path_outdated():
        warning("\n⚠️  PATH OUTDATED DETECTED! ⚠️")
        error("Your system PATH points to an outdated GitGo location.")
        warning(f"Current script: {get_current_script_path()}")
        warning(f"System PATH: {get_system_gitgo_path() or 'Not found'}")
        warning(f"Platform: {get_platform_display_name()}")

        info("\nTo fix this issue, run:")
        success("    gitgo update")
        warning("This will update your wrapper script to the current location.\n")
        return False
    return True


def update_operation(arguments):
    HELP_COMMANDS = ["help", "--help", "-h"]
    
    # handle gitgo update command - update wrapper to current location (cross-platform)
    if len(arguments) > 1 and arguments[1] in HELP_COMMANDS:
        warning("\nUsage: gitgo update\n")
        warning("Updates your gitgo wrapper to point to the current GitGo location.")
        warning("This fixes issues when GitGo is moved to a different directory.\n")
        sys.exit(0)
    
    info(f"\n🔧 INITIATING UPDATE OPERATION... [{get_platform_display_name()}]")
    
    current_script = get_current_script_path()
    current_dir = os.path.dirname(current_script)
    
    info(f"Current GitGo location: {current_dir}")
    
    # create or update wrapper script in a system-accessible location
    try:
        # Get platform-specific bin directory
        target_dir = get_bin_directory()
        
        if not os.path.exists(target_dir):
            os.makedirs(target_dir, exist_ok=True)
            success(f"✅ Created directory: {target_dir}")
        
        # Get wrapper filename (gitgo.bat for Windows, gitgo for Unix)
        wrapper_name = get_executable_name()
        wrapper_path = os.path.join(target_dir, wrapper_name)
        
        # Create wrapper content
        wrapper_content = create_wrapper_script(current_script, current_dir)
        
        # Write wrapper file
        with open(wrapper_path, 'w', newline='\n' if not is_windows() else None) as f:
            f.write(wrapper_content)
        
        # Make executable on Unix systems
        if not is_windows():
            import stat
            os.chmod(wrapper_path, os.stat(wrapper_path).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        
        success(f"✅ Wrapper created: {wrapper_path}")
        
        # Check if target_dir is in PATH
        if not is_in_path(target_dir):
            warning("\n⚠️  MANUAL ACTION REQUIRED ⚠️")
            warning("Add this directory to your system PATH:")
            success(f"    {target_dir}")
            
            if is_windows():
                info("\nHow to add to PATH on Windows:")
                warning("1. Press Win + R, type 'sysdm.cpl', press Enter")
                warning("2. Click 'Environment Variables' button")
                warning("3. Under 'User variables', find and select 'Path', click 'Edit'")
                warning(f"4. Click 'New' and add: {target_dir}")
                warning("5. Click 'OK' on all dialogs")
                warning("6. Restart your terminal")
            else:
                info("\nHow to add to PATH on Linux/Termux:")
                warning("Add this line to your shell configuration file (~/.bashrc or ~/.zshrc):")
                success(f"    export PATH=\"$PATH:{target_dir}\"")
                warning("\nThen run: source ~/.bashrc (or ~/.zshrc)")
        else:
            success("✅ Directory already in PATH!")
        
        success("\n🎯 UPDATE COMPLETE!")
        info("GitGo should now work from any location.")
        warning("If issues persist, restart your terminal.")
    
    except Exception as e:
        error(f"❌ Update failed: {str(e)}")
        if is_windows():
            warning("You may need to run this command as Administrator.")
        else:
            warning("Check file permissions and try again.")
        sys.exit(1)
