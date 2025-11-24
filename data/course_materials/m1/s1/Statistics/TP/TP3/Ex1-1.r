# 1.
n0 <- 100
mu0 <- 1
sigma0 <- 1
Nsim <- 10000
moyennes <- rep(0, times = Nsim)
for (i in 1:Nsim) {
y <- rnorm(n0,mu0,sigma0)
moyennes[i] <- mean(y)
}

# 2.
x.grid <- seq(from = min(moyennes), to = max(moyennes), length.out = 100)
hist(moyennes, x.grid, probability = TRUE)
lines(x.grid, dnorm(x.grid,mu0,sigma0/sqrt(n0)), col = 'red')
1

# 3.
Femp <- ecdf(moyennes)
plot(Femp, do.points = FALSE)
lines(x.grid,pnorm(x.grid,mu0,sigma0/sqrt(n0)), col = 'red')

# 4.
probs <- seq(0,1,0.01)
Qemp <- quantile(moyennes, probs)
plot(qnorm(probs),Qemp,type='l')

#5
SE <- mean((moyennes - mu0)^2)
print(c('Estimation du risque :', as.character(SE)))
## [1] "Estimation du risque :" "0.00978093150407023"
print(c('Risque :', as.character(sigma0^2/n0)))
## [1] "Risque :" "0.01"
print(c('erreur relative :',
as.character(abs(SE - sigma0^2/n0)/(sigma0^2/n0))))
## [1] "erreur relative :" "0.0219068495929769"


