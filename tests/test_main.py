import pytest
from pygitgo.main import validate_repo_url

@pytest.mark.parametrize("url", [
    "https://github.com/Huerte/GitGo.git",
    "https://github.com/Huerte/GitGo",
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