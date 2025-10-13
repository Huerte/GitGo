from utils.executor import run_command
from utils.colors import *
import sys


def all_save_state():
    # "--pretty=%gd: %s" this format specifier remove branch from the result
    output = run_command(["git", "stash", "list", "--pretty=%gd: %s"])
    if not output:
        info("\nNo saved states found.\n")
        sys.exit(0)

    save_states = [result[6:] for result in output.splitlines()]
    
    return save_states


def display_save_states(save_states):
    # Display the list of saved states
    print("\nSaved States:")
    print("----------------")
    for state in save_states:
        highlight(f"- {state.split(': ', 1)[0]}: {state.split(': ', 1)[1]}")

    print("----------------\n")
    info("Enter the ID of the state you want to load (or 'q' to cancel): ")


def validate_state_id(state_id, save_states):
    if not state_id.isdigit:
        error("\nInvalid input. Please enter a valid state ID.\n")
        return False
    elif int(state_id) < 0:
        error("\nState ID cannot be negative. Please enter a valid state ID.\n")
        return False
    elif int(state_id) >= len(save_states):
        error("\nState ID out of range. Please enter a valid state ID.\n")
        return False
    return True


def load_state(arguments):
    if len(arguments) > 1:
        error("\nToo many arguments for load operation!\n")
        sys.exit(1)

    # All list of all saved state
    save_states = all_save_state()
    
    display_save_states(save_states)

    while True:
        # Ask user to input the id of the state to load
        state_id = input(">> ").strip()

        if state_id.lower() == 'q':
            info("\nLoad operation cancelled by user.\n")
            sys.exit(0)

        # Validate the input
        if validate_state_id(state_id, save_states):
            break
    
    # Load the selected state
    run_command(["git", "stash", "apply", f"stash@{{{state_id}}}"])

    success(f"\nState '{save_states[int(state_id)]}' loaded successfully.\n")


def save_state(arguments):
    if len(arguments) > 2:
        error("\nToo many arguments for save operation!\n")
        sys.exit(1)
    elif len(arguments) < 2:
        error("\nState name is required for save operation!\n")
        sys.exit(1)
    
    # Name of the state to save
    state_name = arguments[1]

    run_command(["git", "stash", "push", "-m", state_name])

    success(f"\nState '{state_name}' saved successfully.\n")


# TODO: Implement update_state and delete_state functions
def update_state(arguments):
    pass

def delete_state(arguments):
    pass