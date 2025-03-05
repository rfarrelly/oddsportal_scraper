ODDSPORTAL_DATE_FORMAT = "%d %b %Y"
OUTPUT_DATE_FORMAT = "%Y-%m-%d"

ODDSPORTAL_LOCATORS = {
    "ODDS_XPATH": "//a[contains(@href, '/bookmaker/bet365/betslip/')]",
    "HOME_XPATH": '//*[@id="react-event-header"]/div/div/div[1]/div[1]/div[1]/p',
    "AWAY_XPATH": '//*[@id="react-event-header"]/div/div/div[1]/div[3]/div[2]/p',
    "DATE_XPATH": '//*[@id="react-event-header"]/div/div/div[2]/div[1]',  #'//*[@id="app"]/div/div[1]/div/main/div[3]/div[2]/div[1]/div[2]/div[1]',  # noqa
}

ODDSPORTAL_MARKETS = {
    "btts_links": "#bts;2",
    "match_links": "#1X2;2",
    # "O1.5": "/#over-under;2;1.50;0",
    # "O2.5": "/#over-under;2;2.50;0",
}
