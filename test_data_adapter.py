
import pandas as pd

from modules.data_adapter import adapt_sales_data


sample_data = pd.DataFrame({
    "Sale Date": ["2026-10-20", "2026-10-20", "2026-10-21"],
    "Product": ["Burger", "Burger", "Pizza"],
    "Qty": [2, 2, 1],
    "Price": [100, 100, 250],
    "Revenue": [200, 200, 250],
})

result = adapt_sales_data(sample_data)

print("Import summary:")
print(result["summary"])

print("\nAccepted records:")
print(result["accepted"])

print("\nValidation issues:")
print(result["issues"])
