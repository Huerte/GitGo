from pygitgo.main import link_operation


def test_link_existing_repo_skips_staging(mocker):
    mocker.patch('pygitgo.main.validate_repo_url', return_value=True)
    mocker.patch('pygitgo.main.git_init', return_value=False)   
    fake_commit = mocker.patch('pygitgo.main.git_commit')
    mocker.patch('pygitgo.main.add_remote_origin')
    mocker.patch('pygitgo.main.confirm_remote_link', return_value=True)
    from argparse import Namespace
    link_operation(Namespace(url="git@github.com:user/repo.git", message="init"))
    fake_commit.assert_not_called()   
    

def test_link_new_repo_runs_commit(mocker):
    mocker.patch('pygitgo.main.validate_repo_url', return_value=True)
    mocker.patch('pygitgo.main.git_init', return_value=True)    
    fake_commit = mocker.patch('pygitgo.main.git_commit', return_value=True)
    mocker.patch('pygitgo.main.add_remote_origin')
    mocker.patch('pygitgo.main.confirm_remote_link', return_value=True)
    mocker.patch('pygitgo.main.get_current_branch', return_value='main')
    mocker.patch('pygitgo.main.get_config', return_value='main')
    mocker.patch('pygitgo.main.run_command', return_value='')
    mocker.patch('builtins.input', return_value='n')
    from argparse import Namespace
    link_operation(Namespace(url="git@github.com:user/repo.git", message="init"))
    fake_commit.assert_called_once()