import logging
import threading
from datetime import datetime, timedelta
from typing import Callable, Optional
from urllib.parse import urljoin

import requests
from pydantic import BaseModel

from .exceptions import QPayException

logger = logging.getLogger(__name__)


class AccessToken(BaseModel):
    token: str
    expires: datetime


class RefreshToken(BaseModel):
    token: str
    expires: datetime


class QPayAuth(requests.auth.AuthBase):
    def __init__(
        self,
        host: str,
        username: str,
        password: str,
        now: Optional[Callable[[], datetime]] = None,
    ):
        self._access_token: Optional[AccessToken] = None
        self._refresh_token: Optional[RefreshToken] = None
        self._token_lock = threading.Lock()
        self._host = urljoin(host, "auth/")
        self._username = username
        self._password = password
        self._now = now

    def _timestamp(self):
        if self._now:
            return self._now()
        else:
            return datetime.now()

    def _fetch_token(
        self, refresh_token: Optional[RefreshToken] = None
    ) -> tuple[AccessToken, RefreshToken]:
        try:
            now = self._timestamp()
            r = (
                requests.post(
                    urljoin(self._host, "refresh"),
                    headers={"Authorization": f"Bearer {refresh_token.token}"},
                )
                if refresh_token and refresh_token.expires > now
                else requests.post(
                    urljoin(self._host, "token"),
                    auth=(self._username, self._password),
                )
            )
            r.raise_for_status()
            token = r.json()
            access_token = AccessToken(
                token=token["access_token"],
                expires=now + timedelta(seconds=token["expires_in"]),
            )
            refresh_token = RefreshToken(
                token=token["refresh_token"],
                expires=now + timedelta(seconds=token["refresh_expires_in"]),
            )
            return (access_token, refresh_token)
        except requests.HTTPError as exc:
            logger.exception(exc)
            if refresh_token and exc.response.status_code == 401:
                return self._fetch_token()
            raise QPayException(
                exc.response.json(), request=exc.request, response=exc.response
            ) from exc

    def _get_token(self) -> AccessToken:
        with self._token_lock:
            now = self._timestamp()

            if self._access_token and self._access_token.expires > now:
                return self._access_token

            self._access_token, self._refresh_token = self._fetch_token(
                self._refresh_token
            )
            return self._access_token

    def __call__(self, r):
        token = self._get_token()
        r.headers["Authorization"] = f"Bearer {token.token}"
        return r
