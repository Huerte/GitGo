from pygitgo.auth.ssh_utils import is_ssh_url
from pygitgo.main import validate_repo_url
import pytest

@pytest.mark.parametrize("url", [
    "git@github.com:Huerte/GitGo.git",
    "git@gitlab.com:Company/App.git"
])

def test_is_ssh_url_valid(url):
    result = is_ssh_url(url)
    assert result == True


@pytest.mark.parametrize("url", [
    "https://github.com/Huerte/GitGo"
    "hello-world",
    ""
])

def test_is_ssh_url_invalid(url):
    result = is_ssh_url(url)
    assert result == False

@pytest.mark.parametrize("url", [
    "https://github.com/Huerte/GitGo.git",
    "git@github.com:Huerte/GitGo.git",
])

def test_validate_repo_url_valid_url(url):
    result = validate_repo_url(url)
    assert result == True

@pytest.mark.parametrize('bad_url', [
    "not-a-valid-url",
    "https://google.com",
    "",
])

def test_validate_repo_url_invalid_url(bad_url):
    result = validate_repo_url(bad_url)
    assert result == False