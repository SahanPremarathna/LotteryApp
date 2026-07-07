from scrapers.utils import (
    get_dlb_soup,
    find_real_result_heading,
    get_draw_info,
    collect_h6_values,
    get_historical_result_row,
    get_historical_draw_info,
    collect_historical_values
)

LOTTERY_NAME = "Ada Kotipathi"


def scrape_ada_kotipathi(day_offset=0):
    soup = get_dlb_soup()
    heading = find_real_result_heading(soup, LOTTERY_NAME)

    if day_offset:
        row = get_historical_result_row(heading, day_offset)
        draw_number, draw_date = get_historical_draw_info(row)
        values = collect_historical_values(row)

        if len(values) != 5:
            raise Exception(f"{LOTTERY_NAME}: Expected 5 values, got {values}")

        return {
            "source": "DLB",
            "lottery": LOTTERY_NAME,
            "draw_number": draw_number,
            "draw_date": draw_date,
            "letter": values[0],
            "numbers": values[1:],
            "raw_result": values
        }

    draw_tag, draw_number, draw_date = get_draw_info(heading)

    values = collect_h6_values(draw_tag, 5)

    if len(values) != 5:
        raise Exception(f"{LOTTERY_NAME}: Expected 5 values, got {values}")

    return {
        "source": "DLB",
        "lottery": LOTTERY_NAME,
        "draw_number": draw_number,
        "draw_date": draw_date,
        "letter": values[0],
        "numbers": values[1:],
        "raw_result": values
    }
