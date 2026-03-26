from pathlib import Path
import sys


src_dir = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_dir))


def capture_system_exit_code(function):
    try:
        function()
        return None
    except SystemExit as e:
        return e.code