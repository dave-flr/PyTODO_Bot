import os
from imgurpython import ImgurClient
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')

imgur_client = ImgurClient(CLIENT_ID, CLIENT_SECRET)
