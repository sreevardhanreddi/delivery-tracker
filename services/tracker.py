from concurrent.futures import ThreadPoolExecutor

import bs4
import requests
from loguru import logger


def bd_track(num: str) -> tuple[list[dict], str] | tuple[None, None]:
    try:
        res = requests.get(
            "https://www.bluedart.com/trackdartresultthirdparty?trackFor=0&trackNo={}".format(
                num
            )
        )
        if res.status_code != 200:
            logger.error("Error in fetching the page")
            return None, None
        soup = bs4.BeautifulSoup(res.text, "html.parser")
        status_events = soup.find("div", id="SCAN{}".format(num))
        if status_events is None:
            logger.error("Error in fetching the status")
            return None, None

        # convert the table to a list of dictionaries
        status = []
        for row in status_events.find_all("tr"):

            cells = row.find_all("td")
            if len(cells) != 4:
                continue

            status.append(
                {
                    "location": cells[0].text.strip(),
                    "details": cells[1].text.strip(),
                    "date": cells[2].text.strip(),
                    "time": cells[3].text.strip(),
                }
            )

        return status, "bluedart"
    except Exception as e:
        logger.error(f"An error occurred fetching from bluedart: {e}")
        return None, None


def dtdc_track(num: str) -> tuple[list[dict], str] | tuple[None, None]:
    try:
        # Define the URL and headers
        url = "https://trackcom.dtdc.com/ctbs-tracking/customerInterface.tr?submitName=getLoadMovementDetails&cnNo={}".format(
            num
        )
        headers = {
            "Accept": "text/javascript, text/html, application/xml, text/xml, */*",
            "Accept-Language": "en-US,en;q=0.9,zh-TW;q=0.8,zh;q=0.7",
            "Connection": "keep-alive",
            "Content-Length": "0",
            "Content-type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Origin": "https://trackcom.dtdc.com",
            "Referer": f"https://trackcom.dtdc.com/ctbs-tracking/customerInterface.tr?submitName=showCITrackingDetails&cnNo={num}&cType=Consignment",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "X-Prototype-Version": "1.7.3",
            "X-Requested-With": "XMLHttpRequest",
            "sec-ch-ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"macOS"',
        }

        # Make the POST request
        res = requests.post(url, headers=headers, verify=False)
        if res.status_code != 200:
            logger.error(
                f"Failed to fetch data from DTDC API. Status code: {res.status_code}"
            )
            return None, None

        data = res.json()
        # Convert the table to a list of dictionaries
        status = []
        for item in data:
            if item.get("activityType") == "No Data available":
                return None, None

            status.append(
                {
                    "location": "{}".format(item.get("dest") or item.get("origin", "")),
                    "details": "{}".format(
                        # item.get("deliveryStatus"),
                        item.get("activityType"),
                    ),
                    "date": "{}".format(item.get("dateWithNoSuffix")),
                    "time": "{}".format(item.get("time")),
                }
            )

        return status, "dtdc"

    except Exception as e:
        logger.error(f"An error occurred fetching from dtdc: {e}")
        return None, None


def track_all(num: str):
    status = None, None
    tasks = [bd_track, dtdc_track]
    with ThreadPoolExecutor(max_workers=len(tasks)) as executor:
        futures = [executor.submit(task, num) for task in tasks]
        for future in futures:
            events, service = future.result()
            if service is not None:
                status = events, service

    return status
