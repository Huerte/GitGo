from pygitgo.auth.account import get_user, set_user, ensure_user_configure, sanitize_signing_config
from pygitgo.exceptions import GitCommandError



def test_get_user_both_exist(mocker):
    fake_run = mocker.patch("pygitgo.auth.account.run_command", side_effect=["John Doe", "john@example.com"])
    name, email = get_user()
    assert name == "John Doe"
    assert email == "john@example.com"
    assert fake_run.call_count == 2


def test_get_user_none_exist(mocker):
    fake_run = mocker.patch("pygitgo.auth.account.run_command", side_effect=GitCommandError(["git", "config"]))
    name, email = get_user()
    assert name is None
    assert email is None
    assert fake_run.call_count == 2


def test_set_user(mocker):
    fake_run = mocker.patch("pygitgo.auth.account.run_command")
    fake_success = mocker.patch("pygitgo.auth.account.success")

    set_user("Alice", "alice@example.com")

    fake_run.assert_any_call(["git", "config", "--global", "user.name", "Alice"])
    fake_run.assert_any_call(["git", "config", "--global", "user.email", "alice@example.com"])
    fake_success.assert_called_once()


def test_ensure_user_configure_already_exists(mocker):
    mocker.patch("pygitgo.auth.account.get_user", return_value=("John Doe", "john@example.com"))
    fake_set = mocker.patch("pygitgo.auth.account.set_user")

    result = ensure_user_configure()
    assert result is True
    fake_set.assert_not_called()


def test_ensure_user_configure_defaults_exist(mocker):
    mocker.patch("pygitgo.auth.account.get_user", return_value=(None, None))
    fake_set = mocker.patch("pygitgo.auth.account.set_user")
    mocker.patch("pygitgo.auth.account.info")

    result = ensure_user_configure(default_email="git@github.com", default_username="GithubUser")
    assert result is True
    fake_set.assert_called_once_with("GithubUser", "git@github.com")


def test_ensure_user_configure_prompt_success(mocker):
    mocker.patch("pygitgo.auth.account.get_user", return_value=(None, None))
    fake_set = mocker.patch("pygitgo.auth.account.set_user")
    mocker.patch("pygitgo.auth.account.info")
    mocker.patch("pygitgo.auth.account.warning")
    mocker.patch("builtins.input", side_effect=["John Doe", "john@example.com"])

    result = ensure_user_configure()
    assert result is True
    fake_set.assert_called_once_with("John Doe", "john@example.com")


def test_ensure_user_configure_prompt_failure(mocker):
    mocker.patch("pygitgo.auth.account.get_user", return_value=(None, None))
    fake_set = mocker.patch("pygitgo.auth.account.set_user")
    mocker.patch("pygitgo.auth.account.info")
    mocker.patch("pygitgo.auth.account.warning")
    mocker.patch("pygitgo.auth.account.error")
    mocker.patch("builtins.input", side_effect=["", ""])

    result = ensure_user_configure()
    assert result is False
    fake_set.assert_not_called()


def test_sanitize_signing_config_disabled(mocker):
    fake_run = mocker.patch("pygitgo.auth.account.run_command", return_value="false")
    sanitize_signing_config()
    fake_run.assert_called_once_with(["git", "config", "--global", "commit.gpgsign"])


def test_sanitize_signing_config_not_configured(mocker):
    fake_run = mocker.patch("pygitgo.auth.account.run_command", side_effect=GitCommandError(["git", "config"]))
    sanitize_signing_config()
    fake_run.assert_called_once_with(["git", "config", "--global", "commit.gpgsign"])


def test_sanitize_signing_config_ssh_format(mocker):
    fake_run = mocker.patch("pygitgo.auth.account.run_command", side_effect=["true", "ssh"])
    sanitize_signing_config()
    assert fake_run.call_count == 2
    fake_run.assert_any_call(["git", "config", "--global", "commit.gpgsign"])
    fake_run.assert_any_call(["git", "config", "--global", "gpg.format"])


def test_sanitize_signing_config_unset_gpg_program(mocker):
    fake_run = mocker.patch("pygitgo.auth.account.run_command", side_effect=["true", "openpgp", None, None])
    fake_warning = mocker.patch("pygitgo.auth.account.warning")

    sanitize_signing_config()

    assert fake_run.call_count == 4
    fake_run.assert_any_call(["git", "config", "--global", "commit.gpgsign"])
    fake_run.assert_any_call(["git", "config", "--global", "gpg.format"])
    fake_run.assert_any_call(["git", "config", "--global", "--unset", "gpg.program"])
    fake_run.assert_any_call(["git", "config", "--global", "--unset", "commit.gpgsign"])
    assert fake_warning.call_count == 2


def test_sanitize_signing_config_unset_gpg_program_error(mocker):
    fake_run = mocker.patch(
        "pygitgo.auth.account.run_command",
        side_effect=["true", "openpgp", GitCommandError(["git", "config"]), GitCommandError(["git", "config"])]
    )
    fake_warning = mocker.patch("pygitgo.auth.account.warning")

    sanitize_signing_config()

    assert fake_run.call_count == 4
    assert fake_warning.call_count == 2

