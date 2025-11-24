library(dplyr)
library(NbClust)
library(broom)

# Chargement des données
df <- read.csv("données.csv", sep = "&", dec = ",", header = TRUE)

# Conversion des colonnes numériques
df[, -1] <- df[, -1] %>%
  lapply(function(x) as.numeric(gsub(",", ".", x))) %>%
  as.data.frame()

# Calcul du barycentre global 
barycentre <- colMeans(df[, -1], na.rm = TRUE)

# Calcul de l'inertie totale
inertie_totale <- sum(rowSums((df[, -1] - barycentre)^2, na.rm = TRUE))
cat("Inertie totale du nuage de points :", inertie_totale, "\n")

# Classification ascendante hiérarchique
dist_matrix <- dist(df[, -1], method = "euclidean")
cah <- hclust(dist_matrix, method = "ward.D2")
plot(cah, labels = df[, 1], main = "Dendrogramme CAH", sub = "", xlab = "")

# Découpage en k classes (ex: k = 3)
k <- 3
df$Cluster <- cutree(cah, k) %>% as.factor()
print(df[, c(1, ncol(df))])

# Premier élément réuni lors de la fusion
print(df$Pays[abs(cah$merge[1, ])])

# Découpage en 9 classes pour la visualisation à l'étape 6
k <- 9
df$Cluster <- cutree(cah, k) %>% as.factor()
print(df[, c(1, ncol(df))])

# Calcul de l'inertie intra-classes
inertie_intr <- sum(sapply(unique(df$Cluster), function(cl) {
  individus <- df[df$Cluster == cl, -c(1, ncol(df))]
  barycentre_cl <- colMeans(individus, na.rm = TRUE)
  sum(rowSums((individus - barycentre_cl)^2, na.rm = TRUE))
}))
cat("Inertie intra-classes :", inertie_intr, "\n")

# Calcul de l'inertie inter-classes
barycentre_gl <- colMeans(df[, -c(1, ncol(df))], na.rm = TRUE)
inertie_inte <- sum(sapply(unique(df$Cluster), function(cl) {
  individus <- df[df$Cluster == cl, -c(1, ncol(df))]
  barycentre_cl <- colMeans(individus, na.rm = TRUE)
  nrow(individus) * sum((barycentre_cl - barycentre_gl)^2)
}))
cat("Inertie inter-classes :", inertie_inte, "\n")

# Affichage des hauteurs des fusions et distances entre agrégations
print(cah$height)
print(diff(cah$height))

# Choix du nombre optimal de classes
df_matrix <- as.matrix(df[, -1])
par(mfrow = c(2, 2))
k <- 10

rsq <- rep(0, nrow(df_matrix))
for (i in seq_len(nrow(df_matrix))) {
  cla <- as.factor(cutree(cah, i))
  rsq[i] <- sum(t((t(sapply(seq_len(ncol(df_matrix)),
                            function(i) tapply(df_matrix[, i], cla, mean))) -
                     apply(df_matrix, 2, mean))**2) * as.vector(table(cla))) /
    inertie_totale
}
plot((1:k), rsq[1:k], type = "o", pch = 16, xlab = "nombre de classes",
     ylab = "RSQ")

sp_rsq <- rsq[2:length(rsq)] - rsq[1:(length(rsq) - 1)]
plot(2:k, sp_rsq[1:(k - 1)], type="o", pch = 16, xlab = "nombre de classes",
     ylab = "SPRSQ")

pseudo_f <- rsq[2:(length(rsq) - 1)] / ((2:(length(rsq) - 1)) - 1) /
  ((1 - rsq[2:(length(rsq) - 1)]) / (length(rsq) - ((2:(length(rsq) - 1)))))
plot((2:(length(rsq) - 1))[1:k], pseudo_f[1:k], type = "o", pch = 16,
     xlab = "nombre de classes", ylab = "pseudoF")

pseudo_t2 <- NbClust(data = df_matrix, method = "ward.D2", index = "pseudot2")$
  All.index
plot((2:(length(rsq) - 1))[1:k], pseudo_t2[1:k], type = "o", pch = 16,
     xlab = "nombre de classes", ylab = "pseudoT2")

# Choix du k optimal et affichage des classes
k <- 2
df$Cluster <- cutree(cah, k) %>% as.factor()
print(df[, c(1, ncol(df))])

# Calcul et affichage des moyennes par classes
moyennes_classes <- df %>%
  group_by(Cluster) %>%
  summarise(across(where(is.numeric), mean, na.rm = TRUE)) %>%
  as.data.frame()
print("Moyennes par classe (k=2):")
print(moyennes_classes)

# Calcul des valeurs tests
calculer_valeurs_tests <- function(df, k) {
  df$Cluster <- cutree(cah, k) %>% as.factor()
  variables_numeriques <- setdiff(names(df)[sapply(df, is.numeric)], "Cluster")
  resultats <- lapply(variables_numeriques, function(var) {
    aov_result <- aov(as.formula(paste(var, "~ Cluster")), data = df)
    f_value <- summary(aov_result)[[1]]$`F value`[1]
    p_value <- summary(aov_result)[[1]]$`Pr(>F)`[1]
    if (k == 2) {
      t_test <- t.test(as.formula(paste(var, "~ Cluster")), data = df)
      list(Variable = var, F_value = f_value, p_value = p_value,
           T_value = t_test$statistic, DF = t_test$parameter, Mean_Diff =
             diff(t_test$estimate))
    } else {
      list(Variable = var, F_value = f_value, p_value = p_value, T_value = NA,
           DF = NA, Mean_Diff = NA)
    }
  })
  do.call(rbind, resultats) %>% as.data.frame() %>% arrange("p_value")
}

print(calculer_valeurs_tests(df, k = 2))