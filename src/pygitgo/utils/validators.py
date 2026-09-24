import re


def validate_repo_url(url):
    # Validate that the URL looks like a valid Git repository URL
    patterns = [
        r'^https?://[\w.-]+(?:[:]\d+)?/.+(?:\.git)?/?$',  # HTTPS
        r'^git@[\w.-]+:.+(?:\.git)?$',          # SSH
    ]
    return any(re.match(p, url.strip()) for p in patterns)
