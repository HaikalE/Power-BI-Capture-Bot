import io
import os
import time
import uuid
from io import StringIO

from bs4 import BeautifulSoup
from lxml import etree
from PIL import Image
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


def create_driver():
    """Create the headless Chrome session used for report capture."""
    try:
        options = webdriver.ChromeOptions()
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        return webdriver.Chrome(options=options)
    except Exception as exc:
        print(f"Unable to create Chrome driver: {exc}")
        return None


def captures(driver, element_xpath, page, total_page):
    """Navigate to one Power BI report page and save a temporary screenshot."""
    try:
        page = int(page)
        total_page = int(total_page)
        if not 1 <= page <= total_page:
            raise ValueError("page must be within the report page range")

        navigation = driver.find_element(
            By.XPATH,
            "//*[@id='embedWrapperID']/div[2]/logo-bar/div/div/div/"
            "logo-bar-navigation/span/a",
        )
        navigation.click()

        page_list = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, '//*[@id="flyoutElement"]/div[1]/div/div/ul')
            )
        )
        page_buttons = WebDriverWait(page_list, 10).until(
            EC.visibility_of_all_elements_located((By.TAG_NAME, "button"))
        )

        target_button = page_buttons[page - 1]
        ActionChains(driver).move_to_element(target_button).click(target_button).perform()

        element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, element_xpath))
        )

        # Power BI can report the element as present before the visual finishes painting.
        time.sleep(2)
        image_binary = element.screenshot_as_png
        image = Image.open(io.BytesIO(image_binary))

        session_id = str(uuid.uuid4())
        directory = os.path.join("images", session_id)
        os.makedirs(directory, exist_ok=True)
        file_path = os.path.join(directory, f"image-{page}.png")
        image.save(file_path)
        return file_path

    except TimeoutException:
        print("Timed out while waiting for the Power BI report to render.")
        return None
    except (IndexError, ValueError) as exc:
        print(f"Invalid report page: {exc}")
        return None
    except Exception as exc:
        print(f"Capture failed: {exc}")
        return None


def count_page(page_source):
    """Extract the number of report pages from Power BI's navigation markup."""
    try:
        parser = etree.HTMLParser()
        tree = etree.parse(StringIO(page_source), parser)
        elements = tree.xpath(
            '//*[@id="embedWrapperID"]/div[2]/logo-bar/div/div/div/'
            'logo-bar-navigation/span/a/span/span[3]'
        )
        return elements[0].text if elements else None
    except Exception as exc:
        print(f"Unable to determine page count: {exc}")
        return None


def find_target_elements(page_source):
    """Return the report visual container when a Power BI report has loaded."""
    if not page_source:
        return None

    try:
        soup = BeautifulSoup(page_source, "html.parser")
        return soup.find(
            "div",
            {"class": "visualContainerHost visualContainerOutOfFocus"},
        )
    except Exception as exc:
        print(f"Unable to inspect report markup: {exc}")
        return None


def get_page_source(driver):
    """Wait briefly for client-side rendering, then return the current DOM."""
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        time.sleep(2)
        return driver.page_source
    except Exception as exc:
        print(f"Unable to read page source: {exc}")
        return None
