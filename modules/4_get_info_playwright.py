"""
This script uses Playwright and makes some actions:
load page, enter search text,
click search button and first product of the list,
parse product data and save to DB
"""

import os

os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"  # noqa

import subprocess
from pprint import pprint  # noqa
from sys import executable

from playwright.sync_api import sync_playwright, Page

from load_django import *  # noqa
from parser_app.models import Status, ProductInfo


def install_playwright_browsers():
    """
    Install playwright browsers
    """
    print("🤖 Checking/Installing Playwright browsers...")
    try:
        subprocess.run([executable, "-m", "playwright", "install", "chromium"])
        print("✅ Browsers installed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install browsers: {e}")


def open_page(page: Page, url: str) -> None:
    """Open page"""
    page.goto(url, wait_until="domcontentloaded")


def enter_search_query(page: Page) -> None:
    """Enter search query"""
    search_input_xpath = (
        "//*[contains(@class, 'header-bottom-in')]//input[@type='search']"
    )

    # 1. Click to focus
    page.locator(search_input_xpath).click()

    # 2. Type with delay (100ms between keys)
    page.locator(search_input_xpath).press_sequentially(
        "Apple iPhone 15 128GB Black", delay=100
    )

    # 3. Wait a bit for the UI to settle/animation to finish
    page.wait_for_timeout(1000)


def click_search_button(page: Page) -> None:
    """Click search button"""
    search_button_xpath = "//input[contains(@class, 'qsr-submit')][@type='submit']"
    page.locator(search_button_xpath).click()


def click_first_product(page: Page) -> None:
    first_product_xpath = "(//*[contains(@class, 'br-pp-img')]/a)[2]"
    # Playwright auto-waits for the element to be actionable
    page.locator(first_product_xpath).click()


def parse_product_data(page) -> dict | None:
    """Parse product data"""

    # Product Data
    product_info = {}

    def save_text_value(attrib: str, xpath: str) -> None:
        try:
            product_info[attrib] = page.locator(xpath).text_content().strip()
        except AttributeError as e:
            print(f"❌ Error {attrib}", e)
            product_info[attrib] = None
            # TO DO: logging

    # Name
    save_text_value("name", "//h1[contains(@class, 'main-title')]")

    # Color
    save_text_value("color", "//a[starts-with(@title, 'Колір')]")

    # Built-in Memory
    save_text_value("builtin_memory", "//a[starts-with(@title, 'Вбудована пам')]")

    # Manufacturer
    save_text_value("manufacturer", "//span[text()='Виробник']/following-sibling::span")

    # SKU
    save_text_value("sku", "(//*[contains(@class, 'br-pr-code-val')])[1]")

    # Reviews Count
    save_text_value("reviews_count", "(//*[contains(@class, 'reviews-count')]/span)[1]")

    # Prices
    try:
        xpath = "//*[contains(@class, 'main-price-block')]//*[contains(@class, 'price-wrapper')]/span"
        prices = page.locator(xpath).all()
    except AttributeError as e:
        print("❌ Error Prices", e)
        product_info["price_regular"] = None
        product_info["price_sale"] = None
        # TO DO: logging
    else:
        # Regular Price
        try:
            product_info["price_regular"] = prices[0].text_content().strip()
        except IndexError:
            product_info["price_regular"] = None
            # TO DO: logging

        # Sale Price
        try:
            product_info["price_sale"] = prices[1].text_content().strip()
        except IndexError:
            product_info["price_sale"] = None
            # TO DO: logging

    # Images
    try:
        xpath = "//*[contains(@class, 'br-pr-slider')]//img"
        images = page.locator(xpath).all()

        images_srcs = []
        for image in images:
            images_srcs.append(image.get_attribute("src"))

        product_info["images"] = images_srcs
    except AttributeError as e:
        print("❌ Error Images", e)
        product_info["images"] = None
        # TO DO: logging

    # Characteristics
    try:
        xpath = "//*[contains(@class, 'br-pr-chr-item')]"
        characteristics = page.locator(xpath).all()

        characteristics_list = []
        for characteristic in characteristics:
            try:
                xpath = "xpath=.//h3"
                title = characteristic.locator(xpath).text_content().strip()

                xpath = "xpath=.//div/div"
                items = characteristic.locator(xpath).all()
            except AttributeError as e:
                print("❌ Error Characteristic Block", e)
                # TO DO: logging
                continue
            else:
                items_dict = {}
                for item in items:
                    try:
                        xpath = "xpath=.//span"
                        key, value, *rest = item.locator(xpath).all()
                    except AttributeError as e:
                        print("❌ Error Characteristic Row", e)
                        # TO DO: logging
                        continue
                    else:
                        # Default parameter
                        param_name = None
                        param_value = None

                        try:
                            param_name = key.text_content().strip()
                            param_value = (
                                value.text_content().replace("\xa0", " ").strip()
                            )
                        except AttributeError as e:
                            print("❌ Error Characteristic Cols", e)
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
    except AttributeError as e:
        print("❌ Error Characteristics", e)
        product_info["characteristics"] = None
        # TO DO: logging

    return product_info


def steps(page) -> None:
    # Step 1: Open the main page
    url = "https://brain.com.ua/"
    print(f"Step 1: Navigating to {url}")
    open_page(page, url)

    # Step 2: Input search query
    print("Step 2: Entering search query...")
    enter_search_query(page)

    # Step 3: Click search button
    print("Step 3: Clicking search button...")
    click_search_button(page)

    # Step 4: Click the 1st result
    print("Step 4: Clicking the first result...")
    click_first_product(page)

    # Step 5: Parse product info
    print("Step 5: Parse product details...")
    data = parse_product_data(page)

    # Step 6: Save to DB
    save_to_db(page, data)

    # pprint(data)


def save_to_db(page: Page, data: dict) -> None:
    # Saving product_info into DB
    data["link"] = page.url
    data["status"] = Status.DONE

    ProductInfo.objects.get_or_create(**data)


def main() -> None:
    """
    Main function
    """
    with sync_playwright() as p:
        # Launch browser in headful mode to see the actions (headless=False)
        browser = p.chromium.launch(headless=False)

        # Create a new page context
        page = browser.new_page()

        # Run actions
        steps(page)

        # Close browser
        browser.close()


if __name__ == "__main__":
    install_playwright_browsers()

    main()
