import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime

HEADERS = {
    "User-Agent": "Mozilla/5.0 LotteryResultChecker/1.0"
}

SOURCES = {
    "DLB": "https://www.dlb.lk/result/2/",
    "NLB": "https://www.nlb.lk/results"
}


def clean_text(text):
    return re.sub(r"\s+", " ", text).strip()


def scrape_page(source_name, url):
    response = requests.get(url, headers=HEADERS, timeout=20)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    text = soup.get_text("\n")
    lines = [clean_text(line) for line in text.splitlines() if clean_text(line)]

    results = []

    current = None

    for line in lines:
        # Detect lottery names loosely
        if any(keyword.lower() in line.lower() for keyword in [
            "sampatha", "wasana", "kapruka", "super ball",
            "govi", "mega", "jaya", "nidhanaya", "sasiri",
            "lagna", "ada kotipathi", "supiri"
        ]):
            if current:
                results.append(current)

            current = {
                "source": source_name,
                "lottery": line,
                "draw_number": None,
                "draw_date": None,
                "numbers": []
            }

        elif current:
            # Draw number/date pattern
            draw_match = re.search(r"Draw Number\s*-\s*(\d+)\s*\|\s*(.+)", line, re.I)
            if draw_match:
                current["draw_number"] = draw_match.group(1)
                current["draw_date"] = draw_match.group(2)

            # NLB style: "Mega Power 2588"
            nlb_match = re.search(r"(.+?)\s+(\d{3,5})$", line)
            if nlb_match and current["draw_number"] is None:
                current["draw_number"] = nlb_match.group(2)

            # Winning numbers / letters
            tokens = re.findall(r"\b[A-Z]\b|\b\d{1,2}\b", line)
            if tokens:
                current["numbers"].extend(tokens)

    if current:
        results.append(current)

    # Remove weak/empty results
    clean_results = []
    for item in results:
        if item["numbers"] or item["draw_number"]:
            item["numbers"] = item["numbers"][:10]
            clean_results.append(item)

    return clean_results


def main():
    all_results = []

    for source, url in SOURCES.items():
        try:
            data = scrape_page(source, url)
            all_results.extend(data)
            print(f"[OK] Scraped {source}: {len(data)} results")
        except Exception as e:
            print(f"[ERROR] {source}: {e}")

    output = {
        "scraped_at": datetime.now().isoformat(),
        "results": all_results
    }

    with open("lottery_results.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print("Saved to lottery_results.json")


if __name__ == "__main__":
    main()