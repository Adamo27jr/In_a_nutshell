# Chargement des packages nécessaires
library(labelled)
library(questionr)
library(pROC)
library(glm.predict)
library(generalhoslem)

# 1. Création du projet et importation des données
setwd("~/tpdc/tplogit")  # Adapter le chemin
infarctus <- read.table("infarctus.txt", header=TRUE)

# Ajout de labels
var_label(infarctus) <- list(
  y = "Infarctus du myocarde (0=non, 1=oui)",
  age = "Âge du patient",
  hpt = "Hypertension (0=non, 1=oui)"
)

# Recodage de la variable hypertension en facteur
infarctus$hpt <- factor(infarctus$hpt, levels = c(0,1), labels = c("Non", "Oui"))

# 3. Table de contingence entre y et hpt
table(infarctus$y, infarctus$hpt)

# 4. Calcul des probabilités empiriques
prop.table(table(infarctus$y, infarctus$hpt), margin = 2)

# 5. Calcul des cotes empiriques et OR
odds_non <- 28 / 326
odds_oui <- 43 / 212
odds_ratio <- odds_oui / odds_non

# 6. Modèle logistique univarié (hpt)
modele1 <- glm(y ~ hpt, data=infarctus, family=binomial)
summary(modele1)

# 7. Estimation des probabilités
predict(modele1, type="response")

# 9. Calcul de la déviance et test de significativité
deviance(modele1)
deviance(glm(y ~ 1, data=infarctus, family=binomial))

# 12. Modèle logistique univarié (age)
modele2 <- glm(y ~ age, data=infarctus, family=binomial)
summary(modele2)

# 15. Matrice de variance-covariance
summary(modele2)$cov.scaled

# 16. Tests de Wald, rapport de vraisemblance et score
drop1(modele2, test = "LRT")
drop1(modele2, test = "Rao")

# 17. Calcul des odds-ratios
exp(coef(modele2))

# 18. Prévision et intervalle de confiance
predict(modele2, newdata = data.frame(age=51), type="response", se.fit=TRUE)

# 19. Recodage de age en variable catégorielle
infarctus$agec <- cut(infarctus$age, breaks=c(0,45,50,60,100), right=FALSE, labels=c("<45", "45-49", "50-59", "≥60"))

# 20. Test du Chi²
chisq.test(table(infarctus$y, infarctus$agec))

# 24. Modèle logistique multivarié (age et hpt)
modele4 <- glm(y ~ age + hpt, data=infarctus, family=binomial)
summary(modele4)

# 28. Test de Hosmer-Lemeshow
logitgof(modele4)

# 29. Courbe ROC et AUC
roc_curve <- roc(infarctus$y, fitted(modele4))
plot(roc_curve)
auc(roc_curve)
