import base64
import hashlib
import hmac

GITHUB_HOST_KEYS = (
    ("ssh-ed25519",
     "AAAAC3NzaC1lZDI1NTE5AAAAIOMqqnkVzrm0SdG6UOoqKLsabgH5C9okWi0dh2l9GKJl"),
    ("ecdsa-sha2-nistp256",
     "AAAAE2VjZHNhLXNoYTItbmlzdHAyNTYAAAAIbmlzdHAyNTYAAABBBEmKSENjQEezOmxkZMy7opKgwFB9nkt5YRrYMjNuG5N87uRgg6CLrbo5wAdT/y6v0mKV0U2w0WZ2YB/++Tpockg="),
    ("ssh-rsa",
     "AAAAB3NzaC1yc2EAAAADAQABAAABgQCj7ndNxQowgcQnjshcLrqPEiiphnt+VTTvDP6mHBL9j1aNUkY4Ue1gvwnGLVlOhGeYrnZaMgRK6+PKCUXaDbC7qtbW8gIkhL7aGCsOr/C56SJMy/BCZfxd1nWzAOxSDPgVsmerOBYfNqltV9/hWCqBywINIR+5dIg6JTJ72pcEpEjcYgXkE2YEFXV1JHnsKgbLWNlhScqb2UmyRkQyytRLtL+38TGxkxCflmO+5Z8CSSNY7GidjMIZ7Q4zMjA2n1nGrlTDkzwDCsw+wqFPGQA179cnfGWOWRVruj16z6XyvxvjJwbz0wQZ75XK5tKSb7FNyeIEs4TT4jk+S4dhPeAUC5y+bDYirYgM4GC7uEnztnZyaVWQ7B381AK4Qdrwt51ZqExKbQpTUNn+EjqoTwvqNj4kqx5QUCI0ThS/YkOxJCXmPUWZbhjpCg56i+2aB6CmK2JGhn57K5mj0MNdBXA4/WnwH6XoPWJzK5Nyu2zB3nAZp+S5hpQs+p1vN1/wsjk="),
)

GITHUB_FINGERPRINTS = {
    "ssh-ed25519": "SHA256:+DiY3wvvV6TuJJhbpZisF/zLDA0zPMSvHdkr4UvCOqU",
    "ecdsa-sha2-nistp256": "SHA256:p2QAMXNIC1TJYWeIOttrVc98/R1BUFWu3/LiyKgUfQM",
    "ssh-rsa": "SHA256:uNiVztksCsDhcc0u9e8BujQXVUpKZIDTMczCvj3tD2s",
}

PINNED_HOSTS = ("github.com",)


def fingerprint(key_b64: str) -> str:
    """OpenSSH-style SHA256 fingerprint of a base64 public key body."""
    digest = hashlib.sha256(base64.b64decode(key_b64)).digest()
    return "SHA256:" + base64.b64encode(digest).decode().rstrip("=")


def known_hosts_lines(host: str = "github.com"):
    return [f"{host} {key_type} {body}" for key_type, body in GITHUB_HOST_KEYS]


def _hashed_entry_matches(field: str, host: str) -> bool:
    # OpenSSH hashed form: |1|<base64 salt>|<base64 HMAC-SHA1(salt, host)>
    try:
        _, version, salt_b64, hash_b64 = field.split("|")
        if version != "1":
            return False
        digest = hmac.new(base64.b64decode(salt_b64), host.encode(), hashlib.sha1).digest()
        return hmac.compare_digest(digest, base64.b64decode(hash_b64))
    except Exception:
        return False


def host_key_types_present(text: str, host: str) -> set:
    """Key types already recorded for `host` in known_hosts text (plain or hashed entries)."""
    found = set()
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if parts[0].startswith("@"):  # @cert-authority / @revoked markers
            parts = parts[1:]
        if len(parts) < 3:
            continue
        hosts_field, key_type = parts[0], parts[1]
        if hosts_field.startswith("|1|"):
            matched = _hashed_entry_matches(hosts_field, host)
        else:
            matched = host in hosts_field.split(",") or f"[{host}]:22" in hosts_field.split(",")
        if matched:
            found.add(key_type)
    return found
