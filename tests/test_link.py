import pytest
from argparse import Namespace
from pygitgo.exceptions import GitCommandError, GitGoError
from pygitgo.commands.link import link_operation


def test_link_invalid_url():
    args = Namespace(url="invalid-url", message="Initial commit")
    with pytest.raises(GitGoError) as exc_info:
        link_operation(args)
    assert "Invalid repository URL!" in str(exc_info.value)


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

    fake_run = mocker.patch("pygitgo.commands.link.run_command", return_value="")

    args = Namespace(url="git@github.com:user/repo.git", message="Initial commit")
    link_operation(args)

    fake_commit.assert_called_once_with("Initial commit", loading_msg="Creating initial commit...", ok_text="Initial commit created.")
    fake_add_remote.assert_called_once_with("git@github.com:user/repo.git")
    fake_run.assert_any_call(["git", "branch", "-m", "main"], loading_msg="Renaming branch 'master' to 'main'...")
    fake_run.assert_any_call(["git", "ls-remote", "--heads", "origin", "main"], loading_msg="Checking remote branches...")
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
            "1234567890abcdef refs/heads/main",  # remote_refs check
            "Successfully pulled"                 # git pull
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
            "1234567890abcdef refs/heads/main",  # remote_refs check
            GitCommandError(["git", "pull"])     # git pull fails
        ]
    )

    args = Namespace(url="git@github.com:user/repo.git", message="Initial commit")
    link_operation(args)

    fake_error.assert_called_once_with("Failed to merge remote content. You may need to resolve conflicts manually.")
    fake_warning.assert_any_call("Run: git pull origin main --allow-unrelated-histories")