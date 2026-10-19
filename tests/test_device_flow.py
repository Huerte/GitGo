import pytest
from pygitgo.auth import device_flow as df


@pytest.fixture(autouse=True)
def _cid(monkeypatch):
    monkeypatch.setenv("GITGO_GITHUB_CLIENT_ID", "Iv1.test")


def test_unavailable_without_client_id(monkeypatch):
    monkeypatch.delenv("GITGO_GITHUB_CLIENT_ID", raising=False)
    monkeypatch.setattr(df, "DEFAULT_CLIENT_ID", "")
    assert df.is_available() is False


def test_available_with_env_client_id():
    assert df.is_available() is True


def test_start_returns_codes(mocker):
    req = mocker.patch.object(df, "_request", return_value={"device_code": "d", "user_code": "U", "verification_uri": "v"})
    assert df.start()["user_code"] == "U"
    assert req.call_args[0][1]["client_id"] == "Iv1.test"
    assert "admin:public_key" in req.call_args[0][1]["scope"]
    assert "write:ssh_signing_key" in req.call_args[0][1]["scope"]


def test_start_error_is_readable(mocker):
    mocker.patch.object(df, "_request", return_value={"error": "device_flow_disabled", "error_description": "Device Flow must be explicitly enabled"})
    with pytest.raises(df.DeviceFlowError, match="explicitly enabled"):
        df.start()


def _poll(mocker, responses, expires=900):
    mocker.patch.object(df, "_request", side_effect=responses)
    sleeps = []
    clock = iter(range(0, 100000, 1))
    token = lambda: df.wait_for_token({"device_code": "d", "interval": 5, "expires_in": expires}, sleep=sleeps.append, now=lambda: next(clock))
    return token, sleeps


def test_wait_polls_until_approved(mocker):
    run, sleeps = _poll(mocker, [{"error": "authorization_pending"}, {"error": "authorization_pending"}, {"access_token": "tok"}])
    assert run() == "tok"
    assert sleeps == [5, 5, 5]


def test_wait_obeys_slow_down(mocker):
    run, sleeps = _poll(mocker, [{"error": "slow_down", "interval": 10}, {"access_token": "tok"}])
    assert run() == "tok"
    assert sleeps == [5, 10]


@pytest.mark.parametrize("err,msg", [("access_denied", "canceled"), ("expired_token", "expired")])
def test_wait_terminal_errors(mocker, err, msg):
    run, _ = _poll(mocker, [{"error": err}])
    with pytest.raises(df.DeviceFlowError, match=msg):
        run()


def test_wait_times_out(mocker):
    mocker.patch.object(df, "_request", return_value={"error": "authorization_pending"})
    ticks = iter([0, 1, 2000, 2001])
    with pytest.raises(df.DeviceFlowError, match="expired"):
        df.wait_for_token({"device_code": "d", "interval": 1, "expires_in": 10}, sleep=lambda s: None, now=lambda: next(ticks))


def test_identity_prefers_primary_verified_email(mocker):
    mocker.patch.object(df, "_request", side_effect=[
        {"login": "octo", "id": 7, "email": None},
        [{"email": "no@x", "primary": False, "verified": True}, {"email": "yes@x", "primary": True, "verified": True}],
    ])
    assert df.fetch_identity("t") == ("octo", "yes@x")


def test_identity_falls_back_to_noreply(mocker):
    mocker.patch.object(df, "_request", side_effect=[{"login": "octo", "id": 7}, {"message": "Not Found", "_status": 404}])
    assert df.fetch_identity("t") == ("octo", "7+octo@users.noreply.github.com")


def test_upload_registers_both_key_kinds(mocker):
    req = mocker.patch.object(df, "_request", return_value={})
    df.upload_keys("t", "ssh-ed25519 AAAA", "GitGo (pc)")
    paths = [c[0][0] for c in req.call_args_list]
    assert paths == ["https://api.github.com/user/keys", "https://api.github.com/user/ssh_signing_keys"]


def test_upload_treats_already_registered_as_success(mocker):
    mocker.patch.object(df, "_request", return_value={"_status": 422, "message": "Validation Failed", "errors": [{"message": "key is already in use"}]})
    df.upload_keys("t", "k", "title")


def test_upload_surfaces_real_failures(mocker):
    mocker.patch.object(df, "_request", return_value={"_status": 403, "message": "Resource not accessible"})
    with pytest.raises(df.DeviceFlowError, match="403"):
        df.upload_keys("t", "k", "title")


def test_request_parses_http_error_body(mocker):
    import io, urllib.error
    err = urllib.error.HTTPError("u", 422, "Unprocessable", {}, io.BytesIO(b'{"message": "Validation Failed"}'))
    mocker.patch("urllib.request.urlopen", side_effect=err)
    resp = df._request("https://api.github.com/user/keys", {"title": "t", "key": "k"}, token="x", method="POST")
    assert resp["_status"] == 422 and resp["message"] == "Validation Failed"


def test_request_wraps_network_errors(mocker):
    import urllib.error
    mocker.patch("urllib.request.urlopen", side_effect=urllib.error.URLError("offline"))
    with pytest.raises(df.DeviceFlowError, match="offline"):
        df._request("https://github.com/login/device/code", {"a": "b"})
