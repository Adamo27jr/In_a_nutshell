#1

#2
n0 <- 30
mu0 <- 5
sigma0 <- 1
jdd_gauss <- rnorm(n0,mu0,sigma0)

# 3.
tau <- 10/qnorm(0.975)
m <- 0

# 4.
v <- 1/tau^2 + n0/sigma0^2
v <- sqrt(1/v)
hat_mu <- ((sum(jdd_gauss)/sigma0^2) + (m/tau^2)) * v^2

#5
x.grid <- seq(from = -5, to = mu0+5, length.out = 1e3)
comp_loi_gauss <- tibble(
x = x.grid,
prior = dnorm(x.grid,m,tau),
post = dnorm(x.grid,hat_mu,v)
)
ggplot(comp_loi_gauss,aes(x = x)) +
geom_line(aes(y = prior) , color = 'orange') +
geom_line(aes(y = post), color = 'blue') +
geom_vline(xintercept = mu0, linetype = 'dotdash', color = 'black')
