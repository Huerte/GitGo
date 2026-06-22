from pygitgo.utils.cli_io import info, warning, error
from pygitgo.utils.executor import run_command
from pygitgo.exceptions import GitGoError


def list_tags():
    result = run_command("git tag")
    if result.returncode == 0:
        tags = result.stdout.strip().split('\n') if result.stdout.strip() else []
        if tags:
            info("Tags in repository:")
            for tag in tags:
                print(f"  • {tag}")
        else:
            warning("No tags found in repository.")
    else:
        raise GitGoError("Failed to list tags.")

def tag_operation(args):
    action = args.action if hasattr(args, 'action') else None
    
    if not action or action == 'list':
        list_tags()
    else:
        raise GitGoError(f"Invalid tag operation '{action}'!")
