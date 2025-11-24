library(VIM)

# Import des données
ozone <- read.csv("ozone_1.csv", sep = ";", dec = ",")

# Résumé des manquants
summary(ozone)

# Graphique aggr
aggr(ozone, col = c('blue', 'red'), numbers = TRUE, sortVars = TRUE, cex.axis = 0.7)

# Matrixplot
matrixplot(ozone, col = c("grey", "red"))

# Marginplot pour T12 et T15
marginplot(ozone[, c("T12", "T15")], col = c("blue", "red", "orange"))