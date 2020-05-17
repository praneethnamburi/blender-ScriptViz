using SimPN
using Plots
plotly()

t, u = SimPN.use_integrator(dt=0.001)
plot(t, u)
