import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request

from pygitgo.exceptions import GitGoError

DEFAULT_CLIENT_ID = "Ov23liG3Gn4Z7mqvGQHo"

SCOPES = "admin:public_key write:ssh_signing_key read:user user:email"
_CODE_URL = "https://github.com/login/device/code"
_TOKEN_URL = "https://github.com/login/oauth/access_token"
_API = "https://api.github.com"
_GRANT = "urn:ietf:params:oauth:grant-type:device_code"


class DeviceFlowError(GitGoError):
    pass


def client_id() -> str:
    return os.environ.get("GITGO_GITHUB_CLIENT_ID", "").strip() or DEFAULT_CLIENT_ID


def is_available() -> bool:
    return bool(client_id())


def _request(url, data=None, token=None, method=None):
    headers = {"Accept": "application/json", "User-Agent": "GitGo-CLI"}
    body = None
    if data is not None:
        if url.startswith(_API):
            body = json.dumps(data).encode()
            headers["Content-Type"] = "application/json"
        else:
            body = urllib.parse.urlencode(data).encode()
    if token:
        headers["Authorization"] = f"Bearer {token}"
        headers["X-GitHub-Api-Version"] = "2022-11-28"
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace") if hasattr(e, "read") and e.fp else ""
        try:
            detail = json.loads(raw)
        except ValueError:
            detail = {"message": raw}
        detail["_status"] = e.code
        return detail
    except urllib.error.URLError as e:
        raise DeviceFlowError(f"Could not reach GitHub: {e.reason}")


def start():
    resp = _request(_CODE_URL, {"client_id": client_id(), "scope": SCOPES})
    if "device_code" not in resp:
        raise DeviceFlowError(
            "GitHub did not start the login: " + str(resp.get("error_description") or resp.get("message") or resp)
        )
    return resp


def wait_for_token(device, sleep=time.sleep, now=time.monotonic):
    interval = int(device.get("interval", 5))
    deadline = now() + int(device.get("expires_in", 900))
    while now() < deadline:
        sleep(interval)
        resp = _request(_TOKEN_URL, {
            "client_id": client_id(),
            "device_code": device["device_code"],
            "grant_type": _GRANT,
        })
        if resp.get("access_token"):
            return resp["access_token"]
        err = resp.get("error")
        if err == "authorization_pending":
            continue
        if err == "slow_down":
            interval = int(resp.get("interval", interval + 5))
            continue
        if err == "access_denied":
            raise DeviceFlowError("Login was canceled on GitHub.")
        if err == "expired_token":
            raise DeviceFlowError("The code expired before it was approved.")
        raise DeviceFlowError(str(resp.get("error_description") or err or resp))
    raise DeviceFlowError("The code expired before it was approved.")


def fetch_identity(token):
    user = _request(f"{_API}/user", token=token)
    if "login" not in user:
        raise DeviceFlowError("GitHub did not return your account: " + str(user.get("message", user)))
    login = user["login"]
    email = user.get("email") or ""
    if not email:
        emails = _request(f"{_API}/user/emails", token=token)
        if isinstance(emails, list):
            for entry in emails:
                if entry.get("primary") and entry.get("verified"):
                    email = entry["email"]
                    break
    if not email:
        email = f"{user['id']}+{login}@users.noreply.github.com"
    return login, email


def _upload(path, title, public_key, token):
    resp = _request(f"{_API}{path}", {"title": title, "key": public_key}, token=token, method="POST")
    status = resp.get("_status")
    if status is None:
        return
    message = str(resp.get("message", "")) + " " + str(resp.get("errors", ""))
    if status == 422 and "already" in message.lower():
        return  # same key is already registered: that is the outcome we want
    raise DeviceFlowError(f"GitHub rejected the key upload ({status}): {resp.get('message', resp)}")


def upload_keys(token, public_key, title):
    _upload("/user/keys", title, public_key, token)
    _upload("/user/ssh_signing_keys", title, public_key, token)
