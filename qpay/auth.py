import threading
from datetime import datetime, timedelta
from typing import NamedTuple, Optional
from urllib.parse import urljoin

import requests


class AccessToken(NamedTuple):
    token: str
    expires: datetime


class RefreshToken(NamedTuple):
    token: str
    expires: datetime


class QPayAuth(requests.auth.AuthBase):
    def __init__(self, host: str, username: str, password: str):
        self._access_token: Optional[AccessToken] = None
        self._refresh_token: Optional[RefreshToken] = None
        self._token_lock = threading.Lock()
        self._host = urljoin(host, "auth")
        self._username = username
        self._password = password

    def _fetch_token(
        self, refresh_token: Optional[RefreshToken] = None
    ) -> tuple[AccessToken, RefreshToken]:
        try:
            now = datetime.now()
            r = (
                requests.post(
                    urljoin(self._host, "refresh"),
                    headers={"Authorization": f"Bearer {refresh_token.token}"},
                )
                if refresh_token and refresh_token.expires < now
                else requests.post(
                    urljoin(self._host, "token"),
                    auth=(self._username, self._password),
                )
            )
            r.raise_for_status()
            token = r.json()
            access_token = AccessToken(
                token["access_token"], now + timedelta(seconds=token["expires_in"])
            )
            refresh_token = RefreshToken(
                token["refresh_token"],
                now + timedelta(seconds=token["refresh_expires_in"]),
            )
            return (access_token, refresh_token)
        except requests.HTTPError as exception:
            if refresh_token and exception.response.status_code == 401:
                return self._fetch_token()
            raise exception

    def _get_tokens(self) -> AccessToken:
        with self.__token_lock:
            now = datetime.now()
            if self._access_token and self._access_token.expires > now:
                return self._access_token

            self._access_token, self._refresh_token = self._fetch_token(
                self._refresh_token
            )
            return self._access_token

    def __call__(self, r):
        token = self._get_token()
        r.headers["Authorization"] = f"{token.token_type} {token.token}"
        return r
