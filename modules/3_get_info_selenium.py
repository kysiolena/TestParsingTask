"""
This script makes some actions:
load page, enter search text,
click search button and first product of the list,
parse product data and save to DB
"""

import time
from pprint import pprint  # noqa

from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

from load_django import *  # noqa
from parser_app.models import ProductInfo, Status


def open_page(driver, url: str) -> None:
    """
    Open a web page.
    """
    driver.get(url)
    driver.maximize_window()


def enter_search_query(wait) -> None:
    """
    Enter search query.
    """
    # Locating the search input field
    search_input = wait.until(
        EC.presence_of_element_located(
            (
                By.XPATH,
                "//*[contains(@class, 'header-bottom-in')]//input[@type='search']",
            )
        )
    )
    search_input.clear()
    search_input.send_keys("Apple iPhone 15 128GB Black")


def click_search_button(wait) -> None:
    """
    Click search button.
    """
    # Looking for the search button
    search_button = wait.until(
        EC.element_to_be_clickable(
            (
                By.XPATH,
                "//input[contains(@class, 'qsr-submit')][@type='submit']",
            )
        )
    )
    search_button.click()


def click_first_product(wait) -> None:
    """
    Click first product.
    """
    first_product = wait.until(
        EC.element_to_be_clickable((By.XPATH, "//*[contains(@class, 'br-pp-img')]/a"))
    )
    first_product.click()


def parse_product_data(driver, wait) -> dict | None:
    # Product Data
    product_info = {}

    def save_text_value(attrib: str, xpath: str) -> None:
        try:
            product_info[attrib] = (
                driver.find_element(By.XPATH, xpath)
                .get_attribute("textContent")
                .strip()
            )
        except (NoSuchElementException, AttributeError) as e:
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
    save_text_value("sku", "//*[contains(@class, 'br-pr-code-val')]")

    # Reviews Count
    save_text_value("reviews_count", "//*[contains(@class, 'reviews-count')]/span")

    # Prices
    try:
        prices = driver.find_elements(
            By.XPATH,
            "//*[contains(@class, 'main-price-block')]//*[contains(@class, 'price-wrapper')]/span",
        )
    except NoSuchElementException as e:
        print("❌ Error Prices", e)
        product_info["price_regular"] = None
        product_info["price_sale"] = None
        # TO DO: logging
    else:
        # Regular Price
        try:
            product_info["price_regular"] = (
                prices[0].get_attribute("textContent").strip()
            )
        except IndexError:
            product_info["price_regular"] = None
            # TO DO: logging

        # Sale Price
        try:
            product_info["price_sale"] = prices[1].get_attribute("textContent").strip()
        except IndexError:
            product_info["price_sale"] = None
            # TO DO: logging

    # Images
    try:
        images = driver.find_elements(
            By.XPATH, "//*[contains(@class, 'br-pr-slider')]//img"
        )

        images_srcs = []
        for image in images:
            images_srcs.append(image.get_attribute("src"))

        product_info["images"] = images_srcs
    except NoSuchElementException as e:
        print("❌ Error Images", e)
        product_info["images"] = None
        # TO DO: logging

    # Characteristics
    try:
        characteristics = driver.find_elements(
            By.XPATH, "//*[contains(@class, 'br-pr-chr-item')]"
        )

        characteristics_list = []
        for characteristic in characteristics:
            try:
                title = (
                    characteristic.find_element(By.XPATH, ".//h3")
                    .get_attribute("textContent")
                    .strip()
                )

                items = characteristic.find_elements(By.XPATH, ".//div/div")
            except (AttributeError, NoSuchElementException) as e:
                print("❌ Error Characteristic Block", e)
                # TO DO: logging
                continue
            else:
                items_dict = {}
                for item in items:
                    try:
                        key, value, *rest = item.find_elements(By.XPATH, ".//span")
                    except (AttributeError, NoSuchElementException) as e:
                        print("❌ Error Characteristic Row", e)
                        # TO DO: logging
                        continue
                    else:
                        # Default parameter
                        param_name = None
                        param_value = None

                        try:
                            param_name = key.get_attribute("textContent").strip()
                            param_value = (
                                value.get_attribute("textContent")
                                .replace("\xa0", " ")
                                .strip()
                            )
                        except (AttributeError, NoSuchElementException) as e:
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
    except (AttributeError, NoSuchElementException) as e:
        print("❌ Error Characteristics", e)
        product_info["characteristics"] = None
        # TO DO: logging

    return product_info


def save_to_db(driver, data: dict) -> None:
    # Saving product_info into DB
    data["link"] = driver.current_url
    data["status"] = Status.DONE

    ProductInfo.objects.get_or_create(**data)


def steps(url: str, driver: WebDriver, wait: WebDriverWait) -> None:
    # Step 1: Open the page
    open_page(driver, url)

    # Step 2: Enter search query
    enter_search_query(wait)

    # Step 3: Click the "Find" button
    click_search_button(wait)

    # Step 4: Click on the first search result
    click_first_product(wait)

    # Step 5: Parse product details
    data = parse_product_data(driver, wait)

    # Step 6: Save to DB
    save_to_db(driver, data)

    # pprint(data)


def main() -> None:
    # Initialize the driver
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--start-maximized")
    driver = webdriver.Chrome(
        options=chrome_options, service=Service(ChromeDriverManager().install())
    )
    driver.set_window_size(1920, 1080)
    wait = WebDriverWait(driver, 10)

    try:
        # Run actions
        url = "https://brain.com.ua/"
        steps(url, driver, wait)
    finally:
        # Keep the browser open for a few seconds to see the result, then close
        time.sleep(10)

        driver.quit()


if __name__ == "__main__":
    main()
