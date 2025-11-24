import sqlite3
import os

# Create a new SQLite database
db_file = 'onetable.db'
if os.path.exists(db_file):
  os.remove(db_file)

conn = sqlite3.connect(db_file)
cursor = conn.cursor()

# Create one table
cursor.execute('''
CREATE TABLE Orders (
  OrderID INTEGER PRIMARY KEY,
  CustomerName TEXT,
  CustomerEmail TEXT,
  ProductID INTEGER,
  ProductName TEXT,
  Category TEXT,
  Quantity INTEGER,
  UnitPrice REAL
)
''')

# Insert initial data
initial_data = [
  (1, 'Alice', 'alice@email.com', 101, 'Widget', 'Gadgets', 2, 10.00),
  (2, 'Bob', 'bob@email.com', 102, 'Gizmo', 'Electronics', 1, 15.00),
  (3, 'Alice', 'alice@email.com', 103, 'Doohickey', 'Gadgets', 3, 5.00),
  (4, 'Charlie', 'charlie@email.com', 101, 'Widget', 'Gadgets', 1, 10.00)
]

cursor.executemany('INSERT INTO Orders VALUES (?,?,?,?,?,?,?,?)', initial_data)
conn.commit()

print("Initial data inserted. Open the database in DB Browser for SQLite to view the 'Orders' table.")

#  Anomaly 1
print("\nDemonstrating  Anomaly_1:")
print("Changing Alice's email to 'alice_new@email.com'")
cursor.execute("UPDATE Orders SET CustomerEmail = 'alice_new@email.com' WHERE CustomerName = 'Alice'")
conn.commit()
print("Check the 'Orders' table in DB Browser. Alice's email should be updated in multiple rows.")
print("What happened to  Alice's email.")
print("Conclusion :  Anomaly_1  est une anomalie de type redondance car l’adresse mail d’Alice est répétée dans 2 lignes ce qui entraîne une augmentation inutile de la taille de la base de données.")

# Demonstrate  Anomaly_2
print("\nDemonstrating Anomaly_2:")
print("Attempting to add a new product without customer information")
try:
  cursor.execute("INSERT INTO Orders (ProductID, ProductName, Category, UnitPrice) VALUES (104, 'Thingamajig', 'Gadgets', 7.50)")
  conn.commit()
  print("New product added, but with missing customer information.")
except sqlite3.IntegrityError:
  print("Failed to insert new product due to missing customer information.")

print("Conclusion : Anomaly_2 est une anomalie de type insertion qui va entraîner des valeurs nulles car on essaye d’ajouter une commande sans ajouter les informations du client ce qui va entraîner l’apparition de valeurs nulles.")

# Demonstrate  Anomaly_3
print("\nDemonstrating  Anomaly_3:")
print("Removing all orders for 'Widget'")
cursor.execute("DELETE FROM Orders WHERE ProductName = 'Widget'")
conn.commit()
print("Check the 'Orders' table.")
print("Conclusion :  Anomaly_3  est une anomalie de type perte de sémantique car en supprimant les lignes de commande où le produit est widget on va perdre des informations.")

# Demonstrate Anomaly_4
print("\nDemonstrating Anomaly_4:")
print("Inserting a 'NEW' product information")
try:
  cursor.execute("INSERT INTO Orders VALUES (5, 'David', 'david@email.com', 101, 'Widget', 'Electronics', 1, 12.00)")
  conn.commit()
  print("Check the 'Orders' table. What happened to 'Widget' ?")
except:
  print("Conclusion : Anomaly_4 est une anomalie de type mise à jour car on essaye de mettre à jour la base de données en ajoutant une commande mais le produit que l’on essaye d’ajouter n’existe pas dans la base de données.")

# Close the connection
conn.close()

print("\nScript execution complete.")
print("Open 'onetable.db' in DB Browser for SQLite to examine the results.")

#mise a jour 
#insertion
#suppression