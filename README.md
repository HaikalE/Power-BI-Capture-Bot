# Power BI Capture Bot

Telegram bot that opens a public Power BI report with headless Chrome, discovers report pages, captures selected report visuals, and returns screenshots through Telegram.

The project combines browser automation and chat-bot interaction to automate a repetitive reporting workflow.

## How it works

```text
/capture <Power BI public URL>
            |
            v
Telegram bot
            |
            v
Selenium / headless Chrome
            |
            v
Power BI report navigation
            |
            v
page screenshot
            |
            v
Telegram image response
```

## Stack

- Python
- `python-telegram-bot`
- Selenium
- Chrome / ChromeDriver
- Pillow
- BeautifulSoup
- lxml

## Setup

Install the Python dependencies used by the project and provide the Telegram token through an environment variable:

```bash
export TELEGRAM_BOT_TOKEN="your-token"
python index.py
```

Then send the bot:

```text
/capture https://app.powerbi.com/view?...
```

The bot opens the report, reads the available report pages, and returns buttons for capturing one page or all available pages.

## Security notes

Secrets must not be committed to the repository. The bot token is loaded from `TELEGRAM_BOT_TOKEN`; `.env` files are excluded by `.gitignore`.

A token was present in an earlier repository revision. Removing it from the current source does not remove it from Git history, so any credential that has ever been committed should be revoked and replaced before the project is used again.

The bot accepts public Power BI report URLs only. A production deployment should also add stronger URL validation, resource/time limits, isolated browser execution, concurrency controls, and abuse protection before processing untrusted requests.

## Engineering notes

The current capture logic depends on Power BI DOM structure and XPath selectors. Those selectors can break when the third-party interface changes. A more robust revision would isolate report-navigation selectors behind a dedicated adapter and add browser-level integration tests.

## Author

Muhammad Haikal Rahman  
[GitHub](https://github.com/HaikalE) · [Portfolio](https://haikale.github.io)
