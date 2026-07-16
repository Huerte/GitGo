from pygitgo.utils.update_checker import check_for_updates_background, check_for_updates
from pygitgo.utils.cli_io import info, warning, error, write, _highlight_cmd
from pygitgo.utils.bootstrap import ensure_first_run_setup
from pygitgo.commands.resolve import resolve_operation
from pygitgo.commands.config import config_operation
from pygitgo.commands.state import state_operation
from pygitgo.commands.undo import undo_operation
from pygitgo.commands.pull import pull_operation
from pygitgo.commands.jump import jump_operation
from pygitgo.commands.link import link_operation
from pygitgo.commands.push import push_operation
from pygitgo.commands.user import user_operation
from pygitgo.commands.repo import repo_operation
from pygitgo.commands.init import init_operation
from pygitgo.commands.sync import sync_operation
from pygitgo.commands.log import log_operation
from pygitgo.commands.new import new_operation
from pygitgo.utils.cli_io import set_verbosity
from pygitgo.utils.banner import show_banner
from pygitgo.exceptions import GitGoError
import argparse
import sys



def get_version():
    try:
        from importlib.metadata import version
        return version("pygitgo")
    except Exception:
        return "dev"


class ColorHelpFormatter(argparse.RawDescriptionHelpFormatter):
    def _format_action(self, action):
        result = super()._format_action(action)
        return _highlight_cmd(result)

    def format_help(self):
        result = super().format_help()
        return _highlight_cmd(result)


def _add_subcommand(subparsers, name, help, epilog=None, description=None):
    kwargs = {
        "help": help,
        "formatter_class": ColorHelpFormatter
    }
    if epilog is not None:
        kwargs["epilog"] = epilog
    if description is not None:
        kwargs["description"] = description
    return subparsers.add_parser(name, **kwargs)


