from pygitgo.utils.colors import _supports_color
import pygitgo.utils.colors
import importlib
import pytest
import sys
import os

@pytest.fixture(autouse=True)
def restore_colors_after_tests():
    yield
    importlib.reload(pygitgo.utils.colors)

def test_supports_color_no_isatty(mocker):
    class DummyStdout:
        pass
    mocker.patch("sys.stdout", DummyStdout())
    assert _supports_color() is False

def test_supports_color_isatty_false(mocker):
    mock_stdout = mocker.MagicMock()
    mock_stdout.isatty.return_value = False
    mocker.patch("sys.stdout", mock_stdout)
    assert _supports_color() is False

def test_supports_color_term_dumb(mocker):
    mock_stdout = mocker.MagicMock()
    mock_stdout.isatty.return_value = True
    mocker.patch("sys.stdout", mock_stdout)
    mocker.patch.dict(os.environ, {"TERM": "dumb"})
    assert _supports_color() is False

def test_supports_color_no_color_env(mocker):
    mock_stdout = mocker.MagicMock()
    mock_stdout.isatty.return_value = True
    mocker.patch("sys.stdout", mock_stdout)
    mocker.patch.dict(os.environ, {"NO_COLOR": "1"})
    assert _supports_color() is False

def test_supports_color_non_windows_success(mocker):
    mock_stdout = mocker.MagicMock()
    mock_stdout.isatty.return_value = True
    mocker.patch("sys.stdout", mock_stdout)
    mocker.patch("sys.platform", "linux")
    mocker.patch.dict(os.environ, {}, clear=True)
    assert _supports_color() is True

def test_supports_color_win32_ctypes_exception(mocker):
    mock_stdout = mocker.MagicMock()
    mock_stdout.isatty.return_value = True
    mocker.patch("sys.stdout", mock_stdout)
    mocker.patch("sys.platform", "win32")
    mocker.patch.dict(os.environ, {}, clear=True)
    mocker.patch.dict(sys.modules, {"ctypes": None})
    assert _supports_color() is False

def test_supports_color_win32_invalid_handle(mocker):
    mock_stdout = mocker.MagicMock()
    mock_stdout.isatty.return_value = True
    mocker.patch("sys.stdout", mock_stdout)
    mocker.patch("sys.platform", "win32")
    mocker.patch.dict(os.environ, {}, clear=True)
    
    mock_ctypes = mocker.MagicMock()
    mock_ctypes.windll.kernel32.GetStdHandle.return_value = -1
    mocker.patch.dict(sys.modules, {"ctypes": mock_ctypes})
    assert _supports_color() is False
    
    mock_ctypes.windll.kernel32.GetStdHandle.return_value = None
    assert _supports_color() is False

def test_supports_color_win32_get_console_mode_fail(mocker):
    mock_stdout = mocker.MagicMock()
    mock_stdout.isatty.return_value = True
    mocker.patch("sys.stdout", mock_stdout)
    mocker.patch("sys.platform", "win32")
    mocker.patch.dict(os.environ, {}, clear=True)
    
    mock_ctypes = mocker.MagicMock()
    mock_ctypes.windll.kernel32.GetStdHandle.return_value = 123
    mock_ctypes.windll.kernel32.GetConsoleMode.return_value = False
    mocker.patch.dict(sys.modules, {"ctypes": mock_ctypes})
    assert _supports_color() is False

def test_supports_color_win32_set_console_mode_fail(mocker):
    mock_stdout = mocker.MagicMock()
    mock_stdout.isatty.return_value = True
    mocker.patch("sys.stdout", mock_stdout)
    mocker.patch("sys.platform", "win32")
    mocker.patch.dict(os.environ, {}, clear=True)
    
    mock_ctypes = mocker.MagicMock()
    mock_ctypes.windll.kernel32.GetStdHandle.return_value = 123
    mock_ctypes.windll.kernel32.GetConsoleMode.return_value = True
    mock_ctypes.windll.kernel32.SetConsoleMode.return_value = False
    mocker.patch.dict(sys.modules, {"ctypes": mock_ctypes})
    assert _supports_color() is False

def test_supports_color_win32_success(mocker):
    mock_stdout = mocker.MagicMock()
    mock_stdout.isatty.return_value = True
    mocker.patch("sys.stdout", mock_stdout)
    mocker.patch("sys.platform", "win32")
    mocker.patch.dict(os.environ, {}, clear=True)
    
    mock_ctypes = mocker.MagicMock()
    mock_ctypes.windll.kernel32.GetStdHandle.return_value = 123
    mock_ctypes.windll.kernel32.GetConsoleMode.return_value = True
    mock_ctypes.windll.kernel32.SetConsoleMode.return_value = True
    mocker.patch.dict(sys.modules, {"ctypes": mock_ctypes})
    assert _supports_color() is True

def test_color_constants_when_color_enabled(mocker):
    mock_stdout = mocker.MagicMock()
    mock_stdout.isatty.return_value = True
    mocker.patch("sys.stdout", mock_stdout)
    mocker.patch("sys.platform", "linux")
    mocker.patch.dict(os.environ, {}, clear=True)
    
    importlib.reload(pygitgo.utils.colors)
    assert pygitgo.utils.colors.RED == "\033[31m"
    assert pygitgo.utils.colors.GREEN == "\033[32m"
    assert pygitgo.utils.colors.YELLOW == "\033[33m"
    assert pygitgo.utils.colors.BLUE == "\033[34m"
    assert pygitgo.utils.colors.CYAN == "\033[36m"
    assert pygitgo.utils.colors.RESET == "\033[0m"

def test_color_constants_when_color_disabled(mocker):
    mock_stdout = mocker.MagicMock()
    mock_stdout.isatty.return_value = False
    mocker.patch("sys.stdout", mock_stdout)
    mocker.patch("sys.platform", "linux")
    mocker.patch.dict(os.environ, {}, clear=True)
    
    importlib.reload(pygitgo.utils.colors)
    assert pygitgo.utils.colors.RED == ""
    assert pygitgo.utils.colors.GREEN == ""
    assert pygitgo.utils.colors.YELLOW == ""
    assert pygitgo.utils.colors.BLUE == ""
    assert pygitgo.utils.colors.CYAN == ""
    assert pygitgo.utils.colors.RESET == ""
