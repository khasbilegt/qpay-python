import logging
from typing import Literal
from urllib.parse import urljoin

import requests

from .auth import QPayAuth
from .singleton import Singleton

logger = logging.getLogger(__name__)


class QPayClient(Singleton):
    def __init__(self, host: str, username: str, password: str):
        session = requests.Session()
        session.auth = QPayAuth(host, username, password)
        self._host = host
        self._session = session

    def _request(self, method: Literal["get", "post", "delete"], path: str, **kwargs):
        try:
            url = urljoin(self._host, path)
            response = self._session.request(method, url, **kwargs)
            response.raise_for_status()

            return response.json()
        except requests.RequestException as exc:
            logger.exception(exc)
            raise exc
