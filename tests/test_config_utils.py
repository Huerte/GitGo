from pygitgo.utils.config import get_config, set_config, get_default_branch


def test_get_config_fallback(mocker):
    from pygitgo.exceptions import GitCommandError
    fake_run = mocker.patch('pygitgo.utils.config.run_command', side_effect=GitCommandError(['git']))

    fallback_value = "false"

    result = get_config("default-key", fallback_value)
    assert result == fallback_value

def test_get_config_ok(mocker):
    fake_run = mocker.patch('pygitgo.utils.config.run_command', return_value="true")

    fallback_value = "false"

    result = get_config("default-key", fallback_value)
    assert result != fallback_value

def test_set_config_fallback(mocker):
    from pygitgo.exceptions import GitCommandError
    fake_run = mocker.patch('pygitgo.utils.config.run_command', side_effect=GitCommandError(['git']))
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

def test_get_config_strip(mocker):
    fake_run = mocker.patch('pygitgo.utils.config.run_command', return_value="  true  \n")
    result = get_config("default-key", "false")
    assert result == "true"

def test_get_config_error_handling(mocker):
    from pygitgo.exceptions import GitCommandError
    fake_run = mocker.patch('pygitgo.utils.config.run_command', side_effect=GitCommandError(['git']))
    result = get_config("default-key", "fallback")
    assert result == "fallback"



def test_get_default_branch_uses_git_init_default_branch(mocker):
    mocker.patch(
        "pygitgo.utils.config.run_command",
        return_value="develop",
    )
    result = get_default_branch()
    assert result == "develop"


def test_get_default_branch_falls_back_to_gitgo_config(mocker):
    from pygitgo.exceptions import GitCommandError
    mocker.patch(
        "pygitgo.utils.config.run_command",
        side_effect=[GitCommandError(["git"]), "trunk"],
    )
    result = get_default_branch()
    assert result == "trunk"


def test_get_default_branch_hard_fallback_to_main(mocker):
    from pygitgo.exceptions import GitCommandError
    mocker.patch("pygitgo.utils.config.run_command", side_effect=GitCommandError(["git"]))
    result = get_default_branch()
    assert result == "main"


def test_get_default_branch_handles_git_not_found(mocker):
    from pygitgo.exceptions import GitCommandError
    # GitCommandError is raised by run_command when git is not found
    mocker.patch("pygitgo.utils.config.run_command", side_effect=GitCommandError(["git"]))
    result = get_default_branch()
    assert result == "main"
