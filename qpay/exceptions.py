from typing import Union

import requests


class QPayException(Exception):
    def __init__(
        self,
        message: str,
        request: Union[requests.Request, requests.PreparedRequest, None],
        response: Union[requests.Response, None],
    ) -> None:
        self.message = message
        self.request = request
        self.response = response
        super().__init__(self.message)

    def __str__(self) -> str:
        return f"""QPayException(message="{self.message}")"""
