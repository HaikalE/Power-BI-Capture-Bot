from selenium.common.exceptions import TimeoutException
import uuid
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains

from PIL import Image
import io
from lxml import etree
from selenium.webdriver.support.ui import WebDriverWait
from io import StringIO
import os 
import time
from bs4 import BeautifulSoup
from selenium.webdriver.support import expected_conditions as EC

def create_driver():
    try:
        options = webdriver.ChromeOptions()
        options.add_experimental_option("detach", True)
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        driver = webdriver.Chrome(options=options)
        return driver

    except Exception as e:
        print("Error occurred while creating driver:", e)
        return None

def captures(driver, element_xpath, page, total_page):
    try:
        # Check if the page is within the valid range
        page = int(page)
        total_page = int(total_page)
        if not 1 <= page <= total_page:
            print("Page number is out of range.")
            return 
        
        # Find the element for navigating to pages
        middle_text_pages = driver.find_element(By.XPATH, "//*[@id='embedWrapperID']/div[2]/logo-bar/div/div/div/logo-bar-navigation/span/a")
        
        # Click the navigation element
        middle_text_pages.click()
        print("Clicked on the element successfully!_Y",driver)

        # Wait for the specific page button to be clickable
        # page_button_xpath = f"//button[contains(text(), 'Page {page}')]"

        ul_element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="flyoutElement"]/div[1]/div/div/ul')))

        # Find all the button elements within the ul element
        buttons = WebDriverWait(ul_element, 10).until(EC.visibility_of_all_elements_located((By.TAG_NAME, "button")))
        
        # Select the button based on the page index (assuming the page index starts from 1)
        target_button = buttons[page - 1]  # Adjust the index since Python lists are 0-indexed
        print(target_button)
        # Scroll the button into view
        
        # Click the target button
        #target_button.click()
        ActionChains(driver).move_to_element(target_button).click(target_button).perform()
        #page_button = WebDriverWait(driver, 3).until(EC.element_to_be_clickable((By.XPATH, page_button_xpath)))
        
        # Click the page button
        #page_button.click()
        print(f"Clicked on Page {page} successfully!")
        
        # Find the element to capture
        element = driver.find_element(By.XPATH, element_xpath)
        
        # Take a screenshot of the found element
        time.sleep(5)  # Add a short delay for element rendering
        image_binary = element.screenshot_as_png 

        img = Image.open(io.BytesIO(image_binary))
        # Generate a unique session ID
        session_id = str(uuid.uuid4())
        directory = f"images/{session_id}"
        os.makedirs(directory, exist_ok=True)

        # Save the screenshot with a unique file name
        file_path = os.path.join(directory, f"image-{page}.png")
        img.save(file_path)
        print("Screenshot saved successfully! ")
        return (file_path)
    except TimeoutException:
        print("Timeout occurred while capturing the image.")
        return None
    except Exception as e:
        print("Error occurred:", e)
        return None

def count_page(page_source):
    try:
        parser = etree.HTMLParser()
        tree = etree.parse(StringIO(page_source), parser)
        elements = tree.xpath("""//*[@id="embedWrapperID"]/div[2]/logo-bar/div/div/div/logo-bar-navigation/span/a/span/span[3]""")
        return elements[0].text
    except Exception as e:
        print("Error occurred:", e)
        return None

def find_target_elements(page_source):
    """Scrape desired elements using BeautifulSoup"""
    try:
        if page_source is None:
            return None

        # Parse the page source with BeautifulSoup
        soup = BeautifulSoup(page_source, 'html.parser')

        # Find all desired elements
        target_elements = soup.find('div', {'class': 'visualContainerHost visualContainerOutOfFocus'})

        return target_elements
    
    except Exception as e:
        print("An error occurred while scraping the page:", e)
        return None

def find_target_elements(page_source):
    """Scrape desired elements using BeautifulSoup"""
    try:
        if page_source is None:
            return None

        # Parse the page source with BeautifulSoup
        soup = BeautifulSoup(page_source, 'html.parser')
        
        # Find all desired elements
        target_elements = soup.find('div', {'class': 'visualContainerHost visualContainerOutOfFocus'})
        
        return target_elements
        
    except Exception as e:
        print("Error occurred:", e)
        return None

def get_xpath(element):
    """Get the XPath of a BeautifulSoup element"""
    xpath = ''
    components = []
    while element.parent:
        siblings = element.parent.find_all(element.name, recursive=False)
        components.append(
            element.name + '[' + str(siblings.index(element) + 1) + ']'
        )
        element = element.parent
    components.reverse()
    xpath = '/'.join(components)
    return '/' + xpath

def get_page_source(driver):
    """Get the page source using Selenium"""
    try:
        time.sleep(5)
        # Get the page source
        page_source = driver.page_source
        
        return page_source
        
    except Exception as e:
        print("Error occurred:", e)
        return None


if __name__ == "__main__":
    #url = 'https://app.powerbi.com/view?r=eyJrIjoiNTM0Yjc2YmUtYTc3Yy00YzAzLWJjYzktNzIxOGUyOGIwYmZjIiwidCI6ImZjNzQzMDc1LTkzZWQtNGE1Yy04MmMwLWNhNWVhYzkxNDIyMCIsImMiOjEwfQ%3D%3D'
    url='https://app.powerbi.com/view?r=eyJrIjoiYmI2NjkxNGQtNjk2YS00YTNiLTg4MWMtNjg2ZGZlYzM4OWM3IiwidCI6ImZjNzQzMDc1LTkzZWQtNGE1Yy04MmMwLWNhNWVhYzkxNDIyMCIsImMiOjEwfQ%3D%3D'
    element_xpath ='/html[1]/body[1]/div[1]/report-embed[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/exploration-container[1]/div[1]/div[1]/docking-container[1]/div[1]/div[1]/div[1]/div[1]/exploration-host[1]/div[1]/div[1]/exploration[1]/div[1]/explore-canvas[1]/div[1]/div[2]/div[1]/div[2]/div[2]'
    driver = create_driver()
    if driver:
        driver.get(url)
        page_source = get_page_source(driver)
        target_elements = find_target_elements(page_source)
        if target_elements:
            total_page=count_page(page_source)
            print(captures(driver,element_xpath,8,total_page))
        else:
            print("Failed to get page source.")
        driver.quit()
