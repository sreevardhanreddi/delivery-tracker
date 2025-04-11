import os
import subprocess
import time

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


def test_selenium():
    print("Testing Selenium setup...")

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
        print(f"Using Chromium binary at: {os.environ.get('CHROME_BIN')}")

    try:
        print("Launching browser...")

        # Find ChromeDriver path
        chromedriver_path = find_chromedriver()
        if chromedriver_path:
            print(f"Using ChromeDriver at: {chromedriver_path}")
            service = Service(executable_path=chromedriver_path)
        else:
            print("ChromeDriver path not found, using default Service")
            service = Service()

        driver = webdriver.Chrome(service=service, options=chrome_options)

        print("Navigating to a test page...")
        driver.get("https://www.google.com")

        print("Waiting for page to load...")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "q")))

        print("Page loaded successfully!")
        print(f"Page title: {driver.title}")

        driver.quit()
        print("Selenium test completed successfully!")
        return True
    except Exception as e:
        print(f"Error in Selenium test: {str(e)}")
        if "driver" in locals():
            driver.quit()
        return False


if __name__ == "__main__":
    test_selenium()
