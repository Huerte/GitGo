from pygitgo.utils.banner import _safe, _format_sync, show_banner
import pytest


def test_safe_success():
    def mock_fn():
        return "success"
    assert _safe(mock_fn, default="default") == "success"

def test_safe_exception():
    def mock_fn():
        raise ValueError("error")
    assert _safe(mock_fn, default="default") == "default"

def test_format_sync_exception(mocker):
    mocker.patch("pygitgo.utils.banner.run_command", side_effect=Exception("error"))
    assert _format_sync() is None

def test_format_sync_invalid_output(mocker):
    mocker.patch("pygitgo.utils.banner.run_command", return_value="only_one_part")
    assert _format_sync() is None
    
    mocker.patch("pygitgo.utils.banner.run_command", return_value="three parts here")
    assert _format_sync() is None

@pytest.mark.parametrize("ahead,behind,expected", [
    (0, 0, "up to date"),
    (2, 0, "2 ahead"),
    (0, 3, "3 behind"),
    (2, 3, "2 ahead, 3 behind (diverged)"),
])
def test_format_sync_valid_cases(mocker, ahead, behind, expected):
    mocker.patch("pygitgo.utils.banner.run_command", return_value=f"{ahead}\t{behind}")
    res = _format_sync()
    assert expected in res

def test_show_banner_clean_status(mocker, capsys):
    mocker.patch("pygitgo.main.get_version", return_value="1.10.1")
    mocker.patch("pygitgo.utils.banner.ensure_inside_git_repository")
    mocker.patch("pygitgo.utils.banner.get_user", return_value=("Huerte", "huerte@example.com"))
    mocker.patch("pygitgo.utils.banner.get_current_branch", return_value="main")
    mocker.patch("pygitgo.utils.banner.check_for_updates", return_value=None)
    
    def mock_run(args, *a, **k):
        cmd_str = " ".join(args) if isinstance(args, list) else str(args)
        if "remote.origin.url" in cmd_str:
            return "https://github.com/Huerte/GitGo.git"
        elif "status" in cmd_str:
            return ""
        elif "rev-list" in cmd_str:
            return "0\t0"
        return ""
    
    mocker.patch("pygitgo.utils.banner.run_command", side_effect=mock_run)
    
    mock_commits = [{"hash": "abcdef0", "message": "Initial commit", "date": "2026-07-17", "author": "Huerte"}]
    mocker.patch("pygitgo.utils.banner.get_recent_commits", return_value=mock_commits)
    
    mock_size = mocker.MagicMock()
    mock_size.columns = 80
    mock_size.lines = 20
    mocker.patch("shutil.get_terminal_size", return_value=mock_size)
    
    show_banner()
    
    captured = capsys.readouterr().out
    assert "GitGo 1.10.1" in captured
    assert "Your Fast Git Companion" in captured
    assert "Identity" in captured
    assert "Huerte <huerte@example.com>" in captured
    assert "Remote" in captured
    assert "https://github.com/Huerte/GitGo.git" in captured
    assert "Branch" in captured
    assert "main" in captured
    assert "Sync" in captured
    assert "up to date" in captured
    assert "Status" in captured
    assert "clean" in captured
    assert "Latest" in captured
    assert "[abcdef0] Initial commit" in captured

def test_show_banner_dirty_status(mocker, capsys):
    mocker.patch("pygitgo.main.get_version", return_value="1.10.1")
    mocker.patch("pygitgo.utils.banner.ensure_inside_git_repository")
    mocker.patch("pygitgo.utils.banner.get_user", return_value=(None, None))
    mocker.patch("pygitgo.utils.banner.get_current_branch", side_effect=Exception("no branch"))
    mocker.patch("pygitgo.utils.banner.check_for_updates", return_value="Update available: 1.10.2")
    
    def mock_run(args, *a, **k):
        cmd_str = " ".join(args) if isinstance(args, list) else str(args)
        if "remote.origin.url" in cmd_str:
            raise Exception("no remote")
        elif "status" in cmd_str:
            return "M  src/main.py\n?? test.py\n"
        elif "rev-list" in cmd_str:
            return "2\t3"
        return ""
    
    mocker.patch("pygitgo.utils.banner.run_command", side_effect=mock_run)
    mocker.patch("pygitgo.utils.banner.get_recent_commits", return_value=[])
    
    mock_size = mocker.MagicMock()
    mock_size.columns = 40
    mock_size.lines = 20
    mocker.patch("shutil.get_terminal_size", return_value=mock_size)
    
    show_banner()
    
    captured = capsys.readouterr().out
    assert "Identity" in captured
    assert "Not set <Not set>" in captured
    assert "Remote" in captured
    assert "not set" in captured
    assert "Branch" in captured
    assert "unknown" in captured
    assert "Sync" in captured
    assert "2 ahead, 3 behind (diverged)" in captured
    assert "Status" in captured
    assert "1 modified, 1 untracked" in captured
    assert "Latest" in captured
    assert "no commits yet" in captured
    assert "Update available: 1.10.2" in captured

def test_show_banner_dirty_only_modified(mocker, capsys):
    mocker.patch("pygitgo.main.get_version", return_value="1.10.1")
    mocker.patch("pygitgo.utils.banner.ensure_inside_git_repository")
    mocker.patch("pygitgo.utils.banner.get_user", return_value=("user", "email"))
    mocker.patch("pygitgo.utils.banner.get_current_branch", return_value="main")
    mocker.patch("pygitgo.utils.banner.check_for_updates", return_value=None)
    
    def mock_run(args, *a, **k):
        cmd_str = " ".join(args) if isinstance(args, list) else str(args)
        if "remote.origin.url" in cmd_str:
            return "https://github.com/Huerte/GitGo.git"
        elif "status" in cmd_str:
            return "M  src/main.py\n"
        elif "rev-list" in cmd_str:
            return "0\t0"
        return ""
    
    mocker.patch("pygitgo.utils.banner.run_command", side_effect=mock_run)
    mocker.patch("pygitgo.utils.banner.get_recent_commits", return_value=[])
    
    show_banner()
    
    captured = capsys.readouterr().out
    assert "1 modified" in captured
    assert "untracked" not in captured

def test_show_banner_dirty_only_untracked(mocker, capsys):
    mocker.patch("pygitgo.main.get_version", return_value="1.10.1")
    mocker.patch("pygitgo.utils.banner.ensure_inside_git_repository")
    mocker.patch("pygitgo.utils.banner.get_user", return_value=("user", "email"))
    mocker.patch("pygitgo.utils.banner.get_current_branch", return_value="main")
    mocker.patch("pygitgo.utils.banner.check_for_updates", return_value=None)
    
    def mock_run(args, *a, **k):
        cmd_str = " ".join(args) if isinstance(args, list) else str(args)
        if "remote.origin.url" in cmd_str:
            return "https://github.com/Huerte/GitGo.git"
        elif "status" in cmd_str:
            return "?? untracked.py\n"
        elif "rev-list" in cmd_str:
            return "0\t0"
        return ""
    
    mocker.patch("pygitgo.utils.banner.run_command", side_effect=mock_run)
    mocker.patch("pygitgo.utils.banner.get_recent_commits", return_value=[])
    
    show_banner()
    
    captured = capsys.readouterr().out
    assert "1 untracked" in captured
    assert "modified" not in captured
