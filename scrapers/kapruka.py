from scrapers.utils import get_dlb_soup, find_lottery_heading, get_draw_info, collect_values_after

LOTTERY_NAME = "Kapruka"


def scrape_kapruka():
    soup = get_dlb_soup()
    heading = find_lottery_heading(soup, LOTTERY_NAME)
    draw_tag, draw_number, draw_date = get_draw_info(heading)

    values = collect_values_after(draw_tag, 6)

    if len(values) != 6:
        raise Exception(f"{LOTTERY_NAME}: Expected 6 values, got {values}")

    return {
        "source": "DLB",
        "lottery": LOTTERY_NAME,
        "draw_number": draw_number,
        "draw_date": draw_date,
        "letter": values[0],
        "numbers": values[1:5],
        "bonus": values[5],
        "raw_result": values
    }