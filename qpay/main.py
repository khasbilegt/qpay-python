import logging
from typing import Literal
from urllib.parse import urljoin

import requests
from pydantic import BaseModel, Field

from .auth import QPayAuth
from .exceptions import QPayException
from .singleton import Singleton

logger = logging.getLogger(__name__)


class Invoice(BaseModel):
    class URL(BaseModel):
        name: str = Field(description="Банкны нэр")
        description: str = Field(description="Утга")
        link: str = Field(description="Холбоос линк")

    invoice_id: str = Field(description="Нэхэмжлэхийн дугаар")
    qr_text: str = Field(description="Данс болон картын гүйлгээ дэмжих QR утга")
    qr_image: str = Field(description="QPay лого голдоо агуулсан base64 зурган QR код")
    urls: list[URL] = Field(
        description="Аппликейшнээс банкны аппликейшнруу үсрэх Deeplink"
    )


class CreateInvoicePayload(BaseModel):
    invoice_code: str = Field(description="QPay-ээс өгсөн нэхэмжлэхийн код")
    sender_invoice_no: str = Field(
        description="Байгууллагаас үүсгэх давтагдашгүй нэхэмжлэлийн дугаар"
    )
    invoice_receiver_code: str = Field(
        default="terminal",
        description="Байгууллагын нэхэмжлэхийг хүлээн авч буй"
        "харилцагчийн дахин давтагдашгүй дугаар",
    )
    invoice_description: str = Field(description="Нэхэмжлэлийн утга")
    amount: int = Field(description="Мөнгөн дүн")
    callback_url: str = Field(
        description="Төлбөр төлсөгдсөн эсэх талаар мэдэгдэл авах URL"
    )
    #


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
        except requests.HTTPError as exc:
            logger.exception(exc)
            raise QPayException(
                exc.response.json(), request=exc.request, response=exc.response
            ) from exc

    def invoice_create(self, json: dict) -> Invoice:
        payload = CreateInvoicePayload(**json)
        response = self._request("post", "invoice", json=payload.model_dump())
        return Invoice(**response)

    def invoice_cancel(self, invoice_id: str) -> bool:
        response = self._request("delete", f"invoice/{invoice_id}")
        return "error" not in response
