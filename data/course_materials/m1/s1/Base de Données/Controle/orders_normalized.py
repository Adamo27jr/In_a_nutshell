import sqlite3
import os

db_file = 'onetable_normalized.db'
if os.path.exists(db_file):
    os.remove(db_file)

conn = sqlite3.connect(db_file)
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE Customers (
    CustomerID INTEGER PRIMARY KEY,
    CustomerName TEXT,
    CustomerEmail TEXT
)
''')

cursor.execute('''
CREATE TABLE Products (
    ProductID INTEGER PRIMARY KEY,
    ProductName TEXT,
    Category TEXT,
    UnitPrice REAL
)
''')

cursor.execute('''
CREATE TABLE Orders (
    OrderID INTEGER PRIMARY KEY,
    CustomerID INTEGER,
    ProductID INTEGER,
    Quantity INTEGER,
    FOREIGN KEY (CustomerID) REFERENCES Customers(CustomerID),
    FOREIGN KEY (ProductID) REFERENCES Products(ProductID)
)
''')

customers_data = [
    (1, 'Alice', 'alice@email.com'),
    (2, 'Bob', 'bob@email.com'),
    (3, 'Charlie', 'charlie@email.com')
]

cursor.executemany('INSERT INTO Customers VALUES (?, ?, ?)', customers_data)

products_data = [
    (101, 'Widget', 'Gadgets', 10.00),
    (102, 'Gizmo', 'Electronics', 15.00),
    (103, 'Doohickey', 'Gadgets', 5.00)
]

cursor.executemany('INSERT INTO Products VALUES (?, ?, ?, ?)', products_data)

orders_data = [
    (1, 1, 101, 2), 
    (2, 2, 102, 1),
    (3, 1, 103, 3),
    (4, 3, 101, 1)
]

cursor.executemany('INSERT INTO Orders VALUES (?, ?, ?, ?)', orders_data)

conn.commit()

print("Data inserted into the normalized tables (Customers, Products, Orders).")
print("Open the database in DB Browser for SQLite to view the tables.")

conn.close()
print("\nScript execution complete.")
