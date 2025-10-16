import requests
from bs4 import BeautifulSoup
from PIL import Image
import pytesseract
import cv2
import numpy as np
import io

class CaptchaSolver:
    def __init__(self, captcha_url):
        self.captcha_url = captcha_url

    def fetch_captcha(self):
        response = requests.get(self.captcha_url)
        response.raise_for_status()
        return response.content

    def process_image(self, image_bytes):
        image = Image.open(io.BytesIO(image_bytes))
        # Convert to grayscale
        image = image.convert('L')
        # Convert to numpy array for OpenCV
        img_np = np.array(image)
        # Thresholding
        _, img_thresh = cv2.threshold(img_np, 128, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
        # Convert back to PIL
        processed_image = Image.fromarray(img_thresh)
        return processed_image

    def solve_captcha(self, image_bytes):
        processed_image = self.process_image(image_bytes)
        text = pytesseract.image_to_string(processed_image, config='--psm 8')
        return text.strip()
