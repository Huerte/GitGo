from pygitgo.exceptions import GitCommandError, GitGoError
from pygitgo.commands.link import link_operation, _link_interrupt_cleanup, link_core
from argparse import Namespace
import pytest
import sys

def test_link_invalid_url():
    args = Namespace(url="invalid-url", message="Initial commit")
    with pytest.raises(GitGoError) as exc_info:
        link_operation(args)
    assert "Invalid remote repository URL:" in str(exc_info.value)

def test_link_existing_repo(mocker):
    mocker.patch("pygitgo.commands.link.validate_repo_url", return_value=True)
    mocker.patch("pygitgo.commands.link.git_init", return_value=False)
    fake_add_remote = mocker.patch("pygitgo.commands.link.add_remote_origin")
    fake_confirm = mocker.patch("pygitgo.commands.link.confirm_remote_link", return_value=True)
    fake_success = mocker.patch("pygitgo.commands.link.success")
    fake_commit = mocker.patch("pygitgo.commands.link.git_commit")

    args = Namespace(url="git@github.com:user/repo.git", message="Initial commit")
    link_operation(args)

    fake_add_remote.assert_called_once_with("git@github.com:user/repo.git")
    fake_confirm.assert_called_once_with(ok_text="Remote linked to existing repository.")
    fake_success.assert_not_called()
    fake_commit.assert_not_called()

def test_link_new_repo_no_remote_refs(mocker):
    mocker.patch("pygitgo.commands.link.validate_repo_url", return_value=True)
    mocker.patch("pygitgo.commands.link.git_init", return_value=True)
    fake_commit = mocker.patch("pygitgo.commands.link.git_commit", return_value=True)
    fake_add_remote = mocker.patch("pygitgo.commands.link.add_remote_origin")
    mocker.patch("pygitgo.commands.link.confirm_remote_link", return_value=True)
    mocker.patch("pygitgo.commands.link.get_current_branch", return_value="master")
    mocker.patch("pygitgo.commands.link.get_default_branch", return_value="main")
    fake_push = mocker.patch("pygitgo.commands.link.git_push")

    fake_run = mocker.patch(
        "pygitgo.commands.link.run_command",
        side_effect=[
            "",       
            "",       
            "abc123", 
        ]
    )

    args = Namespace(url="git@github.com:user/repo.git", message="Initial commit")
    link_operation(args)

    fake_commit.assert_called_once_with("Initial commit", loading_msg="Creating initial commit...", ok_text="Initial commit created.")
    fake_add_remote.assert_called_once_with("git@github.com:user/repo.git")
    fake_run.assert_any_call(["git", "branch", "-m", "main"], loading_msg="Renaming branch 'master' to 'main'...", ok_text="Branch renamed to 'main'.")
    fake_run.assert_any_call(["git", "ls-remote", "--heads", "origin", "main"], loading_msg="Checking remote branches...", ok_text="Remote branches checked.")
    fake_push.assert_called_once_with("main")

def test_link_new_repo_with_remote_refs_pull_success(mocker):
    mocker.patch("pygitgo.commands.link.validate_repo_url", return_value=True)
    mocker.patch("pygitgo.commands.link.git_init", return_value=True)
    mocker.patch("pygitgo.commands.link.git_commit", return_value=True)
    mocker.patch("pygitgo.commands.link.add_remote_origin")
    mocker.patch("pygitgo.commands.link.confirm_remote_link", return_value=True)
    mocker.patch("pygitgo.commands.link.get_current_branch", return_value="main")
    mocker.patch("pygitgo.commands.link.get_default_branch", return_value="main")
    fake_push = mocker.patch("pygitgo.commands.link.git_push")
    fake_success = mocker.patch("pygitgo.commands.link.success")

    fake_run = mocker.patch(
        "pygitgo.commands.link.run_command",
        side_effect=[
            "1234567890abcdef refs/heads/main",  
            "Successfully pulled",                
            "123456"                              
        ]
    )

    args = Namespace(url="git@github.com:user/repo.git", message="Initial commit")
    link_operation(args)

    fake_run.assert_any_call(
        ["git", "pull", "origin", "main", "--allow-unrelated-histories", "--no-edit"],
        loading_msg="Pulling and merging remote content...",
        ok_text="Remote content merged."
    )
    fake_success.assert_not_called()
    fake_push.assert_called_once_with("main")

