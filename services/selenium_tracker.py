import json
import os
import subprocess
import time

from loguru import logger
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


def find_chromedriver():
    """Find the ChromeDriver executable path."""
    # Check common locations
    possible_paths = [
        "/usr/bin/chromedriver",
        "/usr/local/bin/chromedriver",
        "/usr/lib/chromium-browser/chromedriver",
        "/usr/lib/chromium/chromedriver",
        "/usr/lib/chromium-driver/chromedriver",
    ]

    # Check environment variable
    if os.environ.get("CHROMEDRIVER_PATH"):
        return os.environ.get("CHROMEDRIVER_PATH")

    # Check which command
    try:
        result = subprocess.run(
            ["which", "chromedriver"], capture_output=True, text=True, check=False
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except Exception:
        pass

    # Check possible paths
    for path in possible_paths:
        if os.path.exists(path) and os.access(path, os.X_OK):
            return path

    # If not found, return None
    return None


def wait_for_network_idle(driver, timeout=30):
    """Wait for network requests to become idle, including streaming requests."""
    logger.info("Waiting for network requests to complete...")
    start_time = time.time()
    last_request_time = start_time
    active_requests = set()

    while time.time() - start_time < timeout:
        # Get the performance logs
        logs = driver.get_log("performance")

        for entry in logs:
            try:
                log_data = json.loads(entry["message"])["message"]

                # Track request IDs for streaming
                if "Network.requestWillBeSent" in str(log_data):
                    request_id = log_data.get("params", {}).get("requestId")
                    if request_id:
                        active_requests.add(request_id)

                # Remove completed requests
                if "Network.loadingFinished" in str(log_data):
                    request_id = log_data.get("params", {}).get("requestId")
                    if request_id in active_requests:
                        active_requests.remove(request_id)
                        last_request_time = time.time()

                # Check for streaming responses
                if "Network.dataReceived" in str(log_data):
                    last_request_time = time.time()

            except Exception as e:
                logger.debug(f"Error parsing log entry: {e}")
                continue

        # If no active requests and no new data for 2 seconds, consider network idle
        if len(active_requests) == 0 and time.time() - last_request_time > 2:
            logger.info("Network is idle - no active requests")
            return True

        time.sleep(0.5)

    logger.warning(
        f"Timeout waiting for network idle. Active requests: {len(active_requests)}"
    )
    return False


def dtdc_track_srv(tracking_number: str):
    link = "https://www.dtdc.in/trace.asp"
    query = "given the tracking number {}, provide a json response you receive directly, no yapping, thank you".format(
        tracking_number
    )

    # Configure Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-software-rasterizer")
    chrome_options.add_argument("--window-size=1920,1080")

    # Use Chromium binary if available
    if os.environ.get("CHROME_BIN"):
        chrome_options.binary_location = os.environ.get("CHROME_BIN")
        logger.info(f"Using Chromium binary at: {os.environ.get('CHROME_BIN')}")

    chrome_options.set_capability(
        "goog:loggingPrefs", {"performance": "ALL", "browser": "ALL"}
    )

    try:
        logger.info("Launching browser...")

        # Find ChromeDriver path
        chromedriver_path = find_chromedriver()
        if chromedriver_path:
            logger.info(f"Using ChromeDriver at: {chromedriver_path}")
            service = Service(executable_path=chromedriver_path)
        else:
            logger.warning("ChromeDriver path not found, using default Service")
            service = Service()

        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.get(link)

        # Wait for and click the chatbot icon
        logger.info("Waiting for chatbot icon...")
        chatbot_icon = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "small-chat"))
        )
        chatbot_icon.click()

        # Wait for and switch to the iframe
        logger.info("Waiting for iframe...")
        iframe = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "the_iframe"))
        )
        driver.switch_to.frame(iframe)

        # Find and fill the text area
        logger.info("Finding text area...")
        text_area = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "chat-input"))
        )
        text_area.send_keys(query)
        text_area.send_keys("\n")

        # Wait for network requests to complete, including streaming
        wait_for_network_idle(driver)

        # Additional wait for the response to be visible and stable
        logger.info("Waiting for bot response to be visible and stable...")
        last_response = None
        stable_count = 0

        while stable_count < 3:  # Wait for response to be stable for 3 checks
            bot_responses = driver.find_elements(By.CLASS_NAME, "bot-block")
            if bot_responses:
                current_response = bot_responses[-1].text
                if current_response == last_response:
                    stable_count += 1
                else:
                    stable_count = 0
                last_response = current_response
            time.sleep(0.5)

        # Get the final bot response
        bot_responses = driver.find_elements(By.CLASS_NAME, "bot-block")
        if bot_responses:
            bot_response_text = bot_responses[-1].text
            logger.info("Bot response: {}".format(bot_response_text))
        else:
            bot_response_text = "No response received"
            logger.warning("No bot response found")

        driver.quit()
        return bot_response_text

    except Exception as e:
        logger.error(f"Error in DTDC tracking: {str(e)}")
        if "driver" in locals():
            driver.quit()
        return None


