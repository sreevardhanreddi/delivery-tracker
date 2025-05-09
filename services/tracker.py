import json
import re
from concurrent.futures import ThreadPoolExecutor

import bs4
import requests
from loguru import logger

from services.selenium_tracker import dtdc_track_srv
from utils.common import parse_date_time_string

REQUEST_TIMEOUT = 120


def get_common_headers():
    return {
        "accept": "application/json, text/plain, */*",
        "accept-language": "en-US,en;q=0.9,zh-TW;q=0.8,zh;q=0.7",
        "origin": "https://www.google.com",
        "priority": "u=1, i",
        "referer": "https://www.google.com/",
        "sec-ch-ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"macOS"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    }


def bd_track(num: str) -> dict:
    logger.info(f"Tracking {num} with bluedart")
    status = {"events": None, "service": None}
    try:
        headers = {
            **get_common_headers(),
        }
        res = requests.get(
            "https://www.bluedart.com/trackdartresultthirdparty?trackFor=0&trackNo={}".format(
                num
            ),
            headers=headers,
            timeout=REQUEST_TIMEOUT,
        )
        if res.status_code != 200:
            logger.error("Error fetching from bluedart")
            return status
        soup = bs4.BeautifulSoup(res.text, "html.parser")
        status_events = soup.find("div", id="SCAN{}".format(num))
        if status_events is None:
            logger.error("Error fetching the status from bluedart")
            return status

        # convert the table to a list of dictionaries
        events = []
        for row in status_events.find_all("tr"):

            cells = row.find_all("td")
            if len(cells) != 4:
                continue

            date_time = cells[2].text.strip() + " " + cells[3].text.strip()
            date_time = parse_date_time_string(date_time)
            events.append(
                {
                    "location": cells[0].text.strip(),
                    "details": cells[1].text.strip(),
                    # "date": cells[2].text.strip(),
                    # "time": cells[3].text.strip(),
                    "date_time": date_time,
                }
            )
        status["events"] = events
        status["service"] = "bluedart"

    except Exception as e:
        logger.error(f"An error occurred fetching from bluedart: {e}")

    return status


def dtdc_track(num: str) -> dict:
    status = {"events": None, "service": None}
    try:
        # Define the URL and headers
        url = "https://trackcom.dtdc.com/ctbs-tracking/customerInterface.tr?submitName=getLoadMovementDetails&cnNo={}".format(
            num
        )
        headers = {
            **get_common_headers(),
            "origin": "https://trackcom.dtdc.com",
            "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
        }

        # Make the POST request
        res = requests.post(
            url,
            headers=headers,
            verify=False,
            timeout=REQUEST_TIMEOUT,
        )
        if res.status_code != 200:
            logger.error(
                f"Failed to fetch data from DTDC API. Status code: {res.status_code}"
            )
            return status

        data = res.json()
        # Convert the table to a list of dictionaries
        events = []
        for item in data:
            if item.get("activityType") == "No Data available":
                return status

            date_time = item.get("dateWithNoSuffix") + " " + item.get("time")
            date_time = parse_date_time_string(date_time)
            events.append(
                {
                    "location": "{} -> {}".format(
                        item.get("origin", ""), item.get("dest", "")
                    ),
                    "details": "{}".format(
                        # item.get("deliveryStatus"),
                        item.get("activityType"),
                    ),
                    # "date": "{}".format(item.get("dateWithNoSuffix")),
                    # "time": "{}".format(item.get("time")),
                    "date_time": date_time,
                }
            )

        status["events"] = events
        status["service"] = "dtdc"

    except Exception as e:
        logger.error(f"An error occurred fetching from dtdc: {e}")
    return status


def dtdc_track_by_browser(num: str) -> dict:
    logger.info(f"Tracking {num} with dtdc_track_by_browser")
    status = {"events": None, "service": None}
    try:
        response_text = dtdc_track_srv(num)
        try:
            response_text = json.loads(response_text)
        except Exception as e:
            logger.error(error=f"Error parsing JSON: {e}")

        timeline_steps = response_text.get("milestones", [])
        location_details = []
        for item in timeline_steps:
            details = item.get("event", "")
            location = item.get("location", "")
            datetime_text = item.get("date", "")

            parsed_datetime = None
            # Parse datetime
            if datetime_text:
                parsed_datetime = parse_date_time_string(datetime_text)

            parsed_data = {
                "location": location,
                "date_time": parsed_datetime,
                "details": details,
            }
            location_details.append(parsed_data)

        location_details.reverse()
        status["events"] = location_details
        status["service"] = "dtdc"

    except Exception as e:
        logger.error("An error occurred fetching from dtdc", e)
    return status


def ecom_express_track(num: str) -> dict:
    logger.info(f"Tracking {num} with ecom_express_track")
    status = {"events": None, "service": None}
    try:
        json_data = {"awb_field": num}
        headers = {
            **get_common_headers(),
        }
        res = requests.post(
            "https://www.ecomexpress.in/api/track-awb",
            json=json_data,
            headers=headers,
            timeout=REQUEST_TIMEOUT,
        )
        if res.status_code != 200:
            logger.error(
                f"Failed to fetch data from ECOM Express API. Status code: {res.status_code}"
            )
            return status

        data = res.json()
        if res.status_code != 200:
            logger.error("Error fetching from ecom_express")
            return status

        # convert the table to a list of dictionaries
        events = []
        if data.get("status") == "AWB_NOT_FOUND":
            return status
        shipment_status = data.get("result", {}).get("shipment_status", [])
        shipment_status.reverse()
        for item in shipment_status:

            date, time = item.get("added_on").split(" ")
            date_time = item.get("added_on")
            date_time = parse_date_time_string(date_time)
            events.append(
                {
                    "location": "{}".format(item.get("service_center_name", "")),
                    "details": "{}".format(
                        item.get("external_status_desc", "")
                        or item.get("status_name", "")
                    ),
                    # "date": "{}".format(date),
                    # "time": "{}".format(time),
                    "date_time": date_time,
                }
            )

        status["events"] = events
        status["service"] = "ecom_express"

    except Exception as e:
        logger.error(f"An error occurred fetching from ecom_express: {e}")

    return status


def delhivery_track(num: str) -> dict:
    logger.info(f"Tracking {num} with delhivery_track")
    status = {"events": None, "service": None}
    try:
        headers = {
            **get_common_headers(),
            "origin": "https://www.delhivery.com",
            "referer": "https://www.delhivery.com/",
        }

        params = {
            "wbn": num,
        }
        res = requests.get(
            "https://dlv-api.delhivery.com/v3/unified-tracking",
            params=params,
            headers=headers,
            timeout=REQUEST_TIMEOUT,
        )
        if res.status_code != 200:
            logger.error(
                f"Failed to fetch data from Delhivery API. Status code: {res.status_code}"
            )
            return status

        data = res.json()

        if res.status_code != 200:
            logger.error("Error fetching from delhivery")
            return status

        events = []
        if data.get("message") != "Success":
            return status

        tracking_events = data["data"][0]["trackingStates"][-1]

        # delhivery has a different format
        date_time = (
            tracking_events["scans"][-1]["scanDateTime"]
            or data["data"][0]["status"]["statusDateTime"]
        )
        date_time = parse_date_time_string(date_time)
        details = tracking_events["scans"][-1]["scanNslRemark"]
        location = tracking_events["scans"][-1]["cityLocation"]
        events.append(
            {
                "location": location,
                "details": details,
                "date_time": date_time,
            }
        )

        status["events"] = events
        status["service"] = "delhivery"

    except Exception as e:
        logger.error(f"An error occurred fetching from delhivery : {e}")

    return status


def shadow_fax_track(num: str) -> dict:
    logger.info(f"Tracking {num} with shadow_fax_track")
    status = {"events": None, "service": None}
    try:
        headers = {
            **get_common_headers(),
            "authorization": "Token cePcVR7z7FIETB4PxguHC2YJGk6NncHnByrJttgRIUqNxfWezuzAUvtALyqcHJEC",
        }
        res = requests.get(
            "https://saruman.shadowfax.in/web_app/delivery/track/{}/".format(num),
            headers=headers,
            timeout=REQUEST_TIMEOUT,
        )
        if res.status_code != 200:
            logger.error("Error in fetching the data from shadowfax")
            return status

        data = res.json()
        tracking_events = data["data"][0]

        sub_tracking_events = tracking_events.get("sub_status", [])
        # convert the table to a list of dictionaries
        events = []
        for i, item in enumerate(sub_tracking_events):

            time = tracking_events["time"][i]

            date_time = parse_date_time_string(time)
            events.append(
                {
                    # "location": item,
                    "details": item,
                    "date_time": date_time,
                }
            )
        status["events"] = events
        status["service"] = "shadow_fax"

    except Exception as e:
        logger.error(f"An error occurred fetching from shadow fax: {e}")

    return status


def ekart_track(num: str) -> dict:
    logger.info(f"Tracking {num} with ekart_track")
    status = {"events": None, "service": None}
    try:
        headers = {
            **get_common_headers(),
            "origin": "https://www.ekartlogistics.com",
            "referer": "https://www.ekartlogistics.com",
        }
        res = requests.post(
            "http://www.ekartlogistics.com/ws/getTrackingDetails",
            json={"trackingId": num},
            headers=headers,
            timeout=REQUEST_TIMEOUT,
        )
        if res.status_code != 200:
            logger.error("Error in fetching the data from ekart")
            return status
        data = res.json()
        events = []
        for item in data.get("shipmentTrackingDetails", []):
            events.append(
                {
                    "location": item.get("city", ""),
                    "details": item.get("statusDetails", ""),
                    "date_time": parse_date_time_string(item.get("date", "")),
                }
            )

        events.reverse()
        status["events"] = events
        status["service"] = "ekart"
    except Exception as e:
        logger.error(f"An error occurred fetching from ekart: {e}")
    return status


def track_by_service(num: str, service: str) -> dict:
    logger.info(f"Tracking {num} with {service}")
    status = {"events": None, "service": None}
    if service == "bluedart":
        return bd_track(num)
    elif service == "dtdc":
        return dtdc_track_by_browser(num)
    elif service == "ecom_express":
        return ecom_express_track(num)
    elif service == "delhivery":
        return delhivery_track(num)
    elif service == "shadow_fax":
        return shadow_fax_track(num)
    elif service == "ekart":
        return ekart_track(num)
    else:
        logger.error(f"Invalid service: {service}")
        return status


def track_all(num: str) -> dict:
    logger.info(f"Tracking {num} with track_all")
    status = {"events": None, "service": None}
    tasks = [
        bd_track,
        # dtdc_track,
        dtdc_track_by_browser,
        ecom_express_track,
        delhivery_track,
        shadow_fax_track,
        ekart_track,
    ]
    with ThreadPoolExecutor(max_workers=len(tasks)) as executor:
        futures = [executor.submit(task, num) for task in tasks]
        for future in futures:
            res = future.result()
            events = res.get("events", None)
            if events is not None:
                status["events"] = events
                status["service"] = res.get("service")

    return status
