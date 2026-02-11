"""
Parsing data from https://brain.com.ua/ukr/Mobilniy_telefon_Apple_iPhone_16_Pro_Max_256GB_Black_Titanium-p1145443.html
"""

import pprint

from bs4 import BeautifulSoup
from requests import Session
from requests.exceptions import RequestException

# 1. Initialize the Session
session = Session()

# 2. Assign global headers (these will be sent with every request)
session.headers.update(
    {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "en-GB,en;q=0.9,ru-RU;q=0.8,ru;q=0.7,en-US;q=0.6",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
        "sec-ch-ua-platform": '"Windows"',
        "dnt": "1",
    }
)

# 3. Pre-load your specific cookies into the session
# This mimics a returning user with an active session
initial_cookies = {
    "PHPSESSID": "s0449bcr0ud0eeu1gsemb3ckgh",
    "Lang": "ua",
    "CityID": "23562",
    "view_type": "grid",
}
session.cookies.update(initial_cookies)


def get_product_data(url: str) -> dict | None:
    """
    Parse product data from https://brain.com.ua
    :param url:
    :return:
    """
    try:
        # We don't need to pass headers/cookies here; they are held by the session
        response = session.get(url, timeout=10)
        response.raise_for_status()  # Raises an error for 4xx or 5xx codes

        soup = BeautifulSoup(response.text, "html.parser")

        # Product Data
        product_info = {}

        # Name
        try:
            product_info["name"] = soup.select_one(
                "h1.main-title"
            ).text.strip()  # //h1[@class='main-title']
        except AttributeError:
            product_info["name"] = None
            # TO DO: logging

        # Color
        try:
            product_info["color"] = soup.select_one(
                "a[title^='Колір'"
            ).text.strip()  # //a[starts-with(@title, 'Колір')]
        except AttributeError:
            product_info["color"] = None
            # TO DO: logging

        # Built-in Memory
        try:
            product_info["builtin_memory"] = soup.select_one(
                "a[title^='Вбудована пам'"
            ).text.strip()  # //a[starts-with(@title, 'Вбудована пам')]
        except AttributeError:
            product_info["builtin_memory"] = None
            # TO DO: logging

        # Manufacturer
        try:
            product_info["manufacturer"] = soup.select_one(
                ".br-pr-chr .br-pr-chr-item:last-of-type > div div:first-of-type span:last-of-type"
            ).text.strip()  # //span[text()='Виробник']/following-sibling::span
        except AttributeError:
            product_info["manufacturer"] = None
            # TO DO: logging

        # Prices
        try:
            prices = soup.select(
                ".main-price-block .price-wrapper > span"
            )  # //*[contains(@class, 'main-price-block')]//*[@class='price-wrapper']/span
        except AttributeError:
            product_info["price_regular"] = None
            product_info["price_sale"] = None
            # TO DO: logging
        else:
            # Regular Price
            try:
                product_info["price_regular"] = prices[0].text.strip()
            except IndexError:
                product_info["price_regular"] = None
                # TO DO: logging

            # Sale Price
            try:
                product_info["price_sale"] = prices[1].text.strip()
            except IndexError:
                product_info["price_sale"] = None
                # TO DO: logging

        # SKU
        try:
            product_info["sku"] = soup.select_one(
                ".main-right-block .br-pr-code-val"
            ).text.strip()  # //*[contains(@class, 'main-right-block')]//*[@class='br-pr-code-val']
        except AttributeError:
            product_info["sku"] = None
            # TO DO: logging

        # Reviews Count
        try:
            product_info["reviews_count"] = soup.select_one(
                "##"
            ).text.strip()  # //*[contains(@class, 'main-right-block')]//*[@class='br-pr-code-val']/ancestor-or-self::*[@class='br-pr-code-wrapper']/*[contains(@class, 'main-comments-block')]//*[contains(@class, 'reviews-count')]/span
        except AttributeError:
            product_info["reviews_count"] = None
            # TO DO: logging

        """
        Все фото товара. Здесь нужно собрать ссылки на фото и сохранить в список
        Кол-во отзывов
        Диагональ экрана
        Разрешение дисплея
        Характеристики товара. Все характеристики на вкладке. Характеристики собрать как словарь
        """

        return product_info

    except RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None


if __name__ == "__main__":
    # URL
    target_url = "https://brain.com.ua/ukr/Mobilniy_telefon_Apple_iPhone_16_Pro_Max_256GB_Black_Titanium-p1145443.html"

    # Get data
    data = get_product_data(target_url)

    # Display data
    pprint.pprint(data)
