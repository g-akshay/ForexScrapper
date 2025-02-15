#!/usr/bin/env python3
import requests
import json
import logging
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from PyPDF2 import PdfReader
import io
import re
from datetime import datetime
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class SBIScraper:
    def __init__(self):
        self.url = "https://sbi.co.in/"
        logging.info("Initializing SBI Scraper")

    def get_latest_forex_pdf_url(self):
        try:
            logging.info("Fetching SBI homepage to find forex rates PDF link...")
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            }
            response = requests.get(self.url, headers=headers)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')
            logging.info("Parsing SBI homepage for forex PDF link...")

            for link in soup.find_all('a', href=True):
                if "FOREX CARD RATES" in link.text.upper():
                    pdf_url = urljoin(self.url, link['href'])
                    logging.info(f"Found forex PDF URL: {pdf_url}")
                    return pdf_url

            raise Exception("Could not find Forex rates PDF link on SBI website")

        except Exception as e:
            logging.error(f"Error fetching latest URL: {str(e)}")
            return None

    def extract_tt_buy_rate_from_pdf(self, url):
        try:
            logging.info("Downloading forex rates PDF...")
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'application/pdf',
                'Referer': 'https://sbi.co.in/'
            }

            response = requests.get(url, headers=headers)
            response.raise_for_status()

            if not response.content:
                raise Exception("PDF content is empty")

            logging.info("Parsing PDF content...")
            pdf_bytes = io.BytesIO(response.content)
            pdf_reader = PdfReader(pdf_bytes)

            for page_num, page in enumerate(pdf_reader.pages):
                logging.info(f"Scanning page {page_num + 1} for USD rate...")
                text = page.extract_text()
                match = re.search(r'UNITED STATES DOLLAR\s+USD/INR\s+([0-9.]+)', text, re.IGNORECASE)
                if match:
                    tt_buy_rate = float(match.group(1))
                    logging.info(f"Found TT Buy rate: {tt_buy_rate}")
                    return tt_buy_rate

            raise Exception("Could not find TT Buy rate in PDF")

        except Exception as e:
            logging.error(f"Error extracting rate from PDF: {str(e)}")
            return None

    def get_rate(self):
        """Main method called by the scraper framework"""
        try:
            logging.info("Starting SBI rate scraping process...")

            pdf_url = self.get_latest_forex_pdf_url()
            if not pdf_url:
                raise Exception("Could not get PDF URL")

            tt_buy_rate = self.extract_tt_buy_rate_from_pdf(pdf_url)
            if tt_buy_rate is None:
                raise Exception("Could not extract TT buy rate from PDF")

            # Get current timestamp in UTC
            timestamp = datetime.utcnow().isoformat() + "Z"

            rate_data = {
                'bank': 'SBI',  # Note: Using uppercase 'SBI' to match existing entries
                'tt_buy_rate': tt_buy_rate,
                'timestamp': timestamp
            }

            logging.info(f"Successfully scraped SBI rate: {rate_data}")

            # Update existing entry if present
            self.update_existing_entry(rate_data)

            return rate_data

        except Exception as e:
            logging.error(f"Error in SBI scraper: {str(e)}")
            return None

    def update_existing_entry(self, rate_data):
        """Update existing entry in all_banks_data.json if present"""
        try:
            json_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'all_banks_data.json')

            if not os.path.exists(json_path):
                logging.info("all_banks_data.json does not exist yet")
                return

            with open(json_path, 'r', encoding='utf-8') as file:
                data = json.load(file)

            current_date = datetime.now().strftime('%Y-%m-%d')

            # Find today's entry
            for entry in data['historical_data']:
                if entry['date'] == current_date:
                    # Find and update SBI entry
                    for rate in entry['rates']:
                        if rate['bank'].upper() == 'SBI':
                            logging.info(f"Updating existing SBI entry for {current_date}")
                            rate.update(rate_data)

                            # Save updated data
                            with open(json_path, 'w', encoding='utf-8') as file:
                                json.dump(data, file, indent=2)
                            return

            logging.info("No existing SBI entry found for today")

        except Exception as e:
            logging.error(f"Error updating existing entry: {str(e)}")

if __name__ == "__main__":
    # When run individually, execute and show results
    scraper = SBIScraper()
    result = scraper.get_rate()
    if result:
        print("\nSuccessfully scraped SBI rate:")
        print(json.dumps(result, indent=2))
    else:
        print("\nFailed to scrape SBI rate")
