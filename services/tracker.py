import bs4
import requests
from loguru import logger


def bd_track(num: str) -> list[dict] | None:
    try:
        res = requests.get(
            "https://www.bluedart.com/trackdartresultthirdparty?trackFor=0&trackNo={}".format(
                num
            )
        )
        if res.status_code != 200:
            logger.error("Error in fetching the page")
            return None
        soup = bs4.BeautifulSoup(res.text, "html.parser")
        status_events = soup.find("div", id="SCAN{}".format(num))
        if status_events is None:
            logger.error("Error in fetching the status")
            return None

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

        return status
    except Exception as e:
        logger.error(e)
        return None
