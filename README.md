# ForexScrapper

A web scraping application that collects daily USD-INR TT buy rates from multiple Indian bank websites and visualizes the trends over time.

**Live Dashboard:** https://g-akshay.github.io/ForexScrapper/

## Features

- **Multi-bank scraping** — Fetches TT buy rates from SBI, ICICI, HSBC, Kotak, Canara, IOB, IDFC, BOB, BOI, and Yes Bank
- **Automated daily runs** — GitHub Actions workflow triggers at 11 AM IST to collect fresh rates
- **Historical tracking** — Maintains the last 15 days of rate data in JSON format
- **Interactive chart** — Plotly.js-powered line chart showing rate trends across banks
- **Top banks table** — Displays the top 5 banks with the highest average rates

## Tech Stack

- **Scraping:** Python, BeautifulSoup, Selenium (for JS-rendered pages)
- **Visualization:** Plotly.js, HTML/CSS
- **Automation:** GitHub Actions (scheduled cron job)
- **Hosting:** GitHub Pages

## Project Structure

```
ForexScrapper/
├── .github/workflows/
│   └── forex_scraper.yml    # GitHub Actions workflow (daily cron)
├── src/
│   ├── banks/               # Individual bank scraper modules
│   │   ├── scraper_sbi.py
│   │   ├── scraper_icici.py
│   │   ├── scraper_hsbc.py
│   │   ├── scraper_kotak.py
│   │   ├── scraper_canara.py
│   │   ├── scraper_iob.py
│   │   ├── scraper_idfc.py
│   │   ├── scraper_bob.py
│   │   ├── scraper_boi.py
│   │   └── scraper_yes.py
│   ├── all_banks_data.json   # Aggregated historical rate data
│   ├── bank_urls.json        # Bank forex page URLs
│   ├── requirements.txt      # Python dependencies
│   └── run_all_scrapers.py   # Main scraper orchestrator
├── index.html                # Frontend dashboard
├── LICENSE                   # MIT License
└── README.md
```

## Getting Started

### Prerequisites

- Python 3.9+
- Google Chrome (for Selenium-based scrapers)

### Installation

```bash
pip install -r src/requirements.txt
```

### Run Scrapers

```bash
python src/run_all_scrapers.py
```

This runs all bank scrapers concurrently (Selenium-based scrapers in parallel, followed by request-based ones) and updates `src/all_banks_data.json` with the latest rates.

### View Dashboard Locally

Open `index.html` in a browser. It reads from `src/all_banks_data.json` to render the chart and table.

## How It Works

1. `run_all_scrapers.py` orchestrates all scrapers using `ThreadPoolExecutor`
2. Selenium-based scrapers (Kotak, IOB, IDFC) run in parallel with headless Chrome
3. Request-based scrapers (SBI, Canara, HSBC, ICICI) run concurrently after
4. Results are merged into `all_banks_data.json`, retaining the last 15 days of data
5. GitHub Actions commits and pushes the updated data daily, which is served via GitHub Pages

## License

MIT
