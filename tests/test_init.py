import pytest
import urllib.error
import zipfile
import io
import os
from unittest.mock import patch, MagicMock, mock_open
from pygitgo.exceptions import GitGoError
from pygitgo.commands.init import (
    _resolve_lang,
    _scaffold_language,
    init_operation,
    _fetch_available_templates,
    _fetch_gitignore,
    _download_and_extract_template,
    _parse_template_slug
)

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
    with pytest.raises(GitGoError) as ex:
        _resolve_lang("notalanguage", SAMPLE_AVAILABLE)
    assert "No .gitignore template found" in str(ex.value)

def test_resolve_lang_suggestions():
    available = {"python": "Python", "pytorch": "PyTorch", "java": "Java"}
    with pytest.raises(GitGoError) as ex:
        _resolve_lang("pyt", available)
    assert "pytorch" in str(ex.value)

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

    init_operation(args, standalone=True)

    mock_scaffold.assert_called_once_with("python", args.name, args.name)
    mock_git_init.assert_called_once()

def test_parse_template_slug():
    assert _parse_template_slug("owner/repo") == "owner/repo"
    assert _parse_template_slug("https://github.com/owner/repo") == "owner/repo"
    assert _parse_template_slug("https://github.com/owner/repo.git") == "owner/repo"
    assert _parse_template_slug("git@github.com:owner/repo.git") == "owner/repo"
    
    with pytest.raises(GitGoError):
        _parse_template_slug("invalid_format")

@patch("urllib.request.urlopen")
def test_fetch_available_templates_success(mock_urlopen):
    mock_resp = MagicMock()
    mock_resp.read.return_value = b'[{"name": "Python.gitignore", "type": "file"}, {"name": "Go.gitignore", "type": "file"}]'
    mock_urlopen.return_value.__enter__.return_value = mock_resp

    templates = _fetch_available_templates()
    assert templates == {"python": "Python", "go": "Go"}

@patch("urllib.request.urlopen")
def test_fetch_available_templates_http_error(mock_urlopen):
    mock_urlopen.side_effect = urllib.error.HTTPError("url", 500, "Internal Server Error", {}, None)
    with pytest.raises(GitGoError) as ex:
        _fetch_available_templates()
    assert "HTTP 500" in str(ex.value)

@patch("urllib.request.urlopen")
def test_fetch_available_templates_generic_error(mock_urlopen):
    mock_urlopen.side_effect = Exception("network fail")
    with pytest.raises(GitGoError) as ex:
        _fetch_available_templates()
    assert "network fail" in str(ex.value)

@patch("urllib.request.urlopen")
def test_fetch_gitignore_success(mock_urlopen):
    mock_resp = MagicMock()
    mock_resp.read.return_value = b"gitignore data"
    mock_urlopen.return_value.__enter__.return_value = mock_resp

    content = _fetch_gitignore("Python")
    assert content == "gitignore data"

@patch("urllib.request.urlopen")
def test_fetch_gitignore_not_found(mock_urlopen):
    mock_urlopen.side_effect = urllib.error.HTTPError("url", 404, "Not Found", {}, None)
    with pytest.raises(GitGoError) as ex:
        _fetch_gitignore("Python")
    assert "not found in GitHub gitignore templates" in str(ex.value)

@patch("urllib.request.urlopen")
def test_fetch_gitignore_other_http_error(mock_urlopen):
    mock_urlopen.side_effect = urllib.error.HTTPError("url", 500, "Error", {}, None)
    with pytest.raises(GitGoError) as ex:
        _fetch_gitignore("Python")
    assert "HTTP 500" in str(ex.value)

@patch("urllib.request.urlopen")
def test_fetch_gitignore_generic_error(mock_urlopen):
    mock_urlopen.side_effect = Exception("network error")
    with pytest.raises(GitGoError) as ex:
        _fetch_gitignore("Python")
    assert "Network error fetching gitignore" in str(ex.value)

@patch("urllib.request.urlopen")
def test_download_and_extract_template_http_404(mock_urlopen, mocker):
    mocker.patch("sys.stdout.isatty", return_value=True)
    mock_urlopen.side_effect = urllib.error.HTTPError("url", 404, "Not Found", {}, None)
    with pytest.raises(GitGoError) as ex:
        _download_and_extract_template("owner/repo", "dir")
    assert "not found on GitHub" in str(ex.value)

@patch("urllib.request.urlopen")
def test_download_and_extract_template_http_other(mock_urlopen):
    mock_urlopen.side_effect = urllib.error.HTTPError("url", 500, "Error", {}, None)
    with pytest.raises(GitGoError) as ex:
        _download_and_extract_template("owner/repo", "dir")
    assert "HTTP 500" in str(ex.value)

