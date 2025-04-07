import json
import time

from loguru import logger
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


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
    chrome_options.set_capability(
        "goog:loggingPrefs", {"performance": "ALL", "browser": "ALL"}
    )

    try:
        logger.info("Launching browser...")
        driver = webdriver.Chrome(options=chrome_options)
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
