from pygitgo.commands.state import (
    delete_state, save_state, load_state, validate_state_id,
    all_save_state
)
import pytest


@pytest.mark.parametrize('state_id', ['1', '3', '11', '00002'])
def test_validate_state_id(state_id, mocker):
    fake_error = mocker.patch('pygitgo.commands.state.error')
    result = validate_state_id(state_id, [1] * 12)
    assert result is True
    fake_error.assert_not_called()


@pytest.mark.parametrize('state_id', ['-1', '-3', '-11', '-00002'])
def test_validate_state_id_negative(state_id, mocker):
    fake_error = mocker.patch('pygitgo.commands.state.error')
    result = validate_state_id(state_id, [1] * 12)
    assert result is False
    fake_error.assert_called_with("\nState ID cannot be '0' or negative. Please enter a valid state ID.\n")


@pytest.mark.parametrize('state_id', ['4', '10', '15', '0000020'])
def test_validate_state_id_out_scope(state_id, mocker):
    fake_error = mocker.patch('pygitgo.commands.state.error')
    result = validate_state_id(state_id, [1] * 3)
    assert result is False
    fake_error.assert_called_with("\nState ID out of range. Please enter a valid state ID.\n")


def test_all_save_state_no_output(mocker):
    mocker.patch("pygitgo.commands.state.git_stash_list", return_value="")
    mocker.patch("pygitgo.commands.state.info")

    result = all_save_state()

    assert result == []


def test_all_save_state_with_output(mocker):
    output = (
        "stash@{0}||2023-10-27 10:00:00||Test stash\n"
        "stash@{1}||2023-10-27 10:05:00||Another stash"
    )
    mocker.patch("pygitgo.commands.state.git_stash_list", return_value=output)

    result = all_save_state()

    assert len(result) == 2
    assert result[0] == {
        "id": 1, "ref": "stash@{1}",
        "date": "2023-10-27 10:05:00", "message": "Another stash",
        "stash_index": 1
    }
    assert result[1] == {
        "id": 2, "ref": "stash@{0}",
        "date": "2023-10-27 10:00:00", "message": "Test stash",
        "stash_index": 0
    }


def test_all_save_state_malformed_line(mocker):
    output = "malformed_line_here\nstash@{1}||2023-10-27 10:05:00||Another stash"
    mocker.patch("pygitgo.commands.state.git_stash_list", return_value=output)
    fake_warning = mocker.patch("pygitgo.commands.state.warning")

    result = all_save_state()

    assert len(result) == 1
    assert result[0]["message"] == "Another stash"
    fake_warning.assert_called_once_with("Skipping malformed line: malformed_line_here")


def test_load_state_specific_id(mocker):
    save_states = [{"id": 1, "ref": "stash@{0}", "date": "date", "message": "msg", "stash_index": 0}]
    mocker.patch("pygitgo.commands.state.all_save_state", return_value=save_states)
    mocker.patch("pygitgo.commands.state.validate_state_id", return_value=True)
    fake_apply = mocker.patch("pygitgo.commands.state.git_stash_apply", return_value=True)
    fake_success = mocker.patch("pygitgo.commands.state.success")

    load_state("1")

    fake_apply.assert_called_once_with(stash_id="0")
    fake_success.assert_called_once_with("\nState 'msg' loaded successfully.\n")


def test_load_state_invalid_id(mocker):
    save_states = [{"id": 1, "ref": "stash@{0}", "date": "date", "message": "msg", "stash_index": 0}]
    mocker.patch("pygitgo.commands.state.all_save_state", return_value=save_states)
    mocker.patch("pygitgo.commands.state.validate_state_id", return_value=False)

    from pygitgo.exceptions import GitGoError
    with pytest.raises(GitGoError):
        load_state("100")


def test_load_state_invalid_argument(mocker):
    save_states = [{"id": 1, "ref": "stash@{0}", "date": "date", "message": "msg", "stash_index": 0}]
    mocker.patch("pygitgo.commands.state.all_save_state", return_value=save_states)

    from pygitgo.exceptions import GitGoError
    with pytest.raises(GitGoError):
        load_state("invalid_arg")


