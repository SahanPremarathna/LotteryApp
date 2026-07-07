from scrapers.utils import get_dlb_soup, find_lottery_heading, get_draw_info, collect_values_after

LOTTERY_NAME = "Sasiri"


def scrape_sasiri():
    soup = get_dlb_soup()
    heading = find_lottery_heading(soup, LOTTERY_NAME)
    draw_tag, draw_number, draw_date = get_draw_info(heading)

    values = collect_values_after(draw_tag, 3)

    if len(values) != 3:
        raise Exception(f"{LOTTERY_NAME}: Expected 3 values, got {values}")

    return {
        "source": "DLB",
        "lottery": LOTTERY_NAME,
        "draw_number": draw_number,
        "draw_date": draw_date,
        "numbers": values,
        "raw_result": values
    }