from pygitgo.utils.update_checker import check_for_updates_background, check_for_updates
from pygitgo.utils.bootstrap import ensure_first_run_setup
from pygitgo.utils.colors import info, warning, error
from pygitgo.commands.config import config_operation
from pygitgo.commands.state import state_operation
from pygitgo.commands.undo import undo_operation
from pygitgo.commands.pull import pull_operation
from pygitgo.commands.jump import jump_operation
from pygitgo.commands.link import link_operation
from pygitgo.commands.push import push_operation
from pygitgo.commands.user import user_operation
from pygitgo.commands.new import new_operation
from pygitgo.exceptions import GitGoError
import argparse
import sys



def get_version():
    try:
        from importlib.metadata import version
        return version("pygitgo")
    except Exception:
        return "dev"


def main():
    parser = argparse.ArgumentParser(
        prog='gitgo',
        description="GitGo CLI - Your Fast Git Companion",
        epilog="Use 'gitgo <command> -h' for help on a specific command."
    )
    
    parser.add_argument("-v", "-V", "--version", action="store_true", help="show program's version number and exit")
    parser.add_argument("-r", "--ready", action="store_true", help="Check tool readiness")

    subparsers = parser.add_subparsers(title="Commands", dest="command")
    subparsers.required = False

    jump_parser = subparsers.add_parser("jump", help="Safely switch branches with try-and-revert")
    jump_parser.add_argument("branch", help="The name of the branch to jump to")

    link_parser = subparsers.add_parser("link", help="Init, commit, and link to a remote repo")
    link_parser.add_argument("url", help="The GitHub repository URL to link")
    link_parser.add_argument("message", nargs="?", default="Initial commit", help="Custom commit message")

    push_parser = subparsers.add_parser(
        "push",
        help="Commit and push branch to remote",
        epilog=(
            "Examples:\n"
            "  gitgo push                        Push current branch with default message\n"
            "  gitgo push main 'fix auth bug'    Push to main with a custom message\n"
            "  gitgo push 'fix auth bug'         Push current branch with a custom message\n"
            "  gitgo push -n feature/login 'add login'   Create new branch and push\n"
            "  gitgo push -s main 'fix bug'      Pick which files to include before pushing"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    push_parser.add_argument("-n", "--new", action="store_true", help="Create a new branch before pushing")
    push_parser.add_argument("-s", "--select", action="store_true", help="Interactively select which files to stage")
    push_parser.add_argument("branch", nargs="?", default=None, help="Branch to push to (default: current branch)")
    push_parser.add_argument("message", nargs="?", default=None, help="Commit message")

    state_parser = subparsers.add_parser(
        "state",
        help="Manage saved working states (stashes)",
        epilog=(
            "Examples:\n"
            "  gitgo state list                  Show all saved states\n"
            "  gitgo state save 'halfway done'   Save current work with a name\n"
            "  gitgo state load 1                Restore state by ID\n"
            "  gitgo state delete 1              Delete a specific state\n"
            "  gitgo state delete -a             Delete all saved states"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    state_parser.add_argument(
        "action",
        nargs="?",
        choices=["list", "save", "load", "delete"],
        metavar="action",
        default=None,
        help="list, save, load, delete"
    )
    state_parser.add_argument(
        "identifier",
        nargs="?",
        default=None,
        help="Optional name or ID"
    )
    _alias_group = state_parser.add_mutually_exclusive_group()
    _alias_group.add_argument("-l", dest="action_alias", action="store_const", const="list",   help="Alias for 'list'")
    _alias_group.add_argument("-s", dest="action_alias", action="store_const", const="save",   help="Alias for 'save'")
    _alias_group.add_argument("-o", dest="action_alias", action="store_const", const="load",   help="Alias for 'load'")
    _alias_group.add_argument("-d", dest="action_alias", action="store_const", const="delete", help="Alias for 'delete'")

    state_parser.add_argument(
        "-a", "--all",
        action="store_true",
        help="Apply action to all states (e.g., delete all)"
    )
    
    user_parser = subparsers.add_parser("user", help="Manage Git user identity")
    user_parser.add_argument("action", nargs="?", choices=["login", "logout"], default=None, help="login or logout")

    config_parser = subparsers.add_parser("config",
        help="Manage GitGo default settings",
        epilog=(
            "Examples:\n"
            "  gitgo config set default-branch master\n"
            "  gitgo config set default-message 'WIP'\n"
            "  gitgo config get default-branch"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    config_parser.add_argument("action", choices=["set", "get"], help="Action to perform")
    config_parser.add_argument("key", choices=["default-branch", "default-message"], help="The setting to change")
    config_parser.add_argument("value", nargs="?", help="The new value (required for 'set')")

    undo_parser = subparsers.add_parser("undo", 
        help="Safely undo mistakes", 
        epilog=(
            "Examples:\n"
            "  gitgo undo commit       Undo your last commit (your files are safe)\n"
            "  gitgo undo add          Undo 'git add' (files are no longer ready to commit)\n"
            "  gitgo undo changes      DANGER: Throw away all new changes and start fresh\n"
            "  gitgo undo link         Remove the remote and undo the initial commit\n"
            "  gitgo undo push         DANGER: Revert the last push with a force-push"
        ), 
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    undo_parser.add_argument(
        "action", 
        choices=["commit", "add", "changes", "link", "push"], 
        help="What to undo: 'commit', 'add', 'changes', 'link', or 'push'"
    )

    pull_parser = subparsers.add_parser("pull", 
        help="Safely pull the latest code without losing your changes",
        epilog=(
            "Examples:\n"
            "  gitgo pull                Safely pull updates for your current branch\n"
            "  gitgo pull main           Safely pull updates from the 'main' branch\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    pull_parser.add_argument("branch", nargs="?", default=None, help="The branch to pull from (default is your current branch)")

    new_parser = subparsers.add_parser(
        "new",
        help="Create a GitHub repo and link the current project to it",
        epilog=(
            "Examples:\n"
            "  gitgo new                          Use current directory name as repo name\n"
            "  gitgo new my-app                   Create repo 'my-app' and push\n"
            "  gitgo new my-app --private         Create a private repo\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    new_parser.add_argument(
        "name",
        default=None,
        nargs="?",
        metavar="NAME",
        help="Repository name. Defaults to current directory name."
    )
    new_parser.add_argument(
        "-p", "--private",
        default=False,
        action="store_true",
        help="Create a private repository."
    )
    new_parser.add_argument(
        "-d", "--description",
        default="",
        metavar="TEXT",
        help="Short repository description shown on GitHub."
    )
    
    args = parser.parse_args()

    if getattr(args, 'version', False):
        current_v = get_version()
        print(f"GitGo {current_v}")
        print(f"Support GitGo: https://ko-fi.com/huerte")
        check_for_updates(current_v)
        return

    if args.ready:
        info("ALL UNITS ONLINE. GitGo STANDING BY. AWAITING COMMANDS...")
        check_for_updates(get_version())
        return

    if not args.command:
        parser.print_help()
        return

    ensure_first_run_setup()
    check_for_updates_background(get_version())

    try:
        if args.command == "jump":
            jump_operation(args)
        elif args.command == "link":
            link_operation(args)
        elif args.command == "push":
            push_operation(args)
        elif args.command == "state":
            state_operation(args)
        elif args.command == "user":
            user_operation(args)
        elif args.command == "config":
            config_operation(args)
        elif args.command == "undo":
            undo_operation(args)
        elif args.command == "pull":
            pull_operation(args)
        elif args.command == "new":
            new_operation(args)
    except GitGoError as e:
        error(f"{e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print()
        warning("Operation canceled.")
        sys.exit(130)

if __name__ == "__main__":
    main()
