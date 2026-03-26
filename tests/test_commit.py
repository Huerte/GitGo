from pygitgo.commands.commit import generate_messages, commit_operation, atomic_commit
import subprocess
import pytest


def check_pytest_system_exit(function):
    with pytest.raises(SystemExit) as exc_info:
        function()
    return exc_info.value.code

def test_generate_messages():
    assert generate_messages("A", "src/main.py") == "feat: add main.py"
    assert generate_messages("A", "Dockerfile") == "feat: add Dockerfile"
    assert generate_messages("M", "README.md") == "docs: update README.md"
    assert generate_messages("M", "my code file.txt") == "docs: update my code file.txt"
    assert generate_messages("UU", "conflict.py") is None

def test_commit_operation_empty_status(mocker):
    mocker.patch('pygitgo.commands.commit.get_status_content', return_value="")
    fake_warning = mocker.patch('pygitgo.commands.commit.warning')
    
    assert check_pytest_system_exit(commit_operation) == 0
    fake_warning.assert_called_with("\nNo changes to commit.\n")

def test_commit_operation_no_valid_commits(mocker):
    mocker.patch('pygitgo.commands.commit.get_status_content', return_value="UU conflict.py")
    fake_warning = mocker.patch('pygitgo.commands.commit.warning')
    
    assert check_pytest_system_exit(commit_operation) == 0
    fake_warning.assert_called_with("\nNo valid files to automatically commit.\n")

def test_commit_operation_cancel_commit(mocker):
    mocker.patch('pygitgo.commands.commit.get_status_content', return_value="A main.py")
    mocker.patch('builtins.input', return_value="n")
    fake_warning = mocker.patch('pygitgo.commands.commit.warning')
    
    assert check_pytest_system_exit(commit_operation) == 0
    fake_warning.assert_called_with("\nCommit operation cancelled.\n")

def test_commit_operation_cancel_push(mocker):
    mocker.patch('pygitgo.commands.commit.get_status_content', return_value="A main.py")
    mocker.patch('builtins.input', side_effect=["y", "n"])
    mocker.patch('pygitgo.commands.commit.atomic_commit')
    
    assert check_pytest_system_exit(commit_operation) == 0

def test_commit_operation_success(mocker):
    mocker.patch('pygitgo.commands.commit.get_status_content', return_value="A main.py")
    mocker.patch('builtins.input', side_effect=["y", "y"])
    mocker.patch('pygitgo.commands.commit.get_current_branch', return_value="main")
    fake_push = mocker.patch('pygitgo.commands.commit.git_push')
    fake_atomic = mocker.patch('pygitgo.commands.commit.atomic_commit')
    
    commit_operation()
    
    fake_atomic.assert_called_once()
    fake_push.assert_called_once_with("main")

def test_atomic_commit_success(mocker):
    fake_run = mocker.patch('pygitgo.commands.commit.run_command')
    change_list = [["A", "main.py", "feat: add main.py"]]
    
    atomic_commit(change_list)
    
    fake_run.assert_any_call(['git', 'add', 'main.py'])
    fake_run.assert_any_call(['git', 'commit', '-m', "feat: add main.py"])

def test_atomic_commit_failure(mocker):
    fake_run = mocker.patch('pygitgo.commands.commit.run_command', side_effect=[None, subprocess.CalledProcessError(1, 'git')])
    change_list = [["A", "main.py", "feat: add main.py"]]
    
    assert check_pytest_system_exit(lambda: atomic_commit(change_list)) == 1
    fake_run.assert_any_call(['git', 'add', 'main.py'])
