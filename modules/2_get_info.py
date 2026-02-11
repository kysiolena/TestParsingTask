"""
Parsing data from https://brain.com.ua/ukr/Mobilniy_telefon_Apple_iPhone_16_Pro_Max_256GB_Black_Titanium-p1145443.html
***************
Name
Color
Built-in Memory
Manufacturer
Prices
SKU
Reviews Count
Images
Screen Diagonal
Screen Resolution
Characteristics
***************
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
        response = session.get(url)
        response.raise_for_status()  # Raises an error for 4xx or 5xx codes

        soup = BeautifulSoup(response.text, "html.parser")

        # Product Data
        product_info = {}

        # Name
        try:
            product_info["name"] = soup.select_one(
                "h1.main-title"
            ).text.strip()  # //h1[@class='main-title']
        except AttributeError as e:
            print("❌ Error Name", e)
            product_info["name"] = None
            # TO DO: logging

        # Color
        try:
            product_info["color"] = soup.select_one(
                "a[title^='Колір']"
            ).text.strip()  # //a[starts-with(@title, 'Колір')]
        except AttributeError as e:
            print("❌ Error Color", e)
            product_info["color"] = None
            # TO DO: logging

        # Built-in Memory
        try:
            product_info["builtin_memory"] = soup.select_one(
                "a[title^='Вбудована пам']"
            ).text.strip()  # //a[starts-with(@title, 'Вбудована пам')]
        except AttributeError as e:
            print("❌ Error Built-in Memory", e)
            product_info["builtin_memory"] = None
            # TO DO: logging

        # Manufacturer
        try:
            product_info["manufacturer"] = (
                soup.find(string="Виробник").find_next("span").text.strip()
            )
            # //span[text()='Виробник']/following-sibling::span
        except AttributeError as e:
            print("❌ Error Manufacturer", e)
            product_info["manufacturer"] = None
            # TO DO: logging

        # Prices
        try:
            prices = soup.select(
                ".main-price-block .price-wrapper > span"
            )  # //*[contains(@class, 'main-price-block')]//*[@class='price-wrapper']/span
        except AttributeError as e:
            print("❌ Error Prices", e)
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
            sku = soup.select_one(".br-pr-code-val")

            product_info["sku"] = sku.text.strip()
            # //*[@class='br-pr-code-val']
        except AttributeError as e:
            print("❌ Error SKU", e)
            product_info["sku"] = None
            # TO DO: logging

        # Reviews Count
        try:
            product_info["reviews_count"] = soup.select_one(
                ".reviews-count span"
            ).text.strip()
            # //*[contains(@class, 'reviews-count')]/span
        except AttributeError as e:
            print("❌ Error Review Count", e)
            product_info["reviews_count"] = None
            # TO DO: logging

        # Images
        try:
            images = soup.select(".br-pr-slider .br-main-img")
            # //*[contains(@class, 'br-pr-slider')]//img[@class='br-main-img']

            images_srcs = []
            for image in images:
                images_srcs.append(image.get("src"))

            product_info["images"] = images_srcs
        except AttributeError as e:
            print("❌ Error Images", e)
            product_info["images"] = None
            # TO DO: logging

        # Characteristics
        try:
            characteristics = soup.select(".br-pr-chr-item")
            # //*[@class='br-pr-chr-item']

            characteristics_list = []
            for characteristic in characteristics:
                try:
                    title = characteristic.select_one("h3").text.strip()

                    items = characteristic.select("div > div")
                except AttributeError:
                    # TO DO: logging
                    continue
                else:
                    items_dict = {}
                    for item in items:
                        try:
                            key, value, *rest = item.select("span")
                        except AttributeError:
                            # TO DO: logging
                            continue
                        else:
                            # Default parameter
                            param_name = None
                            param_value = None

                            try:
                                param_name = key.text.strip()
                                param_value = value.select_one("a").text.strip()
                            except AttributeError:
                                # TO DO: logging
                                continue
                            else:
                                items_dict[param_name] = param_value
                            finally:
                                # Screen Diagonal
                                if param_name == "Діагональ екрану":
                                    product_info["screen_diagonal"] = param_value

                                # Screen Resolution
                                if param_name == "Роздільна здатність екрану":
                                    product_info["screen_resolution"] = param_value

                    # Append characteristic list
                    characteristics_list.append((title, items_dict))

            product_info["characteristics"] = characteristics_list
        except AttributeError:
            product_info["characteristics"] = None
            # TO DO: logging

        return product_info

    except RequestException as e:
        print(f"❌ Error fetching {url}: {e}")

        return None


if __name__ == "__main__":
    # URL
    target_url = "https://brain.com.ua/ukr/Mobilniy_telefon_Apple_iPhone_16_Pro_Max_256GB_Black_Titanium-p1145443.html"

    # Get data
    data = get_product_data(target_url)

    # Display data
    pprint.pprint(data)
