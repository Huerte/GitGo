from unittest.mock import patch, MagicMock
from pygitgo.commands.new import new_operation


@patch("pygitgo.commands.new.init_operation")
@patch("pygitgo.commands.new.repo_operation")
@patch("pygitgo.commands.new.link_core")
@patch("os.chdir")
def test_new_operation_quickstart(mock_chdir, mock_link_core, mock_repo_operation, mock_init_operation, capsys):
    args = MagicMock()
    args.name = "my-project"
    args.lang = "python"
    args.template = None
    args.private = True
    args.description = "my desc"

    mock_repo_operation.return_value = "https://github.com/user/my-project.git"

    new_operation(args)

    mock_init_operation.assert_called_once_with(args)
    mock_chdir.assert_called_once_with("my-project")
    mock_repo_operation.assert_called_once_with(args, silent=True)
    mock_link_core.assert_called_once_with("https://github.com/user/my-project.git", "Initial commit", silent=True, already_initialized=True)

    captured = capsys.readouterr()
    assert "undo link" in captured.out