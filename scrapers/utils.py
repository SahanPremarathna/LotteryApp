import re
import requests
from bs4 import BeautifulSoup, Tag

DLB_URL = "https://www.dlb.lk/result/2/"

HEADERS = {
    "User-Agent": "SriLankaLotteryChecker/1.0"
}


def clean(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def own_text(tag: Tag) -> str:
    return clean(" ".join(str(x) for x in tag.contents if isinstance(x, str)))


def get_dlb_soup():
    res = requests.get(DLB_URL, headers=HEADERS, timeout=20)
    res.raise_for_status()
    return BeautifulSoup(res.text, "html.parser")


def find_lottery_heading(soup, lottery_name):
    for h2 in soup.find_all("h2"):
        if clean(h2.get_text()).lower() == lottery_name.lower():
            return h2
    raise Exception(f"{lottery_name} heading not found")


def get_draw_info(heading):
    h3 = heading.find_next("h3")
    text = clean(h3.get_text())

    match = re.search(r"Draw Number\s*-\s*(\d+)\s*\|\s*(.+)", text)
    if not match:
        raise Exception(f"Draw info not found: {text}")

    return h3, match.group(1), match.group(2)


def collect_values_after(draw_tag, max_values):
    values = []
    current = draw_tag

    while True:
        current = current.find_next()

        if current is None:
            break

        if current.name == "h2":
            break

        text = own_text(current)

        if re.fullmatch(r"[A-Z]|\d{1,2}|[A-Za-z]+", text):
            values.append(text)

        if len(values) >= max_values:
            break

    return values