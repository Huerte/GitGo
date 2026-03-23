from pygitgo.utils.executor import run_command
from pygitgo.utils.colors import info, highlight, error, warning, success
import sys


ALIASES = {
    "-l": "list",
    "-s": "save",
    "-o": "load",
    "-d": "delete"
}

def all_save_state():
    output = run_command([
        "git", "stash", "list",
        "--date=format:%Y-%m-%d %H:%M:%S",
        "--pretty=%gd||%cd||%s"
    ])

    if not output:
        info("\nNo saved states found.\n")
        sys.exit(0)

    save_states = []

    for line in output.splitlines():
        try:
            stash_ref, date, message = line.split("||", 2)

            index = int(
                stash_ref.replace("stash@{", "").replace("}", "")
            )

            save_states.append({
                "id": index + 1,   
                "ref": stash_ref,  
                "date": date,
                "message": message
            })

        except ValueError:
            warning(f"Skipping malformed line: {line}")

    return save_states


def display_save_states():
    save_states = all_save_state()

    print("\nID | Date                | Saved State")
    print("-" * 60)

    for state in save_states:
        highlight(
            f"{state['id']:>2} | {state['date']} | {state['message']}"
        )

    print("-" * 60 + "\n")


def is_number(value):
    try:
        float(value)
        return True
    except ValueError:
        return False
    
def validate_state_id(state_id, save_states):
    if not is_number(state_id):
        error("\nInvalid input. Please enter a valid state ID.\n")
        return False
    elif (int(float(state_id)) - 1) < 0:
        error("\nState ID cannot be '0' or negative. Please enter a valid state ID.\n")
        return False
    elif (int(float(state_id)) - 1) >= len(save_states):
        error("\nState ID out of range. Please enter a valid state ID.\n")
        return False
    return True


def ask_state_id(save_states):
    proceed = False
    state_id = None

    display_save_states()
    info("\nEnter the ID (or 'q' to cancel): ")

    while not proceed:
        state_id = input(">> ").strip().lower()
        if state_id == 'q':
            warning("\nLoad operation cancelled by user.\n")
            sys.exit(0)
        proceed = validate_state_id(state_id, save_states)
    
    return state_id


def state_list():
    display_save_states()


def load_state(state_id=None):
    save_states = all_save_state()
    proceed = False

    if state_id:
        if state_id.isdigit():
            proceed = validate_state_id(state_id, save_states)
            if not proceed:
                sys.exit(1)
        else:
            error(f"\nInvalid argument '{state_id}' for load operation. Expected a state ID.\n")
            sys.exit(1)
    
    if not proceed:
        state_id = ask_state_id(save_states)
        
    run_command(["git", "stash", "apply", str(int(state_id) - 1)])

    success(f"\nState '{save_states[int(state_id) - 1]['message']}' loaded successfully.\n")


def save_state(state_name=None):
    if not state_name:
        state_name = "Auto-Save"

    run_command(["git", "stash", "push", "-m", state_name])

    success(f"\nState '{state_name}' saved successfully.\n")


def delete_state(identifier=None):
    if not identifier:
        state_id = ask_state_id(all_save_state())
    else:
        if identifier == '-a':
            confirm = input("\nAre you sure you want to delete all saved states? (y/n): ").strip().lower()
            if confirm.lower() == 'y':
                run_command(["git", "stash", "clear"])
                success("\nAll saved states deleted successfully.\n")
                sys.exit(0)
            else:
                warning("\nDelete operation cancelled by user.\n")
                sys.exit(0)
        
        elif not identifier.isdigit():
            error("\nInvalid input. Please enter a valid state ID.\n")
            sys.exit(1)

        state_id = identifier
        if not validate_state_id(state_id, all_save_state()):
            sys.exit(1)
    
    run_command(["git", "stash", "drop", str(int(state_id) - 1)])
    success(f"\nState with ID '{state_id}' deleted successfully.\n")




def state_operations(args):
    action = ALIASES.get(args.action, args.action)
    identifier = getattr(args, "identifier", None)

    if action == "list":
        state_list()
    elif action == "save":
        save_state(identifier)
    elif action == "load":
        load_state(identifier)
    elif action == "delete":
        delete_state(identifier)
    else:
        error(f"\nUnknown state operation: {action}\n")
        sys.exit(1)