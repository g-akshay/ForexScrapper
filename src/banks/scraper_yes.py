#!/usr/bin/env python3
import logging
import json
import os
from datetime import datetime
import requests
from bs4 import BeautifulSoup

class YesScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.yesbank.in/nri-banking/forex-services/forex-rates',
            'Connection': 'keep-alive',
            'Cache-Control': 'no-cache'
        }
        self.url = self._get_url()

    def _get_url(self):
        try:
            json_path = os.path.join(os.path.dirname(__file__), '../bank_urls.json')
            with open(json_path, 'r', encoding='utf-8') as file:
                urls = json.load(file)

            url = urls.get("yes")
            if not url:
                logging.error("URL for Yes Bank not found in bank_urls.json")
                return None
            return url
        except Exception as e:
            logging.error(f"Error loading bank URLs: {str(e)}")
            return None

    def get_rate(self):
        if not self.url:
            return None

        try:
            # First get the session cookie
            session = requests.Session()

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'en-US,en;q=0.9',
                'Referer': 'https://www.yesbank.in/nri-banking/forex-services/forex-rates',
                'Origin': 'https://www.yesbank.in',
                'Connection': 'keep-alive',
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            }

            # The API endpoint for forex rates
            forex_url = "https://www.yesbank.in/api/v1/forex-rates"

            # Request payload
            payload = {
                "rateType": "NRI",
                "currency": "USD",
                "amount": "1"
            }

            logging.info("Fetching forex rates...")
            response = session.post(forex_url, headers=headers, json=payload, timeout=10)

            if response.status_code != 200:
                logging.error(f"Failed to get rates. Status code: {response.status_code}")
                logging.info(f"Response content: {response.text[:200]}")  # Log first 200 chars
                return None

            # Try to parse as JSON
            try:
                data = response.json()
                logging.info("Got JSON response")
                logging.info(f"Response structure: {json.dumps(data, indent=2)[:200]}")

                # Extract rate from response
                if isinstance(data, dict):
                    # Try different possible paths to the rate
                    rate_paths = [
                        lambda d: d.get('data', {}).get('ttBuyRate'),
                        lambda d: d.get('rates', {}).get('ttBuyRate'),
                        lambda d: d.get('ttBuyRate'),
                        lambda d: d.get('data', {}).get('rates', {}).get('buy')
                    ]

                    for path in rate_paths:
                        try:
                            rate = path(data)
                            if rate:
                                tt_buy_rate = float(rate)
                                logging.info(f"Found TT Buy rate: {tt_buy_rate}")
                                return {
                                    'bank': 'Yes Bank',
                                    'tt_buy_rate': tt_buy_rate,
                                    'timestamp': datetime.now().isoformat()
                                }
                        except:
                            continue

            except Exception as e:
                logging.error(f"Error parsing response: {str(e)}")

            logging.error("Could not find USD rate in response")
            return None

        except Exception as e:
            logging.error(f"Unexpected error in Yes Bank scraper: {str(e)}")
            logging.error(f"Response headers: {response.headers if 'response' in locals() else 'No response'}")
            return None

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

    scraper = YesScraper()
    rate = scraper.get_rate()
    if rate:
        print(f"Rate: {rate}")
        if save_rate_to_json(rate):
            print("Successfully saved to all_banks_data.json")
        else:
            print("Failed to save data")
    else:
        print("Rate not found.")
