from pygitgo.utils.bootstrap import check_git_installed, ensure_first_run_setup
from conftest import capture_system_exit_code


def test_check_git_installed_no_exist(mocker):
    mocker.patch("shutil.which", return_value=None)
    fake_error = mocker.patch("pygitgo.utils.bootstrap.error")
    fake_info = mocker.patch("pygitgo.utils.bootstrap.info")

    assert capture_system_exit_code(lambda: check_git_installed()) == 1

    fake_error.assert_called_with("\nGit is not installed or not found on your PATH!")
    fake_info.assert_any_call("Install Git from: https://git-scm.com/downloads")
    fake_info.assert_any_call("After installing, restart your terminal and try again.\n")

def test_check_git_installed_exist(mocker):
    mocker.patch("shutil.which", return_value="ok")
    fake_error = mocker.patch("pygitgo.utils.bootstrap.error")
    fake_info = mocker.patch("pygitgo.utils.bootstrap.info")

    assert capture_system_exit_code(lambda: check_git_installed()) == 0

    fake_error.assert_not_called()
    fake_info.assert_not_called()

def test_ensure_first_run_setup(mocker):
    fake_check = mocker.patch('pygitgo.utils.bootstrap.check_git_installed', return_value=None)
    ensure_first_run_setup()
    fake_check.assert_called_once()
