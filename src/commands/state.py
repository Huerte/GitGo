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
    print("-" * 32)
    for state in save_states:
        state_index = state.split(': ', 1)[0].replace("stash@", "").replace("{", "").replace("}", "")
        highlight(f"{int(state_index) + 1} | {state.split(': ', 1)[1]}")

    print("-" * 32)
    info("\nEnter the ID of the state you want to load (or 'q' to cancel): ")


def validate_state_id(state_id, save_states):
    if not state_id.isdigit:
        error("\nInvalid input. Please enter a valid state ID.\n")
        return False
    elif (int(state_id) - 1) < 0:
        error("\nState ID cannot be negative. Please enter a valid state ID.\n")
        return False
    elif (int(state_id) - 1) >= len(save_states):
        error("\nState ID out of range. Please enter a valid state ID.\n")
        return False
    return True


def ask_state_id(save_states):
    proceed = False
    state_id = None

    while not proceed:
        state_id = input(">> ").strip().lower()
        if state_id == 'q':
            info("\nLoad operation cancelled by user.\n")
            sys.exit(0)
        proceed = validate_state_id(state_id, save_states)
    
    return state_id


def load_state(arguments):
    proceed = False

    if len(arguments) > 1:

        if arguments[1] in ("-h", "--help", "help"):
            print("\nUsage: gitgo load\n")
            print("Loads a previously saved working state.\n")
            warning("\nSyntax:\n")
            print("        gitgo load                # Lists all saved states and prompts for selection")
            print("        gitgo load <state_id>     # Loads the state with the specified ID\n")
            sys.exit(0)
        
        elif arguments[1].isdigit():
            state_id = arguments[1]
            proceed = validate_state_id(state_id, all_save_state())

        else:
            error("\nToo many arguments for save operation!\n")
            sys.exit(1)

    # All list of all saved state
    save_states = all_save_state()
    
    if not proceed:
        display_save_states(save_states)
        state_id = ask_state_id(save_states)
        
    # Load the selected state
    run_command(["git", "stash", "apply", f"stash@{{{int(state_id) - 1}}}"])

    success(f"\nState '{save_states[int(state_id) - 1]}' loaded successfully.\n")


def save_state(arguments):
    if len(arguments) > 2:
        error("\nToo many arguments for save operation!\n")
        sys.exit(1)
    elif len(arguments) < 2:
        state_name = "Auto-Save"
    
    if arguments[1] in ("-h", "--help", "help"):
        print("\nUsage: gitgo save <state_name>\n")
        print("Saves the current working state with the given name.\n")
        warning("\nSyntax:\n")
        print("        gitgo save <state_name>   # Saves the current state with the specified name\n")
        sys.exit(0)
    
    # Name of the state to save
    if len(arguments) == 2:
        state_name = arguments[1]

    run_command(["git", "stash", "push", "-m", state_name])

    success(f"\nState '{state_name}' saved successfully.\n")


def delete_state(arguments):
    if len(arguments) > 2:
        error("\nToo many arguments for delete operation!\n")
        sys.exit(1)
    elif len(arguments) < 2:
        state_id = ask_state_id(all_save_state())
    else:
        if arguments[1] in ("-h", "--help", "help"):
            print("\nUsage: gitgo delete <state_id>\n")
            print("Deletes a previously saved working state.\n")
            warning("\nSyntax:\n")
            print("        gitgo delete <state_id>   # Deletes the state with the specified ID\n")
            print("        gitgo delete -a           # Deletes all saved states\n")
            sys.exit(0)
        
        elif arguments[1] == '-a':
            confirm = input("\nAre you sure you want to delete all saved states? (y/n): ").strip().lower()
            if confirm.lower() == 'y':
                run_command(["git", "stash", "clear"])
                success("\nAll saved states deleted successfully.\n")
                sys.exit(0)
            else:
                warning("\nDelete operation cancelled by user.\n")
                sys.exit(0)
        
        elif not arguments[1].isdigit():
            error("\nInvalid input. Please enter a valid state ID.\n")
            sys.exit(1)

        state_id = arguments[1]
        if not validate_state_id(state_id, all_save_state()):
            sys.exit(1)
    
    run_command(["git", "stash", "drop", f"stash@{{{int(state_id) - 1}}}"])
    success(f"\nState with ID '{state_id}' deleted successfully.\n")