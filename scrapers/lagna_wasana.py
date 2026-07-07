from scrapers.utils import (
    get_dlb_soup,
    find_real_result_heading,
    get_draw_info,
    collect_h6_values,
    find_first_image_info,
    get_historical_result_row,
    get_historical_draw_info,
    collect_historical_values,
    find_historical_image_info
)

LOTTERY_NAME = "Lagna Wasana"


def scrape_lagna_wasana(day_offset=0):
    soup = get_dlb_soup()
    heading = find_real_result_heading(soup, LOTTERY_NAME)

    if day_offset:
        row = get_historical_result_row(heading, day_offset)
        draw_number, draw_date = get_historical_draw_info(row)
        numbers = collect_historical_values(row)
        lagna_image = find_historical_image_info(row)

        if len(numbers) != 4:
            raise Exception(f"{LOTTERY_NAME}: Expected 4 numbers, got {numbers}")

        return {
            "source": "DLB",
            "lottery": LOTTERY_NAME,
            "draw_number": draw_number,
            "draw_date": draw_date,
            "lagna": lagna_image,
            "numbers": numbers,
            "raw_result": numbers
        }

    draw_tag, draw_number, draw_date = get_draw_info(heading)

    numbers = collect_h6_values(draw_tag, 4)
    lagna_image = find_first_image_info(draw_tag)

    if len(numbers) != 4:
        raise Exception(f"{LOTTERY_NAME}: Expected 4 numbers, got {numbers}")

    return {
        "source": "DLB",
        "lottery": LOTTERY_NAME,
        "draw_number": draw_number,
        "draw_date": draw_date,
        "lagna": lagna_image,
        "numbers": numbers,
        "raw_result": numbers
    }
