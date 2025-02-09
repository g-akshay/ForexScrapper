#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup
import logging
import json
import os
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class BOIScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.url = self._get_url()

    def _get_url(self):
        try:
            json_path = os.path.join(os.path.dirname(__file__), '../bank_urls.json')
            with open(json_path, 'r', encoding='utf-8') as file:
                urls = json.load(file)

            url = urls.get("boi")
            if not url:
                logging.error("URL for Bank of India not found in bank_urls.json")
                return None
            return url
        except Exception as e:
            logging.error(f"Error loading bank URLs: {str(e)}")
            return None

    def get_rate(self):
        if not self.url:
            return None

        try:
            # Setup Chrome options for headless browsing
            chrome_options = Options()
            chrome_options.add_argument('--headless=new')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')

            # Initialize the driver using Selenium Manager
            driver = webdriver.Chrome(options=chrome_options)
            driver.set_page_load_timeout(20)

            try:
                # Load the page
                logging.info(f"Accessing URL: {self.url}")
                driver.get(self.url)

                # Wait for table to be present
                wait = WebDriverWait(driver, 15)
                logging.info("Waiting for table to load...")
                table = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table.table")))

                # Get the page source after JavaScript execution
                content = driver.page_source
                logging.info("Successfully retrieved page content")

                # Parse with BeautifulSoup
                soup = BeautifulSoup(content, 'html.parser')

                # Find the forex rates table
                table = soup.find('table', {'class': 'table'})
                if not table:
                    logging.error("Could not find forex rates table")
                    return None

                # Get all rows
                rows = table.find_all('tr')
                logging.info(f"Found {len(rows)} rows in the table")

                # Find USD row and TTB (TT Buy) rate
                for row in rows:
                    cells = row.find_all('td')
                    if not cells:
                        continue

                    # Get all cell texts
                    cell_texts = [cell.get_text().strip() for cell in cells]
                    logging.info(f"Processing row: {cell_texts}")

                    # Look for USD in the row
                    if any('USD' in cell.get_text().upper() for cell in cells):
                        logging.info(f"Found USD row: {cell_texts}")

                        # TTB (TT Buy) is in the fourth column (index 3)
                        if len(cells) >= 4:
                            tt_buy_rate = cells[3].get_text().strip()
                            logging.info(f"Found TT Buy rate: {tt_buy_rate}")

                            # Convert to float and remove any non-numeric characters
                            tt_buy_rate = float(''.join(filter(
                                lambda x: x.isdigit() or x == '.',
                                tt_buy_rate
                            )))

                            return {
                                'bank': 'Bank of India',
                                'tt_buy_rate': tt_buy_rate,
                                'timestamp': datetime.now().isoformat()
                            }

                logging.error("Could not find USD TT Buy rate in the table")
                return None

            finally:
                driver.quit()

        except Exception as e:
            logging.error(f"Unexpected error in BOI scraper: {str(e)}")
            return None

def save_rate_to_json(rate_data):
    """Save the rate data to all_banks_data.json while maintaining last 15 days of data"""
    json_path = os.path.join(os.path.dirname(__file__), '../all_banks_data.json')

    try:
        # Initialize default structure
        all_data = {"historical_data": []}

        # Read existing data if file exists
        if os.path.exists(json_path):
            try:
                with open(json_path, 'r', encoding='utf-8') as file:
                    file_data = json.load(file)
                    if isinstance(file_data, dict) and "historical_data" in file_data:
                        all_data = file_data
            except Exception as e:
                logging.warning(f"Could not read existing file, starting fresh: {str(e)}")

        current_date = datetime.now().strftime('%Y-%m-%d')
        logging.info(f"Processing data for date: {current_date}")

        # Convert historical_data to list if it's not already
        if not isinstance(all_data["historical_data"], list):
            logging.warning("historical_data was not a list, resetting it")
            all_data["historical_data"] = []

        # Find or create today's entry
        today_entry = None
        for entry in all_data["historical_data"]:
            if isinstance(entry, dict) and entry.get("date") == current_date:
                today_entry = entry
                break

        if today_entry is None:
            logging.info("Creating new entry for today")
            today_entry = {"date": current_date, "rates": []}
            all_data["historical_data"].append(today_entry)

        # Ensure rates is a list
        if not isinstance(today_entry.get("rates"), list):
            logging.warning("rates was not a list, resetting it")
            today_entry["rates"] = []

        # Update or add the rate
        rate_updated = False
        for rate in today_entry["rates"]:
            if isinstance(rate, dict) and rate.get("bank") == rate_data["bank"]:
                logging.info(f"Updating existing rate for {rate_data['bank']}")
                rate["tt_buy_rate"] = rate_data["tt_buy_rate"]
                rate["timestamp"] = rate_data["timestamp"]
                rate_updated = True
                break

        if not rate_updated:
            logging.info(f"Adding new rate for {rate_data['bank']}")
            today_entry["rates"].append({
                "bank": rate_data["bank"],
                "tt_buy_rate": rate_data["tt_buy_rate"],
                "timestamp": rate_data["timestamp"]
            })

        # Sort and limit to 15 days
        all_data["historical_data"].sort(
            key=lambda x: x["date"] if isinstance(x, dict) else "",
            reverse=True
        )
        all_data["historical_data"] = all_data["historical_data"][:15]

        # Write the updated data
        with open(json_path, 'w', encoding='utf-8') as file:
            json.dump(all_data, file, indent=2)

        logging.info(f"Successfully saved rate data for {rate_data['bank']}")
        return True

    except Exception as e:
        logging.error(f"Error saving rate data to JSON: {str(e)}")
        logging.exception("Full traceback:")
        return False

# For testing
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    scraper = BOIScraper()
    rate = scraper.get_rate()
    if rate:
        print(f"Extracted rate: {rate['tt_buy_rate']}")
        if save_rate_to_json(rate):
            print("Successfully saved to all_banks_data.json")
        else:
            print("Failed to save data")
    else:
        print("Rate not found.")
