from pygitgo.utils.colors import info, print_banner
from pygitgo.commands.init import init_operation
from pygitgo.commands.repo import repo_operation
from pygitgo.commands.link import link_core
import os


def new_operation(args):
    init_operation(args)

    os.chdir(args.name)

    repo_url = repo_operation(args, silent=True)

    link_core(repo_url, "Initial commit", silent=True)

    print_banner("PROJECT LAUNCHED. SCAFFOLDED, CREATED, AND DEPLOYED.")

    print()
    info("Run 'gitgo undo link' to remove the remote and undo the initial commit.")

