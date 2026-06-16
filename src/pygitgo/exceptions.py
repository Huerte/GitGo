class GitGoError(Exception):
    pass


class GitCommandError(GitGoError):
    def __init__(self, command, stderr="", returncode=1):
        self.command = command
        self.stderr = stderr
        self.returncode = returncode
        cmd_str = ' '.join(command) if isinstance(command, list) else command
        super().__init__(f"Command failed: {cmd_str}\n{stderr}")

