import sys
import time

from loguru import logger
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


def get_driver():
    """Setup Chrome driver with necessary options"""
    chrome_options = Options()
    # chrome_options.add_argument("--headless")  # Run in headless mode (optional)
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument(
        "--ignore-certificate-errors"
    )  # Disable certificate errors
    chrome_options.add_argument("--auto-open-devtools-for-tabs")
    chrome_options.add_argument(
        "--disable-third-party-cookies"
    )  # This is deprecated and unreliable

    # If running in Docker, you might need to add these options
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")

    service = Service()
    if sys.platform == "linux":
        chrome_options.add_argument("--headless")  # Run in headless mode (optional)
        service = Service("/usr/local/bin/chromedriver")
        chrome_options.binary_location = "/opt/chrome/chrome"

    return webdriver.Chrome(service=service, options=chrome_options)


def test_selenium():
    driver = get_driver()
    driver.get("https://www.google.com")
    time.sleep(5)
    driver.quit()


def dtdc_track_selenium_srv(tracking_number: str):
    driver = get_driver()

    try:
        # Wait for the form to load
        wait = WebDriverWait(driver, 10)

        logger.info("Fetching dtdc.in")
        driver.get("https://dtdc.in/trace.asp")
        logger.info("Loaded dtdc.in")
        logger.info("add tracking number")
        driver.find_element(By.ID, "trackingNumber").send_keys(tracking_number)

        # Switch to captcha iframe (adjust frame name/ID as needed)
        logger.info("Waiting for captcha iframe")
        captcha_iframe = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "iframe[name^='a-']"))
        )
        driver.switch_to.frame(captcha_iframe)

        # Click the captcha checkbox
        captcha_checkbox = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".recaptcha-checkbox-border"))
        )
        captcha_checkbox.click()
        logger.info("Clicked captcha checkbox")

        logger.info("Waiting for captcha to be solved for 5 seconds")
        time.sleep(5)
        # close any alerts
        try:
            logger.info("Closing any alerts")
            alert = driver.switch_to.alert
            alert.accept()
        except:
            pass

        logger.info("Switching back to default content")
        # Switch back to default content
        driver.switch_to.default_content()

        # Click the submit button
        submit_button = wait.until(
            EC.element_to_be_clickable(
                (
                    By.CSS_SELECTOR,
                    "#trackingHomeForm > div > div > div.row.pt-2.justify-content-between > div > div > div.form-group > input",
                )
            )
        )
        submit_button.click()
        logger.info("Clicked submit button")

        logger.info("Waiting for results to load")
        # Wait a moment for captcha verification
        time.sleep(5)

        # Get the page source
        page_source = driver.page_source
        return page_source

    except Exception as e:
        logger.error(f"An error occurred fetching from dtdc.in : {e}")

    finally:
        driver.quit()

    return ""