def ekart_track_srv(tracking_number: str):
    """Track Ekart shipment using Selenium to handle CSRF protection."""
    link = (
        f"https://ekartlogistics.com/ekartlogistics-web/shipmenttrack/{tracking_number}"
    )

    # Configure Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-software-rasterizer")
    chrome_options.add_argument("--window-size=1920,1080")

    # Use Chromium binary if available
    if os.environ.get("CHROME_BIN"):
        chrome_options.binary_location = os.environ.get("CHROME_BIN")
        logger.info(f"Using Chromium binary at: {os.environ.get('CHROME_BIN')}")

    chrome_options.set_capability(
        "goog:loggingPrefs", {"performance": "ALL", "browser": "ALL"}
    )

    try:
        logger.info(f"Launching browser for Ekart tracking: {tracking_number}")

        # Find ChromeDriver path
        chromedriver_path = find_chromedriver()
        if chromedriver_path:
            logger.info(f"Using ChromeDriver at: {chromedriver_path}")
            service = Service(executable_path=chromedriver_path)
        else:
            logger.warning("ChromeDriver path not found, using default Service")
            service = Service()

        driver = webdriver.Chrome(service=service, options=chrome_options)

        # Enable CDP Network domain so we can read response bodies.
        # (Selenium's performance logs provide requestId; CDP fetches body.)
        try:
            driver.execute_cdp_cmd("Network.enable", {})
        except Exception as e:
            logger.debug(f"Could not enable CDP Network domain: {e}")

        driver.get(link)

        # Wait for the page to load and tracking data to appear
        logger.info("Waiting for tracking data...")
        time.sleep(3)  # Give time for initial load

        api_url = "https://ekartlogistics.com/ekartlogistics-web-routes-api/ekartlogistics-web-proxy/trackings/v2"

        # Try to capture the JSON directly from the network request the page makes.
        logger.info("Waiting for Ekart API response...")
        api_request_id = None
        start_time = time.time()
        while time.time() - start_time < 20:
            try:
                logs = driver.get_log("performance")
            except Exception as e:
                logger.debug(f"Could not read performance logs: {e}")
                logs = []

            for entry in logs:
                try:
                    message = json.loads(entry.get("message", "{}")).get("message", {})
                    method = message.get("method")
                    params = message.get("params", {})

                    if method == "Network.responseReceived":
                        response = params.get("response", {})
                        url = response.get("url")
                        if url == api_url:
                            api_request_id = params.get("requestId")
                    # Sometimes the URL is easiest to capture at request time.
                    if method == "Network.requestWillBeSent" and not api_request_id:
                        request = params.get("request", {})
                        if request.get("url") == api_url:
                            api_request_id = params.get("requestId")
                except Exception:
                    continue

            if api_request_id:
                try:
                    body = driver.execute_cdp_cmd(
                        "Network.getResponseBody", {"requestId": api_request_id}
                    )
                    response_text = body.get("body")
                    if body.get("base64Encoded") and response_text:
                        import base64

                        response_text = base64.b64decode(response_text).decode("utf-8")

                    if response_text:
                        logger.info("Captured Ekart API JSON from network")
                        driver.quit()
                        return response_text
                except Exception as e:
                    # The body may not be available yet; keep polling.
                    logger.debug(f"Ekart API response body not ready yet: {e}")

            time.sleep(0.5)

    except Exception as e:
        logger.error(f"Error in Ekart tracking: {str(e)}")
        if "driver" in locals():
            driver.quit()
        return None


