from pathlib import Path
import sys


src_dir = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_dir))


from pygitgo.exceptions import GitGoError

def capture_system_exit_code(function):
    try:
        function()
        return 0
    except SystemExit as e:
        return e.code
    except GitGoError:
        return 1