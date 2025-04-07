import sys
import time

from loguru import logger
from playwright.sync_api import sync_playwright


def dtdc_track_srv(tracking_number: str):
    link = "https://www.dtdc.in/trace.asp"

    query = "given the tracking number {}, provide a json response you receive directly, no yapping, thank you".format(
        tracking_number
    )
    with sync_playwright() as p:
        logger.info("Launching browser...")
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto(link, wait_until="load")

        # click on the chatbot icon and wait for it to appear
        chatbot_icon = page.locator("#small-chat")
        chatbot_icon.click()

        # Wait for the iframe to be available and switch to it
        iframe = page.frame_locator("iframe#the_iframe")
        # iframe.wait_for_selector(".chat-input", state="visible")

        # Now interact with elements inside the iframe
        logger.info("Waiting for iframe to load...")
        text_area = iframe.locator(".chat-input")
        text_area.fill(query)

        # Press Enter to send the message
        logger.info("Sending message...")
        text_area.press("Enter")

        # Wait for all network requests to become idle
        logger.info("Waiting for network idle...")
        page.wait_for_load_state("networkidle", timeout=30000)

        # Wait a bit more to ensure the response is fully loaded
        page.wait_for_timeout(1000)

        bot_responses = iframe.locator(".bot-block")
        last_bot_response = bot_responses.last
        bot_response_text = last_bot_response.inner_text()
        logger.info("Bot response: {}".format(bot_response_text))

        browser.close()
        return bot_response_text
