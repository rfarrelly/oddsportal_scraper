import re
import requests
from bs4 import BeautifulSoup
from config.config import (
    ODDSPORTAL_BASE_URL,
    ODDSPORTAL_LINKS_REGEX,
    ODDSPORTAL_REQUEST_HEADER,
    ODDSPORTAL_MARKETS,
)


def get_links(league_url_frag: str, market: str):
    url = ODDSPORTAL_BASE_URL + league_url_frag
    res = requests.get(url, headers=ODDSPORTAL_REQUEST_HEADER)
    soup = BeautifulSoup(res.content, "lxml")
    div_tag = soup.find("div", {"class": "empty:min-h-[80vh]"})
    match_frags = re.findall(ODDSPORTAL_LINKS_REGEX, str(div_tag.contents))

    market_urls = list(
        set([url + frag + ODDSPORTAL_MARKETS[market] for frag in match_frags])
    )

    print(f"Found {len(market_urls)} matches for {league_url_frag}")

    return market_urls
