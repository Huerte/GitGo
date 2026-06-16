from pygitgo.commands.config import config_operation
from conftest import capture_system_exit_code
from argparse import Namespace
import pytest


def test_config_operation_not_valid_keys(mocker):
    fake_error = mocker.patch('pygitgo.commands.config.error')
    fake_warning = mocker.patch('pygitgo.commands.config.warning')
    
    VALID_KEYS = ["default-branch", "default-message"]

    key = "not-valid"
    value = "true"
    args = Namespace(key=key, action="set", value=value)

    assert capture_system_exit_code(lambda: config_operation(args)) == 0

    fake_error.assert_called_with(f"\nInvalid configuration key: '{key}'")
    fake_warning.assert_called_with(f"Valid keys are: {', '.join(VALID_KEYS)}\n")

def test_config_operation_set_no_value(mocker):
    fake_error = mocker.patch('pygitgo.commands.config.error')
    args = Namespace(key="default-branch", action="set")
    config_operation(args)
    fake_error.assert_called_with("\nYou must provide a value to set!\n")

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
    fake_info.assert_called_with("\ndefault-branch is currently set to: 'main'\n")

def test_config_operation_get_none(mocker):
    mocker.patch('pygitgo.commands.config.get_config', return_value=None)
    fake_warning = mocker.patch('pygitgo.commands.config.warning')
    args = Namespace(key="default-branch", action="get")
    config_operation(args)
    fake_warning.assert_called_with("\ndefault-branch is not currently set.\n")
