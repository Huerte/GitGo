from pygitgo.utils.colors import info, success, warning, error, highlight
from pygitgo.commands.stash_operation import (
    git_stash_apply, git_stash_clear, git_stash_drop,
    git_stash_list, git_stash_push
)
from pygitgo.utils.executor import run_command, command_failed
from pygitgo.exceptions import GitGoError



def all_save_state():
    output = git_stash_list()

    if command_failed(output) or not output:
        return []

    save_states = []
    lines = output.splitlines()
    total = len(lines)

    for i, line in enumerate(reversed(lines)):
        try:
            stash_ref, date, message = line.split("||", 2)
            stash_index = total - 1 - i

            save_states.append({
                "id": i + 1,
                "ref": f"stash@{{{stash_index}}}",
                "date": date,
                "message": message,
                "stash_index": stash_index
            })

        except ValueError:
            warning(f"Skipping malformed line: {line}")

    return save_states


def display_save_states(save_state=None):
    save_states = save_state if save_state is not None else all_save_state()

    if not save_states:
        info("No saved states found.")
        return

    print("\nID | Date                | Saved State")
    print("-" * 60)

    for state in save_states:
        highlight(
            f"{state['id']:>2} | {state['date']} | {state['message']}"
        )

    print("-" * 60)
    print()


def is_number(value):
    val = str(value).strip()
    if val.startswith('-'):
        return val[1:].isdigit()
    return val.isdigit()


def validate_state_id(state_id, save_states):
    if not is_number(state_id):
        error(f"Invalid ID. Expected a number between 1 and {len(save_states)}.")
        return False
    elif (int(state_id) - 1) < 0:
        error(f"Invalid ID. Range is 1 to {len(save_states)}.")
        return False
    elif (int(state_id) - 1) >= len(save_states):
        error(f"ID out of range. Range is 1 to {len(save_states)}.")
        return False
    return True


def ask_state_id(save_states):
    proceed = False
    state_id = None

    display_save_states(save_states)
    print("Enter the ID (or 'q' to cancel):")

    while not proceed:
        state_id = input(">> ").strip().lower()
        if state_id == 'q':
            info("Load canceled.")
            return
        proceed = validate_state_id(state_id, save_states)

    return state_id


def state_list():
    display_save_states()


def load_state(state_id=None):
    save_states = all_save_state()

    if not save_states:
        info("No saved states to load.")
        return

    proceed = False

    if state_id:
        if state_id.isdigit():
            proceed = validate_state_id(state_id, save_states)
            if not proceed:
                raise GitGoError("Load aborted — invalid state ID.")
        else:
            raise GitGoError(f"Invalid argument '{state_id}' for load. Expected a state ID number.")

    if not proceed:
        state_id = ask_state_id(save_states)
        if not state_id:
            return

    selected_state = save_states[int(state_id) - 1]

    apply_result = git_stash_apply(stash_id=str(selected_state["stash_index"]))
    if not apply_result:
        error(f"Failed to load state. There may be a conflict with your current changes.")
        raise GitGoError("Load failed — resolve conflicts first.")
    success(f"State '{selected_state['message']}' restored.")


def save_state(state_name=None):
    if not state_name:
        state_name = "Auto-Save"

    has_changes = run_command(['git', 'status', '--porcelain'], allow_fail=True)
    if not command_failed(has_changes) and not has_changes.strip():
        info("No local changes to save.")
        return

    output = git_stash_push(label=state_name)
    if not output:
        error(f"Failed to save state '{state_name}'.")
    else:
        success(f"State '{state_name}' saved.")


def delete_state(identifier=None):
    save_states = all_save_state()
    if not save_states:
        info("No saved states to delete.")
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
                    error("Failed to delete all saved states.")
                else:
                    success("All saved states deleted.")
            else:
                info("Delete canceled.")
            return
        elif not identifier.isdigit():
            raise GitGoError(f"Invalid input '{identifier}'. Expected a state ID number.")

        state_id = identifier
        if not validate_state_id(state_id, save_states):
            raise GitGoError("Delete aborted — invalid state ID.")

    selected_state = save_states[int(state_id) - 1]

    drop_result = git_stash_drop(stash_id=str(selected_state["stash_index"]))
    if not drop_result:
        error(f"Failed to delete state {state_id}.")
        raise GitGoError("Delete failed — see above.")
    success(f"State {state_id} deleted.")


def state_operations(args):
    alias = getattr(args, "action_alias", None)
    positional = getattr(args, "action", None)

    if alias and positional and alias != positional:
        raise GitGoError(
            f"Conflicting actions: '{positional}' and '{alias}'. Use one or the other."
        )

    action = alias or positional
    identifier = getattr(args, "identifier", None)

    if getattr(args, "all", False):
        if action != "delete":
            raise GitGoError(
                "The -a/--all flag is only valid with the delete action."
            )
        identifier = "-a"

    if not action:
        raise GitGoError("Missing action. Use: list, save, load, delete (or -l, -s, -o, -d).")

    if action == "list":
        state_list()
    elif action == "save":
        save_state(identifier)
    elif action == "load":
        load_state(identifier)
    elif action == "delete":
        delete_state(identifier)
    else:
        raise GitGoError(f"Unknown state operation: {action}")