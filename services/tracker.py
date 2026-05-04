import json
import re
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from itertools import zip_longest

import bs4
import requests
from loguru import logger

from services.selenium_tracker import (
    dtdc_track_srv,
    ekart_track_srv,
    xpressbees_track_srv,
)
from utils.common import parse_date_time_string

REQUEST_TIMEOUT = 120


def get_common_headers():
    return {
        "accept": "application/json, text/plain, */*",
        "accept-language": "en-US,en;q=0.9,zh-TW;q=0.8,zh;q=0.7",
        "origin": "https://www.google.com",
        "priority": "u=1, i",
        "referer": "https://www.google.com/",
        "sec-ch-ua": '"Google Chrome";v="147", "Not.A/Brand";v="8", "Chromium";v="147"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36",
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

        eta = None
        # BlueDart often renders ETA as human-readable text, e.g. "27 Jan 2026".
        # Extract from normalized page text to avoid brittle tag assumptions.
        page_text = soup.get_text(" ", strip=True)
        eta_match = re.search(
            r"Expected Date of Delivery\s*"
            r"(\d{1,2}\s+[A-Za-z]{3}\s+\d{4}"
            r"|\d{4}[-/]\d{1,2}[-/]\d{1,2}"
            r"|\d{1,2}[-/]\d{1,2}[-/]\d{4})",
            page_text,
        )

        if eta_match:
            eta_str = eta_match.group(1).strip()
            eta = parse_date_time_string(eta_str)
        status["eta"] = eta

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
            datetime_text = item.get("date", "") or item.get("timestamp", "")

            parsed_datetime = None
            # Parse datetime
            if datetime_text:
                parsed_datetime = parse_date_time_string(datetime_text)

            if not parsed_datetime:
                logger.warning(f"skipping entry {item}, unable to parse datetime")
                continue

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


def ekart_track_by_browser(num: str) -> dict:
    """Track Ekart using Selenium browser automation."""
    logger.info(f"Tracking {num} with ekart_track_by_browser")
    status = {"events": None, "service": None}
    try:
        response_text = ekart_track_srv(num)
        if not response_text:
            return status

        try:
            response_data = json.loads(response_text)
        except Exception as e:
            logger.error(f"Error parsing JSON from Ekart: {e}")
            return status

        # Handle different response formats
        if isinstance(response_data, dict) and "tracking_events" in response_data:
            # Fallback format with text events
            events = []
            for event_text in response_data.get("tracking_events", []):
                events.append(
                    {
                        "location": "",
                        "details": event_text,
                        "date_time": None,
                    }
                )
            if events:
                status["events"] = events
                status["service"] = "ekart"
        elif isinstance(response_data, dict) and "data" in response_data:
            # Structured data format
            tracking_data = response_data.get("data", {}).get(num, {})
            scans = tracking_data.get("scans", [])

            events = []
            for item in scans:
                events.append(
                    {
                        "location": item.get("location", ""),
                        "details": item.get("status_description", "")
                        or item.get("scan_type", ""),
                        "date_time": parse_date_time_string(
                            item.get("scan_datetime", "")
                        ),
                    }
                )

            if events:
                events.reverse()
                status["events"] = events
                status["service"] = "ekart"

        elif isinstance(response_data, dict) and num in response_data:
            # Ekart v2 API response captured from network: keyed by tracking id.
            tracking_data = response_data.get(num) or {}
            details_list = tracking_data.get("shipmentTrackingDetails") or []

            events = []
            for item in details_list:
                events.append(
                    {
                        "location": item.get("city", ""),
                        "details": item.get("statusDetails", ""),
                        "date_time": parse_date_time_string(item.get("date")),
                    }
                )

            if events:
                events.reverse()
                status["events"] = events
                status["service"] = "ekart"
                status["eta"] = parse_date_time_string(
                    tracking_data.get("expectedDeliveryDate")
                )

    except Exception as e:
        logger.error(f"An error occurred fetching from ekart_track_by_browser: {e}")
    return status


def xpressbees_track_by_browser(num: str) -> dict:
    logger.info(f"Tracking {num} with xpressbees_track_by_browser")
    status = {"events": None, "service": None}
    try:
        response_text = xpressbees_track_srv(num)
        if not response_text:
            return status

        events = []
        eta = None

        # POST /api/tracking response: {"domestic": [{"status","shippingDate","origin","EDD"}]}
        try:
            payload = json.loads(response_text)
        except Exception:
            return status

        if not isinstance(payload, dict):
            return status

        for item in (payload.get("domestic") or []) + (
            payload.get("international") or []
        ):
            details = item.get("status") or ""
            date_str = item.get("shippingDate") or ""
            location = item.get("origin") or ""
            if details and date_str:
                events.append(
                    {
                        "location": location.strip(),
                        "details": details.strip(),
                        "date_time": parse_date_time_string(date_str),
                    }
                )
            edd = item.get("EDD") or ""
            if eta is None and edd:
                eta = parse_date_time_string(edd)

        if not events:
            return status

        deduped_events = []
        seen = set()
        for event in events:
            dt = event.get("date_time")
            dedupe_key = (
                event.get("details", ""),
                event.get("location", ""),
                dt.isoformat() if dt else "",
            )
            if dedupe_key in seen:
                continue
            seen.add(dedupe_key)
            deduped_events.append(event)

        deduped_events.sort(
            key=lambda e: e.get("date_time") or datetime.min,
            reverse=True,
        )

        status["events"] = deduped_events
        status["service"] = "xpressbees"
        status["eta"] = eta

    except Exception as e:
        logger.error(f"An error occurred fetching from xpressbees: {e}")

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
            "https://dlv-api.delhivery.com/v3/unified-tracking-new",
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

        events = []
        if data.get("message") != "Success":
            return status

        tracking_items = data.get("data") or []
        tracking_item = tracking_items[0] if tracking_items else {}
        tracking_states = tracking_item.get("trackingStates") or []
        latest_tracking_state = tracking_states[-1] if tracking_states else {}
        scans = latest_tracking_state.get("scans") or []
        latest_scan = scans[-1] if scans else {}
        current_status = tracking_item.get("status") or {}

        # delhivery has a different format
        date_time = parse_date_time_string(
            latest_scan.get("scanDateTime") or current_status.get("statusDateTime")
        )
        details = (
            latest_scan.get("scanNslRemark")
            or latest_scan.get("scan")
            or current_status.get("instructions")
            or current_status.get("status")
        )
        location = latest_scan.get("cityLocation") or tracking_item.get("destination")

        if date_time or details or location:
            events.append(
                {
                    "location": location,
                    "details": details,
                    "date_time": date_time,
                }
            )

        status["events"] = events
        status["service"] = "delhivery"
        status["eta"] = parse_date_time_string(tracking_item.get("promiseDeliveryDate"))

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

        payload = res.json()
        if payload.get("message") != "Success":
            logger.error(
                f"Shadowfax API did not return Success. message={payload.get('message')}"
            )
            return status

        data_items = payload.get("data") or []
        if not isinstance(data_items, list) or not data_items:
            logger.error("Shadowfax API returned empty/malformed data")
            return status

        tracking_item = data_items[0] or {}
        sub_statuses = tracking_item.get("sub_status") or []
        times = tracking_item.get("time") or []

        if not isinstance(sub_statuses, list) or not isinstance(times, list):
            logger.error("Shadowfax API returned malformed sub_status/time")
            return status

        events = []
        for details, time_str in zip_longest(sub_statuses, times, fillvalue=None):
            if not details:
                continue
            date_time = parse_date_time_string(time_str) if time_str else None
            events.append(
                {
                    "details": details,
                    "date_time": date_time,
                }
            )

        status["events"] = events
        status["service"] = "shadow_fax"
        status["eta"] = parse_date_time_string(
            payload.get("order_details", {}).get("exp_delivery_date", "")
        )

    except Exception as e:
        logger.error(f"An error occurred fetching from shadow fax: {e}")

    return status


def shree_maruti_track(num: str) -> dict:
    logger.info(f"Tracking {num} with shree_maruti_track")
    status = {"events": None, "service": None}
    try:
        headers = {
            **get_common_headers(),
            "accept": "*/*",
            "origin": "https://tracking.shreemaruti.com",
            "referer": "https://tracking.shreemaruti.com/",
            "sec-fetch-site": "cross-site",
        }
        res = requests.get(
            f"https://apis-hubops.innofulfill.com/tracking/v2/{num}",
            headers=headers,
            timeout=REQUEST_TIMEOUT,
        )
        if res.status_code != 200:
            logger.error(
                f"Failed to fetch data from Shree Maruti API. Status code: {res.status_code}"
            )
            return status

        payload = res.json()
        statuses = payload.get("statuses") or []
        if not isinstance(statuses, list) or not statuses:
            return status

        events = []
        for item in statuses:
            details = (
                item.get("subcategory") or item.get("status") or item.get("event") or ""
            )
            location = item.get("location") or ""

            date_time = None
            ts = item.get("statusTimestamp")
            if isinstance(ts, (int, float)):
                date_time = datetime.fromtimestamp(ts / 1000)
            elif isinstance(ts, str) and ts.strip():
                date_time = parse_date_time_string(ts)

            events.append(
                {
                    "location": location,
                    "details": details,
                    "date_time": date_time,
                }
            )

        if not events:
            return status

        events.sort(
            key=lambda e: e.get("date_time") or datetime.min,
            reverse=True,
        )

        status["events"] = events
        status["service"] = "shree_maruti"

    except Exception as e:
        logger.error(f"An error occurred fetching from shree maruti: {e}")

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
        return ekart_track_by_browser(num)
    elif service == "xpressbees":
        return xpressbees_track_by_browser(num)
    elif service == "shree_maruti":
        return shree_maruti_track(num)
    else:
        logger.error(f"Invalid service: {service}")
        return status


def track_all(num: str) -> dict:
    logger.info(f"Tracking {num} with track_all")
    status = {"events": None, "service": None}

    # Prioritize lightweight trackers first
    lightweight_tasks = [
        bd_track,
        ecom_express_track,
        delhivery_track,
        shadow_fax_track,
        shree_maruti_track,
        # ekart_track,  # Disabled due to CSRF validation issues - too complex for API-only approach
    ]

    # Try lightweight trackers first in parallel
    with ThreadPoolExecutor(max_workers=len(lightweight_tasks)) as executor:
        futures = [executor.submit(task, num) for task in lightweight_tasks]
        for future in futures:
            res = future.result()
            events = res.get("events", None)
            if events is not None:
                status["events"] = events
                status["service"] = res.get("service")
                status["eta"] = res.get("eta", "")
                return status

    # If no results from lightweight trackers, try resource-heavy browser trackers
    logger.info(
        f"No results from lightweight trackers, trying browser-based trackers for {num}"
    )

    # Try XpressBees
    res = xpressbees_track_by_browser(num)
    events = res.get("events", None)
    if events is not None:
        status["events"] = events
        status["service"] = res.get("service")
        status["eta"] = res.get("eta", "")
        return status

    # Try DTDC first
    res = dtdc_track_by_browser(num)
    events = res.get("events", None)
    if events is not None:
        status["events"] = events
        status["service"] = res.get("service")
        status["eta"] = res.get("eta", "")
        return status

    # Try Ekart as last resort
    logger.info(f"DTDC browser tracker failed, trying ekart_track_by_browser for {num}")
    res = ekart_track_by_browser(num)
    events = res.get("events", None)
    if events is not None:
        status["events"] = events
        status["service"] = res.get("service")
        status["eta"] = res.get("eta", "")

    return status
