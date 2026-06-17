from pygitgo.commands.new import new_operation, _assert_not_inside_target
from unittest.mock import patch, MagicMock
from pygitgo.exceptions import GitGoError
import pytest


@patch("pygitgo.commands.new.init_operation")
@patch("pygitgo.commands.new.repo_operation")
@patch("pygitgo.commands.new.link_core")
@patch("os.chdir")
def test_new_operation_quickstart(mock_chdir, mock_link_core, mock_repo_operation, mock_init_operation, capsys):
    args = MagicMock()
    args.name = "my-project"
    args.lang = "python"
    args.template = None
    args.private = True
    args.description = "my desc"

    mock_repo_operation.return_value = "https://github.com/user/my-project.git"

    new_operation(args)

    mock_init_operation.assert_called_once_with(args)
    mock_chdir.assert_called_once_with("my-project")
    mock_repo_operation.assert_called_once_with(args, silent=True)
    mock_link_core.assert_called_once_with("https://github.com/user/my-project.git", "Initial commit", silent=True, already_initialized=True)

    captured = capsys.readouterr()
    assert "undo link" in captured.out

def test_guard_raises_when_already_inside(tmp_path, monkeypatch):
    target = tmp_path / "my-app"
    target.mkdir()
    monkeypatch.chdir(target)
    with pytest.raises(GitGoError, match="Directory mismatch"):
        _assert_not_inside_target("my-app")


def test_guard_passes_when_outside(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _assert_not_inside_target("my-app") 


def test_guard_case_insensitive_on_windows(tmp_path, monkeypatch):
    target = tmp_path / "My-App"
    target.mkdir()
    monkeypatch.chdir(target)
    with patch("pygitgo.commands.new.get_platform", return_value="windows"):
        with pytest.raises(GitGoError):
            _assert_not_inside_target("my-app")


def test_guard_case_sensitive_on_non_windows(tmp_path, monkeypatch):
    target = tmp_path / "My-App"
    target.mkdir()
    monkeypatch.chdir(target)
    with patch("pygitgo.commands.new.get_platform", return_value="linux"):
        _assert_not_inside_target("my-app")


@patch("pygitgo.commands.new.init_operation")
@patch("pygitgo.commands.new.repo_operation")
@patch("pygitgo.commands.new.link_core")
@patch("os.chdir")
@patch("pygitgo.commands.new.banner")
@patch("pygitgo.commands.new.error")
@patch("pygitgo.commands.new.confirm")
def test_new_operation_link_failure(mock_confirm, mock_error, mock_banner, mock_chdir, mock_link_core, mock_repo_operation, mock_init_operation):
    args = MagicMock()
    args.name = "my-project"
    args.lang = "python"
    args.template = None
    args.private = True
    args.description = "my desc"

    mock_repo_operation.return_value = "https://github.com/user/my-project.git"
    mock_link_core.side_effect = GitGoError("remote link cancelled")
    mock_confirm.return_value = False

    with pytest.raises(SystemExit) as sys_exit:
        new_operation(args)

    assert sys_exit.value.code == 1
    mock_init_operation.assert_called_once_with(args)
    mock_chdir.assert_called_once_with("my-project")
    mock_repo_operation.assert_called_once_with(args, silent=True)
    mock_link_core.assert_called_once_with("https://github.com/user/my-project.git", "Initial commit", silent=True, already_initialized=True)
    mock_banner.assert_not_called()
    mock_error.assert_called_once_with("remote link cancelled")
    mock_confirm.assert_called_once_with("Delete the repo I just created on GitHub? (y/n): ", destructive=True)