from pygitgo.exceptions import GitGoError
from pygitgo.main import main
import pytest
import sys


@pytest.fixture
def _patch_startup(mocker):
    mocker.patch("pygitgo.main.ensure_first_run_setup")
    mocker.patch("pygitgo.main.check_for_updates_background")


def test_main_version_flag(mocker, capsys):
    mocker.patch.object(sys, "argv", ["gitgo", "-v"])
    mocker.patch("pygitgo.main.get_version", return_value="1.8.2")
    mock_check = mocker.patch("pygitgo.main.check_for_updates")

    main()

    captured = capsys.readouterr()
    assert "GitGo 1.8.2" in captured.out
    mock_check.assert_called_once_with("1.8.2")


def test_main_ready_flag(mocker, capsys):
    mocker.patch.object(sys, "argv", ["gitgo", "--ready"])
    mocker.patch("pygitgo.main.get_version", return_value="1.8.2")
    mock_check = mocker.patch("pygitgo.main.check_for_updates")
    mock_info = mocker.patch("pygitgo.main.info")

    main()

    mock_info.assert_called_once()
    mock_check.assert_called_once_with("1.8.2")


def test_main_no_command_prints_help(mocker, capsys, _patch_startup):
    mocker.patch.object(sys, "argv", ["gitgo"])

    main()

    captured = capsys.readouterr()
    assert "usage:" in captured.out.lower() or "Commands" in captured.out


@pytest.mark.parametrize("command,handler", [
    ("jump", "jump_operation"),
    ("link", "link_operation"),
    ("push", "push_operation"),
    ("state", "state_operation"),
    ("user", "user_operation"),
    ("config", "config_operation"),
    ("undo", "undo_operation"),
    ("pull", "pull_operation"),
    ("repo", "repo_operation"),
    ("new", "new_operation"),
    ("init", "init_operation"),
    ("log", "log_operation"),
])
def test_main_dispatches_command(mocker, _patch_startup, command, handler):
    mocker.patch.object(sys, "argv", ["gitgo", command] + _argv_tail(command))
    mock_handler = mocker.patch(f"pygitgo.main.{handler}")

    main()

    mock_handler.assert_called_once()


def _argv_tail(command):
    tails = {
        "jump": ["feature"],
        "link": ["https://github.com/user/repo.git"],
        "push": [],
        "state": ["list"],
        "user": [],
        "config": ["get", "default-branch"],
        "undo": ["commit"],
        "pull": [],
        "repo": [],
        "new": ["my-app"],
        "init": ["my-app"],
        "log": [],
    }
    return tails[command]


def test_main_init_passes_standalone(mocker, _patch_startup):
    mocker.patch.object(sys, "argv", ["gitgo", "init", "my-app"])
    mock_init = mocker.patch("pygitgo.main.init_operation")

    main()

    mock_init.assert_called_once()
    assert mock_init.call_args.kwargs["standalone"] is True


def test_main_gitgo_error_exits_one(mocker, _patch_startup):
    mocker.patch.object(sys, "argv", ["gitgo", "push"])
    mocker.patch("pygitgo.main.push_operation", side_effect=GitGoError("push failed"))
    mock_error = mocker.patch("pygitgo.main.error")

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 1
    mock_error.assert_called_once_with("push failed")


def test_main_keyboard_interrupt_exits_130(mocker, _patch_startup):
    mocker.patch.object(sys, "argv", ["gitgo", "push"])
    mocker.patch("pygitgo.main.push_operation", side_effect=KeyboardInterrupt())
    mock_warning = mocker.patch("pygitgo.main.warning")

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 130
    mock_warning.assert_called_once_with("Operation canceled.")
