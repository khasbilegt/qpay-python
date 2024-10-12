import logging
from decimal import Decimal
from typing import Literal
from urllib.parse import urljoin

import requests
from pydantic import BaseModel, Field, field_serializer

from .auth import QPayAuth
from .exceptions import QPayException
from .singleton import Singleton

logger = logging.getLogger(__name__)


class Invoice(BaseModel):
    class URL(BaseModel):
        name: str = Field(description="Банкны нэр")
        description: str = Field(description="Утга")
        logo: str = Field(description="Тухайн банкны лого")
        link: str = Field(description="Холбоос линк")

    id: str = Field(alias="invoice_id", description="Нэхэмжлэхийн дугаар")
    qr_text: str = Field(description="Данс болон картын гүйлгээ дэмжих QR утга")
    qr_image: str = Field(description="QPay лого голдоо агуулсан base64 зурган QR код")
    short_url: str = Field(
        alias="qPay_shortUrl",
        description="QPay богино URL /Мессеж илгээхэд ашиглаж болно/",
    )
    urls: list[URL] = Field(
        description="Аппликейшнээс банкны аппликейшнруу үсрэх Deeplink"
    )


class Payment(BaseModel):
    id: str = Field(alias="payment_id", description="QPay-ээс үүссэн гүйлгээний дугаар")
    status: Literal["NEW", "FAILED", "PAID", "REFUNDED"] = Field(
        alias="payment_status",
        description="Гүйлгээ төлөв NEW: Гүйлгээ үүсгэгдсэн"
        "FAILED: Гүйлгээ амжилтгүй"
        "PAID: Төлөгдсөн"
        "REFUNDED: Гүйлгээ буцаагдсан",
    )
    amount: Decimal = Field(alias="payment_amount", description="Гүйлгээний үнийн дүн")
    currency: Literal["MNT"] = Field(
        alias="payment_currency", description="Гүйлгээний валют"
    )
    wallet: str = Field(
        alias="payment_wallet", description="Гүйлгээ хийсэн воллетийн дугаар"
    )
    type: Literal["P2P", "CARD"] = Field(
        alias="payment_type",
        description="Гүйлгээний төрөл P2P: Дансны гүйлгээ CARD: Картын гүйлгээ",
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
    amount: Decimal = Field(description="Мөнгөн дүн")
    callback_url: str = Field(
        description="Төлбөр төлсөгдсөн эсэх талаар мэдэгдэл авах URL"
    )
    #

    @field_serializer("amount")
    def serialize_amount(self, amount: Decimal, _info):
        return str(amount)


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
                f"Error: [{exc.response.status_code}] {method.capitalize()} - {path}",
                request=exc.request,
                response=exc.response,
            ) from exc

    def invoice_create(self, json: dict) -> Invoice:
        payload = CreateInvoicePayload(**json)
        response = self._request("post", "invoice", json=payload.model_dump())
        return Invoice(**response)

    def invoice_cancel(self, invoice_id: str) -> bool:
        response = self._request("delete", f"invoice/{invoice_id}")
        return "error" not in response

    def payment_check(self, invoice_id: str) -> bool:
        response = self._request(
            "post",
            "payment/check",
            json={"object_type": "INVOICE", "object_id": invoice_id},
        )

        if (rows := response["rows"]) and (len(rows) == 1) and (payment := rows[0]):
            return payment["payment_status"] == "PAID"
        return False
