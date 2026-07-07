import json
import re
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import requests
from bs4 import BeautifulSoup


BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

DLB_URL = "https://www.dlb.lk/result/2/"
DLB_PAGINATION_URL = "https://www.dlb.lk/result/pagination_re"
HEADERS = {"User-Agent": "SriLankaLotteryTrialRun/1.0"}

LOTTERIES = {
    "ada_kotipathi": {
        "name": "Ada Kotipathi",
        "type": "letter_numbers",
        "value_count": 5,
        "logo": "https://www.dlb.lk/front_img/Logo20190925.jpg",
    },
    "kapruka": {
        "name": "Kapruka",
        "type": "letter_numbers_special",
        "value_count": 6,
        "logo": "https://www.dlb.lk/front_img/1708410688145-01.jpg",
    },
    "super_ball": {
        "name": "Super Ball",
        "type": "super_ball",
        "value_count": 5,
        "current_special_number": "26001",
        "logo": "https://www.dlb.lk/front_img/147754265507.png",
    },
    "lagna_wasana": {
        "name": "Lagna Wasana",
        "type": "lagna_numbers",
        "value_count": 4,
        "logo": "https://www.dlb.lk/front_img/17244079611-06.jpg",
    },
    "sasiri": {
        "name": "Sasiri",
        "type": "numbers_only",
        "value_count": 3,
        "logo": "https://www.dlb.lk/front_img/17244080311-07.jpg",
    },
    "supiri_dhana_sampatha": {
        "name": "Supiri Dhana Sampatha",
        "type": "letter_numbers",
        "value_count": 7,
        "logo": "https://www.dlb.lk/front_img/1735713525logo_SDS_new-01.png",
    },
}


def clean(text):
    return re.sub(r"\s+", " ", text or "").strip()


def get_soup():
    response = requests.get(DLB_URL, headers=HEADERS, timeout=20)
    response.raise_for_status()
    return BeautifulSoup(response.text, "html.parser")


def parse_dlb_date(text):
    match = re.search(r"(\d{4})-([A-Za-z]{3})-(\d{2})", text)
    if not match:
        return None

    parsed = datetime.strptime(match.group(0), "%Y-%b-%d")
    return parsed.strftime("%Y-%m-%d")


def find_result_heading(soup, lottery_name):
    for h2 in soup.find_all("h2"):
        if clean(h2.get_text()).lower() != lottery_name.lower():
            continue

        current = h2
        while True:
            current = current.find_next()
            if current is None or current.name == "h2":
                break

            if current.name == "h3" and "Draw Number" in clean(current.get_text()):
                return h2

    raise RuntimeError(f"Result section not found for {lottery_name}")


def get_current_draw_info(heading):
    h3 = heading.find_next("h3")
    text = clean(h3.get_text())
    match = re.search(r"Draw Number\s*-\s*(\d+)\s*\|\s*(.+)", text)
    if not match:
        raise RuntimeError(f"Draw info not found: {text}")

    return h3, match.group(1), clean(match.group(2))


def collect_current_values(draw_tag, count):
    values = []
    current = draw_tag

    while True:
        current = current.find_next()
        if current is None:
            break

        text = clean(current.get_text())
        if text == "MORE" or current.name == "h2":
            break

        if current.name == "h6":
            value = clean(current.get_text())
            if value:
                values.append(value)

        if len(values) >= count:
            break

    return values


def collect_current_images(draw_tag):
    images = []
    current = draw_tag

    while True:
        current = current.find_next()
        if current is None:
            break

        text = clean(current.get_text())
        if text == "MORE" or current.name == "h2":
            break

        if current.name == "img" and current.get("src"):
            images.append(image_payload(current))

    return images


def image_payload(image):
    return {
        "src": image.get("src"),
        "alt": image.get("alt"),
        "title": image.get("title"),
    }


def preferred_image(images):
    for image in images:
        src = image.get("src") or ""
        if "symbol_special" not in src and "more.png" not in src:
            return image
    return images[0] if images else None


def get_lottery_ids(heading):
    result_input = heading.find_next("input", id=re.compile(r"^resultID\d+$"))
    if result_input is None:
        raise RuntimeError("Result ID input not found")

    lot_id = re.search(r"\d+", result_input.get("id", ""))
    if not lot_id:
        raise RuntimeError("Lottery ID not found")

    return lot_id.group(0), result_input.get("value")


