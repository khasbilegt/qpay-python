import json
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
        "amount": 100,
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

    def json_callback(request, context):
        body = json.loads(request.body)
        assert request.headers["Authorization"] == "Bearer ACCESS_TOKEN"
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
    assert invoice.invoice_id == response_body["invoice_id"]
    assert invoice.qr_text == response_body["qr_text"]
    assert invoice.qr_image == response_body["qr_image"]
    assert invoice.model_dump()["urls"] == response_body["urls"]
