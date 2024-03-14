
import logging

import requests
import re

import capture_powerbi_NEW as capture

import os 

from telegram import ForceReply, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, CallbackQueryHandler
from selenium.common.exceptions import TimeoutException
from selenium import webdriver
from selenium.webdriver.common.by import By
from PIL import Image
import io
import shutil

from lxml import etree
from selenium.webdriver.support.ui import WebDriverWait
import time
from selenium.webdriver.support import expected_conditions as EC

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# Define a few command handlers. These usually take the two arguments update and
# context.

page_source = None
driver = None
buttons = []

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message explaining how to use the bot."""
    message = (
        "Welcome to the Power BI Capture Bot!\n"
        "To capture a Power BI page, use the /capture command and send the URL for Power BI.\n"
        "You can then select to capture all pages or a specific page.\n"
        "For capturing all pages, the bot will capture each page separately.\n"
        "For capturing a specific page, you will be provided with options to select the page.\n"
        "Enjoy capturing your Power BI pages!"
    )
    await update.message.reply_text(message)

# async def capture_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     """Prompt the user to input the URL for Power BI."""
#     message = (
#         "Please send the URL for Power BI."
#     )
#     await update.message.reply_text(message, reply_markup=ForceReply())

def is_url_valid(url):
    global page_source
    global driver
    page_source = capture.get_page_source(driver)
    target_elements = capture.find_target_elements(page_source)
    if (target_elements) :
        return True
    else :
        return False 
async def send_page_buttons(update: Update, total_page: int) -> None:
    global driver
    global buttons
    buttons_label=[]
    # Add an "All" option
    #buttons.append([all_button])
    """Send buttons for each page."""
    # buttons = [
    #     [InlineKeyboardButton(f"Page {page}", callback_data=f"page_{page}_{total_page}")] 
    #     for page in range(1, total_page + 1)
    # ]
    # Find the element for navigating to pages
    middle_text_pages = driver.find_element(By.XPATH, "//*[@id='embedWrapperID']/div[2]/logo-bar/div/div/div/logo-bar-navigation/span/a")
    
    # Click the navigation element
    middle_text_pages.click()
    print("Clicked on the element successfully!")
    ul_element = WebDriverWait(driver, 2).until(EC.presence_of_element_located((By.XPATH, '//*[@id="flyoutElement"]/div[1]/div/div/ul')))

    # Find all the button elements within the ul element
    buttons = WebDriverWait(ul_element, 3).until(EC.visibility_of_all_elements_located((By.TAG_NAME, "button")))
    # buttons_label = [InlineKeyboardButton(button.text, callback_data=f"page_{button.text}_{total_page}") for button in buttons]
    # reply_markup = InlineKeyboardMarkup([buttons_label])
    buttons_label.append([InlineKeyboardButton("All Page", callback_data=f"page_0_{total_page}_All Page")])
    param=1
    for button in buttons :
        buttons_label.append([InlineKeyboardButton(button.text, callback_data=f"page_{param}_{total_page}_{button.text}")])
        param+=1
    reply_markup = InlineKeyboardMarkup(buttons_label)
    
    await update.message.reply_text("Please select a page:", reply_markup=reply_markup)
    middle_text_pages.click()

async def capture_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global page_source
    global driver
    driver = capture.create_driver()
    """Capture the URL sent by the user and validate it."""
    url = "https://app.powerbi.com/view?r=eyJrIjoiMjU4NzcwNDctNmZmNi00ZjRlLWJmYzItNzU4YmIyZTA3ZWE1IiwidCI6ImZjNzQzMDc1LTkzZWQtNGE1Yy04MmMwLWNhNWVhYzkxNDIyMCIsImMiOjEwfQ%3D%3D"
    # Regular expression to match a URL
    url_pattern = re.compile(
        r"^(http:\/\/www\.|https:\/\/www\.|http:\/\/|https:\/\/)?[a-z0-9]+([\-\.]{1}[a-z0-9]+)*\.[a-z]{2,5}(:[0-9]{1,5})?(\/.*)?$",
        re.IGNORECASE
    )
    if url_pattern.match(url):
        await update.message.reply_text("Please wait while we process your request...")
        # URL is valid, do something with it
        driver.get(url)
        if driver:
            if(is_url_valid(url)):
                total_page=int(capture.count_page(page_source))
                await send_page_buttons(update, total_page)
            else :
                await update.message.reply_text(f"URL is either not valid or does not belong to the specified power bi website.")
        else :
            await update.message.reply_text("There was an issue with the driver. Please try again later.")
            
    else:
        # URL is not valid
        await update.message.reply_text("Invalid URL. Please provide a valid URL.")

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Echo the user message."""
    await update.message.reply_text(update.message.text)

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global driver 
    global buttons
    element_xpath = '/html[1]/body[1]/div[1]/report-embed[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/exploration-container[1]/div[1]/div[1]/docking-container[1]/div[1]/div[1]/div[1]/div[1]/exploration-host[1]/div[1]/div[1]/exploration[1]/div[1]/explore-canvas[1]/div[1]/div[2]/div[1]/div[2]/div[2]'        
    if (driver.service.is_connectable()):
        try:
            query = update.callback_query
            page_data = query.data.split("_")[1:]  # Extract page number from callback data
            page = int(page_data[0])
            total_page = int(page_data[1])
            label_button = page_data[2]

            if page == 0:  # If "All Page" option is selected
                await query.message.reply_text(f"Capture all pages")
                param=1
                print(buttons)
                for button in buttons:
                    label_button=button.text
                    await query.message.reply_text(f"Capture page - {param}...")
                    image_path = capture.captures(driver, element_xpath, param, total_page)
                    if image_path:
                        await context.bot.send_photo(chat_id=update.effective_chat.id, photo=open(image_path, 'rb'))
                        shutil.rmtree(os.path.dirname(image_path))
                        await query.message.reply_text(f"Here's your capture for page {param}!")
                    else:
                        await query.message.reply_text(f"Failed to capture the image for page {param}.")
                    param+=1
            else:
                await query.message.reply_text(f"Capture page - {label_button}...")
                image_path = capture.captures(driver, element_xpath, page, total_page)
                if image_path:
                    await context.bot.send_photo(chat_id=update.effective_chat.id, photo=open(image_path, 'rb'))
                    shutil.rmtree(os.path.dirname(image_path))
                    await query.message.reply_text(f"Here's your capture for page {label_button}!")
                else:
                    await query.message.reply_text("Failed to capture the image.")
        
        except TimeoutException:
            print("Timeout occurred while capturing the image.")
        except Exception as e:
            print("Error occurred:", e)
        finally:
            driver.quit()  # Quit the driver if finished
    else :
        await update.callback_query.message.edit_text("Session not found. Need to /capture again.")

def main() -> None:
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token("7043417303:AAE-whidG7zSFfsBdmDZ5ANjkVSTo_YV5mw").build()

    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("capture", capture_command))
    # on non command i.e message - echo the message on Telegram
    #application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    # application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & filters.REPLY, capture_url))
    application.add_handler(CallbackQueryHandler(button_callback))  # Add callback query handler
    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
