import json
import matplotlib.pyplot as plt
import datetime

def load_data(bank):
    filename = f"{bank}_data.json"
    try:
        with open(filename, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return []

def generate_chart():
    banks = ["iob", "canara", "bob", "pnb", "boi", "icici", "kotak", "yes", "hsbc"]
    data = {bank: load_data(bank) for bank in banks}

    plt.figure(figsize=(10, 6))
    for bank, rates in data.items():
        dates = [datetime.datetime.strptime(entry["date"], "%Y-%m-%d") for entry in rates]
        values = [entry["rate"] for entry in rates]
        plt.plot(dates, values, label=bank)

    plt.xlabel("Date")
    plt.ylabel("TT Buy Rate (USD-INR)")
    plt.title("Comparison of TT Buy Rates (USD-INR) Across Banks")
    plt.legend()
    plt.grid(True)
    plt.style.use('dark_background')
    plt.show()

if __name__ == "__main__":
    generate_chart()
