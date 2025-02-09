#!/usr/bin/env python3
import logging
import importlib
import os
import json
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError
from rich.console import Console
from rich.live import Live
from rich.table import Table
from rich.panel import Panel
from rich import box
import signal
import sys
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

console = Console()

class BankStatus:
    def __init__(self, banks):
        self.status = {bank: "Pending" for bank in banks}
        self.rates = {bank: None for bank in banks}

    def update(self, bank, status, rate=None):
        self.status[bank] = status
        if rate:
            self.rates[bank] = rate

    def get_table(self):
        table = Table(box=box.ROUNDED)
        table.add_column("Bank", style="cyan")
        table.add_column("Status", style="magenta")
        table.add_column("Rate", style="green")

        for bank, status in self.status.items():
            rate = str(self.rates[bank]) if self.rates[bank] else "-"
            status_style = {
                "Pending": "yellow",
                "Running": "blue",
                "Complete": "green",
                "Failed": "red"
            }.get(status, "white")

            table.add_row(
                bank.upper(),
                f"[{status_style}]{status}[/{status_style}]",
                rate
            )

        return Panel(table, title="Forex Rate Scraper Status", border_style="blue")

def get_scraper_class_name(bank):
    """Get the correct scraper class name for a bank"""
    if bank == 'iob':
        return 'IOBScraper'
    elif bank == 'canara':
        return 'CanaraScraper'
    elif bank == 'kotak':
        return 'KotakScraper'  # Changed to match the actual class name
    elif bank == 'icici':
        return 'ICICIScraper'
    elif bank == 'hsbc':
        return 'HSBCScraper'
    else:
        return f"{bank.upper()}Scraper"

def run_scraper(bank, bank_status):
    """Run a single scraper and return its result"""
    try:
        bank_status.update(bank, "Running")
        module_name = f"banks.scraper_{bank}"
        class_name = get_scraper_class_name(bank)

        module = importlib.import_module(module_name)
        scraper_class = getattr(module, class_name)

        scraper = scraper_class()
        rate = scraper.get_rate()

        if rate:
            bank_status.update(bank, "Complete", rate['tt_buy_rate'])
            return rate
        else:
            bank_status.update(bank, "Failed")
            return None

    except Exception as e:
        bank_status.update(bank, "Failed")
        logging.error(f"Error running {bank} scraper: {str(e)}")
        return None

def run_selenium_scraper(bank, bank_status):
    """Run a single selenium scraper with its own Chrome instance"""
    driver = None
    try:
        bank_status.update(bank, "Running")

        module_name = f"banks.scraper_{bank}"
        class_name = get_scraper_class_name(bank)
        module = importlib.import_module(module_name)
        scraper_class = getattr(module, class_name)

        # Create Chrome instance
        chrome_options = Options()
        chrome_options.add_argument('--headless=new')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

        driver = webdriver.Chrome(options=chrome_options)
        driver.set_page_load_timeout(90)

        scraper = scraper_class()
        scraper.driver = driver

        # Add a small delay before scraping
        time.sleep(2)

        rate = scraper.get_rate()
        if rate:
            bank_status.update(bank, "Complete", rate['tt_buy_rate'])
            return rate
        else:
            bank_status.update(bank, "Failed")
            return None

    except Exception as e:
        logging.error(f"Error in {bank} selenium scraper: {str(e)}")
        bank_status.update(bank, "Failed")
        return None
    finally:
        if driver:
            try:
                driver.quit()
            except Exception as e:
                logging.error(f"Error closing Chrome for {bank}: {str(e)}")

def cleanup_resources(executor=None, futures=None):
    """Cleanup resources and connections"""
    if futures:
        for future in futures:
            if not future.done():
                future.cancel()

    if executor:
        executor.shutdown(wait=False)

def signal_handler(signum, frame):
    """Handle interrupt signals"""
    console.print("\n[red]Received interrupt signal. Cleaning up...[/red]")
    cleanup_resources()
    sys.exit(1)

