from pygitgo.utils.executor import run_command
from pygitgo.exceptions import GitCommandError
import subprocess
import pytest

def test_run_command_success(mocker):
    mock_run = mocker.patch("subprocess.run")
    mock_result = mocker.MagicMock()
    mock_result.stdout = "hello world\n"
    mock_run.return_value = mock_result

    res = run_command(["echo", "hello"])
    assert res == "hello world"
    mock_run.assert_called_once_with(["echo", "hello"], check=True, capture_output=True, text=True, stdin=subprocess.DEVNULL)

def test_run_command_success_complete(mocker):
    mock_run = mocker.patch("subprocess.run")
    mock_result = mocker.MagicMock()
    mock_run.return_value = mock_result

    res = run_command(["echo", "hello"], return_complete=True)
    assert res == mock_result

def test_run_command_spinner_success(mocker):
    mock_run = mocker.patch("subprocess.run")
    mock_result = mocker.MagicMock()
    mock_result.stdout = "done"
    mock_run.return_value = mock_result

    # Mock yaspin spinner
    mock_yaspin = mocker.patch("pygitgo.utils.executor.yaspin")
    mock_spinner = mocker.MagicMock()
    mock_yaspin.return_value = mock_spinner

    res = run_command(["echo", "hello"], loading_msg="Loading...", ok_text="Ok")
    assert res == "done"
    mock_spinner.start.assert_called_once()
    assert mock_spinner.text == "Ok"
    mock_spinner.ok.assert_called_once_with("✔")

def test_run_command_called_process_error(mocker):
    mock_run = mocker.patch("subprocess.run", side_effect=subprocess.CalledProcessError(1, ["cmd"], stderr="some error"))
    
    with pytest.raises(GitCommandError) as exc_info:
        run_command(["cmd"])
    
    assert exc_info.value.returncode == 1
    assert exc_info.value.stderr == "some error"

def test_run_command_os_error(mocker):
    mock_run = mocker.patch("subprocess.run", side_effect=OSError("file not found"))
    
    with pytest.raises(GitCommandError) as exc_info:
        run_command(["cmd"])
    
    assert exc_info.value.returncode == 1
    assert "Command not found or execution failed" in exc_info.value.stderr

def test_run_command_dubious_ownership_confirm(mocker):
    mock_run = mocker.patch("subprocess.run")
    mock_run.side_effect = [
        subprocess.CalledProcessError(1, ["git", "status"], stderr="fatal: detected dubious ownership in repository at 'C:/path'"),
        mocker.MagicMock(stdout="trusted success"),  # fix_command call success
        mocker.MagicMock(stdout="final result")       # retry call success
    ]

    mock_danger = mocker.patch("pygitgo.utils.executor.danger")
    mock_warning = mocker.patch("pygitgo.utils.executor.warning")
    mock_info = mocker.patch("pygitgo.utils.executor.info")
    mock_success = mocker.patch("pygitgo.utils.executor.success")
    mock_confirm = mocker.patch("pygitgo.utils.executor.confirm", return_value=True)

    res = run_command(["git", "status"])
    assert res == "final result"
    mock_danger.assert_called_once_with("Git blocked this folder for security reasons (dubious ownership).")
    mock_confirm.assert_called_once()
    mock_success.assert_called_once_with("Directory trusted. Retrying command...")

def test_run_command_dubious_ownership_decline(mocker):
    mock_run = mocker.patch("subprocess.run")
    mock_run.side_effect = subprocess.CalledProcessError(1, ["git", "status"], stderr="fatal: detected dubious ownership in repository at 'C:/path'")

    mock_danger = mocker.patch("pygitgo.utils.executor.danger")
    mock_warning = mocker.patch("pygitgo.utils.executor.warning")
    mock_info = mocker.patch("pygitgo.utils.executor.info")
    mock_confirm = mocker.patch("pygitgo.utils.executor.confirm", return_value=False)

    with pytest.raises(GitCommandError):
        run_command(["git", "status"])
    
    mock_confirm.assert_called_once()
    mock_warning.assert_called_with("Fix declined. Operations in this directory will continue to fail.")
