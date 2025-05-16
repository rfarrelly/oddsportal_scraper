from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
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
import concurrent.futures
import signal
import sys
import os
import threading
import time

# Global variables with thread-safe access
data_lock = threading.Lock()
data = []
links_lock = threading.Lock()
links = []
failed_links = []

# Flag for graceful shutdown
is_shutting_down = threading.Event()


def scrape_webpage(url):
    """Scrape a single webpage and return the extracted data"""
    if is_shutting_down.is_set():
        return None

    options = Options()
    options.binary_location = (
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    )
    options.add_argument("--headless")
    driver = None

    try:
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()), options=options
        )
        driver.get(url)

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, ODDSPORTAL_LOCATORS["ODDS_XPATH"])
            )
        )

        odds = [
            x.text
            for x in driver.find_elements(By.XPATH, ODDSPORTAL_LOCATORS["ODDS_XPATH"])
        ]

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, ODDSPORTAL_LOCATORS["HOME_XPATH"])
            )
        )

        home_elements = driver.find_elements(
            By.XPATH, ODDSPORTAL_LOCATORS["HOME_XPATH"]
        )
        home_team = home_elements[0].text

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, ODDSPORTAL_LOCATORS["AWAY_XPATH"])
            )
        )

        away_elements = driver.find_elements(
            By.XPATH, ODDSPORTAL_LOCATORS["AWAY_XPATH"]
        )
        away_team = away_elements[0].text

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, ODDSPORTAL_LOCATORS["DATE_XPATH"])
            )
        )

        date_elements = driver.find_elements(
            By.XPATH, ODDSPORTAL_LOCATORS["DATE_XPATH"]
        )

        date_element = date_elements[0].text
        event_date, event_time, event_day = parse_datetime(date_element)

        result_data = {
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

        result_data = expand_odds_fields(result_data)
        result_data.pop("odds")

        return result_data

    except Exception as e:
        print(f"Error scraping {url}: {e}")
        with links_lock:
            failed_links.append(url)
        return None

    finally:
        if driver:
            try:
                driver.quit()
            except Exception as e:
                print(f"Error while quitting WebDriver: {e}")


def scrape_task(url):
    """Task function for concurrent execution"""
    try:
        result = scrape_webpage(url)
        if result:
            with data_lock:
                data.append(result)
            print(f"Successfully scraped: {url}")
        return url, result is not None
    except Exception as e:
        print(f"Task failed for {url}: {e}")
        return url, False


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
        data[f"{data['book']}H"] = data["odds"][0]
        data[f"{data['book']}D"] = data["odds"][1]
        data[f"{data['book']}A"] = data["odds"][2]
    return data


def handle_exit(signum, frame):
    """Handle exit signals gracefully"""
    print("\nGracefully shutting down...")
    is_shutting_down.set()

    # Wait a moment to allow threads to finish cleanly
    time.sleep(1)

    # Save collected data
    save_data()

    # Report failed links
    print(f"Failed Links: {failed_links}")
    sys.exit(0)


def save_data():
    """Save the collected data to a CSV file"""
    with data_lock:
        if data:
            data_df = pd.DataFrame(data).sort_values("date")
            data_df.to_csv("fixtures.csv", index=False)
            print(f"Saved collected data to fixtures.csv ({len(data)} records)")
        else:
            print("No data was collected to save")


def progress_monitor(total_links):
    """Monitor and display progress"""
    start_time = time.time()
    while not is_shutting_down.is_set():
        with data_lock, links_lock:
            processed = len(data) + len(failed_links)
            remaining = total_links - processed
            elapsed = time.time() - start_time

            if processed > 0 and elapsed > 0:
                rate = processed / elapsed
                eta = remaining / rate if rate > 0 else 0

                print(
                    f"\r[Progress] Processed: {processed}/{total_links} ({processed/total_links*100:.1f}%) | "
                    f"Success: {len(data)} | Failed: {len(failed_links)} | "
                    f"Rate: {rate:.2f} links/sec | ETA: {eta/60:.1f} minutes",
                    end="",
                )

        # Exit if all links are processed
        if processed >= total_links:
            print("\nAll links processed!")
            break

        time.sleep(5)  # Update every 5 seconds

    print()  # New line after progress monitor ends


def get_optimal_workers():
    """Determine the optimal number of workers based on system resources"""
    cpu_count = os.cpu_count() or 4
    # Use slightly more workers than CPUs since this is an I/O-bound task
    return min(32, cpu_count * 2)  # Cap at a reasonable maximum


def main():
    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, handle_exit)
    signal.signal(signal.SIGTERM, handle_exit)

    print("Gathering links...")
    all_links = [get_links(league, "1X2") for league in ODDSPORTAL_FOOTBALL_SUBDOMAINS]
    all_links = list(chain(*all_links))

    with links_lock:
        links.extend(all_links)
        total_links = len(links)

    print(f"Found {total_links} links to process")

    # Determine optimal number of workers
    max_workers = get_optimal_workers()
    print(f"Using {max_workers} concurrent workers")

    # Start progress monitor in a separate thread
    monitor_thread = threading.Thread(target=progress_monitor, args=(total_links,))
    monitor_thread.daemon = True
    monitor_thread.start()

    # Process links concurrently
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Create a copy of links to avoid modification during iteration
        links_to_process = links.copy()

        # Submit all tasks
        future_to_url = {
            executor.submit(scrape_task, url): url for url in links_to_process
        }

        # Process results as they complete
        for future in concurrent.futures.as_completed(future_to_url):
            url = future_to_url[future]
            try:
                _, success = future.result()
                if success:
                    with links_lock:
                        if url in links:
                            links.remove(url)
            except Exception as e:
                print(f"Exception processing result for {url}: {e}")

    # Wait for monitor thread to finish
    monitor_thread.join(timeout=1)

    # Save data on normal completion
    save_data()

    print(f"Scraped {len(data)} links successfully")
    print(f"Failed to scrape {len(failed_links)} links")
    if failed_links:
        print(f"Failed links: {failed_links}")


if __name__ == "__main__":
    main()
