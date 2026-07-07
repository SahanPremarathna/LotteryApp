import re
import requests
from bs4 import BeautifulSoup, Tag

DLB_URL = "https://www.dlb.lk/result/2/"
DLB_PAGINATION_URL = "https://www.dlb.lk/result/pagination_re"
HEADERS = {"User-Agent": "SriLankaLotteryChecker/1.0"}


def clean(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def get_dlb_soup():
    res = requests.get(DLB_URL, headers=HEADERS, timeout=20)
    res.raise_for_status()
    return BeautifulSoup(res.text, "html.parser")


def get_lottery_ids(heading):
    result_input = heading.find_next("input", id=re.compile(r"^resultID\d+$"))
    if result_input is None:
        raise Exception(f"Result ID not found after heading: {clean(heading.get_text())}")

    lot_id_match = re.search(r"\d+", result_input.get("id", ""))
    if not lot_id_match:
        raise Exception(f"Lottery ID not found in input id: {result_input}")

    return lot_id_match.group(0), result_input.get("value")


def get_historical_result_row(heading, day_offset):
    if day_offset < 1:
        raise Exception(f"Historical day offset must be 1 or more, got {day_offset}")

    lottery_id, result_id = get_lottery_ids(heading)
    page_id = (day_offset - 1) // 10
    row_index = (day_offset - 1) % 10

    res = requests.post(
        DLB_PAGINATION_URL,
        headers=HEADERS,
        data={
            "pageId": str(page_id),
            "resultID": result_id,
            "lotteryID": lottery_id,
            "lastsegment": "2",
        },
        timeout=20,
    )
    res.raise_for_status()

    rows = [
        row_html
        for row_html in re.split(r"(?=<tr\b)", res.text)
        if row_html.strip().startswith("<tr")
    ]

    if row_index >= len(rows):
        raise Exception(
            f"Historical result not found for offset {day_offset}; "
            f"page {page_id} has {len(rows)} rows"
        )

    return BeautifulSoup(rows[row_index], "html.parser")


def get_historical_draw_info(row):
    first_cell = row.find("td")
    if first_cell is None:
        raise Exception("Historical draw info cell not found")

    text = clean(first_cell.get_text())
    match = re.search(r"(\d+)\s*\|\s*(.+)", text)
    if not match:
        raise Exception(f"Historical draw info not found: {text}")

    return match.group(1), match.group(2)


def collect_historical_values(row):
    values = []

    for item in row.find_all("li"):
        classes = item.get("class", [])
        if "res_eng_letter" not in classes and "res_number" not in classes:
            continue

        value = clean(item.get_text())
        if value:
            values.append(value)

    return values


def find_historical_image_info(row):
    images = row.find_all("img", src=True)
    image = next(
        (
            candidate
            for candidate in images
            if "symbol_special" not in candidate.get("src", "")
            and "more.png" not in candidate.get("src", "")
        ),
        images[0] if images else None
    )

    if image is None:
        return None

    return {
        "alt": image.get("alt"),
        "title": image.get("title"),
        "src": image.get("src")
    }


def find_real_result_heading(soup, lottery_name):
    for h2 in soup.find_all("h2"):
        if clean(h2.get_text()).lower() != lottery_name.lower():
            continue

        current = h2
        while True:
            current = current.find_next()
            if current is None:
                break

            if current.name == "h2":
                break

            if current.name == "h3" and "Draw Number" in clean(current.get_text()):
                return h2

    raise Exception(f"Real result section not found for {lottery_name}")


def get_draw_info(heading):
    h3 = heading.find_next("h3")
    text = clean(h3.get_text())

    match = re.search(r"Draw Number\s*-\s*(\d+)\s*\|\s*(.+)", text)
    if not match:
        raise Exception(f"Draw info not found: {text}")

    return h3, match.group(1), match.group(2)


def collect_h6_values(draw_tag, max_values):
    values = []
    current = draw_tag

    while True:
        current = current.find_next()

        if current is None:
            break

        text = clean(current.get_text())

        if text == "MORE":
            break

        if current.name == "h2":
            break

        if current.name == "h6":
            value = clean(current.get_text())
            if value:
                values.append(value)

        if len(values) >= max_values:
            break

    return values


def find_first_image_info(draw_tag):
    current = draw_tag

    while True:
        current = current.find_next()

        if current is None:
            return None

        if current.name == "h6" or clean(current.get_text()) == "MORE":
            return None

        if current.name == "img":
            return {
                "alt": current.get("alt"),
                "title": current.get("title"),
                "src": current.get("src")
            }
