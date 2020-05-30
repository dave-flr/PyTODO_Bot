import qrcode
import zbarlight
import requests
from PIL import Image
from io import BytesIO


def generate_qr(text):
    return qrcode.make(text)


def decode_qr(img_url):
    response = requests.get(img_url)
    image = Image.open(BytesIO(response.content))
    image.load()

    codes = zbarlight.scan_codes(['qrcode'], image)
    return codes[0].decode()