@patch("urllib.request.urlopen")
def test_download_and_extract_template_generic_error(mock_urlopen):
    mock_urlopen.side_effect = Exception("connection failed")
    with pytest.raises(GitGoError) as ex:
        _download_and_extract_template("owner/repo", "dir")
    assert "connection failed" in str(ex.value)

@patch("urllib.request.urlopen")
def test_download_and_extract_template_zip_error(mock_urlopen):
    mock_resp = MagicMock()
    mock_resp.read.return_value = b"invalid zip data"
    mock_urlopen.return_value.__enter__.return_value = mock_resp
    with pytest.raises(GitGoError) as ex:
        _download_and_extract_template("owner/repo", "dir")
    assert "Failed to extract template" in str(ex.value)

@patch("urllib.request.urlopen")
def test_download_and_extract_template_empty_zip(mock_urlopen):
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zf:
        pass
    mock_resp = MagicMock()
    mock_resp.read.return_value = zip_buffer.getvalue()
    mock_urlopen.return_value.__enter__.return_value = mock_resp
    with pytest.raises(GitGoError) as ex:
        _download_and_extract_template("owner/repo", "dir")
    assert "Downloaded ZIP archive is empty" in str(ex.value)

@patch("urllib.request.urlopen")
def test_download_and_extract_template_success(mock_urlopen, tmp_path):
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zf:
        zf.writestr("root-dir/", "")
        zf.writestr("root-dir/README.md", "hello template")
        zf.writestr("root-dir/sub/", "")
        zf.writestr("root-dir/sub/config.json", "{}")
    mock_resp = MagicMock()
    mock_resp.read.return_value = zip_buffer.getvalue()
    mock_urlopen.return_value.__enter__.return_value = mock_resp

    target = tmp_path / "target"
    _download_and_extract_template("owner/repo", str(target))
    assert (target / "README.md").read_text() == "hello template"
    assert (target / "sub" / "config.json").read_text() == "{}"

@patch("pygitgo.commands.init._fetch_gitignore")
@patch("pygitgo.commands.init._fetch_available_templates")
def test_scaffold_language_all(mock_available, mock_gitignore, tmp_path):
    mock_available.return_value = {
        "node": "Node",
        "rust": "Rust",
        "dart": "Dart",
        "flutter": "Flutter",
        "go": "Go",
        "dotnet": "Dotnet"
    }
    mock_gitignore.return_value = "gitignore"

    os.makedirs(tmp_path / "node", exist_ok=True)
    _scaffold_language("node", str(tmp_path / "node"), "node-app")
    assert (tmp_path / "node" / "package.json").exists()

    os.makedirs(tmp_path / "rust", exist_ok=True)
    _scaffold_language("rust", str(tmp_path / "rust"), "rust-app")
    assert (tmp_path / "rust" / "Cargo.toml").exists()
    assert (tmp_path / "rust" / "src" / "main.rs").exists()

    os.makedirs(tmp_path / "dart", exist_ok=True)
    _scaffold_language("dart", str(tmp_path / "dart"), "dart-app")
    assert (tmp_path / "dart" / "pubspec.yaml").exists()

    os.makedirs(tmp_path / "flutter", exist_ok=True)
    _scaffold_language("flutter", str(tmp_path / "flutter"), "flutter-app")
    assert (tmp_path / "flutter" / "pubspec.yaml").exists()

    os.makedirs(tmp_path / "go", exist_ok=True)
    _scaffold_language("go", str(tmp_path / "go"), "go-app")
    assert (tmp_path / "go" / "go.mod").exists()
    assert (tmp_path / "go" / "main.go").exists()

    os.makedirs(tmp_path / "dotnet", exist_ok=True)
    _scaffold_language("dotnet", str(tmp_path / "dotnet"), "dotnet-app")
    assert (tmp_path / "dotnet" / "dotnet-app.csproj").exists()
    assert (tmp_path / "dotnet" / "Program.cs").exists()

def test_init_operation_folder_not_empty(tmp_path):
    args = MagicMock()
    args.name = str(tmp_path / "non-empty")
    os.makedirs(args.name)
    with open(os.path.join(args.name, "file.txt"), "w") as f:
        f.write("data")

    with pytest.raises(GitGoError) as ex:
        init_operation(args)
    assert "already exists and is not empty" in str(ex.value)

@patch("pygitgo.commands.init.git_init")
@patch("pygitgo.commands.init._scaffold_language")
def test_init_operation_error_cleanup(mock_scaffold, mock_git_init, tmp_path):
    args = MagicMock()
    args.name = str(tmp_path / "target-folder")
    args.template = None
    args.lang = "python"
    mock_git_init.side_effect = Exception("init failed")

    with pytest.raises(Exception):
        init_operation(args)
    assert not os.path.exists(args.name)