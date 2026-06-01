import pytest
from unittest.mock import patch, MagicMock
from pygitgo.commands.staging import get_changed_files, display_file_picker, selective_stage
from argparse import Namespace
import subprocess

@patch("pygitgo.commands.staging.run_command")
def test_get_changed_files_with_changes(mock_run_command):
    mock_run_command.return_value = "M  src/main.py\n?? new_file.txt\nM  README.md"

    files = get_changed_files()

    assert len(files) == 3
    assert files[0]["path"] == "src/main.py"
    assert files[0]["label"] == "modified"
    assert files[1]["path"] == "new_file.txt"
    assert files[1]["label"] == "new file"
    assert files[2]["path"] == "README.md"
    assert files[2]["label"] == "modified"


@patch("pygitgo.commands.staging.run_command")
def test_get_changed_files_no_changes(mock_run_command):
    from pygitgo.exceptions import GitCommandError
    mock_run_command.side_effect = GitCommandError(["git", "status"])

    files = get_changed_files()

    assert files == []


@patch("pygitgo.commands.staging.run_command")
def test_get_changed_files_empty_status(mock_run_command):
    mock_run_command.return_value = ""

    files = get_changed_files()

    assert files == []


@patch("pygitgo.commands.staging.run_command")
def test_get_changed_files_deleted_file(mock_run_command):
    mock_run_command.return_value = "D  old_file.py"

    files = get_changed_files()

    assert len(files) == 1
    assert files[0]["path"] == "old_file.py"
    assert files[0]["label"] == "deleted"


@patch("pygitgo.commands.staging.pick")
def test_display_file_picker_select_specific(mock_pick):
    mock_pick.return_value = [("(modified) src/main.py", 0), ("(modified) README.md", 2)]

    files = [
        {"status": "M", "label": "modified", "path": "src/main.py"},
        {"status": "??", "label": "new file", "path": "new_file.txt"},
        {"status": "M", "label": "modified", "path": "README.md"},
    ]

    selected = display_file_picker(files)

    assert selected == ["src/main.py", "README.md"]
    mock_pick.assert_called_once()


@patch("pygitgo.commands.staging.pick")
def test_display_file_picker_select_all(mock_pick):
    mock_pick.return_value = [("(modified) src/main.py", 0), ("(new file) new_file.txt", 1)]

    files = [
        {"status": "M", "label": "modified", "path": "src/main.py"},
        {"status": "??", "label": "new file", "path": "new_file.txt"},
    ]

    selected = display_file_picker(files)

    assert selected == ["src/main.py", "new_file.txt"]


@patch("pygitgo.commands.staging.pick")
def test_display_file_picker_cancel(mock_pick):
    mock_pick.return_value = []

    files = [
        {"status": "M", "label": "modified", "path": "src/main.py"},
    ]

    selected = display_file_picker(files)

    assert selected == []


@patch("pygitgo.commands.staging.pick")
def test_display_file_picker_select_single(mock_pick):
    mock_pick.return_value = [("(new file) new_file.txt", 1)]

    files = [
        {"status": "M", "label": "modified", "path": "src/main.py"},
        {"status": "??", "label": "new file", "path": "new_file.txt"},
    ]

    selected = display_file_picker(files)

    assert selected == ["new_file.txt"]


@patch("pygitgo.commands.staging.run_command")
@patch("pygitgo.commands.staging.success")
def test_selective_stage(mock_success, mock_run_command):
    selected_files = ["src/main.py", "README.md"]

    selective_stage(selected_files)

    assert mock_run_command.call_count == 2
    mock_run_command.assert_any_call(["git", "add", "--", "src/main.py"])
    mock_run_command.assert_any_call(["git", "add", "--", "README.md"])
    mock_success.assert_called_once()


@patch("pygitgo.commands.staging.run_command")
@patch("pygitgo.commands.staging.success")
def test_selective_stage_single_file(mock_success, mock_run_command):
    selective_stage(["README.md"])

    mock_run_command.assert_called_once_with(["git", "add", "--", "README.md"])
    mock_success.assert_called_once()
