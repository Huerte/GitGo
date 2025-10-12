RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
CYAN = "\033[36m"
RESET = "\033[0m"


def info(msg): 
    print(f"{BLUE}  {msg}{RESET}")

def success(msg): 
    print(f"{GREEN}  {msg}{RESET}")

def warning(msg): 
    print(f"{YELLOW}  {msg}{RESET}")

def error(msg): 
    print(f"{RED}  {msg}{RESET}")

def highlight(msg): 
    print(f"{CYAN}  {msg}{RESET}")
