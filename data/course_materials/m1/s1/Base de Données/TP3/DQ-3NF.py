# Qualité des données 
import pandas as pd
#import matplotlib.pyplot as plt
from collections import defaultdict

# Read the CSV file
df = pd.read_csv('bookstore_orders.csv')

print("Data Quality Analysis Report")
print("============================")

# 1. Check for missing values
print("\n1. Missing Values:")
missing_values = df.isnull().sum()
print(missing_values[missing_values > 0])

# 2. Check for duplicate orders
print("\n2. Duplicate Orders:")
duplicates = df[df.duplicated(subset=['OrderID'])]
print(f"Number of duplicate orders: {len(duplicates)}")

# 3. Inconsistent customer information
print("\n3. Inconsistent Customer Information:")
customer_emails = df.groupby('CustomerName')['CustomerEmail'].nunique()
inconsistent_customers = customer_emails[customer_emails > 1]
print(inconsistent_customers)

# 4. Price inconsistencies
print("\n4. Price Inconsistencies:")
price_inconsistencies = df.groupby('BookTitle')['Price'].nunique()
print(price_inconsistencies[price_inconsistencies > 1])

# 5. Data type issues
print("\n5. Data Type Issues:")
df['Price'] = pd.to_numeric(df['Price'], errors='coerce')
df['Quantity'] = pd.to_numeric(df['Quantity'], errors='coerce')
print("Rows with non-numeric Price or Quantity:")
print(df[df['Price'].isnull() | df['Quantity'].isnull()])

# 6. Redundant data
print("\n6. Redundant Data:")
book_authors = df.groupby('BookTitle')['Author'].nunique()
print("Books with multiple authors (potential data inconsistency):")
print(book_authors[book_authors > 1])

# 7. Invalid quantities
print("\n7. Invalid Quantities:")
invalid_quantities = df[df['Quantity'] <= 0]
print(f"Number of orders with invalid quantities: {len(invalid_quantities)}")

# 8. Visualize data quality issues
#plt.figure(figsize=(10, 6))
issues = [
  'Missing Values', 'Duplicate Orders', 'Inconsistent Customer Info',
  'Price Inconsistencies', 'Data Type Issues', 'Redundant Data', 'Invalid Quantities'
]
counts = [
  missing_values.sum(),
  len(duplicates),
  len(inconsistent_customers),
  len(price_inconsistencies[price_inconsistencies > 1]),
  len(df[df['Price'].isnull() | df['Quantity'].isnull()]),
  len(book_authors[book_authors > 1]),
  len(invalid_quantities)
]

"""
plt.bar(issues, counts)
plt.title('Data Quality Issues')
plt.xlabel('Issue Type')
plt.ylabel('Count')
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.savefig('data_quality_issues.png')
print("\nData quality issues visualization saved as 'data_quality_issues.png'")
"""

# 9. Suggest improvements
print("\n9. Suggested Improvements:")
print("a. Normalize the database to 3NF:")
print("   - Create separate tables for Customers, Books, and Orders")
print("b. Implement data validation:")
print("   - Ensure all required fields are filled")
print("   - Validate email formats")
print("   - Ensure prices and quantities are positive numbers")
print("c. Implement data consistency checks:")
print("   - Ensure consistent pricing for books")
print("   - Maintain a single email per customer")
print("d. Use appropriate data types for each column")
print("e. Implement referential integrity constraints")
print("f. Regular data audits and cleaning processes")
