ODDSPORTAL_BASE_URL = "https://www.oddsportal.com/football/"
ODDSPORTAL_DATE_FORMAT = "%d %b %Y"
OUTPUT_DATE_FORMAT = "%Y-%m-%d"
ODDSPORTAL_LINKS_REGEX = r"\b\w+(?:-\w+)+-\w{8}\b"
ODDSPORTAL_REQUEST_HEADER = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36",  # noqa
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "en-US,en;q=0.5",
    "Connection": "keep-alive",
    "Referer": "https://www.oddsportal.com/football/england/premier-league/",
}


ODDSPORTAL_FOOTBALL_SUBDOMAINS = [
    "england/premier-league/",
    # "england/championship/",
    # "england/league-one/",
    # "england/league-two/",
    # "england/national-league/",
    # "scotland/premiership/",
    # "scotland/championship/",
    # "scotland/league-one/",
    # "scotland/league-two/",
    # "germany/bundesliga/",
    # "germany/2-bundesliga/",
    # "france/ligue-1/",
    # "france/ligue-2/",
    # "spain/laliga/",
    # "spain/laliga2/",
    # "italy/serie-a/",
    # "italy/serie-b/",
    # "belgium/jupiler-pro-league/",
    # "netherlands/eredivisie/",
    # "netherlands/eerste-divisie/",
    # "portugal/liga-portugal/",
    # "turkey/super-lig/",
]

ODDSPORTAL_LOCATORS = {
    "ODDS_XPATH": "//a[contains(@href, '/bookmaker/bet365/betslip/')]",
    "HOME_XPATH": '//*[@id="react-event-header"]/div/div/div[1]/div[1]/div[1]/p',
    "AWAY_XPATH": '//*[@id="react-event-header"]/div/div/div[1]/div[3]/div[2]/p',
    "DATE_XPATH": '//*[@id="react-event-header"]/div/div/div[2]/div[1]',  #'//*[@id="app"]/div/div[1]/div/main/div[3]/div[2]/div[1]/div[2]/div[1]',  # noqa
}

ODDSPORTAL_MARKETS = {
    "btts": "/#bts;2",
    "match_odds": "/#1X2;2",
    "O1.5": "/#over-under;2;1.50;0",
    "O2.5": "/#over-under;2;2.50;0",
}