def test_link_new_repo_with_remote_refs_pull_failure(mocker):
    mocker.patch("pygitgo.commands.link.validate_repo_url", return_value=True)
    mocker.patch("pygitgo.commands.link.git_init", return_value=True)
    mocker.patch("pygitgo.commands.link.git_commit", return_value=True)
    mocker.patch("pygitgo.commands.link.add_remote_origin")
    mocker.patch("pygitgo.commands.link.confirm_remote_link", return_value=True)
    mocker.patch("pygitgo.commands.link.get_current_branch", return_value="main")
    mocker.patch("pygitgo.commands.link.get_default_branch", return_value="main")
    fake_error = mocker.patch("pygitgo.commands.link.error")
    fake_warning = mocker.patch("pygitgo.commands.link.warning")

    fake_run = mocker.patch(
        "pygitgo.commands.link.run_command",
        side_effect=[
            "1234567890abcdef refs/heads/main",  
            GitCommandError(["git", "pull"]),    
            "123456"                             
        ]
    )

    args = Namespace(url="git@github.com:user/repo.git", message="Initial commit")
    with pytest.raises(GitGoError):
        link_operation(args)

    fake_error.assert_called_once_with("Failed to merge remote content. You may need to resolve conflicts manually.")
    fake_warning.assert_any_call("Run: git pull origin main --allow-unrelated-histories")

def test_link_core_already_initialized_commits_and_pushes(mocker):
    from pygitgo.commands.link import link_core

    mocker.patch("pygitgo.commands.link.validate_repo_url", return_value=True)
    mocker.patch("pygitgo.commands.link.check_connection", return_value=True)
    mocker.patch("pygitgo.commands.link.convert_https_to_ssh", return_value="git@github.com:user/repo.git")
    fake_init = mocker.patch("pygitgo.commands.link.git_init")
    fake_commit = mocker.patch("pygitgo.commands.link.git_commit", return_value=True)
    fake_add_remote = mocker.patch("pygitgo.commands.link.add_remote_origin")
    mocker.patch("pygitgo.commands.link.get_current_branch", return_value="main")
    mocker.patch("pygitgo.commands.link.get_default_branch", return_value="main")
    mocker.patch("pygitgo.commands.link.run_command", return_value="123456")
    fake_push = mocker.patch("pygitgo.commands.link.git_push")

    link_core(
        "https://github.com/user/repo.git",
        "Initial commit",
        silent=True,
        already_initialized=True,
    )

    fake_init.assert_not_called()
    fake_commit.assert_called_once_with(
        "Initial commit",
        loading_msg="Creating initial commit...",
        ok_text="Initial commit created.",
    )
    fake_add_remote.assert_called_once_with("git@github.com:user/repo.git")
    fake_push.assert_called_once_with("main")

def test_link_keyboard_interrupt_during_commit(mocker):
    from pygitgo.commands.link import link_core

    mocker.patch("pygitgo.commands.link.validate_repo_url", return_value=True)
    mocker.patch("pygitgo.commands.link.check_connection", return_value=False)
    mocker.patch("pygitgo.commands.link.git_init", return_value=True)
    mocker.patch("pygitgo.commands.link.git_commit", side_effect=KeyboardInterrupt())
    mock_warning = mocker.patch("pygitgo.commands.link.warning")
    mock_cleanup = mocker.patch("pygitgo.commands.link._link_interrupt_cleanup")

    with pytest.raises(SystemExit) as exc_info:
        link_core("https://github.com/user/repo.git", "Initial commit")

    assert exc_info.value.code == 130
    mock_warning.assert_any_call("Link interrupted (Ctrl+C).")
    mock_cleanup.assert_called_once_with(
        "https://github.com/user/repo.git",
        True,
        False,
        False,
    )

def test_link_keyboard_interrupt_after_remote_added(mocker):
    from pygitgo.commands.link import link_core

    mocker.patch("pygitgo.commands.link.validate_repo_url", return_value=True)
    mocker.patch("pygitgo.commands.link.check_connection", return_value=False)
    mocker.patch("pygitgo.commands.link.git_init", return_value=True)
    mocker.patch("pygitgo.commands.link.git_commit", return_value=True)
    mocker.patch("pygitgo.commands.link.add_remote_origin")
    mocker.patch("pygitgo.commands.link.get_current_branch", side_effect=KeyboardInterrupt())
    mock_cleanup = mocker.patch("pygitgo.commands.link._link_interrupt_cleanup")

    with pytest.raises(SystemExit) as exc_info:
        link_core("https://github.com/user/repo.git", "Initial commit")

    assert exc_info.value.code == 130
    mock_cleanup.assert_called_once_with(
        "https://github.com/user/repo.git",
        True,
        True,
        True,
    )

def test_link_existing_repo_failure(mocker):
    mocker.patch("pygitgo.commands.link.validate_repo_url", return_value=True)
    mocker.patch("pygitgo.commands.link.git_init", return_value=False)
    fake_add_remote = mocker.patch("pygitgo.commands.link.add_remote_origin")
    fake_confirm = mocker.patch("pygitgo.commands.link.confirm_remote_link", side_effect=GitGoError("Connection failed"))

    args = Namespace(url="git@github.com:user/repo.git", message="Initial commit")
    with pytest.raises(GitGoError) as exc_info:
        link_operation(args)
    
    assert "Connection failed" in str(exc_info.value)
    fake_add_remote.assert_called_once_with("git@github.com:user/repo.git")
    fake_confirm.assert_called_once_with(ok_text="Remote linked to existing repository.")

