import json
from datetime import datetime

from scrapers.ada_kotipathi import scrape_ada_kotipathi
from scrapers.kapruka import scrape_kapruka
from scrapers.super_ball import scrape_super_ball
from scrapers.lagna_wasana import scrape_lagna_wasana
from scrapers.sasiri import scrape_sasiri
from scrapers.supiri_dhana_sampatha import scrape_supiri_dhana_sampatha


SCRAPERS = [
    scrape_ada_kotipathi,
    scrape_kapruka,
    scrape_super_ball,
    scrape_lagna_wasana,
    scrape_sasiri,
    scrape_supiri_dhana_sampatha,
]


def ask_day_offset():
    value = input(
        "Enter result day offset "
        "(0 = present/latest, 1 = yesterday, 2 = day before yesterday): "
    ).strip()

    if not value:
        return 0

    try:
        day_offset = int(value)
    except ValueError:
        raise ValueError(f"Please enter a number, got: {value}")

    if day_offset < 0:
        raise ValueError("Day offset cannot be negative")

    return day_offset


def main():
    day_offset = ask_day_offset()
    results = []

    for scraper in SCRAPERS:
        try:
            result = scraper(day_offset=day_offset)
            results.append(result)
            print(f"[OK] {result['lottery']}")
        except Exception as e:
            print(f"[ERROR] {scraper.__name__}: {e}")

    output = {
        "scraped_at": datetime.now().isoformat(),
        "day_offset": day_offset,
        "results": results
    }

    with open("lottery_results.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(json.dumps(output, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
