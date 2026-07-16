from pygitgo.commands.config import config_operation
from argparse import Namespace
import pytest


from pygitgo.exceptions import GitGoError


def test_config_operation_not_valid_keys(mocker):
    VALID_KEYS = ["default-branch", "default-message"]
    key = "not-valid"
    value = "true"
    args = Namespace(key=key, action="set", value=value)

    with pytest.raises(GitGoError, match="Invalid configuration key"):
        config_operation(args)


def test_config_operation_set_no_value(mocker):
    args = Namespace(key="default-branch", action="set")
    with pytest.raises(GitGoError, match="You must provide a value to set"):
        config_operation(args)

def test_config_operation_set_ok(mocker):
    fake_set = mocker.patch('pygitgo.commands.config.set_config')
    args = Namespace(key="default-branch", action="set", value="main")
    config_operation(args)
    fake_set.assert_called_with("default-branch", "main")

def test_config_operation_get_ok(mocker):
    mocker.patch('pygitgo.commands.config.get_config', return_value="main")
    fake_info = mocker.patch('pygitgo.commands.config.info')
    args = Namespace(key="default-branch", action="get")
    config_operation(args)
    fake_info.assert_called_with("\ndefault-branch is currently set to: 'main'\n", required=True)

def test_config_operation_get_none(mocker):
    mocker.patch('pygitgo.commands.config.get_config', return_value=None)
    fake_warning = mocker.patch('pygitgo.commands.config.warning')
    args = Namespace(key="default-branch", action="get")
    config_operation(args)
    fake_warning.assert_called_with("\ndefault-branch is not currently set.\n", required=True)