def test_link_interrupt_cleanup_exceptions(mocker):
    mocker.patch("pygitgo.commands.link.run_command", side_effect=GitCommandError(["merge", "--abort"]))
    mocker.patch("shutil.rmtree", side_effect=Exception("rmtree failed"))
    fake_warning = mocker.patch("pygitgo.commands.link.warning")
    _link_interrupt_cleanup("https://url.git", True, False, True)
    fake_warning.assert_any_call("Could not auto-remove '.git' folder.")

def test_link_interrupt_cleanup_not_initialized(mocker):
    mocker.patch("pygitgo.commands.link.run_command", return_value="")
    fake_success = mocker.patch("pygitgo.commands.link.success")
    _link_interrupt_cleanup("https://url.git", False, False, False)
    fake_success.assert_called_once_with("No Git state was changed. Your files are safe.")

def test_link_core_ssh_check_fails(mocker):
    mocker.patch("pygitgo.commands.link.validate_repo_url", return_value=True)
    mocker.patch("pygitgo.commands.link.check_connection", return_value=False)
    mocker.patch("pygitgo.commands.link.git_init", return_value=True)
    mocker.patch("pygitgo.commands.link.git_commit", return_value=True)
    mocker.patch("pygitgo.commands.link.add_remote_origin")
    mocker.patch("pygitgo.commands.link.get_current_branch", return_value="main")
    mocker.patch("pygitgo.commands.link.get_default_branch", return_value="main")
    fake_warning = mocker.patch("pygitgo.commands.link.warning")
    mocker.patch("pygitgo.commands.link.run_command", return_value="")
    mocker.patch("pygitgo.commands.link.git_push")
    mocker.patch("pygitgo.commands.link.banner")

    link_core("https://github.com/user/repo.git", "message", silent=True)
    fake_warning.assert_called_once_with("SSH check failed. Using HTTPS — you may be prompted for credentials on push.")

def test_link_core_branch_fails(mocker):
    mocker.patch("pygitgo.commands.link.validate_repo_url", return_value=True)
    mocker.patch("pygitgo.commands.link.git_init", return_value=True)
    mocker.patch("pygitgo.commands.link.git_commit", return_value=True)
    mocker.patch("pygitgo.commands.link.add_remote_origin")
    mocker.patch("pygitgo.commands.link.get_default_branch", return_value="main")
    mocker.patch("pygitgo.commands.link.get_current_branch", side_effect=GitCommandError(["branch"]))

    with pytest.raises(GitGoError) as ex:
        link_core("git@github.com:user/repo.git", "message", silent=True)
    assert "Could not determine the current branch" in str(ex.value)

def test_link_core_ls_remote_fails(mocker):
    mocker.patch("pygitgo.commands.link.validate_repo_url", return_value=True)
    mocker.patch("pygitgo.commands.link.git_init", return_value=True)
    mocker.patch("pygitgo.commands.link.git_commit", return_value=True)
    mocker.patch("pygitgo.commands.link.add_remote_origin")
    mocker.patch("pygitgo.commands.link.get_current_branch", return_value="main")
    mocker.patch("pygitgo.commands.link.get_default_branch", return_value="main")
    mocker.patch("pygitgo.commands.link.git_push")
    mocker.patch("pygitgo.commands.link.run_command", side_effect=[
        GitCommandError(["ls-remote"]),
        GitCommandError(["rev-parse"])
    ])
    link_core("git@github.com:user/repo.git", "message", silent=True)

def test_link_core_no_commits(mocker):
    mocker.patch("pygitgo.commands.link.validate_repo_url", return_value=True)
    mocker.patch("pygitgo.commands.link.git_init", return_value=True)
    mocker.patch("pygitgo.commands.link.git_commit", return_value=True)
    mocker.patch("pygitgo.commands.link.add_remote_origin")
    mocker.patch("pygitgo.commands.link.get_current_branch", return_value="main")
    mocker.patch("pygitgo.commands.link.get_default_branch", return_value="main")
    mocker.patch("pygitgo.commands.link.run_command", side_effect=[
        "",
        GitCommandError(["rev-parse"])
    ])
    fake_info = mocker.patch("pygitgo.commands.link.info")
    link_core("git@github.com:user/repo.git", "message", silent=True)
    fake_info.assert_called_once_with("Repository is currently empty. Add files and run 'gitgo push' to upload.")