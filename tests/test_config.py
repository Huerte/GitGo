from pygitgo.utils.config import get_config, set_config, config_operation
from conftest import capture_system_exit_code
from argparse import Namespace
import subprocess


def test_get_config_fallback(mocker):
    fake_run = mocker.patch('pygitgo.utils.config.run_command', return_value="")

    fallback_value = "false"

    result = get_config("default-key", fallback_value)
    assert result == fallback_value

def test_get_config_ok(mocker):
    fake_run = mocker.patch('pygitgo.utils.config.run_command', return_value="true")

    fallback_value = "false"

    result = get_config("default-key", fallback_value)
    assert result != fallback_value

def test_set_config_fallback(mocker):
    fake_run = mocker.patch('pygitgo.utils.config.run_command', return_value=subprocess.CalledProcessError(1, 'git'))
    fake_error = mocker.patch('pygitgo.utils.config.error')

    key = 'default-key'

    result = set_config(key, 'true')
    assert result == False

    fake_error.assert_called_with(f"\nFailed to save configuration for '{key}'.")

def test_set_config_ok(mocker):
    fake_run = mocker.patch('pygitgo.utils.config.run_command', return_value='ok')
    fake_error = mocker.patch('pygitgo.utils.config.error')
    fake_success = mocker.patch('pygitgo.utils.config.success')
    
    key = 'default-key'
    value = 'true'

    result = set_config(key, value)
    assert result == True

    fake_error.assert_not_called()
    fake_success.assert_called_with(f"\nConfiguration saved: {key} = '{value}'")

def test_config_operation_not_valid_keys(mocker):
    fake_error = mocker.patch('pygitgo.utils.config.error')
    fake_warning = mocker.patch('pygitgo.utils.config.warning')
    

    VALID_KEYS = ["default-branch", "default-message"]

    key = "not-valid"
    value = "true"
    args = Namespace(key=key, action="set", value=value)

    assert capture_system_exit_code(lambda: config_operation(args)) is None

    fake_error.assert_called_with(f"\nInvalid configuration key: '{key}'")
    fake_warning.assert_called_with(f"Valid keys are: {', '.join(VALID_KEYS)}\n")

def test_get_config_strip(mocker):
    fake_run = mocker.patch('pygitgo.utils.config.run_command', return_value="  true  \n")
    result = get_config("default-key", "false")
    assert result == "true"

def test_get_config_error_handling(mocker):
    fake_run = mocker.patch('pygitgo.utils.config.run_command', return_value=subprocess.CalledProcessError(1, 'git'))
    result = get_config("default-key", "fallback")
    assert result == "fallback"

def test_config_operation_set_no_value(mocker):
    fake_error = mocker.patch('pygitgo.utils.config.error')
    args = Namespace(key="default-branch", action="set") # value is missing
    config_operation(args)
    fake_error.assert_called_with("\nYou must provide a value to set!\n")

def test_config_operation_set_ok(mocker):
    fake_set = mocker.patch('pygitgo.utils.config.set_config')
    args = Namespace(key="default-branch", action="set", value="main")
    config_operation(args)
    fake_set.assert_called_with("default-branch", "main")

def test_config_operation_get_ok(mocker):
    mocker.patch('pygitgo.utils.config.get_config', return_value="main")
    fake_info = mocker.patch('pygitgo.utils.config.info')
    args = Namespace(key="default-branch", action="get")
    config_operation(args)
    fake_info.assert_called_with("\ndefault-branch is currently set to: 'main'\n")

def test_config_operation_get_none(mocker):
    mocker.patch('pygitgo.utils.config.get_config', return_value=None)
    fake_warning = mocker.patch('pygitgo.utils.config.warning')
    args = Namespace(key="default-branch", action="get")
    config_operation(args)
    fake_warning.assert_called_with("\ndefault-branch is not currently set.\n")

