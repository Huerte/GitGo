from pygitgo.auth.ssh_utils import is_ssh_url
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