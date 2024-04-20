<h1 align="center">
  QPayClient
</h1>

<p align="center">
  <a href="#usage">Ашиглах</a> •
  <a href="#contribution">Хөгжүүлэлтэнд оролцох</a> •
  <a href="#license">Лиценз</a>
</p>

<p align="center">QPay v2 гүйлгээний сервисүүдийг Python хэлний орчинд ашиглахад зориулсан сан</p>

### <a id="usage"></a>QPayClient -г ашиглах

Хамгийн эхлээд `QPayClient` -с объект үүсгэж авна. Ингэхийн тулд KKTТ ХХК -тай гэрээ хийн нэр, нууц үг авсан байх шаардлагатай. Нэг л удаа үүсгээд авчихсан байхад токен дуусах, сунгах зэрэг дээр санаа зовох шаардлагагүй.

```py
import qpay import QPayClient

client = QPayClient(host="https://merchant.qpay.mn/v2/", username="MERCHANT_USERNAME", password="MERCHANT_PASSWORD")

...
```

QPayClient нь singleton paradigm -г ашигладаг учир нэг л объект үүсгэж, тэрийгээ дахин ашиглана. Шаардлагатай сервисүүдийг үүсгэсэн объектоороо дамжуулан дуудна.

```py
...

payload = {"invoice_code": ... }
invoice = client.invoice_create(json=payload)
print(invoice.qr_text) # 0002010102121531279404962794049600000000KKTQ...

...
```

## <a id="contribution"></a>Хөгжүүлэлтэнд оролцох

Энэхүү сантай холбоотой алдаа засвар, сайжруулалт болон бусад санал, хүсэлтийг нээлттэй хүлээж авах ба ялангуяа чанартай кодын өөрчлөлтүүд илгээвэл маш их баярлах болно.

Жич: Кодын өөрчлөлт оруулахдаа заавал тестийг нь хамт оруулахаа битгий мартаарай.

## <a id="license"></a>Лиценз

[MIT License](https://choosealicense.com/licenses/mit/)
