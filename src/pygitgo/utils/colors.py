import shutil

RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
CYAN = "\033[36m"
RESET = "\033[0m"


def info(msg):
    print(f"{BLUE}{msg.strip()}{RESET}")

def success(msg):
    print(f"{GREEN}{msg.strip()}{RESET}")

def warning(msg):
    print(f"{YELLOW}{msg.strip()}{RESET}")

def error(msg):
    print(f"{RED}{msg.strip()}{RESET}")

def highlight(msg):
    print(f"{CYAN}{msg.strip()}{RESET}")

def print_banner(title, subtitle="AWAITING NEXT ORDERS."):
    width = min(shutil.get_terminal_size().columns, 72)
    print()
    print(GREEN + ("=" * width) + RESET)
    print(GREEN + title.center(width) + RESET)
    if subtitle:
        print(CYAN + subtitle.center(width) + RESET)
    print(GREEN + ("=" * width) + RESET)
    print()
