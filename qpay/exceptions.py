import requests


class QPayException(Exception):
    def __init__(
        self,
        *args: object,
        request: requests.Request | requests.PreparedRequest | None,
        response: requests.Response | None,
    ) -> None:
        super().__init__(args)
        self.request = request
        self.response = response
