# Chargement des packages nécessaires
install.packages("labelled")
install.packages(c("questionr", "pROC", "glm.predict", "generalhoslem"))
library(labelled)
library(questionr)
library(pROC)
library(glm.predict)
library(generalhoslem)

# 1
# Création du projet et importation des données
setwd("~/tpdc/tplogit")  # Adapter le chemin
infarctus <- read.table("infarctus.txt", header = TRUE)

# 2
# Ajout de labels
var_label(infarctus) <- list(
  y = "Infarctus du myocarde (0=non, 1=oui)",
  age = "Âge du patient",
  hpt = "Hypertension (0=non, 1=oui)"
)

# Recodage de la variable hypertension en facteur
infarctus$hpt <- factor(infarctus$hpt, levels = c(0,1), labels = c("Non", "Oui"))

# 4. Calcul des probabilités empiriques
print(prop.table(table(infarctus$y, infarctus$hpt), margin = 2))
