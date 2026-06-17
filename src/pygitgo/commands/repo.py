from pygitgo.utils.config import get_config, set_config
from pygitgo.utils.cli_io import info, warning, banner
from pygitgo.utils.platform import open_url
from pygitgo.exceptions import GitGoError
import subprocess
import urllib
import json
import os

GITHUB_API = "https://api.github.com"

_TOKEN_URL = "https://github.com/settings/tokens/new?scopes=repo&description=GitGo"


def _clear_saved_token():
    try:
        subprocess.run(
            ["git", "config", "--global", "--unset", "gitgo.github-token"],
            capture_output=True
        )
    except Exception:
        pass


def _prompt_for_token():
    info("GitGo needs a GitHub token to create repositories.")
    info("Required scope: repo")
    info("Tip: set 'Expiration' to 'No expiration' for a permanent token (Classic PAT only).")
    open_url(_TOKEN_URL)

    token = input(
        "After creating the token on GitHub,\n"
        "come back here and paste it: "
    ).strip()

    if not token:
        raise GitGoError("Cancelled. No repository was created.")

    set_config("github-token", token, silent=True)
    return token


def _get_github_token():
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    if token:
        return token

    try:
        result = subprocess.run(
            ["gh", "auth", "token"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            token = result.stdout.strip()
            if token:
                return token
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    token = get_config("github-token", "").strip()
    if token:
        return token

    return _prompt_for_token()


def create_github_repo(name, private=False, description="", token=None, retry_count=0):
    
    if not token:
        token = _get_github_token()
    
    payload = json.dumps({
        "name": name,
        "private": private,
        "description": description,
    }).encode("utf-8")

    req = urllib.request.Request(
        f"{GITHUB_API}/user/repos",
        data=payload,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "GitGo-CLI"
        }, method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        if e.code == 422:
            raise GitGoError(f"Repository '{name}' already exists on GitHub.")
        elif e.code == 401:
            if retry_count >= 3:
                raise GitGoError("GitHub authentication failed. Please check your GitHub token.")
            warning("Token is invalid or expired. Clearing saved token...")
            _clear_saved_token()
            warning("Please create a new token. Opening GitHub now...")
            new_token = _prompt_for_token()
            return create_github_repo(name, private=private, description=description, token=new_token, retry_count=retry_count + 1)

        body = e.read().decode("utf-8", errors="replace")
        try:
            msg = json.loads(body).get("message", body)
        except Exception:
            msg = body
        raise GitGoError(f"GitHub API error {e.code}: {msg}")
    except urllib.error.URLError as e:
        raise GitGoError(f"Network error creating repo: {e.reason}")


def repo_operation(args, silent=False):
    if args.name:
        repo_name = args.name
    else:
        repo_name = os.path.basename(os.path.abspath("."))
        info(f"No name given: using current directory name: '{repo_name}'")

    token = _get_github_token()

    from yaspin import yaspin
    import sys
    kwargs = {"text": f"Creating GitHub repository '{repo_name}'..."}
    if sys.stdout.isatty():
        kwargs["color"] = "cyan"
    spinner = yaspin(**kwargs)
    spinner.start()

    try:
        repo_ = create_github_repo(
            name=repo_name,
            private=args.private,
            description=args.description or "",
            token=token
        )
        repo_url = repo_.get("clone_url")
        spinner.text = f"Successfully created remote repository: {repo_url}"
        spinner.ok("✔")
    except Exception as e:
        spinner.text = str(e)
        spinner.fail("✖")
        raise e

    if not silent:
        banner("REMOTE TARGET ESTABLISHED. REPOSITORY READY.", "GITHUB TARGET CREATION CONFIRMED.")
        info(f"\nTo connect and push your local code, run:\n  gitgo link {repo_url}")
    return repo_url


def parse_repo_fullname(url):
    s = url.strip()
    if s.endswith(".git"):
        s = s[:-4]
    if "github.com/" in s:
        parts = s.split("github.com/")
        if len(parts) > 1:
            return parts[1]
    elif "github.com:" in s:
        parts = s.split("github.com:")
        if len(parts) > 1:
            return parts[1]
    return None


def delete_github_repo(full_name, token=None):
    if not token:
        token = _get_github_token()
    req = urllib.request.Request(
        f"{GITHUB_API}/repos/{full_name}",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "GitGo-CLI"
        }, method="DELETE",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return True
    except Exception as e:
        raise GitGoError(f"Failed to delete repository from GitHub: {str(e)}")