def run_all_scrapers():
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    # Separate scrapers by type
    selenium_scrapers = ['kotak', 'iob', 'idfc']  # Selenium-based scrapers
    request_scrapers = [
        'canara',
        'hsbc',
        'icici'
    ]  # Request-based scrapers

    # Initialize bank status tracker
    bank_status = BankStatus(selenium_scrapers + request_scrapers)

    results = []
    executor = None
    futures = []

    try:
        with Live(bank_status.get_table(), refresh_per_second=4) as live:
            # First run Selenium-based scrapers one by one
            for bank in selenium_scrapers:
                try:
                    logging.info(f"Starting {bank.upper()} scraper with dedicated Chrome instance...")
                    rate = run_selenium_scraper(bank, bank_status)
                    if rate:
                        results.append(rate)
                    live.update(bank_status.get_table())
                except Exception as e:
                    logging.error(f"Error running {bank} scraper: {str(e)}")
                    bank_status.update(bank, "Failed")
                    live.update(bank_status.get_table())
                finally:
                    time.sleep(10)

            # Then run request-based scrapers in parallel
            with ThreadPoolExecutor(max_workers=len(request_scrapers)) as request_executor:
                future_to_bank = {
                    request_executor.submit(run_scraper, bank, bank_status): bank
                    for bank in request_scrapers
                }
                futures = list(future_to_bank.keys())

                # Collect results
                for future in as_completed(future_to_bank, timeout=30):
                    bank = future_to_bank[future]
                    try:
                        rate = future.result(timeout=20)
                        if rate:
                            results.append(rate)
                        live.update(bank_status.get_table())
                    except Exception as e:
                        logging.error(f"Error getting result from {bank}: {str(e)}")
                        bank_status.update(bank, "Failed")
                        live.update(bank_status.get_table())

    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        logging.exception("Full traceback:")
    finally:
        cleanup_resources(executor, futures)

    # Final status display
    console.print("\n")
    console.print(bank_status.get_table())

    # Show final results
    if results:
        save_rates_to_json(results)
        console.print("\n[green]Rates collected and saved to all_banks_data.json[/green]")
        console.print("\nRates:", results)
    else:
        console.print("\n[red]No rates were collected[/red]")

    # Final cleanup
    cleanup_resources()

def save_rates_to_json(rates):
    """Save all rates to JSON file with 15 day retention"""
    json_path = os.path.join(os.path.dirname(__file__), 'all_banks_data.json')

    try:
        # Initialize or load existing data
        all_data = {"historical_data": []}
        if os.path.exists(json_path):
            with open(json_path, 'r', encoding='utf-8') as file:
                all_data = json.load(file)

        # Get today's date
        current_date = datetime.now().strftime('%Y-%m-%d')

        # Find or create today's entry
        today_entry = None
        for entry in all_data["historical_data"]:
            if entry["date"] == current_date:
                today_entry = entry
                break

        if not today_entry:
            today_entry = {"date": current_date, "rates": []}
            all_data["historical_data"].append(today_entry)

        # Update rates for today
        for rate in rates:
            rate_updated = False
            for existing_rate in today_entry["rates"]:
                if existing_rate["bank"] == rate["bank"]:
                    existing_rate.update(rate)
                    rate_updated = True
                    break

            if not rate_updated:
                today_entry["rates"].append(rate)

        # Sort by date (newest first) and keep only last 15 days
        all_data["historical_data"].sort(
            key=lambda x: x["date"],
            reverse=True
        )
        all_data["historical_data"] = all_data["historical_data"][:15]

        # Save to file
        with open(json_path, 'w', encoding='utf-8') as file:
            json.dump(all_data, file, indent=2)

        logging.info(f"Saved {len(rates)} rates for {current_date}")

    except Exception as e:
        logging.error(f"Error saving to JSON: {str(e)}")

if __name__ == "__main__":
    run_all_scrapers()
