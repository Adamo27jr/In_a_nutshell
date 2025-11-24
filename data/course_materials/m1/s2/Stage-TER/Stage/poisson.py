import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import poisson

# Paramètre de la loi de Poisson
lambda_ = 1.5  # λ = 1

# Création des valeurs possibles de k (nombre d'enfants vivants)
k_values = np.arange(0, 11)  # De 0 à 10 enfants

# Calcul des probabilités P(X=k)
probabilities = poisson.pmf(k_values, lambda_)

# Tracé du graphe
plt.figure(figsize=(10, 6))
plt.bar(k_values, probabilities, color='skyblue', edgecolor='black', alpha=0.7)
plt.title("Loi de Poisson λ=1.5", fontsize=14)
plt.xlabel('Nombre d\'enfants vivants k', fontsize=12)
plt.ylabel('Probabilité P(X=k)', fontsize=12)
plt.xticks(k_values)
plt.grid(axis='y', linestyle='--', alpha=0.7)

# Affichage des valeurs de probabilité sur les barres
for k, p in zip(k_values, probabilities):
    plt.text(k, p + 0.01, f'{p:.3f}', ha='center', fontsize=10)

plt.show()