def get_history_page(heading, page_id):
    lottery_id, result_id = get_lottery_ids(heading)
    response = requests.post(
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
    response.raise_for_status()

    return [
        row_html
        for row_html in re.split(r"(?=<tr\b)", response.text)
        if row_html.strip().startswith("<tr")
    ]


def parse_history_row(row_html):
    row = BeautifulSoup(row_html, "html.parser")
    first_cell = row.find("td")
    if first_cell is None:
        return None

    draw_text = clean(first_cell.get_text())
    draw_match = re.search(r"(\d+)\s*\|\s*(.+)", draw_text)
    if not draw_match:
        return None

    values = []
    for item in row.find_all("li"):
        classes = item.get("class", [])
        if "res_eng_letter" not in classes and "res_number" not in classes:
            continue

        value = clean(item.get_text())
        if value:
            values.append(value)

    images = [image_payload(image) for image in row.find_all("img", src=True)]

    return {
        "draw_number": draw_match.group(1),
        "draw_date": clean(draw_match.group(2)),
        "draw_date_iso": parse_dlb_date(draw_match.group(2)),
        "values": values,
        "images": images,
    }


def shape_result(lottery, draw_number, draw_date, values, images=None, is_current=False):
    images = images or []
    expected = lottery["value_count"]
    if len(values) != expected:
        raise RuntimeError(
            f"{lottery['name']}: expected {expected} values, got {values}"
        )

    result = {
        "source": "DLB",
        "lottery": lottery["name"],
        "draw_number": draw_number,
        "draw_date": draw_date,
        "draw_date_iso": parse_dlb_date(draw_date),
        "logo": lottery.get("logo"),
        "raw_result": values,
    }

    result_type = lottery["type"]

    if result_type == "numbers_only":
        result["numbers"] = values
    elif result_type == "lagna_numbers":
        result["lagna"] = preferred_image(images)
        result["numbers"] = values
    elif result_type == "letter_numbers_special":
        result["letter"] = values[0]
        result["numbers"] = values[1:5]
        result["special_number"] = values[5]
    elif result_type == "super_ball":
        result["letter"] = values[0]
        result["numbers"] = values[1:]
        if is_current and lottery.get("current_special_number"):
            result["special_number"] = lottery["current_special_number"]
            result["raw_result"] = values + [lottery["current_special_number"]]
        else:
            result["special_image"] = preferred_image(images)
    else:
        result["letter"] = values[0]
        result["numbers"] = values[1:]

    return result


def find_result_by_date(lottery_key, date_iso):
    if lottery_key not in LOTTERIES:
        raise RuntimeError("Unknown lottery selected")

    lottery = LOTTERIES[lottery_key]
    soup = get_soup()
    heading = find_result_heading(soup, lottery["name"])
    draw_tag, draw_number, draw_date = get_current_draw_info(heading)

    if parse_dlb_date(draw_date) == date_iso:
        values = collect_current_values(draw_tag, lottery["value_count"])
        images = collect_current_images(draw_tag)
        return shape_result(
            lottery,
            draw_number,
            draw_date,
            values,
            images=images,
            is_current=True,
        )

    target_date = datetime.strptime(date_iso, "%Y-%m-%d").date()

    for page_id in range(80):
        rows = get_history_page(heading, page_id)
        if not rows:
            break

        for row_html in rows:
            parsed = parse_history_row(row_html)
            if not parsed or not parsed["draw_date_iso"]:
                continue

            row_date = datetime.strptime(parsed["draw_date_iso"], "%Y-%m-%d").date()
            if row_date == target_date:
                return shape_result(
                    lottery,
                    parsed["draw_number"],
                    parsed["draw_date"],
                    parsed["values"],
                    images=parsed["images"],
                )

            if row_date < target_date:
                raise RuntimeError(f"No {lottery['name']} result found for {date_iso}")

    raise RuntimeError(f"No {lottery['name']} result found for {date_iso}")


def json_response(handler, payload, status=200):
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def static_response(handler, path):
    if path == "/":
        file_path = BASE_DIR / "index.html"
    else:
        file_path = BASE_DIR / path.lstrip("/")

    if not file_path.resolve().is_relative_to(BASE_DIR):
        handler.send_error(404)
        return

    if not file_path.exists() or not file_path.is_file():
        handler.send_error(404)
        return

    content_type = "text/html; charset=utf-8"
    if file_path.suffix == ".css":
        content_type = "text/css; charset=utf-8"
    elif file_path.suffix == ".js":
        content_type = "application/javascript; charset=utf-8"

    body = file_path.read_bytes()
    handler.send_response(200)
    handler.send_header("Content-Type", content_type)
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


class TrialLotteryHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path == "/api/lotteries":
            payload = [
                {"key": key, "name": value["name"], "logo": value.get("logo")}
                for key, value in LOTTERIES.items()
            ]
            json_response(self, {"lotteries": payload})
            return

        if parsed.path == "/api/result":
            query = parse_qs(parsed.query)
            lottery_key = query.get("lottery", [""])[0]
            date_iso = query.get("date", [""])[0]

            if not lottery_key or not date_iso:
                json_response(
                    self,
                    {"error": "Please select both a lottery and a date."},
                    status=400,
                )
                return

            try:
                result = find_result_by_date(lottery_key, date_iso)
                json_response(self, {"result": result})
            except Exception as exc:
                json_response(self, {"error": str(exc)}, status=404)
            return

        static_response(self, parsed.path)

    def log_message(self, format, *args):
        return


def run(port=5055):
    server = ThreadingHTTPServer(("127.0.0.1", port), TrialLotteryHandler)
    print(f"Trial lottery UI running at http://127.0.0.1:{port}")
    server.serve_forever()


if __name__ == "__main__":
    run()
