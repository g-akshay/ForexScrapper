#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup
import logging
import json
import os
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

class IOBScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        self.url = self._get_url()
        self.driver = None
        self._driver_owned = False  # Track if we created the driver

    def _get_url(self):
        try:
            json_path = os.path.join(os.path.dirname(__file__), '../bank_urls.json')
            with open(json_path, 'r', encoding='utf-8') as file:
                urls = json.load(file)

            url = urls.get("iob")
            if not url:
                logging.error("URL for IOB not found in bank_urls.json")
                return None
            return url
        except Exception as e:
            logging.error(f"Error loading bank URLs: {str(e)}")
            return None

    def setup_driver(self):
        """Setup Chrome driver if not provided externally"""
        if not self.driver:
            chrome_options = Options()
            chrome_options.add_argument('--headless=new')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.set_page_load_timeout(30)
            self._driver_owned = True

    def cleanup(self):
        """Cleanup resources if we own them"""
        if self._driver_owned and self.driver:
            try:
                self.driver.quit()
            except Exception:
                pass
            self.driver = None
            self._driver_owned = False

    def get_rate(self):
        if not self.url:
            logging.error("No URL configured for IOB")
            return None

        try:
            self.setup_driver()
            if not self.driver:
                logging.error("No webdriver available")
                return None

            self.driver.get(self.url)
            wait = WebDriverWait(self.driver, 15)
            try:
                # Wait for the specific table with class Gridview
                table = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "Gridview")))
            except TimeoutException:
                logging.error("Timeout waiting for IOB rate table")
                return None

            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            table = soup.find('table', {'class': 'Gridview', 'id': 'ctl00_ContentPlaceHolder1_gv'})

            if not table:
                return None

            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all(['td', 'th'])
                # USD is in the second column (index 1)
                if len(cells) >= 6 and cells[1].get_text().strip() == 'USD':
                    try:
                        # TTBuy is in the fifth column (index 4)
                        tt_buy_rate = float(cells[4].get_text().strip())
                        return {
                            'bank': 'Indian Overseas Bank',
                            'tt_buy_rate': tt_buy_rate,
                            'timestamp': datetime.now().isoformat()
                        }
                    except Exception:
                        continue

            return None

        except Exception as e:
            logging.error(f"Error in IOB scraper: {str(e)}")
            return None
        finally:
            if self._driver_owned:
                self.cleanup()

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

    scraper = IOBScraper()
    rate = scraper.get_rate()
    if rate:
        print(f"Extracted rate: {rate['tt_buy_rate']}")
        if save_rate_to_json(rate):
            print("Successfully saved to all_banks_data.json")
        else:
            print("Failed to save data")
    else:
        print("Rate not found.")
