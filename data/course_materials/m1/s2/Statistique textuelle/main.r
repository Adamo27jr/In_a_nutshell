texte <- "La santé ne pas manquer d argent avoir une bonne ambiance familiale je voudrais pouvoir aider les enfants abandonnés leur redonner le goût à la vie pouvoir aider les personnes âgées handicapées secourir les gens autour de soi"
segmentation <- unlist(strsplit(texte, split = " "))
print(length(segmentation))

print(table(segmentation))