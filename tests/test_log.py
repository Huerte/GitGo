from pygitgo.exceptions import GitCommandError, GitGoError
from pygitgo.commands.log import log_operation
from argparse import Namespace
import pytest

@pytest.fixture
def base_args():
    return Namespace(number=5, branch=None)

def test_log_operation_success(mocker, base_args):
    mock_run = mocker.patch("pygitgo.commands.log.run_command")
    
    # Mock rev-parse (is-inside-work-tree)
    # Mock rev-parse HEAD (commits exist)
    # Mock log command output
    mock_run.side_effect = [
        "true",  # rev-parse --is-inside-work-tree
        "abc1234",  # rev-parse HEAD
        "abc1234||User Name||2 hours ago||Initial commit"  # git log
    ]
    
    mock_branch = mocker.patch("pygitgo.commands.log.get_current_branch", return_value="main")
    mock_write = mocker.patch("pygitgo.commands.log.write")
    mock_banner = mocker.patch("pygitgo.commands.log.banner")

    # Mock colors to be enabled for test consistency
    mocker.patch("pygitgo.commands.log.YELLOW", "\033[33m")
    mocker.patch("pygitgo.commands.log.CYAN", "\033[36m")
    mocker.patch("pygitgo.commands.log.GREEN", "\033[32m")
    mocker.patch("pygitgo.commands.log.RESET", "\033[0m")
    
    log_operation(base_args)
    
    mock_banner.assert_called_once_with("Commit History", "Showing last 5 commits on main", required=True)
    mock_write.assert_any_call("[\033[33mabc1234\033[0m] Initial commit (\033[36m2 hours ago\033[0m) [\033[32mUser Name\033[0m]", required=True)


def test_log_not_git_repo(mocker, base_args):
    mock_run = mocker.patch("pygitgo.commands.log.run_command")
    mock_run.side_effect = GitCommandError(["git"], "fatal: not a git repository")
    
    with pytest.raises(GitGoError, match="Not inside a git repository"):
        log_operation(base_args)

def test_log_no_commits(mocker, base_args):
    mock_run = mocker.patch("pygitgo.commands.log.run_command")
    mock_run.side_effect = [
        "true",
        GitCommandError(["git"], "fatal: ambiguous argument 'HEAD': unknown revision")
    ]
    
    mock_info = mocker.patch("pygitgo.commands.log.info")
    
    log_operation(base_args)
    mock_info.assert_called_once_with("No commits found in this repository.")

def test_log_invalid_branch(mocker, base_args):
    base_args.branch = "nonexistent"
    
    mock_run = mocker.patch("pygitgo.commands.log.run_command", return_value="true")
    mocker.patch("pygitgo.commands.log.is_branch_exist", return_value=False)
    
    with pytest.raises(GitGoError, match="Branch 'nonexistent' does not exist"):
        log_operation(base_args)

def test_log_with_branch_success(mocker, base_args):
    base_args.branch = "feature"
    
    mock_run = mocker.patch("pygitgo.commands.log.run_command")
    mock_run.side_effect = [
        "true",  # rev-parse --is-inside-work-tree
        "abc1234",  # rev-parse HEAD
        "def5678||Bob||1 day ago||Feature added"  # git log
    ]
    
    mocker.patch("pygitgo.commands.log.is_branch_exist", return_value=True)
    mock_banner = mocker.patch("pygitgo.commands.log.banner")
    
    log_operation(base_args)
    mock_banner.assert_called_once_with("Commit History", "Showing last 5 commits on feature", required=True)

