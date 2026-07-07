from scrapers.utils import get_dlb_soup, find_lottery_heading, get_draw_info, collect_values_after

LOTTERY_NAME = "Supiri Dhana Sampatha"


def scrape_supiri_dhana_sampatha():
    soup = get_dlb_soup()
    heading = find_lottery_heading(soup, LOTTERY_NAME)
    draw_tag, draw_number, draw_date = get_draw_info(heading)

    values = collect_values_after(draw_tag, 5)

    if len(values) != 5:
        raise Exception(f"{LOTTERY_NAME}: Expected 5 values, got {values}")

    return {
        "source": "DLB",
        "lottery": LOTTERY_NAME,
        "draw_number": draw_number,
        "draw_date": draw_date,
        "letter": values[0],
        "digits": values[1:],
        "raw_result": values
    }