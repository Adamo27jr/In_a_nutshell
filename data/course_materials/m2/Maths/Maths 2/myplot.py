from math import ceil, floor
import numpy as np
from matplotlib import pyplot as plt


def plot_decision_area(X,y,clf):
    """Exemple de fonction pour l'affichage du résultat d'une classification.
    Entrées:
     - X   : la matrice des données, chaque ligne représente une donnée
     - y   : le vecteur indiquant les classes d'appartenance des données 
     - clf : le classificateur
    """
    # Récupération de l'objet Axes de Matplotlib courant
    ax = plt.gca()

    # Choix des marqueurs et des couleurs pour les différentes classes
    markers=['s','^']
    colors=('#3ca02c','#d62728')

    # Récupération des dimensions pour l'affichage
    (x_min, x_max) = (X[:, 0].min() - 1.0, X[:, 0].max() + 1.0)
    (y_min, y_max) = (X[:, 1].min() - 1.0, X[:, 1].max() + 1.0)

    # Récupération de la résolution
    (xnum, ynum) = plt.gcf().dpi * plt.gcf().get_size_inches()
    (xnum, ynum) = (floor(xnum), ceil(ynum))
    # Calcul de la grille de points pour l'affichage des régions de décisions
    (xx, yy) = np.meshgrid(np.linspace(x_min, x_max, num=xnum),
                           np.linspace(y_min, y_max, num=ynum))
    my_grid = np.array([xx.ravel(), yy.ravel()]).T

    # Utilisation du classificateur pour classer chaque point de la grille
    Z = clf.predict(my_grid)
    Z = Z.reshape(xx.shape)
    # Affichage des zones de décisions à partir de la grille
    cset = ax.contourf(xx, yy, Z, colors=colors,
                       levels=np.arange(Z.max() + 2) - 0.5, alpha= 0.45,
                       antialiased= True)

    # Affichage de la frontière de décision
    ax.contour(xx, yy, Z, cset.levels, linewidths=0.5, colors="black",
               antialiased=True)

    ax.axis([xx.min(), xx.max(), yy.min(), yy.max()])

    # Affichage des points du jeu de données
    # Chaque itération de la boucle affiche les points d'une classe donnée
    for idx, c in enumerate(np.unique(y)):
        x_data = X[y == c, 0]
        y_data = X[y == c, 1]

        ax.scatter(x=x_data,y=y_data,c=colors[idx],marker=markers[idx],
                   alpha= 0.8, edgecolor= "black")

    return ax
