# Creation d'un jeu de données
# Exemple qui illustre les problèmes courants de qualité des données dans une table relationnelle non-3NF (Third Normal Form). Nous utiliserons un fichier CSV pour représenter cette table, puis nous l'analyserons pour identifier les différents problèmes de qualité des données. Ensuite, nous utiliserons Python pour traiter le fichier CSV et mettre en évidence ces problèmes.
#Considérons le scénario d'une petite librairie qui maintient une table unique pour les livres, les commandes et les informations sur les clients. Cette conception viole la 3NF et entraîne plusieurs problèmes de qualité des données.

import csv

# Create a CSV file with data quality issues
csv_data = [
  ["OrderID", "Date", "CustomerName", "CustomerEmail", "BookTitle", "Author", "Price", "Quantity"],
  ["1001", "2023-05-01", "John Doe", "john@example.com", "Python Basics", "Jane Smith", "29.99", "2"],
  ["1002", "2023-05-02", "Jane Doe", "jane@example.com", "Data Science Fundamentals", "John Smith", "39.99", "1"],
  ["1003", "2023-05-02", "John Doe", "john@example.com", "Python Basics", "Jane Smith", "29.99", "1"],
  ["1004", "2023-05-03", "Alice Johnson", "alice@example.com", "Machine Learning 101", "Bob Wilson", "49.99", "1"],
  ["1005", "2023-05-04", "Bob Wilson", "bob@example.com", "Data Science Fundamentals", "John Smith", "39.99", "2"],
  ["1006", "2023-05-05", "John Doe", "johndoe@example.com", "Python Basics", "Jane Smith", "29.99", "1"],
  ["1007", "2023-05-06", "Alice Johnson", "alice@example.com", "Machine Learning 101", "Bob Wilson", "45.99", "1"],
  ["1008", "2023-05-07", "", "anonymous@example.com", "SQL for Beginners", "Jane Smith", "34.99", "1"],
  ["1009", "2023-05-08", "John Doe", "john@example.com", "Advanced Python", "Jane Smith", "", "1"],
  ["1010", "2023-05-09", "Eve Brown", "eve@example.com", "Data Science Fundamentals", "John Smith", "39.99", "0"],
]

with open('bookstore_orders.csv', 'w', newline='') as file:
  writer = csv.writer(file)
  writer.writerows(csv_data)

print("CSV file 'bookstore_orders.csv' has been created.")