def test_load_state_no_args(mocker):
    save_states = [
        {"id": 1, "ref": "stash@{1}", "date": "date", "message": "msg", "stash_index": 1},
        {"id": 2, "ref": "stash@{0}", "date": "date2", "message": "msg2", "stash_index": 0},
    ]
    mocker.patch("pygitgo.commands.state.all_save_state", return_value=save_states)
    mocker.patch("pygitgo.commands.state.ask_state_id", return_value="2")
    fake_apply = mocker.patch("pygitgo.commands.state.git_stash_apply", return_value=True)
    fake_success = mocker.patch("pygitgo.commands.state.success")

    load_state()

    fake_apply.assert_called_once_with(stash_id="0")
    fake_success.assert_called_once_with("\nState 'msg2' loaded successfully.\n")


def test_save_state_no_args(mocker):
    mocker.patch("pygitgo.commands.state.run_command", return_value="M file")
    fake_push = mocker.patch(
        "pygitgo.commands.state.git_stash_push",
        return_value=True
    )
    fake_success = mocker.patch("pygitgo.commands.state.success")

    save_state()

    fake_push.assert_called_once_with(label="Auto-Save")
    fake_success.assert_called_once_with("\nState 'Auto-Save' saved successfully.\n")


def test_save_state_with_name(mocker):
    mocker.patch("pygitgo.commands.state.run_command", return_value="M file")
    fake_push = mocker.patch(
        "pygitgo.commands.state.git_stash_push",
        return_value=True
    )
    fake_success = mocker.patch("pygitgo.commands.state.success")

    save_state("My-State")

    fake_push.assert_called_once_with(label="My-State")
    fake_success.assert_called_once_with("\nState 'My-State' saved successfully.\n")


def test_delete_state_all_confirm(mocker):
    mocker.patch("builtins.input", return_value="y")
    mocker.patch("pygitgo.commands.state.all_save_state", return_value=[{"id": 1}])
    fake_clear = mocker.patch("pygitgo.commands.state.git_stash_clear", return_value=True)
    fake_success = mocker.patch("pygitgo.commands.state.success")

    delete_state("-a")

    fake_clear.assert_called_once()
    fake_success.assert_called_once_with("\nAll saved states deleted successfully.\n")


def test_delete_state_all_cancel(mocker):
    mocker.patch("builtins.input", return_value="n")
    mocker.patch("pygitgo.commands.state.all_save_state", return_value=[{"id": 1}])
    fake_warning = mocker.patch("pygitgo.commands.state.warning")

    delete_state("-a")

    fake_warning.assert_called_once_with("\nDelete operation cancelled by user.\n")


def test_delete_state_invalid_id(mocker):
    mocker.patch("pygitgo.commands.state.all_save_state", return_value=[{"id": 1}])

    from pygitgo.exceptions import GitGoError
    with pytest.raises(GitGoError):
        delete_state("abc")


def test_delete_state_specific_id(mocker):
    save_states = [{"id": 1, "ref": "stash@{0}", "date": "date", "message": "msg", "stash_index": 0}]
    mocker.patch("pygitgo.commands.state.validate_state_id", return_value=True)
    mocker.patch("pygitgo.commands.state.all_save_state", return_value=save_states)
    fake_drop = mocker.patch("pygitgo.commands.state.git_stash_drop", return_value=True)
    fake_success = mocker.patch("pygitgo.commands.state.success")

    delete_state("1")

    fake_drop.assert_called_once_with(stash_id="0")
    fake_success.assert_called_once_with("\nState with ID '1' deleted successfully.\n")


def test_delete_state_no_args(mocker):
    save_states = [
        {"id": 1, "ref": "stash@{1}", "date": "date", "message": "msg", "stash_index": 1},
        {"id": 2, "ref": "stash@{0}", "date": "date2", "message": "msg2", "stash_index": 0},
    ]
    mocker.patch("pygitgo.commands.state.all_save_state", return_value=save_states)
    mocker.patch("pygitgo.commands.state.ask_state_id", return_value="2")
    fake_drop = mocker.patch("pygitgo.commands.state.git_stash_drop", return_value=True)
    fake_success = mocker.patch("pygitgo.commands.state.success")

    delete_state()

    fake_drop.assert_called_once_with(stash_id="0")
    fake_success.assert_called_once_with("\nState with ID '2' deleted successfully.\n")
