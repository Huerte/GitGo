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