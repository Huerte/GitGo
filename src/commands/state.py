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


def display_save_states():
    save_states = all_save_state()

    # Display the list of saved states
    print("\nSaved States:")
    print("-" * 32)
    for state in save_states:
        state_index = state.split(': ', 1)[0].replace("stash@", "").replace("{", "").replace("}", "")
        highlight(f"{int(state_index) + 1} | {state.split(': ', 1)[1]}")

    print("-" * 32 + '\n')


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
            warning("\nLoad operation cancelled by user.\n")
            sys.exit(0)
        proceed = validate_state_id(state_id, save_states)
    
    return state_id


def state_list(arguments):
    if len(arguments) > 1:
        if arguments[1] in ("-h", "--help", "help"):
            print("\nDisplay all saved states.\n")
            warning("\nUsage:\n")
            print("  gitgo state list        # Show all saved states")
            print("  gitgo state -l          # Alias\n")
            sys.exit(0)
        error("\nToo many arguments for list operation!\n")
        sys.exit(1)

    display_save_states()


def load_state(arguments):
    proceed = False

    if len(arguments) > 1:

        if arguments[1] in ("-h", "--help", "help"):
            print("\nLoad a previously saved working state.\n")
            warning("\nUsage:\n")
            print("  gitgo state load <id>   # Load a specific state by ID")
            print("  gitgo state load        # Show all saved states and prompt for selection")
            print("  gitgo state -o <id>     # Alias\n")
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
        display_save_states()
        info("\nEnter the ID of the state you want to load (or 'q' to cancel): ")
        state_id = ask_state_id(save_states)
        
    # Load the selected state
    run_command(["git", "stash", "apply", f"stash@{{{int(state_id) - 1}}}"])

    success(f"\nState '{save_states[int(state_id) - 1]}' loaded successfully.\n")


def save_state(arguments):
    print(arguments)
    if len(arguments) > 2:
        error("\nToo many arguments for save operation!\n")
        sys.exit(1)
    elif len(arguments) < 2:
        state_name = "Auto-Save"
    
    # Name of the state to save
    if len(arguments) == 2:
        if arguments[1] in ("-h", "--help", "help"):
            print("\nSave the current working state with an optional name.\n")
            warning("\nUsage:\n")
            print("  gitgo state save <name>   # Save with a specific name")
            print("  gitgo state save          # Save with default name 'Auto-Save'")
            print("  gitgo state -s <name>     # Alias\n")
            sys.exit(0)
            
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
            print("\nDelete one or all saved working states.\n")
            warning("\nUsage:\n")
            print("  gitgo state delete <id>   # Delete a specific state by ID")
            print("  gitgo state delete -a     # Delete all saved states")
            print("  gitgo state -d <id>       # Alias\n")
            print("  gitgo state -d <id>       # Alias for delete all\n")
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


def state_operations_help():
    warning("\nState Operations Help:\n")
    print("  list, -l      Display all saved states.")
    print("  load, -o      Load a previously saved working state.")
    print("  save, -s      Save the current working state with a given name.")
    print("  delete, -d    Delete a previously saved working state.\n")
    info("Use 'gitgo state <operation> --help' for more information on a specific operation.\n")


def state_operations(arguments):
    if len(arguments) == 0 or arguments[0] in ("-h", "--help", "help"):
        state_operations_help()
        sys.exit(0)

    type_of_operation = arguments[0].lower()
    if type_of_operation in ["list", "-l"]:
        state_list(arguments)
    elif type_of_operation in ["load", "-o"]:
        load_state(arguments)
    elif type_of_operation in ["save", "-s"]:
        save_state(arguments)
    elif type_of_operation in ["delete", "d"]:
        delete_state(arguments)
    else:
        error(f"\nUnknown state operation: {type_of_operation}\n")
        state_operations_help()
        sys.exit(1)