# Création du jeu de données
data <- data.frame(
  Groupe = c("AgArtCommChEnt", "CadPrIntel", "Pinter", "Employés", "Ouvriers",
             "Retraités-inactifs"),
  Sciences = c(26757, 103009, 49844, 50914, 33089, 36909),
  Autres = c(
    19041 + 21279 + 35988 + 5252 + 18081,   # AgArtCommChEnt
    68475 + 54497 + 122705 + 18114 + 96241, # CadPrIntel
    25592 + 27658 + 72565 + 11388 + 26260,  # Pinter
    32148 + 37731 + 91446 + 12674 + 21964,  # Employés
    17771 + 25970 + 53805 + 7126 + 12470,   # Ouvriers
    27960 + 28790 + 85196 + 5328 + 24439    # Retraités-inactifs
  )
)

# Affichage des données
print(data)

library(tidyr)

# Création d'une colonne Y et expansion des données
data_long <- data %>%
  uncount(Sciences, .id = "Y") %>%
  mutate(Y = 1) %>%
  bind_rows(
    data %>% uncount(Autres, .id = "Y") %>% mutate(Y = 0)
  )

# Définir "Employés" comme référence
data_long$Groupe <- relevel(factor(data_long$Groupe), ref = "Employés")

# Vérification
print(table(data_long$Groupe, data_long$Y))

# Ajustement du modèle
model <- glm(Y ~ Groupe, family = binomial(), data = data_long)

# Résumé du modèle
print(summary(model))

# Calcul des odds ratios (OR)
print(exp(coef(model)))
print(exp(confint.default(model)))
