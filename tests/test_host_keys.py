from pygitgo.auth.host_keys import (
    GITHUB_HOST_KEYS, GITHUB_FINGERPRINTS, fingerprint, known_hosts_lines,
)

# Copied by hand from docs.github.com/.../githubs-ssh-key-fingerprints
PUBLISHED = {
    "ssh-ed25519": "SHA256:+DiY3wvvV6TuJJhbpZisF/zLDA0zPMSvHdkr4UvCOqU",
    "ecdsa-sha2-nistp256": "SHA256:p2QAMXNIC1TJYWeIOttrVc98/R1BUFWu3/LiyKgUfQM",
    "ssh-rsa": "SHA256:uNiVztksCsDhcc0u9e8BujQXVUpKZIDTMczCvj3tD2s",
}


def test_embedded_keys_hash_to_the_published_fingerprints():
    assert {t for t, _ in GITHUB_HOST_KEYS} == set(PUBLISHED)
    for key_type, body in GITHUB_HOST_KEYS:
        assert fingerprint(body) == PUBLISHED[key_type]


def test_fingerprint_table_matches_published():
    assert GITHUB_FINGERPRINTS == PUBLISHED


def test_known_hosts_lines_format():
    lines = known_hosts_lines("github.com")
    assert len(lines) == 3
    assert all(line.startswith("github.com ssh-") or line.startswith("github.com ecdsa-") for line in lines)
