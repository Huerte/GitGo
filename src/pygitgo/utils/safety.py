"""Checks that stop people from accidentally committing secrets."""
from fnmatch import fnmatch
import posixpath

# Matched against the lowercase file name only (not the folder).
SENSITIVE_PATTERNS = (
    ".env", ".env.*",
    "*.pem", "*.key", "*.p12", "*.pfx", "*.ppk", "*.jks", "*.keystore",
    "id_rsa", "id_dsa", "id_ecdsa", "id_ed25519",
    "credentials.json", "service-account*.json", "secrets.json", "secrets.yml", "secrets.yaml",
    ".netrc", ".git-credentials", ".htpasswd",
)

# '.env.example' and friends are meant to be committed.
SAFE_SUFFIXES = (".example", ".sample", ".template", ".dist", ".defaults")


def is_sensitive(path):
    name = posixpath.basename(path.replace("\\", "/")).lower()
    if name.endswith(SAFE_SUFFIXES):
        return False
    return any(fnmatch(name, pattern) for pattern in SENSITIVE_PATTERNS)


def find_sensitive(paths):
    return [p for p in paths if is_sensitive(p)]