def xpressbees_track_srv(tracking_number: str):
    """Track XpressBees shipment using Selenium and capture XHR responses."""

    # ── Tuneable flags ────────────────────────────────────────────────────────
    HEADLESS = True
    PAGE_IDLE_TIMEOUT = 15  # seconds to wait for page load network idle
    ALTCHA_WAIT_TIMEOUT = 20  # seconds to wait for ALTCHA to reach "verified"
    POST_ALTCHA_IDLE_TIMEOUT = 8  # seconds to wait for post-verification idle
    SEARCH_BTN_TIMEOUT = 8  # seconds to wait for Search button to be clickable
    API_IDLE_TIMEOUT = 10  # seconds to wait for tracking API network idle
    API_CAPTURE_TIMEOUT = 15  # seconds to poll for the captured API response bodies
    # ─────────────────────────────────────────────────────────────────────────

    link = f"https://www.xpressbees.com/shipment/tracking?awbNo={tracking_number}"

    chrome_options = Options()
    if HEADLESS:
        chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-software-rasterizer")
    chrome_options.add_argument("--window-size=1920,1080")

    if os.environ.get("CHROME_BIN"):
        chrome_options.binary_location = os.environ.get("CHROME_BIN")
        logger.info(f"Using Chromium binary at: {os.environ.get('CHROME_BIN')}")

    chrome_options.set_capability(
        "goog:loggingPrefs", {"performance": "ALL", "browser": "ALL"}
    )

    try:
        logger.info(f"Launching browser for XpressBees tracking: {tracking_number}")

        chromedriver_path = find_chromedriver()
        if chromedriver_path:
            logger.info(f"Using ChromeDriver at: {chromedriver_path}")
            service = Service(executable_path=chromedriver_path)
        else:
            logger.warning("ChromeDriver path not found, using default Service")
            service = Service()

        driver = webdriver.Chrome(service=service, options=chrome_options)
        try:
            driver.execute_cdp_cmd("Network.enable", {})
        except Exception as e:
            logger.debug(f"Could not enable CDP Network domain for XpressBees: {e}")

        driver.get(link)

        # Step 1: wait for the page to fully load and initial network requests to idle.
        logger.info("XpressBees: waiting for page load + network idle...")
        wait_for_network_idle(driver, timeout=PAGE_IDLE_TIMEOUT)

        # Step 2: click the checkbox input inside altcha-widget > .altcha-checkbox.
        # The altcha-widget is a Vue component with light DOM (no shadow root).
        logger.info("XpressBees: clicking .altcha-checkbox input...")
        try:
            altcha_input = WebDriverWait(driver, ALTCHA_WAIT_TIMEOUT).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "altcha-widget .altcha-checkbox input")
                )
            )
            driver.execute_script("arguments[0].click();", altcha_input)
            logger.info("XpressBees: .altcha-checkbox input clicked")
        except Exception as e:
            logger.warning(f"XpressBees: could not click .altcha-checkbox input: {e}")

        # Step 3: wait for ALTCHA to finish verifying (data-state becomes "verified").
        logger.info("XpressBees: waiting for altcha verification to complete...")
        try:
            WebDriverWait(driver, ALTCHA_WAIT_TIMEOUT).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "altcha-widget .altcha[data-state='verified']")
                )
            )
            logger.info("XpressBees: ALTCHA verified")
        except Exception as e:
            logger.warning(
                f"XpressBees: timed out waiting for ALTCHA verified state: {e}"
            )
        wait_for_network_idle(driver, timeout=POST_ALTCHA_IDLE_TIMEOUT)

        # Step 4: click the Search button (matched by text — multiple submit buttons exist).
        # Start collecting performance logs BEFORE clicking so the Network.responseReceived
        # event for /api/tracking is not drained by a wait_for_network_idle call.
        driver.get_log("performance")  # flush stale pre-click entries
        logger.info("XpressBees: clicking Search button...")
        try:
            search_button = WebDriverWait(driver, SEARCH_BTN_TIMEOUT).until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//button[normalize-space(.)='Search']")
                )
            )
            driver.execute_script("arguments[0].click();", search_button)
            logger.info("XpressBees: Search button clicked")
        except Exception as e:
            logger.warning(f"XpressBees: could not click Search button: {e}")

        # Step 5: poll CDP logs directly for the POST /api/tracking response.
        # (Intentionally no wait_for_network_idle here — it consumes the log entries.)
        tracking_api_url = "https://www.xpressbees.com/api/tracking"
        api_request_id = None
        api_response_text = None

        start_time = time.time()
        while time.time() - start_time < API_CAPTURE_TIMEOUT:
            try:
                logs = driver.get_log("performance")
            except Exception as e:
                logger.debug(f"Could not read XpressBees performance logs: {e}")
                logs = []

            for entry in logs:
                try:
                    message = json.loads(entry.get("message", "{}")).get("message", {})
                    if message.get("method") != "Network.responseReceived":
                        continue
                    params = message.get("params", {})
                    response = params.get("response", {})
                    if response.get("url") == tracking_api_url and not api_request_id:
                        api_request_id = params.get("requestId")
                except Exception:
                    continue

            if api_request_id and not api_response_text:
                try:
                    body = driver.execute_cdp_cmd(
                        "Network.getResponseBody", {"requestId": api_request_id}
                    )
                    text = body.get("body")
                    if body.get("base64Encoded") and text:
                        import base64

                        text = base64.b64decode(text).decode("utf-8")
                    if text:
                        api_response_text = text
                except Exception as e:
                    logger.debug(f"XpressBees POST response body not ready yet: {e}")

            if api_response_text:
                logger.info("Captured XpressBees POST tracking JSON from network")
                logger.debug(f"XpressBees post_response: {api_response_text}")
                driver.quit()
                return api_response_text

            time.sleep(0.5)

        logger.warning(
            "XpressBees: API response not captured, falling back to page HTML"
        )
        html = driver.page_source
        driver.quit()
        return html

    except Exception as e:
        logger.error(f"Error in XpressBees tracking: {str(e)}")
        if "driver" in locals():
            driver.quit()
        return None
