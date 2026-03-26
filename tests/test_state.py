from pygitgo.commands.state import (
    delete_state, save_state, load_state, validate_state_id, 
    all_save_state
)
from unittest.mock import call
import pytest


@pytest.mark.parametrize('state_id',[
    '1', '3', '11', '00002', '7.0'
])
def test_validate_state_id(state_id, mocker):
    fake_error = mocker.patch('pygitgo.commands.state.error')

    save_states = [1] * 12
    result = validate_state_id(state_id, save_states)
    assert result == True

    fake_error.assert_not_called()

@pytest.mark.parametrize('state_id',[
    '-1', '-3', '-11', '-00002', '-7.0'
])
def test_validate_state_id_negative(state_id, mocker):

    save_states = [1] * 12
    fake_error = mocker.patch('pygitgo.commands.state.error')

    result = validate_state_id(state_id, save_states)
    assert result == False

    fake_error.assert_called_with("\nState ID cannot be '0' or negative. Please enter a valid state ID.\n")

@pytest.mark.parametrize('state_id',[
    '4', '10', '15', '0000020', '00007.00000'
])
def test_validate_state_id_out_scope(state_id, mocker):

    save_states = [1] * 3
    fake_error = mocker.patch('pygitgo.commands.state.error')

    result = validate_state_id(state_id, save_states)
    assert result == False

    fake_error.assert_called_with("\nState ID out of range. Please enter a valid state ID.\n")


def test_all_save_state_no_output(mocker):
    fake_run = mocker.patch("pygitgo.commands.state.run_command", return_value="")
    fake_info = mocker.patch("pygitgo.commands.state.info")

    with pytest.raises(SystemExit) as exc_info:
        all_save_state()

    assert exc_info.value.code == 0
    fake_info.assert_called_once_with("\nNo saved states found.\n")
    fake_run.assert_called_once_with([
        "git", "stash", "list",
        "--date=format:%Y-%m-%d %H:%M:%S",
        "--pretty=%gd||%cd||%s"
    ])

def test_all_save_state_with_output(mocker):
    output = "stash@{0}||2023-10-27 10:00:00||Test stash\nstash@{1}||2023-10-27 10:05:00||Another stash"
    fake_run = mocker.patch("pygitgo.commands.state.run_command", return_value=output)

    result = all_save_state()

    assert len(result) == 2
    assert result[0] == {
        "id": 1,
        "ref": "stash@{0}",
        "date": "2023-10-27 10:00:00",
        "message": "Test stash"
    }
    assert result[1] == {
        "id": 2,
        "ref": "stash@{1}",
        "date": "2023-10-27 10:05:00",
        "message": "Another stash"
    }
    fake_run.assert_called_once_with([
        "git", "stash", "list",
        "--date=format:%Y-%m-%d %H:%M:%S",
        "--pretty=%gd||%cd||%s"
    ])

def test_all_save_state_malformed_line(mocker):
    output = "malformed_line_here\nstash@{1}||2023-10-27 10:05:00||Another stash"
    fake_run = mocker.patch("pygitgo.commands.state.run_command", return_value=output)
    fake_warning = mocker.patch("pygitgo.commands.state.warning")

    result = all_save_state()

    assert len(result) == 1
    assert result[0] == {
        "id": 2,
        "ref": "stash@{1}",
        "date": "2023-10-27 10:05:00",
        "message": "Another stash"
    }
    fake_warning.assert_called_once_with("Skipping malformed line: malformed_line_here")
    fake_run.assert_called_once_with([
        "git", "stash", "list",
        "--date=format:%Y-%m-%d %H:%M:%S",
        "--pretty=%gd||%cd||%s"
    ])


def test_load_state_specific_id(mocker):
    save_states = [{"id": 1, "ref": "stash@{0}", "date": "date", "message": "msg"}]
    mocker.patch("pygitgo.commands.state.all_save_state", return_value=save_states)
    mocker.patch("pygitgo.commands.state.validate_state_id", return_value=True)
    fake_run = mocker.patch("pygitgo.commands.state.run_command")
    fake_success = mocker.patch("pygitgo.commands.state.success")

    load_state("1")

    fake_run.assert_called_once_with(["git", "stash", "apply", "0"])
    fake_success.assert_called_once_with("\nState 'msg' loaded successfully.\n")

def test_load_state_invalid_id(mocker):
    save_states = [{"id": 1, "ref": "stash@{0}", "date": "date", "message": "msg"}]
    mocker.patch("pygitgo.commands.state.all_save_state", return_value=save_states)
    mocker.patch("pygitgo.commands.state.validate_state_id", return_value=False)

    with pytest.raises(SystemExit) as exc_info:
        load_state("100")

    assert exc_info.value.code == 1