def main():
    parser = argparse.ArgumentParser(
        prog='gitgo',
        description="GitGo CLI - Your Fast Git Companion",
        epilog="Use 'gitgo <command> -h' for help on a specific command."
    )
    
    parser.add_argument("-v", "-V", "--version", action="store_true", help="show program's version number and exit")
    parser.add_argument("-r", "--ready", action="store_true", help="Check tool readiness")

    parser.add_argument("-q", "--quiet", action="store_true", help="Hide all non-error output")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose debug output")

    subparsers = parser.add_subparsers(title="Commands", dest="command")
    subparsers.required = False

    jump_parser = _add_subcommand(
        subparsers,
        "jump", 
        help="Safely switch branches with try-and-revert",
        epilog="Examples:\n  gitgo jump feature/login          Switch to 'feature/login' branch"
    )
    jump_parser.add_argument("branch", help="The name of the branch to jump to")

    link_parser = _add_subcommand(
        subparsers,
        "link", 
        help="Init, commit, and link to a remote repo",
        epilog=(
            "Examples:\n"
            "  gitgo link https://github.com/user/repo.git               Link to a remote repo\n"
            "  gitgo link https://github.com/user/repo.git 'First commit' Link with custom commit message"
        )
    )
    link_parser.add_argument("url", help="The GitHub repository URL to link")
    link_parser.add_argument("message", nargs="?", default="Initial commit", help="Custom commit message")

    push_parser = _add_subcommand(
        subparsers,
        "push",
        help="Commit and push branch to remote",
        epilog=(
            "Examples:\n"
            "  gitgo push                        Push current branch with default message\n"
            "  gitgo push main 'fix auth bug'    Push to main with a custom message\n"
            "  gitgo push 'fix auth bug'         Push current branch with a custom message\n"
            "  gitgo push -n feature/login 'add login'   Create new branch and push\n"
            "  gitgo push -s main 'fix bug'      Pick which files to include before pushing"
        )
    )
    push_parser.add_argument("-n", "--new", action="store_true", help="Create a new branch before pushing")
    push_parser.add_argument("-s", "--select", action="store_true", help="Interactively select which files to stage")
    push_parser.add_argument("branch", nargs="?", default=None, help="Branch to push to (default: current branch)")
    push_parser.add_argument("message", nargs="?", default=None, help="Commit message")

    state_parser = _add_subcommand(
        subparsers,
        "state",
        help="Manage saved working states (stashes)",
        epilog=(
            "Examples:\n"
            "  gitgo state list                  Show all saved states\n"
            "  gitgo state save 'halfway done'   Save current work with a name\n"
            "  gitgo state load 1                Restore state by ID\n"
            "  gitgo state delete 1              Delete a specific state\n"
            "  gitgo state delete -a             Delete all saved states"
        )
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
    
    user_parser = _add_subcommand(
        subparsers,
        "user", 
        help="Manage Git user identity",
        epilog=(
            "Examples:\n"
            "  gitgo user login                  Authenticate with Git provider\n"
            "  gitgo user logout                 Remove authentication credentials"
        )
    )
    user_parser.add_argument("action", nargs="?", choices=["login", "logout"], default=None, help="login or logout")

    config_parser = _add_subcommand(
        subparsers,
        "config",
        help="Manage GitGo default settings",
        epilog=(
            "Examples:\n"
            "  gitgo config set default-branch master\n"
            "  gitgo config set default-message 'WIP'\n"
            "  gitgo config get default-branch"
        )
    )
    config_parser.add_argument("action", choices=["set", "get"], help="Action to perform")
    config_parser.add_argument("key", choices=["default-branch", "default-message"], help="The setting to change")
    config_parser.add_argument("value", nargs="?", help="The new value (required for 'set')")

    undo_parser = _add_subcommand(
        subparsers,
        "undo", 
        help="Safely undo mistakes", 
        epilog=(
            "Examples:\n"
            "  gitgo undo commit       Undo your last commit (your files are safe)\n"
            "  gitgo undo add          Undo 'git add' (files are no longer ready to commit)\n"
            "  gitgo undo changes      DANGER: Throw away all new changes and start fresh\n"
            "  gitgo undo link         Remove the remote and undo the initial commit\n"
            "  gitgo undo push         DANGER: Revert the last push with a force-push\n"
            "  gitgo undo pull         Revert the branch to its state before the last pull"
        )
    )
    undo_parser.add_argument(
        "action", 
        choices=["commit", "add", "changes", "link", "push", "pull"], 
        help="What to undo: 'commit', 'add', 'changes', 'link', 'push', or 'pull'"
    )

    pull_parser = _add_subcommand(
        subparsers,
        "pull", 
        help="Safely pull the latest code without losing your changes",
        epilog=(
            "Examples:\n"
            "  gitgo pull                Safely pull updates for your current branch\n"
            "  gitgo pull main           Safely pull updates from the 'main' branch\n"
        )
    )
    pull_parser.add_argument("branch", nargs="?", default=None, help="The branch to pull from (default is your current branch)")

    resolve_parser = _add_subcommand(
        subparsers,
        "resolve", 
        help="Resolve a paused sync after fixing a merge conflict",
        description="Automatically stages your resolved files and finishes the active merge conflict, bypassing the text editor.",
        epilog=(
            "Examples:\n"
            "  gitgo resolve                     Finish merge conflict after fixing files\n"
            "  gitgo resolve --abort             Cancel the merge/rebase and revert to pre-pull state"
        )
    )
    resolve_parser.add_argument("--abort", action="store_true", help="Abort the current merge/rebase and revert to the pre-pull state")

    init_parser = _add_subcommand(
        subparsers,
        "init",
        help="Scaffold a new project structure",
        epilog=(
            "Examples:\n"
            "  gitgo init my-app python          Scaffold a Python project locally\n"
            "  gitgo init my-app --template owner/repo  Download a template locally\n"
        )
    )
    init_parser.add_argument(
        "name",
        metavar="NAME",
        help="Project name or path to scaffold"
    )
    init_parser.add_argument(
        "lang",
        nargs="?",
        default=None,
        metavar="LANG",
        help="Language to scaffold (e.g. python, node, rust, go)."
    )
    init_parser.add_argument(
        "--template",
        default=None,
        metavar="OWNER/REPO",
        help="GitHub template repo to clone instead of a language scaffold."
    )

    repo_parser = _add_subcommand(
        subparsers,
        "repo",
        help="Create a remote GitHub repository",
        epilog=(
            "Examples:\n"
            "  gitgo repo                         Use current directory name as repo name\n"
            "  gitgo repo my-app                  Create repo 'my-app' on GitHub\n"
            "  gitgo repo my-app --private        Create a private repo\n"
        )
    )
    repo_parser.add_argument(
        "name",
        default=None,
        nargs="?",
        metavar="NAME",
        help="Repository name. Defaults to current directory name."
    )
    repo_parser.add_argument(
        "-p", "--private",
        default=False,
        action="store_true",
        help="Create a private repository."
    )
    repo_parser.add_argument(
        "-d", "--description",
        default="",
        metavar="TEXT",
        help="Short repository description shown on GitHub."
    )

    new_parser = _add_subcommand(
        subparsers,
        "new",
        help="Scaffold, create remote repo, and push in one command",
        epilog=(
            "Examples:\n"
            "  gitgo new my-app python            Scaffold a Python project and push it\n"
            "  gitgo new my-app --private         Private repo, no language scaffold\n"
            "  gitgo new my-app rust --private    Private Rust project\n"
        )
    )
    new_parser.add_argument(
        "name",
        metavar="NAME",
        help="Project name. Used for both the local folder and the GitHub repo."
    )
    new_parser.add_argument(
        "lang",
        nargs="?",
        default=None,
        metavar="LANG",
        help="Language to scaffold (e.g. python, node, rust, go)."
    )
    new_parser.add_argument(
        "--template",
        default=None,
        metavar="OWNER/REPO",
        help="GitHub template repo to clone instead of a language scaffold."
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

    log_parser = _add_subcommand(
        subparsers,
        "log",
        help="Show commit history",
        epilog=(
            "Examples:\n"
            "  gitgo log                         Show last 5 commits for current branch\n"
            "  gitgo log -n 10                   Show last 10 commits\n"
            "  gitgo log -b main                 Show commits for the 'main' branch\n"
            "  gitgo log -b feature -n 3         Show last 3 commits for 'feature' branch"
        )
    )
    log_parser.add_argument(
        "-n", "--number",
        dest="number",
        type=int,
        default=5,
        metavar="NUMBER",
        help="Number of commits to show."
    )
    log_parser.add_argument(
        "-b", "--branch",
        default=None,
        metavar="BRANCH",
        help="Branch to show commits for."
    )

    sync_parser = _add_subcommand(
        subparsers,
        "sync",
        help="Download updates, save your work, and upload in one step (pull, commit, push)",
        epilog=(
            "Examples:\n"
            "  gitgo sync                        Sync with default commit message\n"
            "  gitgo sync 'Fix navbar'           Sync and commit with a custom message\n"
        )
    )
    sync_parser.add_argument("message", nargs="?", default=None, help="Commit message for your local changes")

    args = parser.parse_args()

    set_verbosity(quiet=args.quiet, verbose=getattr(args, 'verbose', False))

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
        show_banner()
        return

    ensure_first_run_setup()
    check_for_updates_background(get_version())

    COMMANDS = {
        "push": push_operation,
        "link": link_operation,
        "jump": jump_operation,
        "state": state_operation,
        "user": user_operation,
        "resolve": resolve_operation,
        "config": config_operation,
        "undo": undo_operation,
        "pull": pull_operation,
        "repo": repo_operation,
        "new": new_operation,
        "init": lambda a: init_operation(a, standalone=True),
        "log": log_operation,
        "sync": sync_operation,
    }

    try:
        handler = COMMANDS.get(args.command)
        if handler:
            handler(args)
    except GitGoError as e:
        error(f"{e}")
        sys.exit(1)
    except KeyboardInterrupt:
        write()
        warning("Operation canceled.")
        sys.exit(130)
    except Exception as e:
        error(f"Unexpected error ({type(e).__name__}): {e}")
        info("If this keeps happening, report it: https://github.com/Huerte/GitGo/issues")
        sys.exit(1)

if __name__ == "__main__":
    main()
