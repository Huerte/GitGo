from pygitgo.commands.user import display_current_user, user_operation
from pygitgo.exceptions import GitGoError
from argparse import Namespace
import pytest


def test_display_current_user_configured(mocker):
    mocker.patch('pygitgo.commands.user.get_user', return_value=('Alice', 'alice@example.com'))
    mocker.patch('shutil.get_terminal_size', return_value=Namespace(columns=80))
    fake_info = mocker.patch('pygitgo.commands.user.info')

    display_current_user()

    fake_info.assert_any_call("Git User:  Alice")
    fake_info.assert_any_call("Git Email: alice@example.com")


def test_display_current_user_not_configured(mocker):
    mocker.patch('pygitgo.commands.user.get_user', return_value=(None, None))
    fake_warning = mocker.patch('pygitgo.commands.user.warning')
    fake_info = mocker.patch('pygitgo.commands.user.info')

    display_current_user()

    fake_warning.assert_called_once_with("No Git user identity configured.")
    fake_info.assert_called_once_with("Run 'gitgo user login'")


def test_user_operation_no_action(mocker):
    fake_display = mocker.patch('pygitgo.commands.user.display_current_user')
    args = Namespace()
    user_operation(args)
    fake_display.assert_called_once()


def test_user_operation_login(mocker):
    fake_login = mocker.patch('pygitgo.commands.user.login')
    args = Namespace(action='login')
    user_operation(args)
    fake_login.assert_called_once()


def test_user_operation_logout(mocker):
    fake_logout = mocker.patch('pygitgo.commands.user.logout')
    args = Namespace(action='logout')
    user_operation(args)
    fake_logout.assert_called_once()


def test_user_operation_invalid_action(mocker):
    args = Namespace(action='invalid')
    with pytest.raises(GitGoError) as exc_info:
        user_operation(args)
    assert "Invalid user operation 'invalid'!" in str(exc_info.value)
