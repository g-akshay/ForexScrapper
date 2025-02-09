# USD-INR TT Buy Rate Scraping and Visualization Project

## Overview

This project involves building a web scraping application to extract USD-INR TT buy rates from multiple bank websites, storing the data for the last 15 days, and publishing it as a JSON file. The data will later be used to generate a line chart similar to the one at https://forex.geekdevs.com/.

---

## Features

### **1. Data Scraping**

- **Objective**: Extract the USD-INR TT buy rates from various bank websites.
- **Tools**:
  - `BeautifulSoup` or `Selenium` for web scraping.
  - `Requests` for making HTTP requests.
- **Target Websites**:
  - Bank websites like ICICI, SBI, HDFC, etc., that publish TT buy rates.
  - Example: ICICI Bank's forex page [6].
- **Frequency**: The scraper will run daily (or periodically) to fetch updated rates.
- **Source of bank URLS**: /ForexScrapper/src/bank_urls.json

### **2. Data Storage**

- **Format**: Store the scraped data in a JSON file.
- **Structure**:
  {
  "date": "2025-02-09",
  "rates": [
  {
  "bank": "ICICI Bank",
  "tt_buy_rate": 87.43
  },
  {
  "bank": "HDFC Bank",
  "tt_buy_rate": 87.50
  }
  ]
  }
- **Retention Policy**: Maintain data for the last 15 days only. Older entries will be purged.

### **3. Data Publishing**

- Publish the JSON file to a specified directory or API endpoint for downstream usage.
- Example file name: `usd_inr_tt_rates.json`.

### **4. Historical Data Management**

- Store historical rates (last 15 days) in a database or as an extended JSON file.
- Example structure:
  {
  "historical_data": [
  {
  "date": "2025-02-08",
  "rates": [
  { "bank": "ICICI Bank", "tt_buy_rate": 87.40 },
  { "bank": "HDFC Bank", "tt_buy_rate": 87.45 }
  ]
  },
  ...
  ]
  }

### **5. Visualization**

- Use the stored data to generate a line chart showing trends in USD-INR TT buy rates over time.
- Libraries:
- Frontend: `Chart.js` or `D3.js`.
- Backend (optional): Python's `matplotlib` or `Plotly`.

---

## Application Flow

### **1. Scraper Initialization**

1. Define target bank URLs and selectors for extracting TT buy rates.
2. Configure scraping frequency using a scheduler like `cron` (Linux) or `APScheduler` (Python).

### **2. Scraping Process**

1. Send HTTP requests to target bank pages using the `requests` library.
2. Parse HTML content with `BeautifulSoup` or interact dynamically using `Selenium` if JavaScript rendering is required.
3. Extract relevant rate information using CSS selectors or XPath.

### **3. Data Validation and Cleaning**

1. Validate scraped data:

- Ensure rates are numeric and within expected ranges.
- Check for null or missing values.

2. Clean data:

- Remove unnecessary characters (e.g., currency symbols).
- Standardize formats.

### **4. Data Storage**

1. Append new data to a JSON file or database (e.g., SQLite, MongoDB).
2. Implement logic to retain only the last 15 days of data.

### **5. Publishing Data**

1. Save the updated JSON file to a public directory or expose it via an API endpoint.

### **6. Visualization**

1. Fetch historical data from the JSON file or database.
2. Render a line chart showing trends over time on a frontend application.

---

## Technical Stack

### **Backend**

- Python for scraping and data processing.
- Libraries:
- `requests`, `BeautifulSoup`, and optionally `Selenium`.
- `pandas` for data manipulation.
- `Flask` or `FastAPI` for exposing APIs.

### **Frontend**

- React.js or plain HTML/JS for rendering charts.
- Charting Library: `Chart.js`, `D3.js`, or similar.

### **Database (Optional)**

- SQLite for lightweight storage of historical data.
- MongoDB for NoSQL storage (if dynamic querying is needed).

---

## Implementation Steps

### **Step 1: Scraper Development**

1. Write Python scripts to scrape TT buy rates from target websites.
2. Handle dynamic content loading using Selenium if necessary.

### **Step 2: Data Storage Setup**

1. Create a JSON structure for storing daily rates and historical data.
2. Implement logic to maintain only the last 15 days of records.

### **Step 3: API Development (Optional)**

1. Build RESTful APIs using Flask/FastAPI to serve scraped data.
2. Endpoints:

- `/api/rates`: Fetch current day's rates.
- `/api/historical`: Fetch historical rates.

### **Step 4: Frontend Integration**

1. Develop a simple web page with a line chart displaying trends in USD-INR TT buy rates.
2. Fetch data from the JSON file/API and render it dynamically.

---

## Challenges and Solutions

### Challenge: Dynamic Content Loading

- Some bank websites may use JavaScript to render forex rates dynamically.
- Solution: Use Selenium for browser automation or analyze network requests to directly access APIs serving rate data.

### Challenge: Rate Variability Across Banks

- Different banks may have slight variations in their TT buy rates due to margins and policies [7].
- Solution: Scrape multiple banks and calculate averages if needed.

---

## Future Enhancements

1. Add support for more currencies (e.g., EUR-INR, GBP-INR).
2. Automate email notifications when significant rate changes occur.
3. Integrate with third-party APIs like XE.com for fallback rate retrieval [5].
4. Deploy the application on cloud platforms like AWS/GCP for scalability.

---

## Example Output

### JSON File (`usd_inr_tt_rates.json`)

{
"date": "2025-02-09",
"rates": [
{ "bank": "ICICI Bank", "tt_buy_rate": 87.43 },
{ "bank": "HDFC Bank", "tt_buy_rate": 87.50 }
],
"historical_data": [
{
"date": "2025-02-08",
"rates": [
{ "bank": "ICICI Bank", "tt_buy_rate": 87.40 },
{ "bank": "HDFC Bank", "tt_buy_rate": 87.45 }
]
},
...
]
}

This structured explanation provides all the necessary details to implement your project efficiently!
