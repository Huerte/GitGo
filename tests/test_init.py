from unittest.mock import patch, MagicMock
from pygitgo.exceptions import GitGoError
from pygitgo.commands.init import (
    _resolve_lang,
    _scaffold_language,
    init_operation,
)
import pytest
import os


SAMPLE_AVAILABLE = {
    "python": "Python",
    "go": "Go",
    "rust": "Rust",
    "ruby": "Ruby",
    "c++": "C++",
    "node": "Node",
    "dotnet": "Dotnet",
    "visualstudio": "VisualStudio",
}


def test_resolve_lang():
    assert _resolve_lang("py", SAMPLE_AVAILABLE) == "Python"
    assert _resolve_lang("python", SAMPLE_AVAILABLE) == "Python"
    assert _resolve_lang("golang", SAMPLE_AVAILABLE) == "Go"
    assert _resolve_lang("rust", SAMPLE_AVAILABLE) == "Rust"
    assert _resolve_lang("ruby", SAMPLE_AVAILABLE) == "Ruby"


def test_resolve_lang_csharp_aliases():
    assert _resolve_lang("cs", SAMPLE_AVAILABLE) == "VisualStudio"
    assert _resolve_lang("csharp", SAMPLE_AVAILABLE) == "VisualStudio"
    assert _resolve_lang("dotnet", SAMPLE_AVAILABLE) == "Dotnet"
    assert _resolve_lang(".net", SAMPLE_AVAILABLE) == "Dotnet"


def test_resolve_lang_unknown_raises():
    with pytest.raises(GitGoError):
        _resolve_lang("notalanguage", SAMPLE_AVAILABLE)


@patch("pygitgo.commands.init._fetch_gitignore")
@patch("pygitgo.commands.init._fetch_available_templates")
def test_scaffold_language_python(mock_available, mock_gitignore, tmp_path):
    mock_available.return_value = {"python": "Python"}
    mock_gitignore.return_value = "mock gitignore content"

    _scaffold_language("python", str(tmp_path), "test-project")

    assert (tmp_path / "README.md").exists()
    assert (tmp_path / ".gitignore").exists()
    assert (tmp_path / "pyproject.toml").exists()
    assert (tmp_path / ".python-version").exists()
    mock_gitignore.assert_called_once_with("Python")


@patch("pygitgo.commands.init._fetch_gitignore")
@patch("pygitgo.commands.init._fetch_available_templates")
def test_scaffold_language_csharp(mock_available, mock_gitignore, tmp_path):
    mock_available.return_value = {"visualstudio": "VisualStudio"}
    mock_gitignore.return_value = "mock gitignore content"

    _scaffold_language("cs", str(tmp_path), "test-project")

    assert (tmp_path / "README.md").exists()
    assert (tmp_path / ".gitignore").exists()
    assert (tmp_path / "test-project.csproj").exists()
    assert (tmp_path / "Program.cs").exists()
    mock_gitignore.assert_called_once_with("VisualStudio")


@patch("pygitgo.commands.init._download_and_extract_template")
@patch("pygitgo.commands.init.git_init")
def test_init_operation_template(mock_git_init, mock_download, tmp_path):
    args = MagicMock()
    args.name = str(tmp_path / "new-project")
    args.template = "owner/repo"
    args.lang = None

    init_operation(args)

    mock_download.assert_called_once_with("owner/repo", args.name)
    mock_git_init.assert_called_once()


@patch("pygitgo.commands.init._scaffold_language")
@patch("pygitgo.commands.init.git_init")
def test_init_operation_lang(mock_git_init, mock_scaffold, tmp_path):
    args = MagicMock()
    args.name = str(tmp_path / "new-project")
    args.template = None
    args.lang = "python"

    init_operation(args)

    mock_scaffold.assert_called_once_with("python", args.name, args.name)
    mock_git_init.assert_called_once()