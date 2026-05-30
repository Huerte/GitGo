from pygitgo.utils.colors import info, highlight, error, warning, success
from pygitgo.commands.stash_operation import (
    git_stash_apply, git_stash_clear, git_stash_drop,
    git_stash_list, git_stash_push
)
from pygitgo.utils.executor import run_command, command_failed
from pygitgo.exceptions import GitGoError


ALIASES = {
    "-l": "list",
    "-s": "save",
    "-o": "load",
    "-d": "delete"
}

def all_save_state():
    output = git_stash_list()

    if command_failed(output) or not output:
        return []

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


def display_save_states(save_state=None):
    save_states = save_state if save_state is not None else all_save_state()

    if not save_states:
        info("\nNo saved states found.\n")
        return

    print("\nID | Date                | Saved State")
    print("-" * 60)

    for state in save_states:
        highlight(
            f"{state['id']:>2} | {state['date']} | {state['message']}"
        )

    print("-" * 60 + "\n")


def is_number(value):
    val = str(value).strip()
    if val.startswith('-'):
        return val[1:].isdigit()
    return val.isdigit()
    
def validate_state_id(state_id, save_states):
    if not is_number(state_id):
        error("\nInvalid input. Please enter a valid state ID.\n")
        return False
    elif (int(state_id) - 1) < 0:
        error("\nState ID cannot be '0' or negative. Please enter a valid state ID.\n")
        return False
    elif (int(state_id) - 1) >= len(save_states):
        error("\nState ID out of range. Please enter a valid state ID.\n")
        return False
    return True


def ask_state_id(save_states):
    proceed = False
    state_id = None

    display_save_states(save_states)
    info("\nEnter the ID (or 'q' to cancel): ")

    while not proceed:
        state_id = input(">> ").strip().lower()
        if state_id == 'q':
            warning("\nLoad operation cancelled by user.\n")
            return
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
                raise GitGoError()
        else:
            raise GitGoError(f"\nInvalid argument '{state_id}' for load operation. Expected a state ID.\n")
    
    if not proceed:
        state_id = ask_state_id(save_states)
        if not state_id:
            return
        
    apply_result = git_stash_apply(stash_id=str(int(state_id) - 1))
    if not apply_result:
        error(f"\nFailed to load state. There may be a conflict with your current changes.\n")
        raise GitGoError()
    success(f"\nState '{save_states[int(state_id) - 1]['message']}' loaded successfully.\n")


def save_state(state_name=None):
    if not state_name:
        state_name = "Auto-Save"
        
    has_changes = run_command(['git', 'status', '--porcelain'], allow_fail=True)
    if not command_failed(has_changes) and not has_changes.strip():
        warning("\nNo local changes to save.\n")
        return
        
    output = git_stash_push(label=state_name)
    if not output:
        error(f"\nFailed to save state '{state_name}'.\n")
    else:
        success(f"\nState '{state_name}' saved successfully.\n")


def delete_state(identifier=None):
    save_states = all_save_state()
    if not save_states:
        warning("\nNo saved states to delete.\n")
        return

    if not identifier:
        state_id = ask_state_id(save_states)
        if not state_id:
            return
    else:
        if identifier == '-a':
            confirm = input("\nAre you sure you want to delete all saved states? (y/n): ").strip().lower()
            if confirm == 'y':
                clear_result = git_stash_clear()
                if not clear_result:
                    error("\nFailed to delete all saved states.\n")
                else:
                    success("\nAll saved states deleted successfully.\n")
            else:
                warning("\nDelete operation cancelled by user.\n")
            return
        elif not identifier.isdigit():
            raise GitGoError("\nInvalid input. Please enter a valid state ID.\n")

        state_id = identifier
        if not validate_state_id(state_id, save_states):
            raise GitGoError()
    
    drop_result = git_stash_drop(stash_id=str(int(state_id) - 1))
    if not drop_result:
        error(f"\nFailed to delete state with ID '{state_id}'.\n")
        raise GitGoError()
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
        raise GitGoError(f"\nUnknown state operation: {action}\n")
    