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
import time

class IDFCScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        self.url = self._get_url()
        self.driver = None
        self._driver_owned = False

    def _get_url(self):
        try:
            json_path = os.path.join(os.path.dirname(__file__), '../bank_urls.json')
            with open(json_path, 'r', encoding='utf-8') as file:
                urls = json.load(file)
                return urls.get("idfc")
        except Exception as e:
            logging.error(f"Error loading bank URLs: {str(e)}")
            return None

    def setup_driver(self):
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
        if self._driver_owned and self.driver:
            try:
                self.driver.quit()
            except Exception:
                pass
            self.driver = None
            self._driver_owned = False

    def get_rate(self):
        if not self.url:
            logging.error("No URL configured for IDFC")
            return None

        try:
            self.setup_driver()
            if not self.driver:
                logging.error("No webdriver available")
                return None

            logging.info("IDFC: Loading URL...")
            self.driver.get(self.url)

            # First wait for page to load
            wait = WebDriverWait(self.driver, 15)
            try:
                logging.info("IDFC: Waiting for page load...")
                # Wait for any table to appear
                table = wait.until(EC.presence_of_element_located((By.TAG_NAME, "table")))
                # Give extra time for dynamic content
                time.sleep(5)
                logging.info("IDFC: Page loaded")
            except TimeoutException:
                logging.error("IDFC: Timeout waiting for page load")
                return None

            soup = BeautifulSoup(self.driver.page_source, 'html.parser')

            # Find all tables and look for one with USD rate
            tables = soup.find_all('table')
            logging.info(f"IDFC: Found {len(tables)} tables")

            for table in tables:
                # Log table classes to help debug
                logging.info(f"IDFC: Table classes: {table.get('class', [])}")

                rows = table.find_all('tr')
                logging.info(f"IDFC: Table has {len(rows)} rows")

                # Log first row to see structure
                if rows:
                    first_row = rows[0].get_text().strip()
                    logging.info(f"IDFC: First row content: {first_row}")

                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    cell_texts = [cell.get_text().strip() for cell in cells]
                    logging.info(f"IDFC: Row content: {cell_texts}")

                    if len(cells) >= 5 and any('USD' in cell.get_text() for cell in cells):
                        try:
                            # Try different column indices
                            for i in [3, 4]:
                                try:
                                    rate_text = cells[i].get_text().strip()
                                    logging.info(f"IDFC: Trying column {i}: {rate_text}")
                                    tt_buy_rate = float(rate_text.replace(',', ''))
                                    logging.info(f"IDFC: Found USD rate: {tt_buy_rate}")
                                    return {
                                        'bank': 'IDFC First Bank',
                                        'tt_buy_rate': tt_buy_rate,
                                        'timestamp': datetime.now().isoformat()
                                    }
                                except (ValueError, IndexError):
                                    continue

                        except Exception as e:
                            logging.error(f"IDFC: Error parsing rate: {str(e)}")
                            continue

            logging.error("IDFC: Could not find USD rate in any table")
            return None

        except Exception as e:
            logging.error(f"IDFC: Error in scraper: {str(e)}")
            logging.exception("IDFC: Full traceback:")
            return None
        finally:
            if self._driver_owned:
                self.cleanup()

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    scraper = IDFCScraper()
    rate = scraper.get_rate()
    if rate:
        print(f"Extracted rate: {rate['tt_buy_rate']}")
    else:
        print("Rate not found.")