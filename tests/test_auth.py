from datetime import datetime, timedelta
from unittest.mock import MagicMock
from urllib.parse import urljoin

import pytest

from qpay import QPayAuth, QPayException

HOST = "https://merchant.qpay.mn/v2/"
AUTH_HOST = urljoin(HOST, "auth/")
ACCESS_TOKEN = "DUMMY_ACCESS_TOKEN"
NEW_ACCESS_TOKEN = "NEW_DUMMY_ACCESS_TOKEN"
REFRESH_TOKEN = "DUMMY_REFRESH_TOKEN"


def test_token(requests_mock, monkeypatch):
    def token_callback(request, _):
        assert request.headers["authorization"] == "Basic dXNlcm5hbWU6cGFzc3dvcmQ="
        return {
            "token_type": "bearer",
            "refresh_expires_in": 50,
            "refresh_token": REFRESH_TOKEN,
            "access_token": ACCESS_TOKEN,
            "expires_in": 10,
        }

    def refresh_callback(request, _):
        assert request.headers["authorization"] == f"Bearer {REFRESH_TOKEN}"
        return {
            "token_type": "bearer",
            "refresh_expires_in": 50,
            "refresh_token": "NEW_DUMMY_REFRESH_TOKEN",
            "access_token": NEW_ACCESS_TOKEN,
            "expires_in": 10,
        }

    token_url = urljoin(AUTH_HOST, "token")
    refresh_url = urljoin(AUTH_HOST, "refresh")
    requests_mock.post(token_url, json=token_callback)
    requests_mock.post(
        refresh_url,
        [
            {"json": {"message": "Error"}, "status_code": 401},
            {"json": refresh_callback, "status_code": 200},
        ],
    )

    auth = QPayAuth(HOST, "username", "password")
    request = MagicMock(headers={})

    # Нэвтрэх нэр, нууц үгийг ашиглан токен авна
    with monkeypatch.context() as m:
        frozen_time = datetime(2014, 4, 20, 10, 30, 00)
        m.setattr("qpay.auth.QPayAuth._timestamp", lambda _: frozen_time)
        token = auth._get_token()
        assert token.token == ACCESS_TOKEN
        assert token.expires == frozen_time + timedelta(seconds=10)
        assert auth(request).headers["Authorization"] == f"Bearer {ACCESS_TOKEN}"

    # Токен сэргээн авах хүсэлт 401 буцаавал, нэвтрэх нэр нууц үгээр дахин токен авна
    with monkeypatch.context() as m:
        frozen_time = datetime(2014, 4, 20, 10, 30, 40)
        m.setattr("qpay.auth.QPayAuth._timestamp", lambda _: frozen_time)
        token = auth._get_token()
        assert token.token == ACCESS_TOKEN
        assert token.expires == frozen_time + timedelta(seconds=10)
        assert auth(request).headers["Authorization"] == f"Bearer {ACCESS_TOKEN}"

    # Сэргээх токен ашиглан хандалтын токен дахиж авна
    with monkeypatch.context() as m:
        frozen_time = datetime(2014, 4, 20, 10, 31, 00)
        m.setattr("qpay.auth.QPayAuth._timestamp", lambda _: frozen_time)
        token = auth._get_token()
        assert token.token == NEW_ACCESS_TOKEN
        assert token.expires == frozen_time + timedelta(seconds=10)
        assert auth(request).headers["Authorization"] == f"Bearer {NEW_ACCESS_TOKEN}"

    # Сэргээх токены хугацаа дууссан бол нэвтрэх нэр, нууц үгээр шинийг авна
    with monkeypatch.context() as m:
        frozen_time = datetime(2014, 4, 20, 11, 00, 00)
        m.setattr("qpay.auth.QPayAuth._timestamp", lambda _: frozen_time)
        token = auth._get_token()
        assert token.token == ACCESS_TOKEN
        assert token.expires == frozen_time + timedelta(seconds=10)
        assert auth(request).headers["Authorization"] == f"Bearer {ACCESS_TOKEN}"

    assert [i.url for i in requests_mock.request_history] == [
        token_url,
        refresh_url,
        token_url,
        refresh_url,
        token_url,
    ]


def test_timestamp():
    auth = QPayAuth(HOST, "username", "password")
    assert isinstance(auth._timestamp(), datetime)

    now = datetime.now()
    mocked_now = MagicMock(**{"return_value": now})
    auth = QPayAuth(HOST, "username", "password", mocked_now)
    assert auth._timestamp() == now


def test_token_request_raises_exception(requests_mock):
    with pytest.raises(QPayException) as exc:
        json = {"message": "error"}
        auth = QPayAuth(HOST, "username", "password")
        requests_mock.post(urljoin(AUTH_HOST, "token"), json=json, status_code=500)
        auth._get_token()

    assert exc.value.response.json() == json
