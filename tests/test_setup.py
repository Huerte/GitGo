from pygitgo.utils.setup import check_git_installed, ensure_first_run_setup
from conftest import capture_system_exit_code


def test_check_git_installed_no_exist(mocker):
    mocker.patch("shutil.which", return_value=None)
    fake_error = mocker.patch("pygitgo.utils.setup.error")
    fake_info = mocker.patch("pygitgo.utils.setup.info")

    assert capture_system_exit_code(lambda: check_git_installed()) == 1

    fake_error.assert_called_with("\nGit is not installed or not found on your PATH!")
    fake_info.assert_any_call("Install Git from: https://git-scm.com/downloads")
    fake_info.assert_any_call("After installing, restart your terminal and try again.\n")

def test_check_git_installed_exist(mocker):
    mocker.patch("shutil.which", return_value="ok")
    fake_error = mocker.patch("pygitgo.utils.setup.error")
    fake_info = mocker.patch("pygitgo.utils.setup.info")

    assert capture_system_exit_code(lambda: check_git_installed()) == None

    fake_error.assert_not_called()
    fake_info.assert_not_called()

def test_ensure_first_run_setup_already_initialized(mocker):
    mocker.patch('pygitgo.utils.setup.check_git_installed', return_value=None)
    fake_get_config = mocker.patch('pygitgo.utils.setup.get_config', return_value="ok")
    fake_github_function = mocker.patch('pygitgo.utils.setup.ensure_github_known_host', return_value=None)
    fake_set_config = mocker.patch('pygitgo.utils.setup.set_config', return_value=True)
    fake_info = mocker.patch("pygitgo.utils.setup.info")

    ensure_first_run_setup()

    fake_info.assert_not_called()
    fake_github_function.assert_not_called()
    fake_set_config.assert_not_called()

    fake_get_config.assert_called_with("initialized", fallback_value="false")

def test_ensure_first_run_setup_not_initialized(mocker):
    mocker.patch('pygitgo.utils.setup.check_git_installed', return_value=None)
    fake_get_config = mocker.patch('pygitgo.utils.setup.get_config', return_value="false")
    fake_github_function = mocker.patch('pygitgo.utils.setup.ensure_github_known_host', return_value=None)
    fake_set_config = mocker.patch('pygitgo.utils.setup.set_config', return_value=True)
    fake_info = mocker.patch("pygitgo.utils.setup.info")

    ensure_first_run_setup()

    fake_info.assert_called_with("\nInitializing GitGo network settings for the first time... please wait.")
    fake_github_function.assert_called_once()
    fake_set_config.assert_called_with("initialized", "true")

    fake_get_config.assert_called_with("initialized", fallback_value="false")

