from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from config.config import (
    ODDSPORTAL_LOCATORS,
    ODDSPORTAL_DATE_FORMAT,
    OUTPUT_DATE_FORMAT,
)
from datetime import datetime
import pytz


def scrape_webpage(url):

    driver = webdriver.Chrome()

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
        "date": event_date.strftime(OUTPUT_DATE_FORMAT),
        "time": event_time.strftime("%H:%M"),
        "day": event_day,
        "league": f"{url.split('/')[4]}-{url.split('/')[5]}",
        "odds": odds,
        "home": home_team,
        "away": away_team,
        "book": ODDSPORTAL_LOCATORS["ODDS_XPATH"].split("/")[4],
    }

    try:
        driver.quit()
    except Exception as e:
        print(f"Error while quitting WebDriver: {e}")

    return data


def parse_datetime(date: str) -> tuple[datetime]:
    date_parts = date.split(",")
    event_day = date_parts[0].replace("\n", "")
    event_date = date_parts[1].replace("\n", "")
    event_time = date_parts[2].replace("\n", "").strip()

    parsed_date = datetime.strptime(event_date, ODDSPORTAL_DATE_FORMAT)
    parsed_time = datetime.strptime(event_time, "%H:%M").time()

    event_datetime = datetime.combine(parsed_date, parsed_time)

    utc_timezone = pytz.utc
    uk_timezone = pytz.timezone("Europe/London")

    event_datetime = utc_timezone.localize(event_datetime)
    event_datetime = event_datetime.astimezone(uk_timezone)

    return event_datetime.date(), event_datetime.time(), event_day


def main():
    data = scrape_webpage(
        "https://www.oddsportal.com/football/england/premier-league/nottingham-manchester-city-W2wDbEZq/#1X2;2"
    )

    print(data)


if __name__ == "__main__":
    main()
