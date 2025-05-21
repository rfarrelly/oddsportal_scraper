import re
import time
import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

from config import (
    ODDSPORTAL_BASE_URL,
    ODDSPORTAL_LINKS_REGEX,
    ODDSPORTAL_REQUEST_HEADER,
    ODDSPORTAL_MARKETS,
)


def scroll_to_bottom(page, pause_time=1.5, max_scrolls=20):
    for _ in range(max_scrolls):
        previous_height = page.evaluate("document.body.scrollHeight")
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(pause_time)
        current_height = page.evaluate("document.body.scrollHeight")
        if current_height == previous_height:
            break


def get_page_content(url: str, debug=False):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, timeout=60000)
        scroll_to_bottom(page)
        html = page.content()
        browser.close()

    if debug:
        with open("debug_page.html", "w", encoding="utf-8") as f:
            f.write(html)

    return html


def get_next_fixture_links(league_url_frag: str, market: str):
    try:
        url = ODDSPORTAL_BASE_URL + league_url_frag
        res = requests.get(url, headers=ODDSPORTAL_REQUEST_HEADER)
        soup = BeautifulSoup(res.content, "lxml")
        div_tag = soup.find("div", {"class": "empty:min-h-[80vh]"})
        match_frags = re.findall(ODDSPORTAL_LINKS_REGEX, str(div_tag.contents))
        market_urls = list(
            set([url + frag + ODDSPORTAL_MARKETS[market] for frag in match_frags])
        )
    except Exception as e:
        print(f"No matches found for {league_url_frag}: {e}")
        return []

    print(f"Found {len(market_urls)} matches for {league_url_frag}")
    return market_urls


def extract_links(league_url_frag: str, containers: list, market: str):
    links = []
    for container in containers:
        a_tags = container.find_all("a", href=True)
        for a in a_tags:
            href = a["href"]
            if f"/football/{league_url_frag}" in href:
                links.append(href)
    match_frags = re.findall(ODDSPORTAL_LINKS_REGEX, str(links))
    market_urls = list(
        set(
            [
                ODDSPORTAL_BASE_URL
                + league_url_frag
                + frag
                + ODDSPORTAL_MARKETS[market]
                for frag in match_frags
            ]
        )
    )
    return market_urls


def get_historical_links(league_url_frag: str, market: str):
    market_urls = []

    # Page 1
    url = ODDSPORTAL_BASE_URL + league_url_frag + "results/#/page/1"
    html = get_page_content(url)
    soup = BeautifulSoup(html, "html.parser")
    containers = soup.find_all("div", {"class": "min-h-[80vh]"})
    market_urls.extend(extract_links(league_url_frag, containers, market))

    # Pagination
    pagination = soup.find_all("a", {"class": "pagination-link"})
    page_numbers = sorted(
        [int(x["data-number"]) for x in pagination if "data-number" in x.attrs]
    )
    max_page_number = max(page_numbers) if page_numbers else 1

    for page_number in range(2, max_page_number + 1):
        print(f"Scraping page {page_number}...")
        url = ODDSPORTAL_BASE_URL + league_url_frag + f"results/#/page/{page_number}"
        html = get_page_content(url)
        soup = BeautifulSoup(html, "html.parser")
        containers = soup.find_all("div", {"class": "min-h-[80vh]"})
        market_urls.extend(extract_links(league_url_frag, containers, market))

    print(f"Found {len(market_urls)} historical matches for {league_url_frag}")
    return market_urls


# Example usage
if __name__ == "__main__":
    murls = get_historical_links("england/championship/", "dc")
    breakpoint()
