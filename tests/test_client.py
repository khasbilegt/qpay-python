import json
import uuid
from urllib.parse import urljoin

import pytest

from qpay import QPayClient, QPayException

HOST = "https://merchant.qpay.mn/v2/"
AUTH_HOST = urljoin(HOST, "auth/")


@pytest.fixture
def client():
    return QPayClient(host=HOST, username="username", password="password")


@pytest.fixture
def requests_mock(requests_mock):
    response = {
        "token_type": "bearer",
        "refresh_expires_in": 36000,
        "refresh_token": "REFRESH_TOKEN",
        "access_token": "ACCESS_TOKEN",
        "expires_in": 36000,
    }
    token_url = urljoin(AUTH_HOST, "token")
    refresh_url = urljoin(AUTH_HOST, "refresh")
    requests_mock.post(token_url, json=response)
    requests_mock.post(refresh_url, json=response)
    return requests_mock


def test_invoice_create(requests_mock, client):
    request_body = {
        "invoice_code": "TEST_INVOICE",
        "sender_invoice_no": "1234567",
        "invoice_receiver_code": "terminal",
        "invoice_description": "test",
        "amount": 100.50,
        "callback_url": "https://bd5492c3ee85.ngrok.io/payments?payment_id=1234567",
    }
    response_body = {
        "invoice_id": "00f94137-66fd-4d90-b2b2-8225c1b4ed2d",
        "qr_text": "QR_TEXT",
        "qr_image": "QR_IMAGE",
        "urls": [
            {
                "name": "Khan bank",
                "description": "Хаан банк",
                "link": "khanbank://q?qPay_QRcode=QR_DATA",
            },
            {
                "name": "State bank",
                "description": "Төрийн банк",
                "link": "statebank://q?qPay_QRcode=QR_DATA",
            },
        ],
    }

    def json_callback(request, _):
        body = json.loads(request.body)
        for key in request_body:
            assert key in body
        return response_body

    requests_mock.post(
        urljoin(client._host, "invoice"),
        [
            {"json": {"message": "Error!"}, "status_code": 403},
            {"json": json_callback, "status_code": 200},
        ],
    )

    with pytest.raises(QPayException) as exc:
        client.invoice_create(json=request_body)
    assert exc.value.response.json() == {"message": "Error!"}

    invoice = client.invoice_create(json=request_body)
    assert invoice.id == response_body["invoice_id"]
    assert invoice.qr_text == response_body["qr_text"]
    assert invoice.qr_image == response_body["qr_image"]
    assert invoice.model_dump()["urls"] == response_body["urls"]


def test_invoice_cancel(requests_mock, client):
    invoice_id = uuid.uuid4()

    def json_callback(request, _):
        assert request.method == "DELETE"
        assert str(invoice_id) in request.url
        return {}

    requests_mock.delete(
        urljoin(client._host, f"invoice/{str(invoice_id)}"),
        [
            {
                "json": {"error": "INVOICE_NOTFOUND", "message": "Нэхэмжлэл олдсонгүй"},
                "status_code": 422,
            },
            {"json": json_callback, "status_code": 200},
        ],
    )

    with pytest.raises(QPayException) as exc:
        client.invoice_cancel(invoice_id=invoice_id)
    assert exc.value.response.json()["error"] == "INVOICE_NOTFOUND"
    assert client.invoice_cancel(invoice_id=invoice_id)


def test_payment_check(requests_mock, client):
    invoice_id = uuid.uuid4()
    payment = {
        "payment_id": "593744473409193",
        "payment_status": "PAID",
        "payment_date": "2020-10-19T08:58:46.641Z",
        "payment_fee": "1.00",
        "payment_amount": "100.00",
        "payment_currency": "MNT",
        "payment_wallet": "0fc9b71c-cd87-4ffd-9cac-2279ebd9deb0",
        "transaction_type": "P2P",
    }
    requests_mock.post(
        urljoin(client._host, "payment/check"),
        [
            {"json": {"count": 0, "rows": []}, "status_code": 200},
            {"json": {"count": 1, "rows": [payment]}, "status_code": 200},
        ],
    )

    assert len(client.payment_check(invoice_id=str(invoice_id))) == 0
    assert len(client.payment_check(invoice_id=str(invoice_id))) == 1
