from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from config.config import (
    ODDSPORTAL_LOCATORS,
    ODDSPORTAL_DATE_FORMAT,
    OUTPUT_DATE_FORMAT,
    ODDSPORTAL_FOOTBALL_SUBDOMAINS,
)
from datetime import datetime
from fractions import Fraction
from links.get_match_links import get_links
import pandas as pd
from itertools import chain


def scrape_webpage(url):
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    driver = webdriver.Chrome(options=options)
    driver.get(url)

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, ODDSPORTAL_LOCATORS["ODDS_XPATH"]))
    )

    try:
        odds = [
            x.text
            for x in driver.find_elements(By.XPATH, ODDSPORTAL_LOCATORS["ODDS_XPATH"])
        ]
    except Exception as e:
        print(f"Error getting odds: {e}")

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, ODDSPORTAL_LOCATORS["HOME_XPATH"]))
    )

    try:
        home_elements = driver.find_elements(
            By.XPATH, ODDSPORTAL_LOCATORS["HOME_XPATH"]
        )
        home_team = home_elements[0].text
    except Exception as e:
        print(f"Error getting home team: {url} - {e}")

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, ODDSPORTAL_LOCATORS["AWAY_XPATH"]))
    )

    try:
        away_elements = driver.find_elements(
            By.XPATH, ODDSPORTAL_LOCATORS["AWAY_XPATH"]
        )
        away_team = away_elements[0].text
    except Exception as e:
        print(f"Error getting away team: {url} - {e}")

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, ODDSPORTAL_LOCATORS["DATE_XPATH"]))
    )

    try:
        date_elements = driver.find_elements(
            By.XPATH, ODDSPORTAL_LOCATORS["DATE_XPATH"]
        )

        date_element = date_elements[0].text
        event_date, event_time, event_day = parse_datetime(date_element)

    except Exception as e:
        print(f"Error getting date: {url} - {e}")

    data = {
        "timestamp": datetime.now().isoformat(sep=" ", timespec="minutes"),
        "date": event_date,
        "time": event_time,
        "day": event_day,
        "league": f"{url.split('/')[4]}-{url.split('/')[5]}",
        "odds": [round(float(Fraction(f)), 2) for f in odds],
        "home": home_team,
        "away": away_team,
        "market": url.split("/")[7].replace("#", "").split(";")[0].replace("#", ""),
        "book": ODDSPORTAL_LOCATORS["ODDS_XPATH"].split("/")[4],
    }

    data = expand_odds_fields(data)
    data.pop("odds")

    try:
        driver.quit()
    except Exception as e:
        print(f"Error while quitting WebDriver: {e}")

    return data


def parse_datetime(date: str) -> tuple[str]:
    date_parts = date.split(",")
    event_date = date_parts[1].replace("\n", "")
    event_time = date_parts[2].replace("\n", "").strip()

    parsed_date = datetime.strptime(event_date, ODDSPORTAL_DATE_FORMAT)
    parsed_time = datetime.strptime(event_time, "%H:%M").time()

    event_datetime = datetime.combine(parsed_date, parsed_time)

    return (
        event_datetime.date().strftime(OUTPUT_DATE_FORMAT),
        event_datetime.time().strftime("%H:%M"),
        event_datetime.strftime("%A"),
    )


def expand_odds_fields(data: dict):
    if data["market"] == "1X2":
        data[f"{data["book"]}H"] = data["odds"][0]
        data[f"{data["book"]}D"] = data["odds"][1]
        data[f"{data["book"]}A"] = data["odds"][2]
    return data


def main():

    links = [get_links(league, "1X2") for league in ODDSPORTAL_FOOTBALL_SUBDOMAINS]
    links = list(chain(*links))

    data = []

    while links:
        for link in links:
            print(f"Processing: {link}")
            try:
                data.append(scrape_webpage(link))
                links.remove(link)
            except Exception as e:
                print(f"{link} Failed: {e}")
                continue

    data_df = pd.DataFrame(data).sort_values("date")

    data_df.to_csv("fixtures.csv", index=False)


if __name__ == "__main__":
    main()
