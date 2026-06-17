from pygitgo.utils.colors import RED, GREEN, YELLOW, BLUE, CYAN, RESET
import shutil


def confirm(prompt, destructive=False):
    prefix = ""
    if destructive:
        prefix = f"{RED}DANGER: {RESET}"
    user_input = input(f"{prefix}{prompt}").strip().lower()
    return user_input == 'y'

def danger(msg):
    print(f"{RED}DANGER: {msg.strip()}{RESET}")

def warning(msg):
    print(f"{YELLOW}WARNING: {msg.strip()}{RESET}")

def error(msg):
    print(f"{RED}{msg.strip()}{RESET}")

def info(msg):
    print(f"{BLUE}{msg.strip()}{RESET}")

def success(msg):
    print(f"{GREEN}{msg.strip()}{RESET}")

def banner(title, subtitle=""):
    width = min(shutil.get_terminal_size().columns, 72)
    print()
    print(GREEN + ("=" * width) + RESET)
    print(GREEN + title.center(width) + RESET)
    if subtitle:
        print(CYAN + subtitle.center(width) + RESET)
    print(GREEN + ("=" * width) + RESET)
    print()
