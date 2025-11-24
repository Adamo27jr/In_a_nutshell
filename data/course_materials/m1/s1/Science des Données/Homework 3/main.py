import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

# Définir la matrice de projection P
P = np.array([[0.5, 0.5, -0.5],
              [0.0, 1.0, 0.0],
              [-0.5, 0.5, 0.5]])

# Créer une grille de points dans l'espace
x = np.linspace(-5, 5, 10)
y = np.linspace(-5, 5, 10)
X, Y = np.meshgrid(x, y)

# Calculer les coordonnées Z pour le plan projeté
# Ici, on peut définir Z = 0 pour un plan horizontal
Z = np.zeros_like(X)

# Créer une figure
fig = plt.figure(figsize=(10, 8))
ax = fig.add_subplot(111, projection='3d')

# Tracer le plan dans l'espace
ax.plot_surface(X, Y, Z, alpha=0.5, rstride=100, cstride=100, color='blue')

# Tracer quelques vecteurs de l'espace original
original_vectors = np.array([[2, 1, 1], [1, 2, 1], [1, 1, 2]])
for vec in original_vectors:
    ax.quiver(0, 0, 0, vec[0], vec[1], vec[2], color='r', arrow_length_ratio=0.1)

# Appliquer la transformation P
projected_vectors = P @ original_vectors.T

# Tracer les vecteurs projetés
for vec in projected_vectors.T:
    ax.quiver(0, 0, 0, vec[0], vec[1], vec[2], color='g', arrow_length_ratio=0.1)

# Configurer l'affichage
ax.set_xlabel('X axis')
ax.set_ylabel('Y axis')
ax.set_zlabel('Z axis')
ax.set_title('Projection of Vectors onto the Plane')
ax.view_init(elev=20, azim=30)

plt.show()
