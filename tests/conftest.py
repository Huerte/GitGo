import sys
from pathlib import Path

src_dir = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_dir))

import pytest
from pygitgo.exceptions import GitGoError


def capture_system_exit_code(function):
    try:
        function()
        return 0
    except SystemExit as e:
        return e.code
    except GitGoError:
        return 1


@pytest.fixture(autouse=True)
def _clear_ssh_cache():
    """Reset the SSH response cache before every test."""
    from pygitgo.auth.ssh_utils import clear_ssh_cache
    clear_ssh_cache()
    yield
    clear_ssh_cache()

@pytest.fixture(autouse=True)
def _restore_cwd():
    """Ensure the working directory is restored after every test."""
    import os
    orig_cwd = os.getcwd()
    yield
    os.chdir(orig_cwd)

@pytest.fixture(autouse=True)
def _isolated_template_cache(tmp_path, monkeypatch):
    """Keep tests from reading or writing the real ~/.gitgo gitignore template cache."""
    monkeypatch.setattr(
        "pygitgo.commands.init._template_cache_file",
        lambda: str(tmp_path / "gitignore_templates.json"),
        raising=False,
    )
