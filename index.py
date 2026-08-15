import logging
import os
import re
import shutil

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

import capture_powerbi as capture

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

page_source = None
driver = None
buttons = []

POWERBI_URL_PATTERN = re.compile(
    r"^https://app\.powerbi\.com/view\?.+",
    re.IGNORECASE,
)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Power BI Capture Bot\n\n"
        "Use /capture <public Power BI URL> to open a report and choose a page to capture. "
        "The bot can capture one page or iterate over all pages exposed by the report navigation."
    )


def is_report_loaded() -> bool:
    global page_source, driver
    if driver is None:
        return False
    page_source = capture.get_page_source(driver)
    return capture.find_target_elements(page_source) is not None


async def send_page_buttons(update: Update, total_page: int) -> None:
    global driver, buttons

    navigation = driver.find_element(
        By.XPATH,
        "//*[@id='embedWrapperID']/div[2]/logo-bar/div/div/div/logo-bar-navigation/span/a",
    )
    navigation.click()

    list_element = WebDriverWait(driver, 5).until(
        EC.presence_of_element_located(
            (By.XPATH, '//*[@id="flyoutElement"]/div[1]/div/div/ul')
        )
    )
    buttons = WebDriverWait(list_element, 5).until(
        EC.visibility_of_all_elements_located((By.TAG_NAME, "button"))
    )

    rows = [
        [
            InlineKeyboardButton(
                "All pages",
                callback_data=f"page_0_{total_page}_All pages",
            )
        ]
    ]
    for page_number, button in enumerate(buttons, start=1):
        label = button.text or f"Page {page_number}"
        rows.append(
            [
                InlineKeyboardButton(
                    label,
                    callback_data=f"page_{page_number}_{total_page}_{label}",
                )
            ]
        )

    await update.message.reply_text(
        "Select a report page:",
        reply_markup=InlineKeyboardMarkup(rows),
    )
    navigation.click()


async def capture_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global driver

    if not context.args:
        await update.message.reply_text("Usage: /capture <public Power BI URL>")
        return

    url = context.args[0].strip()
    if not POWERBI_URL_PATTERN.match(url):
        await update.message.reply_text("Please provide a public app.powerbi.com/view URL.")
        return

    driver = capture.create_driver()
    if driver is None:
        await update.message.reply_text("Unable to start the browser session.")
        return

    await update.message.reply_text("Opening the report...")
    driver.get(url)

    if not is_report_loaded():
        driver.quit()
        driver = None
        await update.message.reply_text("The report could not be loaded or recognized.")
        return

    total_page = int(capture.count_page(page_source))
    await send_page_buttons(update, total_page)


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global driver, buttons

    query = update.callback_query
    await query.answer()

    if driver is None or not driver.service.is_connectable():
        await query.message.reply_text("Browser session expired. Run /capture again.")
        return

    element_xpath = (
        "/html[1]/body[1]/div[1]/report-embed[1]/div[1]/div[1]/div[1]/div[1]/"
        "div[1]/div[1]/exploration-container[1]/div[1]/div[1]/docking-container[1]/"
        "div[1]/div[1]/div[1]/div[1]/exploration-host[1]/div[1]/div[1]/exploration[1]/"
        "div[1]/explore-canvas[1]/div[1]/div[2]/div[1]/div[2]/div[2]"
    )

    try:
        page_data = query.data.split("_", 3)[1:]
        page = int(page_data[0])
        total_page = int(page_data[1])
        label = page_data[2]

        pages = range(1, total_page + 1) if page == 0 else [page]
        for page_number in pages:
            page_label = (
                buttons[page_number - 1].text
                if page == 0 and page_number - 1 < len(buttons)
                else label
            )
            await query.message.reply_text(f"Capturing {page_label}...")

            image_path = capture.captures(
                driver,
                element_xpath,
                page_number,
                total_page,
            )
            if not image_path:
                await query.message.reply_text(f"Failed to capture {page_label}.")
                continue

            try:
                with open(image_path, "rb") as image_file:
                    await context.bot.send_photo(
                        chat_id=update.effective_chat.id,
                        photo=image_file,
                    )
            finally:
                shutil.rmtree(os.path.dirname(image_path), ignore_errors=True)

    except TimeoutException:
        logger.exception("Timed out while capturing report page")
        await query.message.reply_text("The report timed out while rendering.")
    except Exception:
        logger.exception("Unexpected capture error")
        await query.message.reply_text("An unexpected error occurred while capturing the report.")
    finally:
        if driver is not None:
            driver.quit()
            driver = None


def main() -> None:
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN environment variable is required")

    application = Application.builder().token(token).build()
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("capture", capture_command))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