def test_load_state_invalid_argument(mocker):
    save_states = [{"id": 1, "ref": "stash@{0}", "date": "date", "message": "msg"}]
    mocker.patch("pygitgo.commands.state.all_save_state", return_value=save_states)
    fake_error = mocker.patch("pygitgo.commands.state.error")

    with pytest.raises(SystemExit) as exc_info:
        load_state("invalid_arg")

    assert exc_info.value.code == 1
    fake_error.assert_called_once_with("\nInvalid argument 'invalid_arg' for load operation. Expected a state ID.\n")

def test_load_state_no_args(mocker):
    save_states = [{"id": 1, "ref": "stash@{0}", "date": "date", "message": "msg"},
                   {"id": 2, "ref": "stash@{1}", "date": "date2", "message": "msg2"}]
    mocker.patch("pygitgo.commands.state.all_save_state", return_value=save_states)
    mocker.patch("pygitgo.commands.state.ask_state_id", return_value="2")
    fake_run = mocker.patch("pygitgo.commands.state.run_command")
    fake_success = mocker.patch("pygitgo.commands.state.success")

    load_state()

    fake_run.assert_called_once_with(["git", "stash", "apply", "1"])
    fake_success.assert_called_once_with("\nState 'msg2' loaded successfully.\n")


def test_save_state_no_args(mocker):
    fake_run = mocker.patch("pygitgo.commands.state.run_command")
    fake_success = mocker.patch("pygitgo.commands.state.success")

    save_state()

    fake_run.assert_called_once_with(["git", "stash", "push", "-m", "Auto-Save"])
    fake_success.assert_called_once_with("\nState 'Auto-Save' saved successfully.\n")

def test_save_state_with_name(mocker):
    fake_run = mocker.patch("pygitgo.commands.state.run_command")
    fake_success = mocker.patch("pygitgo.commands.state.success")

    save_state("My-State")

    fake_run.assert_called_once_with(["git", "stash", "push", "-m", "My-State"])
    fake_success.assert_called_once_with("\nState 'My-State' saved successfully.\n")


def test_delete_state_all_confirm(mocker):
    mocker.patch("builtins.input", return_value="y")
    fake_run = mocker.patch("pygitgo.commands.state.run_command")
    fake_success = mocker.patch("pygitgo.commands.state.success")

    with pytest.raises(SystemExit) as exc_info:
        delete_state("-a")

    assert exc_info.value.code == 0
    fake_run.assert_called_once_with(["git", "stash", "clear"])
    fake_success.assert_called_once_with("\nAll saved states deleted successfully.\n")

def test_delete_state_all_cancel(mocker):
    mocker.patch("builtins.input", return_value="n")
    fake_warning = mocker.patch("pygitgo.commands.state.warning")

    with pytest.raises(SystemExit) as exc_info:
        delete_state("-a")

    assert exc_info.value.code == 0
    fake_warning.assert_called_once_with("\nDelete operation cancelled by user.\n")

def test_delete_state_invalid_id(mocker):
    fake_error = mocker.patch("pygitgo.commands.state.error")
    
    with pytest.raises(SystemExit) as exc_info:
        delete_state("abc")

    assert exc_info.value.code == 1
    fake_error.assert_called_once_with("\nInvalid input. Please enter a valid state ID.\n")

def test_delete_state_specific_id(mocker):
    mocker.patch("pygitgo.commands.state.validate_state_id", return_value=True)
    mocker.patch("pygitgo.commands.state.all_save_state", return_value=[])
    fake_run = mocker.patch("pygitgo.commands.state.run_command")
    fake_success = mocker.patch("pygitgo.commands.state.success")

    delete_state("1")

    fake_run.assert_called_once_with(["git", "stash", "drop", "0"])
    fake_success.assert_called_once_with("\nState with ID '1' deleted successfully.\n")

def test_delete_state_no_args(mocker):
    mocker.patch("pygitgo.commands.state.all_save_state", return_value=[])
    mocker.patch("pygitgo.commands.state.ask_state_id", return_value="2")
    fake_run = mocker.patch("pygitgo.commands.state.run_command")
    fake_success = mocker.patch("pygitgo.commands.state.success")

    delete_state()

    fake_run.assert_called_once_with(["git", "stash", "drop", "1"])
    fake_success.assert_called_once_with("\nState with ID '2' deleted successfully.\n")
