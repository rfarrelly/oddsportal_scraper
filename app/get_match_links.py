import re
import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import time

from config import (
    ODDSPORTAL_BASE_URL,
    ODDSPORTAL_LINKS_REGEX,
    ODDSPORTAL_REQUEST_HEADER,
    ODDSPORTAL_MARKETS,
)


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
        print(f"No matches found for {league_url_frag}")
        return []

    print(f"Found {len(market_urls)} matches for {league_url_frag}")
    return market_urls


def get_historical_links(league_url_frag: str, market: str, page_num: str):

    url = ODDSPORTAL_BASE_URL + league_url_frag + "results/#/page/" + page_num

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, timeout=60000)

        # Scroll to bottom to trigger dynamic loading
        previous_height = 0
        while True:
            current_height = page.evaluate("(window.innerHeight + window.scrollY)")
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(1)
            new_height = page.evaluate("(window.innerHeight + window.scrollY)")
            if new_height == previous_height:
                break
            previous_height = new_height

        html = page.content()
        browser.close()

    soup = BeautifulSoup(html, "html.parser")
    containers = soup.find_all("div", {"class": "min-h-[80vh]"})

    links = []
    for container in containers:
        a_tags = container.find_all("a", href=True)
        for a in a_tags:
            href = a["href"]
            if "/football/england/premier-league/" in href:
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

    print(f"Found {len(market_urls)} historical matches for {league_url_frag}")
    return market_urls
