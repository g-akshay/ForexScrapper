#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup
import logging
import json
import os
from datetime import datetime

class CanaraScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        self.url = self._get_url()

    def _get_url(self):
        try:
            json_path = os.path.join(os.path.dirname(__file__), '../bank_urls.json')
            with open(json_path, 'r', encoding='utf-8') as file:
                urls = json.load(file)
                return urls.get("canara")
        except Exception as e:
            logging.error(f"Error loading bank URLs: {str(e)}")
            return None

    def get_rate(self):
        if not self.url:
            logging.error("No URL configured for Canara Bank")
            return None

        try:
            response = requests.get(self.url, headers=self.headers, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            tables = soup.find_all('table')

            if not tables:
                return None

            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    cell_text = ' '.join(cell.get_text().strip() for cell in cells)

                    if 'USD' in cell_text:
                        try:
                            tt_buy_rate = cells[3].get_text().strip()
                            tt_buy_rate = float(''.join(filter(lambda x: x.isdigit() or x == '.', tt_buy_rate)))

                            return {
                                'bank': 'Canara Bank',
                                'tt_buy_rate': tt_buy_rate,
                                'timestamp': datetime.now().isoformat()
                            }
                        except Exception as e:
                            continue

            return None

        except requests.RequestException as e:
            logging.error(f"Request failed: {str(e)}")
            return None
        except Exception as e:
            logging.error(f"Error in Canara scraper: {str(e)}")
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
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    scraper = CanaraScraper()
    logging.info(f"URL from config: {scraper.url}")
    rate = scraper.get_rate()
    if rate:
        print(f"Extracted rate: {rate['tt_buy_rate']}")
        if save_rate_to_json(rate):
            print("Successfully saved to all_banks_data.json")
        else:
            print("Failed to save data")
    else:
        print("Rate not found.")
