#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup
import logging
import json
import os
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from selenium.common.exceptions import TimeoutException

class KotakScraper:
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
                return urls.get("kotak")
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
            self.driver.set_page_load_timeout(90)
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
            logging.error("No URL configured for Kotak")
            return None

        try:
            self.setup_driver()
            if not self.driver:
                logging.error("No webdriver available")
                return None

            self.driver.set_page_load_timeout(30)
            self.driver.get(self.url)

            # Wait for the forex rate table (using table_1 class)
            wait = WebDriverWait(self.driver, 15)
            try:
                table = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "table_1")))
            except TimeoutException:
                logging.error("Timeout waiting for Kotak rate table")
                return None

            soup = BeautifulSoup(self.driver.page_source, 'html.parser')

            # Find all tables with class table_1
            tables = soup.find_all('table', {'class': 'table_1'})

            # Get the last table (forex rates table)
            if tables:
                table = tables[-1]  # Last table
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if cells and 'USD' in cells[0].get_text():
                        try:
                            tt_buy_rate = float(cells[1].get_text().strip())
                            return {
                                'bank': 'Kotak Bank',
                                'tt_buy_rate': tt_buy_rate,
                                'timestamp': datetime.now().isoformat()
                            }
                        except Exception:
                            continue

            return None

        except Exception as e:
            logging.error(f"Error in Kotak scraper: {str(e)}")
            return None
        finally:
            if self._driver_owned:
                self.cleanup()

def save_rate_to_json(rate_data):
    """Save the rate data to all_banks_data.json while maintaining last 15 days of data"""
    json_path = os.path.join(os.path.dirname(__file__), '../all_banks_data.json')

    try:
        all_data = {"historical_data": []}

        if os.path.exists(json_path):
            try:
                with open(json_path, 'r', encoding='utf-8') as file:
                    file_data = json.load(file)
                    if isinstance(file_data, dict) and "historical_data" in file_data:
                        all_data = file_data
            except Exception as e:
                logging.warning(f"Could not read existing file, starting fresh: {str(e)}")

        current_date = datetime.now().strftime('%Y-%m-%d')

        if not isinstance(all_data["historical_data"], list):
            all_data["historical_data"] = []

        today_entry = None
        for entry in all_data["historical_data"]:
            if isinstance(entry, dict) and entry.get("date") == current_date:
                today_entry = entry
                break

        if today_entry is None:
            today_entry = {"date": current_date, "rates": []}
            all_data["historical_data"].append(today_entry)

        if not isinstance(today_entry.get("rates"), list):
            today_entry["rates"] = []

        rate_updated = False
        for rate in today_entry["rates"]:
            if isinstance(rate, dict) and rate.get("bank") == rate_data["bank"]:
                rate["tt_buy_rate"] = rate_data["tt_buy_rate"]
                rate["timestamp"] = rate_data["timestamp"]
                rate_updated = True
                break

        if not rate_updated:
            today_entry["rates"].append({
                "bank": rate_data["bank"],
                "tt_buy_rate": rate_data["tt_buy_rate"],
                "timestamp": rate_data["timestamp"]
            })

        all_data["historical_data"].sort(
            key=lambda x: x["date"] if isinstance(x, dict) else "",
            reverse=True
        )
        all_data["historical_data"] = all_data["historical_data"][:15]

        with open(json_path, 'w', encoding='utf-8') as file:
            json.dump(all_data, file, indent=2)

        return True

    except Exception as e:
        logging.error(f"Error saving rate data to JSON: {str(e)}")
        return False

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    scraper = KotakScraper()
    rate = scraper.get_rate()  # Will handle driver setup/cleanup internally

    if rate:
        print(f"Extracted rate: {rate['tt_buy_rate']}")
        if save_rate_to_json(rate):
            print("Successfully saved to all_banks_data.json")
        else:
            print("Failed to save data")
    else:
        print("Rate not found.")
