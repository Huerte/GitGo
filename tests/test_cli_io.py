from pygitgo.utils.cli_io import confirm, danger, warning, error, info, success, banner
from pygitgo.utils.colors import RED, GREEN, YELLOW, BLUE, RESET
import os

def test_confirm_yes(mocker):
    mocker.patch("builtins.input", return_value="y")
    assert confirm("Proceed?") is True

def test_confirm_no(mocker):
    mocker.patch("builtins.input", return_value="n")
    assert confirm("Proceed?") is False

def test_confirm_destructive(mocker):
    mock_input = mocker.patch("builtins.input", return_value="y")
    assert confirm("Proceed?", destructive=True) is True
    # check that DANGER: prefix is included in prompt
    mock_input.assert_called_once_with(f"{RED}DANGER: {RESET}Proceed?")

def test_danger(mocker):
    mock_print = mocker.patch("builtins.print")
    danger("irreversible action")
    mock_print.assert_called_once_with(f"{RED}DANGER: irreversible action{RESET}")

def test_warning(mocker):
    mock_print = mocker.patch("builtins.print")
    warning("recoverable risk")
    mock_print.assert_called_once_with(f"{YELLOW}WARNING: recoverable risk{RESET}")

def test_error(mocker):
    mock_print = mocker.patch("builtins.print")
    error("failed operation")
    mock_print.assert_called_once_with(f"{RED}failed operation{RESET}")

def test_info(mocker):
    mock_print = mocker.patch("builtins.print")
    info("some info")
    mock_print.assert_called_once_with(f"{BLUE}some info{RESET}")

def test_success(mocker):
    mock_print = mocker.patch("builtins.print")
    success("action done")
    mock_print.assert_called_once_with(f"{GREEN}action done{RESET}")

def test_banner(mocker):
    mock_print = mocker.patch("builtins.print")
    mocker.patch("shutil.get_terminal_size", return_value=os.terminal_size((80, 24)))
    
    banner("TITLE", "SUBTITLE")
    
    # Check that print was called to output the banner
    assert mock_print.call_count >= 4
